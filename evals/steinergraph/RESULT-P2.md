# P2: the Steiner graph is compact, but one step inside it rarely stays inside it; that, not distance, limits retrieval

*19 Nov 2026, bill. Registered first (REGISTERED-P2.md, 24ff5f5, amended 3d23042 before scoring to move percolation
to james). $0, no Jev, nothing fitted. Held-out test of P1/L1, on L1's graph (`p2.py` imports james's `l1.py` from
james/steiner-l1). Output: `p2.txt`; unregistered diagnostic `p2-diag.txt`; per-question rows `out/p2-*.jsonl`
(likeness, connection, recall against budget, oracle seed ids, and MuSiQue's seed sets), keyed on qid for james's
fixtures.*

**Verdict:**
- **Bar 1 (compactness) fails on all three sets.**
- **Bar 4 (blind decomposition) fails narrowly:** +.029 [−.004, +.066], against a bar of +.03 with the interval above 0.
- **Bar 3 shows the registered split was vacuous:** every question has a seed within one link of its gold.

## What the numbers say

| test | cards | PR titles | MuSiQue |
|---|---|---|---|
| **Likeness** | | | |
| questions with ≥1 seed in S (entry point) | 45/150 | 83/93 | 116/150 |
| questions with ≥1 seed within one link of S | 150/150 | 92/93 | 149/150 |
| gold in search's top 50 | 139/319 | 169/266 | 246/399 |
| **Connection** | | | |
| gold pairs directly linked (shuffled) | .946 (.013) | .901 (.018) | .789 (.030) |
| one uniform step from gold lands on other gold (shuffled) | .094 (.0001) | .139 (.0001) | .025 (.0002) |
| **Recall beyond the seeds, uniform avalanche** | | | |
| k = 1 / 5 / 20 reads | .096 / .207 / .508 | .140 / .380 / .674 | .055 / .122 / .269 |
| recorded Jev walk, 5 reads | .355 | .098 | .362 |

- **The Steiner graph is compact: in hops, and far beyond chance.**
  - 79–95% of gold pairs share a direct link, against 1–3% on shuffled links.
  - The mean link distance between gold passages is 1.05–1.22, against about 2.0 shuffled.
  - Distance can't separate questions, because nearly every question sits at 1. So the compactness test (bar 1)
    could not pass as registered: the thirds split at 1.00 against 1.00. Only on MuSiQue is there spread, and the
    direction is the one predicted: +.097 [−.027, +.223].
- **What limits connection is the step probability, not the distance.**
  - From a gold passage, one uniform step lands on another gold passage with probability .025–.139. The links are
    there, but each passage has about 325 of them on cards and PR titles and about 530 on MuSiQue, and wide doors dilute
    the step.
  - The ordering across corpora (PR titles .139, cards .094, MuSiQue .025) is the ordering of U's recall (.38, .21,
    .12).
  - Per question (diagnostic, not registered), the in-S step correlates with U's recall@5 at Spearman .22, .28 and
    .38 (p ≤ .04), and with the Jev walk on MuSiQue at .43.
  - This is what L1's learned weights move: they redistribute the step toward narrow doors and low-degree targets.
- **Likeness: "within one link" means nothing on a graph this dense. "In S" separates.**
  - Diagnostic, not registered. With at least one seed already gold, U's recall@5 roughly doubles: cards .175 →
    .317, PR titles .079 → .419, MuSiQue .071 → .140.
  - On MuSiQue the Jev walk also doubles, .216 → .412.
  - Cards is the corpus where likeness limits: only 45 of 150 questions have a seed in S. On PR titles (83/93) and
    MuSiQue (116/150), search usually lands on S.
- **Decomposition: most of the gain needs the answers.** MuSiQue, total recall at 10 reads (5 seeds plus U's top 5):

  | seeds | total recall | entry points |
  |---|---|---|
  | single question | .475 | 1.03 |
  | blind sub-questions | .504 (+.029 [−.004, +.066]) | 1.13 |
  | oracle (best 5 of search's top 50) | .520 (+.045 [+.022, +.071]) | 1.15 |
  | sub-questions filled with each hop's answer | .770 (+.295 [+.246, +.344]) | 1.81 |

  - Splitting the question without answering it barely moves the seeds, and even the best choice among search's top
    50 adds only .045.
  - The large gain, +.295, comes from substituting hop 1's answer into hop 2's sub-question. That is iterative
    retrieval: read, then search again. A decomposition helps once each sub-question is asked after the previous one
    is answered. That is a walk, and Jev reads during it.

## Which factor limits each corpus

- **Cards: likeness and connection both limit.**
  - Search seldom lands on gold: entry on 30% of questions.
  - Inside S the step is moderate (.094).
  - The Jev walk (.355) beats U (.207), because Jev reads meaning that search misses.
- **PR titles: connection, as a matter of choice.**
  - Search lands on S (entry on 89% of questions), and S is the most connected of the three (.139).
  - Structure alone (.380) beats Jev's walk (.098). Jev's door choice is the fault, as in P1 and evals/steiner (b).
- **MuSiQue: connection, at the step.**
  - Search usually lands (77% of questions), but one step from gold rarely stays on gold (.025): multi-hop gold is
    linked mostly through wide entity doors.
  - Jev's walk (.362) triples U (.122), so meaning is what carries the step there.

## Postmortem

- **Two registered measures saturated, as evals/steiner's share did on 18 Nov.**
  - On a graph with about 300 links per passage, "near" (one link) and pairwise distance put almost every question at
    the same value.
  - I registered hop-based compactness without checking its variance on dev. A minute on dev would have shown it.
  - Rule from here: check a measure's spread on dev before registering a bar on it.
  - The informative measures turned out to be the probabilistic ones (the in-S step) and exact entry (seed in S).
- **Bar 4's oracle is weak by construction.** Greedy cover within one link saturates too, since any seed covers most
  of S. A stronger oracle would maximise U's recall directly. The filled decomposition is the real upper bound.
- **What this buys a Jev run** (Sirsh's 12:34: say what each run should show):
  1. On MuSiQue, an iterative-decomposition walk: Jev picks the next sub-question's seed from what has been read. It
     should close part of the .295 gap.
  2. On PR titles, L1's learned weights as an option in Jev's batch (james's next).
  - Both are measurable on these rows: entry and in-S step before and after.
