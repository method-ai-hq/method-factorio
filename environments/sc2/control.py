#!/usr/bin/env python3
"""Operator setup checks for PySC2. This is not a scored policy evaluator."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import signal
import sys
import time
import traceback
import uuid

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
from absl import flags
from pysc2 import maps, run_configs
from pysc2.agents import scripted_agent
from pysc2.env import mock_sc2_env, sc2_env
from pysc2.lib import actions, features
from s2clientprotocol import sc2api_pb2

ROOT = Path(__file__).resolve().parents[2]
MAP = "MoveToBeacon"


def interface():
    return features.AgentInterfaceFormat(
        feature_dimensions=features.Dimensions(screen=64, minimap=64),
        use_feature_units=True,
    )


def offline():
    """Exercise upstream observations, legal action encoding, and reset offline."""
    with mock_sc2_env.SC2TestEnv(
        map_name=MAP, players=[sc2_env.Agent(sc2_env.Race.terran)],
        agent_interface_format=interface(),
    ) as env:
        first = env.reset()[0]
        assert first.first()
        assert first.observation.feature_screen.shape[1:] == (64, 64)
        assert env.step([actions.FUNCTIONS.no_op()])[0].mid()
        assert env.reset()[0].first()
    transform = features.Features(features.AgentInterfaceFormat(
        feature_dimensions=features.Dimensions(screen=64, minimap=64)))
    encoded = transform.transform_action(
        None, actions.FUNCTIONS.Move_screen("now", [12, 20]),
        skip_available=True,
    )
    decoded = sc2api_pb2.Action.FromString(encoded.SerializeToString())
    command = decoded.action_feature_layer.unit_command
    assert command.ability_id == 3794
    assert (command.target_screen_coord.x, command.target_screen_coord.y) == (12, 20)
    print(json.dumps({"status": "offline_pass", "live_game_tested": False}))


def doctor():
    report = {
        "python": platform.python_version(), "platform": platform.platform(),
        "packages": {p: importlib.metadata.version(p) for p in
                     ("pysc2", "protobuf", "numpy", "s2clientprotocol")},
        "live_game_tested": False,
    }
    try:
        config = run_configs.get()
        report["game_path"] = config.data_dir
        report["game_version"] = config.version._asdict()
        binary_name = {"Darwin": "SC2.app/Contents/MacOS/SC2",
                       "Linux": "SC2_x64", "Windows": "SC2_x64.exe"}[platform.system()]
        binary = Path(config.data_dir) / "Versions" / (
            "Base%05d" % config.version.build_version) / binary_name
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise FileNotFoundError(f"Game executable is missing or not executable: {binary}")
        # Read through the same map resolver that a real launch uses.
        data = maps.get(MAP).data(config)
        report["map_sha256"] = hashlib.sha256(data).hexdigest()
        report["status"] = "ready_for_live_check"
    except Exception as error:
        report.update(status="installation_incomplete", error=str(error))
    print(json.dumps(report, indent=2))
    return report


def smoke():
    """One bounded real game using the upstream MoveToBeacon script."""
    report = doctor()
    if report["status"] != "ready_for_live_check":
        return 2
    out = ROOT / "runs" / "sc2" / (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    started = time.monotonic()
    report.update(status="running", map=MAP, seed=1, realtime=False,
                  step_mul=8, game_loop_limit=2048, wall_limit_seconds=180,
                  game_time_mode="advances only when the client steps",
                  requested_game_speed="game API default; not measured",
                  concurrency=1, policy="pysc2.agents.scripted_agent.MoveToBeacon",
                  purpose="environment_control_check", model_calls=0,
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out / "settings.json").write_text(json.dumps(report, indent=2) + "\n")

    def timeout(_signum, _frame):
        raise TimeoutError("180-second wall limit reached")

    previous = signal.signal(signal.SIGALRM, timeout)
    signal.alarm(180)
    env = None
    try:
        env = sc2_env.SC2Env(
            map_name=MAP, players=[sc2_env.Agent(sc2_env.Race.terran)],
            agent_interface_format=interface(), random_seed=1,
            realtime=False, step_mul=8, game_steps_per_episode=2048,
            visualize=False, disable_fog=False,
        )
        agent = scripted_agent.MoveToBeacon()
        agent.setup(env.observation_spec()[0], env.action_spec()[0])
        agent.reset()
        obs = env.reset()[0]
        initial_loop = int(obs.observation.game_loop[0])
        reward = 0.0
        moved = False
        with (out / "actions.jsonl").open("x") as trace:
            for step in range(256):
                if obs.last():
                    break
                action = agent.step(obs)
                moved |= int(action.function) == actions.FUNCTIONS.Move_screen.id
                before = int(obs.observation.game_loop[0])
                obs = env.step([action])[0]
                reward += float(obs.reward)
                trace.write(json.dumps({
                    "step": step, "action": {"function": int(action.function),
                        "arguments": [[int(v) for v in arg] for arg in action.arguments]},
                    "loop_before": before, "loop_after": int(obs.observation.game_loop[0]),
                    "reward": float(obs.reward), "wall_seconds": time.monotonic() - started,
                }) + "\n")
                trace.flush()
        final_loop = int(obs.observation.game_loop[0])
        replay = Path(env.save_replay(str(out), prefix="control-check"))
        report.update(initial_game_loop=initial_loop, final_game_loop=final_loop,
                      total_reward=reward, move_sent=moved, replay=str(replay),
                      replay_sha256=hashlib.sha256(replay.read_bytes()).hexdigest())
        if not (moved and final_loop > initial_loop and reward > 0):
            raise RuntimeError("No verified beacon reward after movement")
        report.update(status="live_control_pass", live_game_tested=True)
    except Exception as error:
        report.update(status="live_control_fail", error=str(error))
        (out / "error.txt").write_text(traceback.format_exc())
    finally:
        # Write the result before shutdown so a shutdown failure leaves evidence.
        report["wall_seconds_before_close"] = time.monotonic() - started
        (out / "result.json").write_text(json.dumps(report, indent=2) + "\n")
        try:
            if env is not None:
                env.close()
        except Exception as error:
            report.update(status="live_control_fail", close_error=str(error))
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous)
        report["wall_seconds"] = time.monotonic() - started
        (out / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "result_dir": str(out)}, indent=2))
    return 0 if report["status"] == "live_control_pass" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("offline", "doctor", "smoke"))
    args = parser.parse_args()
    flags.FLAGS([sys.argv[0]])
    if args.command == "offline":
        offline()
        return 0
    if args.command == "doctor":
        return 0 if doctor()["status"] == "ready_for_live_check" else 2
    return smoke()


if __name__ == "__main__":
    sys.exit(main())
