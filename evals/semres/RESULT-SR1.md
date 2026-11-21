# SR1 result: a reversible structure-and-semantics network doesn't price a two-hop chain

*21 Nov 2026, james. Registration: REGISTERED-SR1.md (89e9261). $0, token-free, about 2 min CPU. Output: out/sr1.{txt,json}.*

**FAIL.** No arm ranks the answer in the top 5 in at least 3 of 4 seeds for every case type. Counts are seeds of 4
where a ranks in the top 5, landing on s:

| Case | struct | sem | comb | comb@25 | comb + direction memory @25 |
|---|---|---|---|---|---|
| A semantic | 1 | 0 | 1 | 1 | 1 |
| B bridge | 0 | 0 | **3** | 3 | 2 |
| C hub lure | 0 | 0 | 1 | 1 | 1 |
| D cluster lure | 0 | 0 | 0 | 0 | 0 |

The gate held. Exact h matched 20,000 Monte Carlo walkers within 1.6 s.d., and the same check misses by 20 s.d. at a
wrong α.

## What it shows

1. **The back-current.** A reversible network doesn't know which way it came.
   - The question resembles its own start s, so the conductance pulls every walker back from the bridge to s.
   - Under comb the walk spends itself on 4–25 passages, with total hits ≈ 1–2: s and b, back and forth.
   - The answer's hit-by-25 is ≤ .017 in all 16 cases. In B it still *ranks* second, only because nothing else is hit either.
2. **Direction memory moves the walker on, and the rank read can't see it.**
   - Making reversal dear raised the answer's hit-by-25 in **16 of 16** cases, e.g. .0005 → .72 and .0000 → .71.
   - It also spread the walk from about 4–25 passages to 260–390, with total hits ≈ 5.3–5.5.
   - So a gains, but more passages pass it, and its rank falls in most cases.
   - That is a property of the read ("top 5 by mass"), not of the walk. A read that ranks by mass can't credit a walk for
     reaching further.
3. **Structure alone puts the answer at 5–21 every time.** That's just "two hops away": the hop count's neighbours
   outrank it, with no lure involved.
4. **Case A was badly designed.** The "semantic" answer's cos to the question (.38 and .22 on the first two seeds)
   sits at its 100 topic-mates' mean (.42 and .21). So semantics can't single it out, and sem ranks it 73–127. A $0
   look at that spread would have shown it before the run.
5. **D's cluster lure takes everything.** comb ranks a 91–323, and direction memory makes it worse (515–863).
   - The lures look like the question and are wired to s by the first hop's relation, so they win both semantic terms.
   - That is yesterday's twin gaming in miniature. bill's storage readout (SR23) measures whether the cluster holds mass.

## What the theory needs

The numbers say a single symmetric conductance can't price a chain whose second hop looks unlike the question. Two
pieces are missing:
- **Direction (an asymmetric, non-reversible term).** Direction memory supplies part of it. It is a momentum walk in
  the non-backtracking family, not a true inductor: it changes the steady state, not only the transient (bill's review).
- **A read that credits reach.** One option is each passage's hit against its hit under a null landing, which is what
  CS did for collisions. Another is the question's *coverage* of the gold, which is Sirsh's question (3) and bill's SR23.

The probes in SR23 (the start + r1 for the first hop, and the second hop's relation + the answer's type) give the walk
the second hop's semantics directly. That is the "intelligent questioner" half of the theory.

## Postmortem

- *Predicted:*
  - sem gets A. **Wrong**, by design (point 4).
  - struct fails C. Right, but it fails everywhere.
  - comb fails B–D. **Wrong for B:** 3 of 4.
  - Direction memory raises hit at a in B–D. Right, in 16 of 16 including A, but the registered read is rank.
- *Could a $0 look have stopped it?* For A, yes: print the cos of a against its topic-mates. For the rank read, partly.
  The gate's case already showed h(a) = .0005. I should have registered hit-by-25, not rank, as the primary read for
  direction memory, since its mechanism is reach.
- *Constants:*
  - α = .15 and 25 steps are L1's.
  - Both node and edge Bayes scales are measured on the world.
  - μ_nn applied to the displacement cosine is **borrowed by analogy**, which is the one assumed scale. A derived
    version would be the likelihood ratio of that cosine along planted 2-paths against random ones.
  - The generator's numbers describe the world and were fixed before the readout.
- *Next:*
  1. bill's SR23 (probes, collision against coverage, storage), now running.
  2. Then one registered re-read of SR1 with hit-by-25 against a null-landing hit, which needs no new walks.
  3. Only then the Jev carry-over (Sirsh's step two): does Jev's choice at b follow the Bayes conductance, and does it
     backtrack?
