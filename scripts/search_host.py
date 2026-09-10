"""Supplied-kit search host. Not approved for scoring until live checks pass."""
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
import socketserver
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = Path(__file__).resolve().parents[1]
from automatic_evaluator import KIT as START_INVENTORY, SNAPSHOT, SNAPSHOT_FUNCTION, measure
from search_startup import StartupGate, write_status


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
    p.add_argument("--seed", type=int, default=61001)
    p.add_argument("--job-deadline", type=float, required=True)
    p.add_argument("--map-x", type=int, default=16)
    p.add_argument("--map-y", type=int, default=0)
    p.add_argument("--recording-mode", choices=["native","none"], default="native")
    p.add_argument("--validation-fault", choices=["none","two_windows","stored_only"],default="none")
    p.add_argument("--seconds", type=int, default=300)
    p.add_argument("--actions", type=int, default=200)
    p.add_argument("--port", type=int, default=18765)
    p.add_argument("--rcon-port", type=int, default=27117)
    p.add_argument("--game-port", type=int, default=34217)
    p.add_argument("--speed", type=float, default=20)
    p.add_argument("--transport", choices=["http", "unix"], default="http")
    p.add_argument("--socket-path")
    p.add_argument("--factorio", default="/Applications/factorio.app/Contents/MacOS/factorio")
    args = p.parse_args()
    if Path(args.run).name != args.run or args.run in (".", ".."):
        p.error("run must be a new plain folder name")
    if not math.isfinite(args.speed) or not 0 < args.speed <= 20:
        p.error("speed must be in (0,20]")
    if args.seconds <= 0 or args.actions <= 0:
        p.error("time and action limits must be positive")
    if args.transport == "unix" and not args.socket_path:
        p.error("unix transport requires --socket-path")
    host_started = time.monotonic()
    host_wall_started = time.time()
    absolute_deadline = min(args.job_deadline-30, host_wall_started+300)
    if absolute_deadline <= time.time(): p.error("job deadline reached")
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
        "auto_pause": False, "autosave_interval": 0, "max_players": 2})
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
        "--bind", f"127.0.0.1:{args.game_port}", "--rcon-bind", f"127.0.0.1:{args.rcon_port}",
        "--rcon-password", password, "--server-settings", str(game / "server.json")],
        stdout=log, stderr=log)
    instance = None
    recorder = None
    host_ready = False
    startup_gate = StartupGate(ROOT / "runs/graphics-startup.lock")
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
                client = RCONClient("127.0.0.1", args.rcon_port, password, timeout=10)
                client.send_command("/sc rcon.print(game.tick)")
                client.close()
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("RCON startup timed out")
        if args.recording_mode == "native":
            from search_recording import Recorder
            recorder = Recorder(run_dir=run, factorio=args.factorio, game_port=args.game_port,
                                rcon_port=args.rcon_port, rcon_password=password,
                                deadline_epoch=absolute_deadline+30)
            write_status(run / "startup.json", stage="waiting_for_startup_slot", started_at=host_wall_started)
            startup_gate.acquire(absolute_deadline-40, cancelled=stop.is_set)
            write_status(run / "startup.json", stage="starting_client", started_at=host_wall_started)
            recorder.start_peer()
        else:
            write_status(run / "recording-mode.json", mode="none", reason="headless optimization",
                         video_required=False, graphical_client_started=False)
        write_status(run / "startup.json", stage="initializing_game", started_at=host_wall_started)
        import fle.env.instance as fle_instance
        from fle.env import Position, Direction
        from fle.env.game_types import Prototype, Resource
        fle_instance.RCON_PASSWORD = password

        class NativeInstance(fle_instance.FactorioInstance):
            def _generate_chunks(self, center_x=0, center_y=0, chunk_radius=4):
                # The declared benchmark terrain lies inside these chunks.
                return super()._generate_chunks(center_x=center_x,center_y=center_y,chunk_radius=min(chunk_radius,4))

            @staticmethod
            def connect_to_server(address, tcp_port):
                return RCONClient(address, tcp_port, password, timeout=10), address

            def initialise(self, *a, **kw):
                # Preserve generated ore amounts across FLE's setup reset.
                self._generate_chunks(center_x=0, center_y=0, chunk_radius=25)
                self.rcon_client.send_command('/sc storage.test_ores={}; for _,e in pairs(game.surfaces[1].find_entities_filtered{type="resource"}) do table.insert(storage.test_ores,{e=e,amount=e.amount}) end')
                super().initialise(*a, **kw)
                self.rcon_client.send_command('/sc for _,v in pairs(storage.test_ores) do if v.e.valid then v.e.amount=v.amount end end; storage.test_ores=nil; game.forces.player.reset(); for _,t in pairs(game.forces.player.technologies) do t.researched=false end; game.surfaces[1].always_day=false')

        instance = NativeInstance(address="127.0.0.1", tcp_port=args.rcon_port, fast=True,
            inventory=START_INVENTORY, all_technologies_researched=False,
            clear_entities=False, peaceful=False, reset_speed=args.speed, reset_paused=False)
        ns = instance.namespace
        # Declared operator terrain: clear 129x129 grass area and add an iron patch.
        setup = f"local s=storage.agent_characters[1].surface; for _,e in pairs(s.find_entities_filtered{{area={{{{-64,-64}},{{64,64}}}}}}) do if e.type~='character' then e.destroy() end end; local ts={{}}; for x=-64,64 do for y=-64,64 do table.insert(ts,{{name='grass-1',position={{x,y}}}}) end end; s.set_tiles(ts); for x={args.map_x}-4,{args.map_x}+4 do for y={args.map_y}-4,{args.map_y}+4 do s.create_entity{{name='iron-ore',position={{x,y}},amount=1000}} end end; game.speed=20; game.tick_paused=false;"
        instance.rcon_client.send_command('/sc '+setup)
        instance.rcon_client.send_command('/sc '+SNAPSHOT_FUNCTION)
        handed_off = False
        illegal = False
        def snapshot():
            return json.loads(instance.rcon_client.send_command("/sc " + SNAPSHOT))
        if recorder:
            write_status(run / "startup.json", stage="capturing_initial_frame", started_at=host_wall_started)
            recorder.start()
        initial = snapshot()
        assert not initial["research"] and initial["enemies"] == 0
        assert not initial["furnaces"] and initial["iron_plates_produced"] == 0
        (run / "initial.json").write_text(json.dumps(initial, indent=2))
        metadata = {"seed": args.seed, "inventory": START_INVENTORY, "seconds_limit": args.seconds,
            "action_limit": args.actions, "fast": True, "speed": args.speed, "thinking_paused": False,
            "transport": args.transport, "rcon_port": args.rcon_port, "game_port": args.game_port,
            "startup_seconds": time.monotonic()-host_started,
            "recording_mode":args.recording_mode,
            "client_startup_limit_seconds":120 if recorder else None, "serialized_graphics_startup":bool(recorder),
            "billing": "Paid OpenAI API authorized for one-hour job", "api_spending_cap_usd": None,
            "job_deadline_epoch": args.job_deadline, "validation_fault":args.validation_fault, "map_patch": {"x":args.map_x,"y":args.map_y,"size":9,"amount_per_tile":1000},
            "terrain": "Operator cleared area -64..64, grass-1; 9x9 iron patch; natural terrain outside",
            "fle_commit": subprocess.check_output(["git", "-C", str(ROOT / "local/deps/fle"), "rev-parse", "HEAD"], text=True).strip(),
            "factorio_version": subprocess.check_output([args.factorio,"--version"],text=True).splitlines()[0],
            "host_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "started_at": time.time(), "mode": "integration; not a scored rocket trial"}
        (run / "settings.json").write_text(json.dumps(metadata, indent=2))
        deadline = time.monotonic() + max(0, absolute_deadline-time.time())
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
            nonlocal count, handed_off, illegal
            if not isinstance(req, dict):
                raise ValueError("request must be an object")
            op = req.get("action")
            allowed = {"observe", "nearest", "move", "place", "insert", "entities", "pickup", "rotate", "finish"}
            count += 1
            if handed_off:
                illegal = True
                raise ValueError("playing access revoked")
            if op not in allowed:
                illegal = True
                raise ValueError("action is not allowed")
            if time.monotonic() >= deadline or stop.is_set():
                raise ValueError("test time limit reached")
            if count > args.actions:
                raise ValueError("action limit reached")
            if op == "finish":
                handed_off = True
                if args.validation_fault != 'none':
                    from search_validation_faults import install_fault
                    install_fault(instance.rcon_client,args.validation_fault)
                measurements = measure(instance.rcon_client, absolute_deadline)
                (run / "measurement.json").write_text(json.dumps(measurements,indent=2))
                stop.set()
                return {"handoff":True,"measurement_complete":True}
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
            if op == "place":
                if req['item'] not in START_INVENTORY or req['item']=='coal': raise ValueError('not kit equipment')
                return ns.place_entity(prototype(req["item"]), direction=Direction[req.get("direction","UP")],position=position(req["position"]), exact=req.get("exact", True))
            if op == "insert":
                if req['item'] != 'coal':
                    illegal = True
                    raise ValueError('only coal into fuel inventories is allowed')
                t=req['target']; pos=position(t['position']); name=t['name']
                if name not in ('stone-furnace','burner-inserter','burner-mining-drill'): raise ValueError('target has no allowed fuel inventory')
                code = f"local c=storage.agent_characters[1]; local e=c.surface.find_entity({json.dumps(name)},{{x={pos.x},y={pos.y}}}); assert(e and e.force==c.force,'missing target'); assert(math.abs(c.position.x-e.position.x)<=10 and math.abs(c.position.y-e.position.y)<=10,'out of reach'); local inv=e.get_fuel_inventory(); assert(inv,'no fuel inventory'); local n=math.min({quantity},c.get_item_count('coal')); local k=inv.insert{{name='coal',count=n}}; c.remove_item{{name='coal',count=k}}; rcon.print(k)"
                return {'inserted':int(instance.rcon_client.send_command('/sc '+code))}
            if op == "pickup":
                t=req['target']; pos=position(t['position']); name=t['name']
                if name not in START_INVENTORY or name=='coal': raise ValueError('not equipment')
                code=f"local c=storage.agent_characters[1]; local e=c.surface.find_entity({json.dumps(name)},{{x={pos.x},y={pos.y}}}); assert(e and e.force==c.force,'missing target'); assert(math.abs(c.position.x-e.position.x)<=10 and math.abs(c.position.y-e.position.y)<=10,'out of reach'); rcon.print(c.mine_entity(e))"
                return {'picked_up':instance.rcon_client.send_command('/sc '+code).strip()=='true'}
            if op == "rotate": return ns.rotate_entity(target(req["target"]), Direction[req["direction"]])
            if op == "entities": return snapshot()["entities"]
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

        def execute_request(req):
            start = time.time()
            monotonic_start = time.monotonic()
            try:
                signal.setitimer(signal.ITIMER_REAL, min(90, max(0.01, deadline-time.monotonic())))
                result = serial(dispatch(req))
                action_end = time.monotonic()
                state = snapshot()
                response = {"ok": True, "result": result, "state": state}
            except Exception as error:
                action_end = time.monotonic()
                response = {"ok": False, "error": str(error)}
                # An error is not proof that the action had no effect.
                try:
                    response["state"] = snapshot()
                except Exception:
                    response["state"] = None
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
            end = time.monotonic()
            actions.write(json.dumps({"request":req,"started_at":start,"ended_at":time.time(),
                "monotonic_started":monotonic_start,"duration_seconds":end-monotonic_start,
                "action_seconds":action_end-monotonic_start,"post_observation_seconds":end-action_end,
                "response":response})+"\n")
            return response

        def execute_payload(req):
            if isinstance(req, dict) and set(req) == {"batch"}:
                batch = req["batch"]
                if not isinstance(batch,list) or not 1 <= len(batch) <= 50:
                    return {"ok":False,"error":"batch requires 1 to 50 actions"}
                if any(not isinstance(a,dict) or "action" not in a or "batch" in a for a in batch):
                    return {"ok":False,"error":"batch entries must be action objects"}
                results=[]
                for a in batch:
                    result=execute_request(a)
                    results.append(result)
                    if not result["ok"]: break
                return {"ok":all(r["ok"] for r in results),"results":results,
                        "executed":len(results),"requested":len(batch)}
            return execute_request(req)

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_): pass
            def setup(self):
                super().setup()
                self.connection.settimeout(5)
            def do_POST(self):
                if self.path != "/action":
                    self.send_error(404); return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 65536: raise ValueError("invalid request length")
                    req = json.loads(self.rfile.read(length))
                    response = execute_payload(req)
                except Exception as error:
                    response = {"ok": False, "error": str(error)}
                payload = json.dumps(response).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        class UnixHandler(socketserver.StreamRequestHandler):
            def handle(self):
                self.connection.settimeout(5)
                try:
                    line=self.rfile.readline(65538)
                    if not line.endswith(b"\n") or len(line)>65537:
                        raise ValueError("send one JSON line of at most 65536 bytes")
                    response=execute_payload(json.loads(line))
                except Exception as error:
                    response={"ok":False,"error":str(error)}
                self.wfile.write(json.dumps(response).encode()+b"\n")

        if args.transport == "unix":
            http = socketserver.UnixStreamServer(args.socket_path, UnixHandler)
            os.chmod(args.socket_path, 0o600)
            endpoint = "unix:"+args.socket_path
        else:
            http = HTTPServer(("127.0.0.1", args.port), Handler)
            endpoint = f"http://127.0.0.1:{args.port}/action"
        http.timeout = 1
        host_ready = True
        write_status(run / "startup.json", stage="ready", started_at=host_wall_started)
        startup_gate.close()
        print(json.dumps({"ready": True,"endpoint":endpoint,"run":str(run),"initial":initial}), flush=True)
        while not stop.is_set() and time.monotonic() < deadline:
            if recorder and recorder.error:
                raise RuntimeError("Game recording failed: " + recorder.error)
            http.handle_request()
        http.server_close()
        if args.transport == "unix":
            Path(args.socket_path).unlink(missing_ok=True)
        actions.close()
        (run / "action-summary.json").write_text(json.dumps({"count":count,"legal":not illegal,"handed_off":handed_off,"within_deadline":time.time()<=absolute_deadline},indent=2))
    except BaseException as error:
        write_status(run / "failure.json", phase="gameplay" if host_ready else "startup",
                     code=getattr(error,"code","host_failure"), error=str(error))
        raise
    finally:
        # Retain the gate through cleanup if startup failed, so the next loader
        # cannot overlap with a peer that is still shutting down.
        if instance and server.poll() is None:
            try:
                instance.rcon_client.send_command("/sc game.tick_paused=true")
                final = json.loads(instance.rcon_client.send_command("/sc " + SNAPSHOT))
                (run / "final.json").write_text(json.dumps(final, indent=2))
                if recorder and recorder.records:
                    recorder.capture("final")
                prepare_final_save(instance)
            except Exception as error:
                (run / "shutdown-error.txt").write_text(str(error))
        if recorder:
            try: recorder.close()
            except Exception as error: (run / 'recording-error.txt').write_text(str(error))
        server.terminate()
        try: server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            server.kill(); server.wait()
        log.close()
        startup_gate.close()
        if server.returncode == 0 and (run / "final.json").exists() and not (run / "shutdown-error.txt").exists():
            shutil.copyfile(game / "working.zip", game / "final.zip")
        (run / "host-timing.json").write_text(json.dumps({"total_seconds":time.monotonic()-host_started,
            "finished_at":time.time(),"server_exit_code":server.returncode},indent=2))


if __name__ == "__main__":
    main()
