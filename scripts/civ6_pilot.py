"""Offline authoring, selection, and reports for the fixed Civ pilot."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

from civ6_baseline import task_text
from civ6_codex import run_codex
from civ6_verify import canonical,digest

ROOT=Path(__file__).resolve().parents[1]
JOB=ROOT/'runs/civ6-pilot-20260910'
DOC=ROOT/'docs/civ6/pilot-20260910'
METHODS=ROOT/'methods/civ6/pilot-20260910'


def read(path):
    return json.loads(path.read_text())


def trial_summary(run, detail=False):
    result=read(run/'result.json') if (run/'result.json').exists() else {'status':'pending'}
    terminal=read(run/'terminal.json') if (run/'terminal.json').exists() else {}
    profile=read(run/'profile.json')
    execution=terminal.get('execution') or {}
    summary={'run_id':run.name,'pilot':profile.get('pilot'),'result':result,
        'play_seconds':terminal.get('play_seconds'),'requests':terminal.get('requests'),
        'usage':execution.get('usage'),'execution_status':execution.get('status'),
        'subscription_cost_usd':None,'api_calls':execution.get('api_calls')}
    if execution.get('status')=='operator_cutoff':summary['comparison_eligible']=False
    else:summary['comparison_eligible']=result['status'] in ('calibration_goal_met','goal_not_met')
    if detail:
        records=[json.loads(line) for line in (run/'capture.jsonl').read_text().splitlines()]
        requests=[r['request'] for r in records if r['kind']=='request']
        summary['request_counts']=dict(Counter(r['action'] for r in requests))
        summary['decisions']=[r for r in requests if r['action'] in ('production','research','civic','policies','purchase','improve','harvest','remove_feature','focus','found')]
        summary['boundaries']=[]
        for rec in records:
            if rec['kind']!='boundary':continue
            s=rec['state']
            summary['boundaries'].append({'turn':s['turn'],'science':s['science'],'gold':s['gold'],'net_gold':s['net_gold'],
                'cities':[{k:c[k] for k in ('key','population','food_surplus','production','science')} for c in s['cities']]})
        summary['rejections']=[r['response'] for r in records if r['kind']=='response' and not r['response'].get('ok',True)]
        final=run/'astra/final.txt'
        if final.exists():summary['actor_final']=final.read_text()[:7000]
    return summary


def author(version):
    lock=read(DOC/'lock.json')
    if version not in (2,3):raise ValueError('Use this command for revisions 2 and 3')
    if time.time()>=lock['stop_unix']-120:raise RuntimeError('Not enough job time for authoring')
    previous=METHODS/f'v{version-1}.md'
    source=JOB/f'search-v{version-1}'
    summary=trial_summary(source,True)
    if summary['result']['status']=='pending':raise RuntimeError('Previous trial has no checked result')
    profile=read(ROOT/lock['base_profile'])
    task=f'''You are the offline author of Civ economy Method v{version}. No game endpoint is available.
Write your improved Method to method.md in this workspace. Use only this task.
Do not play the game, call other agents/models, or read other paths.
The Method goes to a fresh Astra actor that must make live decisions with LLM reasoning.
Study the supplied previous Method and actual trial evidence. Improve the slowest
cause of delay or failure. Keep useful steps. Aim to satisfy the exact task sooner
with fewer tokens and requests. Do not change the task or execution budget.
Use only the documented API. Avoid fixed coordinates, engine IDs, or a recorded
action sequence. Keep the Method below 650 words. Use conditional decisions based
on observed state and estimated completion time. Do not assume untested mechanics.
Preserve the full five-round hold. A connection fault is not a gameplay failure.
The selection rule is success, fewer completed turns, fewer requests, then playing time.
Also write changes.md with a short explanation tied to the actual evidence.

PREVIOUS METHOD:
{previous.read_text()}

ACTUAL TRIAL EVIDENCE:
{json.dumps(summary,indent=2)}

PLAYER TASK AND API:
{task_text(profile)}
'''
    path=JOB/f'author-v{version}-task.md'
    with path.open('x') as f:f.write(task)
    output=JOB/f'author-v{version}'
    execution=run_codex(task,output,None,min(90,lock['stop_unix']-time.time()-30))
    candidate=output/'workspace/method.md'
    if execution['status']!='completed' or not candidate.is_file() or candidate.is_symlink():
        raise RuntimeError('Author did not complete a regular Method file')
    content=candidate.read_bytes()
    if not content.strip() or len(content)>32000:raise ValueError('Invalid Method length')
    with (METHODS/f'v{version}.md').open('xb') as f:f.write(content)
    changes=output/'workspace/changes.md'
    if changes.is_file() and not changes.is_symlink():
        with (METHODS/f'v{version}-changes.md').open('xb') as f:f.write(changes.read_bytes())
    print(json.dumps({'version':version,'method_sha256':hashlib.sha256(content).hexdigest(),
                      'author_seconds':execution['wall_seconds'],'usage':execution['usage']},indent=2))


def freeze():
    lock=read(DOC/'lock.json')
    trials=[trial_summary(JOB/f'search-v{v}') for v in (1,2,3)]
    eligible=[s for s in trials if s['comparison_eligible']]
    if not eligible:raise RuntimeError('No valid candidate trial to select')
    def rank(s):
        r=s['result']
        return (not r['goal_met'],r['completed_turns'],s['requests'],s['play_seconds'])
    best=min(eligible,key=rank)
    version=best['run_id'].split('-')[-1]
    method=METHODS/f'{version}.md'
    frozen={'lock_sha256':digest(lock),'frozen_unix':time.time(),'selected_version':version,
        'method_path':str(method.relative_to(ROOT)),'method_sha256':hashlib.sha256(method.read_bytes()).hexdigest(),
        'selection_rule':lock['selection_order'],'development_trials':trials}
    if frozen['method_sha256']!=best['pilot']['method_sha256']:
        raise RuntimeError('Candidate Method changed since its trial')
    with (DOC/'frozen.json').open('xb') as f:f.write(canonical(frozen))
    print(json.dumps({'selected_version':version,'method_sha256':frozen['method_sha256']},indent=2))


def report():
    trials=[trial_summary(p) for p in sorted(JOB.iterdir()) if p.is_dir() and (p/'profile.json').exists()]
    authors=[]
    for p in sorted(JOB.glob('author-v*/execution.json')):
        e=read(p);authors.append({'run_id':p.parent.name,'status':e['status'],'wall_seconds':e['wall_seconds'],
            'usage':e.get('usage'),'subscription_cost_usd':None,'api_calls':e['api_calls']})
    result={'lock':read(DOC/'lock.json'),'trials':trials,'authors':authors,
            'supervisor_cost_usd':None,'supervisor_tokens':None,'scope':'same_map_calibration_pilot'}
    (JOB/'summary.json').write_bytes(canonical(result))
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('author','freeze','report'))
    p.add_argument('--version',type=int)
    a=p.parse_args()
    if a.action=='author':author(a.version)
    elif a.action=='freeze':freeze()
    else:report()
