"""Headless science task. Public HTTP actions cannot invoke game administration."""
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import math
from pathlib import Path
import random
import signal
import time

from science_contract import CONTRACT, KIT, ITEMS, RECIPES, RULES, digest
from science_server import FACTORIO, ROOT, Server


def sources():
    return {name: hashlib.sha256((ROOT / "scripts" / name).read_bytes()).hexdigest()
            for name in ["science_contract.py", "science_runtime.lua", "science_server.py",
                         "science_host.py", "science_verify.py"]}


def patches(seed):
    # Eight separate deposits. Seed zero is reserved for the checker reference.
    kinds = ["copper-ore", "iron-ore", "iron-ore", "iron-ore",
             "iron-ore", "iron-ore", "iron-ore", "copper-ore"]
    rng = random.Random(seed)
    if seed:
        rng.shuffle(kinds)
    return [{"name": name, "x": -70 + i * 20, "y": 80 if seed == 0 else rng.randrange(68, 93),
             "radius": 3, "amount": 10000} for i, name in enumerate(kinds)]


def setup(server, seed):
    config = {"contract": CONTRACT, "rules_hash": digest(RULES), "rules": RULES,
              "inventory": KIT, "items": ITEMS, "recipes": RECIPES, "patches": patches(seed),
              "seed": seed, "sources": sources(), "audit": {"actions": 0, "violations": 0,
                                                           "elapsed_seconds": 0}}
    encoded = json.dumps(json.dumps(config, separators=(",", ":")))
    code = """
game.tick_paused=true
local s=game.surfaces[1]
s.request_to_generate_chunks({0,0},5); s.force_generate_chunk_requests()
for _,e in pairs(s.find_entities()) do e.destroy() end
local tiles={}
for x=-128,128 do for y=-128,128 do table.insert(tiles,{name='grass-1',position={x,y}}) end end
s.set_tiles(tiles); s.always_day=true; s.daytime=0
local f=game.forces.player
f.reset()
for _,t in pairs(f.technologies) do t.researched=false end
""" + "storage.science=helpers.json_to_table(" + encoded + ")\n" + """
for _,p in ipairs(storage.science.patches) do
  for x=p.x-p.radius,p.x+p.radius do for y=p.y-p.radius,p.y+p.radius do
    s.create_entity{name=p.name,position={x,y},amount=p.amount}
  end end
end
for _,r in ipairs(storage.science.recipes) do f.recipes[r].enabled=true end
storage.science.mods={}
for name,version in pairs(script.active_mods) do
  if name~='core' then storage.science.mods[name]=version end
end
storage.science.game_version=script.active_mods['base']
game.speed=20
rcon.print('ready')
"""
    result = server.command(code)
    if result.strip() != "ready":
        raise RuntimeError("Science setup failed: " + result)
    server.install()
    server.command("storage.science.initial=science_snapshot(); game.tick_paused=false")
    return server.read("storage.science.initial")


def action(server, request):
    encoded = json.dumps(json.dumps(request, separators=(",", ":"), allow_nan=False))
    return server.read("(function() local ok,result=pcall(science_action,helpers.json_to_table(" + encoded +
                       ")); return {ok=ok,result=ok and result or nil,error=not ok and tostring(result) or nil} end)()")


def finalize(server, run, elapsed, error=None):
    trace_hash = hashlib.sha256((run / "actions.jsonl").read_bytes()).hexdigest()
    server.command("game.tick_paused=true; script.on_event(defines.events.on_tick,nil); "
                   f"storage.science.audit.elapsed_seconds={elapsed}; "
                   f"storage.science.audit.trace_sha256={json.dumps(trace_hash)}")
    record = server.read("storage.science")
    record["final"] = server.read("science_snapshot()")
    if error:
        record["host_error"] = error
    (run / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--port", type=int, default=18880)
    p.add_argument("--rcon-port", type=int, default=27880)
    p.add_argument("--game-port", type=int, default=34880)
    p.add_argument("--factorio", default=FACTORIO)
    args = p.parse_args()
    if Path(args.run).name != args.run or args.run in (".", ".."):
        p.error("run must be a new plain folder name")
    run = ROOT / "runs" / args.run
    run.mkdir(parents=True, exist_ok=False)
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    started = time.monotonic()
    with Server(run / "game", rcon_port=args.rcon_port, game_port=args.game_port,
                factorio=args.factorio) as server:
        initial = setup(server, args.seed)
        error = None
        with (run / "actions.jsonl").open("w", buffering=1) as trace:
            def execute(req):
                if time.monotonic() - started >= RULES["seconds"]:
                    raise TimeoutError("Trial deadline reached")
                before = time.monotonic() - started
                try:
                    response = action(server, req)
                except (TypeError, ValueError):
                    response = action(server, {"action": "invalid_request"})
                trace.write(json.dumps({"request": req, "elapsed_seconds": before, "response": response}) + "\n")
                return response

            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *_):
                    pass

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
                                for item in batch:
                                    results.append(execute(item))
                                    if not results[-1]["ok"]:
                                        break
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
                    except (BrokenPipeError, ConnectionResetError):
                        pass

            try:
                with HTTPServer(("127.0.0.1", args.port), Handler) as http:
                    http.timeout = .1
                    print(json.dumps({"ready": True, "endpoint": f"http://127.0.0.1:{args.port}/action",
                                      "run": str(run), "contract": CONTRACT, "initial": initial}), flush=True)
                    while not stopping and time.monotonic() - started < RULES["seconds"]:
                        http.handle_request()
                        if server.read("storage.science.measurement and storage.science.measurement.done or false"):
                            break
            except Exception as exc:
                error = str(exc)
                raise
            finally:
                finalize(server, run, time.monotonic() - started, error)
    # Factorio's clean shutdown saves the paused world. Check the process result.
    if server.process.returncode != 0:
        raise RuntimeError("Final save was not confirmed by a clean Factorio exit")
    print(json.dumps({"saved": str(run / "game/world.zip"), "verify":
                      f".venv/bin/python scripts/science_verify.py {run}"}), flush=True)


if __name__ == "__main__":
    main()
