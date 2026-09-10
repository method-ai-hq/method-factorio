"""Run separate repair attempts. Resume only completed evidence, never a player."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import time
import threading

from repair_host import sources
from repair_trial import trial
from science_server import ROOT


RUNNERS = ["repair_codex.py", "repair_trial.py", "repair_batch.py", "repair_method.py"]


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate_hashes(policy):
    if policy is None:
        return None
    root = Path(policy).resolve().parent
    files = sorted(root.rglob("*"))
    if any(p.is_symlink() for p in files):
        raise ValueError("Candidate bundles must not contain symbolic links")
    return {str(p.relative_to(root)): file_hash(p) for p in files if p.is_file()}


def freeze_candidate(output, policy):
    if policy is None:
        return None
    frozen = {"policy": Path(policy).name, "files": candidate_hashes(policy)}
    path = output / (Path(policy).name + "-candidate-lock.json")
    if path.exists() and json.loads(path.read_text()) != frozen:
        raise RuntimeError("Candidate changed; use a new version and retain its previous attempts")
    if not path.exists():
        path.write_text(json.dumps(frozen, indent=2) + "\n")
    return frozen


def validate_resume(result, case, policy, task_hash):
    if result.get("case_sha256") != file_hash(case / "case.json") or result.get("case_id") != case.name:
        raise RuntimeError("Saved attempt belongs to a different case")
    if result.get("task_sha256") != task_hash:
        raise RuntimeError("Saved attempt used different task instructions")
    if result.get("kind") != ("method" if policy else "direct"):
        raise RuntimeError("Saved attempt belongs to a different policy kind")
    if policy and result.get("execution", {}).get("candidate_files") != candidate_hashes(policy):
        raise RuntimeError("Saved attempt used different candidate files")


def freeze(output):
    frozen = {"sources": sources(), "task_sha256": hashlib.sha256((ROOT / "docs/repair-task.md").read_bytes()).hexdigest()}
    path = output / "benchmark.json"
    if path.exists():
        if json.loads(path.read_text()) != frozen:
            raise RuntimeError("Frozen benchmark changed; use a new experiment and repeat comparisons")
    else:
        path.write_text(json.dumps(frozen, indent=2) + "\n")
    runner_sources = {name: file_hash(ROOT / "scripts" / name) for name in RUNNERS}
    runner_path = output / "runner-freeze.json"
    if runner_path.exists():
        if json.loads(runner_path.read_text())["sources"] != runner_sources:
            raise RuntimeError("Frozen runner changed; review and record the change before more trials")
    else:
        # Migration records known completed attempts, without pretending they used
        # the newly frozen runner. Native task/host/scoring sources are unchanged.
        legacy = {}
        for record in sorted(output.glob("direct-development-*/codex/execution.json")):
            execution = json.loads(record.read_text())
            legacy[str(record.relative_to(output))] = execution.get("source_sha256", {})
        runner_path.write_text(json.dumps({"sources": runner_sources,
            "accepted_legacy_execution_sources": legacy,
            "migration": "Runner classification and freeze checks added after initial direct attempts; original execution hashes retained."}, indent=2) + "\n")
    return frozen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--split", choices=["development", "final"], required=True)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--workers", type=int, choices=[1, 2], default=1)
    parser.add_argument("--slot-start", type=int, default=0)
    parser.add_argument("--method", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    frozen = freeze(args.output)
    candidate = freeze_candidate(args.output, args.method)
    stopped = threading.Event()
    indices = list(range(args.start, args.start + args.count))

    def worker(slot):
        results = []
        for index in indices[slot::args.workers]:
            if stopped.is_set():
                break
            if freeze(args.output) != frozen or freeze_candidate(args.output, args.method) != candidate:
                stopped.set()
                raise RuntimeError("Frozen run inputs changed")
            case = args.cases / f"{args.split}-{index:03d}"
            kind = args.method.name if args.method else "direct"
            output = args.output / f"{kind}-{case.name}"
            if output.exists():
                if not (output / "summary.json").exists():
                    raise RuntimeError("Incomplete attempt preserved; inspect before continuing: " + str(output))
                result = json.loads((output / "summary.json").read_text())
                validate_resume(result, case, args.method, frozen["task_sha256"])
            else:
                deadline = time.monotonic() + 3600
                while not (case / "certificate.json").exists() or not (case / "case.json").exists():
                    if stopped.is_set():
                        return results
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Case not ready: " + str(case))
                    time.sleep(2)
                if freeze(args.output) != frozen:
                    raise RuntimeError("Benchmark changed")
                result = trial(case, output, slot=slot + args.slot_start, method=args.method)
            results.append(result)
            print(json.dumps({k: result.get(k) for k in ("case_id", "kind", "status", "actions", "game_wall_seconds", "error")}), flush=True)
            if result["status"] == "infrastructure_failure":
                stopped.set()
                raise RuntimeError("Repair infrastructure failure; preserve and inspect " + str(output))
        return results

    def guarded_worker(slot):
        try:
            return worker(slot)
        except BaseException:
            stopped.set()
            raise

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        results = sum(list(executor.map(guarded_worker, range(args.workers))), [])
    report = {"attempts": len(results), "passes": sum(r["scored_pass"] for r in results),
              "results": [{k: r.get(k) for k in ("case_id", "kind", "status", "actions", "game_wall_seconds")} for r in results]}
    label = (args.method.name if args.method else "direct") + "-" + args.split
    (args.output / (label + "-summary.json")).write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
