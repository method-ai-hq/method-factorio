"""Build the local index and reviewed report for the stopped 2026-09-10 job."""
import hashlib
import html
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[1]
JOB=ROOT/'runs/search-v3-20260910'
EVIDENCE=ROOT/'evidence/policy-search-v3-2026-09-10'

def read(path,default=None):return json.loads(path.read_text()) if path.exists() else default

def main():
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    audit=read(ROOT/'runs/recording-smoke-01/capture-audit.json')
    rows=[]
    for i,x in enumerate(audit['episodes'][:4],1):
        rows.append({'episode':i,'kind':'recording setup','run':str(ROOT/x['path']),'outcome':x['outcome'],'reason':x.get('reason'),'policy':None,'recording_complete':x['evidence_complete'],'frames':x['native_frame_count'],'video':str(ROOT/x['path']/x['video']) if x.get('video') else None,'source_audit':str(ROOT/'runs/recording-smoke-01/capture-audit.json')})
    for num,name in [(5,'search-v3-smoke-working'),(6,'search-v3-smoke-working-02')]+[(x['episode_number'],Path(x['run']).name) for x in read(JOB/'negative-checks.json')]:
        run=ROOT/'runs'/name
        rec=read(run/'recording/recording.json',{})
        paths={'video':run/rec.get('video','missing'),'action_trace':run/'actions.jsonl','state':run/'final.json','initial_state':run/'initial.json','settings':run/'settings.json','verdict':run/'production-verdict.json','measurements':run/'measurement.json','save':run/'game/final.zip','save_inspection':run/'save-inspection/result.json','recording':run/'recording/recording.json','capture_times':run/'recording/frames.jsonl','host_timing':run/'host-timing.json'}
        row={'episode':num,'kind':'operator reference setup' if num==6 else 'failed setup','run':str(run),'policy':None,'outcome':'working reference production passed; not scored' if num==6 else 'infrastructure failure','reason':None if num==6 else 'Initial image timeout' if num==5 else 'Graphical peer did not join within 60 seconds','frames':rec.get('frames',0),'recording_complete':rec.get('complete',False)}
        row.update({key:str(path) if path.is_file() else None for key,path in paths.items()})
        row['missing_artifacts']=[key for key in paths if row[key] is None]
        rows.append(row)
    all_json=JOB/'setup-index.json';all_json.write_text(json.dumps(rows,indent=2)+'\n')
    (JOB/'index.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    policies=read(ROOT/'policies/search-v3/index.json')
    summary={'status':'setup stopped; scoring not approved','job_started_utc':'2026-09-10T16:17:12Z','setup_stopped_utc':'2026-09-10T16:30:28Z','hard_deadline_utc':'2026-09-10T17:17:12Z','stop_reason':'All 12 allowed setup episodes were used. The six negative reference attempts failed graphical peer startup.','candidate_policies':11,'baseline_policies':2,'validated_method_documents':13,'scored_trials':0,'development_trials':0,'final_trials':0,'winning_policy':None,'measured_policy_improvement':False,'setup_episodes':12,'recording_complete_episodes':sum(r['recording_complete'] for r in rows),'videos_including_incomplete':sum(bool(r.get('video')) for r in rows),'native_frames':sum(r['frames'] for r in rows),'maximum_concurrent_reference_worlds_attempted':6,'concurrent_recording_worlds_validated':2,'jpeg_live_validated':False,'working_reference':{'kind':'operator-authored fixture, not a candidate policy','ore_per_window':[5,5,5],'plates_per_window':[5,5,5],'warmup_ticks':600,'window_ticks':1200,'save_reload_passed':True,'recording_complete':True,'speed':20,'thinking_paused':False},'validation':{'public_runtime_tests_passed':40,'evaluator_predicate_tests_passed':8,'negative_live_checks_completed':0,'evaluator_approved':False},'cost':{'policy_execution_api_requests':0,'policy_execution_api_cost_usd':0,'setup_api_requests':3,'setup_api_input_tokens':442,'setup_api_output_tokens':43,'setup_api_known_estimate_usd':0.00657,'policy_design_and_supervision':'Codex subscription; metered token and dollar cost unknown','search_execution_cost':'No policy search trial ran','basis':'Standard public API rates; estimate, not invoice'},'maps':{'development_proposal':[{'seed':61001,'patch':[16,0]},{'seed':61002,'patch':[-18,8]},{'seed':61003,'patch':[6,-20]}],'development_maps_frozen':False,'final_maps_opened':False,'final_maps_frozen':False,'terrain':'Declared grass area from -64 to64, 9x9 iron patch with 1000 ore per tile, natural terrain outside. Only first development setup was exercised.'},'limits':{'total_job_minutes':60,'setup_minutes':15,'setup_episode_cap':12,'scored_trial_cap':120,'policy_cap':32,'data_cap_gib':20,'free_disk_minimum_gib':10},'setup_outcomes':[{'episode':r['episode'],'outcome':r['outcome'],'recording_complete':r['recording_complete'],'frames':r['frames']} for r in rows]}
    (EVIDENCE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    for source,target in [(ROOT/'runs/search-v3-smoke-working-02/production-verdict.json',EVIDENCE/'reference-production.json'),(ROOT/'runs/search-v3-smoke-working-02/save-inspection/result.json',EVIDENCE/'reference-save-inspection.json')]:
        target.write_text(source.read_text())
    source_paths=['scripts/search_host.py','scripts/automatic_evaluator.py','scripts/search_recording.py','scripts/search_inspect.py','scripts/search_validation_faults.py','docs/automatic-production-evaluator.md','scripts/method3_run.py','scripts/method3_game_tool.py','scripts/method3_compute.py']
    freeze={'approved_for_scoring':False,'reason':summary['stop_reason'],'sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths},'settings':{'maximum_recording_gap_seconds':1,'speed':20,'trial_seconds':300,'close_seconds':30,'actions':200,'model_requests':60},'validation':str(EVIDENCE/'summary.json')}
    (JOB/'benchmark-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
    (EVIDENCE/'source-hashes.json').write_text(json.dumps(freeze,indent=2)+'\n')
    job=read(JOB/'job.json');job.update(status='stopped_setup_limit',scored_trials=0,setup_episodes=12,stopped_new_work_at_utc='2026-09-10T16:30:28Z');(JOB/'job.json').write_text(json.dumps(job,indent=2)+'\n')
    def link(path,label):return f'<a href="{html.escape(path,quote=True)}">{html.escape(label)}</a>' if path else '<span class="missing">Missing</span>'
    trs=[]
    for r in rows:
        trs.append('<tr>'+''.join('<td>'+v+'</td>' for v in [str(r['episode']),html.escape(r['kind']),html.escape(r['outcome']),str(r['frames']),link(r.get('video'),'Play'),link(r.get('action_trace'),'Actions'),link(r.get('capture_times'),'Frames'),link(r.get('verdict'),'Verdict'),link(r.get('save'),'Save'),link(r.get('save_inspection'),'Inspection'),link(r['run'],'Folder')])+'</tr>')
    htmltext='''<!doctype html><meta charset="utf-8"><title>Factorio Method v3 — setup results</title><style>body{font:16px system-ui;margin:40px;color:#19242c;background:#f7f7f3}h1{font-size:30px}p{max-width:950px;line-height:1.5}table{border-collapse:collapse;background:white;width:100%;font-size:14px}td,th{padding:12px;text-align:left;border-bottom:1px solid #ddd}a{color:#155f85}.missing{color:#888}.status{border-left:5px solid #b35b2b;padding:12px;background:#fff0e5}</style><h1>Factorio × Method v3</h1><p class="status"><b>Setup stopped. No scored trials. No selected policy.</b><br>12 setup episodes used. Six parallel game clients failed to join within 60 seconds. Negative live evaluator checks remain incomplete.</p><p>11 candidate Methods and 2 baseline Methods passed validation. The operator reference produced 5 new plates and 5 new ore in each of 3 windows. Its save reload agreed. This result is an environment check.</p><p>Actual game recordings use speed 20, about 2 frames per wall-clock second. Missing evidence remains marked below. The earlier images use PNG; the later JPEG recorder has not passed a live check.</p>'''
    htmltext+='<p>'+link(str(ROOT/'policies/search-v3/README.md'),'Frozen policy designs')+' · '+link(str(EVIDENCE/'summary.json'),'Reviewed summary')+' · '+link(str(all_json),'Full local index')+'</p>'
    htmltext+='<table><thead><tr>'+''.join('<th>'+x+'</th>' for x in ['Episode','Type','Outcome','Frames','Video','Actions','Times','Verdict','Save','Reload','All files'])+'</tr></thead><tbody>'+''.join(trs)+'</tbody></table>'
    htmltext+='<p>Known setup API estimate: $0.00657 for 3 requests. Policy execution cost: $0 because no policy ran. Codex authoring and supervision cost is unknown. Raw game files remain local.</p>'
    (JOB/'index.html').write_text(htmltext)
    print(json.dumps({'index':str(JOB/'index.html'),'episodes':len(rows),'scored_trials':0,'videos':summary['videos_including_incomplete']}))

if __name__=='__main__':main()
