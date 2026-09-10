"""Private native Factorio process used by the science host and save verifier."""
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import time

from factorio_rcon import RCONClient

ROOT = Path(__file__).resolve().parents[1]
FACTORIO = "/Applications/factorio.app/Contents/MacOS/factorio"
RUNTIME = Path(__file__).with_name("science_runtime.lua")


class Server:
    def __init__(self, directory, *, rcon_port, game_port, factorio=FACTORIO, save=None):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=False)
        self.process = self.client = self.log = None
        self.factorio = factorio
        data = Path(factorio).resolve().parents[1] / "data"
        (self.directory / "config.ini").write_text(f"[path]\nread-data={data}\nwrite-data={self.directory}\n")
        mods = self.directory / "mods"
        mods.mkdir()
        (mods / "mod-list.json").write_text(json.dumps({"mods": [
            {"name": n, "enabled": n == "base"} for n in ["base", "quality", "elevated-rails", "space-age"]]}))
        settings = json.loads((data / "server-settings.example.json").read_text())
        settings.update(name="Method science checker", visibility={"public": False, "lan": False},
                        require_user_verification=False, auto_pause=False, autosave_interval=0)
        settings_path = self.directory / "server.json"
        settings_path.write_text(json.dumps(settings))
        base = [factorio, "--config", str(self.directory / "config.ini"), "--mod-directory", str(mods)]
        self.save = self.directory / "world.zip"
        if save:
            shutil.copyfile(save, self.save)
        else:
            gen = self.directory / "map.json"
            gen.write_text(json.dumps({"seed": 1, "peaceful_mode": True,
                "autoplace_settings": {kind: {"treat_missing_as_default": False, "settings": {}}
                                       for kind in ["entity", "tile", "decorative"]}}))
            with (self.directory / "create.log").open("w") as log:
                subprocess.run(base + ["--create", str(self.save), "--map-gen-settings", str(gen)],
                               stdout=log, stderr=log, check=True, timeout=60)
        password = secrets.token_urlsafe(32)
        log_path = self.directory / "server.log"
        self.log = log_path.open("w")
        os.chmod(log_path, 0o600)
        try:
            self.process = subprocess.Popen(base + ["--start-server", str(self.save),
                "--bind", f"127.0.0.1:{game_port}", "--rcon-bind", f"127.0.0.1:{rcon_port}",
                "--rcon-password", password, "--server-settings", str(settings_path)],
                stdout=self.log, stderr=self.log)
            limit = time.monotonic() + 30
            while time.monotonic() < limit:
                if self.process.poll() is not None:
                    raise RuntimeError("Factorio stopped; see the private server log")
                try:
                    self.client = RCONClient("127.0.0.1", rcon_port, password, timeout=5)
                    self.command("rcon.print(game.tick)")
                    return
                except Exception:
                    if self.client:
                        self.client.close()
                        self.client = None
                    time.sleep(.1)
            raise TimeoutError("Factorio startup timed out")
        except BaseException:
            self.close()
            raise

    def command(self, code):
        return self.client.send_command("/sc " + code)

    def read(self, expression):
        # Large RCON packets are very slow in the dependency's string parser.
        # Capture once, then transfer bounded chunks without advancing the snapshot.
        raw = self.command("science_read_json=helpers.table_to_json({value=" + expression + "}); "
                           "if #science_read_json<=16000 then rcon.print(science_read_json) "
                           "else rcon.print('CHUNKS:'..#science_read_json) end")
        try:
            if raw.startswith("CHUNKS:"):
                length = int(raw.split(":", 1)[1])
                parts = []
                index = 1
                while index <= length:
                    chunk = self.command(f"local a={index}; local z=math.min(a+15999,#science_read_json); "
                        "while z<#science_read_json and string.byte(science_read_json,z+1)>=128 "
                        "and string.byte(science_read_json,z+1)<192 do z=z-1 end; "
                        "rcon.print(helpers.table_to_json({part=string.sub(science_read_json,a,z),next_index=z+1}))")
                    chunk = json.loads(chunk)
                    if chunk["next_index"] <= index:
                        raise ValueError("non-advancing response chunk")
                    parts.append(chunk["part"])
                    index = chunk["next_index"]
                raw = "".join(parts)
            return json.loads(raw)["value"]
        except (ValueError, KeyError) as error:
            raise RuntimeError("Game read failed: " + raw[:500]) from error
        finally:
            self.command("science_read_json=nil")

    def install(self):
        result = self.command(RUNTIME.read_text() + '\nrcon.print("installed")')
        if result.strip() != "installed":
            raise RuntimeError("Science runtime installation failed: " + result)

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        if self.log:
            self.log.close()
            self.log = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
