"""Reload one terminal save and compare its paused game state with the host record."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import time

from factorio_rcon import RCONClient
from automatic_evaluator import SNAPSHOT, SNAPSHOT_FUNCTION


def inspect(run, rcon_port, game_port, deadline):
    started = time.time()
    deadline = min(deadline, started + 30)
    review = run / "save-inspection"
    review.mkdir(exist_ok=False, mode=0o700)
    terminal = run / "game/final.zip"
    shutil.copyfile(terminal, review / "inspection.zip")
    factorio = "/Applications/factorio.app/Contents/MacOS/factorio"
    (review / "config.ini").write_text("[path]\nread-data=/Applications/factorio.app/Contents/data\nwrite-data=" + str(review) + "\n")
    password = secrets.token_urlsafe(32)
    output = {"passed": False, "save_sha256": hashlib.sha256(terminal.read_bytes()).hexdigest()}
    server = None
    try:
        with (review / "server.log").open("w") as log:
            (review / "server.log").chmod(0o600)
            server = subprocess.Popen([factorio, "--config", str(review / "config.ini"),
                "--mod-directory", str(run / "game/mods"), "--start-server", str(review / "inspection.zip"),
                "--bind", f"127.0.0.1:{game_port}", "--rcon-bind", f"127.0.0.1:{rcon_port}",
                "--rcon-password", password, "--server-settings", str(run / "game/server.json")],
                stdout=log, stderr=log)
            def stop(signum, frame):
                raise InterruptedError("Save inspection was stopped")
            signal.signal(signal.SIGTERM, stop)
            signal.signal(signal.SIGINT, stop)
            while time.time() < deadline - 3:
                if server.poll() is not None:
                    raise RuntimeError("The terminal save server stopped; read the private log")
                client = None
                try:
                    client = RCONClient("127.0.0.1", rcon_port, password, timeout=min(2, max(.1, deadline-time.time()-3)))
                    # The saved game must already be paused. Do not advance or repair it.
                    client.send_command("/sc " + SNAPSHOT_FUNCTION)
                    state = json.loads(client.send_command("/sc " + SNAPSHOT))
                    break
                except Exception:
                    time.sleep(.1)
                finally:
                    if client:
                        client.close()
            else:
                raise TimeoutError("The terminal save inspection reached its deadline")
            (review / "state.json").write_text(json.dumps(state, indent=2) + "\n")
            expected = json.loads((run / "final.json").read_text())
            fields = ("tick", "paused", "speed", "position", "inventory", "entities", "furnaces", "research", "iron_plates_produced", "iron_ore_remaining", "enemies")
            # Dictionary order is not semantic. Preserve all list positions and values.
            def canonical(value):
                if isinstance(value, list):
                    return [canonical(v) for v in value]
                if isinstance(value, dict):
                    return {k: canonical(v) for k, v in sorted(value.items())}
                return value
            checks = {k: k in state and k in expected and canonical(state[k]) == canonical(expected[k]) for k in fields}
            checks["paused_before_reload"] = expected.get("paused") is True
            checks["paused_after_reload"] = state.get("paused") is True
            output.update({"passed": all(checks.values()), "checks": checks})
    except Exception as error:
        output["error"] = str(error)
    finally:
        if server and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=max(.1, min(2, deadline - time.time())))
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=1)
        output["wall_seconds"] = time.time() - started
        (review / "result.json").write_text(json.dumps(output, indent=2) + "\n")
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--rcon-port", type=int, required=True)
    parser.add_argument("--game-port", type=int, required=True)
    parser.add_argument("--job-deadline", type=float, required=True)
    args = parser.parse_args()
    if time.time() >= args.job_deadline - 3:
        raise SystemExit("The job deadline does not allow a save inspection")
    output = inspect(args.run.resolve(), args.rcon_port, args.game_port, args.job_deadline)
    print(json.dumps(output, indent=2))
    return 0 if output["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
