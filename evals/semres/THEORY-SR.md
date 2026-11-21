# Semantic resistance: what a walk pays to cross, and what Jev actually charges

*21 Nov 2026, bill and james. This draft is bill's, for james's review before it goes to Sirsh. It answers Sirsh's brief
of 21 Nov (13:15Z and 13:16Z). Every number is from a registered run, listed at the end with its PR. Total Jev spend is
about $0.017. No Claude data was used, and the worlds are token-free.*

## Summary

The walk's step probability mixes structure and semantics. We wanted one quantity that prices both. **Semantic
resistance** is that quantity: the nats a walker pays to take a step. A step's resistance is −log of the step's share
of the walker's choice. Along a chain, the resistances add like resistors in series, and the reach is the product of
the shares (SR1a). Structure decides which steps exist. Semantics decide what each costs.

The question is who sets the prices.

**Cosine similarity sets them badly.** The vectors' own best-fit slope makes a decider so sharp that it won't leave a
topic. On real MuSiQue text, the second hop looks *less* like the question than the best distractor. A similarity-priced
walk fails on every bridge.

**Jev prices steps differently,** and we measured how:
- A weak similarity term of about 1–3 nats per unit of cosine.
- A large relational term for "this passage is what the one I've read leads to": 3.7 nats on MuSiQue, 1.6 on our cards.
- Terms for the asked type (about +0.7–1.1 nats) and for the needed relation, the second only when the door shows its
  link (about +0.7).
- A mild penalty for going back to what it has read (−0.85 nats), not a refusal.

With Jev's prices in place of similarity's, the same synthetic worlds, walk and solver reach the answer. On rendered
text, Jev's own choices match those prices at the chain's entry.

**Two things bound this.**
- The relational term depends on the corpus.
- A cluster wired by the right relation still traps the walker. That's the "twin gaming" of the coherence work, now
  sitting in the relational term.

## Sirsh's three questions

### 1. From a landing node, what is the probability of reaching each other node?

It's exact and computable. The walk is a resistor network, and reach is a voltage (Doyle & Snell).
- Hold the target at 1 V and ground every node through the walker's stopping leak (α = .15). The voltage at the
  landing node is the probability of reaching the target before stopping (`net.reach`).
- It matches 20,000 Monte Carlo walkers within 1.6 s.d., and fails by 20 s.d. when α is wrong (SR1's gate).

**Along a chain, reach factorises:**

h(a) ≈ (1−α)² · P(s→b) · P(b→a) · Q,  with  Q = 1 / (1 − (1−α)² · P(s→b) · P(b→s))

- On bridge worlds this is exact to three digits (median ratio 1.000, SR1a). With a hub nearby it under-predicts by up
  to 3.4×, because hubs are extra paths.
- Q is the walker bouncing between s and b. It's a reflection that gives the crossing repeated tries, worth up to about
  3.6×. It's not a loss.

**What the measure must combine.** The step share P(u→v) = c_uv / Σ c_uw. Structure decides which links exist. The
conductance c is where semantics enter, and the rest of this write-up is about which semantics.

### 2. If the question is split into probes, what is their combined percolation?

For independent probes, combined reach is P(v) = 1 − Π_k (1 − h_k(v)). At a fixed budget, give k probes 1/k of the
mass each.

**The first factor is landing (SR23).** A probe's percolation is P(it lands near) × P(it reaches | landed).
- Under a similarity decider, the second factor is nearly 0 across a topic boundary, so the landing decides everything.
- The only real percolation in 16 world-cases came where a probe naming the answer's *type* landed beside the answer
  (h = .85 and 1.0).
- So a questioner's split helps exactly when a probe can land where the walk can't cross to.

SR23 was degenerate (hits around 1e−4) and gives no pass or fail. The landing reading is all it supports.

### 3. Is coherence the probability that the reach sets together cover the gold?

Two readings need to be kept apart.
- **Collision (AND):** h_i·h_j, where two pulses meet. This is the earlier surprise-coherence measure, CS.
- **Coverage (OR):** every gold is reached by some probe.

**On chains, collision is the wrong reading.** A chain's second hop is reached from one seed only. On MuSiQue, CS
buried such a gold at rank about 2,000 where the walk had it at about 300 (CS-Q2, mq 130508). Coverage is the reading
that fits a chain. Collision fits only gold that sits where independent chains meet, which is the comparison-question
shape.

We didn't get a clean test of coverage against collision in vector space (SR23 was degenerate). The surprise-coherence
work (CS-Q1, CS-Q2) showed that no collision-based measure both resisted gaming and pointed at gold.

## What sets the prices: vectors against Jev

**The vectors.** The best logistic slope of the gold next hop on bge-small cosine is 8.7 nats per cos unit against the
question, and 10.2 against the read passage (MuSiQue dev, 200 questions).
- That's sharp. In a synthetic world built that sharp, a topic crossing costs 6–10 nats a step, and the walker almost
  never leaves its topic (SR1, SR23).
- On real MuSiQue the typical crossing is only about 0.5 nats under that slope. Even so, the vectors rank the gold next
  hop first in only 20% (question), 55% (read passage) or 62% (both) of questions (SR-J).

**Jev**, given 19 options after reading hop 1 (SR-J):

| | MuSiQue (40) | cards (40) |
|---|---|---|
| Jev picks gold first | **97%** | **75%** |
| best vector decider | 62% | 25% |
| similarity slope (nats per cos unit) | ≈ 1 | ≈ 1.7–3 |
| relational term γ (nats) | **3.7** [3.3, 4.1] | **1.6** [1.4, 1.8] |

- **The relational term is mostly the bridge entity.** On MuSiQue, "the passage names what hop 1 resolved" carries 3.8
  nats on its own. A decider using only that gets 90% (SR-J amendment 2). We couldn't split it from the gold label,
  because the two coincide.
- **The carry-over** (SR1c): the same worlds, walk and solver failed under every similarity-only conductance (0 of 4 on
  bridges). Under Jev's (β ≈ 1, γ ≈ 3.7) they put the answer in the top 5 in 4 of 4 (bridge) and 3 of 4 (hub lure),
  identically across γ's interval. Reach is .08–.42, and the chain formula prices it within 1.2–1.4×.

**On rendered text, Jev's own choices** (SR-JW2 and JW3, with string-reader controls registered first):

| | entry (hop 1) | bridge (hop 2) |
|---|---|---|
| door hides its links | Jev 1/16 against string reader 7 | Jev **14/16** against dictionary reader 9 |
| door shows its links, as real passages do | Jev **11/16** against string reader 7 (P ≈ .04) | Jev 13/16 |
| Jev against the theory's share, log | −0.09 [−0.79, +0.24] | +0.37 [+0.15, +0.63] |
| way-back share, Jev against theory | — | .09 against .29 (relative to a theory that over-credits the start) |

**The terms, fitted** (FITJEV: $0, registered before the fit, on the 64 rendered option sets; 95% intervals):

| term | door hides its links | door shows its links |
|---|---|---|
| γ_type (the door is of the asked type) | +1.09 [+.71, +1.54] | +0.70 [+.28, +1.06] |
| γ_rel (the door is linked by a needed relation) | +0.12 [−.10, +.35] | +0.66 [+.43, +.92] |
| γ_read (the door is already read) | +0.33 [−.27, +.98] | −0.85 [−1.46, −.29] |
| β (cosine) | not estimable here | not estimable here |

The conductance, as measured:

**c(u→v) ∝ exp( β·cos + γ_rel·[needed relation] + γ_type·[asked type] + γ_read·[already read] )**

- **β** is about 1–3 nats per unit of cosine, from SR-J on real text. The rendered worlds can't estimate it.
- **γ_rel** pays only when the door shows its link. In rendered worlds it's about +0.7, because "has relation r1 or r2"
  is common there.
- **The 3.7 and 1.6 from SR-J** are the *joint* term for "this is the next hop": relation, type and identity together.
  So they're larger than γ_rel + γ_type here.
- **γ_type** is the steadiest term: +0.7 to +1.1 in both renderings.
- **γ_read** is a mild penalty, −0.85 nats, about a 2.3× reduction, and only when doors show their links. It is not a
  mask.
  - An earlier draft said "−∞" and "one-way", from the way-back share. That was a ratio against a theory that
    over-credits the start, and a share ratio against a theory is not a coefficient.
- **No back-current.** The "inductance" first modelled as direction memory was compensating for an over-sharp
  similarity decider. With Jev's prices there's no back-current, and direction memory changes nothing (SR1c).

**Jev prices a door by what the door shows.** When the bridge passage hides its links, Jev doesn't take it, even though
the read passage names it (1/16). When the bridge shows them, Jev takes it (11/16).

So MuSiQue's miss on single-seed chains belongs to the graph: the walk never presents the entry door (S1′'s entry-hop
analysis, S4). The decider isn't refusing it.

## What this changes

1. **Price walks with the decider's conductance, not the embedding's.**
   - A graph measure, such as T\* cost, coherence or a repair reward, that uses cosine as its semantic term prices steps
     Jev doesn't pay, and misses the step it does pay for.
   - The relational term is the one to put into graph measures. The bridge entity, which the graph's own key doors
     already encode, is the computable stand-in for it.
2. **The entry hop is a graph property.** Repair should present entry doors whose passage names its link. That's a
   gold-free target, and candidate source (b) from S3 becomes concrete.
3. **The open problem is relational twins.** A cluster joined by the right relation takes the relational bonus too (D:
   2 of 4 in SR1c). The surprise-coherence null discounted hubs but not this. A null for relational convergence is the
   next coherence question.

## What is noise or unshown

- **SR23** (probes, collision, storage) was degenerate, and its bar counts compared numbers around 1e−4.
- **SR1** and **SR1a** have no registered pass. SR1a is descriptive, on seen worlds, after a mis-chosen gate.
- **SR-JW**'s hop-2 result is withdrawn: the renderer stated the answer's type literally.
- **β ≈ 1 is partly MuSiQue's construction.** On cards, Jev follows the question's wording more (β_q ≈ 3).
- **Rendered worlds use invented names and fixed word lists.** Nothing here was run on a real walk with Jev in the loop.
- **Small n.** These are directional slices of 16–40 items. 11 against 7 out of 16 is P ≈ .04.

## Postmortem, across the day

- **We twice registered readouts without printing one case's magnitudes** (CS-Q2 run 1, SR23), and once picked a gate
  that didn't fit its readout (SR1a). The harnesses now gate on degeneracy, matched to the readout.
- **A control has to be the cheap reader's actual rule.** SR-JW's normalised word overlap missed a literal giveaway that
  a one-string check found. The string readers are now registered rows.
- **A share ratio against a theory is not a coefficient.** The way-back share made the read term look like a hard mask.
  The fit makes it −0.85 nats.
- **The decider changed the theory, not the vectors.** The vector-space modelling (SR1, SR23) was reframed by $0.0044 of
  Jev calls. Next time, measure the decider's prices first. Stage 0 cost $0.00045.

## Runs

All are on avalanche-db. Each is registered before scoring, with a postmortem in its result file.

| run | file | PR |
|---|---|---|
| CS-Q1, CS-Q2 | RESULT-CS-Q1.md, RESULT-CS-Q2.md | #56, #55 |
| SR1, SR1a, SR1b, SR1c | evals/semres/RESULT-SR1*.md | #57 |
| SR23 | RESULT-SR23.md | #58 |
| SR-J (with amendments 1–3) | RESULT-SRJ.md | #59 |
| SR-JW, SR-JW2, SR-JW3 | RESULT-SRJW*.md | #57 |
| FITJEV (γ_type, γ_rel, γ_read) | RESULT-FITJEV.md | #57 |
