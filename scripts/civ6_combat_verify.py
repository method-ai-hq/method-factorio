"""Combat task predicate and trace verifier. Live capture calibration required."""
from civ6_verify import require,integer,number,digest,cities,check_baseline_records


def roles(state):
    require(state['task_type']=='combat','Wrong task state')
    result={r['role']:r for r in state['role_states']}
    require(set(result)=={'home','second','target'} and len(state['role_states'])==3,'Missing or duplicate role')
    for r in result.values():
        require(type(r['exists']) is bool,'Missing role existence')
        if r['exists']:
            integer(r['owner']);integer(r['id']);integer(r['original_owner']);integer(r['population'])
            require(type(r['transfer_type']) is int,'Invalid transfer type')
    return result


def check_combat_start(state):
    own=cities(state); r=roles(state); me=state['player']
    require(len(own)==2 and all(c['population']==4 and c['owner']==me for c in own.values()),'Wrong starting cities')
    require(set(own)=={r['home']['key'],r['second']['key']},'Starting city roles differ')
    require(all(v['exists'] for v in r.values()),'Missing starting role city')
    require(r['target']['owner']!=me and r['target']['population']==4 and not r['target']['walls'],'Wrong target start')
    require(state['gold']==50 and state['turn']==1,'Wrong starting treasury or turn')
    require(sorted(u['type'] for u in state['units'])==['UNIT_BUILDER','UNIT_SLINGER','UNIT_SLINGER','UNIT_WARRIOR','UNIT_WARRIOR'],'Wrong army kit')
    require(next(u['charges'] for u in state['units'] if u['type']=='UNIT_BUILDER')==3,'Wrong builder kit')
    require(all(u['damage']==0 for u in state['units']),'Damaged starting army')
    require(set(state['technologies'])=={'TECH_MINING','TECH_POTTERY','TECH_ANIMAL_HUSBANDRY'},'Wrong starting research')
    require(not state['civics'] and not state['civic_progress'] and not state['research_progress'],'Stored research or civic progress')
    require(all(c['queue_size']==0 and c['food']==0 and not c['stored_production'] for c in own.values()),'Stored city progress')
    major=[p for p in state['players'] if p['major']]
    require(len(major)==2 and sum(p['human'] for p in major)==1,'Need one player and one built-in AI')
    require(state['cost_multiplier']==50 and state['multiplayer'] is False and state['tutorial_level']==-1,'Wrong runtime mode')
    require(state['ruleset']=='RULESET_STANDARD' and state['gathering_storm_loaded'] is False,'Wrong rules')
    require(state['combat_transfer_code']==-1173539618,'Unexpected transfer enum; revalidate the installed game')
    return r


def retained(state,start_roles):
    r=roles(state); me=state['player']
    for name in ('home','second'):
        require(r[name]['exists'] and (r[name]['key'],r[name]['owner'],r[name]['id'])==
                (start_roles[name]['key'],me,start_roles[name]['id']),'Starting city lost or replaced')
    return r


def combat_goal(state,start_roles,captured_id):
    r=retained(state,start_roles)['target']
    return (captured_id is not None and r['exists'] and r['key']==start_roles['target']['key']
            and r['owner']==state['player'] and r['id']==captured_id
            and r['original_owner']==start_roles['target']['original_owner']
            and r['transfer_type']==state['combat_transfer_code'])


def verify_combat(records,start,reloaded,profile,terminal_hash):
    initial=check_combat_start(start)
    require(profile['task_type']=='combat' and profile['status']=='calibration','Wrong combat profile')
    require(profile['max_completed_turns']==30 and profile['hold_rounds']==5,'Changed task thresholds')
    require(digest(start)==profile['start_state_sha256'],'Wrong starting state')
    require(records[0]['kind']=='start' and records[-1]['kind']=='finish','Incomplete trace')
    header,finish=records[0],records[-1]
    require(header['state']==start and header['profile_sha256']==digest(profile),'Wrong starting profile')
    require(header['start_save_sha256']==profile['start_save_sha256'],'Wrong starting save')
    require(len(header['method_sha256'])==64 and bool(header['run_id']),'Missing run identity')
    require(finish['state']==reloaded and finish['terminal_save_sha256']==terminal_hash,'Independent final save differs')
    records=check_baseline_records(records,finish,profile)
    require(all(r['kind'] not in {'start','finish'} for r in records[1:-1]),'Repeated endpoint record')
    turn=start['turn']; ended=False; action=None; action_name=None
    actions=0; captured_id=None; streak=None; longest=0; last_wall=0; last_state=start
    for rec in records:
        wall=number(rec['wall_seconds']); require(last_wall<=wall<=profile['max_wall_seconds'],'Clock order or limit');last_wall=wall
        kind=rec['kind']
        require(kind in {'start','finish','begin','after_action','turn_end','turn_blocked','boundary','role_added','role_removed'},'Unknown combat record')
        if kind=='begin':
            require(action is None and not ended,'Overlapping action')
            action=integer(rec['action_id']); require(action==actions,'Missing action')
            actions+=1;require(actions<=profile['max_actions'],'Action limit')
            action_name=rec['name'];require(action_name in profile['allowed_actions'],'Unapproved action')
        elif kind=='after_action':
            require(action is not None and action==rec['action_id'],'Unmatched action');action=None;action_name=None
        elif kind=='turn_end':
            require(action is None and not ended,'Bad end-turn order');ended=True
        elif kind=='turn_blocked':
            require(ended and action is None and not rec['blocking']['processing'] and not rec['blocking']['sent'],'Invalid blocked turn');ended=False
        elif kind=='boundary':
            require(ended and action is None,'Missing turn-end request');ended=False;turn+=1
            require(turn-start['turn']<=30,'Turn limit exceeded')
        elif kind=='role_removed':
            name=rec['role'];require(name in initial and rec['key']==initial[name]['key'],'Unknown role removal')
            if name in ('home','second') and rec['owner']==start['player']:
                require(False,'Starting city removed')
            if name=='target' and rec['owner']==start['player']:
                captured_id=None;streak=None
        elif kind=='role_added':
            name=rec['role'];require(name in initial and rec['key']==initial[name]['key'],'Unknown added role')
            if name=='target' and rec['owner']==start['player']:
                require(action_name in {'attack','move'} or ended,'Capture lacks a player combat or queued-movement action')
                require(rec['transfer_type']==start['combat_transfer_code'],'Target was not acquired through combat')
                require(rec['original_owner']==initial['target']['original_owner'],'Target replaced')
                captured_id=integer(rec['id']);streak=None
        elif kind=='finish':
            require(action is None and not ended,'Unfinished action or turn')
        if kind in {'start','finish','after_action','turn_end','turn_blocked','boundary'}:
            state=rec['state'];require(state['turn']==turn and state['player']==start['player'],'Wrong turn or player')
            for field in ('ruleset','speed','map_seed','game_seed','active_mods','tutorial_level','quick_combat','quick_movement','auto_end_turn','multiplayer','combat_transfer_code'):
                require(state[field]==start[field],'Runtime configuration changed')
            r=retained(state,initial)
            require(all(r[name]['key']==initial[name]['key'] for name in initial),'Role location changed')
            if not combat_goal(state,initial,captured_id): streak=None
            elif kind=='boundary': streak=0 if streak is None else streak+1
            longest=max(longest,streak or 0);last_state=state
    require(last_state==reloaded,'Terminal state mismatch')
    won=streak is not None and streak>=5
    return {'status':'calibration_goal_met' if won else 'goal_not_met','goal_met':won,'verified_pass':False,
            'completed_turns':turn-start['turn'],'hold_rounds':streak or 0,'longest_hold_rounds':longest,
            'actions':actions,'wall_seconds':last_wall,'limit':'Live capture fixtures and legal reference certification are required.'}
