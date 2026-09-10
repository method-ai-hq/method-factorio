# Civ 6: competing Method searches

Status: design v1, 10 September 2026. This specifies a new experiment. It does
not authorize spending, start agents, or establish a working game validator.
The Factorio experiment and its results remain unchanged.

## Question and recommendation

Can two independent groups improve the same starting Method through fixed,
matched tests, and which final Method wins more unseen Civ 6 games?

Use two levels of competition:

1. **First experiment: matched games.** Groups A and B each design a Method.
   Each Method controls the human player in a separate copy of the same
   starting save, against the same built-in opponent. This tests competing
   policy design. It is not direct A-versus-B gameplay.
2. **Later experiment: direct play.** A and B control opposing civilizations
   in one world. This needs a separate, validated control system. Do not treat
   a matched-game result as evidence that direct control works.

A group can contain an author and a critic. Both work on the group's Method.
Group size is not the number of civilizations or game clients. Members share
one design budget and one execution budget. Extra agents do not create extra
compute allowances.

## What is known

The locally installed civ6-mcp source is upstream revision
`dd2019056371b92ea4854e879ddf05a8cad95e8a`. In the preceding setup, MCP
initialization returned 76 tools, and a live FireTuner connection returned the
result of a Lua print command. No loaded-game, win, fog-of-war, or independent
save validation was established by that check.

The upstream [agent-versus-agent design][ava] is explicitly a proposal. Its
author reports that FireTuner is disabled in multiplayer, including hot-seat.
That restriction has not been independently tested on this installation.
Simply connecting two MCP processes will not assign them different players;
the current adapter normally uses `Game.GetLocalPlayer()`.

The proposed AI-player control extension is not a fair duel implementation.
In particular, stopping unit moves does not prove that AI research, production,
diplomacy, or other actions have stopped. Restoring movement can change game
rules. Those issues must be resolved before direct games count.

The upstream [README][mcp] requires Gathering Storm. Its local availability
and the full tool contract must pass setup checks. Do not silently change to
base-game rules if the expansion is unavailable.

## Fixed rules for matched-games-v1

These are proposed design choices, not measured settings. Once the owner
adopts v1, a changed rule requires a new experiment ID. The execution lock
binds these rules to tested files and operator budgets before the first trial.

| Item | Fixed rule |
| --- | --- |
| Game | Steam Civ 6, Gathering Storm rules; exact game build and content hashes in the lock. |
| World | Duel-size Pangaea, standard resources and start position, Ancient Era. |
| Players | Human Trajan/Rome, built-in AI Gilgamesh/Sumeria; Prince difficulty. |
| Other actors | No city-states; barbarians off; tribal villages off. |
| Other settings | Online game speed; disaster intensity 0; no optional game modes; no gameplay mods. |
| Victory | Domination only. Disable score and all other victory conditions. |
| Start | Fresh generated world before the human's first action; no supplied cities, units, research, or resource grants beyond normal game rules. |
| Horizon | At most 250 completed human turns. Also stop at a verified terminal result. |
| Time | 90 minutes of wall time per play attempt, starting before save load. AI processing and model thinking count. |
| Local limits | 120 seconds per model request, 60 seconds per tool request, 300 seconds per human turn. No automatic turn end. |
| Compute | At most 500 model requests, 2,000,000 input tokens, 100,000 output tokens per attempt. Sum all agents and checks. |
| Actions | At most 10,000 tool requests and 10,000 primitive game actions per attempt. Each member of a batch counts; each request is at most 100 actions. |
| Concurrency | One native Civ 6 process and one broker connection. Start all trials serially. |
| Recording | No video during search or final evaluation; retain state and action evidence. Later recorded demos are new attempts. |
| Retry | No replacement play attempts. An uncertain mutation is never blindly retried. |
| Policy state | Empty private state at each attempt; no learning across evaluation games. |

Civ 6 still needs its graphical game process. Omitting video is not a claim
that Civ 6 has a validated headless server. Record game turns, game speed,
wall time, and each pause separately. Thinking does not authorize an opponent
turn. The operator verifies this in setup.

The numerical ceilings above are not spending permission. Before launch, the
operator must set a total dollar cap, equal dollar caps for both design groups,
an equal per-attempt dollar cap, a final-evaluation reserve, a setup allowance,
and an absolute job deadline. No missing budget is interpreted as unlimited
or zero cost. A central caller reserves the worst permitted request cost
before each call, and stops if the remaining cap cannot cover it. Record the
pricing source and missing usage; unmetered execution cannot pass the lock.

## What a Method may change

Both groups begin from one frozen initial Method, M0. An independent initial
author creates M0 before receiving development feedback. Also freeze a direct
agent baseline, D, with the same tools, knowledge, model access, helper-code
access, and total play budget. M0 and D receive the same objective, without an
operator-written build order. Record their full authoring inputs.

Candidates may change instructions, decomposition, internal checks, bounded
loops, helper code, retained-state formats, and the use of the approved model
profiles. Method v3 is the proposed execution format. Bind a public runtime
revision and its validated model profiles in the lock; do not import private
workspace code. All child calls go through the central usage meter.

Candidates may not change game settings, tools, visibility rules, the broker,
validator, save lists, budgets, result rules, or the other group's files.
Every submission is a content-addressed bundle. It includes the Method, all
executable helpers, prompts, dependencies, parent hash, and change hypothesis.
Freeze it before testing. No edits during an attempt. Working state may change
only through the already-frozen procedure.

Policy helpers must run in an enforced process boundary with no host shell,
raw FireTuner access, external network, shared home directory, game-save access,
or validator credentials. The existing unrestricted desktop MCP is for setup;
it is not the playing interface for this experiment. Prompt restrictions alone
are insufficient, especially when groups compete to exploit a system.

## Two-round hill climb

This is a small, exploratory pilot. Two rounds are fixed before execution.
Each round gives each group 30 minutes of design time and at most two designer
agents sharing that time and the group's total cap. Designers may inspect
public documentation and their group's development records. They cannot inspect the other group's source, messages,
or any final-evaluation files. Each can see the other's validated aggregate
score after a round. In-game observations remain separate from design data.

Prepare eight development scenarios in advance: two screen scenarios and two
confirmation scenarios per round. Use the same scenarios for both groups.
Confirmation results are released only after that round's candidate is frozen.
Round-two scenarios differ from round one. Both groups submit before either
receives that round's results. No extra candidates or screen tests are allowed.

For each group and round:

1. Freeze one child of the current incumbent with a specific hypothesis.
2. Run child and incumbent from each of the two screen saves. Use fresh state
   for every run. Alternate which runs first by scenario index and round.
3. Compare paired results using the rule below. If the screen does not pass,
   retain the incumbent. Preserve the child and all results.
4. If the screen passes, run both on the two unused confirmation saves.
5. Promote only if confirmation also passes. Otherwise retain the incumbent.

A run has `success = 1` only for an independently verified domination victory
within all limits. All policy failures, losses, and limit stops have
`success = 0`. For a pair, the child wins if its success is higher. If both
succeed, the child wins only if it used fewer completed human turns; equal
turns tie. If neither succeeds, the pair ties. A candidate passes a stage only
with at least one paired win and no paired loss. Ties retain the incumbent.
Missing evidence or an infrastructure fault blocks the stage; it cannot help
a candidate pass.

This conservative rule can produce no promotions. If full-game victories are
too rare, report a flat search. Do not add score, population, or military power
to the fitness after observing results. A shorter score-based experiment would
need a new ID and could establish only improvement on that shorter task.

This first pilot uses a fixed AI opponent. It therefore avoids a moving
opponent during selection. Rivalry is between designers, not a claim of
self-play or minimax training.

## Final evaluation

Before search, an operator prepares and seals eight separate final starting
saves. Freeze D, M0, A-final, and B-final before exposing any final observations.
All four run on all eight saves, once each. Keep the same fixed game settings;
this tests transfer to new maps, not new leaders or game rules. A reused bundle
still receives its own scheduled run; do not copy an earlier result.

Use a four-policy rotation by scenario index: D/M0/A/B, M0/A/B/D, A/B/D/M0,
B/D/M0/A. Run serially. Hide intermediate final results from designers until
all scheduled runs finish. The operator releases only the active scenario to
the broker, never the full save directory or seed list to a candidate.

Report each policy's verified wins out of eight and every paired outcome.
Primary comparisons are A-final versus M0 and B-final versus M0. Also show
A-final versus B-final and D versus M0. Report paired discordant counts and
a one-sided exact sign test on discordant success pairs for each primary
comparison (null: equal success probability; alternative: final beats M0).
Use p = 1 when there are no discordant pairs. Apply Holm correction to the two
primary p-values at family-wise alpha 0.05. Report a 95% exact binomial interval
for each win rate, and for the conditional win fraction among discordant pairs
when any exist. Secondary comparisons are descriptive. Eight scenarios
are a small sample; do not call a training promotion statistical proof.

The competitive winner is the policy with more verified final wins. Equal
wins mean no winner; turns, cost, and wall time remain secondary measures.
Do not select a new candidate after seeing final results. If the final set is
incomplete or has unresolved infrastructure/evidence failures, publish the
matrix as incomplete and declare no experiment winner. Known policy failures
still count in the scheduled denominator.

Maximum workload: 32 search games plus 32 final games = 64 play attempts.
At 90 minutes each, play alone can require 96 serial hours. Design adds at most
two group-hours. Setup and independent inspections need separate reserved time.
These are hard ceilings, not a time or cost prediction. Before lock, measure
turn latency and inspection time without paid search; abandon this pilot or
issue a smaller experiment version if it does not fit the owner's cap. Do not
truncate a large design and call the partial sample the planned experiment.

## Failure handling

A model timeout, policy crash, invalid action loop, or exhausted per-policy
budget is a policy failure when the game and broker are healthy. A rejected
illegal action has no game effect and uses the request allowance; repeated
errors can exhaust the budget. Attempted access outside the process boundary
is a policy disqualification and counts as a failure.

A game crash, broken state reader, wrong starting save, incomplete trusted
log, validator failure, or unmetered call is an infrastructure/evidence fault.
Preserve evidence, stop new trials, and repair offline within the remaining
operator limits. Do not reset the clock, replace the attempt, omit the fault,
or grant a candidate a win by default. Changes to protected components require
a new lock and cohort; results from different locks are not pooled. There is
no discretionary replay rule based on whether a candidate was winning.

## Direct A-versus-B extension

Use a new experiment ID, `civ6-direct-v1`, only after the tests in
[VALIDATOR.md](VALIDATOR.md) pass. Prefer two genuinely human-controlled seats
with normal rule-enforcing operations if a supported control path exists.
The current FireTuner path does not establish that support. If single-player
AI-seat takeover is the only route, it must prove equal control and no built-in
AI intervention. Otherwise stop; matched games remain a separate valid option.

The proposed direct profile has two major civilizations, no other actors,
Domination only, the same 250-round ceiling, and draws when neither wins.
It uses one broker and a host-controlled turn lease. Only the active seat may
submit actions. No player ID from a candidate can choose its authority. Each
leg gives both policies the same total compute and time allowance. The host
charges only the active seat for its play clock and charges load time equally;
a separate whole-match deadline bounds both. Opponent thinking never consumes
a player's clock. Define and lock the direct schedule and budgets separately.

Each direct match consists of two fresh legs on one fixed world setup. Swap
A and B between the two seats, including civilization and starting location.
This balances seat advantage across the pair; it does not assume map symmetry.
Score a game win as 1, a draw as 0.5, and loss or attributable policy forfeit as
0. Infrastructure faults have no competitive score and block the match.

For direct hill climbing, freeze both groups' incumbents at the start of an
outer round. Freeze an opponent panel containing the opposing incumbent,
opposing initial policy, and all distinct earlier opposing champions. Child
and incumbent face the identical panel, with equal weight per distinct policy,
on identical development maps and both seats. Promote only after a strict
mean match-point improvement on both screen and separate confirmation sets,
with no reduction against the opposing initial policy. Publish both new
incumbents together after the round; never update one opponent midway through
the other group's gate. Keep all archived policies and the full payoff matrix.

This reduces forgetting and response to one weak opponent. It cannot remove
cycles such as A beating B, B beating C, and C beating A. Final direct reporting
must include a frozen archive tournament plus the A-final/B-final duel. A duel
winner is not necessarily the strongest general policy. A direct experiment
must lock panel growth, map counts, final matrix, and resulting maximum games
before launch; it is not executable under the matched-game schedule above.

## Deliverables and launch gates

The design consists of this protocol, [the validator contract](VALIDATOR.md),
and [the execution-lock template](lock-template.json). The template is blocked
by default. It contains no adopted spending cap, generated scenario corpus,
validated broker, or working live validator.

Implement and test the restricted broker and independent inspector next. Then
bind the tested versions, scenario commitments, budgets, and test report in an
operator-owned lock. Freeze that lock outside designer write access. Its hash
is supplied to the scheduler and validator through a trusted channel. A JSON
field that says `approved` is not authorization.

[ava]: https://github.com/lmwilki/civ6-mcp/blob/dd2019056371b92ea4854e879ddf05a8cad95e8a/docs/agent-vs-agent.md
[mcp]: https://github.com/lmwilki/civ6-mcp/blob/dd2019056371b92ea4854e879ddf05a8cad95e8a/README.md
