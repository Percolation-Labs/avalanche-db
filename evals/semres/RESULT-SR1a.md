# SR1a result: the price of a crossing

*21 Nov 2026, james. Registration: REGISTERED-SR1a.md (6f5b6c4). $0, 7 s. Output: out/sr1a.{txt,json}.*

**No bar read: the registered degenerate gate tripped.** 13 of 40 world-cases have exact h(a) < 1/20000. Seed 3 is
degenerate at every noise level, with its crossing costing 23–28 nats. So by the registration neither readout is a
result.

**The gate was the wrong gate for this readout.** I copied it from SR23, where hits were compared with each other and
Monte Carlo resolution mattered. Here both sides, exact h and the formula, are computed exactly, so h = 10⁻⁹ is as
readable as h = .5. What follows is therefore **descriptive and unregistered**. Any pass claim needs a new
registration on new worlds (new seeds), because this one has been seen.

## Described, not passed

**The crossing price.** Across the 39 world-cases with h > 10⁻¹², exact h(a) against the formula
(1−α)²·P(s→b)·P(b→a)·Q:

| Case | n | exact / formula, median | range |
|---|---|---|---|
| B bridge | 19 | 1.000 | 1.000–1.34 |
| C hub lure | 20 | 1.005 | 1.000–3.38 |

- In B the formula is exact to 3 digits in most worlds. The two-step chain with its resonance *is* the reach.
- In C it under-predicts by up to 3.4×. The hub doors are other paths to a that the chain formula leaves out, as
  predicted.
- The crossing cost −log P(b→a) spans 0.02 to 28 nats. Reach falls with it one-for-one, scaled by Q.

**The resonance Q.** Q runs from 1.0, where the forward option wins and there's no back-current, to 3.6, where the
walker ping-pongs. So the back-current multiplies reach by up to about 3.6. It doesn't divide it. In circuit terms it's a
reflection that gives the crossing repeated tries, not a loss.

**Direction memory.**
- It lowers the back share in 40 of 40 world-cases.
- The median back share after arriving at b is 0.000 at noise 1, rising to .50 at noise 4.
- Its scale is μ_nn, the borrowed one, which shrinks as topics blur. So direction memory is strong exactly where it's
  needed least.
- Where the crossing costs over 10 nats, it only narrows the back share by a hair. There is nowhere better to go.

## What the theory now says, plainly

- **Semantic resistance of a chain is additive in nats.**
  - Each hop costs −log(its share of the walker's step), and the total is the sum, like resistors in series.
  - The structure decides which hops exist. The semantics decide each hop's share.
  - A hop to a passage unlike the question (the bridge to the answer) is where the resistance sits: 0 to 28 nats here.
- **Reflection gives a bounded gain.** Q = 1/(1 − (1−α)²·P_fwd·P_back) ≤ 1/(1 − (1−α)²) ≈ 3.6 at α = .15.
- **Direction memory is the closest thing here to inductance.** It cuts the reflection, which helps where the forward
  option is merely unlikely, and does nothing where it is effectively absent.

## Postmortem

- *Predicted:*
  - Readout 1 passes in B, with C a bit under the line. That's true as described, but not a pass.
  - Readout 2 passes. Also true as described, but not a pass.
  - The gate trips at noise 1. It tripped there and at every noise for seed 3. I didn't foresee seed 3, which carries a
    crossing of over 20 nats at every noise level.
- *Could a $0 look have stopped it?* My look used one world-case. A look at the gate's own condition over all 40 would
  have shown that the gate measures the wrong thing for exact quantities, before I registered it. Lesson: a gate
  belongs to its readout. Don't copy one across readouts without asking what it protects.
- *Constants:* α is L1's. The noise grid describes the worlds. μ_nn is borrowed, as stated in SR1.
- *Next:*
  - The formula needs no further $0 confirmation; a new-seed registration would add little.
  - The real question is Sirsh's step two: what crossing price does a real decider pay? That's bill's Jev
    measurement (b).
  - Its number drops straight into h(a) ≈ (1−α)²·P_fwd·e^(−cross)·Q, which predicts Jev's walk on these worlds.
