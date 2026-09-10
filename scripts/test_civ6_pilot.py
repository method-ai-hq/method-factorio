"""Method identity and fixed-task controls for the pilot."""
import json
from pathlib import Path
import tempfile
import unittest

from civ6_baseline import pilot_inputs,task_text
from civ6_verify import digest


class PilotInputs(unittest.TestCase):
    def test_method_changes_prompt_but_not_game_limits(self):
        base=json.loads((Path(__file__).resolve().parents[1]/'docs/civ6/profiles/economy-nearby-food-1.json').read_text())
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);lock=root/'lock.json';method=root/'method.md'
            data={'base_profile_sha256':digest(base),'stop_unix':1}
            lock.write_text(json.dumps(data));method.write_text('Choose from current observations.')
            p,task,content=pilot_inputs(base,lock,'search',method)
            self.assertEqual({k:v for k,v in p.items() if k!='pilot'},base)
            self.assertTrue(task.startswith(task_text(base)))
            self.assertIn(content,task)
            direct,text,_=pilot_inputs(base,lock,'search',None)
            self.assertEqual(text,task_text(base));self.assertIsNone(direct['pilot']['method_sha256'])
            base['max_completed_turns']=36
            with self.assertRaisesRegex(ValueError,'base profile changed'):pilot_inputs(base,lock,'search',method)

    def test_comparison_rejects_changed_method(self):
        base=json.loads((Path(__file__).resolve().parents[1]/'docs/civ6/profiles/economy-nearby-food-1.json').read_text())
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);lock=root/'lock.json';method=root/'method.md'
            data={'base_profile_sha256':digest(base),'stop_unix':1}
            lock.write_text(json.dumps(data));method.write_text('Original Method')
            profile,_,_=pilot_inputs(base,lock,'search',method)
            (root/'frozen.json').write_text(json.dumps({'lock_sha256':digest(data),'method_sha256':profile['pilot']['method_sha256']}))
            pilot_inputs(base,lock,'comparison',method)
            method.write_text('Changed Method')
            with self.assertRaisesRegex(ValueError,'frozen winner'):pilot_inputs(base,lock,'comparison',method)


if __name__=='__main__':unittest.main()
