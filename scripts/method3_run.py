"""Prepare a private bundle, validate it, and run the pinned public Method 3 CLI."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import time

from method3_game_tool import ENDPOINT_ENV, validate_endpoint

ROOT = Path(__file__).resolve().parents[1]
REVISION = "eec2cfd1a5f0bd8254fb8213b88be76cff44ad21"


def usage_estimate(events):
    result = {"known_responses": 0, "input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0, "estimated_known_cost_usd": 0, "pricing_source": "https://developers.openai.com/api/docs/models/gpt-6-astra", "pricing_checked_date": "2026-09-10", "rates_per_million": {"input": 10, "cached_input": 1, "output": 50}, "note": "Standard API estimate. Not a bill. Missing responses and cache-write charges are unknown."}
    requests = 0
    if events.exists():
        for line in events.read_text().splitlines():
            event = json.loads(line)
            requests += event.get("event") == "model.request"
            if event.get("event") != "model.response" or not event.get("usage"):
                continue
            usage = event["usage"]
            incoming = usage.get("input_tokens", 0)
            outgoing = usage.get("output_tokens", 0)
            cached = usage.get("input_tokens_details", {}).get("cached_tokens", 0)
            long = incoming > 272000
            result["known_responses"] += 1
            result["input_tokens"] += incoming
            result["cached_input_tokens"] += cached
            result["output_tokens"] += outgoing
            result["estimated_known_cost_usd"] += ((incoming - cached) * 10 * (2 if long else 1) + cached * (2 if long else 1) + outgoing * 50 * (1.5 if long else 1)) / 1_000_000
    result["requests"] = requests
    result["requests_with_unknown_usage"] = requests - result["known_responses"]
    return result


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def saved_key():
    """Read only this key. Do not export other saved secrets to the runtime."""
    for line in (Path.home() / ".codex/secrets.env").read_text().splitlines():
        text = line.strip().removeprefix("export ")
        if text.startswith("OPENAI_API_KEY="):
            tokens = shlex.split(text.split("=", 1)[1], comments=True)
            if len(tokens) == 1:
                return tokens[0]
    raise RuntimeError("OPENAI_API_KEY is not present in the saved secret file")


def configuration(endpoint, timeout_ms):
    validate_endpoint(endpoint)
    text = lambda description: {"type": "text", "description": description}
    tool = lambda operation, inputs, effects: {
        "description": "Read the actual game state." if operation == "observe" else "Send a JSON action or batch to the restricted game host.",
        "in": inputs, "out": {"response": text("The JSON game response encoded as text.")},
        "run": {"kind": "run", "runtime": "python", "entrypoint": "method3_game_tool.py", "args": [operation]},
        "effects": effects,
    }
    model = lambda effort: {"backend": "openai-responses", "model": "gpt-6-astra", "api_key_env": "OPENAI_API_KEY", "reasoning_effort": effort, "max_output_tokens": 4096}
    return {
        "limits": {"timeout_ms": timeout_ms, "max_model_requests": 60, "max_invocations": 100, "max_tool_calls": 60, "max_output_bytes": 2_000_000, "max_request_bytes": 2_000_000},
        "allow_local_processes": True,
        "runtimes": {"python": {"command": shutil.which("python3"), "version": subprocess.check_output(["python3", "--version"], text=True).strip(), "env": [ENDPOINT_ENV]}, "node": {"command": shutil.which("node"), "version": subprocess.check_output(["node", "--version"], text=True).strip(), "env": [ENDPOINT_ENV]}},
        "models": {"planner": model("medium"), "fast": model("low")},
        "environment": {"game": endpoint},
        "tools": {
            "observe": tool("observe", {"endpoint": text("The supplied local game endpoint.")}, []),
            "act": tool("act", {"endpoint": text("The supplied local game endpoint."), "action": text("One JSON action object encoded as text.")}, ["game"]),
            "compute": {"description": "Run restricted in-memory Python code with loops, math, lists and dictionaries. Set result. act(action_dict) and observe() call only the permitted game endpoint. No imports, attributes, files, environment, or model calls. Work limit: 20 seconds, 50000 line events, 50 game actions.",
                "in": {"endpoint": text("The supplied local game endpoint."), "code": text("Restricted Python code. Set result to the result value.")},
                "out": {"response": text("The JSON result, printed lines and game action count, encoded as text.")},
                "run": {"kind": "run", "runtime": "python", "entrypoint": "method3_compute.py"}, "effects": ["game"]},
        },
    }


def main():
    preflight_started = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("policy", type=Path)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--deadline", required=True, help="Absolute ISO UTC job deadline")
    parser.add_argument("--seconds", type=float, default=270)
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    deadline = datetime.datetime.fromisoformat(args.deadline.replace("Z", "+00:00")).timestamp()
    budget = min(args.seconds, deadline - time.time() - 3)
    if budget <= 0:
        raise SystemExit("The job deadline has passed")
    runtime = ROOT / "runs/method3-runtime"
    revision = subprocess.check_output(["git", "-C", str(runtime), "rev-parse", "HEAD"], text=True).strip()
    if revision != REVISION:
        raise SystemExit("The Method 3 source revision does not match the pin")
    if subprocess.check_output(["git", "-C", str(runtime), "status", "--porcelain", "--untracked-files=no"], text=True).strip():
        raise SystemExit("The Method 3 source has local changes")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    bundle = output / "source"
    shutil.copytree(args.policy.resolve().parent, bundle)
    shutil.copy2(ROOT / "scripts/method3_game_tool.py", bundle / "method3_game_tool.py")
    shutil.copy2(ROOT / "scripts/method3_compute.py", bundle / "method3_compute.py")
    config = configuration(args.endpoint, max(1, int(budget * 1000)))
    config_path = output / "runtime.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    node = config["runtimes"]["node"]["command"]
    cli = runtime / "src/cli.js"
    base = [node, str(cli)]
    version = subprocess.check_output(base + ["--version"], text=True).strip()
    pin = {"source": "https://github.com/method-ai-hq/method-spec.git", "revision": revision, "version": version, "cli": str(cli), "cli_sha256": digest(cli), "node": node, "node_sha256": digest(node), "config_sha256": digest(config_path), "deadline": args.deadline, "profiles": config["models"]}
    (output / "runtime-pin.json").write_text(json.dumps(pin, indent=2) + "\n")
    policy = bundle / args.policy.name
    validation = subprocess.run(base + ["validate", str(policy), "--config", str(config_path)], capture_output=True, text=True, timeout=min(20, budget))
    (output / "validation.json").write_text(json.dumps({"returncode": validation.returncode, "stdout": validation.stdout, "stderr": validation.stderr}, indent=2) + "\n")
    if validation.returncode or args.validate_only:
        print(validation.stdout or validation.stderr)
        return validation.returncode
    command = base + ["run", str(policy), "--config", str(config_path), "--run-dir", str(output / "method")]
    if args.inputs:
        command += ["--inputs", str(args.inputs.resolve())]
    uses_models = subprocess.check_output([node, "--input-type=module", "-e",
        "import {readDocument} from './runs/method3-runtime/src/io.js'; const d=await readDocument(process.argv[1]); console.log(Object.values(d.steps).some(s=>[s.do,s.check].some(x=>x && ['call','agent'].includes(x.kind))));",
        str(policy)], cwd=ROOT, text=True, timeout=min(10, budget)).strip() == "true"
    environment = {"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8", ENDPOINT_ENV: args.endpoint}
    if uses_models:
        environment["OPENAI_API_KEY"] = saved_key()
    start = time.time()
    with (output / "stdout.log").open("w") as stdout, (output / "stderr.log").open("w") as stderr:
        process = subprocess.Popen(command, env=environment, stdout=stdout, stderr=stderr, start_new_session=True)
        (output / "process.json").write_text(json.dumps({"pid": process.pid, "process_group": process.pid,
            "command": command, "deadline": args.deadline, "started_at": time.time(),
            "uses_models": uses_models}, indent=2) + "\n")
        def forward_signal(signum, frame):
            if process.poll() is None:
                os.killpg(process.pid, signum)
        signal.signal(signal.SIGTERM, forward_signal)
        signal.signal(signal.SIGINT, forward_signal)
        try:
            code = process.wait(timeout=max(0.1, min(budget - (time.time() - preflight_started), deadline - time.time() - 3)))
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                code = process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                code = process.wait()
    outcome = {"returncode": code, "started_at": datetime.datetime.fromtimestamp(start, datetime.timezone.utc).isoformat(), "wall_seconds": time.time() - start, "runtime_pin": pin}
    (output / "execution.json").write_text(json.dumps(outcome, indent=2) + "\n")
    (output / "usage-estimate.json").write_text(json.dumps(usage_estimate(output / "method/events.jsonl"), indent=2) + "\n")
    print(json.dumps({"returncode": code, "output": str(output), "wall_seconds": outcome["wall_seconds"]}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
