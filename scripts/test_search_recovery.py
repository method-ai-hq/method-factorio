"""Control tests with small fake workers. No game, recording, or API calls."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from search_startup import StartupFailure, StartupGate, client_stage, recovery_decision
from search_schedule import run_panel
from search_trial import headless_evidence_complete

WORKER = '''import json,pathlib,sys,time
p=pathlib.Path(sys.argv[1]); ordinal=int(sys.argv[2]); attempt=int(sys.argv[3]); mode=sys.argv[4]
def write(x):
 t=p.with_suffix('.tmp'); t.write_text(json.dumps(x)); t.replace(p)
start=time.time();write({'phase':'startup'});time.sleep(.07)
fail=ordinal==0 and (mode=='fail_always' or mode=='fail_once' and attempt==1)
if fail:
 record={'infrastructure_failure':{'phase':'startup','code':'graphics_loading_timeout'},'start':start,'end':time.time()}
else:
 ready=time.time();write({'phase':'playing'});time.sleep(.18)
 record={'infrastructure_failure':None,'start':start,'ready':ready,'end':time.time()}
write({'phase':'finished','record':record})
'''

class StartupTests(unittest.TestCase):
    def test_stage_diagnosis(self):
        self.assertEqual(client_stage('Parallel sprite loader initialized'),'loading_graphics')
        self.assertEqual(client_stage('Sprites loaded'),'joining_server')
        self.assertEqual(client_stage('changing state to(InGame)'),'connected')

    def test_lock_timeout_and_release(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=StartupGate(Path(d)/'lock'),StartupGate(Path(d)/'lock')
            a.acquire(time.time()+1)
            with self.assertRaises(StartupFailure):b.acquire(time.time()+.03)
            a.close();b.acquire(time.time()+1);b.close()

    def test_process_exit_releases_lock(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'lock'
            subprocess.run([sys.executable,'-c',
                'import fcntl,os,sys;f=open(sys.argv[1],"w");fcntl.flock(f,fcntl.LOCK_EX);os._exit(0)',str(path)],check=True)
            gate=StartupGate(path);gate.acquire(time.time()+1);gate.close()

    def test_retry_requires_authorization_and_first_attempt(self):
        r={'infrastructure_failure':{'phase':'startup','code':'graphics_loading_timeout'}}
        self.assertEqual(recovery_decision(r,1,False),'repair_required')
        self.assertEqual(recovery_decision(r,1,True),'retry_serial')
        self.assertEqual(recovery_decision(r,2,True),'repair_required')
        r['infrastructure_failure']['code']='client_exited'
        self.assertEqual(recovery_decision(r,1,True),'repair_required')
        self.assertEqual(recovery_decision({'infrastructure_failure':None},1,True),'continue')

class SchedulerTests(unittest.TestCase):
    def panel(self,mode='ok',authorized=False,recording_mode='native',cutoff=None):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        root=Path(self.directory.name);worker=root/'worker.py';worker.write_text(WORKER)
        def command(row,status):return [sys.executable,str(worker),str(status),str(row['ordinal']),str(row['attempt']),mode]
        return run_panel([{'case':str(i)} for i in range(3)],root,root/'schedule',2,
                         cutoff if cutoff is not None else time.time()+500,time.time()+600,authorized,
                         worker_command=command,recording_mode=recording_mode)
    def test_native_starts_are_serial_but_play_can_overlap(self):
        r=self.panel();self.assertEqual(r['started'],3)
        records=[x['record'] for x in r['results']]
        self.assertGreaterEqual(records[1]['start'],records[0]['ready'])
        self.assertLess(records[1]['start'],records[0]['end'])
    def test_headless_startup_can_overlap(self):
        r=self.panel(recording_mode='none')
        records=[x['record'] for x in r['results']]
        self.assertLess(records[1]['start'],records[0]['ready'])
    def test_recovery_keeps_failure_and_retries_once(self):
        r=self.panel('fail_once',True)
        self.assertEqual(r['started'],4);self.assertEqual(r['final_concurrency'],1)
        self.assertFalse(r['pending']);self.assertIsNone(r['stop_reason'])
        self.assertEqual(r['results'][1]['attempt'],2)
        self.assertTrue(r['results'][0]['record']['infrastructure_failure'])
    def test_repeated_failure_keeps_unstarted_work(self):
        r=self.panel('fail_always',True)
        self.assertEqual(r['started'],2);self.assertEqual(len(r['pending']),2)
        self.assertEqual(r['stop_reason'],'repair_required')
    def test_no_unauthorized_retry(self):
        r=self.panel('fail_once',False)
        self.assertEqual(r['started'],1);self.assertEqual(len(r['pending']),2)
    def test_cutoff_prevents_launch(self):
        r=self.panel(cutoff=time.time()-1)
        self.assertEqual(r['started'],0);self.assertEqual(len(r['pending']),3)

class EvidenceTests(unittest.TestCase):
    def test_headless_requires_saved_game_and_trace(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for name in ('initial.json','final.json','settings.json','actions.jsonl','measurement.json',
                         'action-summary.json','game/final.zip','host-timing.json','save-inspection/result.json'):
                f=p/name;f.parent.mkdir(exist_ok=True);f.write_text('{}')
            (p/'settings.json').write_text('{"recording_mode":"none"}')
            (p/'recording-mode.json').write_text('{"graphical_client_started":false}')
            self.assertTrue(headless_evidence_complete(p))
            (p/'game/final.zip').unlink();self.assertFalse(headless_evidence_complete(p))

if __name__=='__main__':unittest.main()
