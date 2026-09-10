"""Run one recorded, frozen supplied-kit trial. Append every outcome to the index."""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

from automatic_evaluator import verdict
from search_startup import write_status

ROOT = Path(__file__).resolve().parents[1]


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze_valid(freeze):
    return bool(freeze.get("approved_for_scoring") is True and freeze.get("sha256") and
                all((ROOT / name).is_file() and sha(ROOT / name) == digest for name, digest in freeze["sha256"].items()))


def stop(process, seconds=5):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=max(.1, seconds))
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)


def headless_evidence_complete(run):
    required = ("initial.json", "final.json", "settings.json", "actions.jsonl",
                "measurement.json", "action-summary.json", "game/final.zip",
                "host-timing.json", "save-inspection/result.json")
    return (all((run/name).is_file() and (run/name).stat().st_size for name in required)
            and read(run/"settings.json",{}).get("recording_mode")=="none"
            and read(run/"recording-mode.json",{}).get("graphical_client_started") is False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-dir", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--status-file", type=Path)
    parser.add_argument("--source-trial", type=Path, help="Original trial.json for a recorded demonstration")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--map-x", type=int, required=True)
    parser.add_argument("--map-y", type=int, required=True)
    parser.add_argument("--lane", type=int, required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--kind", choices=["development", "final", "baseline", "demonstration"], required=True)
    args = parser.parse_args()
    job = args.job_dir.resolve()
    job.mkdir(parents=True, exist_ok=True)
    case = "".join(c if c.isalnum() or c in "-_" else "-" for c in args.case)
    run_name = f"{job.name}-{case}-{uuid.uuid4().hex[:6]}"
    game_run = ROOT / "runs" / run_name
    trial = job / "trials" / run_name
    trial.mkdir(parents=True, exist_ok=False, mode=0o700)
    started = time.time()
    if args.status_file:
        write_status(args.status_file, phase="startup", trial=run_name)
    record = {"trial": run_name, "case": args.case, "kind": args.kind, "policy": str(args.policy.resolve()),
              "seed": args.seed, "map_x": args.map_x, "map_y": args.map_y, "lane": args.lane,
              "started_at": started, "game_run": str(game_run), "trial_dir": str(trial),
              "comparison_eligible": args.kind != "demonstration",
              "scored_pass": False, "failure_penalty_seconds": 330, "errors": []}
    host = policy = None
    freeze = read(job / "benchmark-freeze.json", {})
    environment = {k: v for k, v in os.environ.items() if k not in ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL")}
    recording_mode = freeze.get("settings", {}).get("recording_mode", "native")
    record["recording_mode"] = recording_mode
    python = str(ROOT / ".venv/bin/python")
    def interrupt(signum, frame):
        raise InterruptedError("Trial stopped by the supervisor")
    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGINT, interrupt)
    try:
        if not freeze_valid(freeze):
            raise RuntimeError("The benchmark freeze is missing, not approved, or changed")
        if recording_mode not in ("native", "none"):
            raise ValueError("Unknown fixed recording mode")
        if recording_mode == "none" and freeze.get("contract") != "automatic-production/headless-1":
            raise ValueError("Headless scoring requires the new headless contract")
        if args.deadline - time.time() < 60:
            raise TimeoutError("Insufficient job time remains for a recorded trial")
        if not 1 <= args.lane <= 8:
            raise ValueError("lane must be 1 to 8")
        before = {str(p.relative_to(args.policy.resolve().parent)): sha(p) for p in args.policy.resolve().parent.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
        before["_runtime_game_helper"] = sha(ROOT / "scripts/method3_game_tool.py")
        before["_runtime_compute_helper"] = sha(ROOT / "scripts/method3_compute.py")
        (trial / "policy-source-hashes.json").write_text(json.dumps(before, indent=2) + "\n")
        record["policy_sha256"] = sha(args.policy.resolve())
        if args.kind == "demonstration":
            if not args.source_trial or recording_mode != "native":
                raise ValueError("A demonstration requires native recording and --source-trial")
            original = read(args.source_trial.resolve(), {})
            old_hashes = read(args.source_trial.resolve().parent / "policy-source-hashes.json", {})
            if not old_hashes or old_hashes != before:
                raise ValueError("Demonstration policy bundle differs from its original trial")
            if original.get("policy_sha256") != record["policy_sha256"] or any(
                    original.get(k) != record[k] for k in ("seed","map_x","map_y")):
                raise ValueError("Demonstration must use the original Method and map")
            record["source_trial"] = str(args.source_trial.resolve())
            record["rerun_notice"] = "New game and model execution; not a replay of the original actions"
        elif args.source_trial:
            raise ValueError("--source-trial is only for a demonstration")
        host_command = [python, str(ROOT / "scripts/search_host.py"), "--run", run_name,
            "--seed", str(args.seed), "--map-x", str(args.map_x), "--map-y", str(args.map_y),
            "--job-deadline", str(args.deadline), "--recording-mode",recording_mode,"--port", str(18900+args.lane),
            "--rcon-port", str(27300+args.lane), "--game-port", str(34400+args.lane)]
        with (trial / "host-console.log").open("w") as log:
            host = subprocess.Popen(host_command, cwd=ROOT, env=environment, stdout=log, stderr=log)
            (trial / "processes.json").write_text(json.dumps({"trial_pid": os.getpid(), "host_pid": host.pid,
                "deadline_epoch": args.deadline}, indent=2) + "\n")
            ready = None
            while time.time() < min(started+180, args.deadline-40):
                if host.poll() is not None:
                    raise RuntimeError("The game host stopped before it was ready")
                for line in (trial / "host-console.log").read_text().splitlines():
                    try:
                        item = json.loads(line)
                        if item.get("ready"):
                            ready = item
                    except (ValueError, AttributeError):
                        pass
                if ready:
                    break
                time.sleep(.1)
            if not ready:
                raise TimeoutError("The game host did not become ready")
            settings = read(game_run / "settings.json", {})
            if settings.get("recording_mode") != recording_mode:
                raise RuntimeError("Host recording mode differs from the fixed settings")
            if settings.get("validation_fault") != "none":
                raise RuntimeError("A scored trial must not use a validation fault")
            if args.status_file:
                write_status(args.status_file, phase="playing", trial=run_name)
            remaining = min(285-(time.time()-started), args.deadline-time.time()-40)
            if remaining <= 0:
                raise TimeoutError("No policy execution time remains")
            command = [sys.executable, str(ROOT / "scripts/method3_run.py"), str(args.policy.resolve()),
                "--endpoint", ready["endpoint"], "--output", str(trial / "runtime"),
                "--seconds", str(remaining), "--deadline", datetime.datetime.fromtimestamp(args.deadline, datetime.timezone.utc).isoformat()]
            with (trial / "policy-console.log").open("w") as policy_log:
                policy = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=policy_log, stderr=policy_log)
                (trial / "processes.json").write_text(json.dumps({"trial_pid": os.getpid(), "host_pid": host.pid,
                    "policy_wrapper_pid": policy.pid, "deadline_epoch": args.deadline}, indent=2) + "\n")
                while policy.poll() is None and time.time() < min(started+290, args.deadline-35):
                    if host.poll() is not None:
                        # A successful finish closes the host while the agent returns its report.
                        if not (game_run / "measurement.json").exists():
                            raise RuntimeError("The game host stopped during policy execution")
                    time.sleep(.1)
                if policy.poll() is None:
                    stop(policy, 3)
                record["policy_returncode"] = policy.returncode
            stop(host, min(22, max(.1, args.deadline-time.time()-30)))
        if not (game_run / "game/final.zip").exists():
            raise RuntimeError("No terminal save was captured")
        inspection_command = [python, str(ROOT / "scripts/search_inspect.py"), str(game_run),
            "--rcon-port", str(27400+args.lane), "--game-port", str(34500+args.lane), "--job-deadline", str(args.deadline)]
        with (trial / "inspection-console.log").open("w") as log:
            subprocess.run(inspection_command, env=environment, stdout=log, stderr=log,
                           timeout=max(.1, min(32, args.deadline-time.time())))
        independent = read(game_run / "save-inspection/result.json", {})
        recording = read(game_run / "recording/recording.json", {})
        action = read(game_run / "action-summary.json", {})
        if read(game_run / "settings.json", {}).get("validation_fault") != "none":
            raise RuntimeError("A validation fault cannot receive a scored verdict")
        after = {str(p.relative_to(args.policy.resolve().parent)): sha(p) for p in args.policy.resolve().parent.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
        after["_runtime_game_helper"] = sha(ROOT / "scripts/method3_game_tool.py")
        after["_runtime_compute_helper"] = sha(ROOT / "scripts/method3_compute.py")
        # Check only this Method and its captured dependencies. Other candidates may change.
        manifest = read(trial / "runtime/method/manifest.json", {})
        used = set(manifest.get("files", {})) | {args.policy.name, "_runtime_game_helper"}
        used.discard("method3_game_tool.py")
        if "method3_compute.py" in used:
            used.remove("method3_compute.py")
            used.add("_runtime_compute_helper")
        unchanged = bool(manifest) and all(name in before and after.get(name) == before[name] for name in used)
        for name, digest in manifest.get("files", {}).items():
            source_name = {"method3_game_tool.py": "_runtime_game_helper", "method3_compute.py": "_runtime_compute_helper"}.get(name, name)
            unchanged = unchanged and before.get(source_name) == digest
        unchanged = unchanged and sha(trial / "runtime/source" / args.policy.name) == before.get(args.policy.name)
        evidence = recording.get("complete") is True and recording.get("error") is None and all((game_run / recording.get(k, "missing")).is_file() for k in ("video", "initial_image", "final_image", "timestamps"))
        if evidence and recording.get("video_sha256"):
            evidence = sha(game_run / recording["video"]) == recording["video_sha256"]
        coverage = {"passed": False, "maximum_gap_seconds": None}
        if recording_mode == "none":
            evidence = headless_evidence_complete(game_run)
            coverage = {"required":False,"reason":"headless optimization contract"}
        if evidence and recording_mode == "native":
            frames = [json.loads(line) for line in (game_run / recording["timestamps"]).read_text().splitlines()]
            actions = [json.loads(line) for line in (game_run / "actions.jsonl").read_text().splitlines()]
            maximum_gap = max((b["wall_requested"]-a["wall_requested"] for a,b in zip(frames, frames[1:])), default=0)
            gap_limit = freeze.get("settings", {}).get("maximum_recording_gap_seconds", 1)
            coverage = {"passed": bool(len(frames)>=2 and actions and frames[0]["wall_requested"]<=min(a["started_at"] for a in actions) and frames[-1]["wall_requested"]>=max(a["ended_at"] for a in actions) and maximum_gap<=gap_limit),
                        "maximum_gap_seconds": maximum_gap, "permitted_gap_seconds": gap_limit}
            evidence = evidence and coverage["passed"]
        within = action.get("within_deadline") is True and time.time()-started <= 330 and time.time() <= args.deadline
        result = verdict(read(game_run / "initial.json", {}), read(game_run / "measurement.json", {}),
            legal_actions=action.get("legal", False), unchanged_bundle=unchanged and freeze_valid(freeze),
            evidence_complete=evidence, independent_save_agrees=independent.get("passed", False), within_limits=within)
        record.update({"verdict": result, "scored_pass": result["scored_pass"], "recording": recording,
                       "save_inspection": independent, "usage": read(trial / "runtime/usage-estimate.json", {}),
                       "runtime_summary": read(trial / "runtime/method/summary.json", {}), "source_unchanged": unchanged,
                       "recording_coverage": coverage})
        (trial / "verdict.json").write_text(json.dumps(result, indent=2) + "\n")
    except BaseException as error:
        record["errors"].append(type(error).__name__ + ": " + str(error))
        record["infrastructure_failure"] = read(game_run / "failure.json", {
            "phase":"startup" if policy is None else "gameplay", "code":"trial_runner_failure"})
    finally:
        stop(policy, 2)
        stop(host, min(22, max(.1, args.deadline-time.time()-3)))
        record["infrastructure_failure"] = record.get("infrastructure_failure") or read(game_run / "failure.json")
        if recording_mode == "native" and not record["infrastructure_failure"] and read(game_run / "recording/recording.json", {}).get("complete") is not True:
            record["infrastructure_failure"] = {"phase":"recording", "code":"incomplete_recording"}
        record["finished_at"] = time.time()
        record["wall_seconds"] = record["finished_at"]-started
        record["ranking_seconds"] = record["wall_seconds"] if record["scored_pass"] else 330
        record.setdefault("usage", read(trial / "runtime/usage-estimate.json", {"unknown": True}))
        record.setdefault("recording", read(game_run / "recording/recording.json", {}))
        record["artifacts"] = {"policy_trace": str(trial / "runtime/method/events.jsonl"), "actions": str(game_run / "actions.jsonl"), "video": str(game_run / "recording/video.mp4") if recording_mode == "native" else None, "save": str(game_run / "game/final.zip"), "inspection": str(game_run / "save-inspection/result.json"), "verdict": str(trial / "verdict.json")}
        (trial / "trial.json").write_text(json.dumps(record, indent=2) + "\n")
        with (job / "index.jsonl").open("a") as index:
            fcntl.flock(index, fcntl.LOCK_EX)
            index.write(json.dumps(record) + "\n")
            index.flush()
            os.fsync(index.fileno())
            fcntl.flock(index, fcntl.LOCK_UN)
    if args.status_file:
        write_status(args.status_file, phase="finished", record=record)
    print(json.dumps({"trial": run_name, "scored_pass": record["scored_pass"], "errors": record["errors"], "wall_seconds": record["wall_seconds"]}))
    return 0 if record["scored_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
