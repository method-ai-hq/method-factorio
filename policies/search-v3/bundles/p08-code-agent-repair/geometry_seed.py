"""Astra-authored geometry controller. Uses only the restricted playing API."""
import json
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
    action('insert',item='coal',quantity=count,target=target(e))

def build():
    action('observe')
    iron = action('nearest',resource='iron-ore')
    if isinstance(iron,dict) and 'position' in iron:
        iron=iron['position']
    action('move',position=iron)
    drill=place('burner-mining-drill',iron,(1,0),False)
    drop=drill.get('drop_position')
    if not drop:
        raise RuntimeError('Drill has no observed drop position')
    vector=cardinal(drill['position'],drop)
    fuel(drill,70)
    belt=place('transport-belt',drop,vector)
    if mode in ('long','elbow'):
        belt=place('transport-belt',point_add(belt['position'],vector),vector)
    if mode=='elbow':
        vector=(-vector[1],vector[0])
        action('rotate',target=target(belt),direction=direction(vector))
        belt=place('transport-belt',point_add(belt['position'],vector),vector)
    inserter=place('burner-inserter',point_add(belt['position'],vector),vector)
    pickup=inserter.get('pickup_position')
    if pickup is None:
        raise RuntimeError('Inserter has no observed pickup position')
    if distance(pickup,belt['position'])>.25:
        action('rotate',target=target(inserter),direction=direction((-vector[0],-vector[1])))
        inserter=observed('burner-inserter')
    if distance(inserter['pickup_position'],belt['position'])>.25:
        raise RuntimeError('Inserter pickup does not match belt')
    # A two-tile furnace can receive at either tile. Its intended near edge
    # contains the observed drop point while its far edge extends downstream.
    furnace=place('stone-furnace',point_add(inserter['drop_position'],vector,.5),vector)
    fuel(inserter,30)
    fuel(furnace,50)
    action('observe')
    return 'Constructed using observed drill drop and inserter pickup/drop positions.'

try:
    report=build()
except Exception as error:
    report='Controller stopped: '+str(error)
    try:
        action('observe')
    except Exception:
        pass
print(json.dumps({'seed_report':report+' Trace: '+json.dumps(trace)}))
