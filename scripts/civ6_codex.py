"""Fresh Astra Codex processes for Civ 6 baselines. No prior game context.

The supervisor supplies task text, never a repository or another run folder.
The game server must enforce allowed operations and action budgets.
Run folders and temporary login state stay under the user Codex home, not
/tmp. The macOS minimal sandbox can read /tmp; no trial files go there.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from urllib.parse import urlparse

MODEL = "gpt-6-astra"
HELPER = '''"""Generic local game HTTP client. No retries of game actions."""
import json
import sys
import urllib.error
import urllib.request
ENDPOINT = __ENDPOINT__
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise RuntimeError("Redirect refused")
def act(action):
    if not ENDPOINT:
        raise RuntimeError("No game endpoint in this run")
    req = urllib.request.Request(ENDPOINT, json.dumps(action).encode(),
                                 {"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(req, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        return json.loads(error.read())
def observe():
    return act({"action": "observe"})
if __name__ == "__main__":
    print(json.dumps(act(json.load(sys.stdin))))
'''


def validate_endpoint(endpoint):
    if endpoint is None:
        return
    parsed = urlparse(endpoint)
    if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
            or not parsed.port or parsed.path != "/action" or parsed.query
            or parsed.fragment or parsed.username or parsed.password):
        raise ValueError("Use http://127.0.0.1:PORT/action")


def command_for(binary, workspace, final_path):
    settings = {
        "model_reasoning_effort": '"medium"',
        "model_provider": '"openai"',
        "forced_login_method": '"chatgpt"',
        "approval_policy": '"never"',
        "web_search": '"disabled"',
        "allow_login_shell": "false",
        "project_doc_max_bytes": "0",
        "history.persistence": '"none"',
        "shell_environment_policy.inherit": '"none"',
        "shell_environment_policy.set.PATH": '"/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"',
        "features.multi_agent": "false",
        "features.apps": "false",
        "default_permissions": '"civ6"',
    }
    # Runtime paths only; no user home, repository, other trials, or auth files.
    paths = (":minimal", "/usr", "/bin", "/sbin", "/System", "/Library", "/Applications", "/opt/homebrew", "/private/etc")
    rules = ", ".join(json.dumps(path) + ' = "read"' for path in paths)
    settings["permissions"] = '{ civ6 = { filesystem = { ' + rules + ', ":workspace_roots" = "write" }, network = { enabled = true } } }'
    command = [str(binary), "exec", "--ignore-user-config", "--ignore-rules",
               "--ephemeral", "--skip-git-repo-check", "--json", "--color", "never",
               "-C", str(workspace), "-m", MODEL, "-o", str(final_path)]
    for key, value in settings.items():
        command += ["-c", f"{key}={value}"]
    return command + ["-"]


def parse_events(path):
    result = {"completed_turns": 0, "input_tokens": 0, "cached_input_tokens": 0,
              "output_tokens": 0, "cache_write_input_tokens": 0, "reasoning_output_tokens": 0, "usage_known": False, "errors": [], "thread_id": None}
    for line in path.read_text(errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            result["errors"].append({"type": "invalid_jsonl", "line": line})
            continue
        kind = event.get("type")
        if kind == "thread.started":
            result["thread_id"] = event.get("thread_id")
        if kind in ("error", "turn.failed"):
            result["errors"].append(event)
        if kind == "turn.completed":
            result["completed_turns"] += 1
            usage = event.get("usage")
            if usage:
                result["usage_known"] = True
                for key in ("input_tokens", "cached_input_tokens", "output_tokens", "cache_write_input_tokens", "reasoning_output_tokens"):
                    result[key] += usage.get(key, 0)
    if not result["usage_known"]:
        for key in ("input_tokens", "cached_input_tokens", "output_tokens", "cache_write_input_tokens", "reasoning_output_tokens"):
            result[key] = None
    return result


def stop_group(process):
    # Always kill the group, including children left after the CLI exits.
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def run_codex(task, output_dir, endpoint=None, wall_seconds=300, *, binary=None, auth_home=None):
    """Return execution evidence, not a game score. Never resume a Codex thread.

    output_dir must not exist. auth_home is trusted supervisor configuration.
    Method steps must pass only remaining trial time, never a renewed budget.
    """
    if not isinstance(task, str) or not task.strip():
        raise ValueError("Task must be nonempty text")
    if not math.isfinite(wall_seconds) or wall_seconds <= 0:
        raise ValueError("Wall time must be positive and finite")
    validate_endpoint(endpoint)
    binary = Path(binary or shutil.which("codex") or "codex").resolve()
    auth_home = Path(auth_home or os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    started = time.monotonic()
    summary = {"model": MODEL, "reasoning_effort": "medium", "auth": "chatgpt",
               "wall_limit_seconds": wall_seconds, "started_unix": time.time(),
               "returncode": None, "status": "infrastructure_failure",
               "subscription_cost_usd": None, "api_calls": 0}
    process = None
    old_handlers = {}
    try:
        isolated_root = auth_home / "isolated-civ6"
        isolated_root.mkdir(mode=0o700, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="run-", dir=isolated_root) as temp:
            root = Path(temp).resolve()
            workspace = root / "work"
            home = root / "home"
            credentials = root / "auth"
            for folder in (workspace, home, credentials):
                folder.mkdir(mode=0o700)
            # Copy only login state; never copy settings, memory, plugins, or history.
            shutil.copyfile(auth_home / "auth.json", credentials / "auth.json")
            (credentials / "auth.json").chmod(0o600)
            helper = HELPER.replace("__ENDPOINT__", repr(endpoint))
            (workspace / "task.md").write_text(task)
            (workspace / "game.py").write_text(helper)
            (output / "task.md").write_text(task)
            (output / "game.py").write_text(helper)
            summary["source_sha256"] = {"runner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                       "task": hashlib.sha256(task.encode()).hexdigest(),
                                       "helper": hashlib.sha256(helper.encode()).hexdigest()}
            command = command_for(binary, workspace, output / "final.txt")
            summary["command"] = command
            environment = {"PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
                           "HOME": str(home), "CODEX_HOME": str(credentials),
                           "TMPDIR": str(workspace), "LANG": "en_US.UTF-8"}
            prompt = ("Read task.md and complete that task. game.py provides act(dict) and observe(). "
                      "Use only the supplied task and this workspace. Except for exact paths in an explicitly assigned sandbox isolation probe, do not inspect external files, "
                      "other processes, other endpoints, credentials, or previous runs. Do not start "
                      "another agent or model. Use the declared game API only. Return a brief factual result.\n")
            with (output / "events.jsonl").open("w") as events, (output / "stderr.log").open("w") as errors:
                process = subprocess.Popen(command, cwd=workspace, env=environment, stdin=subprocess.PIPE,
                                           stdout=events, stderr=errors, start_new_session=True, text=True)
                summary["pid"] = process.pid
                (output / "process.json").write_text(json.dumps({"pid": process.pid, "command": command, "started_unix": time.time()}) + "\n")
                if threading.current_thread() is threading.main_thread():
                    def interrupted(signum, frame):
                        raise InterruptedError(f"Signal {signum}")
                    for sig in (signal.SIGTERM, signal.SIGINT):
                        old_handlers[sig] = signal.signal(sig, interrupted)
                try:
                    process.communicate(prompt, timeout=max(0.001, wall_seconds - (time.monotonic() - started)))
                    summary["returncode"] = process.returncode
                    summary["status"] = "completed" if process.returncode == 0 else "infrastructure_failure"
                except subprocess.TimeoutExpired:
                    summary["status"] = "timeout"
                finally:
                    stop_group(process)
                    summary["returncode"] = process.returncode
            # Retain policy-created files, but never archive credentials or home.
            shutil.copytree(workspace, output / "workspace", symlinks=True)
    except Exception as error:
        summary["error"] = f"{type(error).__name__}: {error}"
        if isinstance(error, InterruptedError):
            summary["status"] = "interrupted"
    finally:
        if process is not None:
            stop_group(process)
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)
        events = output / "events.jsonl"
        if events.exists():
            summary["usage"] = parse_events(events)
            if summary["status"] == "completed" and (summary["usage"]["errors"] or not summary["usage"]["completed_turns"]):
                summary["status"] = "infrastructure_failure"
        summary["wall_seconds"] = time.monotonic() - started
        (output / "execution.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--endpoint")
    parser.add_argument("--seconds", type=float, default=300)
    args = parser.parse_args()
    result = run_codex(args.task.read_text(), args.output, args.endpoint, args.seconds)
    print(json.dumps(result))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
