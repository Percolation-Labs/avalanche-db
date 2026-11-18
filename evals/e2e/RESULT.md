# End to end: results

This file follows [REGISTERED.md](REGISTERED.md), which was merged as #8 before any full score.

## G0 and G1, at $0 (17 Nov 2026, bill)

**Setup.**
- Both stores were built by `midb ingest` through the `documents` adapter (#6, #7, #9).
- `probe/` reads them through the library:
  - search ranks every passage by full-text BM25;
  - G0 raises the doors of search's top 3 and labels them with D6;
  - the walks no model decides (oracle, width-only, coin, search-order) run `lab::run` with 3 seeds, waves of 10,
    and no search filler after the seeds. Each is cut at its first 20 reads.
- `score0.py` scores the rows; the full output is in `score0.txt`. No model was called.
- A 5-question smoke run of the probe came before the full run, after the registration was pushed.

| | A: MuSiQue, 150 questions | B: p8-subsystems, 150 cards |
|---|---|---|
| Doors per question, from 3 seeds | 73 | 40 |
| **G0**, AUC of question–door overlap, gold door vs the rest | **.738** (needs ≥ .55) | **.707** |
| G0, AUC of width | .575 | .612 |
| search recall@10 | .464 | .291 |
| **G1**, oracle − search, recall@10 | **+.139 [+.092, +.186]** | **+.147 [+.078, +.218]** |
| width-only − search | −.110 [−.143, −.078] | −.197 [−.251, −.147] |
| coin − search | −.092 [−.127, −.057] | −.143 [−.196, −.095] |
| search-order − search | −.054 [−.088, −.022] | −.106 [−.155, −.059] |
| full support @10, search / oracle | .140 / .387 | .187 / .327 |

**Both gates pass on both corpora.** The graph this ingester builds carries the answer, and its D6 doors say which
door leads to it. On MuSiQue the overlap AUC is higher than the lab graph's .569, though the ingester and the door
both differ from the lab's, so the two are not a controlled comparison.

**Every walk that doesn't read its doors loses to search at the same budget.** This is the bar the Jev walk faces.
A walk's reads after the three seeds go through doors, so it gives up search's ranks 4–10. Search's ranks 4–10 are
good: on A, recall rises from .409 at 5 to .464 at 10. A decider must pick doors well enough to make up that loss
before it can gain.

## Postmortem

**Where the oracle's gain comes from.** On A the oracle finds 69 gold passages that search's top 10 misses, and 58 of
them are not in search's top 20 at all. It loses 23 that search's top 10 held. On B it finds 54 and loses 23, and
43 of the 54 are beyond search's top 20. The walk's value is reaching documents search doesn't rank, not reordering
search's own list. The hop from a card to the commits that name its id (term door `rem NNNN`) is exactly that.

**What it means for the walk under test.** Width-only is below coin on both corpora. On these graphs, wide doors are
the worst bet, the opposite of the lab's reference worlds, where width was a strong control. Search-order is the
best of the controls, so a ranking from the question's words alone already closes half the gap. Jev has to beat
search-order to show it reads the text. The registered W2 compares the walk with width-only, and search-order is
reported beside it.

**A design question for the walk, not settled here.** The oracle's 23 losses per corpus are search's own reads that
the walk gave up. A walk that keeps more of search's list, through more seeds or search reads in each wave, raises
the floor and may lower the ceiling. That is james's call for the walk. Any change is chosen on questions outside
these 300, because REGISTERED.md fixes the questions.

**Product findings on the way.** Each was fixed and merged, with a test.
- Deep paths overflowed the 120-character stored pointer (#7).
- Full-text search on p8 took 240 s, because the reader ran one `git show` per commit (#9, now 10 s).
- A re-ingest rewrote every fact and never retracted any (#11).

Ingesting p8-subsystems whole takes 101 s and a 2.2 GB store. Size is the next thing to cut.

## The walk's seeds rule, chosen on dev slices (17 Nov, bill, $0)

**Question.** A caller asks for k documents. How many should come from search before the walk opens doors? With
james's first default of 10 seeds, a walk at k=10 returned exactly search's top 10, so W1 would have been 0 by
construction (M-20261117-191822-d81b).

**Dev slices.** None of these questions is among the registered 300:
- 101 MuSiQue questions: `rw_musique.questions`, seed 1119, excluding every used and registered qid
  (`dev/musique-dev.jsonl`);
- 100 of the 365 eligible cards not sampled for the test, seed 1119 (`dev/cards-dev.jsonl`).

**Setup.** The probe ran with the walk's own k-mode settings (`dev/kmode-configs.json`):
- one door a wave, k waves, search only as seeds, a stop at k reads;
- seeds varied.

Oracle and search-order walks, minus search, at the same k:

| k | seeds | oracle, MuSiQue | oracle, p8 | search-order, MuSiQue | search-order, p8 |
|---|---|---|---|---|---|
| 5 | 2 | +.059 | +.100 | −.055 | −.111 |
| 5 | **3** | **+.090** | +.081 | −.018 | −.117 |
| 10 | 2 | +.134 | +.158 | −.055 | −.162 |
| 10 | 3 | +.157 | +.177 | −.014 | −.133 |
| 10 | **5** | **+.192** | **+.221** | −.020 | −.043 |
| 10 | 7 | +.158 | +.218 | −.007 | −.035 |
| 20 | 5 | +.205 | +.267 | −.058 | −.071 |
| 20 | **10** | **+.229** | **+.310** | −.035 | −.045 |
| 20 | 15 | +.208 | +.249 | −.011 | −.043 |

**Rule: seeds = ceil(k/2).**
- It has the highest ceiling at k=10 and k=20 on both corpora, with a floor near the best.
- At k=5, p8 prefers 2 seeds by .019, and the single rule is kept.
- An earlier sweep tried capping reads per door at 3, reading inside the door in the graph's order. The cap lowered
  the oracle at the chosen seeds on both corpora, so there is no cap. It also showed one door a wave matching or
  beating ranking all doors at once.
- james set the rule as the walk's default.

**What this changes for the registered run.** G0 and G1 above used the probe's first settings (3 seeds, waves of 10).
REGISTERED.md says every arm shares the walk's settings at the time of the run, so the control arms (oracle,
width-only, coin, search-order) are rerun on the registered 300 with the k-mode settings and this rule when the Jev
walk runs. G1 is checked again then.

**Parity.** `mcp_drive.py` drives `midb mcp` as Claude does (initialize, tools/call walk). With no key it read the
same documents in the same order as the probe's search-order walk on 4 of 5 dev questions. The fifth differed at
read 10, because that probe config filled with search after one door. The k-mode configs don't fill.

## The registered run: W1 and W2 (17 Nov, bill)

**Setup.**
- The walk arm is `mcp_drive.py` on main at 6f34275. It runs `midb mcp`, then `initialize`, then one `tools/call
  walk` per question and k.
- The walk's defaults: Jev 1.13.0, D6 doors with F2 keys, K6 as `found`, seeds = ceil(k/2), one door a wave.
- The control arms are the probe with the same settings (`run-configs.json`), on the same stores and the same 300
  questions.
- `score.py` scores both; the output is in `score.txt`.
- **Spend:** $0.997 on MuSiQue and $1.002 on p8. The p8 run stopped at the registered $1 cap after 103 of the 150
  questions at k=20, so that row is the 103 completed questions. k=5 and k=10 are complete on both.
- **Pilot:** 5 questions per corpus at k=10, $0.016, looked at only for price.

| recall@10, paired 95% CI | A: MuSiQue, 150 | B: p8-subsystems, 150 |
|---|---|---|
| search | .464 | .291 |
| **walk** (Jev, through MCP) | **.596** | **.323** |
| **W1**, walk − search | **+.132 [+.089, +.174], PASS** | **+.032 [−.025, +.088], FAIL** |
| **W2**, walk − width-only | **+.186 [+.148, +.227], PASS** | **+.139 [+.092, +.189], PASS** |
| walk − search-order | +.151 [+.112, +.192] | +.087 [+.033, +.141] |
| walk − coin | +.174 [+.136, +.213] | +.123 [+.074, +.175] |
| G1 again, oracle − search | +.187 [+.142, +.231] | +.246 [+.176, +.318] |
| full support @10, walk / search | .353 / .140 | .220 / .187 |
| last-hop gold @10, walk / search | .507 / .280 | – |
| k=5, walk − search | +.043 [+.007, +.079] | −.034 [−.082, +.015] |
| k=20, walk − search | +.120 [+.073, +.167] | +.129 [+.051, +.209] (n=103) |

**On MuSiQue the package does what the brief asks.** A question in, ten documents back: the walk returns the full
support for a question 2.5 times as often as search (.353 against .140), and it finds the last hop's paragraph, the
one search can't rank, 1.8 times as often. It gets about 70% of the way from search to the oracle (+.132 of +.187).
W2 passes, so the gain is Jev reading the doors, not the graph's shape.

**On p8-subsystems W1 fails at the primary budget.** The walk is above search, but the CI includes 0 at k=10. It
passes W2: Jev reads the doors better than any unread control. At k=20 it clears search, +.129 [+.051, +.209] on the
103 questions run. The package's claim on a real repository is therefore scoped: at 10 documents, no better than
search; at 20, better.

## Postmortem: why the repository walk gets 13% of its headroom

**Gains and losses.** At k=10 on p8 the walk finds 29 gold commits that search's top 10 misses, and gives up 25
that search's ranks 6–10 held. On MuSiQue the same counts are 59 and 13. The oracle's headroom on p8 is the largest
(+.246), so the doors lead to the answers. The walk doesn't take them.

**The id door is there and is rarely opened.**
- Search puts the card among the seeds on all 150 questions, because the question is its title.
- The term door `rem NNNN`, from the card to everything naming its id, was said here to exist for most cards. That
  was wrong (corrected 17 Nov, [REGISTERED-leads.md](REGISTERED-leads.md)): ingestion kept only four-digit numbers,
  so the door existed only for REM-1000 to REM-9999, about one card in six on the dev cards.
- Jev opened it on 6 of 150.

**Mechanism: the door's description doesn't show the commits.** Take REM-1044:
- Its id door has 14 targets.
- D6 shows the first snippet, then five leads ordered by how many names each target mentions.
- On a repository the passages naming the most are board logs, team logs and other cards' logs, so those are the
  leads.
- The commit that did the work (`train: a read leg ... (REM-1049)`, beside the gold) appears, but among them.
- Jev sees a door to board bookkeeping.
- On MuSiQue, naming many entities marks an informative paragraph. In a repository it marks a list.

**What this is and isn't.** It is a construction finding about D6's lead order on a repository, measured on one
repository and one question type (card title to the commits that name it). It doesn't show that walking a
repository can't beat search: the oracle shows it can, by +.246.

**Next, registered before any run:**
- A lead order that doesn't reward lists, such as fewest names first, or one lead per kind of passage (commit, file,
  note), chosen on the dev cards only.
- Then this test's B arm again, on the same 150 cards.

## Differences from the lab's measured setup

Each is carried with the claim:
- near is tf-idf, not embeddings, and a near door's head says "closest in wording" (james's question,
  M-20261117-195138-9ac1);
- names are rule-based, not spaCy;
- ties are sha-256, not md5.

D6's +.061 and K6's +.046 were measured in the lab. This run measures the package as shipped, not those parts
separately.

## Lead orders on a repository, dev cards (17 Nov, bill, $0.35)

This section follows [REGISTERED-leads.md](REGISTERED-leads.md) and its I1 amendment. All of it is on the 100 dev
cards, none of the test's 150.

**$0 step** (`leads/dollar0-*.txt`). On the I1 store, the id door with gold behind it is raised on 98 cards. On the
merged store it is raised on 15.

| on the I1 store | L0 (today) | L1, fewest names | L2, one per file |
|---|---|---|---|
| Shown, gold doors whose text shows a gold commit | .520 | **.678** | .648 |
| Shown, the id door | .459 | .755 | .816 |
| overlap AUC | .690 | .703 | .708 |

The kinds head changes neither measure, so it is kept. By the registered rule the pick is **L1k**: I1, fewest
names, kinds head.

**Jev step**, recall@10 at k=10 through MCP:

| | search | L0, merged store | L1k, I1 store |
|---|---|---|---|
| recall@10 | .340 | .380 | .345 |
| − search | | +.041 [−.016, +.097] | +.005 [−.067, +.079] |

- L1k − L0 is −.035 [−.099, +.029].
- The pick is not above L0, so under the registered rule it does not go forward and the test is not run.
- Spend: $0.19 and $0.15.

### Postmortem: the door is now taken, and it reads the wrong targets

**The description fix worked on the decision.**
- Jev opened the id door on 72 of 100 cards with L1k, against 6 of 100 with L0.

**What it read.**
- 343 reads went through it, and 12 were gold.
- 281 of the 343 were `board/cards/...`: the card's own other sections, and other cards naming the id.
- The walk reads an opened door's targets in sorted-id order (`Settings.within = "graph"`).
- `board/` sorts before `commit/`, so the commits come last, after the budget is spent.
- On this corpus, sorted-id order buries what the door is for.

**The loss also has a second side.** Opening the id door spends the wave's reads on it. Under L0 the walk opened other
term doors instead, and those found 29 gold, against 9 under L1k.

**Next, registered before any run.** The read order inside an opened door, from candidates that never see the
question:
- `postings`, fewest terms first, which the walk already has;
- `shown`, the door's own order: today's snippet, then its leads, then the rest in lead order. A door then reads what
  it showed.

The order is chosen at $0 on the dev cards, then a Jev dev slice runs against L0, then the test, as above. The
within-door order is james's walk, so it is agreed with him first.

## The read order inside a door, dev cards (17 Nov, bill, $0.005)

This section follows REGISTERED-leads.md, amendment 2.

**$0 step.** The k=10 settings on the I1 store with L1k doors, recall@10 (`leads/within-dollar0.txt`):

| within | oracle | search-order | search |
|---|---|---|---|
| graph (today) | .557 | .297 | .340 |
| postings | .666 | .307 | |
| **shown** | **.727** | .335 | |

The pick is **shown**.

**Jev step.** Recall@10 at k=10 through MCP, on the 100 dev cards:
- I1, L1k and shown together, called **L1kS**, score **.565**.
- That is +.225 [+.147, +.308] over search (.340), and +.185 [+.103, +.270] over the merged walk (L0, .380).
- The 100 walks made 597 requests. 579 were replayed from the cache, because wave 1 is identical to L1k's: the same
  seeds, door text and kappa. Only the read order inside the door changed.
- L1kS goes forward to the registered test.

## The registered test: the walk beats search on p8-subsystems at 10 documents (17 Nov, bill, $1.27)

**Setup.** As in the registered run above, with I1, L1kS and nothing else changed:
- the same 150 test cards and 150 MuSiQue questions;
- MCP, Jev 1.13.0, K6, F2 keys, seeds = ceil(k/2);
- fresh `midb ingest` of both stores with I1;
- the control arms rerun at $0 with the same settings, so W2 compares like with like.

Output: `leads/test/score.txt`.

**Spend.**
- p8: $1.00. k=10 and k=5 completed on all 150 cards; k=20 stopped at the $1 cap after 125 cards.
- MuSiQue: $0.27, k=10.

| recall@10, paired 95% CI | B: p8-subsystems, 150 | A: MuSiQue, 150 |
|---|---|---|
| search | .291 | .464 |
| walk, merged (first run) | .323 | .596 |
| **walk, I1 + L1kS** | **.477** | **.598** |
| **W1**, walk − search | **+.186 [+.118, +.253], PASS** | **+.134 [+.094, +.176], PASS** |
| W2, walk − width-only | +.289 [+.228, +.349], PASS | +.189 [+.150, +.229], PASS |
| walk − search-order | +.211 | +.151 |
| oracle − search | +.421 | +.201 |
| full support @10, walk / search | .307 / .187 | .353 / .140 |
| k=5, walk − search | +.034 [−.027, +.095] | not run |
| k=20, walk − search | +.374 [+.291, +.458] (n=125) | not run |

**The bar is met.**
- On our own repository, at the default 10 documents, the walk returns 64% more of the commits that did a card's work
  than search does.
- It returns all of them for 31% of cards, against 19% for search.
- MuSiQue is unchanged (+.134 against +.132), so the changes didn't buy the repository at the reference world's
  expense.

### Postmortem

**Where the gain comes from.**
- At k=10 Jev opened the card's id door on 98 of 150 cards. The merged walk opened it on 6.
- 68 gold commits came through that door, 18 through other term doors, and 55 from search's five seeds.
- Against search's top 10, the walk found 73 gold commits that search missed and gave up 18 that search's ranks 6–10
  held.

All three changes were needed, and each fixed the previous one's block:
1. **I1** made the door exist. Before it, the door was missing on five cards in six.
2. **L1k** made the door look like what it holds, so Jev took it: 6 → 72 of 100 on dev.
3. **Shown** made the door read what it showed, so taking it paid: dev recall .345 → .565.

**Why k=5 is a null.** At k=5 the walk has 3 seeds and 2 door reads. It gains 35 gold and gives up 26 from search's
ranks 4–5. Two reads are too few for the door to repay the search reads it costs. The claim is made at 10 and 20
documents, not at 5.

**Scope.** These go with every use of the number:
- This is one repository and one question type: a card's title, answered by the commits that name its id. The id
  door is the same relation that defines the gold. A repository whose issues are never named in commits gets no
  such door.
- The test shows that a walk reaches what a link in the text implies, which search can't rank. It doesn't show that
  every repository question gains.
- I1 and the kinds head are generic: any `ABC-123` id; commits and files exist in every git source. The lead order
  and `shown` were chosen on dev cards and checked on MuSiQue, where they were neutral.
- The walk now gets 65% of the oracle's gain (+.186 of +.421), against 13% before. The rest is the next headroom,
  measured with the oracle's door choice and the same read order.

**Where the walk's gain lies, by gold commit** ($0, from the test rows; james's suggestion). No card's title names an
id, by `cards.py`'s rule, so the test split is by wording instead: does a gold commit's message share words with the
card's title (score0.py's tokens, less the question frame)?

| gold commits, found in the top 10 | n | search | walk, merged | walk, this change |
|---|---|---|---|---|
| sharing two or more title words | 238 | .37 | .37 | **.48** |
| sharing at most one | 81 | .00 | .04 | **.33** |

- Search can't reach a commit whose wording differs from the question, and it found none of the 81.
- The walk reaches a third of them through the card's id.
- It also does better on the 238 commits search can match by wording. Why was not measured: either those commits
  are behind the same id door, or they ranked below search's top 10.

## Seeds at k=5 ($0, dev only; [REGISTERED-k5.md](REGISTERED-k5.md))

Oracle recall@k on the I1 stores, with L1k doors and `shown`:

| seeds at k=5 | 1 | 2 | **3 (ceil)** | 4 | | k=10: 4 / **5** | k=20: 9 / **10** |
|---|---|---|---|---|---|---|---|
| p8, 100 dev cards (search .245) | .445 | .437 | .382 | .372 | | .745 / .727 | .902 / .876 |
| MuSiQue, 101 dev questions (search .466) | .463 | .529 | .539 | .540 | | .671 / .677 | .799 / .783 |

**ceil(k/2) stays.** The one rule over k with fewer seeds at k=5 is ceil(k/2) − 1, which is floor(k/2) there. It
raises p8's k=5 ceiling (.382 → .437) and lowers MuSiQue's (.539 → .529), so it fails the registered rule, and no Jev
run was made.

**Postmortem: the corpora pull opposite ways at 5 documents.**
- On MuSiQue, search's ranks 1–3 are where the supporting paragraphs are. A seed given up costs more than a door
  read gains.
- On the repository, the gold commits are behind the card's id door. Search's ranks 3–5 rarely hold them, so each
  door read is worth more.
- A single rule can't serve both at k=5, and a rule chosen per corpus is what the registration rules out.
- So at 5 documents the walk equals search, and that is the claim.
- Not pursued: ceil(k/2) − 1 is within .01 or better at k=10 and k=20 on both corpora (p8 +.018 and +.026, MuSiQue
  −.006 and +.016). That is a different question from this registration's, and it would need its own registration.

## A second question type: pull-request titles, no id (18 Nov, bill, $0.74; [REGISTERED-prs.md](REGISTERED-prs.md))

**Setup.** The 93 test questions. A question is a merged PR's title, and the gold is the PR's own commits (2.86 per
question). The walk ran as merged, with nothing tuned on these questions: MCP, Jev 1.13.0, K6, D6/2, `within` `shown`,
seeds = ceil(k/2). The control arms ran at $0 with the same settings. Output: `prs/score.txt`.

| recall, paired 95% CI | k=5 | **k=10** | k=20 |
|---|---|---|---|
| search | .419 | **.514** | .616 |
| walk | .413 | **.472** | .586 |
| walk − search | −.006 [−.047, +.034] | **−.042 [−.082, −.001], W1 FAIL** | −.029 [−.073, +.015] |
| walk − width-only (W2) | +.041 | +.044 [+.013, +.078], PASS | +.064 |
| oracle − search | +.321 | +.345 (G1 PASS) | +.329 |

G1 also passed on the 65 dev questions (oracle .876, search .508 at k=10).

**The walk does not beat search on this type. At 10 documents it is slightly worse.** The claim in the README stays
scoped to the card questions: on questions whose answer is joined by an id, the walk beats search, and on PR-title
questions it does not.

### Postmortem

**What was measured.**
- Wording carries this type. 221 of the 266 gold commits share two or more title words with the question, and search
  returns 56% of those at k=10, against the walk's 51%. Of the 45 that share at most one word, both return 2%.
- Against search's top 10, the walk found 9 gold commits that search missed and gave up 19 that sat at search's ranks
  6–10. Every gold commit the walk found by a door came through a term door (13 commits) or a session-id door (1).
- PR merge commits carry the title verbatim. One was in search's top 5 on all 93 questions, so it used one of the
  walk's five seeds every time, and one of search's ten slots.
- Claude Code session ids in commit messages (`session_…`) are terms. On 18 of the 93 PRs, two or more gold commits
  share one, which makes that term door a branch-like link to the rest of the PR. Jev opened it on 1 of those 18.
- Walk − search-order is −.013 [−.051, +.024], so on PR titles Jev's door ranking is no better than ranking doors by
  search. With the oracle at +.345 over search, the gap is in the ranking.
- The headroom is real: the oracle gets .859. But search-order (.485) and coin (.438) are below search too, so on
  this type a door read is usually worth less than search's next rank. Jev beats width-only and coin, so it is
  choosing better than chance among doors that are mostly worse than search.

**Which doors hold the headroom ($0, the 65 dev questions, the probe now records `via`).**
- At k=10 the oracle's gold came from search (79), `next` doors (66), session-id term doors (15), other term doors (9)
  and `near` (1).
- A `next` door is the commits beside a read one in history. Its D6 head reads "N unread beside a read one, in the
  same file or history". A PR's commits sit next to each other and next to its merge commit, which is always a seed.
- The oracle used a `next` door to reach gold on 42 of the 65 dev questions. Jev opened a `next` door on 0 of the 93
  test walks at k=10.
- So this is a presentation and choice problem, not a graph problem: the door to the gold exists and is raised, and
  Jev never picks it.

**What would change it, none of it run.**
- A `next` door head that says what is behind it, e.g. "the commits just before and after commit X", so it doesn't
  read as bookkeeping. This is the first candidate, because the door already exists and the oracle uses it.
- A door for the merge commit's parents. The merge is always among the seeds, and its parents are the gold. It is
  the PR's own relation, as the id door was the card's, so a gain from it would need the same scope note.
- Showing the session door as what it is (commits from one working session) rather than as an opaque term.
- Any of these is a new registration, chosen on the 65 dev questions, with the 93 test questions run once.

## PR-title questions, round 2: N and M on dev (18 Nov, bill, $0.47; [REGISTERED-prs2.md](REGISTERED-prs2.md))

**Neither candidate clears the registered bar, so the test wasn't run.**

| 65 dev PR questions, k=10 | recall@10 | − B | walks that opened the door | Jev $ |
|---|---|---|---|---|
| B (as merged) | .507 | – | next 0 | .157 |
| N (next-door head names its commit) | .507 | .000 | next 1 | .078 |
| M (merge door) | .532 | +.025 | merge 1 | .150 |
| NM | .536 | +.029 | merge 1, next 1 | .080 |

The bar was +.03 over B. At $0 the oracle reached .962 on M's store (102 gold commits through merge doors, on 55 of
the 65 questions) against .876 on B's.

### Postmortem

**What was measured.**
- The merge door was raised and shown to Jev: a merge-door head appears in 124 of the stored M requests, and the
  N head in 70 of N's.
- Jev opened a merge door on 1 of 65 walks, and N's `next` door on 1. The oracle used a merge door to reach gold on
  55 of the 65.
- So a door that leads to the gold, named for what it is, is not enough for this decider on this page. The pages
  hold about 20 doors, mostly term doors whose snippets share words with the question.
- M's +.025 and NM's +.029 are within the dev slice's noise. They are reported, not claimed.

**Where the door is lost, partly measured.**
- Jev scored the merge door highest on 12 of the 124 pages that showed one, and in the top three on 48.
- Its mean score was .52 against a page's top score of .70.
- Yet merge doors were opened in 1 walk (4 reads). The walk opens the best-scored door among all doors still open,
  including those scored on earlier waves (`lab.rs`, `order: rank`). So a door that tops its own page can still lose
  to an older door scored higher.
- **Measured at $0** by replaying the 65 M dev walks from the stored requests, with all 65 replayed and none
  called, plus a temporary pick log that isn't committed. Older doors are not the cause:
  - 79 of the 80 picks with a merge door in the batch were in wave 1. The merge commit is a seed, so there was no
    older door to lose to.
  - The merge door was the top of its whole wave once, and that time it was opened.
  - Overall, 24 of the 113 picks went to a door from an older wave.
- So the door loses within its own wave. A wave's doors (about 200) are ranked over about 14 requests. A merge door
  that tops its own page of about 20 is usually beaten by the top of another page, and P from different pages isn't
  on one scale either.

**Why Jev passes the door over on the other pages was not measured.** The candidates registered change the door, not the decider. The
next question is a decider one: does Jev rank a door it is told holds the work of one merge over doors that share the
question's wording? That calls for a hand-picked look, a few pages read in-session (no batch Claude), before any
registration.

**What happens to the code.** Not merged. The candidates are kept as `prs/candidates-N-M.patch` against main at
`23dd6e3`. The defaults are unchanged.

## The merge door's text (H1), test (18 Nov, bill, $0.99; [REGISTERED-merge-text.md](REGISTERED-merge-text.md))

**Dev:**
- PR dev: .541 against B's .507 (+.034), with a merge door opened on 2 of 65 walks against M's 1. It passed both
  conditions, narrowly.
- Cards dev: .573 against .565, no harm.

Spend: dev $0.06; test $0.93 (k=10 $0.15, k=5 $0.22, k=20 $0.57).

| 93 PR test questions, M + H1 | k=5 | **k=10** | k=20 |
|---|---|---|---|
| search | .419 | **.514** | .616 |
| walk, as merged (first run) | .413 | .472 | .586 |
| **walk, M + H1** | .438 | **.502** | .635 |
| walk − search | +.018 [−.023, +.060] | **−.011 [−.053, +.030], W1 FAIL** | +.019 [−.040, +.081] |
| walk − width-only (W2) | +.066 | +.074, PASS | +.112 |
| oracle − search | +.433 | +.442 | +.372 |

**W1 fails. The walk is now level with search on PR titles rather than behind it** (−.042 → −.011 at k=10). Nothing
becomes a default.

**Scope, as james asked (M-20261118-095119-f878).** H1's head carries the branch name, which often paraphrases the PR
title.
- On the 38 test questions whose branch name shares two or more words with the question, walk − search is
  +.010 [−.060, +.080].
- On the other 55 it is −.026 [−.079, +.026].
- Neither half is a win.

### Postmortem

- **The gain is M's construction, not H1's text.** Merge doors were opened on 3 of the 93 test walks at k=10 (2 of 65
  on dev), so the head barely moved Jev's pick. The move from −.042 to −.011 comes with the merge store, which raises
  the oracle from .859 to .955 and the walk's controls with it (search-order .485 → .486, width .428 → .428).
  Credit for the change is M's, small as it is.
- **Calibration across kinds is unchanged.** A door that names its relation in plain words, "one pull request's
  work", is still scored below term doors that share the question's words, though it holds gold far more often. Text
  alone, question-blind, didn't move that.
- **What's left is not free.**
  - A per-kind weight is a dial fitted to data. On james's rule it must be judged on corpora and question types it
    wasn't fitted on: p8 cards, MuSiQue and PR test.
  - The other route is a decider that learns a kind's base rate, which Jev, scoring one door at a time, can't.
  - Neither is registered. The PR-title type is parked at parity with search, and the README's scope stands.
- The code isn't merged. It is kept as `prs/candidates-M-H1.patch`.
