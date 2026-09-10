"""Independently reload a science trial's terminal save, then apply fixed rules."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from science_contract import evaluate
from science_server import FACTORIO, Server


def verify(run, *, rcon_port=27881, game_port=34881, factorio=FACTORIO):
    from science_host import sources
    output = {"scored_pass": False, "production_pass": False}
    try:
        expected = json.loads((run / "record.json").read_text())
        save = run / "game/world.zip"
        output["save_sha256"] = hashlib.sha256(save.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="science-verify-", dir=run) as temp:
            with Server(Path(temp) / "server", save=save, rcon_port=rcon_port,
                        game_port=game_port, factorio=factorio) as server:
                # Do not repair, advance or pause the saved game before inspection.
                server.install()
                actual = server.read("storage.science")
                final = server.read("science_snapshot()")
        saved_expected = {k: v for k, v in expected.items() if k not in ("final", "host_error")}
        checks = {"saved_record_matches": actual == saved_expected,
                  "saved_state_matches": final == expected["final"],
                  "paused_save": final["paused"] is True,
                  "source_matches": actual["sources"] == sources(),
                  "host_completed": not expected.get("host_error")}
        rows = [json.loads(line) for line in (run / "actions.jsonl").read_text().splitlines()]
        checks["complete_action_trace"] = len(rows) == actual["audit"]["actions"]
        checks["action_trace_hash"] = hashlib.sha256((run / "actions.jsonl").read_bytes()).hexdigest() == actual["audit"]["trace_sha256"]
        finishes = [i for i, row in enumerate(rows) if isinstance(row["request"], dict)
                    and row["request"].get("action") == "finish"
                    and row["response"].get("ok") is True]
        checks["finish_is_last_action"] = finishes == [len(rows) - 1]
        output.update(evaluate(actual))
        output["verification"] = checks
        output["scored_pass"] = output["production_pass"] and all(checks.values())
    except Exception as error:
        output["error"] = str(error)
    (run / "verdict.json").write_text(json.dumps(output, indent=2) + "\n")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--rcon-port", type=int, default=27881)
    parser.add_argument("--game-port", type=int, default=34881)
    parser.add_argument("--factorio", default=FACTORIO)
    args = parser.parse_args()
    result = verify(args.run.resolve(), rcon_port=args.rcon_port, game_port=args.game_port, factorio=args.factorio)
    print(json.dumps(result, indent=2))
    return 0 if result["scored_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
