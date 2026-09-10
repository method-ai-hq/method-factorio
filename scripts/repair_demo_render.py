"""Make a silent 60-second presentation and labeled native replay clips."""
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'runs/repair-demo-20260910'
OUT=RUN/'presentation'
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
BG='#10181d'
FG='#f2f4ed'
MUTED='#aab7bc'
ACCENT='#b6ed72'


def text(draw,xy,value,size=40,color=FG,bold=False):
    draw.multiline_text(xy,value,font=ImageFont.truetype(BOLD if bold else FONT,size),
                        fill=color,spacing=18)


def canvas(name,headline=None,subtitle=None,transparent=False):
    im=Image.new('RGBA',(1920,1080),(0,0,0,0) if transparent else BG)
    d=ImageDraw.Draw(im)
    if transparent:
        d.rectangle((0,0,1920,190),fill=(10,18,23,232))
        d.rectangle((0,986,1920,1080),fill=(10,18,23,242))
    d.rectangle((72,54,126,62),fill=ACCENT)
    text(d,(148,42),'METHOD / FACTORIO',25,MUTED,True)
    if headline: text(d,(72,91),headline,48,FG,True)
    if subtitle: text(d,(72,1016),subtitle,26,MUTED)
    return im,d,OUT/f'{name}.png'


def save_overlay(name,headline):
    im,d,p=canvas(name,headline,'NATIVE FACTORIO ACTION REPLAY  /  EDITED TIMING  /  GAME SPEED 4x',True)
    im.save(p)
    return p


def run(cmd,log):
    with (OUT/log).open('w') as stream:
        subprocess.run(cmd,stdout=stream,stderr=stream,check=True,timeout=120)


def video_segment(name,source,seconds,overlay=None,start=0):
    out=OUT/f'{name}.mp4'
    cmd=['ffmpeg','-hide_banner','-nostdin','-y','-ss',str(start),'-i',str(source)]
    if overlay:
        cmd+=['-loop','1','-i',str(overlay),'-filter_complex','[0:v]fps=30,setsar=1[v];[v][1:v]overlay=0:0:shortest=1[out]','-map','[out]']
    else:
        cmd+=['-vf','fps=30,setsar=1']
    cmd+=['-t',str(seconds),'-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
    run(cmd,f'{name}.log')
    return out


def still_segment(name,source,seconds):
    out=OUT/f'{name}.mp4'
    run(['ffmpeg','-hide_banner','-nostdin','-y','-loop','1','-framerate','30','-i',str(source),
         '-t',str(seconds),'-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p',str(out)],f'{name}.log')
    return out


def duration(path):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)],text=True))


def main():
    OUT.mkdir(parents=True,exist_ok=False)
    quick=RUN/'quick-repair-4/recording/video.mp4'
    recovery=RUN/'furnace-recovery-2/recording/video.mp4'
    for run_root in [quick.parents[1],recovery.parents[1]]:
        proof=json.loads((run_root/'demo.json').read_text())
        assert proof['complete'] and proof['initial_equipment_matches'] and proof['final_equipment_matches']
        assert proof['source_files_unchanged'] and all(x['outcome_matches'] for x in proof['actions'])
    overlays={
        'motive':save_overlay('motive','Can Astra improve how it works?'),
        'experiment':save_overlay('experiment','10 practice factories  >  Freeze Method  >  20 unseen factories'),
        'procedure':save_overlay('procedure','Code prepares the map. Astra diagnoses and repairs.'),
        'takeaway':save_overlay('takeaway','Practice. Improve the procedure. Reuse it.'),
        'quick-label':save_overlay('quick-label','Recorded repair: add a drill, turn a belt, turn an inserter'),
        'recovery-label':save_overlay('recovery-label','Recorded recovery: blocked furnace placements, then a new route'),
    }
    im,d,p=canvas('search',subtitle='PRACTICE RESULTS / MEDIAN FULL SUCCESSFUL TIME / EACH SHOWN VERSION TESTED ON 10 CASES')
    text(d,(72,125),'The search learned to simplify.',74,FG,True)
    for x,version,lines,score in [(72,'v01','3 fresh agent stages\nInspect > repair > check','215 s'),
                                (706,'v02','Compact belts\n+ 1 agent session','92 s'),
                                (1340,'v04','Compact full map\n+ 1 agent session','73 s')]:
        d.rounded_rectangle((x,315,x+510,815),radius=18,fill='#1a272d')
        text(d,(x+32,349),version,32,ACCENT,True)
        text(d,(x+32,433),lines,34)
        text(d,(x+32,624),score,94,FG,True)
    text(d,(72,891),'v03: one retained test; corrected v04 completed all ten.',32,MUTED)
    im.save(p); search=p
    im,d,p=canvas('results',subtitle='TIME: SAME 18 SUCCESSFUL PAIRS, INCLUDING VERIFICATION / INPUT: ALL 20 ATTEMPTS, INCLUDING CACHE')
    text(d,(72,125),'Same model. New factories.',74,FG,True)
    text(d,(76,308),'DIRECT ASTRA',32,MUTED,True)
    text(d,(76,380),'93 s',140,FG,True)
    text(d,(690,308),'SEARCHED METHOD',32,ACCENT,True)
    text(d,(690,380),'71 s',140,ACCENT,True)
    text(d,(1350,321),'56%',132,ACCENT,True)
    text(d,(1350,494),'fewer input\ntokens',44)
    d.line((72,665,1848,665),fill='#40535b',width=2)
    text(d,(72,731),'About 23% less full time',58,FG,True)
    text(d,(72,831),'Search and authoring costs are separate.',34,MUTED)
    im.save(p); results=p
    im,d,p=canvas('honesty',subtitle='20 FINAL CASES / THIS SAMPLE DOES NOT ESTABLISH A GENERAL RELIABILITY GAIN')
    text(d,(72,137),'Both repaired every factory.',78,FG,True)
    text(d,(72,300),'20 / 20',160,ACCENT,True)
    text(d,(76,523),'factories repaired by each approach',45)
    text(d,(76,689),'Full rules: Method 20/20   |   Direct Astra 18/20',46,FG,True)
    text(d,(76,801),'Two direct runs made unsupported tool requests.\nTheir factories still worked.',38,MUTED)
    im.save(p); honesty=p
    segments=[video_segment('01-motive',quick,8,overlays['motive']),
              video_segment('02-experiment',recovery,12,overlays['experiment']),
              still_segment('03-search',search,9),
              video_segment('04-procedure',recovery,7,overlays['procedure'],12),
              still_segment('05-results',results,13),
              still_segment('06-honesty',honesty,6),
              video_segment('07-takeaway',recovery,5,overlays['takeaway'],duration(recovery)-5)]
    concat=OUT/'segments.txt'; concat.write_text(''.join(f"file '{p.name}'\n" for p in segments))
    final=OUT/'factorio-method-60s.mp4'
    run(['ffmpeg','-hide_banner','-nostdin','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(final)],'concat.log')
    labeled_quick=video_segment('quick-repair-labeled',quick,duration(quick),overlays['quick-label'])
    labeled_recovery=video_segment('furnace-recovery-labeled',recovery,duration(recovery),overlays['recovery-label'])
    assert abs(duration(final)-60)<.1
    outputs=[final,labeled_quick,labeled_recovery]
    manifest={'duration_seconds':duration(final),'audio':'none; record your own narration','resolution':[1920,1080],
              'native_capture_fps':8,'video_fps':30,'footage':'Native action replay, game speed 4, edited action timing.',
              'outputs':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'seconds':duration(p),'bytes':p.stat().st_size} for p in outputs}}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
