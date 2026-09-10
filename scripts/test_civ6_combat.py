"""Synthetic combat verifier controls. They do not prove live task feasibility."""
import copy
import json
from pathlib import Path
import unittest
from civ6_combat_verify import check_combat_start,verify_combat
from civ6_verify import Invalid,digest


class CombatEvidence(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[1]
        self.start=json.loads((root/'evidence/civ6-economy-setup-2026-09-10/start-state.json').read_text())
        s=self.start;s['task_type']='combat';s['combat_transfer_code']=-1173539618
        s['cities'].append(dict(s['cities'][0],key='28:12',x=28,id=131073))
        warrior=next(u for u in s['units'] if u['type']=='UNIT_WARRIOR')
        builder=next(u for u in s['units'] if u['type']=='UNIT_BUILDER')
        s['units']=[warrior,dict(warrior,id=44),dict(warrior,id=45,type='UNIT_SLINGER'),dict(warrior,id=46,type='UNIT_SLINGER'),builder]
        s['players'].append({'id':1,'human':False,'major':True})
        s['role_states']=[{'role':name,'key':key,'exists':True,'owner':owner,'id':cid,'original_owner':owner,
                           'transfer_type':0,'population':4,'walls':[]} for name,key,owner,cid in
                          [('home','32:12',0,65536),('second','28:12',0,131073),('target','36:12',1,777)]]
        self.profile=json.loads((root/'docs/civ6/profiles/economy-nearby-food-1.json').read_text())
        p=self.profile;p.update(task_type='combat',max_completed_turns=30,start_state_sha256=digest(s))
        self.end=copy.deepcopy(s);self.end['role_states'][2].update(owner=0,id=888,transfer_type=s['combat_transfer_code'])
        self.end['cities'].append(dict(s['cities'][0],key='36:12',x=36,id=888))
        self.records=[{'kind':'start','state':copy.deepcopy(s),'start_save_sha256':p['start_save_sha256'],
                       'profile_sha256':digest(p),'method_sha256':'a'*64,'run_id':'synthetic-combat'},
                      {'kind':'begin','name':'attack','action_id':0},
                      {'kind':'role_removed','role':'target','key':'36:12','owner':1,'id':777},
                      {'kind':'role_added','role':'target','key':'36:12','owner':0,'id':888,'original_owner':1,'transfer_type':s['combat_transfer_code']},
                      {'kind':'after_action','action_id':0,'state':copy.deepcopy(self.end)}]
        for turn in range(2,8):
            self.records.append({'kind':'turn_end','state':copy.deepcopy(self.end)})
            self.end['turn']=turn;self.records.append({'kind':'boundary','state':copy.deepcopy(self.end)})
        execution={'model':'gpt-6-astra','auth':'chatgpt','status':'completed'}
        self.records.append({'kind':'finish','state':copy.deepcopy(self.end),'terminal_save_sha256':'b'*64,
            'play_seconds':100,'execution':execution,'usage':{'model':'gpt-6-astra','auth':'chatgpt',
            'api_calls':0,'model_cost_usd':None,'execution_sha256':digest(execution)}})

    def check(self):
        records=[];request=0;sequence=0
        for r in copy.deepcopy(self.records):
            if r['kind'] in ('begin','turn_end'):
                request+=1;records.append({'kind':'request','request_id':request,'request':{'action':r.get('name','end_turn')}})
            if r['kind'] in ('role_added','role_removed','turn_end','boundary'):
                sequence+=1;r['engine_sequence']=sequence
            records.append(r)
            if r['kind'] in ('after_action','boundary'):
                records.append({'kind':'response','request_id':request,'response':{'ok':True}})
        for i,r in enumerate(records):r['wall_seconds']=i
        return verify_combat(records,self.start,self.end,self.profile,'b'*64)

    def test_combat_and_five_full_rounds(self):
        result=self.check();self.assertTrue(result['goal_met']);self.assertEqual(result['hold_rounds'],5)
        self.assertFalse(result['verified_pass'])

    def test_gift_rejected(self):
        self.records[3]['transfer_type']=-1821839791
        with self.assertRaisesRegex(Invalid,'combat'):self.check()

    def test_original_city_loss_rejected(self):
        self.records.insert(5,{'kind':'role_removed','role':'home','key':'32:12','owner':0,'id':65536})
        with self.assertRaisesRegex(Invalid,'Starting city'):self.check()

    def test_target_loss_breaks_hold(self):
        self.records.insert(-3,{'kind':'role_removed','role':'target','key':'36:12','owner':0,'id':888})
        self.assertFalse(self.check()['goal_met'])

    def test_missing_combat_action(self):
        self.records[1]['name']='research'
        with self.assertRaisesRegex(Invalid,'Capture lacks'):self.check()

    def test_incomplete_hold(self):
        del self.records[-3:-1]
        self.end['turn']=6;self.records[-1]['state']['turn']=6
        self.assertFalse(self.check()['goal_met'])

    def test_final_save_state_changed(self):
        self.end['gold']+=1
        with self.assertRaisesRegex(Invalid,'final save'):self.check()

    def test_start_needs_archery_incomplete(self):
        self.start['technologies'].append('TECH_ARCHERY')
        with self.assertRaisesRegex(Invalid,'research'):check_combat_start(self.start)


if __name__=='__main__':unittest.main()
