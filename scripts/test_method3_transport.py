"""Offline endpoint and pinned-runtime checks. No game launches or paid calls."""
import contextlib
import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from method3_game_tool import ENDPOINT_ENV, request, validate_endpoint
from method3_run import configuration

ROOT = Path(__file__).resolve().parents[1]


@contextlib.contextmanager
def host(redirect=None):
    calls = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            calls.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(302 if redirect else 200)
            if redirect:
                self.send_header('Location', redirect)
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True, 'action': calls[-1]['action']}).encode())
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/action', calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


class TransportTests(unittest.TestCase):
    def test_missing_binding_fails_before_connection(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'not bound'):
                request('http://127.0.0.1:1/action', {'action': 'observe'})

    def test_only_exact_bound_url_is_accepted(self):
        with host() as (endpoint, calls), patch.dict(os.environ, {ENDPOINT_ENV: endpoint}):
            for other in (endpoint.replace('127.0.0.1', 'localhost'), endpoint + '?x=1',
                          endpoint.replace('/action', '/admin'), 'unix:/tmp/other.sock',
                          endpoint.replace('/action', '/action#same'), None):
                with self.subTest(endpoint=other), self.assertRaises(ValueError):
                    request(other, {'action': 'observe'})
            self.assertEqual(calls, [])
            self.assertTrue(request(endpoint, {'action': 'observe'})['ok'])
            self.assertEqual(calls, [{'action': 'observe'}])

    def test_unix_binding_rejects_other_socket_before_connection(self):
        with patch.dict(os.environ, {ENDPOINT_ENV: 'unix:/tmp/operator.sock'}):
            with self.assertRaisesRegex(ValueError, 'does not match'):
                request('unix:/tmp/other.sock', {'action': 'observe'})

    def test_redirect_never_reaches_second_endpoint(self):
        with host() as (other, other_calls), host(other) as (endpoint, calls):
            with patch.dict(os.environ, {ENDPOINT_ENV: endpoint}):
                with self.assertRaisesRegex(ValueError, 'must not redirect'):
                    request(endpoint, {'action': 'observe'})
            self.assertEqual(len(calls), 1)
            self.assertEqual(other_calls, [])

    def test_invalid_operator_endpoints(self):
        for endpoint in ('https://127.0.0.1:1/action', 'http://example.com:1/action',
                         'http://127.0.0.1/action', 'http://user@127.0.0.1:1/action',
                         'http://127.0.0.1:1/admin', 'http://127.0.0.1:1/action?admin=1',
                         'unix:relative.sock', ' http://127.0.0.1:1/action'):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                validate_endpoint(endpoint)

    def test_compute_inherits_binding_and_rejects_mismatch(self):
        with host() as (endpoint, calls):
            environment = {'PATH': os.environ['PATH'], ENDPOINT_ENV: endpoint}
            command = [sys.executable, str(ROOT / 'scripts/method3_compute.py')]
            good = subprocess.run(command, input=json.dumps({'endpoint': endpoint,
                'code': 'result = observe()'}), env=environment, capture_output=True, text=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            bad = subprocess.run(command, input=json.dumps({'endpoint': endpoint + '?wrong=1',
                'code': 'result = observe()'}), env=environment, capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn('does not match', bad.stderr)
            self.assertEqual(len(calls), 1)

    def test_runtime_configuration_passes_only_endpoint_to_helpers(self):
        config = configuration('http://127.0.0.1:1/action', 1000)
        for runtime in config['runtimes'].values():
            self.assertEqual(runtime['env'], [ENDPOINT_ENV])

    def test_pinned_cli_observe_compute_and_clean_helper_environment(self):
        if not (ROOT / 'runs/method3-runtime/src/cli.js').exists():
            self.skipTest('Pinned public Method runtime is not installed')
        with tempfile.TemporaryDirectory() as directory, host() as (endpoint, calls):
            base = Path(directory)
            bundle = base / 'bundle'
            bundle.mkdir()
            (bundle / 'check_env.py').write_text(
                'import json,os\nassert "OPENAI_API_KEY" not in os.environ\n'
                'assert os.environ["METHOD3_GAME_ENDPOINT"]\nprint(json.dumps({"clean":True}))\n')
            shape = lambda kind: {'type': kind, 'description': 'Offline test output.'}
            method = {'format': 'method/3', 'name': 'Offline integration', 'goal': 'Test transport.',
                'files': ['method3_compute.py'],
                'environment': {'game': {'type': 'service', 'description': 'Fake host.'}},
                'inputs': {'code': dict(shape('text'), default='result = observe()')},
                'steps': {
                    'read': {'purpose': 'Read fake state.', 'in': {'endpoint': 'environment.game'},
                        'do': {'kind': 'run', 'runtime': 'python', 'entrypoint': 'method3_game_tool.py', 'args': ['observe']},
                        'out': {'response': shape('text')}, 'limits': {'timeout_ms': 3000}},
                    'calculate': {'purpose': 'Read through compute.', 'after': 'read',
                        'in': {'endpoint': 'environment.game', 'code': 'inputs.code'},
                        'do': {'kind': 'run', 'runtime': 'python', 'entrypoint': 'method3_compute.py'},
                        'out': {'computed': shape('text')}, 'limits': {'timeout_ms': 3000}},
                    'environment_check': {'purpose': 'Check helper environment.', 'after': 'calculate',
                        'do': {'kind': 'run', 'runtime': 'python', 'entrypoint': 'check_env.py'},
                        'out': {'clean': shape('boolean')}, 'limits': {'timeout_ms': 3000}}},
                'result': 'clean'}
            # Each run step has a distinct output name; adapt the stock compute output.
            (bundle / 'compute_adapter.py').write_text(
                'import json,subprocess,sys\np=subprocess.run([sys.executable,"method3_compute.py"],'
                'input=sys.stdin.read(),capture_output=True,text=True,check=True)\n'
                'print(json.dumps({"computed":json.loads(p.stdout)["response"]}))\n')
            method['steps']['calculate']['do']['entrypoint'] = 'compute_adapter.py'
            policy = bundle / 'offline.method'
            policy.write_text(json.dumps(method))
            deadline = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=30)).isoformat()
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/method3_run.py'), str(policy),
                '--endpoint', endpoint, '--output', str(base / 'result'), '--deadline', deadline,
                '--seconds', '20'], capture_output=True, text=True, timeout=30)
            if result.returncode:
                logs = '\n'.join(p.read_text() for p in (base / 'result').glob('*.log'))
                logs += '\n'.join(p.read_text() for p in (base / 'result/method').glob('*.jsonl'))
                self.fail(result.stdout + result.stderr + logs)
            self.assertEqual(len(calls), 2)
            usage = json.loads((base / 'result/usage-estimate.json').read_text())
            self.assertEqual(usage['requests'], 0)
            self.assertEqual(usage['estimated_known_cost_usd'], 0)


if __name__ == '__main__':
    unittest.main()
