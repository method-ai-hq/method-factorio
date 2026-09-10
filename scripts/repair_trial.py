"""One independent repair attempt, with native save verification."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from repair_codex import run_codex
from repair_contract import RULES
from repair_verify import check_case, verify
from science_server import ROOT


def wait_ready(process, path, seconds=45):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if path.exists():
            return json.loads(path.read_text())
        if process.poll() is not None:
            raise RuntimeError(f"Game host exited before ready: {process.returncode}")
        time.sleep(.1)
    raise TimeoutError("Game host did not become ready")


def finished(path):
    if not path.exists():
        return False
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    return bool(rows and isinstance(rows[-1]["request"], dict) and rows[-1]["request"].get("action") == "finish"
                and rows[-1]["response"].get("ok"))



NATIVE_CHECKS = {"case_save_hash", "case_initial_hash", "certificate_hash", "certificate_binding",
                 "certificate_rules", "healthy_native_evidence", "broken_native_evidence",
                 "recoverable_native_evidence", "saved_record_matches", "saved_state_matches",
                 "paused_save", "source_matches", "host_completed", "run_case_matches",
                 "run_initial_matches", "native_initial_matches", "native_initial_paused",
                 "complete_action_trace", "action_trace_hash", "trace_times"}


def classify(verdict, execution, *, host_returncode=0, did_finish=True):
    """Separate invalid run evidence from a legal but unsuccessful attempt."""
    if host_returncode != 0 or execution.get("status") in {"infrastructure_failure", "interrupted"}:
        return "infrastructure_failure"
    checks = verdict.get("verification", {})
    if any(checks.get(key) is not True for key in NATIVE_CHECKS):
        return "infrastructure_failure"
    if verdict.get("error") and did_finish:
        return "infrastructure_failure"
    return "pass" if verdict.get("scored_pass") is True else "fail"


def trial(case_dir, output, *, slot=0, method=None):
    case_dir, output = Path(case_dir).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    host_run = output / "host"
    started = time.monotonic()
    result = {"case_id": case_dir.name, "kind": "method" if method else "direct",
              "status": "infrastructure_failure", "scored_pass": False,
              "case_sha256": None}
    command = [sys.executable, str(ROOT / "scripts/repair_host.py"), "--case", str(case_dir),
               "--run", str(host_run), "--port", str(18950+slot),
               "--rcon-port", str(27950+slot), "--game-port", str(34950+slot)]
    process = None
    try:
        result["case_sha256"] = hashlib.sha256((case_dir / "case.json").read_bytes()).hexdigest()
        _, _, checks = check_case(case_dir)
        if not all(checks.values()):
            raise ValueError("Case certificate failed before model launch")
        with (output / "host.log").open("w") as log:
            process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            ready = wait_ready(process, host_run / "ready.json")
            task = (ROOT / "docs/repair-task.md").read_text()
            result["task_sha256"] = hashlib.sha256(task.encode()).hexdigest()
            if method:
                from repair_method import run_method
                execution = run_method(Path(method), output / "method", ready["endpoint"],
                                       ready["deadline_epoch"], task)
            else:
                execution = run_codex(task, output / "codex", ready["endpoint"],
                                      max(1, ready["deadline_epoch"] - time.time() - 20))
            result["execution"] = execution
            did_finish = finished(host_run / "actions.jsonl")
            if did_finish:
                process.wait(timeout=max(5, ready["deadline_epoch"] - time.time() + 10))
            else:
                process.send_signal(signal.SIGTERM)
                process.wait(timeout=15)
            result["host_returncode"] = process.returncode
        verdict = verify(host_run, case_dir, rcon_port=27960+slot, game_port=34960+slot)
        result["scored_pass"] = verdict["scored_pass"]
        result["status"] = classify(verdict, execution, host_returncode=process.returncode, did_finish=did_finish)
        if not result["scored_pass"] and execution.get("status") == "infrastructure_failure":
            result["status"] = "infrastructure_failure"
            result["error"] = "Model runner failed; inspect saved execution evidence"
        result["verdict"] = verdict
        record = json.loads((host_run / "record.json").read_text())
        result["actions"] = record["audit"]["actions"]
        result["game_wall_seconds"] = record["audit"]["elapsed_seconds"]
    except Exception as error:
        result["status"] = "infrastructure_failure"
        result["scored_pass"] = False
        result["error"] = f"{type(error).__name__}: {error}"
    finally:
        if process is not None and process.poll() is None:
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        result["total_wall_seconds"] = time.monotonic() - started
        (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--slot", type=int, default=0)
    parser.add_argument("--method", type=Path)
    args = parser.parse_args()
    result = trial(args.case, args.output, slot=args.slot, method=args.method)
    print(json.dumps({k: result.get(k) for k in ("case_id", "kind", "status", "actions", "game_wall_seconds", "error")}), flush=True)
    return 0 if result["status"] in {"pass", "fail"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
