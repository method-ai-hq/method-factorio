"""Run one bounded local Method test using the signed-in Codex subscription."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, help="New run name; existing runs are never replaced")
    parser.add_argument("--seed", type=int, default=44340)
    args = parser.parse_args()
    if Path(args.run).name != args.run or args.run in (".", ".."):
        parser.error("run must be a plain folder name")
    env = {k: v for k, v in os.environ.items() if k not in
           ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL")}
    login = subprocess.run(["codex", "login", "status"], env=env, text=True, capture_output=True, timeout=20)
    if login.returncode or "Logged in using ChatGPT" not in login.stdout + login.stderr:
        raise SystemExit("Sign in to Codex with ChatGPT before running this subscription-only test.")
    run = ROOT / "runs" / args.run
    if run.exists():
        raise SystemExit("Run exists. Use a new run name.")
    run.parent.mkdir(exist_ok=True)
    host_log = run.parent / (args.run + "-host.log")
    with host_log.open("x") as log:
        host = subprocess.Popen([sys.executable, "-u", str(ROOT / "scripts/control_test.py"),
            "--run", args.run, "--seed", str(args.seed)], cwd=ROOT, env=env, stdout=log, stderr=log, start_new_session=True)
        worker = None
        try:
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                if host.poll() is not None:
                    raise RuntimeError("Game setup failed. Read the private host log.")
                if '"ready": true' in host_log.read_text():
                    break
                time.sleep(0.5)
            else:
                raise RuntimeError("Game setup timed out.")
            doc = str(ROOT / "docs/control-api.md")
            endpoint = "http://127.0.0.1:18765/action"
            inputs = {"endpoint": endpoint, "tool_documentation": doc}
            resources = {"game": {"description": f"Use only HTTP POST {endpoint}. Tool documentation: {doc}. "
                "For connection preflight read the docs and send one observe request. Successful observation "
                "and documented actions establish readiness. completed is a later Method output, not a game "
                "field. Production is not a connection precondition. Do not play during preflight. "
                "Do not inspect or change host files."}}
            (run / "inputs.json").write_text(json.dumps(inputs))
            (run / "resources.json").write_text(json.dumps(resources))
            paths = ["policies/iron-plates-v1.method", "docs/control-api.md", "scripts/control_test.py", "scripts/check_result.py"]
            (run / "source-hashes.json").write_text(json.dumps({p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}, indent=2))
            with (run / "method-runner.log").open("w") as runner_log:
                command = ["method-run", "run", str(ROOT / paths[0]), "--inputs", str(run / "inputs.json"),
                    "--resources", str(run / "resources.json"), "--workspace", str(ROOT),
                    "--run-dir", str(run / "method"), "--model", "gpt-6-astra", "--verifier-model",
                    "gpt-6-astra", "--concurrency", "1", "--timeout-ms", "720000"]
                worker = subprocess.Popen(command, cwd=ROOT, env=env, stdout=runner_log, stderr=runner_log, start_new_session=True)
                worker.wait(timeout=1140)
        finally:
            if worker is not None and worker.poll() is None:
                os.killpg(worker.pid, signal.SIGTERM)
                try: worker.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(worker.pid, signal.SIGKILL); worker.wait()
            host.terminate()
            try: host.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(host.pid, signal.SIGKILL); host.wait()
    result = subprocess.run([sys.executable, str(ROOT / "scripts/check_result.py"), str(run)], text=True, capture_output=True)
    (run / "check.json").write_text(result.stdout)
    print(result.stdout or result.stderr)
    print("Local run:", run)
    return result.returncode or (worker.returncode if worker is not None else 1)


if __name__ == "__main__":
    raise SystemExit(main())
