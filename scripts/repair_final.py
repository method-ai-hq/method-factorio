"""Paired final tests. Select and freeze a Method before this command."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

from repair_batch import candidate_hashes, file_hash, freeze, freeze_candidate, validate_resume
from repair_report import compare, group
from repair_review import VERSION as REVIEW_VERSION, provenance as review_provenance, review
from repair_trial import trial
from repair_verify import check_case


def lock_json(path, value, message):
    if path.exists() and json.loads(path.read_text()) != value:
        raise ValueError(message)
    if not path.exists():
        path.write_text(json.dumps(value, indent=2) + "\n")


def check_selection(policy, selection, expected_hash, selected):
    if file_hash(selection) != expected_hash:
        raise ValueError("Selection document changed during final tests")
    if selected["candidate_files"] != candidate_hashes(policy):
        raise ValueError("Selected Method changed before or during final tests")
    if selected.get("review_source_sha256") and selected["review_source_sha256"] != file_hash(Path(__file__).with_name("repair_review.py")):
        raise ValueError("Independent recipe reader changed during final tests")


def check_locked_case(case, expected_hash):
    if file_hash(case / "case.json") != expected_hash:
        raise ValueError("Final case changed after the case set was frozen")
    manifest, _, checks = check_case(case)
    if manifest["case_id"] != case.name or manifest["split"] != "final" or not all(checks.values()):
        raise ValueError("Uncertified final case: " + str(case))


def resume_result(output, case, policy, task_hash):
    if not output.exists():
        return None
    summary = output / "summary.json"
    if not summary.exists():
        raise RuntimeError("Incomplete final attempt retained: " + str(output))
    result = json.loads(summary.read_text())
    validate_resume(result, case, policy, task_hash)
    if result.get("status") == "infrastructure_failure":
        raise RuntimeError("Final infrastructure failure retained; inspect before further tests")
    if result.get("status") not in {"pass", "fail"}:
        raise RuntimeError("Final attempt has no completed outcome")
    return result


def run_final(cases_root, policy, selection, output_root, *, count=20):
    # count is exposed for offline tests. The public command fixes twenty cases.
    class Args:
        pass
    args = Args()
    args.cases, args.policy, args.selection, args.output = map(Path, (cases_root, policy, selection, output_root))
    args.count = count

    selected = json.loads(args.selection.read_text())
    selection_hash = file_hash(args.selection)
    check_selection(args.policy, args.selection, selection_hash, selected)
    args.output.mkdir(parents=True, exist_ok=True)
    selection_copy = args.output / "selection.json"
    lock_json(selection_copy, selected, "Cannot replace a Method after final tests start")
    lock_json(args.output / "selection-hash.json", {"sha256": selection_hash},
              "Selection source changed after final tests start")
    cases = [args.cases / f"final-{i:03d}" for i in range(1, args.count+1)]
    manifests = {}
    for case in cases:
        manifests[case.name] = file_hash(case / "case.json")
        check_locked_case(case, manifests[case.name])
    case_lock = args.output / "cases.json"
    lock_json(case_lock, manifests, "Final case set changed")
    for label in ("direct", "method"):
        (args.output / label).mkdir(exist_ok=True)
        freeze(args.output / label)
    freeze_candidate(args.output / "method", args.policy)

    def attempt(case, label, slot):
        policy = args.policy if label == "method" else None
        root = args.output / label
        frozen = freeze(root)
        freeze_candidate(root, policy)
        output = root / f"{label}-{case.name}"
        check_selection(args.policy, args.selection, selection_hash, selected)
        check_locked_case(case, manifests[case.name])
        result = resume_result(output, case, policy, frozen["task_sha256"])
        if result is None:
            result = trial(case, output, slot=slot, method=policy)
        if result["status"] in {"pass", "fail"}:
            reviewed_path = output / "review.json"
            if reviewed_path.exists():
                result = json.loads(reviewed_path.read_text())
                if (result.get("review_contract") != REVIEW_VERSION
                        or result.get("review_provenance") != review_provenance(output, case)):
                    raise RuntimeError("Saved recipe review no longer matches the original evidence")
            else:
                result = review(output, case, rcon_port=27970+slot, game_port=34970+slot)
        print(json.dumps({"approach": label, **{key: result.get(key) for key in
                           ("case_id", "status", "actions", "game_wall_seconds", "error")}}), flush=True)
        return result

    for case in cases:
        for label in ("direct", "method"):
            frozen = freeze(args.output / label)
            resume_result(args.output / label / f"{label}-{case.name}", case,
                          args.policy if label == "method" else None, frozen["task_sha256"])

    with ThreadPoolExecutor(max_workers=2) as pool:
        for case in cases:
            check_selection(args.policy, args.selection, selection_hash, selected)
            check_locked_case(case, manifests[case.name])
            # Check both retained outcomes before either missing arm can start.
            for label in ("direct", "method"):
                frozen = freeze(args.output / label)
                resume_result(args.output / label / f"{label}-{case.name}", case,
                              args.policy if label == "method" else None, frozen["task_sha256"])
            futures = [pool.submit(attempt, case, label, slot)
                       for slot, label in enumerate(("direct", "method"))]
            results = [future.result() for future in futures]
            if any(r["status"] == "infrastructure_failure" for r in results):
                raise RuntimeError("Final infrastructure failure retained; inspect before further tests")
    check_selection(args.policy, args.selection, selection_hash, selected)
    for case in cases:
        check_locked_case(case, manifests[case.name])
    direct = group((args.output / "direct").glob("direct-final-*/summary.json"))
    method = group((args.output / "method").glob("method-final-*/summary.json"))
    if any(g["recipe_reviewed_attempts"] != len(cases) for g in (direct, method)):
        raise RuntimeError("Every final attempt must use the same independent recipe reader")
    report = {"direct": direct, "method": method, "comparison": compare(direct, method),
              "selection": selected, "case_manifest_hashes": manifests}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["comparison"], indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, choices=[20], default=20)
    args = parser.parse_args()
    run_final(args.cases, args.policy, args.selection, args.output, count=args.count)


if __name__ == "__main__":
    main()
