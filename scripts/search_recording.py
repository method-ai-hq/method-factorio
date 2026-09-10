"""Actual Factorio capture through one graphical peer per game world.

The host owns this recorder. Do not expose its RCON connection to a policy.
Start the peer before FLE inserts functions into game storage: joining a live
FLE world can fail when Factorio tries to serialize those functions.
"""
from __future__ import annotations

import hashlib
import io
from PIL import Image
import json
from pathlib import Path
import shutil
import subprocess
import threading
import time

from search_startup import StartupFailure, client_stage, write_status


class Recorder:
    def __init__(self, run_dir, factorio, game_port, rcon_port, rcon_password,
                 deadline_epoch, fps=2, startup_seconds=120):
        if fps != 2:
            raise ValueError("The fixed recording rate is 2 frames per second")
        self.run = Path(run_dir).resolve()
        self.factorio = str(factorio)
        self.game_port, self.rcon_port = game_port, rcon_port
        self._password = rcon_password
        self.deadline = float(deadline_epoch)
        if not 0 < startup_seconds <= 120:
            raise ValueError("Client startup allowance must be in (0,120]")
        self.startup_seconds = startup_seconds
        self.peer_dir = self.run / "recording-peer"
        self.output = self.run / "recording"
        self.output.mkdir(parents=True, exist_ok=False)
        self.peer_dir.mkdir(parents=True, exist_ok=False)
        self.frames = self.peer_dir / "script-output" / "frames"
        self.frames.mkdir(parents=True)
        self.fps = fps
        self.error = None
        self.peer = None
        self.client = None
        self.thread = None
        self.closed = False
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.records = []
        self.next_frame = 0
        self.started_at = time.time()
        self.source_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        self.log = (self.output / "frames.jsonl").open("a", buffering=1)
        self.peer_log = None
        self.watchdog = threading.Thread(target=self._deadline_watch, daemon=True)
        self.watchdog.start()

    def _remaining(self, limit):
        value = min(limit, self.deadline - time.time())
        if value <= 0:
            raise TimeoutError("The job deadline has expired")
        return value

    def _deadline_watch(self):
        if not self.stop.wait(max(0, self.deadline - time.time())):
            self.error = "The recorder reached the job deadline"
            self.stop.set()
            if self.peer is not None and self.peer.poll() is None:
                self.peer.terminate()

    def start_peer(self):
        """Join a new server before FLE initialization; return after peer setup."""
        from factorio_rcon import RCONClient
        data = Path(self.factorio).resolve().parents[1] / "data"
        config = self.peer_dir / "config.ini"
        config.write_text(f"[path]\nread-data={data}\nwrite-data={self.peer_dir}\n"
                          "[general]\nlocale=en\n[graphics]\nfull-screen=false\n")
        mods = self.peer_dir / "mods"
        mods.mkdir()
        (mods / "mod-list.json").write_text(json.dumps({"mods": [
            {"name": n, "enabled": n == "base"}
            for n in ("base", "space-age", "quality", "elevated-rails")]}))
        self.peer_log = (self.output / "peer.log").open("w")
        command = [self.factorio, "--config", str(config), "--mod-directory", str(mods),
                   "--mp-connect", f"127.0.0.1:{self.game_port}", "--disable-audio",
                   "--window-size", "1280x720", "--force-graphics-preset", "very-low"]
        self.peer = subprocess.Popen(command, stdout=self.peer_log, stderr=subprocess.STDOUT)
        (self.output / "peer-process.json").write_text(json.dumps({
            "pid": self.peer.pid, "command": command, "deadline_epoch": self.deadline}, indent=2))
        self.client = RCONClient("127.0.0.1", self.rcon_port, self._password,
                                 timeout=min(5, self._remaining(5)))
        join_started = time.time()
        join_deadline = join_started + self._remaining(self.startup_seconds)
        stage = None
        while time.time() < join_deadline and not self.stop.is_set():
            observed = client_stage((self.output / "peer.log").read_text(errors="replace"))
            if observed != stage:
                stage = observed
                write_status(self.output / "startup.json", stage=stage,
                             started_at=join_started, deadline=join_deadline)
            if self.peer.poll() is not None:
                raise StartupFailure("client_exited", "The recording peer stopped; inspect recording/peer.log")
            raw = self.client.send_command("/sc rcon.print(#game.connected_players)")
            if raw and raw.strip().isdigit() and int(raw.strip()) >= 1:
                # This is setup before the initial state is frozen. A spectator
                # must not add a second character or its default starter kit.
                self.client.send_command('/sc for _,p in pairs(game.connected_players) do '
                    'local c=p.character; p.set_controller{type=defines.controllers.spectator}; '
                    'if c and c.valid then c.destroy() end end; rcon.print("spectator-ready")')
                write_status(self.output / "startup.json", stage="connected",
                             started_at=join_started, elapsed_seconds=time.time()-join_started)
                return
            self.stop.wait(.25)
        code = "graphics_loading_timeout" if stage == "loading_graphics" else "client_join_timeout"
        write_status(self.output / "startup.json", stage=stage, failure_code=code,
                     started_at=join_started, elapsed_seconds=time.time()-join_started)
        raise StartupFailure(code, "The client startup allowance expired during " + str(stage))

    def start(self):
        """Capture and verify the initial game image, then record continuously."""
        try:
            self.capture("initial", timeout=25)
        except Exception as exc:
            self.error = f"Initial frame failed: {exc}"
            raise
        self.thread = threading.Thread(target=self._loop, name="factorio-capture", daemon=True)
        self.thread.start()

    def _loop(self):
        target = time.monotonic() + 1 / self.fps
        while not self.stop.wait(max(0, target - time.monotonic())):
            try:
                self.capture()
            except Exception as exc:
                self.error = f"{type(exc).__name__}: {exc}"
                self.log.write(json.dumps({"error": self.error, "wall_time": time.time()}) + "\n")
                self.stop.set()
                return
            target += 1 / self.fps
            if target < time.monotonic():
                target = time.monotonic()

    def capture(self, label=None, timeout=5):
        """Request a native image and wait for its completed JPEG file."""
        with self.lock:
            self._remaining(5)
            if self.peer is None or self.peer.poll() is not None:
                raise RuntimeError("The recording peer is not running")
            index = self.next_frame
            self.next_frame += 1
            path = self.frames / f"frame-{index:06d}.jpg"
            wall_start = time.time()
            # Prefer the factory bounds once construction starts; otherwise show
            # the agent. This is only camera control, with no game-state changes.
            lua = '''local c=storage.agent_characters and storage.agent_characters[1]
local s=c and c.surface or game.surfaces[1]; local pos=c and c.position or {x=0,y=0}
local es=s.find_entities_filtered{force="player",type={"mining-drill","furnace","inserter","transport-belt"}}
local zoom=0.8
if #es>0 then local a,b,d,e=math.huge,math.huge,-math.huge,-math.huge
 for _,v in pairs(es) do a=math.min(a,v.position.x);b=math.min(b,v.position.y);d=math.max(d,v.position.x);e=math.max(e,v.position.y) end
 pos={x=(a+d)/2,y=(b+e)/2};zoom=math.min(1.5,1280/(32*(d-a+14)),720/(32*(e-b+10))) end
game.take_screenshot{surface=s,position=pos,resolution={1280,720},zoom=zoom,
 path="frames/FRAME",show_gui=false,show_entity_info=true,force_render=true,quality=85}
rcon.print(helpers.table_to_json({tick=game.tick,speed=game.speed,paused=game.tick_paused,position=pos,zoom=zoom}))'''
            raw = self.client.send_command("/sc " + lua.replace("FRAME", path.name))
            if not raw:
                raise RuntimeError("The native capture command returned no game state")
            state = json.loads(raw)
            wait_until = time.time() + self._remaining(timeout)
            while time.time() < wait_until:
                if path.exists() and path.stat().st_size > 100:
                    content = path.read_bytes()
                    if content[:2] == b"\xff\xd8" and content[-2:] == b"\xff\xd9":
                        break
                time.sleep(.01)
            else:
                raise TimeoutError(f"No complete native JPEG arrived within {timeout} seconds")
            with Image.open(io.BytesIO(content)) as picture:
                width, height = picture.size
                picture.verify()
            if (width, height) != (1280, 720):
                raise RuntimeError("The native capture has the wrong resolution")
            record = {"frame": index, "label": label, "path": str(path.relative_to(self.run)),
                      "wall_requested": wall_start, "wall_complete": time.time(),
                      "sha256": hashlib.sha256(content).hexdigest(), "game": state}
            self.records.append(record)
            self.log.write(json.dumps(record) + "\n")
            if label in ("initial", "final"):
                shutil.copyfile(path, self.output / f"{label}.jpg")
            return record

    def close(self):
        """Stop capture, close the peer, and encode the retained native frames."""
        if self.closed:
            return self.summary
        self.stop.set()
        if self.thread is not None:
            self.thread.join(timeout=max(0, min(6, self.deadline - time.time())))
        if self.thread is not None and self.thread.is_alive():
            self.error = self.error or "The capture thread did not stop"
        elif self.client is not None and self.peer is not None and self.peer.poll() is None:
            try:
                self.capture("final")
            except Exception as exc:
                self.error = self.error or f"Final frame failed: {exc}"
        if self.peer is not None and self.peer.poll() is None:
            self.peer.terminate()
            try:
                self.peer.wait(timeout=max(.1, min(3, self.deadline-time.time())))
            except subprocess.TimeoutExpired:
                self.peer.kill()
                self.peer.wait(timeout=2)
        if self.client is not None:
            self.client.close()
        if self.peer_log is not None:
            self.peer_log.close()
        self.log.close()
        video = self.output / "video.mp4"
        if self.records:
            try:
                with (self.output / "encode.log").open("w") as log:
                    subprocess.run(["ffmpeg", "-nostdin", "-y", "-framerate", str(self.fps),
                        "-i", str(self.frames / "frame-%06d.jpg"), "-c:v", "libx264",
                        "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", str(video)], stdout=log, stderr=log,
                        check=True, timeout=self._remaining(15))
            except Exception as exc:
                self.error = self.error or f"Video encoding failed: {exc}"
        gaps = [{"after_frame": a["frame"], "seconds": b["wall_requested"]-a["wall_requested"]}
                for a, b in zip(self.records, self.records[1:])
                if b["wall_requested"]-a["wall_requested"] > 1]
        complete = bool(self.records and video.exists() and video.stat().st_size > 100
                        and (self.output / "initial.jpg").exists()
                        and (self.output / "final.jpg").exists() and self.error is None)
        self.summary = {"mode": "native Factorio graphical-peer screenshot time-lapse",
            "replay": False, "resolution": [1280, 720], "source_image_format": "jpeg",
            "jpeg_quality": 85, "playback_fps": self.fps,
            "nominal_capture_fps": self.fps, "frames": len(self.records),
            "video": "recording/video.mp4", "timestamps": "recording/frames.jsonl",
            "initial_image": "recording/initial.jpg", "final_image": "recording/final.jpg",
            "gaps_over_one_second": gaps, "error": self.error, "complete": complete,
            "started_at": self.started_at, "closed_at": time.time(),
            "deadline_epoch": self.deadline,
            "source_sha256": self.source_sha256}
        if video.exists():
            self.summary["video_sha256"] = hashlib.sha256(video.read_bytes()).hexdigest()
        (self.output / "recording.json").write_text(json.dumps(self.summary, indent=2))
        self.closed = True
        return self.summary
