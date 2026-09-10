"""Run one frozen, certified factory-repair case behind the restricted endpoint."""
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import signal
import time

from repair_contract import CONTRACT, RULES, SPARES, public_case
from science_contract import digest
from science_host import finalize
from science_server import FACTORIO, ROOT, Server

SOURCE_FILES = ["science_contract.py", "science_runtime.lua", "science_server.py",
                "science_host.py", "repair_contract.py", "repair_runtime.lua",
                "repair_host.py", "repair_verify.py"]


def sources():
    return {name: hashlib.sha256((ROOT / "scripts" / name).read_bytes()).hexdigest()
            for name in SOURCE_FILES}


def install(server):
    server.install()
    result = server.command((ROOT / "scripts/repair_runtime.lua").read_text() + '\nrcon.print("installed")')
    if result.strip() != "installed":
        raise RuntimeError("Repair observations failed to install: " + result)


def start_case(server, case_dir):
    case = public_case(json.loads((case_dir / "case.json").read_text()))
    if case["rules_hash"] != digest(RULES):
        raise ValueError("Case was prepared under different repair rules")
    if hashlib.sha256((case_dir / "broken.zip").read_bytes()).hexdigest() != case["broken_save_sha256"]:
        raise ValueError("Starting save does not match the frozen case")
    install(server)
    initial = server.read("science_snapshot()")
    expected = json.loads((case_dir / "initial.json").read_text())
    if initial != expected or digest(initial) != case["initial_sha256"] or initial["paused"] is not True:
        raise ValueError("Starting save state does not match the frozen case")
    if initial["inventory"] != SPARES:
        raise ValueError("Starting repair supplies do not match")
    config = {"case": case, "sources": sources(), "rules": RULES,
              "repair_contract": CONTRACT, "repair_rules_hash": digest(RULES)}
    code = "local config=helpers.json_to_table(" + json.dumps(json.dumps(config)) + "); "
    code += "local b=storage.science; for k,v in pairs(config) do b[k]=v end; "
    code += "b.initial=science_snapshot(); b.contract=config.repair_contract; b.rules_hash=config.repair_rules_hash; "
    code += "b.finished=false; b.measurement=nil; b.clean=nil; b.audit={actions=0,violations=0,elapsed_seconds=0}; "
    code += "script.on_event(defines.events.on_tick,nil); game.tick_paused=false; rcon.print('started')"
    if server.command(code).strip() != "started":
        raise RuntimeError("Could not start the repair case")
    return initial


def action(server, request):
    encoded = json.dumps(json.dumps(request, separators=(",", ":"), allow_nan=False))
    return server.read("(function() local ok,result=pcall(repair_action,helpers.json_to_table(" + encoded +
                       ")); return {ok=ok,result=ok and result or nil,error=not ok and tostring(result) or nil} end)()")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--port", type=int, default=18940)
    parser.add_argument("--rcon-port", type=int, default=27940)
    parser.add_argument("--game-port", type=int, default=34940)
    parser.add_argument("--factorio", default=FACTORIO)
    args = parser.parse_args()
    case_dir, run = args.case.resolve(), args.run.resolve()
    run.mkdir(parents=True, exist_ok=False)
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    started = None
    with Server(run / "game", rcon_port=args.rcon_port, game_port=args.game_port,
                factorio=args.factorio, save=case_dir / "broken.zip") as server:
        initial = start_case(server, case_dir)
        started = time.monotonic()
        error = None
        with (run / "actions.jsonl").open("w", buffering=1) as trace:
            def execute(req):
                elapsed = time.monotonic() - started
                if elapsed >= RULES["seconds"]:
                    raise TimeoutError("Repair trial time limit reached")
                try:
                    result = action(server, req)
                except (TypeError, ValueError):
                    result = action(server, {"action": "invalid_request"})
                trace.write(json.dumps({"request": req, "elapsed_seconds": elapsed, "response": result}) + "\n")
                return result

            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *_): pass

                def do_POST(self):
                    self.connection.settimeout(3)
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        if self.path != "/action" or not 0 < length <= 65536:
                            raise ValueError("Invalid action request")
                        req = json.loads(self.rfile.read(length), parse_constant=lambda _: None)
                    except Exception:
                        req = {"action": "invalid_request"}
                    try:
                        if isinstance(req, dict) and set(req) == {"batch"}:
                            batch = req["batch"]
                            if not isinstance(batch, list) or not 1 <= len(batch) <= 50:
                                response = execute({"action": "invalid_batch"})
                            else:
                                results = []
                                for request in batch:
                                    results.append(execute(request))
                                    if not results[-1]["ok"]: break
                                response = {"ok": all(r["ok"] for r in results), "results": results}
                        else:
                            response = execute(req)
                    except Exception as exc:
                        response = {"ok": False, "error": str(exc)}
                    payload = json.dumps(response).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    try:
                        self.wfile.write(payload)
                    except (BrokenPipeError, ConnectionResetError): pass

            try:
                with HTTPServer(("127.0.0.1", args.port), Handler) as http:
                    http.timeout = .1
                    ready = {"ready": True, "endpoint": f"http://127.0.0.1:{args.port}/action",
                             "contract": CONTRACT, "case_id": json.loads((case_dir / "case.json").read_text())["case_id"],
                             "deadline_epoch": time.time() + RULES["seconds"]}
                    (run / "ready.json").write_text(json.dumps(ready))
                    print(json.dumps(ready), flush=True)
                    while not stopping and time.monotonic()-started < RULES["seconds"]:
                        http.handle_request()
                        if server.read("storage.science.measurement and storage.science.measurement.done or false"):
                            break
            except BaseException as exc:
                error = str(exc)
                raise
            finally:
                finalize(server, run, time.monotonic()-started, error)
    if server.process.returncode != 0:
        raise RuntimeError("Terminal save not confirmed by clean Factorio exit")
    print(json.dumps({"saved": True}), flush=True)


if __name__ == "__main__":
    main()
