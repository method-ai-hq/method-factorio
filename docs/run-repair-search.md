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

## Final comparison

Select and freeze one Method using development results before running any final case. Run direct Astra and that frozen Method on separate copies of each final save. Keep the same task, limits, model, and checker. Use no case builder during the final comparison. Do not feed final results back to the author.

```sh
.venv/bin/python -m unittest discover -s scripts -p 'test_*.py' -q
```

All raw runs and saves stay in ignored local folders. Publish reviewed summaries only. Count production failures, request-rule failures, timeouts, and infrastructure faults separately.
