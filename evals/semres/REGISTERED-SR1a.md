# SR1a: the price of a crossing (registered before the run)

*21 Nov 2026, james. Follows RESULT-SR1 and bill's RESULT-SR23 (#58). $0, token-free.*

**The claim.** Under the structure-and-semantics conductance, a two-hop chain's reach is the product of its step
shares, multiplied by a resonance:

  h(a) ≈ (1−α)² · P(s→b) · P(b→a) · Q,   Q = 1 / (1 − (1−α)² · P(s→b) · P(b→s))

- The crossing cost in nats is −log P(b→a).
- The back-current s ↔ b doesn't only lose mass. Each return is another try at the crossing, and Q counts the tries.
- Direction memory should cut the back share P(b→s), and with it Q.

**Seen before registering (the $0 look, seed 1 case B).** As noise goes 1 → 4, P(b→a) goes .0002 → .052 and exact h(a)
goes .0005 → .118. The formula gives .00052 and .135.

**Worlds.** Topic noise ∈ {1, 1.5, 2, 3, 4}, where cos to topic falls from .7 to about .25. That's 4 seeds × cases B and
C, so 40 world-cases. These numbers describe the worlds; nothing in the measure changes. α = .15 is L1's.

**Gate.** If any world-case's exact h(a) is below 1/20000 (what the Monte Carlo gate could see), stop as degenerate
before any bar is read. That's bill's lesson from SR23.

**Readouts.**
1. The log-log slope of exact h(a) on the formula across the 40 world-cases, with a 95% bootstrap. **Pass if the
   interval covers 1.**
2. Under direction memory, the back share after arriving at b from s, against P(b→s). **Pass if it is lower in at least
   3 of 4 seeds at every noise level.**

**Prediction.**
- 1 passes in B, where s has few other doors.
- C's hub doors add paths the formula ignores, so the slope is a little under 1, and C's points sit below the line.
- 2 passes; direction memory's whole mechanism is a dear reversal.
- The gate will trip at noise 1, where h(a) for some world-case is about .0005 or lower. If it does, I report it, and
  rerun on noise ≥ 1.5 only as a second registration, not as an edit of this one.
