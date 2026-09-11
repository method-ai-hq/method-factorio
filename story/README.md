# Method experiment story

A single-page story of the Factorio experiments and the Civ VI pilot setup error.
It uses plain HTML, CSS, and JavaScript. No build framework or network service
is required to read it. The source template is `story/index.html`.

## Read the complete page

Read the [public story](https://method-ai-hq.github.io/method-factorio/)
in your browser. GitHub Pages serves the reviewed `complete.html` file,
including its charts and three video clips. Changes to that file on `main`
publish through `.github/workflows/publish-story.yml`. The workflow can also
be run manually.

Download [complete.html](complete.html) and open it in a browser. The 43 MB
file includes all three reviewed demo clips and works offline. A clone of
this repository includes the complete page. GitHub may show a download
button instead of a preview because of the file size.

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
The reviewed clips are embedded in `complete.html`; raw recordings and game
saves remain outside Git. Rebuilding requires the original local clip files.
The builder fails if a required clip is absent; it does not substitute footage.

The builder reads the reviewed repair report and checks that both approaches
use matching case hashes. It emits a media and report hash manifest beside
the HTML. No private session logs or parent workspace code are read. To refresh the
public copy after an edit, run:

```sh
python3 scripts/build_project_story.py --output story/complete.html
```

Commit the source, `complete.html`, and `build-manifest.json` together.

## Evidence and updates

- All final chart values come from
  `evidence/repair-search-2026-09-10/final-report.json`.
- Development values come from the adjacent `development-search.json`.
- The prose links each stage to its reviewed evidence.
- The Civ VI section states that the pilot did not execute through the
  Method CLI. It tested a written strategy supplied to Codex. Historical
  numerical results remain in an expandable note and are not presented as
  a Method runtime benchmark. More maps and combat remain unfinished.
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

The edited version cuts about one-third of the article text, removes decorative
labels, places repair clips beside the policy changes, and keeps technical
verification details in expandable notes.

The current article uses the owner-approved argument-led draft. Its main
headline is preserved, and the opening is “Using Astra to beat Astra.”
Changes to the complete HTML trigger the existing GitHub Pages workflow.
