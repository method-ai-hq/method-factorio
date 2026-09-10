"""Run operator-only live science checker tests. No model calls or recordings."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

from science_host import action, finalize, setup, sources
from science_reference import build
from science_server import ROOT, Server
from science_verify import verify

CASES = ["working_http", "empty", "red_only", "no_power", "copper_disconnected",
         "wrong_recipe", "stored_material", "two_windows", "forbidden_transfer", "post_finish"]


def http_reference(run):
    started = time.monotonic()
    process = None
    with (run / "host.log").open("w") as log:
        try:
            process = subprocess.Popen([sys.executable, str(ROOT / "scripts/science_host.py"),
                "--run", run.name + "-host", "--seed", "0", "--port", "18885",
                "--rcon-port", "27885", "--game-port", "34885"],
                cwd=ROOT, stdout=log, stderr=log)

            def send(req):
                request = urllib.request.Request("http://127.0.0.1:18885/action",
                    json.dumps(req).encode(), {"Content-Type": "application/json"})
                with urllib.request.urlopen(request, timeout=20) as response:
                    return json.load(response)

            while time.monotonic() - started < 45:
                if process.poll() is not None:
                    raise RuntimeError("HTTP host failed: " + (run / "host.log").read_text()[-1000:])
                if '"ready": true' in (run / "host.log").read_text():
                    break
                time.sleep(.1)
            else:
                raise TimeoutError("HTTP host was not ready")
            with (run / "client-actions.jsonl").open("w", buffering=1) as trace:
                build(None, trace, started, send=send)
                response = send({"action": "finish"})
                if not response["ok"]:
                    raise RuntimeError(str(response))
            process.wait(timeout=60)
            if process.returncode:
                raise RuntimeError("HTTP host did not close cleanly")
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=5)
    return ROOT / "runs" / (run.name + "-host")


def direct_case(run, case):
    started = time.monotonic()
    with Server(run / "game", rcon_port=27885, game_port=34885) as server:
        setup(server, 0)
        error = None
        with (run / "actions.jsonl").open("w", buffering=1) as trace:
            def call(req):
                response = action(server, req)
                trace.write(json.dumps({"request": req, "response": response,
                                       "elapsed_seconds": time.monotonic()-started}) + "\n")
                return response
            try:
                layout = build(server, trace, started) if case != "empty" else None
                if case in ("red_only", "wrong_recipe"):
                    n = layout["green"]
                    req = {"action": "pickup" if case == "red_only" else "recipe",
                           "name": "assembling-machine-3", "position": {"x": n["x"], "y": n["y"]}}
                    if case == "wrong_recipe":
                        req["recipe"] = "automation-science-pack"
                    assert call(req)["ok"]
                if case in ("no_power", "stored_material", "copper_disconnected"):
                    for e in server.read("science_snapshot()")["entities"]:
                        remove = case == "no_power" and e["type"] == "solar-panel"
                        remove = remove or (case == "stored_material" and e["type"] == "mining-drill")
                        copper = case == "copper_disconnected" and e["type"] == "mining-drill" and abs(e["position"]["x"]-.5) == 70
                        if remove or copper:
                            assert call({"action": "pickup" if remove else "rotate", "name": e["name"],
                                         "position": e["position"], "direction": "DOWN"})["ok"]
                if case == "stored_material":
                    server.command("for _,e in pairs(game.surfaces[1].find_entities_filtered{type='container'}) do "
                                   "e.insert{name='automation-science-pack',count=1000}; "
                                   "e.insert{name='logistic-science-pack',count=1000} end")
                if case == "forbidden_transfer":
                    assert not call({"action": "insert", "item": "iron-plate", "quantity": 100})["ok"]
                assert call({"action": "finish"})["ok"]
                if case == "post_finish":
                    assert not call({"action": "observe"})["ok"]
                if case == "two_windows":
                    server.command("local previous=script.get_event_handler(defines.events.on_tick); "
                        "script.on_event(defines.events.on_tick,function(event) previous(event); "
                        "if event.tick-storage.science.measurement.start==14400 then "
                        "for _,e in pairs(game.surfaces[1].find_entities_filtered{type='assembling-machine'}) "
                        "do e.active=false end end end)")
                deadline = time.monotonic() + 60
                while not server.read("storage.science.measurement.done"):
                    if time.monotonic() > deadline:
                        raise TimeoutError("Live checker test timed out")
                    time.sleep(.2)
            except BaseException as exc:
                error = str(exc)
                raise
            finally:
                finalize(server, run, time.monotonic()-started, error)
    if server.process.returncode != 0:
        raise RuntimeError("Fixture did not save cleanly")
    return run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--cases", nargs="+", choices=CASES, default=CASES)
    args = parser.parse_args()
    if Path(args.run).name != args.run or args.run in (".", ".."):
        parser.error("run must be a new plain folder name")
    root = ROOT / "runs" / args.run
    root.mkdir(parents=True, exist_ok=False)
    summary = {"kind": "operator checker validation, not policy search", "sources": sources(), "cases": []}
    for case in args.cases:
        run = root / case
        run.mkdir()
        # The host requires a flat unique run name, so give the HTTP wrapper one.
        if case == "working_http":
            wrapper = ROOT / "runs" / (args.run + "-http")
            wrapper.mkdir()
            result_dir = http_reference(wrapper)
        else:
            result_dir = direct_case(run, case)
        result = verify(result_dir)
        expected = case == "working_http"
        passed = result["scored_pass"] == expected and all(
            value for name,value in result.get("verification", {}).items()
            if name != "finish_is_last_action" or case != "post_finish")
        if case == "two_windows":
            passed = passed and [w["passed"] for w in result.get("windows", [])] == [True, True, False]
        row = {"case": case, "expected_accept": expected, "test_passed": passed,
               "directory": str(result_dir), "verdict": result}
        summary["cases"].append(row)
        (root / "summary.json").write_text(json.dumps(summary, indent=2)+"\n")
        print(json.dumps({"case": case, "test_passed": passed, "accepted": result["scored_pass"],
                          "error": result.get("error"), "verification": result.get("verification")}), flush=True)
    summary["passed"] = all(r["test_passed"] for r in summary["cases"])
    (root / "summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
