# A door's width as budget spent: registered before any run

*Registered 18 Nov 2026 by bill. Sirsh's steer M-20261118-150956-f539 ("pick up the structural side, for example
counting a door's width as budget spent"), with M-20261118-103300-ceb0 (the floor is a property of the walk; no
door-kind weights, priors or corpus-tuned dials). The split with james (M-20261118-151109-4e7b,
M-20261118-151223-efab): james builds the likeness door, bill this. Stage 0 is $0.*

## Why

The structure study (evals/structure) found orthogonal gold behind narrow doors: median width 2 on PR titles, 13 on
cards, 19 on MuSiQue. james's floor study found that every losing k=10 walk is one door that took all 5 remaining
reads and returned no gold. Today's pick rule (`order: rank`) compares doors by Jev's P alone. A width-2 door and a
width-100 door with the same P look equal, though the first leaves 3 reads for another door and the second spends the
whole budget.

## The rule (fixed now; nothing is tuned)

`order: per_read`. A door's cost is the reads it would take from what is left of the budget,
`min(unread targets, k − reads so far)`. The walk opens the door with the highest `P / cost`. There is no parameter.
When every door is at least as wide as what is left, it is today's rule.

The reference rule is `per_target` (the V0 order, `P / unread targets`), already in lab.rs. It charges a door for
width beyond the budget, which the walk never reads, so it is expected to over-favour narrow doors. It is not a
candidate.

## Stage 0: replayed scores, $0, dev only

- **Data.** The k=10 dev walks (cards-dev 100, prs-dev 65, musique-dev 101), replayed from their stores'
  decisions.jsonl with `midb walk --trace`. Stores: e2e-p8i (cards, PRs) and e2e-mq3. Each door's recorded P is the
  P a re-run would get (#845: Jev scores each door on its own).
- **Simulation.** The probe's E2E_REPLAY mode re-runs each walk with the recorded P, under `rank`, `per_read` and
  `per_target`, in today's k=10 settings (seeds 5, one door a wave, within shown, no search fill). A door no
  recorded batch scored is left unranked, so it is never opened. Each walk reports how many such doors it met
  (`unknown`), and the result states it. A counterfactual walk that leaves the recorded path can only use known
  doors, so stage 0 understates any rule that changes the path.
- **Validation.** The `rank` arm must reproduce the recorded walk's 10 documents on at least 95% of dev walks. If it
  doesn't, the simulation is wrong and nothing else is reported.
- **Measures.** Recall@10 per corpus for search's top 10, `rank` and `per_read` (and `per_target` for reference).
  Paired differences with a bootstrap 95% CI (10,000 resamples, seed 1118). The floor: the number of questions where
  each arm is below search. Read counts by door width.
- **Gate to stage 1.** `per_read` minus `rank` is at least −.01 on every corpus and at least +.02 on one, and its
  count of questions below search is no higher than `rank`'s on every corpus.

## Stage 1: live Jev, only if stage 0 passes

- Dev first, each corpus capped at $1, the same gate as stage 0.
- Then the held-out test sets: cards.jsonl 150, prs-test.jsonl 93, musique-questions.jsonl 150. Each is run once.
- **The bar** on each corpus:
  - W1, `per_read` − search at k=10, CI lower bound ≥ −.01 (the floor);
  - W2, `per_read` − today's walk (the registered test rows) ≥ 0, with its CI reported.
- This does not change a default. A default would need its own decision.

## With james's likeness door

The likeness door's width is the budget left, so under `per_read` its cost is the budget left: it is charged like
any door that wide, with no special case. If both are built, the two are tested crossed, 2×2, and reported in both
orders. Neither rule is credited with the other's gain.
