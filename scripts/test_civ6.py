"""Verifier controls: synthetic traces use a real, separately checked start."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from civ6_verify import Invalid, check_start, digest, healthy_pairs, read_signed, verify, write_signed

EVIDENCE=Path(__file__).resolve().parents[1]/'evidence/civ6-economy-setup-2026-09-10'


class VerifierTests(unittest.TestCase):
    def setUp(self):
        self.start=json.loads((EVIDENCE/'start-state.json').read_text())
        self.profile=json.loads((EVIDENCE/'profile.json').read_text())
        self.end=copy.deepcopy(self.start)
        self.end['science']=20
        self.end['cities'] += [dict(self.end['cities'][0],key=f'{x}:12',x=x,id=x,population=3) for x in (25,38)]
        self.records=[dict(kind='start',state=copy.deepcopy(self.start),start_save_sha256=self.profile['start_save_sha256'],profile_sha256=digest(self.profile),method_sha256='a'*64,run_id='fixture')]
        self.records.append(dict(kind='begin',name='found_city',action_id=0))
        for x in (25,38):
            self.records.append(dict(kind='founded',owner=0,key=f'{x}:12',id=x))
        self.records.append(dict(kind='after_action',action_id=0,state=copy.deepcopy(self.end)))
        for turn in range(2,8):
            self.records.append(dict(kind='turn_end',state=copy.deepcopy(self.end)))
            self.end['turn']=turn
            self.records.append(dict(kind='boundary',state=copy.deepcopy(self.end)))
        self.records.append(dict(kind='finish',state=copy.deepcopy(self.end),terminal_save_sha256='b'*64,usage={'model_calls':0,'model_cost_usd':0}))
        self.retime()

    def retime(self):
        for n,r in enumerate(self.records): r['wall_seconds']=n

    def run_trace(self):
        return verify(self.records,self.start,self.end,self.profile,'b'*64)

    def change_states(self,fn):
        for r in self.records:
            if 'state' in r and r['kind']!='start': fn(r['state'])
        fn(self.end)

    def test_live_start_kit(self):
        self.assertEqual(check_start(self.start)['population'],4)
        self.assertFalse(healthy_pairs(self.start,check_start(self.start),{}))

    def test_six_boundaries_span_five_rounds(self):
        r=self.run_trace()
        self.assertTrue(r['goal_met']); self.assertEqual(r['longest_hold_rounds'],5)
        self.assertFalse(r['verified_pass'])

    def test_five_boundaries_are_insufficient(self):
        del self.records[-3:-1]
        self.end['turn']=6; self.records[-1]['state']['turn']=6
        self.retime(); self.assertFalse(self.run_trace()['goal_met'])

    def test_rounding_does_not_pass(self):
        self.change_states(lambda s:s.update(science=19.96))
        self.assertFalse(self.run_trace()['goal_met'])

    def test_negative_net_gold(self):
        self.change_states(lambda s:s.update(net_gold=-.001))
        self.assertFalse(self.run_trace()['goal_met'])

    def test_negative_balance(self):
        self.change_states(lambda s:s.update(gold=-.001))
        self.assertFalse(self.run_trace()['goal_met'])

    def test_food_surplus_not_food_production(self):
        self.change_states(lambda s:s['cities'][1].update(food_surplus=-.001))
        self.assertFalse(self.run_trace()['goal_met'])

    def test_population_two(self):
        self.change_states(lambda s:s['cities'][1].update(population=2))
        self.assertFalse(self.run_trace()['goal_met'])

    def test_zero_surplus_passes(self):
        self.change_states(lambda s:[c.update(food_surplus=0) for c in s['cities']])
        self.assertTrue(self.run_trace()['goal_met'])

    def test_nonfinite_rejected(self):
        for value in (float('nan'),float('inf'),True,None):
            with self.subTest(value=value):
                records=copy.deepcopy(self.records)
                self.records[5]['state']['science']=value
                with self.assertRaises(Invalid): self.run_trace()
                self.records=records

    def test_missing_field_rejected(self):
        del self.records[5]['state']['science']
        with self.assertRaises(KeyError): self.run_trace()

    def test_captured_city_does_not_count(self):
        self.records=[r for r in self.records if not (r['kind']=='founded' and r['key']=='25:12')]
        self.retime()
        with self.assertRaises(Invalid): self.run_trace()

    def test_capital_lost_then_returned_rejected(self):
        self.records.insert(7,dict(kind='removed',key=self.start['cities'][0]['key']))
        self.retime()
        with self.assertRaisesRegex(Invalid,'Capital lost'): self.run_trace()

    def test_replacement_city_rejected(self):
        self.change_states(lambda s:s['cities'][0].update(id=777))
        with self.assertRaises(Invalid): self.run_trace()

    def test_missing_boundary_rejected(self):
        del self.records[7]
        self.retime()
        with self.assertRaises(Invalid): self.run_trace()

    def test_bad_action_order_rejected(self):
        self.records[4]['action_id']=99
        with self.assertRaises(Invalid): self.run_trace()

    def test_unhealthy_between_boundaries_resets(self):
        s=copy.deepcopy(self.records[9]['state']); s['science']=19
        good=copy.deepcopy(self.records[9]['state'])
        self.records[9:9]=[dict(kind='begin',name='set_research',action_id=1),dict(kind='after_action',action_id=1,state=s),dict(kind='begin',name='set_research',action_id=2),dict(kind='after_action',action_id=2,state=good)]
        self.retime(); self.assertFalse(self.run_trace()['goal_met'])

    def test_reload_mismatch_rejected(self):
        self.end['gold']+=1
        with self.assertRaisesRegex(Invalid,'reload differs'): self.run_trace()

    def test_wrong_save_rejected(self):
        self.records[-1]['terminal_save_sha256']='c'*64
        with self.assertRaises(Invalid): self.run_trace()

    def test_unknown_usage_rejected(self):
        self.records[-1]['usage']['model_cost_usd']=None
        with self.assertRaises(Invalid): self.run_trace()

    def test_wall_limit_rejected(self):
        self.records[-1]['wall_seconds']=self.profile['max_wall_seconds']+1
        with self.assertRaises(Invalid): self.run_trace()

    def test_36th_turn_rejected(self):
        self.records=self.records[:-1]
        for turn in range(8,38):
            self.records.append(dict(kind='turn_end',state=copy.deepcopy(self.end)))
            self.end['turn']=turn
            self.records.append(dict(kind='boundary',state=copy.deepcopy(self.end)))
        self.records.append(dict(kind='finish',state=copy.deepcopy(self.end),terminal_save_sha256='b'*64,usage={'model_calls':0,'model_cost_usd':0}))
        self.retime()
        with self.assertRaisesRegex(Invalid,'Turn limit'): self.run_trace()

    def test_raw_lua_rejected(self):
        self.records[1]['name']='run_lua'
        with self.assertRaises(Invalid): self.run_trace()

    def test_changing_city_pair_cannot_combine_windows(self):
        self.records.insert(4,dict(kind='founded',owner=0,key='41:12',id=41))
        def change(s):
            s['cities'].append(dict(s['cities'][1],key='41:12',x=41,id=41,population=3 if s['turn']>=5 else 2))
            if s['turn']>=5: s['cities'][1]['population']=2
        self.change_states(change)
        self.retime();self.assertFalse(self.run_trace()['goal_met'])

    def test_preloaded_production_rejected(self):
        self.start['cities'][0]['stored_production']=[{'hash':1,'progress':1}]
        with self.assertRaises(Invalid): check_start(self.start)

    def test_changed_rules_rejected(self):
        self.records[5]['state']['ruleset']='RULESET_EXPANSION_2'
        with self.assertRaises(Invalid): self.run_trace()

    def test_repeated_start_rejected(self):
        self.records.insert(6,copy.deepcopy(self.records[0]));self.retime()
        with self.assertRaises(Invalid): self.run_trace()

    def test_signed_trace_tamper_and_truncation(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'trace.jsonl'; key=b'k'*32
            write_signed(path,self.records,key)
            self.assertEqual(read_signed(path,key),self.records)
            with self.assertRaises(Invalid): read_signed(path,b'x'*32)
            lines=path.read_text().splitlines()
            path.write_text('\n'.join(lines[:-1])+'\n')
            with self.assertRaises(Invalid): verify(read_signed(path,key),self.start,self.end,self.profile,'b'*64)
            path.write_text('\n'.join(lines).replace('"science":20','"science":21')+'\n')
            with self.assertRaises(Invalid): read_signed(path,key)


if __name__=='__main__': unittest.main()
