# Run the factory repair comparison

Read [the experiment](repair-experiment.md) and [the player task](repair-task.md) first. Use the existing Python environment and Factorio installation from [the science setup](run-science-task.md). The current host uses the installed Factorio 2.0.77 binary. The local Method runtime must be the clean revision `eec2cfd1a5f0bd8254fb8213b88be76cff44ad21` under `runs/method3-runtime`.

The model runner requires the installed `codex` CLI and an existing ChatGPT login. It uses a temporary copy of that login with restricted permissions. Do not put credentials in a task file or policy. No API key is used. Model use consumes the signed-in subscription allowance.

## Prepare cases

The case builder is an operator tool. Never expose its files or control records to a playing agent or policy author.

```sh
.venv/bin/python scripts/repair_cases.py build --split development --count 10 --output runs/repair-development
.venv/bin/python scripts/repair_cases.py build --split final --count 20 --output runs/repair-final-private
```

The builder keeps healthy, damaged, and repaired saves and their separate checks. It stops if a case does not meet all three conditions. Keep failed case records and use a new output directory for a replacement. Do not change a success condition to admit a case.

## Run direct Astra

```sh
.venv/bin/python scripts/repair_batch.py --cases runs/repair-development --output runs/repair-comparison --split development --count 10 --workers 1
```

Each case starts a new Codex instance. A run gets only the public task, the generic game client, and its own work folder. It can write and run code within that folder. Its records include game actions, model events, generated files, time, token use when available, and the separate save verdict.

## Search a Method

The initial example is `methods/repair-initial/initial.method`. Candidate versions are saved in separate folders under `methods/repair-search/`. Review candidate code before running it: Method code steps run as trusted local code; model shell commands run inside the checked file-access boundary.

```sh
.venv/bin/python scripts/repair_batch.py --cases runs/repair-development --output runs/repair-comparison/v01 --split development --count 10 --workers 1 --slot-start 1 --method methods/repair-search/v01/repair.method
```

Use a separate port slot for each active player. A Method code step calls the fixed `codex_step` function. Each call starts a fresh Astra instance and shares the original trial deadline. Method-native API calls are disabled. Read both Method traces and child Codex traces when accounting for model work.

After a batch, give the author only development evidence. Save changes as a new version. Run the same cases again. The batch stores file hashes and refuses changed candidates or mismatched resumed records. A completed case is not replayed when a batch resumes. An incomplete run must be inspected; it is never silently overwritten.

## Read saved recipes before selecting a Method

The original game reader can export an idle furnace recipe as `null`. Use the
separate `repair_review.review` function on every completed attempt, with its
original case folder. It reads the exact recipe objects retained in the original
save and applies the same success rules. It writes `review.json` and keeps the
original evidence. See the [reader note](../evidence/repair-search-2026-09-10/checker-note.md).
Do not review only failed attempts. Use one fixed reader version for both
approaches and all cases. Include this read in full processing time.

```python
from pathlib import Path
from repair_review import review
review(Path("runs/repair-comparison/direct-development-001"),
       Path("runs/repair-development/development-001"))
```

Run this example with `scripts` on the Python import path. Give simultaneous
reviews separate RCON and game ports. The final runner assigns its own ports.

## Final comparison

Select and freeze one Method using development results before running any final case. Run direct Astra and that frozen Method on separate copies of each final save. Keep the same task, limits, model, and checker. Use no case builder during the final comparison. Do not feed final results back to the author.

Create a selection JSON file before the first final attempt. It must contain
`candidate_files` from `repair_batch.candidate_hashes(policy_path)` and
`review_source_sha256` from `repair_batch.file_hash(Path("scripts/repair_review.py"))`.
Also record the selection rule, development scores, chosen version, and time.
Use all ten development results for each eligible version. Do not change this
file, the chosen Method, the reader, or the final case set after tests start.

```sh
.venv/bin/python scripts/repair_final.py --cases runs/repair-final-private --policy methods/repair-search/v04/repair.method --selection runs/repair-comparison/selection.json --output runs/repair-comparison/final
```

For each of the twenty cases, this command starts one direct player and one
Method player on separate worlds. It waits for both, verifies both saves, and
applies the same recipe read before moving to the next case. It retains failed
attempts and stops on an infrastructure fault. A safe resume accepts completed
matching records and refuses changed or incomplete records. The final output
is `report.json`. Audit the complete result before publication:

```sh
.venv/bin/python scripts/repair_audit.py runs/repair-comparison/final --cases runs/repair-final-private --policy methods/repair-search/v04/repair.method --selection runs/repair-comparison/selection.json
```

This audit checks saved evidence hashes, fixed-rule decisions, selected policy
files, model records, full time, and report totals. It reads files only. Native
saved-game proof comes from each attempt's independent review.

```sh
.venv/bin/python -m unittest discover -s scripts -p 'test_repair*.py' -q
```

The completed experiment's selection record is published with its evidence.
For a later policy search, use new final cases. Do not reuse exposed final
results as evidence of performance on unseen cases.

All raw runs and saves stay in ignored local folders. Publish reviewed summaries only. Count production failures, request-rule failures, timeouts, and infrastructure faults separately.
