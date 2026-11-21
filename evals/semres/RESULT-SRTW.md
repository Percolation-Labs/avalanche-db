# SR-TW result: the relational null doesn't stop relational twins. FAIL

*21 Nov 2026, james. Registered at 85b7a26, with amendment 1 (bill's review) at 934343b before scoring. $0. Output:
`out/srtw.txt` and `.json`. Unregistered exact-null check: `srtw_mf.py`, `out/srtw-mf.txt`.*

**The primary bar fails.** On D clean plus D labels, relKL ranks a above every lure in 0 of 8 (the bar was 7) and in the
top 5 in 0 of 8 (the bar was 6). On A–C it keeps its top-5 count (10 of 12 against raw's 11), so it costs nothing where
raw already wins. But it doesn't fix D.

The registered selection theory half-holds, and only under the mean-field null. Pure rel, which was registered as
descriptive and expected to be noisy, puts a above every lure in 12 of 12 D world-cases, chain included. But:
- it ranks a 8th to 51st among all passages;
- under the exact null (relation labels averaged by sampling), a beats the lures in only 6 of 12.

## Table: a in the top 5 (of 4 seeds), and a above every lure

| case | raw | rel | relKL | deg | degKL |
|---|---|---|---|---|---|
| A clean, top 5 | 4 | 2 | 3 | 0 | 3 |
| B clean, top 5 | 4 | 2 | 4 | 0 | 3 |
| C clean, top 5 | 3 | 2 | 3 | 4 | 3 |
| D clean, top 5 / above lures | 0 / 0 | 0 / 4 | 1 / 0 | 0 / 0 | 0 / 0 |
| D labels, top 5 / above lures | 0 / 0 | 0 / 4 | 0 / 0 | 0 / 0 | 0 / 0 |
| D chain, top 5 / above lures | 0 / 0 | 0 / 4 | 1 / 0 | 0 / 0 | 0 / 0 |

In every D row, under every arm except rel, the best lure ranks 1st, apart from relKL 61004 clean, where it ranks 3rd.

## Predictions, scored

- **raw puts a above every lure in ≤ 4 of 8: held (0 of 8).** It's worse than SR1c's seeds (2 of 4 in the top 5
  there, 0 of 4 here).
- **deg doesn't fix D: held (0 of 8).** The degree null's random starts don't reach the cluster, so the lures look
  maximally surprising. That's CS's blind spot, which is what this run was set up to show.
- **Amendment 1, "lures gain under labels": held.** raw's rank of a worsens under labels in 4 of 4 seeds (8→11, 11→13,
  13→16, 8→15), and so does relKL's (3→9, 11→16, 16→20, 9→15). rel's rank of a doesn't move (it's invariant at a by
  construction). bill's boundary effect is real: a lifted cluster traps the walker.
- **The limit, "chain beats relKL": held, but trivially.** relKL already failed on clean.
- **The limit as it would apply to rel, "a twin chain fools the relations": wrong.** rel still puts a above every lure
  in 4 of 4 under chain.
  - The likely mechanism, a hypothesis that hasn't been tested: reach is a hit probability, and lure1 sits in an 8-clique,
    so once the walker is in the cluster it hits lure1 by many routes anyway. One selected door barely raises a
    probability that's already near saturation.
  - So in a dense cluster a twin chain isn't a twin in route terms. A twin chain to an isolated node would be the fair
    test.

## The exact-null check (unregistered, per bill's review 1)

The null is 40 random relabellings of every non-is_a link per world. Comparing log E_labels[h] with log h_0:
- the median is −0.8 to −1.1 nats, which shifts every node and cancels in a ranking;
- the spread across nodes is wide (5th–95th percentile on 61001: −1.35 to +0.16), and that changes the ranking.

| seed | rel's a > lures, mean-field (clean / labels / chain) | rel's a > lures, exact null |
|---|---|---|
| 61001 | yes / yes / yes (a 8th) | no / no / no (a 17–23rd) |
| 61002 | yes ×3 (a 43rd) | yes ×3 (a 37th) |
| 61003 | yes ×3 (a 51st) | no ×3 (a 125–132nd) |
| 61004 | yes ×3 (a 14th) | yes ×3 (a 9th) |

So rel's 12 of 12 belongs to the mean-field null, not to "relations that select". With the null that the theory
actually describes, it's 6 of 12, a coin flip on four worlds.

## What this answers

Sirsh asked whether a stricter coherence, measured as surprise over a null, stops gaming and is honest enough to be the
reward. For relational twins: **not yet, with any null tried here.**
- The degree null (CS) can't see the cluster.
- The relational null's surprise doesn't locate gold. It ranks a among dozens of relationally routed passages.
- Weighting the surprise by reach (relKL) hands the ranking back to the cluster.
- The selection-not-presence idea survives only under a null we can't defend as exact.

Between the two, raw reach priced by Jev (SR1c, and B, C here) remains the better single number. D's failure stays
open. The repair lead from THEORY-SR item 2 (entry doors naming their link), together with the question's type, is
where separation from a twin would have to come from. The relations can't supply it.

## Postmortem

1. **I predicted the direction of a product without its magnitudes.**
   - What I assumed: relKL = h·rel, with a ahead on rel, so a would be ahead on the product.
   - What the run showed: the lures' h is several times a's, and their rel is the same s→lure0 entry lift that b and a
     share. The product takes the larger spread.
   - The two-line chain formula (SR1c's h(a) and the cluster's hit probability) would have shown this at $0 before
     registering.
   - **Lesson:** price both factors of a product score on the planted cases before naming it primary.
2. **"The mean-field null, exactly" was an overclaim** (bill caught it). h is nonlinear in the conductances.
   - What it cost: the exact null moves a by up to 80 ranks and halves rel's twin result.
   - It was a $0, one-minute check, and I ran it after the registration instead of before.
   - **Lesson:** when a null is "exact by an argument", run the sampled version beside it before registering.
3. **The labels theory missed the boundary** (bill caught it). It was fixed in the amendment before scoring, and the
   amended prediction held in 8 of 8. Review before scoring paid off here.
4. **The twin-chain limit was wrong in an informative way.** "A copy of the relation sequence" isn't a copy of the
   routes, so the condition didn't test what its name says. The next registration should plant the twin on an isolated
   node.

**Spend:** $0, no Jev calls.

**Next, offered and not started:**
- (a) The twin chain to an isolated node, to settle the saturation hypothesis.
- (b) Score D with the question's type term (ATYPE) as the separating evidence, beside rel. That asks the "where must
  separation come from" question directly.

Both are $0.

## Follow-up (b), priced and not run

This was bill's preferred next step: does the question's type term separate a from the twins? I priced it first, on
SR1c's already-seen D worlds (41001–41004), not on fresh seeds.

| seed | h(a) | max h(lure) | gap | P(b→a) |
|---|---|---|---|---|
| 41001 | .116 | .692 | ×6.0 | .43 |
| 41002 | .084 | .646 | ×7.7 | .27 |
| 41003 | .187 | .682 | ×3.7 | .46 |
| 41004 | .164 | .688 | ×4.2 | .40 |

FITJEV's type term is γ_type = 1.09 nats (doors hide links) or .70 (doors show them).
- **In the walk:** b has 5 doors, and one of them (a) is of the asked type. So the term lifts P(b→a) to at most about
  .69, which multiplies h(a) by about 1.6–2.1.
- **In the score:** it adds at most e^1.09 ≈ ×3 against untyped lures, and ×1 against lures of the asked type.
- **Both together:** about ×5, which is still below the gap on 2 of 4 worlds. It also counts the same measured term twice.

So (b) fails by arithmetic, and isn't registered.

**Why the trap wins on reach.** The cluster sits one named-relation door from s, the same distance as b, and it then
holds the walker (h(lure) ≈ .65–.69 ≈ h of a one-hop node). The answer is two hops away. No per-door term of Jev's
measured size makes a two-hop hit probability beat a one-hop one that saturates.

A reach-based measure can separate them only by using the question's *order*: r1, then r2, then the asked type. That's
the per-step choice a decider makes when it's shown the paths. It isn't a property of a reach number. This is where the
remaining SR-TW question lives.
