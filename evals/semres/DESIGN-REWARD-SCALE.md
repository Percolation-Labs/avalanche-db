# Design (22 Nov): a reward scale that isn't a chosen unit

*bill. Follows SR-BC (#91). A design note for james's review; nothing is run or registered yet. $0 when run.*

**The problem.** SR-BR and SR-BC weight a door by (1 + r), where r sums 1/|S_k| per rewarded walk. The "1" makes one
pass's reward worth one unit of base door strength. That is a constant: tripling it (SR-BR's R3) moved the test score
+.007, not distinguishable from noise but in the direction that says the unit matters. Sirsh's rule is no magic
constants, so the reward needs a scale the data sets.

**Options considered.**
1. *Normalise by the mean reward*, (1 + r / mean r). This makes the walk invariant to repeating passes (R and R3 give
   the same walks), but "rewarded memberships are worth double on average" is still a unit.
2. *Normalise by the mean door strength in the pool.* Ties reward to base strength per question, but it changes with
   the pool and has no meaning as a quantity.
3. **A success rate per membership (proposed).** Count, for each (passage, key) membership, the learn walks that used
   it (n) and how many of those succeeded (w). Weight the door by the membership's rate relative to the base rate:

       m(p, k) = [(w + 1) / (n + 2)] / [(W + 1) / (N + 2)]

   where W / N is the success rate of all learn walks (.463). An unwalked membership has m = 1 (no evidence, no
   change). A membership walked and always successful rises; one walked and always failing falls below 1. S_w uses
   m(e, k) · m(v, k) in place of (1 + r(e, k))(1 + r(v, k)).

**Why option 3.**
- **No unit.** It's a ratio of rates; the +1/+2 is Laplace's rule, the standard zero-evidence estimate, not a tuned
  value. Repeating passes over the same walks doesn't change a rate, so accumulation can't move it, and T's fixed
  point is defined the same way.
- **It uses failures.** SR-BR's F arm (failures alone, as a boost) did nothing, but failures as *evidence against* a
  membership are a different use. The removal map (#84) found walked-and-failed memberships carry little value; this
  lets the reward act on them without deletion.
- **It answers "define good, converge toward it"** with a quantity: each door's weight is its measured rate of
  leading to a good walk, relative to the corpus's rate.

**Risks.**
- Most memberships are walked once (n = 1), so m is (2/3)/(.464) ≈ 1.44 for a success and (1/3)/(.464) ≈ .72 for a
  failure. The weights are coarse until a membership is reused, which matches SR-BR's finding that bridges reuse
  little across questions (6 of 459 test questions share a pair).
- Down-weighting failures can break walks that worked through a shared membership, which (1 + r) couldn't (SR-BR lost
  0). Report flips both ways.
- The 1/|S_k| share is dropped: a rate counts walks, not shares. That changes two things at once against SR-BC, so the
  comparison arm should be SR-BC's T* and an arm with rates from successes only (w counted, failures ignored,
  i.e. n = w).

**If registered.** Same data, split and walk as SR-BC. Arms: unweighted, T* (SR-BC), RATE (option 3, fixed point by
T's iteration), RATE-W (successes only). Primary: RATE − T* on test both hops. Prediction: about 0 to +.01; the main
readout is lost walks under RATE.
