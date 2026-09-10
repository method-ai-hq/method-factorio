"""Offline tests: policy failure records and benchmark version separation."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from build_headless_search_report import complete_attempt_record, complete_evidence, report


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.run = self.root / 'game'
        for name in ('initial.json', 'final.json', 'settings.json', 'actions.jsonl', 'game/final.zip'):
            path = self.run / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{}\n')
        inspection = self.run / 'save-inspection/result.json'
        inspection.parent.mkdir()
        inspection.write_text(json.dumps({'passed': True, 'save_sha256': 'save'}))
        self.row = {'trial': 'trial', 'case': 'case', 'kind': 'development',
            'policy': 'initial.method', 'policy_sha256': 'initial', 'benchmark_sha256': 'v2',
            'seed': 1, 'map_x': 1, 'map_y': 1, 'finished_at': 10, 'wall_seconds': 8,
            'game_run': str(self.run), 'runtime_evidence': {'complete': True},
            'source_unchanged': True, 'infrastructure_failure': None, 'scored_pass': False,
            'runtime_summary': {'status': 'failed', 'result': 'PRIVATE RESULT'}, 'policy_returncode': 1,
            'save_inspection': {'passed': True, 'save_sha256': 'save'},
            'verdict': {'evidence_complete': False, 'production_success': False}}

    def test_policy_abort_completes_attempt_but_never_passes(self):
        original = copy.deepcopy(self.row)
        self.assertTrue(complete_attempt_record(self.row))
        self.assertFalse(complete_evidence(self.row))
        self.assertFalse(self.row['scored_pass'])
        self.assertEqual(self.row, original)

    def test_missing_save_check_is_incomplete(self):
        (self.run / 'save-inspection/result.json').unlink()
        self.assertFalse(complete_attempt_record(self.row))

    def test_conflicting_save_check_is_incomplete(self):
        self.row['save_inspection']['save_sha256'] = 'other-save'
        self.assertFalse(complete_attempt_record(self.row))

    def test_missing_action_trace_is_incomplete(self):
        (self.run / 'actions.jsonl').unlink()
        self.assertFalse(complete_attempt_record(self.row))

    def test_comparison_requires_same_version(self):
        job = self.root / 'job'
        job.mkdir()
        (job / 'benchmark-freeze.json').write_text(json.dumps({'version': 'v2', 'map_commitment': {
            'development': [{'seed': 1, 'map_x': 1, 'map_y': 1}]}}))
        (job / 'selection.json').write_text(json.dumps({'initial_policy': 'initial.method',
            'selected_policy': 'selected.method', 'benchmark_sha256': 'v2'}))
        records = []
        for policy in ('direct', 'initial', 'selected'):
            records.append({**self.row, 'trial': policy + '-dev', 'policy': policy + '.method',
                'policy_sha256': policy, 'kind': 'baseline' if policy == 'direct' else 'development'})
        for policy in ('initial', 'selected'):
            for seed in (2, 3):
                records.append({**self.row, 'trial': policy + str(seed), 'policy': policy + '.method',
                    'policy_sha256': policy, 'kind': 'final', 'seed': seed})
        def run():
            (job / 'index.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in records))
            return report(job, self.root / 'output')
        result = run()
        self.assertTrue(result['comparison_complete'])
        self.assertTrue(all(not row['scored_pass'] for row in result['trials']))
        self.assertTrue(all(row['ranking_seconds'] == 330 for row in result['trials']))
        self.assertNotIn('PRIVATE RESULT', json.dumps(result))
        records[0]['benchmark_sha256'] = 'v1'
        self.assertFalse(run()['comparison_complete'])
        records[0]['benchmark_sha256'] = 'v2'
        records[-1]['benchmark_sha256'] = 'v1'
        self.assertFalse(run()['comparison_complete'])


if __name__ == '__main__':
    unittest.main()
