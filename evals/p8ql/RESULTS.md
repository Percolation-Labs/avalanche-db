# P8QL agent eval: results

## Round 3b, 8 Nov 2026: the fuzzy lookup with a likeness wave (REM-1335)

**Versions:** avalanche-db with REM-1334 (every file, ids from bodies) and REM-1335 (a bare
`LIKE` returns a wave of five; `WAVE n` carries n into hops). History store rebuilt from
p8-subsystems 0828fe162 and percolate f3c9191a. Only Q2, both arms, three runs each, $0.46.
Runs are in `runs/2026-11-08-history-wave/`.

| arm | recall | calls (range) | turns | cost |
|---|---|---|---|---|
| baseline | 1.00 | 5.0 (4-6) | 6.7 | $0.073 |
| P8QL, wave of five | 1.00 | 4.0 (2-7) | 6.0 | $0.079 |
| P8QL in round 3, wave of one | 1.00 | 9.7 (7-13) | 8.7 | $0.085 |

**With a wave, the fuzzy lookup no longer costs P8QL extra turns.** It took 6.0 turns against
the baseline's 6.7, down from 8.7. The agent could see REM-1332 among the candidates instead
of rewording until it came first. Cost is still slightly higher ($0.079 against $0.073),
probably because each wave prints five labelled lines. Three runs per arm is directional.

## Round 3, 8 Nov 2026: Percolate's own history, three runs per question per arm

**Versions:** avalanche-db 4ed728b (midb 0.2.0). Store built by `history/build.sh` from
p8-subsystems 2ae637988 (1,331 board cards) and percolate f3c9191a (1,922 commits, 392 merged
pull requests): 35,144 facts, no dream. Same runner as round 2. 30 runs cost $1.98. Gold ids
were computed from git and the card files, not from midb, under the git adapter's two rules
(card ids from commit subjects only; at most 40 files per commit), and then checked against
the store. Questions are in `history/questions.jsonl`; raw runs are in
`runs/2026-11-08-history/`.

| q | tier | recall (both) | baseline calls | P8QL calls | baseline turns | P8QL turns | baseline cost | P8QL cost |
|---|---|---|---|---|---|---|---|---|
| Q1 | record select (REM-1332's PR) | 1.00 | 2.0 | 1.0 | 4.0 | 4.0 | $0.052 | $0.052 |
| Q2 | fuzzy lookup (a card by description) | 1.00 | 5.3 | 9.7 | 6.7 | 8.7 | $0.067 | $0.085 |
| Q3 | graph pattern (cards behind a file) | 1.00 | 4.0 | 3.0 | 5.0 | 6.0 | $0.061 | $0.062 |
| Q4 | graph pattern (cards sharing REM-254's files) | 1.00 | 14.0 | 2.0 | 7.0 | 5.0 | $0.075 | $0.058 |
| Q5 | graph pattern (top two by shared files) | 1.00 | 419.7 | 2.0 | 6.7 | 5.0 | $0.089 | $0.058 |
| mean | | 1.00 | 89.0 | 3.5 | 5.9 | 5.7 | $0.069 | $0.063 |

**Every run in both arms was right again. Counted in agent turns and cost, which is what the
work costs, the two arms are close: P8QL is cheaper on multi-hop patterns and dearer on
fuzzy lookup.**

- **Calls measured the wrong thing.** On Q5 the baseline made 420 `midb` calls in under seven
  turns. The agent wrote its own join as a shell loop over `midb edges`, one invocation per
  commit. Calls count invocations, not the agent's work, so rounds 1 and 2's "a fifth of the
  calls" overstated the difference. From this round, `score.py` prints turns and cost from
  each run's transcript, and those are the measure. Every run spends about four turns on
  fixed overhead (reading the prompt, writing the answer, replying), so Q1's 4.0 is the
  floor and the difference lies above it.
- **Above that floor, P8QL still wins on patterns.** Q4: 1 turn of work against 3. Q5: 1
  against 2.7, at two thirds of the cost and less than half the time (14 s against 35 s).
  The same reading of round 2's billing runs gives 1.0-1.3 work turns against 3.3-4.0 on the
  two pattern questions, at a fifth less cost.
- **P8QL loses the fuzzy lookup, and the reason is in the design.** `LIKE` carries only its top
  candidate forward. When the top candidate is wrong, the agent has to rephrase and try
  again: one run made 13 queries over eight wordings. `search` prints a ranked list, so the
  baseline agent could see REM-1332 lower down and go to it. The README now says a likeness
  step returns a wave of nodes. The current `LIKE` returns a wave of one.
- **The store is missing links, and neither arm can see that.** While computing gold answers
  from git, we found that the git adapter keeps at most 40 files per commit and drops the
  rest without saying so (src/construct/ingest.rs). It also reads card ids only from a
  commit's subject, not its body. For specs/workflow-engine/YAML.md, git names five cards;
  the store links three. Both arms agreed with the store, so recall here is recall against
  what was ingested. *Fixed in REM-1334:* the adapter now keeps every file and reads ids from
  commit bodies, so the store and git agree (20,751 touches each), and `history/questions.jsonl`
  carries the full gold (Q3: five cards, Q4: four).
- **Who-works-with questions have no answer on this history.** 1,860 of the 1,922 commits are
  authored by one git identity, and card owners are not ingested. So the history set has no
  person tier.

**What this does not show.** Nothing in this history has a typed reason (no dream ran, which
needs model credit), so the iterated "why" tier is absent. Both arms reached recall 1.00
again, so accuracy did not separate them on these questions either.

## Round 2, 8 Nov 2026: three runs per question per arm

**Versions:** avalanche-db 17dd4d3 (midb 0.2.0), billing example with Bob and Chen, reworded Q1.
Runner: `evals/p8ql/run.sh`, headless `claude -p` with Sonnet at low effort, Bash only, no MCP
servers, a fresh store per run. Round 1 used subagents, so compare arms within this round, not
with round 1. 30 runs cost $1.85. Raw answers, call logs and agent transcripts are in
`runs/2026-11-08-r2/`.

| q | tier | baseline recall | P8QL recall | baseline calls (range) | P8QL calls (range) |
|---|---|---|---|---|---|
| Q1 | record select | 1.00 | 1.00 | 1.0 (1-1) | 1.0 (1-1) |
| Q2 | fuzzy lookup ("Bobby") | 1.00 | 1.00 | 5.7 (5-6) | 3.0 (3-3) |
| Q3 | graph pattern (who works with Bob) | 1.00 | 1.00 | 11.7 (11-12) | 2.3 (2-3) |
| Q4 | graph pattern (issues fixed in Chen's files) | 1.00 | 1.00 | 11.3 (9-13) | 2.3 (2-3) |
| Q5 | iterated (why a cent off) | 1.00 | 1.00 | 1.0 (1-1) | 3.0 (1-4) |
| mean | | 1.00 | 1.00 | 6.1 | 2.3 |

**Round 1's pattern held across replicates. Every run was right in both arms. P8QL used about
a fifth of the calls on graph patterns and half on the fuzzy lookup. On the open "why" it used
more.** *Correction from round 3:* calls count `midb` invocations, not the agent's work. In
turns the arms are 5.9 (baseline) and 5.0 (P8QL), and in cost $0.063 and $0.060 a question.
On the two pattern questions, P8QL took 1.0-1.3 turns of work against 3.3-4.0.

- **The pattern gap is wider than the run-to-run noise.** On Q3 and Q4 the baseline's
  fewest calls (11 and 9) are more than three times P8QL's most (3 and 3). Six runs per
  question are still a small number, but the ranges do not come close to overlapping.
- **Q5 confirms round 1's other finding.** The baseline answered with one `why` call in all
  three runs. One P8QL run (Q5-2) answered from its single `WALK FROM`. The other two
  followed the walk with record selects on BUG-12, SUP-88 and ADR-007, one of them after a
  second walk from SUP-88. The walk returned the answer each time. The agent re-read the
  records before trusting it, as in round 1. Whether the plan and trace printed above the
  tree cause this is still untested. A run with the trace moved below the tree, or hidden,
  would test it.
- **The reworded Q1 fixed the question defect.** All six runs named round.rs and P-3.

**What this does not show.** The example has ten commits, so every question is answerable
in both arms and recall cannot separate them. That needs a bigger history: next is the same
four tiers on Percolate's own history.

## Round 1, 8 Nov 2026: directional, one run per question

**Versions:** avalanche-db 32f555d (P8QL stages 1-3), billing example with Bob and Chen
(bda7b94). The agent was Claude Sonnet in both arms, with lower effort and the same prompt
apart from the command list. Raw answers and call logs are in `runs/2026-11-08/`.

| q | tier | baseline recall | P8QL recall | baseline calls | P8QL calls |
|---|---|---|---|---|---|
| Q1 | record select | 0.50 | 0.50 | 1 | 1 |
| Q2 | fuzzy lookup ("Bobby") | 1.00 | 1.00 | 7 | 3 |
| Q3 | graph pattern (who works with Bob) | 1.00 | 1.00 | 12 | 2 |
| Q4 | graph pattern (issues fixed in Chen's files) | 1.00 | 1.00 | 8 | 2 |
| Q5 | iterated (why a cent off) | 1.00 | 1.00 | 1 | 5 |
| mean | | 0.90 | 0.90 | 5.8 | 2.6 |

**Both arms reached the same answers. P8QL needed fewer calls on pattern questions, and
more on the open "why" question.**

- **Patterns fold into one statement.** For "who works with Bob?" the baseline agent ran
  `edges` twelve times, record by record: Bob, his commits, their files, those files'
  commits, and those commits' authors. The P8QL agent read the schema and wrote one
  statement over the `works_with` path. Q4 went the same way, 8 calls against 2.
- **Fuzzy lookup worked in both arms, but by different routes.** No person is named Bobby.
  The P8QL agent tried `person = 'Bobby'`, which was refused, then `LIKE 'Bobby'`, which
  matched Bob at 0.60. The baseline agent got there through `search` and `edges` on
  `person:Bob`. Both agents said in their answers that they had assumed Bobby meant Bob.
- **The native walk was not trusted on its own.** For Q5, the baseline's `why` answered in
  one call. The P8QL agent's `WALK FROM` returned the same tree, but the agent then ran a
  record select on four of its records before answering. P8QL's walk output prints the plan
  and trace above the tree, which may read as less final than `why`. That is a hypothesis,
  not tested.
- **Q1 is a defect in the question, not in either arm.** "What did ADR-007 decide about"
  was meant to be answered by the file it governs (`decides -> file:src/invoice/round.rs`).
  Both agents named the decision itself and P-3, and mentioned round.rs only in prose. The
  question now reads "Which file does decision ADR-007 govern". Round 1 used the old
  wording.

**What this does not show.** One run per question, on a ten-commit example, cannot separate
the arms on accuracy, and the call counts could swing from run to run. Keys scanned were not
compared. Next: replicates (three per question per arm), the reworded Q1, and the same tiers
on Percolate's own history, where a pattern touches hundreds of records rather than ten.

*Since 0.2.0 the CLI is `midb`; round 1 ran when it was still called `ava`, so the call logs say `ava`.*
