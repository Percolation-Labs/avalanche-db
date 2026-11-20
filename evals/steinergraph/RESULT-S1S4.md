# S1/S4: the walk's misses are at its entry into the gold tree, and the tree doesn't emerge from walks

*20 Nov 2026, bill, for Sirsh's 17:11 frame.*

- *Registered first: REGISTERED-S1S4.md (74d6ffb), then the amendment REGISTERED-S1S4-amend.md (93d17bb).*
- *$0: no Jev, no Claude. Outputs: `s1.txt` and `s1p.txt` (the 4 cases), `s1-all.txt` and `s1p-all.txt` (all dev).*
- *james runs S2 (drift) and S3 (repair) against the same tree (`s1p.tree`).*

## Verdicts, by the registered rules

| | rule | MuSiQue (88 dev questions with gold beyond the seeds) | cards (85) | verdict |
|---|---|---|---|---|
| **S1, hop tree** | focus above the ball reference on 3 of 4 cases | 0 of 3 cases (the 2-hop case had nothing to connect) | 0 of 1 | **fail** |
| S1, hop tree (all dev) | | focus .022 against .0005; above it on 19/88 | .074 against .0018; above it on 39/85 | |
| **S4, hop tree** | every edge shown at some k on 3 of 4 cases, with random below | 1 of 3 (at k = 9, a search rank) | 0 of 1 | **fail** |
| S4 (all dev, k = 10) | | edge recall .44, all edges on 32/88 | .63, 47/85 | |
| S4, random ×3 | | .05 | .03 | |
| S4, edges whose far end a walk read *(labelled deviation)* | | 40/176 | 80/162 | |

**S1′, the most probable tree** (link cost −log one-step probability), all dev at LC θ with search F:

| | MuSiQue | cards |
|---|---|---|
| tree cost, mean | 8.95 nats | 7.51 nats |
| passages beyond seeds, mean | 2.12 (0.38 non-gold) | 2.08 (0.19 non-gold) |
| dearest hop, mean | 5.12 nats | 4.50 nats |
| coverage (share of the tree read) | .171 (22/88 read any) | .417 (47/85) |

The graph-only reference (UNI, F = 1) gives the same picture: MuSiQue coverage .164, cards .363.

## What it says

1. **Counting hops, the gold tree is trivial and the walk still misses it.**
   - T\* is about 2 passages beyond the seeds, usually one link from a seed. james's S2 found the same on test (90–99%
     of trees are the terminals alone).
   - But the ball within T\*'s depth holds 484 to 21,082 passages. The walk reads 5 of them a step, and on the 4
     cases it reads no tree passage at all, departing at step 1. On cards it reads neighbours that search scores
     higher (about .47) over the gold commits (.01–.18).
   - Hop count is saturated, as P2 found. What matters is the choice within a hop.
2. **Priced by the walk's own probabilities, the tree has a shape the walk follows or doesn't.**
   - On the MuSiQue 4-hop case, the most probable tree routes through 2 non-gold bridge passages. The walk reads them in
     tree order: the 1.4–2.5-nat hop at step 1, and the gold behind it at step 2. It stalls at the 3.7–5.1-nat hops.
   - On cards REM-1001, the tree's first hop out of the seed costs 4.2–5.0 nats, and the walk never enters.
3. **The entry hop decides it** (a $0 diagnostic, *not registered*, MuSiQue only).
   - Across the 88 trees, whether the walk reads any of T\* is predicted by T\*'s cheapest hop: AUC .875 at LC and .888
     at UNI. Covered trees have a cheapest hop of about 2 nats (p ≈ .10–.16), uncovered ones about 4 nats (p ≈ .015).
   - The dearest hop predicts less well (.75 and .61), and total cost hardly at all (.63 and .53).
   - Cards was stopped by the memory limit (postmortem) and is still to run.
   - **Reading:** with 5 reads a step, the walk gets onto the tree only where some hop is likely enough to make the
     top 5 of the walk's next step. A hop at about 1/50 doesn't.
4. **The tree doesn't emerge from walks across seeds.**
   - Pooling walks from search's top 1…10 shows T\*'s edges mostly because search ranks 6–10 hold gold: a seed is
     shown by definition.
   - Edges whose far end a walk actually read are 23% of MuSiQue's T\* edges and 49% of cards'.
   - So, for james's S3, walks co-read the tree's links too seldom to be the only source of repair candidates. S3's
     candidate check will say how seldom.

## For Sirsh's story

- **"We know what good looks like."** The most probable gold tree is computable exactly, about 2 passages beyond the
  seeds, in under a second on MuSiQue and about 5 s on cards.
- **"We can measure how far a graph is from it."** Its cost in nats, and especially its cheapest hop, is a gold-time
  measure of how readable it is.
- **"Drift."** james's S2c shows that cutting the key behind T\*'s cheapest gold edge moves the walk's rank on cards
  (382 → 1,257) and only slightly on MuSiQue.
- **"Repair."** S3 has to lower the tree's entry cost. S4 says walk co-reads alone seldom contain the missing link.

## Postmortem

- **The registered hop tree was the wrong reference, which P2 already implied.** P2 showed that hop reachability
  saturates on these graphs, and I registered a hop-count tree anyway. james's S2 hit the same wall from the other
  side. A $0 look at T\*'s size against its ball, which I printed on the first run, would have redirected this before
  registering. That makes five times now that data in hand predicted the outcome (P2, J3, J4, J5, S1).
- **Two bugs caught on the first run, before any result was written:**
  - the ball was undercounted, because of an EPS in the distances (a strict ≤ on 2 + 2e-9);
  - a door shared by m passages was turned into m(m−1)/2 edges, not a star.
  - Both were found because the first output looked wrong (focus 0 everywhere, 16 edges on 7 passages). Neither
    changed the cases' verdict.
- **S4 confounded search with walks.** I registered "an edge shows when both ends are in a walk's set", which counts
  seeds. The labelled deviation separates the two, and the deviation is the honest number.
- **Memory.** The cards half of the per-question rerun needs about 6.5 GB, from five copies of a 16M-link matrix. Run
  alongside james's S2c, it pushed macOS swap to 12 GB and the disk to 10 GB free, and I stopped it. Next time: one copy,
  built per question, and one large-memory job on the machine at a time.
- **Scope.** Dev only and directional. The 4 cases were fixed by rule. The entry-hop finding is unregistered, from one
  set, and needs registering on cards and on test before it carries weight.
