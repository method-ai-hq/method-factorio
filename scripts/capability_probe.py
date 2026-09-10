"""Fixed advanced FLE fixture probes; no model and no fresh-world win claims.

Fixture administration and independent reads stay in this test process. This
script is not a playing tool. Raw logs and saves remain in ignored runs/.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import time

from control_test import prepare_final_save, serial

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    {"id": "recipe_power", "fixture": "solar-powered assembler 2, 20 iron plates in character", "action": "set iron-gear-wheel recipe and insert 20 iron plates", "pass": "at least 1 gear produced, at least 2 plates consumed, positive machine energy", "timeout_seconds": 15},
    {"id": "locked_recipe", "fixture": "assembler 2; processing-unit recipe locked", "action": "set processing-unit recipe", "pass": "locked recipe rejected and not selected", "timeout_seconds": 10},
    {"id": "research", "fixture": "solar-powered lab; steam-power and automation-science-pack researched; automation unresearched; 10 red science in character", "action": "select automation and insert 10 science", "pass": "automation completes with 10 science consumed", "timeout_seconds": 30},
    {"id": "research_prerequisite", "fixture": "no researched technology", "action": "select automation-3", "pass": "request rejected; no research or completion granted", "timeout_seconds": 10},
    {"id": "oil", "fixture": "solar-powered refinery; oil-processing researched; input fluid 100 crude oil supplied by operator after recipe selection", "action": "select basic-oil-processing", "pass": "consume 100 crude oil and produce at least 45 petroleum gas", "timeout_seconds": 15},
    {"id": "rocket", "fixture": "solar-powered silo; rocket-silo researched; 1000 processing units, 1000 low-density structures, 1000 rocket fuel in character; one satellite supplied by operator if payload needed", "action": "insert normal rocket ingredients, wait for ready state, call FLE launch_rocket at exact silo position", "pass": "trusted on_rocket_launched event count increases by one", "timeout_seconds": 90},
    {"id": "rocket_bad_target", "fixture": "same prepared rocket fixture at origin; no silo at position (0,1000)", "action": "call FLE launch_rocket at (0,1000)", "pass": "request rejected and trusted launch event count stays zero", "timeout_seconds": 90},
    {"id": "continuous_iron", "fixture": "operator-built burner drill, 5 belts, burner inserter and stone furnace on supplied ore; each burner receives 50 coal; empty ore and plate buffers", "action": "run 600 warmup ticks then three 1200-tick windows without item transfer", "pass": "furnace output increases by at least one plate in each window; no operator transfers during windows", "timeout_seconds": 30},
]

SNAPSHOT = '''local c=storage.agent_characters[1];local f=c.force;local s=c.surface
local function inv(v) return v and v.get_contents() or {} end
local es={};for key,e in pairs(storage.cap_entities or {}) do if e.valid then
local v={name=e.name,position=e.position,energy=e.energy,status=e.status}
if e.type=="inserter" or e.type=="mining-drill" then v.drop_position=e.drop_position end
if e.type=="inserter" then v.pickup_position=e.pickup_position;v.held_stack=e.held_stack.valid_for_read and {name=e.held_stack.name,count=e.held_stack.count} or {} end
if e.type=="assembling-machine" or e.type=="rocket-silo" then local r=e.get_recipe();v.recipe=r and r.name;v.products=e.products_finished;v.input=inv(e.get_inventory(defines.inventory.assembling_machine_input));v.output=inv(e.get_inventory(defines.inventory.assembling_machine_output)) end
if e.type=="lab" then v.input=inv(e.get_inventory(defines.inventory.lab_input)) end
if e.type=="furnace" then v.products=e.products_finished;v.input=inv(e.get_inventory(defines.inventory.furnace_source));v.output=inv(e.get_inventory(defines.inventory.furnace_result)) end
if e.type=="rocket-silo" then v.parts=e.rocket_parts;v.silo_status=e.rocket_silo_status;v.ready=e.rocket_silo_status==defines.rocket_silo_status.rocket_ready end
v.fluids=e.get_fluid_contents();es[key]=v end end
local tech={};for _,n in ipairs({"automation","automation-3","processing-unit","oil-processing","rocket-silo"}) do tech[n]=f.technologies[n] and f.technologies[n].researched end
rcon.print(helpers.table_to_json({tick=game.tick,speed=game.speed,paused=game.tick_paused,entities=es,inventory=inv(c.get_main_inventory()),research=f.current_research and f.current_research.name,progress=f.research_progress,technologies=tech,processing_unit_enabled=f.recipes["processing-unit"].enabled,launch_events=storage.cap_launch_events or 0,iron_gear_production=f.get_item_production_statistics(s).get_input_count("iron-gear-wheel")}))'''


def count(contents, name):
    if not contents:
        return 0
    return sum(x["count"] for x in contents if x["name"] == name)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True)
    p.add_argument("--rcon-port", type=int, default=27205)
    p.add_argument("--game-port", type=int, default=34305)
    p.add_argument("--speed", type=float, default=20)
    p.add_argument("--cases", nargs="+", choices=[c["id"] for c in CASES])
    args = p.parse_args()
    selected_cases = [c for c in CASES if args.cases is None or c["id"] in args.cases]
    started = time.monotonic()
    run = ROOT / "runs" / args.run
    run.mkdir(parents=True, exist_ok=False)
    os.chmod(run, 0o700)
    manifest = {"cases": selected_cases, "speed": args.speed, "seed": 44340,
                "mode": "fixed scripted fixtures; operator supplies prerequisites; not fresh-world wins",
                "model_calls": 0, "api_cost_usd": 0,
                "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    frozen = json.dumps(manifest, sort_keys=True, indent=2)
    (run / "fixture-manifest.json").write_text(frozen)
    (run / "probe-source.py").write_bytes(Path(__file__).read_bytes())
    (run / "fixture-manifest.sha256").write_text(hashlib.sha256(frozen.encode()).hexdigest())
    toolroot = ROOT / "local/deps/fle/fle/env/tools/agent"
    (run / "interface-audit.json").write_text(json.dumps({
        "fle_commit": subprocess.check_output(["git", "-C", str(ROOT / "local/deps/fle"), "rev-parse", "HEAD"], text=True).strip(),
        "agent_tools": sorted(x.name for x in toolroot.iterdir() if x.is_dir()),
        "dedicated_train_schedule_tool": False, "dedicated_circuit_condition_tool": False,
        "dedicated_combat_weapon_tool": False,
        "note": "Tool presence alone is not a pass. Current HTTP controls omit recipe, research and launch actions."
    }, indent=2))
    game = run / "game"
    mods = game / "mods"
    mods.mkdir(parents=True)
    (mods / "mod-list.json").write_text(json.dumps({"mods": [{"name": n, "enabled": n == "base"} for n in ["base", "quality", "elevated-rails", "space-age"]]}))
    binary = Path("/Applications/factorio.app/Contents/MacOS/factorio")
    data = binary.parents[1] / "data"
    config = game / "config.ini"
    config.write_text(f"[path]\nread-data={data}\nwrite-data={game}\n")
    (game / "map-gen.json").write_text(json.dumps({"seed": 44340, "peaceful_mode": True, "autoplace_controls": {"enemy-base": {"frequency": 0, "size": 0, "richness": 0}}}))
    settings = json.loads((data / "server-settings.example.json").read_text())
    settings.update({"name": "Advanced fixture probe", "visibility": {"public": False, "lan": False}, "require_user_verification": False, "auto_pause": False, "autosave_interval": 0, "max_players": 1})
    (game / "server.json").write_text(json.dumps(settings))
    base = [str(binary), "--config", str(config), "--mod-directory", str(mods)]
    with (run / "create.log").open("w") as log:
        subprocess.run(base + ["--create", str(game / "working.zip"), "--map-gen-settings", str(game / "map-gen.json")], stdout=log, stderr=log, check=True, timeout=60)
    password = secrets.token_urlsafe(32)
    log = (run / "server.log").open("w")
    os.chmod(run / "server.log", 0o600)
    server = subprocess.Popen(base + ["--start-server", str(game / "working.zip"), "--bind", f"127.0.0.1:{args.game_port}", "--rcon-bind", f"127.0.0.1:{args.rcon_port}", "--rcon-password", password, "--server-settings", str(game / "server.json")], stdout=log, stderr=log)
    instance = None
    results = []
    try:
        from factorio_rcon import RCONClient
        for _ in range(100):
            if server.poll() is not None:
                raise RuntimeError("server stopped; inspect private log")
            try:
                client = RCONClient("127.0.0.1", args.rcon_port, password, timeout=10)
                client.send_command("/sc rcon.print(game.tick)")
                client.close()
                break
            except Exception:
                time.sleep(.2)
        else:
            raise RuntimeError("startup timed out")
        import fle.env.instance as fi
        from fle.env import Position
        from fle.env.game_types import Prototype, RecipeName, Technology
        fi.RCON_PASSWORD = password

        class NativeInstance(fi.FactorioInstance):
            @staticmethod
            def connect_to_server(address, tcp_port):
                return RCONClient(address, tcp_port, password, timeout=10), address

        instance = NativeInstance(address="127.0.0.1", tcp_port=args.rcon_port, fast=True, inventory={}, all_technologies_researched=False, clear_entities=False, peaceful=False, reset_speed=args.speed, reset_paused=False)
        ns = instance.namespace

        def admin(lua):
            response = instance.rcon_client.send_command("/sc " + lua) or ""
            if response.strip() and "error" in response.lower():
                raise RuntimeError(response)
            return response

        def snap():
            return json.loads(admin(SNAPSHOT))

        def fixture(name, techs=(), inventory=None, power=True):
            admin('''game.tick_paused=true;local c=storage.agent_characters[1];local s=c.surface;local f=c.force
for _,e in pairs(s.find_entities_filtered{area={{-80,-90},{80,30}}}) do if e~=c then e.destroy() end end
local tiles={};for x=-80,80 do for y=-90,30 do table.insert(tiles,{name="grass-1",position={x,y}}) end end;s.set_tiles(tiles)
c.teleport({0,8});c.get_main_inventory().clear();f.reset();for _,t in pairs(f.technologies) do t.researched=false end;f.cancel_current_research();s.always_day=true;s.daytime=0
storage.cap_entities={};storage.cap_launch_events=0
script.on_event(defines.events.on_rocket_launched,function(event) storage.cap_launch_events=(storage.cap_launch_events or 0)+1 end)''')
            for tech in techs:
                admin(f'game.forces.player.technologies[{json.dumps(tech)}].researched=true')
            if power:
                admin('''local s=game.surfaces[1];local f=game.forces.player
for x=-30,24,6 do for y=-66,-12,6 do s.create_entity{name="solar-panel",position={x,y},force=f} end end
for x=-27,27,18 do for y=-63,9,18 do s.create_entity{name="substation",position={x,y},force=f} end end''')
            admin(f'storage.cap_entities.machine=game.surfaces[1].create_entity{{name={json.dumps(name)},position={{0,0}},force=game.forces.player}}')
            for item, amount in (inventory or {}).items():
                admin(f'storage.agent_characters[1].insert{{name={json.dumps(item)},count={amount}}}')

        def action(result, name, fn):
            before = time.monotonic()
            try:
                value = fn()
                entry = {"action": name, "ok": True, "result": serial(value)}
            except Exception as exc:
                entry = {"action": name, "ok": False, "error": str(exc)}
            entry["wall_seconds"] = time.monotonic() - before
            entry["state"] = snap()
            result["actions"].append(entry)
            return entry

        def await_state(predicate, timeout):
            until = time.monotonic() + timeout
            while True:
                state = snap()
                if predicate(state) or time.monotonic() >= until:
                    return state
                time.sleep(.2)

        print(json.dumps({"ready": True, "startup_seconds": time.monotonic() - started, "run": str(run)}), flush=True)
        for case in selected_cases:
            r = {"id": case["id"], "criterion": case["pass"], "actions": [], "status": "failed"}
            begin = time.monotonic()
            try:
                cid = case["id"]
                if cid in ("recipe_power", "locked_recipe"):
                    fixture("assembling-machine-2", inventory={"iron-plate": 20})
                    proto = Prototype.AssemblingMachine2
                elif cid == "research":
                    fixture("lab", techs=("steam-power", "automation-science-pack"), inventory={"automation-science-pack": 10})
                    proto = Prototype.Lab
                elif cid == "research_prerequisite":
                    fixture("lab")
                    proto = Prototype.Lab
                elif cid == "oil":
                    fixture("oil-refinery", techs=("oil-processing",))
                    proto = Prototype.OilRefinery
                elif cid in ("rocket", "rocket_bad_target"):
                    fixture("rocket-silo", techs=("rocket-silo",), inventory={"processing-unit": 1000, "low-density-structure": 1000, "rocket-fuel": 1000})
                    proto = Prototype.RocketSilo
                else:
                    fixture("stone-furnace", power=False)
                    admin('''local s=game.surfaces[1];local f=game.forces.player;storage.cap_entities.machine.teleport({0,4})
for x=-1,0 do for y=-5,-4 do s.create_entity{name="iron-ore",position={x,y},amount=1000000} end end
local d=s.create_entity{name="burner-mining-drill",position={0,-4},direction=defines.direction.south,force=f};d.insert{name="coal",count=50};storage.cap_entities.drill=d
local dx=d.drop_position.x;for y=math.floor(d.drop_position.y),1 do s.create_entity{name="transport-belt",position={dx,y},direction=defines.direction.south,force=f} end
local i=s.create_entity{name="burner-inserter",position={dx,2},direction=defines.direction.north,force=f};i.insert{name="coal",count=50};storage.cap_entities.inserter=i
storage.cap_entities.machine.teleport({dx,4})
storage.cap_entities.machine.insert{name="coal",count=50}''')
                    proto = Prototype.StoneFurnace
                r["initial"] = snap()
                (run / f'{cid}-initial.json').write_text(json.dumps(r["initial"], indent=2))
                r["initial_sha256"] = hashlib.sha256(json.dumps(r["initial"], sort_keys=True).encode()).hexdigest()
                ent = ns.get_entity(proto, Position(x=0,y=4 if cid == "continuous_iron" else 0))
                admin(f"game.speed={args.speed};game.tick_paused=false")
                if cid == "recipe_power":
                    action(r, "set_recipe", lambda: ns.set_entity_recipe(ent, Prototype.IronGearWheel))
                    action(r, "insert", lambda: ns.insert_item(Prototype.IronPlate, ent, quantity=20))
                    end = await_state(lambda s: s["entities"]["machine"]["products"] >= 1, case["timeout_seconds"])
                    m = end["entities"]["machine"]
                    passed = m["products"] >= 1 and m["energy"] > 0 and count(m["input"], "iron-plate") <= 18 and count(m["output"], "iron-gear-wheel") >= 1
                elif cid == "locked_recipe":
                    a = action(r, "set_locked_recipe", lambda: ns.set_entity_recipe(ent, Prototype.ProcessingUnit))
                    end = snap()
                    passed = not a["ok"] and end["entities"]["machine"].get("recipe") != "processing-unit" and not end["processing_unit_enabled"]
                elif cid == "research":
                    action(r, "set_research", lambda: ns.set_research(Technology.Automation))
                    action(r, "insert_science", lambda: ns.insert_item(Prototype.AutomationSciencePack, ent, quantity=10))
                    action(r, "get_research_progress", lambda: ns.get_research_progress(Technology.Automation))
                    end = await_state(lambda s: s["technologies"]["automation"], case["timeout_seconds"])
                    passed = end["technologies"]["automation"] and count(end["entities"]["machine"]["input"], "automation-science-pack") == 0
                elif cid == "research_prerequisite":
                    a = action(r, "set_unavailable_research", lambda: ns.set_research(Technology.Automation3))
                    end = snap()
                    passed = not a["ok"] and not end.get("research") and not end["technologies"]["automation-3"]
                elif cid == "oil":
                    action(r, "set_recipe", lambda: ns.set_entity_recipe(ent, RecipeName.BasicOilProcessing))
                    admin('storage.cap_entities.machine.insert_fluid{name="crude-oil",amount=100}')
                    r["operator_input_state"] = snap()
                    end = await_state(lambda s: s["entities"]["machine"]["fluids"].get("petroleum-gas",0) >= 45, case["timeout_seconds"])
                    fluids = end["entities"]["machine"]["fluids"]
                    passed = fluids.get("petroleum-gas",0) >= 45 and fluids.get("crude-oil",0) == 0
                elif cid in ("rocket", "rocket_bad_target"):
                    until = time.monotonic() + case["timeout_seconds"]
                    for attempt in range(400):
                        for item in (Prototype.ProcessingUnit, Prototype.LowDensityStructure, Prototype.RocketFuel):
                            if count(snap()["inventory"], item.value[0]) > 0:
                                action(r, "insert_" + item.value[0], lambda item=item: ns.insert_item(item, ent, quantity=1000))
                        ready = snap()
                        if ready["entities"]["machine"]["ready"] or time.monotonic() >= until:
                            break
                        time.sleep(.2)
                    r["prelaunch"] = ready
                    if ready["entities"]["machine"]["ready"]:
                        admin('local i=storage.cap_entities.machine.get_inventory(defines.inventory.rocket_silo_rocket);if i then i.insert{name="satellite",count=1} end')
                        launch = action(r, "launch_rocket_at_0_1000" if cid == "rocket_bad_target" else "launch_rocket", lambda: ns.launch_rocket(Position(x=0,y=1000 if cid == "rocket_bad_target" else 0)))
                        end = await_state(lambda s: s["launch_events"] >= 1, 20)
                    else:
                        end = ready
                    passed = (not launch["ok"] and end["launch_events"] == 0) if cid == "rocket_bad_target" and ready["entities"]["machine"]["ready"] else cid == "rocket" and end["launch_events"] == 1
                else:
                    def advance_ticks(ticks):
                        admin(f'''game.tick_paused=true;storage.cap_stop_tick=game.tick+{ticks};script.on_nth_tick(1,function() if game.tick>=storage.cap_stop_tick then game.tick_paused=true end end);game.tick_paused=false''')
                        state = await_state(lambda s: s["paused"], 10)
                        admin('script.on_nth_tick(1,nil)')
                        return state
                    base_state = advance_ticks(600)
                    windows = []
                    for window in range(3):
                        end = advance_ticks(1200)
                        delta = count(end["entities"]["machine"]["output"], "iron-plate") - count(base_state["entities"]["machine"]["output"], "iron-plate")
                        windows.append({"start": base_state, "end": end, "plates_added": delta, "target_ticks": 1200, "actual_ticks": end["tick"]-base_state["tick"]})
                        base_state = end
                    r["windows"] = windows
                    passed = all(w["plates_added"] >= 1 and w["actual_ticks"] == 1200 for w in windows)
                r["final"] = end
                r["status"] = "passed" if passed else "failed"
            except Exception as exc:
                r["status"] = "setup_error" if not r["actions"] else "failed"
                r["error"] = str(exc)
                try:
                    r["final"] = snap()
                except Exception:
                    pass
            r["wall_seconds"] = time.monotonic() - begin
            results.append(r)
            (run / f'{case["id"]}-result.json').write_text(json.dumps(r, indent=2))
            print(json.dumps({"case": case["id"], "status": r["status"], "wall_seconds": r["wall_seconds"], "error": r.get("error")}), flush=True)
        (run / "results.json").write_text(json.dumps(results, indent=2))
    finally:
        if instance and server.poll() is None:
            try:
                prepare_final_save(instance)
            except Exception as exc:
                (run / "shutdown-error.txt").write_text(str(exc))
        server.terminate()
        try:
            server.wait(timeout=20)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
        log.close()
        if server.returncode == 0 and not (run / "shutdown-error.txt").exists():
            shutil.copyfile(game / "working.zip", game / "final.zip")
        (run / "timing.json").write_text(json.dumps({"complete_wall_seconds": time.monotonic() - started, "server_exit_code": server.returncode}, indent=2))


if __name__ == "__main__":
    main()
