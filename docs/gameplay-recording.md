# Actual game recording

`scripts/search_recording.py` uses a separate graphical Factorio process for
each server. Factorio renders the images. This is not a replay or a drawing
made from JSON. The capture does not need screen recording permission and does
not include the user's desktop.

The host starts the graphical process before FLE setup. This order is required:
a later connection can fail because FLE puts functions in game storage that
Factorio cannot save for a new connection. The recording player becomes a
spectator. Its starting character is removed before the initial state is fixed.
The policy has no access to this setup connection.

After setup, the host requests and checks an initial image before it allows
policy actions. The recorder then requests about two images per wall-clock
second. Each image is 1280 by 720 pixels. Factorio saves JPEG images at quality 85. The camera shows the factory bounds
when machines exist. Before construction, it shows the agent. The first image
can wait up to 25 seconds for setup to finish on the graphical process. Later
images have a five-second limit. A recording error stops the host.

Each run contains these local files:

| File | Content |
| --- | --- |
| `recording/video.mp4` | H.264 video made from the actual game images, at two frames per second. |
| `recording/initial.jpg` and `recording/final.jpg` | Initial and final game images. |
| `recording/frames.jsonl` | Request and completion times, game tick, speed, pause state, camera position, and image hash. |
| `recording/recording.json` | Capture mode, frame count, gaps, errors, video hash, and completeness result. |
| `recording-peer/script-output/frames/` | Original game images. |
| `recording/peer.log` and `recording/encode.log` | Private process records. |

The video uses a fixed playback rate. Use `frames.jsonl` for exact wall-clock
times and game ticks. `gaps_over_one_second` lists long capture intervals. Game
speed and wall-clock time remain separate. The benchmark uses game speed 20.

The host must check recording completeness together with the action trace,
production result, save, and independent save inspection. A video alone does
not prove a pass. A failed startup can have no video; keep that failed attempt
and report the missing evidence.

The recorder has an absolute deadline. It stops its own graphical process and
uses a bounded `ffmpeg` process to close the video. It does not stop other
Factorio processes. All raw images, videos, game files, and logs stay in the
ignored `runs/` directory.

The local setup checks on 10 September 2026 recorded two separate game worlds
at the same time at speed 20. They produced 17 and 18 frames, with initial and
final images and no capture gaps longer than one second. `ffprobe` confirmed
H.264 video at 1280 by 720. These are capture checks, not scored policy trials.
Two earlier launches and their logs are also retained: one failed because the
parent process exited, and one captured ten native images successfully.

Factorio documents native JPEG capture and the quality setting in the
[game API reference](https://lua-api.factorio.com/latest/classes/LuaGameScript.html#take_screenshot).
The early capture checks used PNG files. JPEG capture was not validated in a
live game. It must pass a new setup check before scored use. Earlier PNG
evidence remains unchanged.
