#!/usr/bin/env python3
"""Exact economy predicate and protected trace checker. No game mutations.

The command checks operator evidence; it does not turn a policy-written JSON
file into evidence. Keys, saves, and the capture process must be inaccessible
to the playing Method. The current profile remains in calibration.
"""
from __future__ import annotations
import argparse
import hashlib
import hmac
import itertools
import json
import math
from pathlib import Path


class Invalid(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise Invalid(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def number(value):
    require(type(value) in (int, float) and math.isfinite(value), 'Missing or non-finite number')
    return value


def integer(value):
    require(type(value) is int and value >= 0, 'Invalid nonnegative integer')
    return value


def cities(state):
    require(state['schema'] == 'civ6-state/1', 'Wrong state schema')
    integer(state['player']); integer(state['turn'])
    for field in ('science', 'gold', 'net_gold'):
        number(state[field])
    result = {}
    for c in state['cities']:
        require(c['key'] == f"{integer(c['x'])}:{integer(c['y'])}", 'Invalid city tile')
        require(c['key'] not in result, 'Duplicate city tile')
        integer(c['id']); integer(c['owner']); integer(c['population'])
        number(c['food_surplus'])
        result[c['key']] = c
    return result


def healthy_pairs(state, capital, births):
    rows = cities(state)
    cap = rows.get(capital['key'])
    if not cap or (cap['id'], cap['owner']) != (capital['id'], state['player']):
        return set()
    if min(state['gold'], state['net_gold'], cap['food_surplus']) < 0 or state['science'] < 20:
        return set()
    eligible = []
    for key, birth in births.items():
        c = rows.get(key)
        if c and key != capital['key'] and (c['id'], c['owner']) == (birth['id'], state['player']) and c['population'] >= 3 and c['food_surplus'] >= 0:
            eligible.append(key)
    return set(itertools.combinations(sorted(eligible), 2))


def check_start(state):
    rows = cities(state)
    require(len(rows) == 1, 'Start must have one city')
    cap = next(iter(rows.values()))
    require(cap['population'] == 4 and cap['owner'] == state['player'], 'Wrong capital population or owner')
    require(state['gold'] == 50, 'Wrong starting treasury')
    require(state['leader'] == 'LEADER_TRAJAN' and state['civilization'] == 'CIVILIZATION_ROME', 'Wrong leader')
    require(state['cost_multiplier'] == 50 and state['multiplayer'] is False, 'Wrong speed or mode')
    require(state['no_barbarians'] is True and state['no_huts'] is True, 'Random encounters enabled')
    require(state['disaster_intensity'] == 0, 'Disasters enabled')
    require([p['id'] for p in state['players'] if p['major']] == [state['player']], 'Unexpected major player')
    require(all(p['id'] in (state['player'], 63) for p in state['players']), 'Unexpected minor player')
    require(state['auto_end_turn'] == 0 and state['quick_combat'] == 1 and state['quick_movement'] == 1, 'Wrong runtime preferences')
    require(state['tutorial_level']==-1, 'Advisor tutorial can block unattended turns')
    require(set(state['technologies']) == {'TECH_MINING','TECH_POTTERY','TECH_ANIMAL_HUSBANDRY'}, 'Wrong starting technology')
    require(not state['civics'] and not state['civic_progress'] and not state['research_progress'], 'Unexpected research or civic progress')
    require(cap['queue_size'] == 0 and cap['food'] == 0 and not cap['stored_production'], 'Preloaded city progress')
    require({b['type'] for b in cap['buildings']} == {'BUILDING_PALACE','BUILDING_MONUMENT'}, 'Unexpected starting building')
    require([d['type'] for d in cap['districts']] == ['DISTRICT_CITY_CENTER'], 'Unexpected district')
    require(sorted(u['type'] for u in state['units']) == ['UNIT_BUILDER','UNIT_SCOUT','UNIT_WARRIOR'], 'Wrong starting units')
    require(next(u['charges'] for u in state['units'] if u['type']=='UNIT_BUILDER') == 3, 'Wrong builder charges')
    require(all(u['damage'] == 0 for u in state['units']), 'Damaged starting units')
    require(all(p['policy'] == -1 for p in state['policies']) and state['era']==0, 'Wrong starting era or policies')
    return cap


def write_signed(path, records, key):
    """Operator utility. Never give this function/key to the playing process."""
    require(len(key) >= 32, 'Signing key too short')
    previous = '0'*64
    with Path(path).open('x') as out:
        for seq, record in enumerate(records):
            row = {'seq': seq, 'previous': previous, 'record': record}
            row['mac'] = hmac.new(key, canonical(row), hashlib.sha256).hexdigest()
            previous = row['mac']
            out.write(canonical(row).decode()+'\n')


def read_signed(path, key):
    require(len(key) >= 32, 'Signing key too short')
    previous = '0'*64
    records = []
    for seq, line in enumerate(Path(path).read_text().splitlines()):
        row = json.loads(line)
        mac = row.pop('mac')
        require(row['seq'] == seq and row['previous'] == previous, 'Broken trace order')
        expected = hmac.new(key, canonical(row), hashlib.sha256).hexdigest()
        require(hmac.compare_digest(mac, expected), 'Trace authentication failed')
        previous = mac
        records.append(row['record'])
    require(len(records) >= 3, 'Incomplete trace')
    return records


def verify(records, start, reloaded, profile, terminal_save_sha256):
    """Input must come from the protected recorder and independent save reader.

    A boundary is emitted by PlayerTurnActivated. Every submitted command has
    begin/end records, and every end-turn request has a pre-turn snapshot.
    City births/removals are engine events, never statements by the policy.
    """
    cap = check_start(start)
    require(digest(start) == profile['start_state_sha256'], 'Wrong starting state hash')
    require(start['ruleset'] == profile['ruleset'] and start['gathering_storm_loaded'] == profile['gathering_storm_loaded'], 'Wrong loaded rules')
    require((profile['max_completed_turns'],profile['hold_rounds'],profile['minimum_science'],profile['new_city_population']) == (35,5,20,3), 'Unsupported task thresholds')
    require(records[0]['kind'] == 'start' and records[-1]['kind'] == 'finish', 'Missing start or finish')
    header, finish = records[0], records[-1]
    require(all(r['kind'] not in {'start','finish'} for r in records[1:-1]), 'Repeated start or finish')
    require(header['state'] == start and header['start_save_sha256'] == profile['start_save_sha256'], 'Wrong initial save/state')
    require(header['profile_sha256'] == digest(profile), 'Wrong profile')
    require(isinstance(header['run_id'], str) and bool(header['run_id']), 'Missing run identity')
    require(len(header['method_sha256']) == 64, 'Missing Method hash')
    require(finish['terminal_save_sha256'] == terminal_save_sha256, 'Wrong final save')
    require(finish['state'] == reloaded, 'Independent reload differs')
    require(integer(finish['usage']['model_calls']) == 0 and number(finish['usage']['model_cost_usd']) == 0, 'This calibration profile permits no model calls')
    require(profile['status'] == 'calibration', 'Unreviewed profile status')
    births, streaks = {}, {}
    initial_turn = start['turn']
    turn, last_wall, action, ended = initial_turn, 0, None, False
    action_count, boundaries, longest = 0, 0, 0
    last_state = start
    seen_tiles = set(cities(start))
    for rec in records:
        wall = number(rec['wall_seconds'])
        require(last_wall <= wall <= profile['max_wall_seconds'], 'Wall clock order or limit')
        last_wall = wall
        kind = rec['kind']
        require(kind in {'start','begin','after_action','turn_end','boundary','founded','removed','finish'}, 'Unknown trace record')
        if kind == 'begin':
            require(action is None and not ended, 'Overlapping or post-turn action')
            action = integer(rec['action_id'])
            require(action == action_count, 'Missing action')
            require(rec['name'] in profile['allowed_actions'], 'Unapproved action')
            action_count += 1
            require(action_count <= profile['max_actions'], 'Action budget exceeded')
        elif kind == 'after_action':
            require(action is not None and rec['action_id'] == action, 'Unmatched action')
            action = None
        elif kind == 'founded':
            require(action is not None and integer(rec['owner']) == start['player'], 'Unattributed city founding')
            require(rec['key'] not in seen_tiles, 'Reused city site or initial city')
            integer(rec['id'])
            births[rec['key']] = {'id':rec['id']}
            seen_tiles.add(rec['key'])
        elif kind == 'removed':
            require(rec['key'] != cap['key'], 'Capital lost')
            births.pop(rec['key'], None)
            streaks = {pair:n for pair,n in streaks.items() if rec['key'] not in pair}
        elif kind == 'turn_end':
            require(action is None and not ended, 'Bad turn-end order')
            ended = True
        elif kind == 'boundary':
            require(action is None and ended, 'Boundary lacks closed action or turn-end checkpoint')
            ended = False
            turn += 1
            boundaries += 1
            require(turn-initial_turn <= 35, 'Turn limit exceeded')
        elif kind == 'finish':
            require(action is None and not ended, 'Unfinished action or turn')
        if kind in {'start','after_action','turn_end','boundary','finish'}:
            state = rec['state']
            rows = cities(state)
            require(state['turn'] == turn and state['player'] == start['player'], 'Missing boundary or wrong player')
            for field in ('ruleset','speed','active_mods','map_seed','game_seed','gathering_storm_loaded','tutorial_level','quick_movement','quick_combat','auto_end_turn','no_huts','no_barbarians','multiplayer'):
                require(state[field] == start[field], 'Game configuration changed')
            require(cap['key'] in rows and (rows[cap['key']]['id'],rows[cap['key']]['owner']) == (cap['id'],start['player']), 'Capital lost or replaced')
            require(set(rows) <= {cap['key']} | set(births), 'City has no trusted founding event')
            healthy = healthy_pairs(state, cap, births)
            streaks = {pair:n for pair,n in streaks.items() if pair in healthy}
            if kind in {'start','boundary'}:
                streaks = {pair:streaks[pair]+1 if pair in streaks else 0 for pair in healthy}
                longest = max([longest, *streaks.values()])
            last_state = state
    require(last_state == reloaded, 'Terminal state mismatch')
    pairs = [list(pair) for pair,n in streaks.items() if n >= 5]
    terminal_rows=cities(reloaded)
    terminal={'science':reloaded['science'],'gold':reloaded['gold'],
              'net_gold':reloaded['net_gold'],'capital_food_surplus':terminal_rows[cap['key']]['food_surplus'],
              'new_self_founded_cities':[{'key':key,'population':terminal_rows[key]['population'],
                                        'food_surplus':terminal_rows[key]['food_surplus']}
                                       for key in sorted(births) if key in terminal_rows]}
    return {'status':'calibration_goal_met' if pairs else 'goal_not_met',
            'verified_pass':False, 'goal_met':bool(pairs), 'qualifying_pairs':pairs,
            'longest_hold_rounds':longest,'completed_turns':boundaries,
            'actions':action_count,'wall_seconds':last_wall,
            'terminal':terminal,
            'limit':'Scored use needs a reviewed action broker and calibration certificate.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start',type=Path,required=True)
    p.add_argument('--trace',type=Path)
    p.add_argument('--key-file',type=Path)
    p.add_argument('--profile',type=Path)
    p.add_argument('--reloaded',type=Path)
    p.add_argument('--terminal-save',type=Path)
    args=p.parse_args()
    try:
        state=json.loads(args.start.read_text())
        if not args.trace:
            cap=check_start(state)
            result={'status':'starting_kit_valid','capital':cap['key'],'verified_pass':False}
        else:
            require(all((args.key_file,args.profile,args.reloaded,args.terminal_save)), 'Missing evidence argument')
            result=verify(read_signed(args.trace,args.key_file.read_bytes()),state,
                          json.loads(args.reloaded.read_text()),json.loads(args.profile.read_text()),
                          hashlib.sha256(args.terminal_save.read_bytes()).hexdigest())
    except (Invalid, KeyError, TypeError, ValueError, OSError) as error:
        print(json.dumps({'status':'invalid_evidence','verified_pass':False,'reason':str(error)}))
        return 2
    print(json.dumps(result,indent=2,allow_nan=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
