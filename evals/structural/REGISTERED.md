# Which structural properties predict a cheap Steiner walk: registered before any run

*Registered 18 Nov 2026 by bill. Sirsh's M-20261118-200827-fd14 says dreaming is only structural: edges with their
attributes, and hubs. It asks which structural properties, spectral and otherwise, predict a cheap Steiner walk.
Split with james (M-20261118-200923-3d3e): bill the properties, james the operator that moves the graph toward them.
james's D0 (#29) found no headroom in which sentence a door shows. His #31 and #32 found that learning door by door
doesn't transfer, so what dreaming learns has to be a property of structure. $0 and question-free: every property
is computed from the graph and what has been read, never from the question or the gold. Nothing is fitted.*

## Properties, per door at a recorded wave (read set R = the reads before that wave)

1. **width**: the door's unread targets.
2. **cohesion**: of the door's unread targets (the first 30 in id order), the share of pairs linked by some other
   door. Are the targets a cluster or a scatter?
3. **convergence**: the number of read passages other than the door's source that link (through any door) to at
   least one of its targets. Do several fragments already read point at the same place?
4. **local spectral mass**: personalized PageRank from R over the passage graph. A step from a passage picks one of
   its doors uniformly, then one of that door's other members uniformly; α = .15, push to residual 1e-5. The mass is
   summed over the door's unread targets, and also reported as a mean per target. PPR is the local spectral
   quantity: its sweep cuts bound conductance (Andersen, Chung and Lang 2006).

## Per question

- **PPR from the seeds:** the mass on gold, and the best gold's rank among unread passages.
- **Controls:** 5 random seeds, and links shuffled at the same widths (seed 1118, as in evals/structure).
- **Prediction:** Spearman with the walk's gain over search, and with (b) per question.

## Measures

- **Within-batch AUC** for separating gold doors (unread gold behind them) from gold-free ones, pooled over every
  pair in a batch, for each property, for Jev's P, and for search order. For width the direction is stated, never
  chosen: narrower counts as more likely gold, by the structure study.
- **Jev's errors:** the pairs where Jev ranks a gold-free door above a gold one. The share that each property orders
  correctly is what structure could add to what Jev already sees.
- **Shuffled-link control** for 2–4: the same properties on the target-shuffled graph.

## Selection and confirmation

- Dev traces (cards 100, PR titles 65, MuSiQue 101) to look.
- Test traces (cards 150, PR titles 93, MuSiQue 150; replayed from decisions.jsonl at $0) to confirm. A property
  counts as a structural predictor only if, on the test traces of all three corpora, its AUC is ≥ .60 and it orders
  ≥ 55% of Jev's errors correctly.
- A property that passes is the target for james's dreaming operator. Whether dreaming can move it, and whether that
  closes (b) on held-out questions, is james's registration.
