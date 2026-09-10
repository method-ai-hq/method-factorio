"""Restricted, metered Civ interface and protected evidence recorder.

No endpoint accepts Lua, paths, game administration, or evaluator settings.
One process owns the debug connection throughout a trial. An uncertain write
ends the trial; it is never retried. Source files are frozen at trial start.
"""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import time

from civ6_transport import StrictConnection
from civ6_verify import canonical, digest, check_start, healthy_pairs, write_signed

ROOT = Path(__file__).resolve().parent
SCHEMAS = {
    'observe': (), 'map': (), 'end_turn': (), 'finish': (),
    'choices': ('city_id?', 'unit_id?'), 'rules': ('table', 'type?'),
    'research': ('type',), 'civic': ('type',),
    'production': ('city_id', 'kind', 'type', 'x?', 'y?'),
    'purchase': ('city_id', 'kind', 'type'),
    'policies': ('assignments',), 'focus': ('city_id','type'),
    'buy_tile': ('city_id','x','y'),
    'move': ('unit_id','x','y'), 'attack': ('unit_id','x','y'),
    'found': ('unit_id',), 'improve': ('unit_id','type'),
    'skip': ('unit_id',), 'fortify': ('unit_id',), 'heal': ('unit_id',),
    'remove_feature': ('unit_id',), 'harvest': ('unit_id',), 'repair': ('unit_id',),
    'unit_command': ('unit_id','command','type?'),
}
READS = {'observe','map','choices','rules'}
TABLES = {'Units','Buildings','Districts','Projects','Technologies','Civics','Policies',
          'Improvements','UnitPromotions','TechnologyPrereqs','CivicPrereqs',
          'District_Adjacencies','Adjacency_YieldChanges','Improvement_YieldChanges',
          'Building_YieldChanges','GlobalParameters'}


def validate(a):
    if type(a) is not dict or a.get('action') not in SCHEMAS:
        raise ValueError('Unknown action')
    fields = SCHEMAS[a['action']]
    if set(a) - {'action', *(f.rstrip('?') for f in fields)}:
        raise ValueError('Unknown field')
    if any(f not in a for f in fields if not f.endswith('?')):
        raise ValueError('Missing field')
    for k,v in a.items():
        if k in ('city_id','unit_id','x','y'):
            if type(v) is not int or not 0 <= v <= 2147483647:
                raise ValueError('Invalid integer')
        if k == 'type' and (type(v) is not str or not re.fullmatch('[A-Z][A-Z0-9_]{0,100}', v)):
            raise ValueError('Invalid type name')
    if ('x' in a) != ('y' in a):
        raise ValueError('Coordinates require x and y')
    if 'kind' in a and a['kind'] not in ('UNIT','BUILDING','DISTRICT','PROJECT'):
        raise ValueError('Invalid production kind')
    if 'table' in a and a['table'] not in TABLES:
        raise ValueError('Rules table is not allowed')
    if 'command' in a and a['command'] not in ('UPGRADE','PROMOTE','CANCEL'):
        raise ValueError('Unit command is not allowed')
    if 'assignments' in a:
        assignments=a['assignments']
        if type(assignments) is not list or not 1 <= len(assignments) <= 12:
            raise ValueError('Invalid policy assignments')
        slots=[]
        for r in assignments:
            if type(r) is not dict or set(r) != {'slot','type'} or type(r['slot']) is not int or not 0 <= r['slot'] <= 11:
                raise ValueError('Invalid policy slot')
            if type(r['type']) is not str or not re.fullmatch('POLICY_[A-Z0-9_]+',r['type']):
                raise ValueError('Invalid policy name')
            slots.append(r['slot'])
        if len(slots) != len(set(slots)):
            raise ValueError('Duplicate policy slot')
    return a


def lua(value):
    if type(value) is str:
        # JSON escaping is safe for the ASCII-only strings accepted above.
        return json.dumps(value)
    if type(value) is int:
        return str(value)
    if type(value) is list:
        return '{' + ','.join(lua(v) for v in value) + '}'
    if type(value) is dict:
        return '{' + ','.join('['+lua(k)+']='+lua(v) for k,v in value.items()) + '}'
    raise ValueError('Unsupported Lua data')


def response(lines, prefix):
    errors = [s for s in lines if s.startswith('CIVERR|')]
    if errors:
        raise RuntimeError(errors[0][7:])
    rows = [s[len(prefix):] for s in lines if s.startswith(prefix)]
    if len(rows) != 1:
        raise RuntimeError('Missing complete game response')
    return json.loads(rows[0])


class Broker:
    def __init__(self, output, profile, task_hash):
        self.output = Path(output)
        self.profile = profile
        self.task_hash = task_hash
        self.key = secrets.token_bytes(32)
        self.records=[]; self.requests=0; self.actions=0; self.turns=0
        self.closed=False; self.failure=None; self.started=None
        self.lock=asyncio.Lock(); self.done=asyncio.Event()
        self.births={}; self.streaks={}; self.longest=0

    def log(self, rec):
        rec = dict(rec,wall_seconds=time.monotonic()-self.started)
        self.records.append(rec)
        with (self.output/'capture.jsonl').open('ab') as f:
            f.write(canonical(rec)+b'\n'); f.flush(); os.fsync(f.fileno())

    async def start(self):
        self.output.mkdir(parents=True,mode=0o700,exist_ok=False)
        (self.output/'key').write_bytes(self.key); (self.output/'key').chmod(0o600)
        (self.output/'profile.json').write_bytes(canonical(self.profile))
        hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('civ6_*') if p.is_file()}
        (self.output/'source-hashes.json').write_bytes(canonical(hashes))
        self.conn=await StrictConnection().__aenter__()
        self.conn.snapshot_code=(ROOT/'civ6_snapshot.lua').read_text()
        self.start_state=await self.conn.snapshot()
        self.cap=check_start(self.start_state)
        if digest(self.start_state) != self.profile['start_state_sha256']:
            raise RuntimeError('Loaded game differs from frozen start')
        (self.output/'start.json').write_bytes(canonical(self.start_state))
        for filename in ('civ6_monitor.lua','civ6_player.lua'):
            lines=await self.conn.execute((ROOT/filename).read_text(),'ingame')
            if any(s.startswith('CIVERR|') for s in lines):
                raise RuntimeError(str(lines))
        self.started=time.monotonic()
        self.log({'kind':'start','state':self.start_state,'run_id':self.output.name,
                  'profile_sha256':digest(self.profile),'method_sha256':self.task_hash,
                  'start_save_sha256':self.profile['start_save_sha256']})
        self.server=await asyncio.start_server(self.http,'127.0.0.1',0)
        self.endpoint='http://127.0.0.1:'+str(self.server.sockets[0].getsockname()[1])+'/action'
        (self.output/'endpoint.json').write_text(json.dumps({'endpoint':self.endpoint}))
        return self

    def goal(self,state,boundary=False):
        healthy=healthy_pairs(state,self.cap,self.births)
        self.streaks={pair:n for pair,n in self.streaks.items() if pair in healthy}
        if boundary:
            self.streaks={pair:self.streaks[pair]+1 if pair in self.streaks else 0 for pair in healthy}
            self.longest=max([self.longest,*self.streaks.values()])
        return {'goal_met':any(n>=5 for n in self.streaks.values()),
                'completed_turns':self.turns,'hold_rounds':max([0,*self.streaks.values()])}

    async def drain(self):
        events=response(await self.conn.execute('CivTaskDrain()','ingame'),'CIVMON|')
        for event in events:
            if event['kind']=='founded': self.births[event['key']]={'id':event['id']}
            if event['kind']=='removed': self.births.pop(event['key'],None)
            if event['kind']=='boundary': self.turns+=1; self.goal(event['state'],True)
            self.log(event)
        return events

    async def dismiss_information(self):
        # Only informational screens, through their normal Close handler.
        # Never close diplomacy, capture choices, trade, or government choices.
        names={'TechCivicCompletedPopup','BoostUnlockedPopup','NaturalWonderPopup'}
        for index,name in self.conn.game.lua_states.items():
            if name in names:
                handler='OnClose' if name=='BoostUnlockedPopup' else 'Close'
                lines=await self.conn.execute('if not ContextPtr:IsHidden() then '+handler+'(); print("CLOSED") end',index)
                if any(s.startswith('CIVERR|') for s in lines): raise RuntimeError(str(lines))
                if 'CLOSED' in lines: self.log({'kind':'information_closed','screen':name})

    async def action(self,a):
        async with self.lock:
            if self.closed:
                return {'ok':False,'error':'Trial is closed'}
            if time.monotonic()-self.started >= self.profile['max_play_seconds'] or self.requests >= self.profile['max_requests']:
                self.closed=True; self.done.set()
                return {'ok':False,'error':'Trial budget exhausted'}
            self.requests+=1
            self.log({'kind':'request','request_id':self.requests,'request':a})
            try:
                validate(a)
            except (ValueError,TypeError) as e:
                result={'ok':False,'error':str(e)}
                self.log({'kind':'response','request_id':self.requests,'response':result})
                return result
            action=a['action']
            try:
                if action=='finish':
                    self.closed=True; self.done.set(); result={'ok':True,'closed':True}
                elif action=='end_turn':
                    if self.turns >= self.profile['max_completed_turns']:
                        self.closed=True; self.done.set(); return {'ok':False,'error':'Turn limit reached'}
                    await self.dismiss_information()
                    await self.conn.execute("CivTaskCheckpoint('turn_end')",'ingame')
                    await self.drain()
                    old=self.turns
                    blocked=None
                    lines=await self.conn.execute('UI.RequestAction(ActionTypes.ACTION_ENDTURN)','ingame')
                    if any(s.startswith('CIVERR|') for s in lines): raise RuntimeError(str(lines))
                    for poll in range(40):
                        await asyncio.sleep(.1)
                        await self.dismiss_information()
                        await self.drain()
                        if self.turns==old+1: break
                        if poll>=3:
                            status=response(await self.conn.execute('print("STATUS|"..CivTaskJSON(CivPlayerTurnStatus()))','ingame'),'STATUS|')
                            if status['blocking'] not in ('NO_ENDTURN_BLOCKING','UNKNOWN') and not status['processing'] and not status['sent'] and status['turn']==self.start_state['turn']+old:
                                # End turn can execute queued moves, then return
                                # control when a unit reaches its destination.
                                # This is a known game outcome, not a retry.
                                pending_state=await self.conn.snapshot()
                                core_turn=response(await self.conn.execute('print("CORE|"..Game.GetCurrentGameTurn())'),'CORE|')
                                await self.drain()
                                if self.turns==old+1: break
                                if pending_state['turn']==core_turn==self.start_state['turn']+old:
                                    blocked=status
                                    break
                    if self.turns != old+1 and blocked is None: raise RuntimeError('Turn did not advance exactly once')
                    state=await self.conn.snapshot(); progress=self.goal(state)
                    # A UI boundary callback can arrive after a state read. Do
                    # not report a next-turn civic choice as a blocked old turn.
                    if blocked is not None and state['turn']!=self.start_state['turn']+old:
                        for _ in range(30):
                            await asyncio.sleep(.1); await self.drain()
                            if self.turns==old+1: break
                        if self.turns!=old+1: raise RuntimeError('Advanced state lacks its boundary event')
                        blocked=None
                        state=await self.conn.snapshot(); progress=self.goal(state)
                    result={'ok':True,'state':response(await self.conn.execute('print("PLAYER|"..CivTaskJSON(CivPlayerObserve()))','ingame'),'PLAYER|'),'task':progress}
                    if blocked is not None:
                        self.log({'kind':'turn_blocked','state':state,'blocking':blocked})
                        result.update(ok=False,error='Turn has not ended. Resolve the reported blocker, then request end_turn again. Use skip for a unit you want to hold in place.',blocking=blocked)
                    if self.turns>=self.profile['max_completed_turns'] or progress['goal_met']:
                        self.closed=True; self.done.set(); result['closed']=True
                elif action in READS:
                    result={'ok':True,'data':response(await self.conn.execute('print("PLAYER|"..CivTaskJSON(CivPlayerAction('+lua(a)+')))','ingame'),'PLAYER|')}
                else:
                    action_id=self.actions; self.actions+=1
                    self.log({'kind':'begin','action_id':action_id,'name':action})
                    lines=await self.conn.execute('print("PLAYER|"..CivTaskJSON(CivPlayerAction('+lua(a)+')))','ingame')
                    # A game rejection can follow a submitted request. Always
                    # capture the resulting state before reporting it.
                    await asyncio.sleep(.1); await self.drain()
                    state=await self.conn.snapshot()
                    self.log({'kind':'after_action','action_id':action_id,'state':state})
                    progress=self.goal(state)
                    try: data=response(lines,'PLAYER|'); result={'ok':True,'data':data,'task':progress}
                    except RuntimeError as e:
                        if any(s in str(e) for s in ('function expected','attempt to','bad argument','Missing complete')):
                            raise
                        result={'ok':False,'error':str(e),'task':progress}
            except Exception as e:
                self.failure=str(e); self.closed=True; self.done.set()
                result={'ok':False,'infrastructure_failure':True,'error':str(e)}
            self.log({'kind':'response','request_id':self.requests,'response':result})
            return result

    async def http(self,reader,writer):
        try:
            head=await asyncio.wait_for(reader.readuntil(b'\r\n\r\n'),5)
            lines=head.decode('ascii').split('\r\n'); headers={}
            if lines[0]!='POST /action HTTP/1.1': raise ValueError('Only POST /action is allowed')
            for line in lines[1:]:
                if line:
                    k,v=line.split(':',1)
                    if k.lower() in headers: raise ValueError('Duplicate header')
                    headers[k.lower()]=v.strip()
            size=int(headers.get('content-length','0'))
            if not 0<size<=16384 or 'transfer-encoding' in headers: raise ValueError('Invalid body length')
            body=await asyncio.wait_for(reader.readexactly(size),5)
            a=json.loads(body,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite number')))
            result=await self.action(a)
        except Exception as e:
            result={'ok':False,'error':str(e)}
        encoded=canonical(result)
        writer.write(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\nContent-Length: '+str(len(encoded)).encode()+b'\r\n\r\n'+encoded)
        await writer.drain(); writer.close(); await writer.wait_closed()

    async def stop(self,execution=None):
        async with self.lock:
            self.closed=True; self.server.close(); await self.server.wait_closed()
            terminal={'failure':self.failure,'requests':self.requests,'turns':self.turns,'execution':execution,
                      'play_seconds':time.monotonic()-self.started}
            try:
                terminal['state']=await self.conn.snapshot()
                terminal['save']=await self.conn.save('CivTask_'+self.output.name.replace('-','_')+'_end')
                terminal['task']=self.goal(terminal['state'])
            except Exception as e:
                terminal['save_error']=str(e)
            (self.output/'terminal.json').write_bytes(canonical(terminal))
            if self.failure:
                (self.output/'result.json').write_bytes(canonical({'status':'infrastructure_failure','verified_pass':False,'reason':self.failure,'completed_turns':self.turns}))
            write_signed(self.output/'trace.partial.jsonl',self.records,self.key)
            await self.conn.__aexit__(None,None,None)
            return terminal
