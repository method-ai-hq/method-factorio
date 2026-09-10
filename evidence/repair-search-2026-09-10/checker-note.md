# Exact recipe names from saved game history

During development, version 4 case 005 was marked as a failure even though the
game made the required products. Each measured minute had 15 red packs,
12–13 green packs, and 60 new copper plates. The checker assigned zero
completed furnace products to copper.

The cause was a JSON export error. When a furnace was idle at a sample boundary,
the old reader used its previous recipe. Factorio can return that recipe as a
recipe object. The old code treated the object as a string, and JSON exported it
as `null`. The [Factorio 2.0.77 API schema](https://lua-api.factorio.com/2.0.77/runtime-api.json)
permits this object type in `previous_recipe`.

The original native save retained the exact recipe objects in all four
historical samples. The new `repair-recipe-export/2` reader loads that original
save and reads those stored names. It does not infer recipes from the final
inventory, reconstruct a game, or repeat a playing attempt.

Before using those names, the reader repeats the original case, source,
record, action-trace, and native save checks on a temporary copy. It then
changes only the affected recipe fields in a separate copy of the sampled
record and applies the unchanged production rules. The original record,
summary, verdict, trace, and save remain unchanged. Each `review.json` records
their hashes, the reader hash, the exact field corrections, and both outcomes.

The positive check changed version 4 case 005 from fail to pass, using eight
exact saved recipe references. The same reader kept direct case 001 as a pass.
A separate damaged-factory control still failed: it made 15 red packs and no
green packs per minute. All of these checks passed independent native save
verification. Seven focused reader tests also passed, including checks that
request-rule failures and time/action limits remain enforced.

The reader is applied to every approach and every development and final
attempt. Its source is frozen before final tests. Full processing time includes
the additional independent read. The original game-host and player sources,
case saves, success thresholds, and playing budgets stay unchanged.

Frozen reader SHA256:
`6452a7f5a0b93beb1ca0ed4774275b569e158c0f846c3d11d65d3c50800b33b3`.

Local proof folders: `runs/repair-idle-furnace-diagnosis-1/` and
`runs/repair-review-negative-control-1/`.
