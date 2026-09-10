"""Replay a recorded legal action sequence to obtain a clean feasibility witness.

This is an operator reference control, not direct Astra and not Method search.
No game state is set during play. All actions use the same restricted broker.
The source trace and exact request sequence remain part of the evidence.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import time
from civ6_broker import Broker
from civ6_verify import canonical,digest,read_signed,write_signed,verify,Invalid
from civ6_transport import StrictConnection
from civ6_admin import sha256


async def run(args):
    if args.finish:
        profile=json.loads((args.output/'profile.json').read_text())
        terminal=json.loads((args.output/'terminal.json').read_text())
        async with StrictConnection() as conn: state=await conn.snapshot()
        if state!=terminal['state'] or sha256(terminal['save']['path'])!=terminal['save']['sha256']:
            raise RuntimeError('Independent replay save differs')
        records=read_signed(args.output/'trace.partial.jsonl',(args.output/'key').read_bytes())
        execution=terminal['execution']
        records.append({'kind':'finish','state':state,'terminal_save_sha256':terminal['save']['sha256'],
            'wall_seconds':time.monotonic()-terminal['started_monotonic'],'play_seconds':terminal['play_seconds'],
            'execution':execution,'usage':{'model':None,'auth':None,'model_calls':0,'api_calls':0,
                'model_cost_usd':0,'execution_sha256':digest(execution)}})
        result=verify(records,json.loads((args.output/'start.json').read_text()),state,profile,terminal['save']['sha256'])
        write_signed(args.output/'trace.jsonl',records,(args.output/'key').read_bytes())
        (args.output/'reload.json').write_bytes(canonical(state));(args.output/'result.json').write_bytes(canonical(result))
        print(json.dumps(result,indent=2));return
    if not args.source_run or not args.profile: raise ValueError('Source run and profile required')
    raw=(args.source_run/'capture.jsonl').read_bytes()
    actions=[r['request'] for r in (json.loads(line) for line in raw.splitlines()) if r['kind']=='request']
    profile=json.loads(args.profile.read_text())
    profile.update(schema='civ6-economy-profile/3',phase='legal_reference_replay',id=args.output.name,
                   max_play_seconds=600,max_wall_seconds=900,model=None,reasoning_effort=None)
    broker=await Broker(args.output,profile,digest(actions)).start()
    (args.output/'reference-actions.json').write_bytes(canonical(actions))
    execution={'model':None,'auth':None,'status':'completed','kind':'recorded_action_replay','api_calls':0,
               'source_trace_sha256':hashlib.sha256(raw).hexdigest(),'actions_sha256':digest(actions),
               'runner_sha256':sha256(__file__)}
    try:
        for index,a in enumerate(actions):
            result=await broker.action(a)
            print(json.dumps({'step':index,'action':a['action'],'ok':result['ok'],'task':result.get('task'),'error':result.get('error')}),flush=True)
            if broker.closed: break
    finally:
        terminal=await broker.stop(execution); terminal['started_monotonic']=broker.started
        (args.output/'terminal.json').write_bytes(canonical(terminal))
    if terminal.get('save'):
        async with StrictConnection() as conn:
            await conn.execute('Players[0]:GetTreasury():ChangeGoldBalance(12345)')
            await conn.load(Path(terminal['save']['path']).stem)
        print('Close the load screen, then run --finish in a separate process.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',type=Path);p.add_argument('--source-run',type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--finish',action='store_true')
    asyncio.run(run(p.parse_args()))
