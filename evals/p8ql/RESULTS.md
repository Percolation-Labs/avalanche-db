# P8QL agent eval: results

## Round 9, 9 Nov 2026: a durable walk handed between two agents

**Versions:** avalanche-db 18a2c74, then e6b0d20, then this round's change. The round 8 history
store. Question: W1 (why every train measures memory retrieval; gold REM-1312, REM-1145).
Harness: `durable/run.sh`. In a handoff, agent A runs `ask` and exactly two `step`s, writes
the token, and stops without answering. Agent B gets only the question and the token. In a
single run, one agent walks with `ask` and `step` from the start. Both use the baseline
commands. 18 agent runs, $1.87.

| what `step` showed B | B resumed the token | B's calls after A | B right | single agent's calls |
|---|---|---|---|---|
| the record it reached (before) | 3 of 3 | 10, 8, 10 | 2 of 3 | 4, 4, 4 |
| plus `reached by:` as a line of ids | 3 of 3 | 6, 7, 8 | 3 of 3 | 4, 4, 4 |
| plus `reached by:` one record per line, with labels | 3 of 3 | 2, 3, 5 | 3 of 3 | 5, 4, 4 |

**The token is durable: every second agent resumed the walk where the first left it, and
none started over. What wasn't durable was the context.** B landed on REM-1145 with no way
to see that the walk had come from REM-1327 by way of REM-1312. So B rebuilt the path with
`edges` and `search`, and one B settled on the wrong cause (REM-1315).

- **The mechanism is that a step showed where the walk was, not how it got there.** The
  session holds the path (each visited frame keeps its parent and link). It just wasn't printed.
- **Now every step prints `reached by:`**: one line per record from the start, each with
  the link that reached it, its `dreamed, not stated` mark, and the record's label. With ids
  alone, B still looked each record up. With labels, B confirmed one or two links and answered.
- **A handoff now costs about what the work costs.** A spent 3 calls and B about 3, against
  4 for one agent alone. The second agent pays for confirmation, not reconstruction.
- **This is one question with a three-step path.** A longer walk prints a longer `reached by`,
  which is capped at 20 records. Whether a reader skims a long path or re-checks it is untested.

## Round 8b, 9 Nov 2026: the prompt decides the first call

The P8QL arm's prompt described `WALK FROM` as being "for open-ended 'why' questions", so on
C1 ("which PRs fixed the problem behind…") no agent walked. The variant says "for any question
that follows reasons or a chain of work (why X, what led to X, what was done about the cause
of X): one walk prints the chain with its links, so it often answers alone". P8QL arm only,
3 runs per question, $0.42; runs are in `runs/2026-11-09-history-chain-b/`.

| q | turns before | turns with the new wording | opened with WALK FROM |
|---|---|---|---|
| C1 | 8.3 | 5.0 | 3 of 3 (was 0 of 3) |
| C2 | 6.3 | 6.0 | 0 of 3 |

All 6 runs were right. On C1 the walk printed REM-1327, REM-1312 and its PRs, and each agent
made one record select to confirm #376 before answering. C2's agents still went straight to the
two cards, which takes three calls, so a walk would save little there. **The wording is now
the default:** it is in every P8QL eval prompt and in the `p8ql_run` MCP description, which is
what a real agent reads. That description also had the old pause text, which predated rounds
3b and 4; it now describes the wave, `WAVE n`, and the `dreamed, not stated` mark. Rounds
before 8b used the older wording, which git history keeps.

**Regression check:** round 5's three "why" questions, rerun on the round 8 store with the new
prompts (18 runs, `runs/2026-11-09-history-why-r8/`): recall 1.00 in both arms (it was 0.89
for the baseline and 1.00 for P8QL); turns 4.8 and 4.9 (was 4.3 and 4.7). Precision is
still low for the reason round 5 gave: agents include the question's own subject card.

## Round 8, 9 Nov 2026: chained questions, and the dream's commit-to-card question

**Versions:** avalanche-db 700b222 plus this round's change. History store with November
dreamed on the stand-in, with round 7's card wording. Two questions (`history-chain/`)
chain a reason to its changes: which PRs fixed the problem behind REM-1327 (REM-1312: #376,
#378), and which PRs carried out the card behind REM-1319 (REM-1316: #381, #386, #392). Gold
is from gh branch names and titles. 24 runs, $1.80; the dream itself billed $0.

**First run: 0.89 recall in both arms, and the misses came from the store.** The dream had
linked only #378 to REM-1312 and only #392 to REM-1316. Agents that fell back from `implements`
to `mentions` recovered the rest. One baseline run trusted `implements` alone and returned only
#392. One P8QL run stopped at REM-1319 and listed its PRs, not REM-1316's. The question's
wording ("the card that made it matter") is partly to blame for that one.

**Scoring the dream's commit and PR links against git** (`history-chain/truth.py`: a commit
whose subject names a card, or a PR or PR merge whose branch or title does): 79 `implements`
written, precision 0.87, recall 0.68. The misses were plain work for a card: b12db8cf fixes
REM-1316's bug, 81e8ac02 is REM-1314's fix, and #376 is half of REM-1312's fix. The commit-to-card
option read "a change that carries out {target}". A card is often a bug, and fixing one does
not read as carrying it out, so the stand-in chose "only mentions".

**The change:** for a commit or PR naming a card, `implements` now reads "a change made for
{target}, in whole or in part: it builds what the card asks for, fixes the problem it reports,
or does a step of its work". Decisions keep the old wording.

| dream | implements written | precision | recall |
|---|---|---|---|
| round 7 wording | 79 | 0.87 | 0.68 |
| round 8 wording | 93 | 0.89 | 0.81 |

The ten links the rule still counts as wrong are the same in both, and all ten are judgement
calls: REM-542's "opened after" version bumps, a budget fold that names REM-1143 in its body,
and a merge between two branches of the same card. The 19 left missed are mostly REM-1309's
research steps and regenerated-SQL commits. #376 is still missed.

**Second run on the new store: 12 of 12 right in both arms.** REM-1316's three PRs are now all
linked. **But P8QL took more turns on C1** (8.3 against 4.7). Its agents read records one by one
(REM-1327, REM-1312, REM-1310, then PRs) and never used `WALK FROM`, while the baseline's `why`
printed the chain and the PRs in one call. The P8QL prompt offers `WALK FROM` for open "why"
questions, and C1 is phrased "which PRs", so this is round 4's finding again: the first call
decides the cost, and the prompt decides the first call.

## Round 7, 9 Nov 2026: the dream question that let scope read as a reason

**Versions:** avalanche-db 96fd024 plus this round's change. The same November dream as
round 5, repeated on a fresh copy of the history store with the Claude stand-in. Round 5's
recordings were copied in, so only the 33 changed card requests were asked again. Cost: $0
billed.

**The change.** For a card naming another card, the dream's alternative to `because` used to
read "names {target} but none of the above holds". Now it lists what a card does with another
card when that card is not a reason: "to put it out of scope, as related or later work, or as
something it depends on or waits for".

| because links | round 5 (old wording) | round 7 (new wording) |
|---|---|---|
| written | 11 | 9 |
| right (checked against both cards) | 5 | 9 |
| wrong: scope or relation read as a reason | 4 | 0 |
| a dependency read as a reason | 2 | 0 |

**Every link is now right. The five right links survive, and every wrong link and
dependency drops below the cut.** Four new links appear, and all four are right: REM-1334 and
REM-1335 because REM-1331 (both filed from this eval), REM-1308 because REM-1307 (its audit
found the gap), and REM-1328 because REM-1323 (found during REM-1323's work). Round 5 had
that last pair the wrong way round, as REM-1323 because REM-1328.

- **The mechanism was a missing option.** The model had to choose between "a reason" and "none
  of the above", and a card that names another card in a Scope line reads as a vague kind of
  reason. Named alternatives give a scope note somewhere to go, and the wrong links fall to
  0.50-0.60.
- **The stand-in still answers at 0.80 when it is unsure.** Five of the nine links sit at
  exactly 0.80, the cut, and all five are right this time. The 0.80 bucket is not a signal of
  error by itself; the wrong links in round 5 were wrong because of the question.
- **This is one dream of one month, checked by one reader** (me, against the card text). The
  wording also goes to Jev when credit returns. Whether Jev's card links change, and in which
  direction, is unmeasured.
- Round 6's question has no wrong link to repeat in this store. REM-1302 now has no `because`
  at all, which is the truth as far as the store can tell.

## Round 6, 9 Nov 2026: a wrong dreamed link, and whether agents can tell

**Versions:** avalanche-db 3c7db37 plus this round's change. The store from round 5. One
question (`history-wrong/`): why was REM-1302 filed? The store's only reason is a wrong
stand-in link, REM-1302 because REM-1296. The card names REM-1296 only to put it out of
scope. The real reason, a user's feedback, is not in the store. 15 runs, $0.90.

| what the output showed | baseline: stated as plain fact | P8QL: stated as plain fact |
|---|---|---|
| no mark | 3 of 3 | 3 of 3 |
| tree `(dreamed)`; record select `dreamed, not stated` | 2 of 3 | 0 of 3 |
| tree `(dreamed, not stated)` | 0 of 3 | not rerun |

**Without a mark, every agent repeated the wrong link as fact. With an explicit mark, every
agent said the link was the dream's judgement, not the source's.**

- **The mechanism is that nothing told a guess from a fact.** The store keeps dreamed links in
  graph `dream`, but neither `why`'s tree nor a record select printed that, and agents cannot
  read card bodies through midb. So a 0.80 guess read exactly like a stated link.
- **Now the walk tree and P8QL's record select mark every dreamed link.** The tree prints
  `because (dreamed, not stated)`, and record select prints `dreamed, not stated`. The README's
  flagship tree shows it.
- **The wording mattered.** `(dreamed)` alone moved one baseline agent out of three; the
  baseline agents had also seen `[dream; T3]` in `edges` without reacting. `dreamed, not
  stated` says what it means, and every agent shown it reported it.
- **Every agent still named REM-1296.** A mark makes a guess visible; it can't supply the
  right answer, which isn't in the store. The fixes are upstream: a dream that does not read a
  scope sentence as a reason (round 5: all four wrong links), and ingesting the evidence a card
  cites. The question also forces a name, so a hedge is the best a reader can do here.

## Round 5, 9 Nov 2026: "why" questions on Percolate's history, after a dream

**Versions:** avalanche-db a6d0459. The history store (REM-1334 ingest) was dreamed for
November with the Claude stand-in (`provider = "claude"`), because Jev returned 402 (no
credit). The dream took 147 calls and wrote 83 links (72 implements, 11 because), and billed
nothing. The question set is `history-why/` with 3 questions x 2 arms x 3 runs, $1.06; runs are in
`runs/2026-11-09-history-why/`.

**The stand-in's links, read one by one.** Of the 11 `because` links, 5 are right: REM-1280
because REM-1275, REM-1311 because REM-1240, REM-1312 because REM-1145 (the Mem0 drop and its
cause), REM-1319 because REM-1316, and REM-1327 because REM-1312. Four are wrong: REM-1283
and REM-1302 name other cards only to put them out of scope, and REM-1323 merely relates
to REM-1328. The last two (REM-1303 and REM-1304 on REM-1167) are dependencies, not causes.
**Every wrong link sits exactly at 0.80, the dream's cut.** The stand-in reports
probabilities in a few coarse values (0.55, 0.60, 0.72, 0.80, 0.88-0.96), and 0.80 is its
"plausible". Above 0.85, 3 of 5 links are right and the other 2 are the dependencies. A stage-0
check of 8 November's slice found all 8 links right; that slice had mostly `implements`.

| q | gold | baseline recall | P8QL recall | baseline turns | P8QL turns |
|---|---|---|---|---|---|
| W1 why trains measure memory retrieval | REM-1312, REM-1145 | 0.67 | 1.00 | 5.0 | 4.7 |
| W2 why worker-path step time matters | REM-1316 | 1.00 | 1.00 | 4.0 | 4.0 |
| W3 why agents post observations | REM-1275 | 1.00 | 1.00 | 4.0 | 5.3 |
| mean | | 0.89 | 1.00 | 4.3 | 4.7 |

**Durable walks work on real history. In both arms, the first walk put the whole chain on
screen: REM-1327 because REM-1312, because REM-1145.**

- **The recall gap is in what the agent named, not what it found.** Two of the three baseline
  W1 runs saw REM-1145 in the `why` tree. They described the cause from the fix commits
  listed under REM-1312 ("words half matches all words", "id tiebreak") and never named the
  card. The P8QL agents ran record selects on REM-1312 and REM-1145 after the walk, and named
  it every time. In the `why` tree, the nine `implemented by` lines under REM-1312 bury the
  one `because` line above them.
- **P8QL's extra turns are those record selects,** the same habit seen in round 4's free-choice
  runs. Here they paid off on W1 and cost a turn on W3.
- **Precision is low in both arms because of how the questions are worded.** The questions
  name their subject ("every release train", "agents post observations"), and agents include
  that subject card in their ids. The gold leaves it out. A question set that counts the
  subject as given, or asks only for the cause, would fix this.
- **None of the three gold chains passes through a wrong link,** by construction: each one
  was checked against the cards. A question whose walk crosses one of the four wrong
  `because` links is the next test, and it is the one that measures what a 0.80 stand-in costs.

## Round 4, 9 Nov 2026: why the P8QL agent re-checked a walk

**Versions:** avalanche-db 7f187f1 plus the changes this round makes. Billing example, Q5 only,
P8QL arm only. 50 runs, $2.97. Runs are in `runs/2026-11-09-*`.

Rounds 1 and 2 guessed that the plan and trace printed above a walk's tree made the walk
read as less final, so the agent re-checked its records. That guess was wrong, and so was
round 2's statement that "the walk returned the answer each time".

| experiment | runs | first call | calls | turns |
|---|---|---|---|---|
| trace above vs below, free choice | 4 + 4 | 0 of 4 vs 3 of 4 WALK FROM | 3.2 vs 1.0 | 5.8 vs 4.0 |
| trace above vs below, "use one native walk" | 5 + 5 | all WALK FROM | 1.0 vs 1.0 | 4.0 vs 4.0 |
| trace above vs below, "start with a native walk" | 6 + 6 | all WALK FROM | 1.0 vs 1.0 | 4.0 vs 4.0 |
| walk pauses on a near tie vs starts at the top | 6 + 6 | 1 vs 5 of 6 WALK FROM | 3.3 vs 1.5 | 5.7 vs 4.3 |

**Where the trace is printed makes no difference. When the walk runs, the agent trusts it:
in the 31 runs this round whose first call was a walk, all 31 answered from it in one call.**

- **The mechanism is a pause, not the trace.** Replaying round 2's statements shows that in
  the two runs that went on to look records up, the walk never ran. Its likeness step found
  BUG-12 at 1.00 and a spreadsheet-export commit at 0.96, inside the 0.1 tie margin, so the
  query paused and listed candidates. The agent then did the sensible thing and read the
  records one by one. In both cases the top candidate was the right start.
- **So a walk no longer pauses.** `WALK FROM` now starts at the top candidate and names the
  next three in its trace, so a wrong start is one re-run away. A bare `LIKE` before hops still
  pauses, where carrying the wrong start would silently change every row.
- **The first trace experiment was confounded.** The two variants differed in which tool the
  agent reached for first, which it decides before seeing any output. The trace order
  only changes `WALK FROM` output, so that batch measured strategy choice. The two
  controlled experiments fix the first call and find no difference at all.
- **The pause A/B didn't measure the pause either, for the same reason.** Five of the six
  old-binary runs opened with a bare `LIKE` and record selects (2 to 5 calls). Five of the six
  new-binary runs opened with `WALK FROM` (1 call). An agent picks its opening before it sees
  any output, so the split is chance between batches. The case for removing the pause rests on
  the replay above, not on this A/B.
- **The first call decides the cost.** Opening with a bare `LIKE` and reading records costs 2 to
  5 calls. Opening with `WALK FROM` costs 1. Nothing in midb's output can change that choice,
  because the choice comes before any output. Only the prompt or the tool descriptions can.
- **Every run carries one turn of hook noise.** Each run loads the user's Claude Code
  settings, whose Stop hook asks the session to register on the board, and the agent
  spends its last turn declining. It is the same in every arm and variant, so it inflates the
  four-turn floor without biasing comparisons. A run without user settings was refused by
  the permission system, so the floor stays as it is.

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
  records before trusting it, as in round 1. *Correction from round 4:* in the other two runs the walk
  paused on a near tie at its likeness step and never ran; the record selects were the agent
  working around the pause, not distrust of a walk. Whether the plan and trace printed above the
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
