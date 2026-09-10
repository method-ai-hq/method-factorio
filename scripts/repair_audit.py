"""Read-only publication audit of a completed, paired repair comparison.

Checks saved hashes and recomputes review decisions. It does not reload games
or replace the independent native save verification retained by each review.
"""
import argparse
import json
from pathlib import Path

from repair_batch import RUNNERS, candidate_hashes, file_hash
from repair_contract import evaluate
from repair_host import sources
from repair_report import compare, group
from repair_review import VERSION, normalize, provenance
from repair_trial import classify, finished
from repair_verify import check_case
from science_server import ROOT


def read(path):
    return json.loads(Path(path).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit_trial(trial, case, *, kind, task_hash, core, runners, candidate_files=None):
    raw = read(trial / "summary.json")
    reviewed = read(trial / "review.json")
    record = read(trial / "host/record.json")
    legacy = read(trial / "host/verdict.json")
    require(raw["case_id"] == case.name and raw["kind"] == kind, "Attempt identity mismatch")
    require(raw["case_sha256"] == file_hash(case / "case.json") and raw["task_sha256"] == task_hash,
            "Attempt case or task hash mismatch")
    require(record["sources"] == core, "Attempt used a different game host or checker")
    require(reviewed["review_contract"] == VERSION and reviewed["review_provenance"] == provenance(trial, case),
            "Review provenance mismatch")
    for key, source in (("raw_summary_sha256", "raw_summary_sha256"), ("raw_record_sha256", "raw_record_sha256"),
                        ("save_sha256", "raw_save_sha256"), ("source_sha256", "review_source_sha256")):
        require(reviewed[key] == reviewed["review_provenance"][source], "Review hash aliases disagree")
    require(raw["verdict"] == legacy == reviewed["legacy_verdict"] == reviewed["independent_legacy_verdict"],
            "Legacy decisions disagree")
    require(not reviewed.get("review_error"), "Review did not complete")
    for key in ("case_id", "case_sha256", "task_sha256", "kind", "execution", "actions", "game_wall_seconds"):
        require(raw.get(key) == reviewed.get(key), "Review changed original trial field: " + key)
    require(reviewed["original_status"] == raw["status"] and reviewed["legacy_scored_pass"] == raw["scored_pass"],
            "Review changed original status history")
    require(reviewed["original_total_wall_seconds"] == raw["total_wall_seconds"]
            and reviewed["review_wall_seconds"] >= 0
            and reviewed["total_wall_seconds"] == raw["total_wall_seconds"] + reviewed["review_wall_seconds"],
            "Review time accounting mismatch")
    normalized, corrections = (normalize(record, reviewed["native_recipe_history"])
                               if record.get("measurement", {}).get("done") is True else (record, []))
    require(corrections == reviewed["corrections"], "Recipe correction list mismatch")
    for value, verdict in ((record, legacy), (normalized, reviewed["verdict"])):
        evaluated = evaluate(value)
        require(all(verdict.get(k) == v for k, v in evaluated.items()), "Stored score differs from fixed rules")
    require(reviewed["verdict"]["verification"] == legacy["verification"], "Review changed native or protocol checks")
    score = (reviewed["verdict"]["production_pass"] and bool(legacy["verification"])
             and all(v is True for v in legacy["verification"].values()))
    require(reviewed["verdict"]["scored_pass"] == score, "Review score is inconsistent")
    status = classify(reviewed["verdict"], raw["execution"], host_returncode=raw.get("host_returncode", 0),
                      did_finish=finished(trial / "host/actions.jsonl"))
    require(status in {"pass", "fail"} and reviewed["status"] == status
            and reviewed["scored_pass"] == (score and status == "pass"), "Incomplete or inconsistent final outcome")
    if kind == "method":
        require(raw["execution"]["candidate_files"] == candidate_files, "Attempt used a different candidate")
        copied = trial / "method/source"
        require(all(file_hash(copied / name) == digest for name, digest in candidate_files.items()),
                "Copied candidate changed")
        for name in ("repair_method.py", "repair_codex.py"):
            require(file_hash(copied / name) == runners[name], "Copied player helper changed")
        child_folders = [p for p in (trial / "method/codex").glob("*") if p.is_dir()]
    else:
        child_folders = [trial / "codex"]
    require(bool(child_folders), "No player execution evidence")
    completed, incomplete = 0, 0
    child_executions = []
    for folder in child_folders:
        # A stopped child may have no execution.json. It must retain a process
        # record, and publication must keep its final usage unknown.
        if not (folder / "execution.json").exists():
            require((folder / "process.json").is_file(), "Missing child execution and process evidence")
            process = read(folder / "process.json")
            command = process["command"]
            require("-m" in command and command[command.index("-m") + 1] == "gpt-6-astra"
                    and 'model_reasoning_effort="medium"' in command
                    and 'forced_login_method="chatgpt"' in command,
                    "Incomplete child has no matching player configuration")
            incomplete += 1
            continue
        execution = read(folder / "execution.json")
        require(execution["source_sha256"]["runner"] == runners["repair_codex.py"], "Different model runner source")
        require(execution["model"] == "gpt-6-astra" and execution["reasoning_effort"] == "medium"
                and execution["auth"] == "chatgpt", "Different player model or access mode")
        if kind == "direct":
            require(execution == raw["execution"], "Direct execution evidence differs from summary")
            require(execution["source_sha256"]["task"] == task_hash, "Direct player received a different task")
        else:
            require(execution in raw["execution"]["codex_runs"], "Method child is absent from summary")
        child_executions.append(execution)
        completed += 1
    if kind == "direct":
        require(completed == 1, "Direct execution.json is missing")
    else:
        expected_children = raw["execution"]["codex_runs"]
        require(sorted(json.dumps(e, sort_keys=True) for e in child_executions)
                == sorted(json.dumps(e, sort_keys=True) for e in expected_children),
                "Method child execution set is missing or duplicated")
    return {"case_id": case.name, "kind": kind, "status": status,
            "review_sha256": file_hash(trial / "review.json"),
            "agent_sessions": completed + incomplete, "sessions_missing_execution": incomplete}


def audit(output, cases_root, policy, selection, *, count=20):
    output, cases_root, policy, selection = map(lambda p: Path(p).resolve(), (output, cases_root, policy, selection))
    selected = read(selection)
    require(selected == read(output / "selection.json"), "Selected policy document changed")
    require(read(output / "selection-hash.json")["sha256"] == file_hash(selection), "Selection source hash mismatch")
    reader_hash = file_hash(ROOT / "scripts/repair_review.py")
    require(selected["review_source_sha256"] == reader_hash and selected["review_contract"] == VERSION,
            "Frozen recipe reader changed")
    candidates = candidate_hashes(policy)
    require(selected["candidate_files"] == candidates, "Selected candidate changed")
    require(read(output / "method" / (policy.name + "-candidate-lock.json")) == {"policy": policy.name, "files": candidates},
            "Candidate lock differs")
    core = sources()
    runners = {name: file_hash(ROOT / "scripts" / name) for name in RUNNERS}
    task_hash = file_hash(ROOT / "docs/repair-task.md")
    for kind in ("direct", "method"):
        require(read(output / kind / "benchmark.json") == {"sources": core, "task_sha256": task_hash},
                "Task or core source lock differs between arms")
        require(read(output / kind / "runner-freeze.json")["sources"] == runners,
                "Player runner lock differs between arms")
    names = {f"final-{i:03d}" for i in range(1, count + 1)}
    manifests = read(output / "cases.json")
    require(set(manifests) == names, "Final case set is missing or has extra cases")
    rows = []
    for kind in ("direct", "method"):
        retained = {p.parent.name for p in (output / kind).glob("*/summary.json")}
        require(retained == {f"{kind}-{name}" for name in names}, "Missing, duplicate, or extra final attempts")
    for name in sorted(names):
        case = cases_root / name
        manifest, _, checks = check_case(case)
        require(manifest["case_id"] == name and manifest["split"] == "final" and all(checks.values()), "Invalid final case certificate")
        require(manifests[name] == file_hash(case / "case.json"), "Final case manifest changed")
        for kind in ("direct", "method"):
            rows.append(audit_trial(output / kind / f"{kind}-{name}", case, kind=kind, task_hash=task_hash,
                                    core=core, runners=runners, candidate_files=candidates))
    direct = group((output / "direct").glob("*/summary.json"), kind="direct")
    method = group((output / "method").glob("*/summary.json"), kind="method")
    report = read(output / "report.json")
    require(report["direct"] == direct and report["method"] == method and report["comparison"] == compare(direct, method),
            "Published report differs from audited attempts")
    require(report["selection"] == selected and report["case_manifest_hashes"] == manifests, "Report selection or cases differ")
    return {"audit_pass": True, "paired_cases": count, "attempts": len(rows), "review_source_sha256": reader_hash,
            "selection_sha256": file_hash(selection), "report_sha256": file_hash(output / "report.json"), "rows": rows,
            "scope": "Read-only file provenance and fixed-rule recomputation; native save reload evidence comes from frozen reviews."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit(args.output, args.cases, args.policy, args.selection)
    except Exception as error:
        print(json.dumps({"audit_pass": False, "error": f"{type(error).__name__}: {error}"}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
