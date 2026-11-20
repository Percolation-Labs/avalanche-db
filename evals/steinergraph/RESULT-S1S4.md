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
| tree cost, mean | 8.71 nats | 7.48 nats |
| passages beyond seeds, mean | 2.09 (0.34 non-gold) | 2.09 (0.20 non-gold) |
| dearest hop, mean | 5.05 nats | 4.48 nats |
| coverage (share of the tree read) | .182 (25/88 read any) | .419 (48/85) |

The graph-only reference (UNI, F = 1) gives the same picture: MuSiQue coverage .171, cards .362.

*These numbers are from the corrected solver.* The first version rooted the whole tree at one seed. james caught it
(M-20261120-172926-b110): on 2hop__135822_46621 it cost 16.405 against his heuristic's 15.476. The fix adds a virtual
root with 0-cost links to every seed, and that case now gives 15.476. Means moved by 0.4 nats at most; no reading
changed.

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
     tree order: the 1.4–2.5-nat hop at step 1, and the gold behind it at step 2. It stalls at the 3.3–5.1-nat hops.
   - On cards REM-1001, the tree's first hop out of the seed costs 4.2–5.0 nats, and the walk never enters.
3. **The entry hop decides it** (a $0 diagnostic, *not registered*).
   - Whether the walk reads any of T\* is best predicted by T\*'s cheapest hop. AUC of "not covered" over "covered":

     | | cheapest hop | dearest hop | total cost |
     |---|---|---|---|
     | MuSiQue, walk as used | **.886** | .730 | .567 |
     | MuSiQue, graph only | **.894** | .628 | .545 |
     | cards, walk as used | **.854** | .783 | .680 |
     | cards, graph only | .732 | **.741** | .627 |

   - Covered trees have a cheapest hop of about 1.7–2.5 nats (p ≈ .08–.18), and uncovered ones 3.5–4.4 nats
     (p ≈ .01–.03).
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
- **A third bug, a definitional one, caught by james:** the solver didn't implement the registered contracted root.
  An exact solver is only exact for the definition it implements; comparing it against a second implementation found
  it.
- **Two bugs caught on the first run, before any result was written:**
  - the ball was undercounted, because of an EPS in the distances (a strict ≤ on 2 + 2e-9);
  - a door shared by m passages was turned into m(m−1)/2 edges, not a star.
  - Both were found because the first output looked wrong (focus 0 everywhere, 16 edges on 7 passages). Neither
    changed the cases' verdict.
- **S4 confounded search with walks.** I registered "an edge shows when both ends are in a walk's set", which counts
  seeds. The labelled deviation separates the two, and the deviation is the honest number.
- **Memory.** The first cards rerun needed about 6.5 GB, from five copies of a 16M-link matrix. Run
  alongside james's S2c, it pushed macOS swap to 12 GB and the disk to 10 GB free, and I stopped it. The fixed solver keeps one copy (peak 2.7 GB), and I now run one large-memory job at a time.
- **Scope.** Dev only and directional. The 4 cases were fixed by rule. The entry-hop finding is unregistered. It holds on
  both dev sets, but needs registering on test before it carries weight.
