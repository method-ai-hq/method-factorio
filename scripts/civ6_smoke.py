#!/usr/bin/env python3
"""Operator-only empty-turn control. No Method, model calls, or scored result.

Capture from the checked start, load the named terminal save, close the load
screen, then use --finish in a NEW process to inspect and verify the save.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import secrets
import time
from civ6_admin import Connection, sha256
from civ6_verify import check_start, digest, read_signed, require, verify, write_signed


async def run(args):
    profile=json.loads(args.profile.read_text())
    start=json.loads(args.start.read_text())
    if args.finish:
        key=(args.output/'key').read_bytes()
        records=read_signed(args.output/'capture.jsonl',key)
        pending=json.loads((args.output/'pending.json').read_text())
        require(sha256(pending['save']['path'])==pending['save']['sha256'],'Terminal save changed')
        async with Connection() as conn:
            state=await conn.snapshot()
        require(state == records[-1]['state'], 'Loaded state differs from captured endpoint')
        records.append({'kind':'finish','state':state,'terminal_save_sha256':pending['save']['sha256'],
                        'usage':{'model_calls':0,'model_cost_usd':0},
                        'wall_seconds':time.monotonic()-pending['started_monotonic']})
        result=verify(records,start,state,profile,pending['save']['sha256'])
        write_signed(args.output/'verified-trace.jsonl',records,key)
        (args.output/'reload-state.json').write_text(json.dumps(state,indent=2)+'\n')
        (args.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2)); return
    require(1<=args.turns<=35,'Probe needs 1 to 35 turns')
    args.output.mkdir(mode=0o700,parents=True,exist_ok=False)
    (args.output/'profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    (args.output/'start-state.json').write_text(json.dumps(start,indent=2)+'\n')
    key=secrets.token_bytes(32)
    fd=os.open(args.output/'key',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as f: f.write(key)
    records=[]
    started=time.monotonic()
    async with Connection() as conn:
        actual=await conn.snapshot()
        check_start(actual)
        require(actual==start and digest(actual)==profile['start_state_sha256'],'Wrong loaded start')
        records.append({'kind':'start','state':actual,'run_id':args.output.name,
                        'method_sha256':sha256(__file__),'start_save_sha256':profile['start_save_sha256'],
                        'profile_sha256':digest(profile),'wall_seconds':time.monotonic()-started})
        await conn.execute(Path(__file__).with_name('civ6_monitor.lua').read_text(),'ingame')
        sequence=0; timings=[]
        for n in range(args.turns):
            tick=time.monotonic()
            await conn.execute("CivTaskCheckpoint('turn_end'); UI.RequestAction(ActionTypes.ACTION_ENDTURN)",'ingame')
            expected=start['turn']+n+1
            for _ in range(40):
                await asyncio.sleep(.1)
                lines=await conn.execute("print('TURN|'..Game.GetCurrentGameTurn())")
                if 'TURN|'+str(expected) in lines: break
            else: raise RuntimeError('Turn did not advance; keep this failed capture')
            lines=await conn.execute('CivTaskDrain()','ingame')
            rows=[json.loads(s[7:]) for s in lines if s.startswith('CIVMON|')]
            require(len(rows)==1,'Missing monitor result')
            require([r['kind'] for r in rows[0]]==['turn_end','boundary'],'Unexpected engine events')
            for rec in rows[0]:
                sequence+=1
                require(rec.pop('engine_sequence')==sequence,'Missing engine event')
                rec['wall_seconds']=time.monotonic()-started;records.append(rec)
            require(records[-1]['state']['turn']==expected,'Wrong boundary turn')
            timings.append(time.monotonic()-tick)
            # Keep a separate signed partial file each turn; failures survive.
            write_signed(args.output/f'partial-{n+1:02}.jsonl',records,key)
            print(json.dumps({'completed_turns':n+1,'seconds':timings[-1]}),flush=True)
        save=await conn.save('CivTask_Empty_'+args.output.name.replace('-','_'))
        write_signed(args.output/'capture.jsonl',records,key)
        pending={'save':save,'started_monotonic':started,'turn_seconds':timings,
                 'capture_seconds':time.monotonic()-started}
        (args.output/'pending.json').write_text(json.dumps(pending,indent=2)+'\n')
        # A controlled marker makes a no-op load detectable. It is after the
        # terminal save and outside the captured trial. Never score this edit.
        await conn.execute('Players[0]:GetTreasury():ChangeGoldBalance(12345)')
        print(json.dumps({'next':'Load the terminal save, close its load screen, then run --finish','save':save},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start',type=Path,default=Path('evidence/civ6-economy-setup-2026-09-10/start-state.json'))
    p.add_argument('--profile',type=Path,default=Path('evidence/civ6-economy-setup-2026-09-10/profile.json'))
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--turns',type=int,default=35)
    p.add_argument('--finish',action='store_true')
    asyncio.run(run(p.parse_args()))
