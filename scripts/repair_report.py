"""Report strict scores separately from restored production and run faults."""
import argparse
import json
import math
from pathlib import Path
import statistics


def median(values):
    return statistics.median(values) if values else None


TOKEN_FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens")


def sessions(path, result):
    """Count saved session folders even when shutdown lost execution.json."""
    execution = result.get("execution", {})
    if result["kind"] == "direct":
        folders = [path.parent / "codex"] if (path.parent / "codex").is_dir() else []
        fallback = [execution] if execution else []
    else:
        folders = sorted(p for p in (path.parent / "method/codex").glob("*") if p.is_dir())
        fallback = execution.get("codex_runs", [])
    if not folders:
        return fallback
    calls = []
    for folder in folders:
        record = folder / "execution.json"
        try:
            calls.append(json.loads(record.read_text()))
        except (FileNotFoundError, json.JSONDecodeError):
            calls.append({"status": "missing_execution", "evidence": str(folder.resolve())})
    return calls


def known_sum(rows, key):
    values = [r[key] for r in rows if r.get(key) is not None]
    return sum(values) if values else None


def valid_time(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def summarize(path):
    result = json.loads(path.read_text())
    verdict = result.get("verdict", {})
    windows = verdict.get("windows", [])
    production = (len(windows) == 3 and all(w.get("passed") is True for w in windows)
                  and bool(verdict.get("verification"))
                  and all(value is True for key, value in verdict["verification"].items()
                          if key != "finish_is_last_action"))
    execution = result.get("execution", {})
    calls = sessions(path, result)
    known = [c["usage"] for c in calls if c.get("usage", {}).get("usage_known") is True
             and all(type(c["usage"].get(key)) is int and c["usage"][key] >= 0 for key in TOKEN_FIELDS)]
    final_known = [c for c in calls if c.get("status") == "completed"
                   and c.get("usage") in known and not c.get("usage", {}).get("errors")]
    complete = len(final_known) == len(calls)
    known_tokens = {key: sum(c[key] for c in known) if known else (0 if not calls else None)
                    for key in TOKEN_FIELDS}
    failed_rules = [key for key, value in verdict.get("checks", {}).items() if not value]
    failure = ("none" if result["scored_pass"] else "infrastructure" if result["status"] == "infrastructure_failure"
               else "request_rule" if production and failed_rules == ["no_play_after_finish"]
               else "time_limit" if execution.get("status") == "timeout" or any(c.get("status") == "timeout" for c in calls)
               else "production_or_completion")
    return {"case_id": result["case_id"], "status": result["status"],
            "strict_pass": result["scored_pass"], "restored_production": production,
            "failure": failure, "failed_rules": failed_rules,
            "actions": result.get("actions"), "game_wall_seconds": result.get("game_wall_seconds"),
            "total_wall_seconds": result.get("total_wall_seconds"), "agent_sessions": len(calls),
            "sessions_with_known_usage": len(known), "sessions_without_final_usage": len(calls)-len(final_known),
            "sessions_missing_execution": sum(c.get("status") == "missing_execution" for c in calls),
            "usage_complete": complete,
            **{"known_" + key: value for key, value in known_tokens.items()},
            **{"total_" + key: value if complete else None for key, value in known_tokens.items()},
            "case_sha256": result.get("case_sha256"), "task_sha256": result.get("task_sha256"),
            "evidence": str(path.resolve())}


def group(paths, kind=None):
    paths = [path for path in paths if kind is None or json.loads(path.read_text()).get("kind") == kind]
    rows = sorted((summarize(path) for path in paths), key=lambda r: r["case_id"])
    if len({r["case_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate case attempts: select one declared attempt per case")
    successful = [r for r in rows if r["strict_pass"]]
    return {"attempts": len(rows), "strict_passes": len(successful),
            "restored_production": sum(r["restored_production"] for r in rows),
            "failure_counts": {key: sum(r["failure"] == key for r in rows) for key in
                               ("request_rule", "time_limit", "production_or_completion", "infrastructure")},
            "median_success_seconds": median([r["game_wall_seconds"] for r in successful if valid_time(r["game_wall_seconds"])]),
            "total_game_wall_seconds": (sum(r["game_wall_seconds"] for r in rows)
                                        if all(valid_time(r["game_wall_seconds"]) for r in rows) else None),
            "agent_sessions": sum(r["agent_sessions"] for r in rows),
            "sessions_without_final_usage": sum(r["sessions_without_final_usage"] for r in rows),
            "sessions_missing_execution": sum(r["sessions_missing_execution"] for r in rows),
            "sessions_with_known_usage": sum(r["sessions_with_known_usage"] for r in rows),
            "usage_complete": all(r["usage_complete"] for r in rows),
            **{"known_" + key: known_sum(rows, "known_" + key) for key in TOKEN_FIELDS},
            **{"total_" + key: known_sum(rows, "total_" + key) if all(r["usage_complete"] for r in rows) else None
               for key in TOKEN_FIELDS}, "rows": rows}


def compare(direct, method, *, allow_partial=False):
    a = {r["case_id"]: r for r in direct["rows"]}
    b = {r["case_id"]: r for r in method["rows"]}
    if len(a) != len(direct["rows"]) or len(b) != len(method["rows"]):
        raise ValueError("Duplicate cases cannot be paired")
    partial = a.keys() != b.keys()
    if partial and not allow_partial:
        raise ValueError("Comparison case sets do not match")
    pairs = [(a[key], b[key]) for key in sorted(a.keys() & b.keys())]
    if any(not x.get("case_sha256") or not x.get("task_sha256") or x["case_sha256"] != y.get("case_sha256") or x["task_sha256"] != y.get("task_sha256") for x, y in pairs):
        raise ValueError("Comparison cases or public instructions do not match")
    outcomes = {"both_pass": 0, "direct_only": 0, "method_only": 0, "neither_pass": 0}
    for x, y in pairs:
        key = "both_pass" if x["strict_pass"] and y["strict_pass"] else "direct_only" if x["strict_pass"] else "method_only" if y["strict_pass"] else "neither_pass"
        outcomes[key] += 1
    common = [(x, y) for x, y in pairs if x["strict_pass"] and y["strict_pass"]]
    timed = [(x, y) for x, y in common if valid_time(x["game_wall_seconds"]) and valid_time(y["game_wall_seconds"])]
    n = outcomes["direct_only"] + outcomes["method_only"]
    tail = min(outcomes["direct_only"], outcomes["method_only"])
    p = min(1, 2*sum(math.comb(n, k) for k in range(tail+1))/2**n) if n else 1
    return {"paired_cases": len(pairs), "partial_comparison": partial,
            "unmatched_direct_cases": sorted(a.keys() - b.keys()),
            "unmatched_method_cases": sorted(b.keys() - a.keys()),
            "unmatched_direct_count": len(a.keys() - b.keys()),
            "unmatched_method_count": len(b.keys() - a.keys()),
            **outcomes, "exact_paired_two_sided_p": p if pairs and not partial else None,
            "common_success_timed_pairs": len(timed),
            "common_success_pairs_missing_time": len(common) - len(timed),
            "common_success_direct_median_seconds": median([x["game_wall_seconds"] for x, _ in timed]),
            "common_success_method_median_seconds": median([y["game_wall_seconds"] for _, y in timed]),
            "common_success_median_speed_ratio": median([x["game_wall_seconds"]/y["game_wall_seconds"] for x, y in timed])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--direct", type=Path, required=True)
    parser.add_argument("--method", type=Path)
    parser.add_argument("--split", choices=["development", "final"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-partial", action="store_true", help="Compare only matched development cases and show unmatched cases")
    args = parser.parse_args()
    if args.allow_partial and args.split != "development":
        parser.error("Partial comparison is only for development progress")
    pattern = f"*-{args.split}-*/summary.json"
    direct = group(args.direct.glob(pattern), kind="direct")
    report = {"split": args.split, "direct": direct,
              "cost_note": "Subscription dollar cost unknown. Known token subtotals include reported partial usage. Total tokens are unknown when final session usage is missing. Agent sessions are not model request counts."}
    if args.method:
        method = group(args.method.glob(pattern), kind="method")
        report.update(method=method, comparison=compare(direct, method, allow_partial=args.allow_partial))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: {k: v for k, v in value.items() if k != "rows"} if isinstance(value, dict) else value
                      for key, value in report.items()}, indent=2))


if __name__ == "__main__":
    main()
