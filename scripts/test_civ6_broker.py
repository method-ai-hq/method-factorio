"""Boundary checks for data-to-Lua input and baseline trace validation."""
import unittest
from civ6_broker import validate,lua
from civ6_verify import Invalid,digest
import test_civ6


class PlayerBoundary(unittest.TestCase):
    def test_admin_and_code_are_rejected(self):
        for a in ({'action':'lua','code':'print(1)'},{'action':'load','name':'save'},
                  {'action':'research','type':'TECH_WRITING"); print(1)'},
                  {'action':'rules','table':'Players'},
                  {'action':'move','unit_id':1,'x':0,'y':0,'code':'bad'},
                  {'action':'unit_command','unit_id':1,'command':'DELETE'}):
            with self.subTest(a=a),self.assertRaises(ValueError): validate(a)

    def test_invalid_coordinates_and_policies(self):
        for a in ({'action':'move','unit_id':True,'x':0,'y':0},
                  {'action':'move','unit_id':1,'x':-1,'y':0},
                  {'action':'production','city_id':1,'kind':'DISTRICT','type':'DISTRICT_CAMPUS','x':1},
                  {'action':'policies','assignments':[{'slot':1,'type':'POLICY_URBAN_PLANNING'},{'slot':1,'type':'POLICY_GOD_KING'}]}):
            with self.subTest(a=a),self.assertRaises(ValueError): validate(a)

    def test_valid_action_is_only_data(self):
        a={'action':'policies','assignments':[{'slot':1,'type':'POLICY_URBAN_PLANNING'}]}
        self.assertEqual(validate(a),a)
        self.assertEqual(lua(a),'{["action"]="policies",["assignments"]={{["slot"]=1,["type"]="POLICY_URBAN_PLANNING"}}}')


class BaselineEvidence(unittest.TestCase):
    def setUp(self):
        self.f=test_civ6.VerifierTests(); self.f.setUp()
        f=self.f
        f.profile.update(schema='civ6-economy-profile/2',max_play_seconds=300,max_requests=100)
        f.records[0]['profile_sha256']=digest(f.profile)
        execution={'model':'gpt-6-astra','auth':'chatgpt','status':'completed'}
        f.records[-1].update(play_seconds=90,execution=execution,usage={
            'model':'gpt-6-astra','auth':'chatgpt','api_calls':0,'model_cost_usd':None,
            'execution_sha256':digest(execution)})
        records=[]; request=0; sequence=0
        for r in f.records:
            if r['kind'] in ('begin','turn_end'):
                request+=1
                records.append({'kind':'request','request_id':request,'request':{'action':r.get('name','end_turn')}})
            if r['kind'] in ('founded','turn_end','boundary'):
                sequence+=1; r['engine_sequence']=sequence
            records.append(r)
            if r['kind'] in ('after_action','boundary'):
                records.append({'kind':'response','request_id':request,'response':{'ok':True}})
        f.records=records; f.retime()

    def test_subscription_baseline_keeps_unknown_cost(self):
        self.assertTrue(self.f.run_trace()['goal_met'])

    def test_broken_request_binding(self):
        next(r for r in self.f.records if r['kind']=='request')['request']['action']='observe'
        with self.assertRaisesRegex(Invalid,'matching request'): self.f.run_trace()

    def test_missing_engine_event(self):
        next(r for r in self.f.records if r['kind']=='boundary')['engine_sequence']+=1
        with self.assertRaisesRegex(Invalid,'engine event'): self.f.run_trace()

    def test_missing_response(self):
        self.f.records=[r for r in self.f.records if not (r['kind']=='response' and r['request_id']==1)]
        with self.assertRaises(Invalid): self.f.run_trace()

    def test_changed_execution(self):
        self.f.records[-1]['execution']['status']='infrastructure_failure'
        with self.assertRaises(Invalid): self.f.run_trace()

    def test_pilot_binds_actual_task(self):
        f=self.f; task_hash=f.records[0]['method_sha256']
        f.profile['pilot']={'arm':'method','phase':'search','task_sha256':task_hash,'method_sha256':'b'*64}
        f.records[0]['profile_sha256']=digest(f.profile)
        finish=f.records[-1]
        finish['execution']['source_sha256']={'task':task_hash}
        finish['usage']['execution_sha256']=digest(finish['execution'])
        self.assertTrue(f.run_trace()['goal_met'])
        finish['execution']['source_sha256']['task']='c'*64
        finish['usage']['execution_sha256']=digest(finish['execution'])
        with self.assertRaisesRegex(Invalid,'not bound'): f.run_trace()

    def test_operator_cutoff_is_not_full_trial(self):
        finish=self.f.records[-1]
        finish['execution']['status']='operator_cutoff'
        finish['usage']['execution_sha256']=digest(finish['execution'])
        with self.assertRaisesRegex(Invalid,'infrastructure failed'): self.f.run_trace()

    def test_reference_replay_is_separate_from_astra(self):
        f=self.f
        f.profile.update(schema='civ6-economy-profile/3',phase='legal_reference_replay')
        f.records[0]['profile_sha256']=digest(f.profile)
        finish=f.records[-1]
        finish['execution'].update(model=None,auth=None)
        finish['usage'].update(model=None,auth=None,model_calls=0,model_cost_usd=0,
                               execution_sha256=digest(finish['execution']))
        self.assertTrue(f.run_trace()['goal_met'])
        finish['usage']['model_calls']=1
        with self.assertRaises(Invalid):f.run_trace()


if __name__=='__main__': unittest.main()
