"""Run an operator-approved panel with separate lanes and fixed job limits."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def disk_usage(job):
    roots = [job] + list((ROOT / "runs").glob(job.name + "-*"))
    total = sum(path.stat().st_size for root in roots for path in root.rglob("*") if path.is_file())
    return {"new_bytes": total, "free_bytes": shutil.disk_usage(ROOT).free,
            "maximum_new_bytes": 20 * 1024**3, "minimum_free_bytes": 10 * 1024**3}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-dir", type=Path, required=True)
    parser.add_argument("--panel", type=Path, required=True, help="JSON array of trial objects")
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--search-deadline", type=float, required=True)
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("--final-panel", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.concurrency <= 8:
        raise SystemExit("Concurrency must be 1 to 8")
    panel = json.loads(args.panel.read_text())
    if not isinstance(panel, list):
        raise SystemExit("The panel must be a JSON array")
    if args.final_panel and (len(panel) != 4 or any(p["kind"] != "final" for p in panel)):
        raise SystemExit("The final panel must contain the four reserved final trials")
    if not args.final_panel and any(p["kind"] == "final" for p in panel):
        raise SystemExit("Use --final-panel for hidden final trials")
    job = args.job_dir.resolve()
    scheduling = job / ("final-schedule" if args.final_panel else "search-schedule")
    scheduling.mkdir(parents=True, exist_ok=False)
    stopped = False
    def stop_signal(signum, frame):
        nonlocal stopped
        stopped = True
    signal.signal(signal.SIGTERM, stop_signal)
    signal.signal(signal.SIGINT, stop_signal)
    pending = list(enumerate(panel))
    active = {}
    results = []
    environment = {k: v for k, v in os.environ.items() if k not in ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL")}
    stop_reason = None
    try:
        while pending or active:
            now = time.time()
            if stopped or now >= args.deadline - 3:
                stop_reason = "supervisor_stop" if stopped else "job_deadline"
                for process, log, row in active.values():
                    if process.poll() is None:
                        process.terminate()
                pending.clear()
            for lane, (process, log, row) in list(active.items()):
                if process.poll() is not None:
                    log.close()
                    results.append({**row, "returncode": process.returncode, "finished_at": time.time()})
                    del active[lane]
            cutoff = args.deadline - 60 if args.final_panel else args.search_deadline
            while pending and len(active) < args.concurrency and stop_reason is None:
                if time.time() >= cutoff:
                    stop_reason = "new_trial_deadline"
                    pending.clear()
                    break
                usage = disk_usage(job)
                (scheduling / "storage.json").write_text(json.dumps(usage, indent=2) + "\n")
                if usage["new_bytes"] >= usage["maximum_new_bytes"] or usage["free_bytes"] < usage["minimum_free_bytes"]:
                    stop_reason = "storage_limit"
                    pending.clear()
                    break
                index_path = job / "index.jsonl"
                count = len(index_path.read_text().splitlines()) if index_path.exists() else 0
                limit = 120 if args.final_panel else 116
                if count + len(active) >= limit:
                    stop_reason = "reserved_trial_cap"
                    pending.clear()
                    break
                ordinal, case = pending.pop(0)
                lane = next(lane for lane in range(1, args.concurrency+1) if lane not in active)
                command = [sys.executable, str(ROOT / "scripts/search_trial.py"), "--job-dir", str(job),
                           "--deadline", str(args.deadline), "--lane", str(lane)]
                for name in ("policy", "case", "seed", "map_x", "map_y", "kind"):
                    command += ["--" + name.replace("_", "-"), str(case[name])]
                log = (scheduling / f"trial-{ordinal:03d}.log").open("w")
                process = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=log, stderr=log)
                row = {"ordinal": ordinal, "case": case, "lane": lane, "pid": process.pid, "started_at": time.time()}
                active[lane] = (process, log, row)
                (scheduling / "active.json").write_text(json.dumps([r for _,_,r in active.values()], indent=2) + "\n")
            (scheduling / "completed.json").write_text(json.dumps(results, indent=2) + "\n")
            if active:
                time.sleep(.2)
            elif stop_reason:
                break
    finally:
        for process, log, row in active.values():
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=max(.1, min(25, args.deadline-time.time())))
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)
            log.close()
        summary = {"started": len(results)+len(active), "completed": len(results),
                   "stop_reason": stop_reason, "results": results, "deadline_epoch": args.deadline}
        (scheduling / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
