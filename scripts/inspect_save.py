"""Load a terminal save in a separate native server and read its game state."""
import argparse
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import time

from factorio_rcon import RCONClient
from control_test import SNAPSHOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    review = run / "save-inspection"
    review.mkdir(exist_ok=False)
    shutil.copyfile(run / "game/final.zip", review / "inspection.zip")
    factorio = "/Applications/factorio.app/Contents/MacOS/factorio"
    (review / "config.ini").write_text("[path]\nread-data=/Applications/factorio.app/Contents/data\nwrite-data="+str(review)+"\n")
    password = secrets.token_urlsafe(32)
    with (review / "server.log").open("w") as log:
        (review / "server.log").chmod(0o600)
        server = subprocess.Popen([factorio, "--config", str(review / "config.ini"),
            "--mod-directory", str(run / "game/mods"), "--start-server", str(review / "inspection.zip"),
            "--bind", "127.0.0.1:34218", "--rcon-bind", "127.0.0.1:27118",
            "--rcon-password", password, "--server-settings", str(run / "game/server.json")],
            stdout=log, stderr=log)
        try:
            for _ in range(60):
                if server.poll() is not None:
                    raise RuntimeError("Saved game did not load; inspect the private log")
                try:
                    client = RCONClient("127.0.0.1",27118,password,timeout=5)
                    result = client.send_command("/sc " + SNAPSHOT)
                    state = json.loads(result)
                    client.close()
                    break
                except Exception:
                    time.sleep(0.25)
            else:
                raise RuntimeError("Saved game inspection timed out")
            (review / "state.json").write_text(json.dumps(state,indent=2))
            final = json.loads((run / "final.json").read_text())
            fields = ("position", "inventory", "furnaces", "research", "iron_plates_produced", "enemies")
            checks = {k:state[k]==final[k] for k in fields}
            output = {"passed":all(checks.values()),"checks":checks,"state":state}
            print(json.dumps(output,indent=2))
            return 0 if output["passed"] else 1
        finally:
            server.terminate()
            try: server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server.kill();server.wait()


if __name__=="__main__":
    raise SystemExit(main())
