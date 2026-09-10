#!/usr/bin/env python3
"""Build the offline story from reviewed evidence and local demo media."""
import argparse
import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / 'runs/repair-demo-20260910'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'runs/method-story/index.html')
    args = parser.parse_args()
    report_path = ROOT / 'evidence/repair-search-2026-09-10/final-report.json'
    report = json.loads(report_path.read_text())
    development = json.loads((ROOT / 'evidence/repair-search-2026-09-10/development-search.json').read_text())
    data = {'comparison': report['comparison'], 'arms': {}, 'development': {}, 'pairs': []}
    for arm in ('direct', 'method'):
        data['arms'][arm] = {key: report[arm][key] for key in ('attempts', 'strict_passes', 'restored_production', 'total_input_tokens', 'total_cached_input_tokens', 'total_output_tokens')}
    for version, result in development['versions'].items():
        data['development'][version] = {key: result[key] for key in ('attempts', 'strict_passes', 'median_success_total_seconds', 'agent_sessions')}
    by_case = {r['case_id']: r for r in report['method']['rows']}
    for direct in report['direct']['rows']:
        method = by_case[direct['case_id']]
        assert direct['case_sha256'] == method['case_sha256']
        data['pairs'].append({'case': direct['case_id'], 'direct': direct['total_wall_seconds'], 'method': method['total_wall_seconds'], 'direct_pass': direct['strict_pass'], 'method_pass': method['strict_pass']})
    assert len(data['pairs']) == 20
    template = (ROOT / 'story/index.html').read_text()
    template = template.replace('__REPORT_DATA__', json.dumps(data, separators=(',', ':')).replace('<', '\\u003c'))
    assets = {
        '__MAIN_VIDEO__': MEDIA / 'presentation/factorio-method-60s.mp4',
        '__QUICK_VIDEO__': MEDIA / 'presentation/quick-repair-labeled.mp4',
        '__RECOVERY_VIDEO__': MEDIA / 'presentation/furnace-recovery-labeled.mp4',
        '__POSTER__': MEDIA / 'furnace-recovery-2/recording-peer/script-output/frames/frame-000140.jpg',
        '__QUICK_POSTER__': MEDIA / 'quick-repair-4/recording/initial.jpg',
    }
    manifest = {'report_sha256': hashlib.sha256(report_path.read_bytes()).hexdigest(), 'assets': {}}
    for marker, path in assets.items():
        content = path.read_bytes()
        mime = 'video/mp4' if path.suffix == '.mp4' else 'image/jpeg'
        template = template.replace(marker, f'data:{mime};base64,' + base64.b64encode(content).decode())
        manifest['assets'][str(path.relative_to(ROOT))] = hashlib.sha256(content).hexdigest()
    assert '__REPORT_DATA__' not in template
    for marker in assets:
        assert marker not in template
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(template)
    (args.output.parent / 'build-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Built {args.output} ({args.output.stat().st_size / 1_000_000:.1f} MB; all media embedded)')


if __name__ == '__main__':
    main()
