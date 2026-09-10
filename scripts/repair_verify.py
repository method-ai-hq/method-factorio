"""Reload repair saves and check the frozen case and independent evidence."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import tempfile

from repair_contract import CONTRACT, RULES, digest, evaluate, public_case
from science_server import FACTORIO, Server
from science_contract import evaluate as science_evaluate


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def linked_file(case_dir, entry, kind):
    root = case_dir.resolve()
    relative = Path(entry[kind + "_path"])
    if relative.is_absolute():
        raise ValueError("Certificate evidence paths must be relative")
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("Certificate evidence is missing or outside the case")
    if file_hash(path) != entry[kind + "_sha256"]:
        raise ValueError("Certificate evidence hash does not match: " + kind)
    return path


def check_case(case_dir):
    """Check supervisor files. These files are never sent to the playing model."""
    case_dir = Path(case_dir)
    manifest = json.loads((case_dir / "case.json").read_text())
    initial = json.loads((case_dir / "initial.json").read_text())
    certificate = json.loads((case_dir / "certificate.json").read_text())
    checks = {
        "case_save_hash": file_hash(case_dir / "broken.zip") == manifest["broken_save_sha256"],
        "case_initial_hash": digest(initial) == manifest["initial_sha256"],
        "certificate_hash": file_hash(case_dir / "certificate.json") == manifest["certificate_sha256"],
        "certificate_binding": all(certificate[k] == manifest[k] for k in
                                   ("case_id", "rules_hash", "broken_save_sha256", "initial_sha256")),
        "certificate_rules": certificate["rules_hash"] == digest(RULES),
    }
    for name in ("healthy", "broken", "recoverable"):
        entry = certificate[name]
        paths = {kind: linked_file(case_dir, entry, kind) for kind in ("record", "save", "verdict")}
        evidence = json.loads(paths["record"].read_text())
        verdict = json.loads(paths["verdict"].read_text())
        wanted = name != "broken"
        checks[name + "_native_evidence"] = (
            entry["production_pass"] is wanted
            and verdict["production_pass"] is wanted
            and science_evaluate(evidence)["production_pass"] is wanted
            and bool(verdict["verification"])
            and all(v is True for v in verdict["verification"].values())
            and verdict["save_sha256"] == entry["save_sha256"]
            and bool(evidence["measurement"]["samples"])
            and evidence["measurement"]["done"] is True
            and evidence["final"]["paused"] is True
            and (verdict["scored_pass"] is True if wanted else entry["verification_pass"] is True)
        )
    return manifest, initial, checks


def install(server):
    server.install()
    runtime = Path(__file__).with_name("repair_runtime.lua")
    if runtime.exists():
        result = server.command(runtime.read_text() + '\nrcon.print("repair installed")')
        if result.strip() != "repair installed":
            raise RuntimeError("Repair runtime installation failed")


def verify(run, case_dir, *, rcon_port=27941, game_port=34941, factorio=FACTORIO):
    from repair_host import sources
    run, case_dir = Path(run), Path(case_dir)
    output = {"scored_pass": False, "production_pass": False, "checks": {}, "windows": [], "verification": {}}
    try:
        manifest, initial, checks = check_case(case_dir)
        output["verification"] = checks
        expected = json.loads((run / "record.json").read_text())
        save = run / "game/world.zip"
        output["save_sha256"] = file_hash(save)
        with tempfile.TemporaryDirectory(prefix="repair-verify-", dir=run) as temp:
            with Server(Path(temp) / "terminal", save=save, rcon_port=rcon_port,
                        game_port=game_port, factorio=factorio) as server:
                # Install functions only. Do not pause, advance, or repair the save.
                install(server)
                actual = server.read("storage.science")
                final = server.read("science_snapshot()")
            with Server(Path(temp) / "initial", save=case_dir / "broken.zip", rcon_port=rcon_port,
                        game_port=game_port, factorio=factorio) as server:
                install(server)
                native_initial = server.read("science_snapshot()")
        checks.update({
            "saved_record_matches": actual == {k: v for k, v in expected.items() if k not in ("final", "host_error")},
            "saved_state_matches": final == expected["final"],
            "paused_save": final["paused"] is True,
            "source_matches": actual["sources"] == sources(),
            "host_completed": not expected.get("host_error"),
            "run_case_matches": actual["case"] == public_case(manifest),
            "run_initial_matches": actual["initial"] == initial,
            "native_initial_matches": native_initial == initial,
            "native_initial_paused": native_initial["paused"] is True,
        })
        trace = (run / "actions.jsonl").read_bytes()
        rows = [json.loads(line) for line in trace.decode().splitlines()]
        audit = actual["audit"]
        checks["complete_action_trace"] = len(rows) == audit["actions"]
        checks["action_trace_hash"] = hashlib.sha256(trace).hexdigest() == audit["trace_sha256"]
        finishes = [i for i, row in enumerate(rows) if isinstance(row["request"], dict)
                    and row["request"].get("action") == "finish" and row["response"].get("ok") is True]
        checks["finish_is_last_action"] = finishes == [len(rows) - 1]
        times = [row["elapsed_seconds"] for row in rows]
        checks["trace_times"] = (all(type(t) in (int, float) and math.isfinite(t)
                                           and 0 <= t <= audit["elapsed_seconds"] for t in times)
                                 and times == sorted(times))
        last = actual["measurement"]["samples"][-1]
        checks["no_changes_after_measurement"] = (
            {k: v for k, v in final.items() if k != "paused"}
            == {k: v for k, v in last.items() if k != "paused"})
        checks["measurement_start"] = (actual["initial"]["tick"] <= actual["measurement"]["start"]
                                       == actual["clean"]["tick"])
        output.update(evaluate(actual))
        output["scored_pass"] = output["production_pass"] and all(checks.values())
    except Exception as error:
        output["error"] = str(error)
    (run / "verdict.json").write_text(json.dumps(output, indent=2) + "\n")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--case", required=True, type=Path, dest="case_dir")
    parser.add_argument("--rcon-port", type=int, default=27941)
    parser.add_argument("--game-port", type=int, default=34941)
    parser.add_argument("--factorio", default=FACTORIO)
    args = parser.parse_args()
    result = verify(args.run.resolve(), args.case_dir.resolve(), rcon_port=args.rcon_port,
                    game_port=args.game_port, factorio=args.factorio)
    print(json.dumps(result, indent=2))
    return 0 if result["scored_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
