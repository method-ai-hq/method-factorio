"""Run a fixed panel with serial startup and bounded, explicit fault recovery."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from search_startup import recovery_decision, write_status
from search_trial import freeze_valid

ROOT = Path(__file__).resolve().parents[1]


def disk_usage(job):
    roots = [job] + list((ROOT / "runs").glob(job.name + "-*"))
    total = 0
    vanished = 0
    for root in roots:
        for directory, _, names in os.walk(root):
            for name in names:
                try:
                    total += (Path(directory) / name).stat().st_size
                except FileNotFoundError:
                    # Factorio removes its temporary save tree during shutdown.
                    # A vanished file occupies no space; other errors still fail.
                    vanished += 1
    return {"new_bytes": total, "free_bytes": shutil.disk_usage(ROOT).free,
            "vanished_temporary_files": vanished,
            "maximum_new_bytes": 20 * 1024**3, "minimum_free_bytes": 10 * 1024**3}


def read(path):
    return json.loads(path.read_text()) if path.exists() else {}


def run_panel(panel, job, scheduling, concurrency, cutoff, deadline, retry_authorized,
              final_panel=False, cancelled=lambda: False, worker_command=None,
              storage_check=disk_usage, recording_mode="native"):
    """worker_command is a test seam; the CLI always uses the real trial runner."""
    scheduling.mkdir(parents=True, exist_ok=False)
    pending = [{'ordinal': i, 'case': case, 'attempt': 1} for i, case in enumerate(panel)]
    active, results, events = {}, [], []
    capacity = concurrency
    stop_reason = None
    environment = {k: v for k, v in os.environ.items()
                   if k not in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'OPENAI_BASE_URL')}
    def save_pending():
        write_status(scheduling / 'pending.json', pending=pending)
        write_status(scheduling / 'active.json', active=[row for _,_,row in active.values()])
    try:
        while pending or active:
            if cancelled() or time.time() >= deadline-3:
                stop_reason = 'supervisor_stop' if cancelled() else 'job_deadline'
                break
            for lane, (process, log, row) in list(active.items()):
                if process.poll() is None:
                    continue
                log.close()
                status = read(Path(row['status_file']))
                record = status.get('record', {'infrastructure_failure': {
                    'phase':'runner', 'code':'missing_trial_result'}})
                results.append({**row, 'returncode':process.returncode, 'record':record})
                del active[lane]
                decision = recovery_decision(record, row['attempt'], retry_authorized and capacity>1)
                if decision == 'retry_serial' and stop_reason is None:
                    capacity = 1
                    replacement = {key:row[key] for key in ('ordinal','case')}
                    replacement.update(attempt=2, replacement_for=row['status_file'])
                    pending.insert(0, replacement)
                elif decision == 'repair_required':
                    stop_reason = 'repair_required'
                if decision != 'continue':
                    events.append({'decision':decision, 'ordinal':row['ordinal'],
                                   'attempt':row['attempt'], 'capacity':capacity,
                                   'failure':record['infrastructure_failure'], 'at':time.time()})
                    write_status(scheduling / 'recovery.json', events=events)
            write_status(scheduling / 'completed.json', results=results)
            if not active and (stop_reason or not pending):
                break
            # Do not start another world until the previous world has an initial
            # frame and is accepting policy actions. No batches of cold starts.
            starting = recording_mode == 'native' and any(read(Path(row['status_file'])).get('phase') not in ('playing','finished')
                           for _,_,row in active.values())
            if pending and len(active)<capacity and not starting and stop_reason is None:
                if time.time() >= cutoff or deadline-time.time()<330:
                    stop_reason = 'new_trial_deadline'
                    continue
                usage = storage_check(job)
                write_status(scheduling / 'storage.json', **usage)
                if usage['new_bytes']>=usage['maximum_new_bytes'] or usage['free_bytes']<usage['minimum_free_bytes']:
                    stop_reason = 'storage_limit'
                    continue
                index = job / 'index.jsonl'
                count = sum(1 for line in index.read_text().splitlines()
                            if json.loads(line).get('kind') in ('development','baseline','final','demonstration')) if index.exists() else 0
                if count+len(active) >= (120 if final_panel else 116):
                    stop_reason = 'reserved_trial_cap'
                    continue
                row = pending.pop(0)
                lane = next(i for i in range(1, concurrency+1) if i not in active)
                status_file = scheduling / f"trial-{row['ordinal']:03d}-attempt-{row['attempt']}.json"
                row.update(lane=lane, concurrency=capacity, status_file=str(status_file), started_at=time.time())
                if worker_command:
                    command = worker_command(row, status_file)
                else:
                    command = [sys.executable, str(ROOT/'scripts/search_trial.py'),
                               '--job-dir',str(job),'--deadline',str(deadline),'--lane',str(lane),
                               '--concurrency',str(capacity),
                               '--status-file',str(status_file)]
                    for name in ('policy','case','seed','map_x','map_y','kind'):
                        command += ['--'+name.replace('_','-'),str(row['case'][name])]
                    if row['case'].get('source_trial'):
                        command += ['--source-trial',str(row['case']['source_trial'])]
                log = status_file.with_suffix('.log').open('w')
                try:
                    process = subprocess.Popen(command,cwd=ROOT,env=environment,stdout=log,stderr=log)
                except BaseException:
                    log.close()
                    pending.insert(0,row)
                    raise
                row['pid'] = process.pid
                active[lane] = process, log, row
                save_pending()
            save_pending()
            if active:
                time.sleep(.05)
    finally:
        for process, log, row in active.values():
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=max(.1,min(25,deadline-time.time())))
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            log.close()
            results.append({**row,'returncode':process.returncode,
                            'record':read(Path(row['status_file'])).get('record'),
                            'interrupted':True})
        active.clear()
        save_pending()
        summary = {'started':len(results),'completed':sum(not r.get('interrupted') for r in results),
                   'stop_reason':stop_reason,'results':results,'pending':pending,
                   'recovery_events':events,'final_concurrency':capacity,'deadline_epoch':deadline}
        write_status(scheduling/'summary.json',**summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--job-dir',type=Path,required=True)
    parser.add_argument('--panel',type=Path,required=True)
    parser.add_argument('--concurrency',type=int,default=2)
    parser.add_argument('--search-deadline',type=float,required=True)
    parser.add_argument('--deadline',type=float,required=True)
    parser.add_argument('--final-panel',action='store_true')
    parser.add_argument('--schedule-name', help='Unique local record name for another panel')
    args = parser.parse_args()
    if not 1<=args.concurrency<=8:
        parser.error('Concurrency must be 1 to 8')
    if args.schedule_name and (Path(args.schedule_name).name != args.schedule_name
                              or args.schedule_name in ('.', '..')):
        parser.error('Schedule name must be a single directory name')
    job = args.job_dir.resolve()
    freeze = read(job/'benchmark-freeze.json')
    if not freeze_valid(freeze):
        parser.error('The tested benchmark must be approved and its source hashes unchanged')
    settings = freeze.get('settings',{})
    if args.concurrency > settings.get('validated_concurrent_worlds',0):
        parser.error('Requested concurrency exceeds the tested level in the fixed settings')
    panel = json.loads(args.panel.read_text())
    if not isinstance(panel,list):
        parser.error('The panel must be an array')
    if args.final_panel and (len(panel)!=4 or any(p['kind']!='final' for p in panel)):
        parser.error('Final panel must contain the four reserved final trials')
    if not args.final_panel and any(p['kind']=='final' for p in panel):
        parser.error('Use --final-panel for final trials')
    stopped = False
    def cancel(*_):
        nonlocal stopped
        stopped = True
    signal.signal(signal.SIGINT,cancel)
    signal.signal(signal.SIGTERM,cancel)
    summary = run_panel(panel,job,job/(args.schedule_name or ('final-schedule' if args.final_panel else 'search-schedule')),
                        args.concurrency,args.deadline-330 if args.final_panel else args.search_deadline,
                        args.deadline,settings.get('startup_recovery')=='one_serial_replacement',
                        final_panel=args.final_panel,cancelled=lambda:stopped,
                        recording_mode=settings.get("recording_mode","native"))
    print(json.dumps({'started':summary['started'],'stop_reason':summary['stop_reason'],
                      'pending':len(summary['pending'])}))
    return 1 if summary['pending'] or summary['stop_reason'] else 0


if __name__=='__main__':
    raise SystemExit(main())
