"""Operator-only factory repair case generation and native certification.

Final layouts, fault labels, and oracle repairs stay in the case control tree.
This module is not a playing tool or an input to policy authors.
"""
import argparse
import hashlib
import json
import io
from pathlib import Path
import random
import shutil
import time

from science_contract import digest
from science_host import action, finalize, setup
from science_server import FACTORIO, Server
from science_verify import verify
from repair_fixture import build as build_factory

REPAIR_KIT = {'transport-belt': 64, 'underground-belt': 16, 'fast-inserter': 16,
              'medium-electric-pole': 20, 'solar-panel': 8, 'electric-furnace': 4,
              'electric-mining-drill': 4, 'assembling-machine-3': 4,
              'steel-chest': 4, 'splitter': 4, 'long-handed-inserter': 8}


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded(value):
    return json.dumps(json.dumps(value, separators=(',', ':')))


def reset(server, actions):
    server.command('game.tick_paused=true; script.on_event(defines.events.on_tick,nil); '
                   'storage.science.finished=nil; storage.science.clean=nil; storage.science.measurement=nil; '
                   'storage.science.audit={actions=' + str(actions) + ',violations=0,elapsed_seconds=0}; '
                   'science_clear_materials()')


def call(server, trace, req, started):
    result = action(server, req)
    trace.write(json.dumps({'request': req, 'elapsed_seconds': time.monotonic()-started, 'response': result})+'\n')
    trace.flush()
    if not result['ok']:
        raise RuntimeError('Fixture action failed; see the private trace')
    return result


def measure(server, run, trace, started):
    call(server, trace, {'action': 'finish'}, started)
    server.command('game.tick_paused=false')
    deadline = time.monotonic()+90
    while not server.read('storage.science.measurement.done'):
        if time.monotonic()>deadline:
            raise TimeoutError('Measurement did not finish')
        time.sleep(.2)
    finalize(server, run, time.monotonic()-started)


def stage_proof(run, factorio):
    result = verify(run, rcon_port=27921, game_port=34921, factorio=factorio)
    return {**result, 'verification_pass': all(result.get('verification', {}).values()) and bool(result.get('verification')),
            'record_path':run.name+'/record.json', 'save_path':run.name+'/game/world.zip',
            'verdict_path':run.name+'/verdict.json', 'record_sha256': sha(run/'record.json'), 'verdict_sha256': sha(run/'verdict.json'),
            'save_sha256': sha(run/'game/world.zip'), 'actions_sha256': sha(run/'actions.jsonl')}


def choose_faults(plan, seed, index):
    rng = random.Random(seed ^ 0xDADA)
    requests = plan['requests']
    placements = [r for r in requests if r['action']=='place']
    recipes = [r for r in requests if r['action']=='recipe']
    # Recipe and essential machine faults guarantee that every broken case fails.
    # Auxiliary belt, inserter, and power faults vary the required repair work.
    kinds = ['recipe', 'recipe-missing', 'belt-reversed', 'inserter-reversed', 'machine-missing',
             'belt-missing', 'inserter-missing', 'power-missing', 'panel-missing']
    selected = [kinds[index % 7]]
    selected += rng.sample([k for k in kinds if k not in selected], index % 4)
    faults = []
    used = set()
    for kind in selected:
        if kind=='power-missing':
            machine=rng.choice([r for r in placements if r['item'] in ('assembling-machine-3','electric-furnace','electric-mining-drill')])
            near=[r for r in placements if r['item']=='medium-electric-pole'
                  and max(abs(r['position'][axis]-machine['position'][axis]) for axis in ('x','y'))<=5
                  and tuple(r['position'].values()) not in used]
            if not near or len(near)>20: raise RuntimeError('Invalid bounded power fault')
            for r in near: used.add(tuple(r['position'].values()))
            faults.append({'kind':kind, 'damage':[{'action':'pickup','name':r['item'],'position':r['position']} for r in near], 'repair':near})
            continue
        if kind in ('recipe', 'recipe-missing'):
            candidates = recipes
        else:
            name = ('transport-belt' if kind.startswith('belt') else 'fast-inserter' if kind.startswith('inserter')
                    else 'medium-electric-pole' if kind=='power-missing' else 'solar-panel' if kind=='panel-missing'
                    else rng.choice(['assembling-machine-3', 'electric-furnace', 'electric-mining-drill']))
            candidates = [r for r in placements if r['item']==name]
        candidates = [r for r in candidates if tuple(r['position'].values()) not in used]
        original = dict(rng.choice(candidates))
        used.add(tuple(original['position'].values()))
        name = original.get('name', original.get('item'))
        target = {'name': name, 'position': original['position']}
        if kind=='recipe-missing':
            original_place = next(r for r in placements if r['item']==name and r['position']==original['position'])
            damage = [{'action':'pickup', **target}, original_place]
            repair = [original]
        elif kind=='recipe':
            wrong = rng.choice([r['recipe'] for r in recipes if r['recipe']!=original['recipe']])
            damage = {'action': 'recipe', **target, 'recipe': wrong}
            repair = [original]
        elif kind.endswith('reversed'):
            opposite = {'UP':'DOWN', 'DOWN':'UP', 'LEFT':'RIGHT', 'RIGHT':'LEFT'}
            damage = {'action':'rotate', **target, 'direction':opposite[original['direction']]}
            repair = [{'action':'rotate', **target, 'direction':original['direction']}]
        else:
            damage = {'action':'pickup', **target}
            repair = [original]
            if name=='assembling-machine-3':
                repair += [r for r in recipes if r['position']==original['position']]
        faults.append({'kind':kind, 'damage':damage, 'repair':repair})
    return faults


def build_case(root, split, index, factorio):
    seed = (710000 if split=='development' else 930000)+index*7919
    case_id = f'{split}-{index+1:03d}'
    case = root/case_id
    case.mkdir(parents=True, exist_ok=False)
    attempt = {'case_id':case_id, 'status':'started', 'seed':seed, 'builder_sources':{name:sha(Path(__file__).with_name(name)) for name in ('repair_cases.py','repair_fixture.py')}}
    write(case/'attempt.json', attempt)
    started = time.monotonic()
    try:
        healthy = case/'healthy'; healthy.mkdir()
        with Server(healthy/'game', rcon_port=27920, game_port=34920, factorio=factorio) as server:
            setup(server, 0)
            with (healthy/'actions.jsonl').open('w') as trace:
                plan = build_factory(server, io.StringIO(), started, seed=seed, send=lambda req: {"ok":True})
                queued = plan["requests"]
                plan["requests"] = []
                for offset in range(0, len(queued), 40):
                    batch = queued[offset:offset+40]
                    results = server.read("(function() local out={} for _,req in ipairs(helpers.json_to_table("+encoded(batch)+")) do local ok,result=pcall(science_action,req); table.insert(out,{ok=ok,result=ok and result or nil,error=not ok and tostring(result) or nil}) end return out end)()")
                    for req,result in zip(batch, results):
                        trace.write(json.dumps({'request':req, 'elapsed_seconds':time.monotonic()-started, 'response':result})+'\n')
                        if result['ok']: plan['requests'].append(req)
                        elif req.get('item')!='medium-electric-pole':
                            raise RuntimeError('Factory placement failed; see the private trace')
                measure(server, healthy, trace, started)
        hp = stage_proof(healthy, factorio)
        if not hp['scored_pass']:
            raise RuntimeError('Healthy factory certification failed')
        faults = choose_faults(plan, seed, index)
        write(case/'operator-control.json', {'seed':seed, 'layout':plan, 'faults':faults})
        # Keep the complete setup trace. Remove only its measurement handoff.
        base_rows = (healthy/'actions.jsonl').read_text().splitlines()[:-1]
        source = case/'source'; source.mkdir()
        with Server(source/'game', save=healthy/'game/world.zip', rcon_port=27920, game_port=34920, factorio=factorio) as server:
            server.install(); reset(server, len(base_rows))
            with (source/'actions.jsonl').open('w') as trace:
                trace.write('\n'.join(base_rows)+'\n')
                for fault in faults:
                    for req in (fault['damage'] if isinstance(fault['damage'],list) else [fault['damage']]):
                        call(server, trace, req, started)
            server.command('science_clear_materials(); storage.science.inventory=helpers.json_to_table('+encoded(REPAIR_KIT)+'); game.tick_paused=true')
            initial = server.read('science_snapshot()')
            write(case/'initial.json', initial)
        shutil.copyfile(source/'game/world.zip', case/'broken.zip')
        source_rows = (source/'actions.jsonl').read_text().splitlines()
        proofs = {}
        for stage in ['broken', 'recoverable']:
            run = case/stage; run.mkdir()
            with Server(run/'game', save=case/'broken.zip', rcon_port=27920, game_port=34920, factorio=factorio) as server:
                server.install(); reset(server, len(source_rows))
                with (run/'actions.jsonl').open('w') as trace:
                    trace.write('\n'.join(source_rows)+'\n')
                    if stage=='recoverable':
                        for fault in reversed(faults):
                            for req in fault['repair']: call(server, trace, req, started)
                    measure(server, run, trace, started)
            proofs[stage] = stage_proof(run, factorio)
        if proofs['broken']['production_pass'] or not proofs['broken']['verification_pass']:
            raise RuntimeError('Broken factory did not fail cleanly')
        if not proofs['recoverable']['scored_pass']:
            raise RuntimeError('Repair certificate failed')
        from repair_contract import RULES as REPAIR_RULES
        certificate = {'case_id':case_id, 'rules_hash':digest(REPAIR_RULES),
                       'broken_save_sha256':sha(case/'broken.zip'), 'initial_sha256':digest(initial),
                       'healthy':hp, **proofs}
        write(case/'certificate.json', certificate)
        write(case/'case.json', {'case_id':case_id, 'split':split, 'contract':'automatic-science-repair/1',
                                'rules_hash':digest(REPAIR_RULES), 'broken_save_sha256':sha(case/'broken.zip'),
                                'initial_sha256':digest(initial), 'certificate_sha256':sha(case/'certificate.json'),
                                'healthy_verified':True, 'broken_verified':True, 'recoverable_verified':True})
        write(case/'attempt.json', {**attempt, 'status':'certified', 'elapsed_seconds':time.monotonic()-started})
        return {'case_id':case_id, 'status':'certified', 'broken_save_sha256':sha(case/'broken.zip')}
    except BaseException as exc:
        write(case/'attempt.json', {**attempt, 'status':'setup_failed', 'error':str(exc), 'elapsed_seconds':time.monotonic()-started})
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command', required=True)
    b=sub.add_parser('build'); b.add_argument('--split', choices=['development','final'], required=True)
    b.add_argument('--count', type=int, required=True); b.add_argument('--output', type=Path, required=True)
    b.add_argument('--factorio', default=FACTORIO); b.add_argument('--start-index', type=int, default=0)
    args=p.parse_args()
    if not 1<=args.count or args.start_index<0 or args.start_index+args.count>(10 if args.split=='development' else 20): p.error('Invalid case count')
    args.output.mkdir(parents=True, exist_ok=True)
    for i in range(args.start_index, args.start_index+args.count):
        try:
            print(json.dumps(build_case(args.output, args.split, i, args.factorio)), flush=True)
        except BaseException:
            print(json.dumps({'case_id':f'{args.split}-{i+1:03d}', 'status':'setup_failed'}), flush=True)
            return 1
    return 0

if __name__=='__main__': raise SystemExit(main())
