# Method field notes

A single-page story of the Factorio experiments and the active Civ VI work.
It uses plain HTML, CSS, and JavaScript. No build framework or network service
is required to read it. The source template is `story/index.html`.

## Build the complete page

From the repository root:

```sh
python3 scripts/build_project_story.py
```

Open `runs/method-story/index.html` in a browser. It is one portable HTML file
with three embedded MP4 videos, embedded poster images, inline charts, and
reviewed result data. The full file is about 43 MB. External evidence links
need an internet connection; the story, charts, and media work offline.

The build needs the local media from the [repair demo](../docs/repair-demo/README.md).
Game media stays outside Git. A fresh source checkout alone does not contain
these clips. The builder fails if a required clip is absent; it does not
substitute generated or unrelated footage.

The builder reads the reviewed repair report and checks that both approaches
use matching case hashes. It emits a media and report hash manifest beside
the HTML. No private session logs or parent workspace code are read.

## Evidence and updates

- All final chart values come from
  `evidence/repair-search-2026-09-10/final-report.json`.
- Development values come from the adjacent `development-search.json`.
- The prose links each stage to its reviewed evidence.
- Civ VI is a dated development snapshot at 21:05 UTC on 10 September 2026.
  It includes the completed two-run-per-arm pilot. More maps and combat
  remain pending.
- Video captions identify later native action replays and edited timing.
- The summary of Methods draws on the owner-authorized brainstorm discussion
  and the public Method specification. It does not export that discussion.

The source design uses a narrow reading column, a chapter rail, generous
space, restrained green charts, and large type. It takes layout cues from
long-form research pages and AI 2027, without copying their text or branding.

## Validation

Checked the built page at 1440 × 1080 and 390 × 844 in Chromium. Checks cover
chart controls, all twenty result rows, chapter links, horizontal overflow,
all three embedded video streams, and browser errors. Visual checks cover
the opening, result charts, and the mobile policy chart. Test captures and
the local browser check script stay in `runs/method-story/`.
