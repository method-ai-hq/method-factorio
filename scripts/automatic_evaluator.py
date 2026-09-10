"""Exact-tick supplied-kit evaluator. Administration is never a playing tool.

This file must pass live reference checks and be frozen before scored use.
"""
import json
import time

KIT = {'burner-mining-drill': 1, 'stone-furnace': 1, 'burner-inserter': 1,
       'transport-belt': 10, 'coal': 150}
SNAPSHOT_FUNCTION = r'''
function benchmark_snapshot()
 local c=storage.agent_characters[1]; local s=c.surface
 local function inv(i) return i and i.get_contents() or {} end
 local entities={}; local furnaces={}; local ore=0
 for _,e in pairs(s.find_entities_filtered{name="iron-ore"}) do ore=ore+e.amount end
 for _,e in pairs(s.find_entities_filtered{force=c.force}) do
  if e.type=="furnace" or e.type=="mining-drill" or e.type=="inserter" or e.type=="transport-belt" then
   local q={id=e.unit_number,name=e.name,type=e.type,position=e.position,direction=e.direction,status=e.status,
    fuel=inv(e.get_fuel_inventory()),box=e.bounding_box}
   if e.type=="furnace" then q.products_finished=e.products_finished;
    q.input=inv(e.get_inventory(defines.inventory.furnace_source));
    q.output=inv(e.get_inventory(defines.inventory.furnace_result)); table.insert(furnaces,q) end
   if e.type=="inserter" or e.type=="mining-drill" then q.drop_position=e.drop_position end
   if e.type=="inserter" then q.pickup_position=e.pickup_position;
    q.held=e.held_stack.valid_for_read and {name=e.held_stack.name,count=e.held_stack.count} or {} end
   if e.type=="mining-drill" then q.mining_target=e.mining_target and {position=e.mining_target.position,name=e.mining_target.name} or nil end
   if e.type=="transport-belt" then q.lines={inv(e.get_transport_line(1)),inv(e.get_transport_line(2))};
    q.outputs={}; for _,b in pairs(e.belt_neighbours.outputs) do table.insert(q.outputs,b.unit_number) end end
   table.insert(entities,q)
  end
 end
 local research={}; for n,t in pairs(c.force.technologies) do if t.researched then table.insert(research,n) end end
 return {tick=game.tick,speed=game.speed,paused=game.tick_paused,position=c.position,
 inventory=inv(c.get_main_inventory()),entities=entities,furnaces=furnaces,research=research,
 iron_plates_produced=c.force.get_item_production_statistics(s).get_input_count("iron-plate"),
 iron_ore_remaining=ore,enemies=#s.find_entities_filtered{force="enemy"}}
end
'''
SNAPSHOT = 'rcon.print(helpers.table_to_json(benchmark_snapshot()))'

def count(items, name):
    if isinstance(items, dict):
        return items.get(name, 0)
    return sum(x['count'] for x in items if x['name'] == name)

def contains(entity, point):
    if not point:
        return False
    box = entity['box']
    a, b = box['left_top'], box['right_bottom']
    return a['x'] <= point['x'] <= b['x'] and a['y'] <= point['y'] <= b['y']

def route(state):
    es = state['entities'] or []
    drills = [e for e in es if e['type'] == 'mining-drill']
    belts = {e['id']: e for e in es if e['type'] == 'transport-belt'}
    inserters = [e for e in es if e['type'] == 'inserter']
    furnaces = [e for e in es if e['type'] == 'furnace']
    for drill in drills:
        queue = [(b['id'], [b['id']]) for b in belts.values() if contains(b, drill.get('drop_position'))]
        seen = set()
        while queue:
            bid, path = queue.pop(0)
            if bid in seen: continue
            seen.add(bid)
            for inserter in inserters:
                if contains(belts[bid], inserter.get('pickup_position')):
                    for furnace in furnaces:
                        if contains(furnace, inserter.get('drop_position')):
                            return {'connected': True, 'drill': drill['id'], 'belts': path,
                                    'inserter': inserter['id'], 'furnace': furnace['id']}
            queue.extend((b, path + [b]) for b in belts[bid].get('outputs', []) if b in belts)
    return {'connected': False}

def measure(client, deadline):
    """Capture four exact boundaries with the game's own on_tick callback."""
    client.send_command('/sc storage.benchmark_measure={start=game.tick, samples={}}; '
        'script.on_event(defines.events.on_tick,function(event) '
        'local m=storage.benchmark_measure; local d=event.tick-m.start; '
        'if d==600 or d==1800 or d==3000 or d==4200 then '
        'table.insert(m.samples,benchmark_snapshot()); end; '
        'if d==4200 then game.tick_paused=true; m.done=true end end)')
    while time.time() < deadline:
        raw = client.send_command('/sc rcon.print(helpers.table_to_json(storage.benchmark_measure))')
        data = json.loads(raw)
        if data.get('done'): return data
        time.sleep(.05)
    raise TimeoutError('production verdict deadline reached')

def verdict(initial, measurement, *, legal_actions, unchanged_bundle, evidence_complete,
            independent_save_agrees, within_limits):
    states = measurement.get('samples', [])
    boundaries = [s['tick'] - measurement['start'] for s in states]
    windows = []
    for a,b in zip(states, states[1:]):
        fa = {f['id']:f for f in a.get('furnaces', [])}
        fb = {f['id']:f for f in b.get('furnaces', [])}
        connection = route(a)
        fid = connection.get('furnace')
        output = count(fb.get(fid,{}).get('output',[]),'iron-plate') - count(fa.get(fid,{}).get('output',[]),'iron-plate')
        products = fb.get(fid,{}).get('products_finished',0) - fa.get(fid,{}).get('products_finished',0)
        plates = b['iron_plates_produced'] - a['iron_plates_produced']
        ore = a['iron_ore_remaining'] - b['iron_ore_remaining']
        checks = {'exact_1200_ticks':b['tick']-a['tick']==1200,'route':connection['connected'] and route(b)==connection,
                  'five_output':output>=5,'five_products':products>=5,'five_game_plates':plates>=5,'five_new_ore':ore>=5}
        windows.append({'from_tick':a['tick'],'to_tick':b['tick'],'output_delta':output,
                        'products_delta':products,'game_plates_delta':plates,'ore_depletion':ore,
                        'route':connection,'checks':checks,'passed':all(checks.values())})
    initial_inventory = {n:count(initial.get('inventory',[]),n) for n in KIT}
    other = sum(x['count'] for x in initial.get('inventory',[]) if x['name'] not in KIT) if isinstance(initial.get('inventory'),list) else sum(v for k,v in initial.get('inventory',{}).items() if k not in KIT)
    checks = {'initial_kit':initial_inventory==KIT and other==0,
              'initial_empty':not initial.get('entities') and not initial.get('research') and initial.get('enemies')==0 and initial.get('iron_plates_produced')==0,
              'fixed_settings':initial.get('speed')==20 and not initial.get('paused') and all(s.get('speed')==20 for s in states),
              'exact_boundaries':boundaries==[600,1800,3000,4200],
              'three_windows':len(windows)==3 and all(w['passed'] for w in windows),
              'legal_actions':bool(legal_actions),'unchanged_bundle':bool(unchanged_bundle),'within_limits':bool(within_limits)}
    production = all(checks.values())
    return {'production_success':production,'scored_pass':production and evidence_complete and independent_save_agrees,
            'checks':checks,'windows':windows,'evidence_complete':bool(evidence_complete),
            'independent_save_agrees':bool(independent_save_agrees),'failure_penalty_seconds':330}
