"""Astra-authored geometry controller. Uses only the restricted playing API."""
import json
import math
import sys
import time
import urllib.request

options = json.load(sys.stdin)
endpoint = options['endpoint']
mode = options.get('mode', 'short')
started = time.monotonic()
trace = []
state = {}

def action(name, **fields):
    global state
    if time.monotonic()-started > 180:
        raise RuntimeError('Policy time limit reached')
    body = {'action': name, **fields}
    request = urllib.request.Request(endpoint, json.dumps(body).encode(), {'Content-Type':'application/json'})
    with urllib.request.urlopen(request, timeout=25) as response:
        result = json.load(response)
    trace.append({'action':body, 'ok':result.get('ok'), 'error':result.get('error')})
    if isinstance(result.get('state'), dict):
        state = result['state']
    if not result.get('ok'):
        raise RuntimeError(str(result.get('error', result)))
    return result.get('result')

def entities(name):
    return [e for e in state.get('entities',[]) if e.get('name') == name]

def observed(name):
    candidates = entities(name)
    if not candidates:
        action('observe')
        candidates = entities(name)
    if not candidates:
        raise RuntimeError('Missing observed entity '+name)
    return candidates[-1]

def target(entity):
    return {'name':entity['name'], 'position':entity['position']}

def point_add(p, v, scale=1):
    return {'x':p['x']+v[0]*scale, 'y':p['y']+v[1]*scale}

def cardinal(p,q):
    dx,dy=q['x']-p['x'],q['y']-p['y']
    return (1 if dx>0 else -1,0) if abs(dx)>abs(dy) else (0,1 if dy>0 else -1)

def direction(v):
    return {(1,0):'RIGHT',(-1,0):'LEFT',(0,1):'DOWN',(0,-1):'UP'}[v]

def distance(a,b):
    return abs(a['x']-b['x'])+abs(a['y']-b['y'])

def place(name,p,v,exact=True):
    action('place',item=name,position=p,direction=direction(v),exact=exact)
    return observed(name)

def fuel(e,count):
    inserted=action('insert',item='coal',quantity=count,target=target(e))
    if not isinstance(inserted,dict) or inserted.get('inserted',0)<count:
        raise RuntimeError('Fuel insertion was incomplete for '+e['name'])

def build():
    iron=action('nearest',resource='iron-ore')
    if isinstance(iron,dict) and 'position' in iron:
        iron=iron['position']
    player=state['position']
    dx,dy=iron['x']-player['x'],iron['y']-player['y']
    reach=8.0
    length=math.hypot(dx,dy)
    if length>reach:
        action('move',position={'x':iron['x']-dx*reach/length,'y':iron['y']-dy*reach/length})
    preferred=cardinal(iron,player)
    drill=place('burner-mining-drill',iron,preferred,False)
    faults=[]
    for orientation in [preferred]+[v for v in [(1,0),(0,1),(-1,0),(0,-1)] if v!=preferred]:
        try:
            if orientation != preferred:
                action('rotate',target=target(drill),direction=direction(orientation))
            drill=observed('burner-mining-drill')
            vector=cardinal(drill['position'],drill['drop_position'])
            belt=place('transport-belt',drill['drop_position'],vector)
            inserter=place('burner-inserter',point_add(belt['position'],vector),vector)
            if distance(inserter['pickup_position'],belt['position'])>.25:
                action('rotate',target=target(inserter),direction=direction((-vector[0],-vector[1])))
                inserter=observed('burner-inserter')
            if distance(inserter['pickup_position'],belt['position'])>.25:
                raise RuntimeError('Inserter pickup mismatch')
            furnace=place('stone-furnace',point_add(inserter['drop_position'],vector,.5),vector)
            drop=inserter['drop_position']
            box=furnace['box']
            if not (box['left_top']['x']<=drop['x']<=box['right_bottom']['x'] and box['left_top']['y']<=drop['y']<=box['right_bottom']['y']):
                raise RuntimeError('Inserter drop does not enter the observed furnace')
            plates_before=state.get('iron_plates_produced',0)
            for machine, count in [(furnace,3),(inserter,2),(drill,4)]:
                fuel(machine,count)
            time.sleep(.3)
            for check_number in range(12):
                action('observe')
                if state.get('iron_plates_produced',0)>plates_before:
                    break
                time.sleep(.15)
            else:
                raise RuntimeError('No new iron plate observed in the bounded startup check')
            return 'Built route after '+str(len(faults))+' failed directions. Faults: '+str(faults)
        except Exception as error:
            if 'not allowed' in str(error):
                raise
            faults.append(str(error))
            action('observe')
            # Recover the supplied downstream kit before trying a new ray.
            # This uses observed entities and preserves machine contents.
            for name in ['stone-furnace','burner-inserter','transport-belt']:
                for entity in list(entities(name)):
                    action('pickup',target=target(entity))
    raise RuntimeError('All four downstream directions failed: '+str(faults))

ready=False
try:
    report=build()
    ready=True
except Exception as error:
    report='Controller stopped: '+str(error)
    try:
        action('observe')
    except Exception:
        pass
try:
    action('finish')
except Exception as error:
    ready=False
    report+=' Finish response: '+str(error)
print(json.dumps({'report':report+' Trace: '+json.dumps(trace),'ready':ready}))
