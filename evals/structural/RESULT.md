# Which structural properties mark the gold door: local PageRank does, and on PR titles it beats Jev

*18 Nov 2026, bill. Registered first (REGISTERED.md, 2b11f78). $0: the k=10 dev and test walks replayed from
decisions.jsonl (test replays: 0 calls), and the probe's E2E_FEATURES mode. Nothing fitted; no default changes.*

## What was asked

Sirsh (M-20261118-200827-fd14): which structural properties predict a cheap Steiner walk, so dreaming, which is only
structural, has something to move the graph toward.

The question tested: for each door at each recorded wave, does a question-free property of the graph and the read set
tell the doors with gold behind them from those without? Four properties were registered: width, cohesion,
convergence, and personalized PageRank (PPR) mass from what has been read.

## Result on the held-out test traces (cards 150, PR titles 93, MuSiQue 150)

Within-batch AUC, gold doors against gold-free ones:

| property | cards | PR titles | MuSiQue | the bar: AUC ≥ .60 on all three, and ≥ 55% of Jev's errors ordered right |
|---|---|---|---|---|
| Jev's P | .862 | .688 | .902 | (reference) |
| search order | .800 | .672 | .770 | (reference) |
| narrow (−width) | .371 | .508 | .378 | fails |
| cohesion | .605 | .481 | .652 | fails |
| convergence | .758 | .566 | .665 | fails (PR) |
| **PPR mass, summed over the door's targets** | **.868** | **.724** | **.808** | **passes**: errors .706 / .571 / .722 |
| PPR mass, mean per target | .665 | .689 | .563 | fails (MuSiQue) |

Shuffled links, each door keeping its width: PPR summed .567 / .507 / .608. Dev agrees: .861 / .712 / .787.

**Per question, PPR from search's 5 seeds,** for questions with gold beyond the seeds: the best such gold ranks in
PPR's top 10 on 59/135 (cards), 55/87 (PR titles) and 37/131 (MuSiQue). It's in the top 100 on 130, 81 and 95. From 5
random seeds, or over shuffled links, it's in the top 10 on 0–1 questions per corpus.

## What it says

1. **The graph's own structure marks the gold door.** PPR mass from what has been read, a local spectral quantity,
   separates gold doors as well as Jev on cards (.868 against .862). It does better than Jev on PR titles (.724
   against .688), the corpus where the encoding gap is: Jev ranks a gold door first on only 21% of waves there
   (evals/steiner). Shuffled links at the same widths fall to chance. So the gold door is distinguishable by
   structure alone, without door text. That is what Sirsh's split predicts: the PR-title fault is in what the walk
   sees, not in the graph.
2. **The answer's region is a PPR neighbourhood of the seeds.** It's within the top 100 for most questions, and
   random seeds or shuffled links almost never reach it. That is a spectral reading of the Steiner claim in
   evals/steiner.

## The postmortem

- **The shuffled control can't separate structure from width for summed properties, and I registered it anyway.** On
  Jev's errors the gold door is usually wide: on MuSiQue dev, median width 44 for the gold door against 8 for the
  gold-free one. Summed mass grows with width even on random links. So on Jev's errors, shuffled PPR orders as many
  pairs right as real PPR (.693 / .580 / .739 against .706 / .571 / .722). **PPR passes the registered bar, but the
  part that fixes Jev's errors is width, not structure.**
- **The width-matched analysis (not registered; reported as such):** pairs within 2× width of each other. There, real
  PPR summed scores .802 / .733 / .826 against shuffled .538 / .498 / .520, and mean per target .783 / .725 / .808. So
  PPR carries structure beyond width. What it adds to Jev on Jev's own errors is not shown structural by this study.
- **The PPR push tolerance was changed from the registered 1e-5 to 1e-4 for speed,** before anything was scored
  (14 s → 1.7 s a question). Mass below 1e-4 isn't propagated, so a door's mass is a slight underestimate. The
  rankings are the claim, not the masses.
- **Process:** a wait loop with `pgrep -f "replay.py.*musique-questions"` came back empty, harmlessly this time. The
  pattern-wait lesson from evals/steiner applies. Wait on PIDs.

## For dreaming (james)

- **The target structure:** dreaming's added edges and hubs should raise a gold door's PPR mass from the read set
  above a gold-free door's of similar width. The width-matched AUC is the measure that isn't confounded.
- **The objective stays (a) and (b).** The width-matched PPR AUC is how to see whether a round of dreaming moved
  structure, rather than only width.
- **Not shown:** whether giving Jev PPR (as a door attribute) or the walk (as a pick term) would help. That is a
  separate registration. It would be the walk using structure, not dreaming writing it.

## Files

- `score.py`, `score.txt`;
- `out/f{d,t}-{cards,prs,mq}.jsonl.gz`: per door per wave, with real and shuffled properties, P, rank, search rank,
  width and gold;
- `out/*.questions.jsonl`: per-question PPR, with controls;
- `probe/src/features.rs`.
