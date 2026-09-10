# One-minute Factorio presentation

Use the silent 60-second video and record your own voice from [the narration](narration.md). The script is 142 words. Read [the explanation](explanation.md) for policy history, why the result may have improved, limitations, next experiments, and possible applications.

## Local media

The reviewed videos stay in ignored local storage, not in Git:

- `runs/repair-demo-20260910/presentation/factorio-method-60s.mp4`: 60-second silent presentation, 1920×1080.
- `runs/repair-demo-20260910/presentation/quick-repair-labeled.mp4`: native game replay of final case 003. It adds a drill, corrects a belt, and turns an inserter.
- `runs/repair-demo-20260910/presentation/furnace-recovery-labeled.mp4`: native game replay of final case 011. It shows blocked furnace placements and the eventual new furnace/belt route.
- `runs/repair-demo-20260910/presentation/search.png`, `results.png`, and `honesty.png`: full-resolution result cards for reuse in an editor.

The videos have no microphone audio. The game clips use native Factorio rendering, with eight captured images per second converted to 30 video frames per second. The displayed action sequence has edited timing and game speed 4. The furnace clip first runs the original initial waiting interval at speed 20, without recording, to preserve the state that blocked its first placement.

## Evidence boundary

The original benchmark ran headless. These are later visual action replays, not historical screen recordings or new agent attempts. No new model call was made. Observations, model thinking, and the finish request are omitted from replay. No replay time is included in benchmark results.

Each selected replay uses a copy of the original damaged save and only its recorded world-changing requests. It checks each accepted or rejected action against the retained trace and checks the initial and final equipment against the source run. Equipment comparison covers names, positions, directions, and assembler recipes; it does not claim identical inventories, item positions, machine progress, or game ticks. The original evidence files are hashed before and after capture.

The viewer uses a spectator. Intro crash-site creation and starter items are disabled only in the demo copy. The game action functions are installed after the graphical client joins so the server and client execute the same code. These capture changes do not alter any benchmark source or result.

Four failed capture setup attempts are retained locally: two caught changes caused by spectator setup, one exposed missing game functions on the joined client, and one found that omitting the original wait changed a furnace placement outcome. They are not scored trials. Only the two successful, checked captures are used in the presentation.

## Reproduce

The existing Factorio installation, Python environment, and FFmpeg are required. Only one graphical client starts at a time. Use new output folders for captures; existing folders are never overwritten.

```sh
.venv/bin/python scripts/repair_demo_capture.py --case runs/repair-cases-final-private-1/final-003 --trial runs/repair-search-20260910/final/method/method-final-003 --output runs/repair-demo-new/quick --camera -72 3 1.8
.venv/bin/python scripts/repair_demo_capture.py --case runs/repair-cases-final-private-1/final-011 --trial runs/repair-search-20260910/final/method/method-final-011 --output runs/repair-demo-new/recovery --camera -26 -64 1.8
```

The render script records this presentation's source folders and edit decisions. Point its source constants at a new pair of checked captures and use a new output folder before rendering again. It refuses to overwrite an existing presentation directory.

## Claim to lead with

“Practice improved a reusable procedure. On twenty unseen factories, it used less execution time and input than a fresh direct Astra run.”

Use “about 23% less full time” and “56% fewer reported input tokens, including cached input.” Time uses the same eighteen successful pairs; tokens use all twenty attempts. Do not turn those figures into a dollar-saving claim. Search costs are separate.

Use “fewer tool-rule errors in this sample” instead of a broad claim of greater reliability. Both repaired all twenty factories. We changed several policy components together and have not isolated their individual effects.

See [the measured results](../../evidence/repair-search-2026-09-10/README.md), [additional trace statistics](trace-statistics.json), and [the demo evidence record](provenance.json).
