"""Native Factorio footage from retained evidence. Never a scored attempt.

Replays only recorded world-changing requests, with edited timing. It checks
each request outcome and final equipment geometry against the original run.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

from PIL import Image
from repair_host import action, install, start_case
from science_server import FACTORIO, Server
from search_recording import Recorder
from search_startup import StartupGate


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def geometry(snapshot):
    return sorted((e['name'], e['position']['x'], e['position']['y'], e['direction'],
                   e.get('recipe') if e['type'] == 'assembling-machine' else None)
                  for e in snapshot['entities'])


class DemoRecorder(Recorder):
    def __init__(self, *args, camera, **kwargs):
        super().__init__(*args, **kwargs)
        self.fps = 8
        self.camera = camera
        self.label = 'Saved action replay'

    def capture(self, label=None, timeout=10):
        with self.lock:
            self._remaining(timeout)
            index = self.next_frame
            self.next_frame += 1
            path = self.frames / f'frame-{index:06d}.jpg'
            x, y, zoom = self.camera
            started = time.time()
            code = ('game.take_screenshot{surface=game.surfaces[1],position={x=%s,y=%s},'
                    'resolution={1920,1080},zoom=%s,path="frames/%s",'
                    'show_gui=false,show_entity_info=true,force_render=true,quality=92}; '
                    'rcon.print(helpers.table_to_json({tick=game.tick,speed=game.speed,paused=game.tick_paused}))') % (x,y,zoom,path.name)
            state = json.loads(self.client.send_command('/sc '+code))
            until = time.time()+self._remaining(timeout)
            while time.time()<until:
                if path.exists():
                    content=path.read_bytes()
                    if content.startswith(b'\xff\xd8') and content.endswith(b'\xff\xd9'):
                        break
                time.sleep(.01)
            else:
                raise TimeoutError('Native demo image did not arrive')
            with Image.open(path) as picture:
                assert picture.size == (1920,1080)
                picture.verify()
            record={'frame':index,'label':label,'caption':self.label,'camera':self.camera,
                    'wall_requested':started,'wall_complete':time.time(),'game':state,
                    'path':str(path.relative_to(self.run)),'sha256':sha(path)}
            self.records.append(record)
            self.log.write(json.dumps(record)+'\n')
            if label in ('initial','final'):
                import shutil
                shutil.copyfile(path,self.output/f'{label}.jpg')
            return record

    def hold(self, seconds):
        for _ in range(round(seconds*self.fps)):
            started=time.monotonic()
            self.capture()
            time.sleep(max(0,1/self.fps-(time.monotonic()-started)))


def capture(case, trial, output, camera):
    case,trial,output=map(lambda p:Path(p).resolve(),(case,trial,output))
    output.mkdir(parents=True,exist_ok=False)
    sources={str(p):sha(p) for p in [case/'broken.zip',trial/'summary.json',trial/'review.json',
                                     trial/'host/actions.jsonl',trial/'host/record.json',trial/'host/game/world.zip']}
    records=[json.loads(line) for line in (trial/'host/actions.jsonl').read_text().splitlines()]
    changes=[r for r in records if r['request'].get('action') in {'place','pickup','rotate','recipe'}]
    expected=json.loads((trial/'host/record.json').read_text())['final']
    recorder=None
    result={'kind':'native visual action replay','scored':False,'new_model_calls':0,
            'timing':'Edited action timing; original benchmark times are not video times.',
            'observations_replayed':False,'finish_replayed':False,'source_hashes':sources,'actions':[]}
    deadline=time.time()+300
    gate=StartupGate(Path('runs/graphics-startup.lock'))
    try:
        gate.acquire(deadline)
        with Server(output/'game',rcon_port=27982,game_port=34982,save=case/'broken.zip') as server:
            initial=start_case(server,case)
            server.command('game.tick_paused=true; '
                           'remote.call("freeplay","set_disable_crashsite",true); '
                           'remote.call("freeplay","set_skip_intro",true); '
                           'remote.call("freeplay","set_created_items",{}); rcon.print("demo-paused")')
            result['spectator_setup']='Freeplay crash site, intro, and starter items disabled in demo copy before visual client joins.'
            recorder=DemoRecorder(output,FACTORIO,34982,27982,server.client.password,deadline,camera=camera)
            recorder.start_peer()
            # Lua globals are not part of the joined save. Install the same
            # functions after joining so both peers execute recorded actions.
            install(server)
            result['initial_equipment_matches']=geometry(server.read('science_snapshot()'))==geometry(initial)
            if not result['initial_equipment_matches']:
                raise RuntimeError('Joining the visual client changed factory equipment')
            gate.close()
            # Preserve the initial simulation interval before the first repair.
            # Missing machines can let inserters spill items that block placement.
            preroll=float(changes[0]['elapsed_seconds']) if changes else 0
            server.command('game.speed=20; game.tick_paused=false; rcon.print("preroll")')
            time.sleep(preroll)
            result['uncaptured_preroll_seconds']=preroll
            result['uncaptured_preroll_game_speed']=20
            server.command('game.speed=4; game.tick_paused=false; rcon.print("demo-speed")')
            recorder.label='Before repair'
            recorder.capture('initial',timeout=25)
            recorder.hold(2)
            for i,row in enumerate(changes):
                req=row['request']
                recorder.label=f"{i+1}/{len(changes)}: {req['action']} {req.get('item',req.get('name',''))}"
                if case.name=='final-003' and i==2:
                    recorder.camera=[-34.5,23.5,1.8]
                    recorder.hold(1)
                actual=action(server,req)
                matches=actual['ok']==row['response']['ok']
                result['actions'].append({'request':req,'original_elapsed_seconds':row['elapsed_seconds'],
                                          'expected_ok':row['response']['ok'],'replay_ok':actual['ok'],
                                          'frame_start':recorder.next_frame,'outcome_matches':matches})
                if not matches:
                    raise RuntimeError('Recorded request outcome differs in visual replay')
                recorder.hold(1.5 if len(changes)<6 else .75)
            current=server.read('science_snapshot()')
            result['final_equipment_matches']=geometry(current)==geometry(expected)
            if not result['final_equipment_matches']:
                raise RuntimeError('Final equipment differs from original retained trial')
            recorder.label='Recorded repairs complete; live production'
            recorder.hold(7)
            recorder.camera=[0,0,.25]
            recorder.label='Whole factory after recorded repairs'
            recorder.hold(4)
            result['capture']=recorder.close()
            result['capture'].update(mode='native Factorio visual action replay',replay=True,
                                     resolution=[1920,1080],jpeg_quality=92,nominal_capture_fps=8,playback_fps=8)
            (recorder.output/'recording.json').write_text(json.dumps(result['capture'],indent=2)+'\n')
            result['source_files_unchanged']=all(sha(Path(p))==h for p,h in sources.items())
            result['complete']=result['source_files_unchanged'] and result['capture']['complete']
    except BaseException as error:
        result['error']=f'{type(error).__name__}: {error}'
        if recorder and not recorder.closed:
            try: recorder.close()
            except Exception: pass
        raise
    finally:
        gate.close()
        (output/'demo.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'source_hashes','actions','capture'}},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',type=Path,required=True)
    parser.add_argument('--trial',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--camera',type=float,nargs=3,required=True)
    args=parser.parse_args()
    capture(args.case,args.trial,args.output,args.camera)
