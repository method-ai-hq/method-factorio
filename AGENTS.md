# Project instructions

## Communication and scope

- Use plain, simple English in reports and project documents.
- Read README.md, GOALS.md, DESIGN.md, EXPERIMENT.md, PLAN.md, DECISIONS.md, and HACKATHON.md before implementation.
- Keep facts, design choices, and measured results distinct.
- This repository is independent of its parent workspace. Commit only this project's intended files.
- Do not read or enumerate the parent workspace's sensitive directory. Do not import private parent code, history, account data, or run logs.

## Experiment integrity

- The root design documents and evaluator are controlled by the project owner. Playing and policy-improvement agents may not edit them.
- Candidate Methods may change only within the declared experiment rules.
- Preserve policy versions and unsuccessful trial results. Do not change the success condition to match a result.
- Keep game administration and evaluation controls outside the playing tool interface.
- Use actual game evidence for a win. Model approval is not proof of completion.
- Do not start paid experiments without an operator-set spending cap.
- Keep game time and wall-clock time separate. Record pause and speed settings.

## Git and release

- Work on main unless the user requests another branch.
- Before changes, check status and fetch origin when a remote exists. If clean, use a fast-forward-only pull.
- Preserve unrelated work. Do not reset, discard, or stash it to prepare a release.
- Commit completed changes and push main to origin/main.
- Run an existing deployment workflow after a push when one exists. This design-only repository has no deployment target yet.
- Update HACKATHON.md when new features or results are ready for the demo.

## Secrets and files

- Never request secrets in chat. Use the owner's macOS hidden-input helper at ~/.codex/scripts/ask-secret.sh when a required secret is missing.
- Keep secrets in an ignored env file with restricted permissions. Never print or commit them.
- Keep game installations, saves, local runs, caches, and raw recordings out of Git by default.
- Publish only reviewed evidence with clear provenance and appropriate rights.

## Search recovery and recording

- Use `docs/headless-policy-search.md` for the owner's current capture rule: optimization may be headless; recorded demonstrations are separate attempts.
- On an infrastructure failure, preserve evidence, pause new trials, diagnose the cause, and continue authorized repair work within the remaining limits. A scheduler `repair_required` result is a handoff to the supervisor, not proof that the whole task is complete.
- Do not start a batch at untested concurrency. The fixed settings must name the validated level. Native graphical clients must start one at a time.
- Keep game-launch limits separate from permitted offline repairs. Never exceed a hard limit, restart the job clock, or silently replace failed results.
- `docs/headless-search-goal.md` is a proposed next-job prompt. Its new budgets and paid-call permission apply only when the owner adopts it.
