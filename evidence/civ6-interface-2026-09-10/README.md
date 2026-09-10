# Civ player interface checks, 10 September 2026

These are interface checks, not the fixed-budget baseline panel. The game
ran in one normal graphical Mac client. Each model attempt used a fresh
ChatGPT-authenticated Codex process with gpt-6-astra and medium reasoning.
Each had a five-minute playing limit. No separately billed API call was used.
Subscription cost is unknown. Token counts appear in `attempts.json`.

## Process isolation

Astra received only the task and a generic local HTTP client in a new
workspace. Its process had no project instructions, conversation history,
previous run folder, MCP configuration, or external model access in its tools.
The shell could read and write its own workspace. Reads of a dummy external
canary and the repository's Civ task document were denied. OPENAI_API_KEY
was absent. The first probe had conflicting instructions and did not attempt
the reads; the corrected second probe performed them.

This is a tested file boundary and a restricted game API. It is not a claim
of a complete adversarial host sandbox: shell networking remains enabled.
The operator owns the single FireTuner connection during play. The player
has no API for raw Lua, world setup, saves, hidden tiles, or the evaluator.

## Recorded attempts

| Attempt | Result |
| --- | --- |
| a | Stopped after two completed turns. End-turn handling needed repair. |
| b | Stopped while closing a boost popup with the wrong handler. |
| c | Stopped after two turns. A queued move returned control for unit orders. |
| d | Reached the target in 34 turns and 253.53 seconds, using 124 requests. Terminal save matched. Strict trace verification failed because a boundary callback was recorded late. |

Attempt d is **target reached, evidence invalid**, not a verified pass. The
recorder reported five hold rounds and terminal science 22.31640625. It shows
why the task must not be described as a demonstrated direct-Astra failure.
It also does not certify feasibility until a clean captured attempt passes
the complete verifier. The original trace remains intact.

An eight-turn operator control with normal research, production, movement,
and improvement actions passed after the popup repair. An exact action replay
reproduced the queued-movement stop. The live Scout had one movement point
left after reaching its destination. The normal UNITOPERATION_SKIP_TURN
operation resolved it, and the next request advanced the game by one turn.
The interface now reports known blockers to the player and checks both the
core turn and boundary callback before returning a completed turn.

The earlier generic rules-row read stopped the connection and required a
restart during setup. It was replaced with a fixed list of public fields.
After restart, enabled community mods became active on load. They were
disabled before further trials. The starting state then matched its saved
hash. Original mod preferences are retained for later restoration.

## Remaining work

Run the full 20-minute direct baseline panel. Certify three economy map cases
with legal completions. Complete live combat capture tests, combat starting
saves, and direct combat baselines. No continuous Method search or runtime
LLM ablation has started.

Raw traces, keys, workspaces, game saves, and complete model logs stay outside
Git. `attempts.json` is the reviewed summary. The exact starting save remains
`CivTask_Economy_Base_Start_v2.Civ6Save` with SHA-256
`1be8153bbb8295773be73979cf59426afacacf5627de4c5994082aaf9d9fc659`.
