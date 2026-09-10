"""Predicate checks. These do not replace required live-game reference checks."""
import copy
import unittest
from automatic_evaluator import KIT, verdict


def entity(uid, kind, x,y, **kw):
    return dict(id=uid,type=kind,position={'x':x,'y':y},box={'left_top':{'x':x-.4,'y':y-.4},'right_bottom':{'x':x+.4,'y':y+.4}},**kw)

def fixture():
    es=[entity(1,'mining-drill',0,0,drop_position={'x':1,'y':0}),entity(2,'transport-belt',1,0,outputs=[]),entity(3,'inserter',2,0,pickup_position={'x':1,'y':0},drop_position={'x':3,'y':0}),entity(4,'furnace',3,0,products_finished=0,output=[])]
    initial=dict(inventory=KIT,entities=[],research=[],enemies=0,iron_plates_produced=0,speed=20,paused=False)
    states=[]
    for i,tick in enumerate([600,1800,3000,4200]):
        state=dict(tick=tick,speed=20,entities=copy.deepcopy(es),iron_plates_produced=5*i,iron_ore_remaining=1000-5*i)
        state['entities'][3].update(products_finished=5*i,output=[{'name':'iron-plate','count':5*i}])
        state['furnaces']=[state['entities'][3]]
        states.append(state)
    return initial,dict(start=0,samples=states)

class EvaluatorTest(unittest.TestCase):
    def result(self, initial, data, **kw):
        opts=dict(legal_actions=True,unchanged_bundle=True,evidence_complete=True,independent_save_agrees=True,within_limits=True);opts.update(kw)
        return verdict(initial,data,**opts)
    def test_working(self): self.assertTrue(self.result(*fixture())['scored_pass'])
    def test_fail_closed(self):
        for predicate in ['legal_actions','unchanged_bundle','evidence_complete','independent_save_agrees','within_limits']:
            with self.subTest(predicate=predicate):self.assertFalse(self.result(*fixture(),**{predicate:False})['scored_pass'])
    def test_exact_ticks(self):
        a,b=fixture();b['samples'][1]['tick']+=1
        self.assertFalse(self.result(a,b)['scored_pass'])
    def test_stored_ore_only(self):
        a,b=fixture()
        for s in b['samples']:s['iron_ore_remaining']=1000
        self.assertFalse(self.result(a,b)['scored_pass'])
    def test_disconnected(self):
        a,b=fixture()
        for s in b['samples']:s['entities'][0]['drop_position']={'x':9,'y':9}
        self.assertFalse(self.result(a,b)['scored_pass'])
    def test_reversed(self):
        a,b=fixture()
        for s in b['samples']:s['entities'][2]['pickup_position'],s['entities'][2]['drop_position']=s['entities'][2]['drop_position'],s['entities'][2]['pickup_position']
        self.assertFalse(self.result(a,b)['scored_pass'])
    def test_two_windows(self):
        a,b=fixture();b['samples'][-1]['iron_ore_remaining']=b['samples'][-2]['iron_ore_remaining']
        self.assertFalse(self.result(a,b)['scored_pass'])
    def test_initial_ore(self):
        a,b=fixture();a['inventory']={**a['inventory'],'iron-ore':1}
        self.assertFalse(self.result(a,b)['scored_pass'])

if __name__=='__main__':unittest.main()
