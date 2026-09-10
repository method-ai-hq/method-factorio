"""Run repair policies with pinned Method v3 and subscription Codex steps.

Method script steps are trusted code. Review them before execution. This module
provides a common model-step function; it does not replace the Method runtime.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import threading
import uuid

from repair_codex import run_codex, stop_group, validate_endpoint

ROOT = Path(__file__).resolve().parents[1]
REVISION = "eec2cfd1a5f0bd8254fb8213b88be76cff44ad21"
ENV_KEYS = ["REPAIR_ENDPOINT", "REPAIR_DEADLINE", "REPAIR_CODEX_OUTPUT", "REPAIR_AUTH_HOME"]


def codex_step(data, instructions="", max_seconds=None):
    """One fresh model execution. Call from a Method v3 Python run step.

    data must include task. Other data is candidate state, passed as context.
    The operator's absolute deadline is never reset. A declared step timeout
    must allow at least five extra seconds beyond max_seconds for shutdown.
    """
    remaining = float(os.environ["REPAIR_DEADLINE"]) - time.time() - 5
    if max_seconds is not None:
        remaining = min(remaining, float(max_seconds))
    if remaining <= 0:
        raise TimeoutError("No time remains for a Codex step")
    task = data["task"]
    if instructions:
        task += "\n\nProcedure instructions:\n" + instructions
    context = {key: value for key, value in data.items() if key != "task"}
    if context:
        task += "\n\nRetained procedure context:\n" + json.dumps(context, ensure_ascii=False)
    output = Path(os.environ["REPAIR_CODEX_OUTPUT"]) / str(uuid.uuid4())
    result = run_codex(task, output, os.environ["REPAIR_ENDPOINT"], remaining,
                       auth_home=os.environ["REPAIR_AUTH_HOME"])
    final = output / "final.txt"
    response = {"report": final.read_text() if final.exists() else "",
                "execution_status": result["status"], "evidence": str(output),
                "remaining_seconds": max(0, float(os.environ["REPAIR_DEADLINE"]) - time.time())}
    if result["status"] != "completed":
        raise RuntimeError("Codex step failed; retained evidence: " + str(output))
    return response


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_method(policy, output_dir, endpoint, deadline, task, *, validate_only=False):
    started = time.monotonic()
    deadline -= 20  # Same evaluation allowance as the direct baseline.
    validate_endpoint(endpoint)
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    runtime = ROOT / "runs/method3-runtime"
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js is required")
    cli = runtime / "src/cli.js"
    process = None
    old_handlers = {}
    phase = "runtime"
    summary = {"status": "infrastructure_failure", "deadline_unix": deadline,
               "returncode": None, "model": "gpt-6-astra", "reasoning_effort": "medium"}
    try:
        revision = subprocess.check_output(["git", "-C", str(runtime), "rev-parse", "HEAD"], text=True).strip()
        dirty = subprocess.check_output(["git", "-C", str(runtime), "status", "--porcelain", "--untracked-files=no"], text=True).strip()
        if revision != REVISION or dirty:
            raise RuntimeError("Method v3 runtime does not match the clean pinned source")
        phase = "candidate"
        policy = Path(policy).resolve()
        for path in policy.parent.rglob("*"):
            if path.is_symlink():
                raise ValueError("Candidate bundles must not contain symbolic links")
        source = output / "source"
        shutil.copytree(policy.parent, source)
        summary["candidate_files"] = {str(p.relative_to(policy.parent)): digest(p)
                                       for p in sorted(policy.parent.rglob("*")) if p.is_file()}
        summary["runtime"] = {"revision": revision, "cli_sha256": digest(cli),
                              "node": node, "version": subprocess.check_output([node, str(cli), "--version"], text=True).strip()}
        for name in ("repair_codex.py", "repair_method.py"):
            shutil.copyfile(ROOT / "scripts" / name, source / name)
        # Use the installed runtime's parser for YAML and JSON candidates.
        parse = "import {readDocument} from './src/io.js'; console.log(JSON.stringify(await readDocument(process.argv[1])));"
        method = json.loads(subprocess.check_output([node, "--input-type=module", "-e", parse, str(source / policy.name)], cwd=runtime, text=True))
        for step in method["steps"].values():
            for operation in (step.get("do"), step.get("check")):
                if operation and operation.get("kind") in ("agent", "call"):
                    raise ValueError("Use subscription Codex through run steps; API model backends are disabled")
        method["files"] = sorted(set(method.get("files", []) + ["repair_codex.py", "repair_method.py"]))
        effective = source / "effective.method"
        effective.write_text(json.dumps(method, indent=2) + "\n")
        remaining = deadline - time.time()
        if remaining <= 0:
            raise TimeoutError("Trial deadline has passed")
        config = {"allow_local_processes": True,
                  "limits": {"timeout_ms": max(1, int(remaining * 1000)), "max_model_requests": 0,
                             "max_invocations": 100, "max_tool_calls": 0,
                             "max_output_bytes": 2_000_000, "max_request_bytes": 2_000_000},
                  "runtimes": {"python": {"command": sys.executable, "version": sys.version.split()[0], "env": ENV_KEYS}},
                  "environment": {"game": endpoint}}
        config_path = output / "runtime.json"
        config_path.write_text(json.dumps(config, indent=2) + "\n")
        inputs = output / "inputs.json"
        inputs.write_text(json.dumps({"task": task}) + "\n")
        command = [node, str(cli)]
        checked = subprocess.run(command + ["validate", str(effective), "--config", str(config_path)], capture_output=True, text=True,
                                 timeout=min(20, max(0.1, deadline - time.time())))
        (output / "validation.json").write_text(json.dumps({"returncode": checked.returncode, "stdout": checked.stdout, "stderr": checked.stderr}, indent=2) + "\n")
        if checked.returncode:
            raise RuntimeError("Method validation failed")
        summary["effective_method_sha256"] = digest(effective)
        if validate_only:
            summary["status"] = "validated"
            summary["returncode"] = 0
            return summary
        child_output = output / "codex"
        child_output.mkdir(mode=0o700)
        environment = {"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8",
                       "REPAIR_ENDPOINT": endpoint, "REPAIR_DEADLINE": str(deadline),
                       "REPAIR_CODEX_OUTPUT": str(child_output),
                       "REPAIR_AUTH_HOME": os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))}
        run_command = command + ["run", str(effective), "--config", str(config_path),
                                 "--inputs", str(inputs), "--run-dir", str(output / "method")]
        summary["command"] = run_command
        with (output / "stdout.log").open("w") as stdout, (output / "stderr.log").open("w") as stderr:
            process = subprocess.Popen(run_command, env=environment, stdout=stdout, stderr=stderr, start_new_session=True)
            summary["pid"] = process.pid
            if threading.current_thread() is threading.main_thread():
                def interrupted(signum, frame):
                    raise InterruptedError(f"Signal {signum}")
                for sig in (signal.SIGTERM, signal.SIGINT):
                    old_handlers[sig] = signal.signal(sig, interrupted)
            (output / "process.json").write_text(json.dumps({"pid": process.pid, "command": run_command, "started_unix": time.time()}) + "\n")
            try:
                summary["returncode"] = process.wait(timeout=max(0.1, deadline - time.time() + 2))
                summary["status"] = "completed" if process.returncode == 0 else "policy_failure"
            except subprocess.TimeoutExpired:
                summary["status"] = "timeout"
            finally:
                stop_group(process)
    except Exception as error:
        summary["error"] = f"{type(error).__name__}: {error}"
        if isinstance(error, (TimeoutError, subprocess.TimeoutExpired)):
            summary["status"] = "timeout"
        elif phase == "candidate" and isinstance(error, (ValueError, KeyError, RuntimeError, subprocess.CalledProcessError)):
            summary["status"] = "policy_failure"
    finally:
        if process is not None:
            stop_group(process)
        # A Method timeout uses SIGKILL on its step. The model child has its
        # own group, so close only incomplete children recorded by this trial.
        cleanup = []
        for record in (output / "codex").glob("*/process.json"):
            if (record.parent / "execution.json").exists():
                continue
            child = json.loads(record.read_text())
            pid = child["pid"]
            live = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True)
            if live.stdout.strip().startswith(child["command"][0] + " exec "):
                try:
                    os.killpg(pid, signal.SIGKILL)
                    cleanup.append({"pid": pid, "reason": "incomplete child after Method stop"})
                except ProcessLookupError:
                    pass
        if cleanup:
            (output / "child-cleanup.json").write_text(json.dumps(cleanup, indent=2) + "\n")
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)
        summary["wall_seconds"] = time.monotonic() - started
        summary["codex_runs"] = [json.loads(p.read_text()) for p in sorted((output / "codex").glob("*/execution.json"))]
        if any(r.get("status") in {"infrastructure_failure", "interrupted"} for r in summary["codex_runs"]):
            summary["status"] = "infrastructure_failure"
        elif summary["status"] == "policy_failure" and any(r.get("status") == "timeout" for r in summary["codex_runs"]):
            summary["status"] = "timeout"
        summary["usage_scope"] = "Codex child traces; Method runtime reports only its own API requests, which are disabled"
        (output / "execution.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("policy", type=Path)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--deadline", type=float, required=True, help="Absolute Unix trial deadline")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    result = run_method(args.policy, args.output, args.endpoint, args.deadline, args.task.read_text(), validate_only=args.validate_only)
    print(json.dumps(result))
    return 0 if result["status"] in ("completed", "validated") else 1


if __name__ == "__main__":
    raise SystemExit(main())
