"""Local integration test host. Game administration never enters the action API."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = Path(__file__).resolve().parents[1]
START_INVENTORY = {"iron-plate": 8, "wood": 1, "stone-furnace": 1,
                   "burner-mining-drill": 1, "pistol": 1, "firearm-magazine": 10}
SNAPSHOT = '''local c=storage.agent_characters[1]; local s=c.surface
local function inv(i) return i and i.get_contents() or {} end
local furnaces={}; for _,e in pairs(s.find_entities_filtered{type="furnace",force=c.force}) do
 table.insert(furnaces,{name=e.name,position=e.position,products_finished=e.products_finished,
 input=inv(e.get_inventory(defines.inventory.furnace_source)),
 output=inv(e.get_inventory(defines.inventory.furnace_result)),
 fuel=inv(e.get_fuel_inventory())}) end
local research={}; for n,t in pairs(c.force.technologies) do if t.researched then table.insert(research,n) end end
local stats=c.force.get_item_production_statistics(s)
rcon.print(helpers.table_to_json({tick=game.tick,speed=game.speed,paused=game.tick_paused,
 position=c.position,inventory=inv(c.get_main_inventory()),furnaces=furnaces,research=research,
 iron_plates_produced=stats.get_input_count("iron-plate"),
 enemies=#s.find_entities_filtered{force="enemy"},always_day=s.always_day}))'''


def prepare_final_save(instance):
    """Prepare for Factorio's shutdown save. Do not resume FLE from this copy."""
    response = instance.rcon_client.send_command('''/sc game.tick_paused=true; test_removed={}; local seen={};
local function strip(t) if seen[t] then return end; seen[t]=true;
 for k,v in pairs(t) do if type(v)=="function" then table.insert(test_removed,{t=t,k=k,v=v}); t[k]=nil
 elseif type(v)=="table" and not v.__self then strip(v) end end end; strip(storage);
script.on_event(defines.events.on_tick,nil); script.on_nth_tick(nil); test_removed=nil; rcon.print("ready")''')
    if response.strip() != "ready":
        raise RuntimeError("checkpoint preparation failed: " + response)


def serial(value):
    if hasattr(value, "model_dump"):
        return serial(value.model_dump(mode="python", exclude={"game"}))
    if isinstance(value, list):
        return [serial(v) for v in value]
    if isinstance(value, dict):
        return {str(k): serial(v) for k, v in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True)
    p.add_argument("--seed", type=int, default=44340)
    p.add_argument("--seconds", type=int, default=1200)
    p.add_argument("--actions", type=int, default=200)
    p.add_argument("--port", type=int, default=18765)
    p.add_argument("--factorio", default="/Applications/factorio.app/Contents/MacOS/factorio")
    args = p.parse_args()
    run = ROOT / "runs" / args.run
    run.mkdir(parents=True, exist_ok=False)
    game = run / "game"
    game.mkdir()
    mods = game / "mods"
    mods.mkdir()
    (mods / "mod-list.json").write_text(json.dumps({"mods": [
        {"name": n, "enabled": n == "base"} for n in
        ["base", "quality", "elevated-rails", "space-age"]]}))
    config = game / "config.ini"
    data = Path(args.factorio).resolve().parents[1] / "data"
    config.write_text(f"[path]\nread-data={data}\nwrite-data={game}\n")
    (game / "map-gen.json").write_text(json.dumps({"seed": args.seed, "peaceful_mode": True,
        "autoplace_controls": {"enemy-base": {"frequency": 0, "size": 0, "richness": 0}}}))
    settings = json.loads((data / "server-settings.example.json").read_text())
    settings.update({"name": "Method control test",
        "visibility": {"public": False, "lan": False}, "require_user_verification": False,
        "auto_pause": False, "autosave_interval": 0, "max_players": 1})
    (game / "server.json").write_text(json.dumps(settings))
    base = [args.factorio, "--config", str(config), "--mod-directory", str(mods)]
    with (run / "create.log").open("w") as log:
        subprocess.run(base + ["--create", str(game / "fresh.zip"), "--map-gen-settings",
                       str(game / "map-gen.json")], stdout=log, stderr=log, check=True, timeout=60)
    # Generated per run; held by this host only. Raw game logs remain private.
    password = secrets.token_urlsafe(32)
    log = (run / "server.log").open("w")
    os.chmod(run / "server.log", 0o600)
    shutil.copyfile(game / "fresh.zip", game / "working.zip")
    server = subprocess.Popen(base + ["--start-server", str(game / "working.zip"),
        "--bind", "127.0.0.1:34217", "--rcon-bind", "127.0.0.1:27117",
        "--rcon-password", password, "--server-settings", str(game / "server.json")],
        stdout=log, stderr=log)
    instance = None
    stop = threading.Event()
    def request_stop(*_):
        stop.set()
    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    try:
        from factorio_rcon import RCONClient
        for _ in range(60):
            if server.poll() is not None:
                raise RuntimeError("Native server stopped; see private server.log")
            try:
                client = RCONClient("127.0.0.1", 27117, password, timeout=10)
                client.send_command("/sc rcon.print(game.tick)")
                client.close()
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("RCON startup timed out")
        import fle.env.instance as fle_instance
        from fle.env import Position, Direction
        from fle.env.game_types import Prototype, Resource
        fle_instance.RCON_PASSWORD = password

        class NativeInstance(fle_instance.FactorioInstance):
            @staticmethod
            def connect_to_server(address, tcp_port):
                return RCONClient(address, tcp_port, password, timeout=10), address

            def initialise(self, *a, **kw):
                # Preserve generated ore amounts across FLE's setup reset.
                self._generate_chunks(center_x=0, center_y=0, chunk_radius=25)
                self.rcon_client.send_command('/sc storage.test_ores={}; for _,e in pairs(game.surfaces[1].find_entities_filtered{type="resource"}) do table.insert(storage.test_ores,{e=e,amount=e.amount}) end')
                super().initialise(*a, **kw)
                self.rcon_client.send_command('/sc for _,v in pairs(storage.test_ores) do if v.e.valid then v.e.amount=v.amount end end; storage.test_ores=nil; game.forces.player.reset(); for _,t in pairs(game.forces.player.technologies) do t.researched=false end; game.surfaces[1].always_day=false')

        instance = NativeInstance(address="127.0.0.1", tcp_port=27117, fast=True,
            inventory=START_INVENTORY, all_technologies_researched=False,
            clear_entities=False, peaceful=False, reset_speed=1, reset_paused=False)
        ns = instance.namespace
        def snapshot():
            return json.loads(instance.rcon_client.send_command("/sc " + SNAPSHOT))
        initial = snapshot()
        assert not initial["research"] and initial["enemies"] == 0
        assert not initial["furnaces"] and initial["iron_plates_produced"] == 0
        (run / "initial.json").write_text(json.dumps(initial, indent=2))
        metadata = {"seed": args.seed, "inventory": START_INVENTORY, "seconds_limit": args.seconds,
            "action_limit": args.actions, "fast": True, "speed": 1, "thinking_paused": False,
            "billing": "Codex ChatGPT subscription; no separate API calls", "api_spending_cap_usd": 0,
            "fle_commit": subprocess.check_output(["git", "-C", str(ROOT / "local/deps/fle"), "rev-parse", "HEAD"], text=True).strip(),
            "factorio_version": subprocess.check_output([args.factorio,"--version"],text=True).splitlines()[0],
            "host_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "started_at": time.time(), "mode": "integration; not a scored rocket trial"}
        (run / "settings.json").write_text(json.dumps(metadata, indent=2))
        deadline = time.monotonic() + args.seconds
        count = 0
        actions = (run / "actions.jsonl").open("a", buffering=1)

        def position(v):
            if not isinstance(v, dict) or set(v) != {"x", "y"}:
                raise ValueError("position requires x and y")
            if any(type(v[k]) not in (float, int) or not math.isfinite(v[k]) or abs(v[k]) > 1000 for k in v):
                raise ValueError("position outside test limits")
            return Position(**v)

        def prototype(name):
            for item in Prototype:
                if item.value[0] == name:
                    return item
            raise ValueError("unknown prototype")

        def target(v):
            return ns.get_entity(prototype(v["name"]), position(v["position"]))

        def dispatch(req):
            nonlocal count
            if not isinstance(req, dict):
                raise ValueError("request must be an object")
            op = req.get("action")
            allowed = {"observe", "nearest", "move", "harvest", "craft", "place", "insert", "extract", "entities", "wait", "pickup", "rotate"}
            if op not in allowed:
                raise ValueError("action is not allowed")
            if time.monotonic() >= deadline or stop.is_set():
                raise ValueError("test time limit reached")
            if count >= args.actions:
                raise ValueError("action limit reached")
            count += 1
            quantity = req.get("quantity", 1)
            if type(quantity) is not int or not 1 <= quantity <= 100:
                raise ValueError("quantity must be an integer from 1 to 100")
            if op == "observe": return snapshot()
            if op == "nearest":
                resources = {"iron-ore": Resource.IronOre, "coal": Resource.Coal,
                             "stone": Resource.Stone, "wood": Resource.Wood, "copper-ore": Resource.CopperOre}
                return ns.nearest(resources[req["resource"]])
            if op == "move": return ns.move_to(position(req["position"]))
            if op == "harvest": return ns.harvest_resource(position(req["position"]), quantity=quantity)
            if op == "craft": return ns.craft_item(prototype(req["item"]), quantity)
            if op == "place": return ns.place_entity(prototype(req["item"]), position=position(req["position"]), exact=req.get("exact", True))
            if op == "insert": return ns.insert_item(prototype(req["item"]), target(req["target"]), quantity=quantity)
            if op == "extract": return ns.extract_item(prototype(req["item"]), target(req["target"]), quantity=quantity)
            if op == "pickup": return ns.pickup_entity(target(req["target"]))
            if op == "rotate": return ns.rotate_entity(target(req["target"]), Direction[req["direction"]])
            if op == "entities": return ns.get_entities(radius=100)
            if op == "wait":
                seconds = req.get("seconds", 1)
                if type(seconds) not in (float, int) or not math.isfinite(seconds) or not 0 < seconds <= 30:
                    raise ValueError("wait seconds must be in (0,30]")
                time.sleep(min(seconds, max(0, deadline-time.monotonic())))
                return snapshot()

        def timed_out(*_):
            stop.set()
            raise TimeoutError("action time limit reached; inspect state before recovery")
        signal.signal(signal.SIGALRM, timed_out)

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_): pass
            def do_POST(self):
                if self.path != "/action":
                    self.send_error(404); return
                start = time.time()
                req = None
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 4096: raise ValueError("invalid request length")
                    req = json.loads(self.rfile.read(length))
                    signal.setitimer(signal.ITIMER_REAL, min(90, max(0.01, deadline-time.monotonic())))
                    result = serial(dispatch(req))
                    response = {"ok": True, "result": result, "state": snapshot()}
                except Exception as error:
                    response = {"ok": False, "error": str(error)}
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                actions.write(json.dumps({"request": req,"started_at": start,"ended_at":time.time(),"response":response})+"\n")
                payload = json.dumps(response).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        http = HTTPServer(("127.0.0.1", args.port), Handler)
        http.timeout = 1
        print(json.dumps({"ready": True,"endpoint":f"http://127.0.0.1:{args.port}/action","run":str(run),"initial":initial}), flush=True)
        while not stop.is_set() and time.monotonic() < deadline:
            http.handle_request()
        http.server_close()
        actions.close()
    finally:
        if instance and server.poll() is None:
            try:
                final = json.loads(instance.rcon_client.send_command("/sc " + SNAPSHOT))
                (run / "final.json").write_text(json.dumps(final, indent=2))
                prepare_final_save(instance)
            except Exception as error:
                (run / "shutdown-error.txt").write_text(str(error))
        server.terminate()
        try: server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            server.kill(); server.wait()
        log.close()
        if server.returncode == 0 and (run / "final.json").exists() and not (run / "shutdown-error.txt").exists():
            shutil.copyfile(game / "working.zip", game / "final.zip")


if __name__ == "__main__":
    main()
