"""Run a fresh direct Astra trial against the Civ broker. Operator only."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import time

from civ6_broker import Broker, ROOT, SCHEMAS, READS
from civ6_codex import run_codex
from civ6_transport import StrictConnection
from civ6_verify import canonical,digest,read_signed,write_signed,verify,Invalid
from civ6_admin import sha256


def task_text(profile):
    return f'''# Civ 6 economy task

From your one population-4 capital, found two additional cities. Each new
city must reach population 3. Sustain at least 20 science per turn,
nonnegative gold balance and net gold income, and nonnegative food surplus
in the capital and both new cities for five complete rounds. Finish within
35 completed player turns. Retain the original capital throughout the task.

The game uses the base rules, Rome led by Trajan, and Online speed. There
are no other major civilizations, city states, barbarians, or tribal huts.
Starting technology: Mining, Pottery, Animal Husbandry. Starting units:
Warrior, Scout, Builder with three charges. Starting treasury: 50 gold.

You have {profile['max_play_seconds']} seconds for all planning and play, and
{profile['max_requests']} total game requests, including reads and rejected
requests. You may plan, write code, and revise your decisions from game
observations. Complete the task through normal game actions. Do not inspect
other files, processes, or network endpoints. No external models or agents.

''' + (ROOT.parent/'docs/civ6/PLAYER_API.md').read_text()


async def run(args):
    profile=json.loads(args.profile.read_text())
    if args.finish:
        terminal=json.loads((args.output/'terminal.json').read_text())
        async with StrictConnection() as conn:
            state=await conn.snapshot()
        if terminal['failure']:
            (args.output/'reload.json').write_bytes(canonical(state))
            result={'status':'infrastructure_failure','verified_pass':False,'reason':terminal['failure'],
                    'reload_matches':state==terminal['state'],'completed_turns':terminal['turns']}
            (args.output/'result.json').write_bytes(canonical(result))
            print(json.dumps(result,indent=2)); return
        if state != terminal['state']:
            raise RuntimeError('Independent reload differs from terminal capture')
        if sha256(terminal['save']['path']) != terminal['save']['sha256']:
            raise RuntimeError('Terminal save changed')
        records=read_signed(args.output/'trace.partial.jsonl',(args.output/'key').read_bytes())
        execution=terminal['execution']
        records.append({'kind':'finish','state':state,'terminal_save_sha256':terminal['save']['sha256'],
            'wall_seconds':time.monotonic()-terminal['started_monotonic'],
            'play_seconds':terminal['play_seconds'],'execution':execution,
            'usage':{'model':execution['model'],'auth':execution['auth'],'api_calls':execution['api_calls'],
                     'model_cost_usd':None,'execution_sha256':digest(execution)}})
        (args.output/'reload.json').write_bytes(canonical(state))
        try:
            result=verify(records,json.loads((args.output/'start.json').read_text()),state,profile,terminal['save']['sha256'])
        except Invalid as error:
            result={'status':'invalid_evidence','verified_pass':False,'reason':str(error),'reload_matches':True,
                    'recorded_task':terminal['task']}
        write_signed(args.output/'trace.jsonl',records,(args.output/'key').read_bytes())
        (args.output/'result.json').write_bytes(canonical(result))
        print(json.dumps(result,indent=2)); return
    task=task_text(profile)
    broker=await Broker(args.output,profile,hashlib.sha256(task.encode()).hexdigest()).start()
    print(json.dumps({'endpoint':broker.endpoint,'run':str(args.output)}),flush=True)
    execution=None
    try:
        execution=await asyncio.to_thread(run_codex,task,args.output/'astra',broker.endpoint,profile['max_play_seconds'])
    finally:
        terminal=await broker.stop(execution)
        terminal['started_monotonic']=broker.started
        (args.output/'terminal.json').write_bytes(canonical(terminal))
    print(json.dumps({k:v for k,v in terminal.items() if k not in ('state','execution')},indent=2),flush=True)
    if terminal.get('save'):
        # A post-trial marker tests that the later reload actually took place.
        async with StrictConnection() as conn:
            await conn.execute('Players[0]:GetTreasury():ChangeGoldBalance(12345)')
            await conn.load(Path(terminal['save']['path']).stem)
        print('Close the load screen, then run --finish in a separate process.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--finish',action='store_true')
    asyncio.run(run(parser.parse_args()))
