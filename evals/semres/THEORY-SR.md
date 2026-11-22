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
topic. On real MuSiQue text, the second hop looks *less* like the question than the best distractor. At MuSiQue's
measured slope, a similarity-priced walk put the answer in the top 5 in 0 of 16 world-cases (SR1b). With the generator's
own Bayes slope it got 3 of 4 bridges (SR1), so the failure is specific to the calibrated slope.

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

- Registered, on fresh worlds under Jev's conductance (SR1c): the formula prices reach on bridges within 1.2–1.4×.
  SR1a's descriptive look found a median ratio of 1.000; it was unregistered, on worlds already seen, after a mis-chosen
  gate. With a hub nearby the formula under-predicts by up to 3.4× there, because hubs are extra paths.
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

> **Caveat (21 Nov, RESULT-SRK correction).** The MuSiQue 40 are the first 40 answerable 2-hop questions in file order,
> an easy block. The best vector decider gets .62 there and .42 over all 1,252. So Jev's 97% is likely optimistic for
> MuSiQue at large. β and γ are within-question contrasts and may carry over better. That's untested.

- **The relational term is mostly the bridge entity.** On MuSiQue, "the passage names what hop 1 resolved" carries 3.8
  nats on its own. A decider using only that gets 90% (SR-J amendment 2). We couldn't split it from the gold label,
  because the two coincide.
- **The carry-over** (SR1c): the same worlds, walk and solver failed under every similarity-only conductance (0 of 4 on
  bridges). Under Jev's (β ≈ 1, γ ≈ 3.7) they put the answer in the top 5 in 4 of 4 (bridge) and 3 of 4 (hub lure),
  identically across γ's interval. Reach is .08–.42, and the chain formula prices it within 1.2–1.4×.
  - The caveat belongs here, not only at the end: the worlds give the relation label exactly, and γ = 3.7 was applied to
    "the relation is r1 or r2", not to the next hop's identity, which is what SR-J measured.

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

**c(u→v) ∝ exp( β·cos + γ_rel·[needed relation] + γ_type·[asked type] + γ_read·[already read] )**, with β from SR-J only

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
  similarity decider. With Jev's prices there's no back-current, and direction memory changes no top-5 count at γ = 3.7, though it raises hit-by-25 in 12 of 16 (SR1c).

**Jev prices a door by what the door shows.** When the bridge passage hides its links, Jev doesn't take it, even though
the read passage names it (1/16). When the bridge shows them, Jev takes it (11/16).

This is consistent with MuSiQue's single-seed chain miss belonging to the graph, with the walk never presenting the
entry door (S1′'s entry-hop analysis; S4's 23% and 49%, which are upper bounds). It's shown only on rendered worlds:
there, the decider takes the entry once the door shows its link (11/16, P ≈ .04).

## Afternoon, 21 Nov: the random-draw price, the door, and REM-1341's vector operations

**Jev's MuSiQue price, redrawn** (SR-J-R, a random 40 from 41–1252, $0.0049): **3.8·cos + 3.2·[next hop]** nats.
- The next-hop term holds (3.24 [2.79, 3.71]).
- The similarity slope was a block artifact (1.0 on the first 40, 3.8 [2.2, 5.4] on the random draw).
- Jev's top-1 is .88, against the best vector's .40.
- SR1c rerun at this price (james): B 4/4, C 3/4, but A and D fall, because the higher β feeds the lure trap.

**Measured gold-free, on all 1,252 questions** (SR-K, SR-E, SR-E2):

| hop-2 decider, given the read passage | top-1 |
|---|---|
| cos(question + read), the text probe | .39–.42 |
| **shared rare door keys, Σ 1/(df − 1), lexical** | **.58** |
| Jev (random draw) | .88 |

- **End to end:** an entry by cosine, then its door link, lands both hops in .50, against .23 for cosine's top two.
- **Order matters.** That beats choosing the pair jointly (+.06 on 500 fresh questions).

**REM-1341, vector operations on key bundles** (SR-KB, SR-KB2, james's W-LOOKS and MaxSim): all fail to beat the text
probe.

| route, 300 random questions | top-1 hop 2 |
|---|---|
| Average PRF / Rocchio of key-phrase vectors (idf or 1/(df − 1), centre removed) | .32–.37 |
| holder means (stored vectors of each key's other passages) | .28–.32 |
| token-level MaxSim, key phrase against option tokens (james, priced only) | .41 |
| lexical door, for reference | .58 |

The warps are a separate note, because they weren't measured on the 300. james priced the Jev-taught and graph-taught
diagonal warps on SR-J's 40, the easy block. Their agreement with Jev's pick was .12 and .40, against the text probe's
.62 on the same block.

**The reading.** The next-hop term is an *identity* term: does the option name what hop 1 resolved? bge-small's
vector space keeps only a trace of that. Averaging turns identity into topic, and topic is what every option in the pool
already shares. So:
- **The cheap library operation is lexical:** shared rare keys weighted by 1/(df − 1).
- **Vectors earn their place before the door and after it.** Before: the entry by cosine. After: ordering the door's
  shortlist for Jev.
- **Twins need the ordered step.** No reach number separates them (SR-TW).

**Open, for Sirsh.** Every vector route used bge-small. A late-interaction model (ColBERT) might keep identity in its
token vectors, but that's a new model, not a $0 look.

## Evening, 21 Nov: a cheap pipeline that names the bridge

**Why the door misses** (K-MISS, seen data). Of the door's 127 misses, 103 lose to a lure with *more* shared-key
strength, and only 24 have no door at all. So the gap is discrimination, not coverage. Walking through the hop-1
answer's key alone (gold, a ceiling) would get .71.

**ColBERT** (SR-CB, fresh). A small CPU late-interaction model doesn't beat the text probe against the whole read
passage (.31 against .40) or the lexical door against the keys (.42 against .54). Handed the bridge's name, it finds hop
2 in .81. So identity survives in token space, and the failure is picking the name out of the read passage.

**Naming is a decision, not a cosine** (SR-BN, fresh). Cheap namers pick the bridge key .05–.15 of the time, out of
about 22. Jev picks it .70. Stepping lexically through Jev's name gives +.093 [+.060, +.130] over the door, at about 8%
of a passage request's input. Once a name is chosen, a token matcher adds nothing over the lexical step. No ColBERT
index is needed.

**Beyond the name** (SR-BT, fresh). Jev's extra is the second relation, and it lives inside the named twins. Asking Jev
only about the twins adds +.119 [+.075, +.168] (+.43 within the twins), at under one passage per question. The rest of
the gap to Jev's full choice is the case where no option shares the name (Jev's name was wrong, .08 right).

**The full walk** (SR-BW on dev, SR-BX on fresh MuSiQue train with a rebuilt graph, #75).

| step from cosine's entry (train, both hops) | |
|---|---|
| the door (cosdoor) | .473 |
| + Jev names the bridge, lexical step | .523 |
| + Jev over the named twins | .617 |
| + Jev's full request only when the name matches nothing (the rescue) | **.723** |
| Jev over all 19 passages | .743 |

- Every piece is a registered gain on fresh questions. The rescue is the largest (+.107 [+.070, +.147]).
- The cheap walk is within about .05 of Jev reading every passage, post hoc (−.020 [−.053, +.013]), at about 40% of
  the input.
- The entry stays cosine's. A Jev entry over titles finds hop 1 less often (−.130), because asked what to read first,
  Jev picks the passage that holds the answer.

## Semantic inductance, 22 Nov: three intuitions as tests

Sirsh's note (22 Nov, 10:35Z) names *semantic inductance*: resistance to *change* in flow, so memory and momentum. These
are tests of it, not a definition.

**(1) Walk momentum: does a step's price depend on the path so far?** (SR-MO, james, dev 3hop1, 100 fresh, $0.040)
- **No momentum at one step.** A wrong earlier read, carried as kappa's `found`, doesn't raise the prices of options on
  its own thread: pull −.056 [−.115, +.009].
- Jev discounts what `found` says was already read (−.18).
- **Any `found` raises every option's price by about +.3 logit,** whether it's true or wrong, on or off the thread. The
  answer's own price stays flat or falls. So history narrows the answer's lead without steering (post hoc).
- **It's content, not format** (SR-MO2, 200 fresh, $0.127). An irrelevant `found` of the same form shifts prices
  +.013 [−.009, +.036]. A question-related one, true or wrong, shifts them about +.29. So relatedness inflates every
  price, and truth doesn't matter.
- No history changes Jev's top choice beyond the noise floor of an identical repeat (flips about 2× the floor, with
  every CI including 0). SR-MI's null common mode had held relatedness fixed, so it couldn't speak to this.
- **On BEAM it's different** (SR-MO3, 109 questions, $0.033). Any `found` (related, a gold sentence, or another
  conversation's) narrows unread gold's average lead by about .1. Related history barely moves non-gold (−.02), and
  unrelated history deflates it (−.2). So "content, not format" is MuSiQue-specific. There's no resemblance pull at one
  step (rho slightly negative).
- Only an oracle history (a gold message's sentence) changes the top choice: +.10. Kappa's BEAM walk loss more likely
  comes from what walks read (related, non-gold) than from step prices. That's an inference.

**(2) Mutual inductance: does flow on one path energise a parallel one?** (SR-MI, bill, train 3hop2, 188 fresh, $0.072)
- **Yes, a little, in Jev.** Having read one parallel branch, Jev prices the other branch +.233 [+.170, +.296] logit
  above an equally question-like control read. That's corrected for a common mode, which is about zero here.
- **In series it's about twice as strong.** The join gets +.52.
- **The vector probe goes the other way.** cos(q + read) *lowers* the parallel branch (−.055): it follows what was read
  away from what's still needed. So split probes combine in the decider, not in vector arithmetic.

**(3) Inertia over time: does well-earned structure resist restructuring?** (bill, #79, $0, unregistered look)
- D3's gold-free pruning vote was run unchanged on graph-mq. Memberships whose key joins two consecutive gold hops are
  removed .008 of the time in round 1, against .136 for the others. That holds within the same passage (.008 against
  .160) and in every df band.
- Survival after all rounds is .978 against .804. Change per round falls from 12.9% to 0.8%, so the graph stiffens.
- **It's mostly relatedness** (james's control). Keys shared by two related non-gold passages of the same pool, matched
  on df, survive at .939. Gold bridges get only a little more (.978).
- **This is structural resistance, not memory.** D3 re-votes from the current graph each round and has no record of
  use.
- **Keeping the bridges isn't enough.** D3's registered test has walks *worse* than random pruning of the same size
  (.765 against .789, from .807). What it removes around the bridges carried context the walks used.
- **The memory term is the wrong lever** (bill, #82, $0 power check). D3 removes only 18 of the 557 memberships that
  gold-free walks used. Removing high-vote memberships loses to random as badly as removing low-vote ones (.759 and
  .765 against .79). Vote-directed pruning probably concentrates damage (an inference from two registered results), so a target for dreaming has to be priced on walks
  (a membership's counterfactual effect on a path's resistance to gold), not on a neighbourhood vote.
- **Priced on walks** (bill, #84, $0, seen waves, split by question). A question's own bridges cost about 3–4× what
  other questions' bridges cost per membership. Those cost about 3–5× an ordinary membership, and pruning ordinary
  memberships is about neutral.
- So "good" is concentrated in question-conditioned bridges. A dreaming target should reward bridges from walk outcomes
  on real questions, not prune by structure. The first bridges removed cost most, so parallel bridges are partly
  redundant.

**Where kappa fits.** Kappa is the walk's memory, sent to Jev as `found`. On today's evidence its effect at a step is a
uniform, relatedness-driven inflation plus a discount on what's been covered, not a pull along the thread. The coupling that does exist sits in
what's *being read*: a branch lifts its chain neighbour and, less, its parallel twin.

Hypothesis, not a finding: inductance-like coupling lives in the current read, not the history. It's testable in one
design that varies read and `found` on one draw.

**Toward Sirsh's "good".** A target for dreaming would be low resistance to gold, measured as the cheap walk's both-hops
rate (it's now within about .05 of Jev at 40% of the input), plus the inductive terms that turn out to carry signal. So
far that's the read-coupling (2), not history (1). (3) shows a structural vote can keep the bridges and still lose walks, so "good" has to price the whole
path, not the bridge alone.

## What this changes

1. **Price walks with the decider's conductance, not the embedding's.**
   - A graph measure, such as T\* cost, coherence or a repair reward, that uses cosine as its semantic term prices steps
     Jev doesn't pay, and misses the step it does pay for.
   - The relational term is the one to put into graph measures. The graph's own key doors are a partial, gold-free
     stand-in. Given the entry, they pick the next hop in .58 of all 1,252 questions, against cosine's .42. But they
     absorb under 1 nat of Jev's 3.8 (SR-K, corrected).
2. **The entry is cosine's, and the graph's door adds the second hop.** Both hops land in .50, against cosine's .23,
   over 1,252 questions (SR-E, SR-E2). Repair should give well-landed entries a door to their link.
3. **Relational twins aren't separated by a reach number.** SR-TW's relational null failed: relKL put a above every lure
   in 0 of 8, and rel's 12/12 dropped to 6/12 under the exact sampled null. A trap one named-relation door from s
   saturates at a one-hop node's reach. Separation lives in the ordered per-step choice. SR-E2 finds the same on real
   data: entry by cosine, then the door, beats choosing the pair jointly (+.060 [+.026, +.094]).

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
| SR-K, SR-E, SR-E2 (with the first-40 correction) | RESULT-SRK.md, RESULT-SRE.md | #60 |
| SR-TW (relational null) | RESULT-SRTW.md | #61 |
| SR1b/SR1c block corrections and re-price | RESULT-SR1b.md, RESULT-SR1c.md | #62 |
| SR-J-R (Jev, random draw) | RESULT-SRJR.md | #63 |
| W-LOOKS, MaxSim (priced, not registered) | RESULT-W-LOOKS.md | #64, #67 |
| SR-KB, SR-KB2 (key-bundle probes) | RESULT-SRKB.md, RESULT-SRKB2.md | #65, #66 |
| K-MISS (where the door misses) | RESULT-K-MISS.md | #69 |
| SR-CB (small ColBERT) | RESULT-SRCB.md | #70 |
| SR-BN (Jev names the bridge) | RESULT-SRBN.md | #71 |
| SR-BT (Jev over the named twins) | RESULT-SRBT.md | #72 |
| SR-BW (full walk, dev) | RESULT-SRBW.md | #73 |
| SR-BX (full walk, train; entry factor; rescue) | RESULT-SRBX.md | #74 |
| Train door-key graph and calibration | NOTE-TRAIN-GRAPH.md | #75 |
| SR-MO (momentum) | RESULT-SRMO.md | #76 |
| SR-MI (mutual inductance) | RESULT-SRMI.md | #77 |
| Inertia look (D3 survival against gold bridges) | RESULT-INERTIA-LOOK.md | #79 |
| SR-MO2 (kappa's shift: content, not format) | RESULT-SRMO2.md | #81 |
| D3m power check and two-entry pricing | NOTE-D3M.md | #82 |
| Removal-value map (bridges, priced on walks) | RESULT-REMOVAL-MAP.md | #84 |
| SR-MO3 (kappa on BEAM, one step) | RESULT-SRMO3.md | #85 |
