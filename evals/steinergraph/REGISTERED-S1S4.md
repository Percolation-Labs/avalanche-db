# S1 and S4 (registered before scoring): how the walk uses the gold Steiner tree, and when the tree emerges across seeds

*20 Nov 2026, bill, for Sirsh's 17:11 frame. james runs S2 (drift) and S3 (repair without the oracle). $0: no Jev, no
Claude, no new data.*

## The reference tree, T*

- **Graph:** L1's stored graph (dream/d1/graph-{mq,p8}.jsonl). Two passages are joined through a door (a key held by
  2–100 passages, the graph's stored limit) or a next/near link.
- **T\*:** the exact node-weighted Steiner tree. Each passage costs 1 and each key costs 0, so T\* is the fewest
  passages that connect every gold passage to the root. The root is the seed set (search's top 5) contracted to one
  node, so the tree may attach at any seed.
  - Computed by Dreyfus–Wagner, which is exact. The terminals are the root plus the gold passages in the graph, at most
    7 here.
  - Next to it: james's shortest-path tree (the union of shortest paths from the nearest seed to each gold passage),
    with the size gap between the two.
- Gold that isn't in the graph, or that the graph can't reach from the seeds, is reported as cut off. That's S2's
  natural drift case, and it is passed to james, not dropped.

## Cases (fixed by rule before looking)

The first dev question, in file order, of MuSiQue's 2hop, 3hop1 and 4hop1 types, and the first dev cards question
(card:REM-1001, with 6 gold passages). That makes 4 cases. Aggregates over all dev (MuSiQue 101, cards 100) are
secondary and are reported only after the cases are read.

## S1: how the walk uses T*

The walk is l1.G.run at L2's fitted θ ('LC': MuSiQue (−1, −1, .15), cards (−1, −1.5, .15)) with search scores as
F, as in K1. U (−1, 0, .15) is reported next to it. Reads at step i are the top 5 beyond the seeds of the no-restart
walk's mass at step i, for i = 1…25 (l1's ITERS). The avalanche read is the top 5 of P, which is what L1–L3 scored.

Measures, per case:

- **Coverage:** the share of T\*'s non-seed passages read at any step.
- **Focus:** the share of reads (the union over steps) that are on T\*.
- **Order:** for each T\* passage read, its first step against its depth from the root.
- **Departure:** the first step whose top 5 holds no T\* passage.
- **Reference:** focus compared with |T\*| / |the passages within T\*'s depth of the seeds|, which is what uniform
  reading of that ball would give.

## S4: when the tree emerges across seeds

- **Seed sets, from search:** the top k of search's 10, for k = 1, 2, 4 and 10 (reporting points, not tuned).
  "Pooled at k" means all walks from k = 1…k together.
- **Seed sets, control:** 3 random draws of 5 passages from the corpus (rng seed 0).
- **A T\* edge "shows"** when both of its passages are among one walk's reads (at any step).
- **Per point:** T\*-edge recall (the share of T\*'s edges that show), and precision (T\* edges shown, over all co-read
  pairs).
- **Emergence point:** the first k where every T\* edge shows.

The walk pool is written for james's S3 to `$S/steiner/pool-{set}.jsonl`: {qid, draw, seeds, reads: [[id, step]]}.

## What would count as directional

- **S1:** T\* is used if focus is above the ball reference on at least 3 of 4 cases. The walk follows T\* if, in
  addition, order rises with depth on those cases.
- **S4:** T\* emerges from search if search-seeded recall reaches 1 at some k on at least 3 of 4 cases, while the random
  draws stay below it.

No threshold here is a fitted or chosen tuning value. The 100 is the stored door limit, 5 and 10 are the stored search
lists, 25 is l1's ITERS, and θ is L2's fit.
