"""Run matched direct-agent and Method pilots on separate native game hosts.

This is a bounded, subscription-only environment test. Raw records stay in runs/.
The existing Method and external evaluator are read without changes.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

import yaml

ROOT = Path(__file__).resolve().parents[1]
STOP = threading.Event()
PORTS = {"A": (18801, 27201, 34301), "B": (18802, 27202, 34302)}
SOURCES = ["policies/iron-plates-v1.method", "docs/control-api.md",
           "scripts/control_test.py", "scripts/check_result.py", "scripts/compare_agent_baselines.py"]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def stop_process(process, grace=20):
    if process is None or process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def stop_host(process):
    """Let the host save before it stops the Factorio child process."""
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def summarize(run, timing):
    actions = []
    if (run / "actions.jsonl").exists():
        actions = [json.loads(line) for line in (run / "actions.jsonl").read_text().splitlines()]
    first_goal = None
    for action in actions:
        state = action["response"].get("state", {})
        furnaces = state.get("furnaces", []) or []
        output = sum(item["count"] for furnace in furnaces for item in (furnace.get("output") or [])
                     if item["name"] == "iron-plate")
        if state.get("iron_plates_produced", 0) >= 20 and output >= 20 and sum(
                furnace["products_finished"] for furnace in furnaces) >= 20:
            first_goal = action["ended_at"]
            break
    usage = {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}
    turns = 0
    exhausted = False
    event_paths = list(run.glob("**/events.jsonl"))
    for path in event_paths:
        for line in path.read_text(errors="replace").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "turn.completed" and "usage" in event:
                turns += 1
                for key in usage:
                    usage[key] += event["usage"].get(key, 0)
            if event.get("type") in ("error", "turn.failed"):
                message = json.dumps(event).lower()
                exhausted |= any(word in message for word in (
                    "usage limit", "rate limit", "quota", "credits exhausted", "insufficient_quota"))
    if exhausted:
        STOP.set()
    timing.update({"first_request_at": actions[0]["started_at"] if actions else None,
                   "first_verified_goal_at": first_goal,
                   "last_request_at": actions[-1]["ended_at"] if actions else None,
                   "complete_trial_seconds": timing["end_at"] - timing["start_at"],
                   "ready_to_goal_seconds": first_goal - timing["ready_at"] if first_goal else None,
                   "start_to_goal_seconds": first_goal - timing["start_at"] if first_goal else None,
                   "usage": usage if turns else None, "completed_model_turns": turns,
                   "subscription_exhausted": exhausted,
                   "cost_usd": None, "api_spend_usd": 0,
                   "concurrent_load": "A and B lanes plus other environment checks on same Mac"})
    write_json(run / "timing.json", timing)
    return timing


def episode(lane, seed, batch, env, batch_deadline):
    name = f"{batch}-{lane.lower()}-{seed}"
    run = ROOT / "runs" / name
    host_log = ROOT / "runs" / (name + "-host.log")
    if run.exists() or host_log.exists():
        raise RuntimeError("Existing run: " + name)
    http, rcon, udp = PORTS[lane]
    timing = {"baseline": lane, "seed": seed, "start_at": time.time(), "ready_at": None,
              "controller_start_at": None, "controller_end_at": None,
              "host_seconds_limit": 900, "host_action_limit": 200,
              "policy_request_limit": 120, "operation_seconds_limit": 720,
              "model": "gpt-6-astra", "reasoning_settings": "user configuration, same for A and B",
              "pilot": seed == 44340}
    worker = host = None
    try:
        with host_log.open("x") as log:
            host = subprocess.Popen([sys.executable, "-u", str(ROOT / "scripts/control_test.py"),
                "--run", name, "--seed", str(seed), "--seconds", "900", "--actions", "200",
                "--port", str(http), "--rcon-port", str(rcon), "--game-port", str(udp), "--speed", "1"],
                cwd=ROOT, env=env, stdout=log, stderr=log, start_new_session=True)
            ready_deadline = min(time.monotonic() + 180, batch_deadline)
            while time.monotonic() < ready_deadline:
                if host.poll() is not None:
                    raise RuntimeError("Host exited before ready; private host log retained.")
                if '"ready": true' in host_log.read_text():
                    break
                time.sleep(0.5)
            else:
                raise TimeoutError("Host setup timed out")
            timing["ready_at"] = time.time()
            doc = str(ROOT / "docs/control-api.md")
            endpoint = f"http://127.0.0.1:{http}/action"
            inputs = {"endpoint": endpoint, "tool_documentation": doc}
            resources = {"game": {"description": f"Use only HTTP POST {endpoint}. Tool documentation: {doc}. "
                "For connection preflight read the docs and send one observe request. Successful observation "
                "and documented actions establish readiness. completed is a later Method output, not a game "
                "field. Production is not a connection precondition. Do not play during preflight. "
                "Do not inspect or change host files. Host limit is 900 seconds and 200 requests."}}
            write_json(run / "inputs.json", inputs)
            write_json(run / "resources.json", resources)
            write_json(run / "source-hashes.json", {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                                                    for p in SOURCES})
            if lane == "B":
                command = ["method-run", "run", str(ROOT / SOURCES[0]), "--inputs", str(run / "inputs.json"),
                    "--resources", str(run / "resources.json"), "--workspace", str(ROOT),
                    "--run-dir", str(run / "method"), "--model", "gpt-6-astra", "--verifier-model",
                    "gpt-6-astra", "--concurrency", "1", "--timeout-ms", "720000"]
                prompt = None
                workdir = ROOT
                events_path = run / "method-runner.log"
            else:
                direct = run / "direct"
                direct.mkdir()
                policy = yaml.safe_load((ROOT / SOURCES[0]).read_text())
                prompt = (policy["steps"]["produce"]["do"] + "\n\n" + json.dumps({
                    "endpoint": endpoint, "tool_documentation": doc,
                    "assigned_output_file": str(direct / "report.md"),
                    "host_seconds_limit": 900, "host_request_limit": 200}) +
                    "\nReturn a short honest final result. Do not use Method; this is the direct-agent baseline.\n")
                (direct / "prompt.md").write_text(prompt)
                command = ["codex", "exec", "--ephemeral", "--dangerously-bypass-approvals-and-sandbox",
                    "--skip-git-repo-check", "--json", "--model", "gpt-6-astra",
                    "--output-last-message", str(direct / "result.txt"), "-"]
                workdir = direct
                events_path = direct / "events.jsonl"
            timing["controller_start_at"] = time.time()
            with events_path.open("w") as output, (run / "controller-stderr.log").open("w") as errors:
                worker = subprocess.Popen(command, cwd=workdir, env=env, stdin=subprocess.PIPE if prompt else None,
                    stdout=output, stderr=errors, text=True, start_new_session=True)
                if prompt:
                    worker.stdin.write(prompt)
                    worker.stdin.close()
                limit = min(batch_deadline, time.monotonic() + (720 if lane == "A" else 900))
                while worker.poll() is None and time.monotonic() < limit:
                    if host.poll() is not None or STOP.is_set():
                        break
                    time.sleep(1)
                if worker.poll() is None:
                    timing["controller_stop_reason"] = "host stop, batch stop, or time limit"
                    stop_process(worker)
                timing["controller_returncode"] = worker.returncode
                timing["controller_end_at"] = time.time()
    except Exception as error:
        timing["infrastructure_error"] = str(error)
    finally:
        stop_process(worker)
        stop_host(host)
        run.mkdir(exist_ok=True)
        checked = subprocess.run([sys.executable, str(ROOT / "scripts/check_result.py"), str(run)],
                                 text=True, capture_output=True)
        (run / "check.json").write_text(checked.stdout)
        if checked.stderr:
            (run / "check-error.txt").write_text(checked.stderr)
        timing["external_check_returncode"] = checked.returncode
        timing["end_at"] = time.time()
    summary = summarize(run, timing)
    print(json.dumps({"run": name, "result": summary}), flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[44340, 44341, 44342])
    parser.add_argument("--minutes", type=int, default=35)
    args = parser.parse_args()
    if Path(args.batch).name != args.batch or args.batch in (".", ".."):
        parser.error("batch must be a plain folder name")
    env = {k: v for k, v in os.environ.items() if k not in
           ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL")}
    login = subprocess.run(["codex", "login", "status"], env=env, text=True, capture_output=True, timeout=20)
    if login.returncode or "Logged in using ChatGPT" not in login.stdout + login.stderr:
        raise SystemExit("ChatGPT subscription login is required.")
    (ROOT / "runs").mkdir(exist_ok=True)
    deadline = time.monotonic() + args.minutes * 60
    def lane_runner(lane):
        outcomes = []
        for seed in args.seeds:
            if STOP.is_set() or time.monotonic() + 120 >= deadline:
                break
            outcomes.append(episode(lane, seed, args.batch, env, deadline))
        return outcomes
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = {lane: pool.submit(lane_runner, lane) for lane in PORTS}
        results = {lane: future.result() for lane, future in futures.items()}
    write_json(ROOT / "runs" / (args.batch + "-summary.json"), results)


if __name__ == "__main__":
    main()
