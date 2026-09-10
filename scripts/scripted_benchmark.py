"""Fixed no-model environment probes. This is not an agent-authored policy.

Uses only the declared playing interface. Setup and shutdown stay in the host.
Each run keeps its raw responses, errors, measurements, and terminal save.
"""
import argparse
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import signal
import socket
import statistics
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def item_count(items, name):
    if isinstance(items, dict):
        return items.get(name, 0)
    return sum(i["count"] for i in items if i["name"] == name)


def latency(values):
    values = sorted(values)
    return {"n": len(values), "median_ms": statistics.median(values) * 1000,
            "p95_ms": values[math.ceil(.95 * len(values)) - 1] * 1000,
            "max_ms": max(values) * 1000} if values else {"n": 0}


class Client:
    def __init__(self, run, transport, socket_path, port):
        self.run, self.transport = run, transport
        self.socket_path, self.port = socket_path, port
        self.trace = (run / "benchmark-actions.jsonl").open("x", buffering=1)
        self.rows = []

    def send(self, request, group="recipe", required=True, lose_response=False):
        start = time.monotonic()
        response = None
        error = None
        try:
            payload = json.dumps(request).encode()
            if self.transport == "http":
                conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=95)
                conn.request("POST", "/action", payload, {"Content-Type": "application/json"})
                if lose_response:
                    conn.close()
                else:
                    response = json.loads(conn.getresponse().read())
                    conn.close()
            else:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
                    conn.settimeout(95)
                    conn.connect(str(self.socket_path))
                    conn.sendall(payload + b"\n")
                    if not lose_response:
                        with conn.makefile("rb") as stream:
                            response = json.loads(stream.readline())
        except Exception as exc:
            error = str(exc)
        row = {"request": request, "group": group, "started_monotonic": start,
               "seconds": time.monotonic() - start, "response": response,
               "transport_error": error, "response_deliberately_lost": lose_response}
        self.rows.append(row)
        self.trace.write(json.dumps(row) + "\n")
        if required and (error or (not lose_response and not response.get("ok"))):
            raise RuntimeError(f"Action failed; no retry: {request}: {error or response}")
        return response


def production(client, speed):
    started = time.monotonic()
    initial = client.send({"action": "observe"})["state"]
    iron = client.send({"action": "nearest", "resource": "iron-ore"})["result"]
    coal = client.send({"action": "nearest", "resource": "coal"})["result"]
    client.send({"action": "move", "position": iron})
    mined_iron = client.send({"action": "harvest", "position": iron, "quantity": 20})
    assert item_count(mined_iron["state"]["inventory"], "iron-ore") == 20
    client.send({"action": "move", "position": coal})
    mined_coal = client.send({"action": "harvest", "position": coal, "quantity": 5})
    assert item_count(mined_coal["state"]["inventory"], "coal") == 5
    placed = client.send({"action": "place", "item": "stone-furnace",
                          "position": coal, "exact": False})["result"]
    target = {"name": placed["name"], "position": placed["position"]}
    client.send({"action": "insert", "item": "iron-ore", "quantity": 20, "target": target})
    loaded = client.send({"action": "insert", "item": "coal", "quantity": 5, "target": target})
    state = loaded["state"]
    # The same game-time production allowance at each speed; poll from actual state.
    until = time.monotonic() + 90
    while state["iron_plates_produced"] < 20 and time.monotonic() < until:
        state = client.send({"action": "wait", "seconds": min(5, 5 / speed)})["state"]
    elapsed = time.monotonic() - started
    furnaces = state["furnaces"] or []
    checks = {"new_iron_plates_20": state["iron_plates_produced"] - initial["iron_plates_produced"] == 20,
              "furnace_output_20": sum(item_count(f["output"], "iron-plate") for f in furnaces) == 20,
              "ore_consumed_20": sum(item_count(f["input"], "iron-ore") for f in furnaces) == 0,
              "inventory_ore_empty": item_count(state["inventory"], "iron-ore") == 0,
              "furnace_products_finished_20": sum(f["products_finished"] for f in furnaces) == 20,
              "fuel_consumed": sum(item_count(f["fuel"], "coal") for f in furnaces) < 5,
              "requested_speed": state["speed"] == speed}
    return {"passed": all(checks.values()), "checks": checks, "seconds": elapsed,
            "game_ticks": state["tick"] - initial["tick"], "initial": initial,
            "final": state, "coal_position": coal, "furnace": target}


def probes(client, result, observe_count, controls):
    checks = {}
    first = client.send({"action": "observe"}, "latency")["state"]
    start = time.monotonic()
    for _ in range(observe_count - 1):
        last = client.send({"action": "observe"}, "latency")["state"]
    duration = time.monotonic() - start
    checks["observation_soak"] = {"passed": True, "count": observe_count,
        "seconds": duration, "game_ticks": last["tick"] - first["tick"],
        "achieved_ticks_per_second": (last["tick"] - first["tick"]) / duration}
    before = client.send({"action": "observe"}, "rate")["state"]
    start = time.monotonic()
    after = client.send({"action": "wait", "seconds": 5}, "rate")["state"]
    duration = time.monotonic() - start
    checks["game_rate"] = {"seconds": duration, "ticks": after["tick"] - before["tick"],
        "achieved_ticks_per_second": (after["tick"] - before["tick"]) / duration,
        "requested_speed": after["speed"], "paused": after["paused"]}
    if not controls:
        return checks
    cases = [
        ("deny_raw_lua", {"action": "execute", "code": "return game.tick"}),
        ("deny_research_grant", {"action": "grant_research", "research": "automation"}),
        ("deny_speed_change", {"action": "set_speed", "speed": 20}),
        ("deny_negative_quantity", {"action": "craft", "item": "iron-gear-wheel", "quantity": -1}),
        ("deny_impossible_craft", {"action": "craft", "item": "rocket-silo"}),
        ("deny_coordinate_limit", {"action": "place", "item": "burner-mining-drill", "position": {"x": 1001, "y": 0}}),
        ("deny_out_of_reach", {"action": "place", "item": "burner-mining-drill", "position": {"x": -900, "y": -900}}),
    ]
    for name, request in cases:
        before = client.send({"action": "observe"}, "negative-check")["state"]
        response = client.send(request, "negative", required=False)
        after = client.send({"action": "observe"}, "negative-check")["state"]
        fields = ("inventory", "position", "research", "iron_plates_produced")
        unchanged = all(before[k] == after[k] for k in fields)
        checks[name] = {"passed": bool(response and not response.get("ok") and unchanged),
                        "unchanged_fields": unchanged, "response": response}
    # Deliberately lose a craft response, then read state; never send the craft again.
    before = client.send({"action": "observe"}, "recovery")["state"]
    client.send({"action": "craft", "item": "iron-gear-wheel", "quantity": 1},
                "recovery", lose_response=True)
    after = client.send({"action": "observe"}, "recovery")["state"]
    checks["lost_response_recovery"] = {
        "passed": item_count(after["inventory"], "iron-gear-wheel") - item_count(before["inventory"], "iron-gear-wheel") == 1
        and item_count(before["inventory"], "iron-plate") - item_count(after["inventory"], "iron-plate") == 2,
        "repeat_sent": False, "action_id_recovery": "not supported; read state after uncertain response"}
    placed = client.send({"action": "place", "item": "burner-mining-drill",
        "position": result["coal_position"], "exact": False}, "placement")
    target = {"name": "burner-mining-drill", "position": placed["result"]["position"]}
    checks["drill_placement_inventory"] = {"passed": item_count(placed["state"]["inventory"], "burner-mining-drill") == 0}
    rotations = []
    for i in range(30):
        direction = ["RIGHT", "DOWN", "LEFT", "UP"][i % 4]
        response = client.send({"action": "rotate", "target": target, "direction": direction}, "rotation", required=False)
        entities_response = client.send({"action": "entities"}, "rotation-check")
        entities = entities_response["result"]
        if isinstance(entities, dict):
            entities = list(entities.values())
        observed = [e for e in entities if isinstance(e, dict) and e.get("name") == target["name"] and e.get("position") == target["position"]]
        rotations.append({"direction": direction, "passed": bool(response and response.get("ok") and observed and observed[0].get("direction") == "Direction." + direction), "observed": observed})
        if not response or not response.get("ok"):
            # The following read inspected state. Stop this family after uncertainty.
            break
    checks["rotations"] = {"passed": len(rotations) == 30 and all(r["passed"] for r in rotations), "cases": rotations}
    picked = client.send({"action": "pickup", "target": target}, "pickup")
    checks["drill_pickup_inventory"] = {"passed": item_count(picked["state"]["inventory"], "burner-mining-drill") == 1}
    return checks


def batch_probes(client):
    """Keep per-action checks identical while varying request grouping."""
    result = {"groups": []}
    initial = client.send({"action": "observe"}, "batch-setup")["state"]
    placed = client.send({"action": "place", "item": "stone-furnace",
        "position": initial["position"], "exact": False}, "batch-setup")
    target = {"name": "stone-furnace", "position": placed["result"]["position"]}
    client.send({"action": "pickup", "target": target}, "batch-setup")
    sequences = {
        "observe": [{"action": "observe"} for _ in range(100)],
        "place_pickup": [request for _ in range(50) for request in [
            {"action": "place", "item": "stone-furnace", "position": target["position"]},
            {"action": "pickup", "target": target}]],
    }
    for family, sequence in sequences.items():
        for size in (1, 10, 50):
            start = time.monotonic()
            passed = True
            completed = 0
            for offset in range(0, len(sequence), size):
                response = client.send({"batch": sequence[offset:offset + size]},
                    f"batch-{family}-{size}", required=False)
                if not response or not response.get("ok"):
                    client.send({"action": "observe"}, "batch-recovery")
                    result["groups"].append({"family": family, "batch_size": size,
                        "passed": False, "completed": completed, "error": response})
                    # A failed mutating batch is never repeated or continued blindly.
                    return result
                for request, reply in zip(sequence[offset:offset + size], response["results"]):
                    state = reply["state"]
                    if family == "place_pickup":
                        expected = 0 if request["action"] == "place" else 1
                        passed = passed and item_count(state["inventory"], "stone-furnace") == expected
                        passed = passed and len(state["furnaces"]) == 1 - expected
                    else:
                        passed = passed and state["inventory"] == initial["inventory"]
                    completed += 1
            elapsed = time.monotonic() - start
            result["groups"].append({"family": family, "batch_size": size, "actions": completed,
                "requests": math.ceil(len(sequence) / size), "seconds": elapsed,
                "actions_per_second": completed / elapsed, "passed": passed})
    before = client.send({"action": "observe"}, "batch-stop-check")["state"]
    response = client.send({"batch": [
        {"action": "craft", "item": "iron-gear-wheel", "quantity": 1},
        {"action": "set_speed", "speed": 20},
        {"action": "craft", "item": "iron-gear-wheel", "quantity": 1}]},
        "batch-stop", required=False)
    after = client.send({"action": "observe"}, "batch-stop-check")["state"]
    result["partial_batch_stop"] = {"response": response,
        "passed": response and not response.get("ok") and response.get("executed") == 2
        and item_count(after["inventory"], "iron-gear-wheel") - item_count(before["inventory"], "iron-gear-wheel") == 1
        and item_count(before["inventory"], "iron-plate") - item_count(after["inventory"], "iron-plate") == 2,
        "repeated_actions": False}
    return result


def episode(args, transport, speed):
    name = f"{args.prefix}-{transport}-s{speed:g}"
    run = ROOT / "runs" / name
    sock = Path("/tmp") / f"factorio-{name}.sock"
    host_log = ROOT / "runs" / (name + "-host.log")
    started = time.monotonic()
    report = {"baseline": "D fixed script, no model", "transport": transport, "speed": speed,
        "seed": args.seed, "billing": "No model calls; no API calls", "name": name,
        "controller_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    client = None
    with host_log.open("x") as log:
        command = [sys.executable, "-u", str(ROOT / "scripts/control_test.py"), "--run", name,
            "--seed", str(args.seed), "--seconds", "500", "--actions", "1600", "--port", str(args.port),
            "--rcon-port", str(args.rcon_port), "--game-port", str(args.game_port), "--speed", str(speed),
            "--transport", transport]
        if transport == "unix":
            command += ["--socket-path", str(sock)]
        host = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=log, start_new_session=True)
        try:
            deadline = time.monotonic() + 150
            while time.monotonic() < deadline:
                if host.poll() is not None:
                    raise RuntimeError("Host setup failed; inspect private host log")
                if '"ready": true' in host_log.read_text():
                    break
                time.sleep(.2)
            else:
                raise RuntimeError("Host readiness timed out")
            report["startup_seconds"] = time.monotonic() - started
            client = Client(run, transport, sock, args.port)
            if args.batch_only:
                report["batching"] = batch_probes(client)
            else:
                result = production(client, speed)
                report["production"] = result
                report["probes"] = probes(client, result, 1000 if transport == "http" and speed == 1 else 100, speed == 1)
        except Exception as exc:
            report["exception"] = str(exc)
            report["traceback"] = traceback.format_exc()
        finally:
            if client:
                client.trace.close()
                report["latency"] = {group: latency([r["seconds"] for r in client.rows if r["group"] == group])
                    for group in sorted({r["group"] for r in client.rows})}
            host.terminate()
            try:
                host.wait(timeout=35)
            except subprocess.TimeoutExpired:
                os.killpg(host.pid, signal.SIGKILL)
                host.wait()
            report["complete_trial_seconds"] = time.monotonic() - started
            report["host_exit_code"] = host.returncode
            report["terminal_save_exists"] = (run / "game/final.zip").exists()
            report["clean_shutdown"] = not (run / "shutdown-error.txt").exists()
            if args.batch_only:
                tested = report.get("batching", {})
                checks_passed = len(tested.get("groups", [])) == 6 and all(
                    group["passed"] for group in tested.get("groups", [])) and bool(
                    tested.get("partial_batch_stop", {}).get("passed"))
            else:
                checks_passed = report.get("production", {}).get("passed", False) and all(
                    check.get("passed", True) for check in report.get("probes", {}).values())
            report["passed"] = bool(checks_passed and not report.get("exception")
                and report["terminal_save_exists"] and report["clean_shutdown"] and host.returncode == 0)
            if run.exists():
                write_json(run / "benchmark-report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--seed", type=int, default=44340)
    parser.add_argument("--port", type=int, default=18804)
    parser.add_argument("--rcon-port", type=int, default=27204)
    parser.add_argument("--game-port", type=int, default=34304)
    parser.add_argument("--speeds", nargs="+", type=float, default=[1, 5, 20])
    parser.add_argument("--transports", nargs="+", choices=["http", "unix"], default=["http", "unix"])
    parser.add_argument("--batch-only", action="store_true", help="Run batching probes instead of production")
    args = parser.parse_args()
    if Path(args.prefix).name != args.prefix or len(args.prefix) > 45:
        parser.error("Use a plain run prefix of at most 45 characters")
    reports = []
    started = time.monotonic()
    for speed in args.speeds:
        for transport in args.transports:
            if time.monotonic() - started >= 1800:
                break
            result = episode(args, transport, speed)
            reports.append(result)
            print(json.dumps({"name": result["name"], "passed": result["passed"],
                "seconds": result.get("complete_trial_seconds"), "exception": result.get("exception")}), flush=True)
    write_json(ROOT / "runs" / (args.prefix + "-summary.json"), reports)
    return 0 if len(reports) == len(args.speeds) * len(args.transports) and all(
        report["passed"] for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
