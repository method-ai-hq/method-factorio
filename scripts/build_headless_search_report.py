"""Build a public report from selected control records, never from raw traces."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import shlex
import statistics


def read(path, default=None):
    return json.loads(path.read_text()) if path.is_file() else default


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.is_file() else []


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def pick(data, keys):
    return {key: data[key] for key in keys if key in data}


def usage(data):
    return pick(data or {}, ('known_responses', 'input_tokens', 'cached_input_tokens', 'output_tokens',
        'requests', 'requests_with_unknown_usage', 'estimated_known_cost_usd', 'unknown'))


def total_usage(items):
    result = {'records': len(items), 'records_without_usage': sum(not x or x.get('unknown') is True for x in items)}
    for key in ('requests', 'known_responses', 'input_tokens', 'cached_input_tokens', 'output_tokens',
                'requests_with_unknown_usage', 'estimated_known_cost_usd'):
        values = [x[key] for x in items if isinstance(x.get(key), (int, float))]
        result[key] = sum(values) if values else None
    result['complete_token_usage'] = bool(items) and not result['records_without_usage'] and all(
        x.get('requests_with_unknown_usage') == 0 for x in items)
    return result


def map_key(row):
    return (row.get('seed'), row.get('map_x'), row.get('map_y'))


def complete_evidence(row):
    verdict = row.get('verdict') or {}
    return bool(row.get('finished_at') and row.get('benchmark_sha256') and row.get('policy_sha256')
        and not row.get('infrastructure_failure') and verdict.get('evidence_complete') is True
        and verdict.get('independent_save_agrees') is True
        and row.get('runtime_evidence', {}).get('complete') is True)


def complete_attempt_record(row):
    """A saved policy failure completes an attempt, without becoming a pass."""
    if not (row.get('finished_at') and row.get('benchmark_sha256') and row.get('policy_sha256')
            and row.get('source_unchanged') is True and not row.get('infrastructure_failure')
            and row.get('runtime_evidence', {}).get('complete') is True and row.get('game_run')):
        return False
    run = Path(row['game_run'])
    required = ('initial.json', 'final.json', 'settings.json', 'actions.jsonl', 'game/final.zip',
                'save-inspection/result.json')
    if not all((run / name).is_file() and (run / name).stat().st_size for name in required):
        return False
    inspection = read(run / 'save-inspection/result.json', {})
    recorded = row.get('save_inspection', {})
    if inspection.get('passed') is not True or not inspection.get('save_sha256'):
        return False
    if recorded and (recorded.get('passed') is not True or
                     recorded.get('save_sha256') != inspection.get('save_sha256')):
        return False
    if complete_evidence(row):
        return True
    # Missing production evidence remains missing. A terminal runtime status and
    # its return code document why the policy stopped before a scored handoff.
    return (row.get('scored_pass') is False and row.get('runtime_summary', {}).get('status')
            in ('completed', 'failed', 'needs_input') and type(row.get('policy_returncode')) is int)


def selected_value(selection, name):
    value = selection.get(name + '_policy', selection.get(name))
    if isinstance(value, dict):
        value = value.get('policy', value.get('path', value.get('sha256')))
    return value or selection.get(name + '_sha256')


def policy_matches(row, value):
    return bool(value) and (row.get('policy_sha256') == value
        or Path(row.get('policy', '')).name == Path(str(value)).name)


def report(job, output):
    config = read(job / 'job.json', {})
    freeze = read(job / 'benchmark-freeze.json', {})
    pricing = read(job / 'pricing.json', {})
    selection = read(job / 'selection.json', {})
    repair = read(job / 'repair-v1.json', {})
    setup_by_run = {}
    for row in rows(job / 'setup-index.jsonl'):
        key = row.get('run', row.get('trial'))
        setup_by_run[key] = {**setup_by_run.get(key, {}), **row}
    setup = []
    for row in setup_by_run.values():
        item = pick(row, ('case', 'status', 'started_at', 'finished_at', 'concurrency', 'repair',
            'check_passed', 'expected_pass', 'wall_seconds', 'startup_seconds', 'command',
            'runtime_command', 'runtime_returncode', 'source_hashes', 'errors', 'error'))
        item['run'] = Path(row.get('run', '')).name
        item['action_count'] = row.get('action_summary', {}).get('count')
        item['production_pass'] = row.get('verdict', {}).get('production_success')
        item['save_pass'] = row.get('save_inspection', {}).get('passed')
        item['save_seconds'] = row.get('save_inspection', {}).get('wall_seconds')
        setup.append(item)
    raw_trials = rows(job / 'index.jsonl')
    trials = []
    for row in raw_trials:
        item = pick(row, ('trial', 'case', 'kind', 'seed', 'map_x', 'map_y', 'concurrency',
            'started_at', 'finished_at', 'benchmark_sha256', 'policy_sha256', 'scored_pass',
            'seconds_to_production_verdict', 'save_inspection_seconds', 'wall_seconds',
            'source_unchanged', 'errors', 'infrastructure_failure', 'runtime_evidence', 'commands'))
        item['policy'] = Path(row.get('policy', '')).name
        game_run = Path(row['game_run']) if row.get('game_run') else None
        trial_dir = Path(row['trial_dir']) if row.get('trial_dir') else None
        actions = read(game_run / 'action-summary.json', {}) if game_run else {}
        inspection = read(game_run / 'save-inspection/result.json', {}) if game_run else {}
        timing = read(game_run / 'host-timing.json', {}) if game_run else {}
        pin = read(trial_dir / 'runtime/runtime-pin.json', {}) if trial_dir else {}
        item['action_count'] = actions.get('count', row.get('action_summary', {}).get('count', row.get('action_count')))
        item['runtime_pin'] = pick(pin, ('source', 'revision', 'version', 'cli_sha256', 'node_sha256', 'config_sha256', 'profiles'))
        item['terminal_save_inspection'] = pick(inspection, ('passed', 'save_sha256', 'checks', 'wall_seconds', 'error'))
        item['host_timing'] = pick(timing, ('total_seconds', 'finished_at', 'server_exit_code'))
        item['ranking_seconds'] = row.get('wall_seconds') if row.get('scored_pass') else 330
        item['usage'] = usage(row.get('usage'))
        item['complete_evidence'] = complete_evidence(row)
        item['complete_attempt_record'] = complete_attempt_record(row)
        item['runtime_status'] = row.get('runtime_summary', {}).get('status')
        item['policy_returncode'] = row.get('policy_returncode')
        item['failure_classification'] = ('none' if row.get('scored_pass') else
            'infrastructure_failure' if row.get('infrastructure_failure') else
            'policy_failure' if item['complete_attempt_record'] else 'incomplete_attempt_record')
        verdict = row.get('verdict', {})
        item['verdict'] = pick(verdict, ('production_success', 'checks', 'windows',
            'evidence_complete', 'independent_save_agrees', 'trial_cleanup_within_deadline'))
        item['save_sha256'] = row.get('save_inspection', {}).get('save_sha256', inspection.get('save_sha256'))
        trials.append(item)
    groups = defaultdict(list)
    for row in trials:
        cohort = 'final' if row.get('kind') == 'final' else 'development'
        groups[(row.get('benchmark_sha256'), cohort, row.get('policy_sha256'))].append(row)
    panels = []
    expected_maps = {map_key(row) for row in freeze.get('map_commitment', {}).get('development', [])}
    for (version, cohort, policy_hash), group in groups.items():
        panels.append({'benchmark_sha256': version, 'cohort': cohort, 'policy': group[0]['policy'],
            'policy_sha256': policy_hash, 'attempts': len(group),
            'passes': sum(row.get('scored_pass') is True for row in group),
            'mean_ranking_seconds': statistics.mean(row['ranking_seconds'] for row in group),
            'map_cases': [list(key) for key in sorted({map_key(row) for row in group})],
            'complete_evidence_count': sum(row['complete_evidence'] for row in group),
            'complete_attempt_count': sum(row['complete_attempt_record'] for row in group),
            'complete_development_map_panel': cohort == 'development' and expected_maps
                == {map_key(row) for row in group},
            'usage': total_usage([row['usage'] for row in group])})
    finals = [row for row in raw_trials if row.get('kind') == 'final']
    initial = selected_value(selection, 'initial')
    selected = selected_value(selection, 'selected')
    final_maps = {map_key(row) for row in finals}
    final_versions = {row.get('benchmark_sha256') for row in finals}
    selection_version = selection.get('benchmark_sha256')
    valid_final = bool(initial and selected and selection_version and len(finals) == 4 and len(final_maps) == 2
        and len(final_versions) == 1 and all(complete_attempt_record(row) for row in finals)
        and final_versions == {selection_version}
        and all(sum(policy_matches(row, policy) and map_key(row) == case for row in finals) == 1
                for policy in (initial, selected) for case in final_maps)
        and len({row.get('policy_sha256') for row in finals}) == 2)
    # Full comparison also needs the direct agent and both Methods on matching development maps.
    development = [row for row in raw_trials if row.get('kind') in ('development', 'baseline')]
    direct = {row.get('policy_sha256') for row in development if row.get('kind') == 'baseline'
              and 'direct' in Path(row.get('policy', '')).name}
    matched_development = any(all(any(row.get('benchmark_sha256') in final_versions
        and map_key(row) == case and complete_attempt_record(row)
        and (row.get('policy_sha256') == policy if policy in direct else policy_matches(row, policy))
        for row in development) for case in expected_maps for policy in (direct_hash, initial, selected))
        for direct_hash in direct) if expected_maps and valid_final else False
    setup_usage = [usage(read(path, {})) for path in job.glob('*-runtime/usage-estimate.json')]
    costs = {'setup': total_usage(setup_usage),
             'development': total_usage([row['usage'] for row in trials if row['kind'] != 'final']),
             'final': total_usage([row['usage'] for row in trials if row['kind'] == 'final'])}
    version_usage = {version: total_usage([row['usage'] for row in trials
        if row.get('benchmark_sha256') == version]) for version in {row.get('benchmark_sha256') for row in trials}}
    known_costs = [item['estimated_known_cost_usd'] for item in costs.values()
                   if item['estimated_known_cost_usd'] is not None]
    limitations = [
        'This is a supplied-kit production test. It is not a rocket launch or a fresh-world win.',
        'Headless trials have no video. Later recorded demonstrations are separate attempts.',
        'The sample is small. It does not establish stable speed or a general success rate.',
        'Benchmark versions are kept separate. No result is pooled across changed source.',
        'Each failed or incomplete attempt receives 330 seconds in the time ranking.',
        'A documented policy failure with a complete trace and matching independent save check can complete a comparison attempt. It remains a failed production trial.',
        'API cost is a known-usage estimate, not a bill. Missing usage, cache-write charges, and subscription authoring cost are unknown.',
        'Missing action counts or runtime pins are reported as unknown. Frozen runtime source hashes are included.',
        'A later save check is shown separately. It does not change the original failed trial verdict.',
        'Concurrency is the scheduler capacity. The index times permit a separate overlap check.',
        'The report uses the saved verdict and evidence flags. It does not repeat the independent save check.',
        freeze.get('isolation', 'Process isolation is not established.'),
    ]
    result = {'job': config, 'comparison_complete': bool(valid_final and matched_development),
        'four_final_trials_complete': valid_final, 'matched_development_complete': matched_development,
        'selection': {'initial_policy': initial, 'selected_policy': selected, 'benchmark_sha256': selection_version},
        'benchmark_version': freeze.get('version'), 'benchmark_sha256': digest(job / 'benchmark-freeze.json'),
        'source_sha256': freeze.get('sha256', {}), 'fixed_settings': freeze.get('settings', {}),
        'setup_attempts': setup, 'setup_count': len(setup),
        'setup_checks_passed': sum(row.get('check_passed') is True for row in setup),
        'trials': trials, 'panels': panels, 'usage_by_phase': costs, 'usage_by_benchmark': version_usage,
        'repair_record': repair,
        'estimated_known_cost_usd': sum(known_costs) if known_costs else None,
        'pricing': pricing, 'limitations': limitations}
    output.mkdir(parents=True, exist_ok=True)
    (output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    number = lambda value: f'{value:.3f}' if isinstance(value, (int, float)) else 'unknown'
    lines = ['# Headless Method v3 policy search', '',
        'Comparison complete.' if result['comparison_complete'] else 'Comparison incomplete.', '',
        f"Job: `{config.get('job_id', job.name)}`. Deadline: `{config.get('deadline_utc', 'unknown')}`.", '',
        f"Setup checks: {result['setup_checks_passed']}/{len(setup)}. Scored attempts: {len(trials)}. Final attempts: {len(finals)}.", '',
        f"Known API cost estimate: ${number(result['estimated_known_cost_usd'])}. Total cost is not fully known.", '',
        '| Version hash | Phase | Policy | Attempts | Passes | Mean time with failure penalty (s) | Known API cost ($) |',
        '| --- | --- | --- | ---: | ---: | ---: | ---: |']
    for panel in panels:
        lines.append(f"| {(panel['benchmark_sha256'] or 'unknown')[:12]} | {panel['cohort']} | {panel['policy']} | {panel['attempts']} | {panel['passes']} | {number(panel['mean_ranking_seconds'])} | {number(panel['usage']['estimated_known_cost_usd'])} |")
    lines += ['', 'Each source version has its own panel in summary.json. All attempts follow.', '',
        '| Trial | Pass | Production (s) | Save check (s) | Full time (s) | Actions |',
        '| --- | --- | ---: | ---: | ---: | ---: |']
    for row in trials:
        lines.append(f"| {row['trial']} | {bool(row.get('scored_pass'))} | {number(row.get('seconds_to_production_verdict'))} | {number(row.get('save_inspection_seconds'))} | {number(row.get('wall_seconds'))} | {row['action_count'] if row['action_count'] is not None else 'unknown'} |")
    lines += ['', 'Setup attempts include deliberate broken factories. A rejected broken factory is a successful setup check.', '',
              '| Setup run | Case | Check passed | Status |', '| --- | --- | --- | --- |']
    lines += [f"| {row['run']} | {row.get('case')} | {row.get('check_passed', 'unknown')} | {row.get('status', 'unknown')} |" for row in setup]
    lines += ['', 'Limits and evidence:', ''] + ['- ' + item for item in limitations]
    lines += ['', 'Exact commands are below. They retain the original deadline and local paths; a new attempt needs a new authorized job.', '']
    for row in trials:
        lines += [f"Trial `{row['trial']}`:", '', '```sh']
        lines += [shlex.join(command) for command in row.get('commands', {}).values()]
        lines += ['```', '']
    lines += ['See [summary.json](summary.json) for exact measurements, all setup attempts, usage by phase, policy hashes, and frozen source hashes.', '']
    (output / 'README.md').write_text('\n'.join(lines))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--job-dir', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    result = report(args.job_dir.resolve(), args.output_dir.resolve())
    print(json.dumps(pick(result, ('comparison_complete', 'setup_count', 'estimated_known_cost_usd'))))


if __name__ == '__main__':
    main()
