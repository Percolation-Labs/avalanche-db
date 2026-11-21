# SR23 result: degenerate, so neither a pass nor a fail of the theory. In this world, a probe's fate is set where it lands

*21 Nov 2026, bill. Registered in REGISTERED-SR23.md (b818ad1). The registered second readout (without r2+type) was coded
after registration and before the run. Output: `out/sr23.{txt,json}`. $0, token-free, 44 s of CPU.*

## Verdict

By the letter, the bars come out as follows:
- (2) fails on B, at 1 of 4 seeds.
- (3) fails, at 1 of 4.
- (L) passes, at 3 of 4.

**None of those counts measures anything.** On 14 of 16 world-cases, every probe's hit-by-25 at the answer is below
.003, and most are 0.0000 to four places. "Beats" compares .0001 with .0000. The ranks of a, in the hundreds among 1,240
passages, sort passages that are all essentially unreached.

The (L) pass is the same kind of thing: lure visits fall from 5.569 to 5.552. 5.569 is Σ(1−α)^t over 25 steps, the most
any set can get. x lands *inside* the lure cluster in every D case, so the walker starts in storage and never leaves.
That's a landing failure, and storage isn't tested.

## What it does show

1. **Where a probe lands decides everything.**
   - The only real percolation in 16 cases is seed 4. There, r2+type lands next to the answer, giving h(a) = .85 in C
     and 1.0 in D, where it landed on a.
   - Everywhere else, no probe lands in a's topic. A walk from another topic doesn't get there within 25 steps.
   - So the combined percolation of decomposed probes is, in this world, the probability that some probe *lands* near
     each gold. The walk adds nearly nothing after the landing.
2. **The Bayes conductance prices a topic crossing at roughly 6–10 nats per step.** On seed 1, case B, under the whole
   question x:
   - s's links have log g = 0.1 (b), 4.3, 4.8 and 6.2 (topic-mates). So p(s → b) ≈ .0016, which is 6.4 nats.
   - From b, the link back to s has log g = 11.6, and the link on to a has 2.2. So without direction memory, p(b → a) is
     about e^−9.4.
   - The chain costs about 16 nats, and the back-current is most of it. That's why direction memory lifts x's hit at a
     from .0005 to .72 there (james's SR1 shows the same in 16 of 16 cases).
   - This is a concrete, quantitative "semantic resistance": the nats a decider pays to cross a topic boundary, which
     comes out as DIM·μ·Δcos.
3. **The world is too sharp for the question.**
   - With DIM = 64 and passages at cos ≈ .7 to their topic, the Bayes-optimal decider almost never leaves a topic, and
     multi-hop retrieval becomes impossible by construction.
   - Real deciders do cross topics, so either real embedding topics are far less separated, or a real decider is much
     softer than Bayes-optimal for its own vectors.
   - Which of the two is exactly what the Jev carry-over step can measure: Jev's effective crossing cost in nats, from
     its choices between an on-topic and an off-topic link. That reframes the Jev step as a measurement, not a
     demonstration.
4. **Collision against coverage can't be read here.** P(all gold reached) is 0 under both everywhere except seed 4 C
   (OR .85, collision 0). That one case agrees with the prediction that coverage, not collision, is how a chain is
   reached, but one case is an anecdote.

## Postmortem

- **This is the same mistake as yesterday's Q2 run 1, the second time in two days.** I registered readouts without a $0
  look at one case's magnitudes. One print of h(a) for one probe would have shown values around 1e−4, and that the
  readout would rank noise.
  - The fix this time is a gate in the harness: before any bar is read, the harness checks that the answer's
    hit-by-25 under x exceeds the leak floor (one α-step's mass) in most cases. If it doesn't, it prints "degenerate"
    and stops. It goes into the next registration as a gate, which is the L3 lesson ("make the cheap direction check a
    gate").
- **Predicted:**
  - "(2) fails with blind probes": yes, though not for the predicted reason. Every probe is blind here, not only r2.
  - "(L) passes": by the letter only. "x lands in the lures" wasn't foreseen, and it's a world-design fact I could have
    printed beforehand.
- **What carries forward:**
  - Landing is a first-class term in the theory. A probe's percolation is P(land near) × P(reach | land), and in this
    world the first factor dominates.
  - The nats-per-crossing reading of semantic resistance is concrete enough to measure on Jev.

## Next (proposed, for james and Sirsh)

1. **A world with an explicit crossing cost.** Keep the generator, but set the topic spread so the Bayes crossing cost is
   a stated number of nats. Report the theory's predictions as a function of that one quantity, the world's own
   semantic resistance, rather than a constant tuned to make walks succeed.
   - Then the claim to test is falsifiable: hit(a) ≈ exp(−Σ crossing costs) along the tree, with direction memory
     removing the back-current term.
   - Gate: one case's magnitudes are printed and checked before registering.
2. **Jev carry-over as a measurement.** Pairs of links (on-topic against cross-topic) where Jev chooses, about 40 choices.
   Fit Jev's crossing cost in nats and compare it with the Bayes value. Registered with spend first; Stage 0 is 4
   choices at about $0.02.
