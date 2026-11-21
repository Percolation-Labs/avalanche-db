# SR1c result: Jev's measured conductance carries the walk to the answer

*21 Nov 2026, james. Registration: REGISTERED-SR1c.md (900fa2d). $0, with no new Jev calls; it uses bill's fit of Jev's
choices (RESULT-SRJ, #59). Outputs: out/sr1c-{3.3,3.7,4.1}.{txt,json,log}.*

**PASS.** At γ = 3.7, comb ranks the answer in the top 5 in **4 of 4 seeds for B and 3 of 4 for C**, on fresh worlds.
The Monte Carlo gate held, at 1.32 s.d.

Seeds of 4 with a in the top 5:

| Case | struct | sem | **comb (Jev: β 1, γ 3.7)** | comb@25 | + direction memory |
|---|---|---|---|---|---|
| A semantic | 2 | 1 | **3** | 3 | 3 |
| B bridge | 0 | 0 | **4** | 4 | 4 |
| C hub lure | 0 | 0 | **3** | 3 | 3 |
| D cluster lure | 0 | 0 | **2** | 2 | 2 |

- **Sensitivity.** The counts are identical at γ = 3.3 and 4.1, the ends of Jev's interval. The only change is
  direction memory on D at 3.3 (0 of 4).
- **Reach.** The answer's reach is now .08–.42, against ≤ .04 in SR1b on the same kind of world. The median crossing
  costs about 1 nat, which is near bill's real 0.5.
- **The chain formula prices it.** On B, exact/formula is 1.19–1.42 (median 1.28). The registered bound was ≤ 1.5.

## What it shows

- **The carry-over Sirsh asked for, in one line.** The same worlds, walk and solver failed under every similarity-only
  conductance (SR1 and SR1b, 0 of 4 on B). They reach the answer once the conductance is the one measured from Jev's
  choices.
- **What made the difference.** Jev's choice is about 1 nat per cos unit of similarity, plus 3.7 nats for "this door is
  the relation the question needs". The second term is the semantic resistance that matters: it is relational, not
  similarity.
- **Back-current is gone, and with it direction memory's job.** Jev's similarity slope is low, so the start no longer
  pulls the walker back. Direction memory raises hit-by-25 in only 12 of 16 cases, and changes no top-5 count at γ = 3.7.
  The "inductance" was compensating for an over-sharp similarity decider.
- **D improves without solving it.** 2 of 4 against 0. The lures sit behind an r1 door, so they get the relational bonus
  too. A cluster wired by the right relation is still a trap. That's the twin gaming again, now at the relation level.

## Caveats

- **"The next hop" in the world is a relation label the question names.** Jev's γ was measured on text, where the
  relation has to be read. The world gives it exactly, but more weakly than Jev had it: about a quarter of all doors
  carry r1 or r2, so the chain's door competes with other matches.
- **β = 1 has a wide interval** ([.13, 1.74]), and I didn't sweep it. A low β is what removes the back-current.
- **Jev's fit comes from 40 MuSiQue questions**, whose distractors are built to resemble the question (bill's caveat).
  Cards and PRs would test whether β ≈ 1 is Jev's or MuSiQue's.

## Postmortem

- *Predicted:*
  - B and C pass: right.
  - D fails: wrong, 2 of 4 (better).
  - The formula within 1.5 on B: right.
- *What I'd have missed without SR1 and SR1b:* that the failures were the decider's, not the theory's. The network, the
  solver and the chain formula didn't change between SR1b and SR1c. Only the conductance did.
- *Constants:*
  - β, γ, the slope 8.7 and the gap .146 are measured.
  - ATYPE is bisected on discarded seeds.
  - Noise 1.0 is SR1's world, uncalibrated.
- *Next:*
  1. bill's (2): the same Jev fit on cards and PRs, about $0.01.
  2. A Jev-in-the-loop walk on 4 of these worlds, rendered as text. Does Jev's own walk match the predicted reach?
     That's the last link in the carry-over. I'd register it at about $0.05.
  3. The real-graph version: the MuSiQue walk with γ from a relation detector in place of Jev.

## Amendment 1: cards' measured conductance (γ 1.6, β 1.7)

Registered before running. Seeds of 4 with a in the top 5:

| Case | Count |
|---|---|
| A | 2 |
| B | 3 |
| C | 2 |
| D | 0 |

- Reach at a on B and C is **0.44× MuSiQue's** (median, range .35–.59). That's as predicted ("drops by about half or more").
- B's ranks are 5, 4, 7 and 2. That makes 3 of 4, against my predicted "at most 2 of 4", so that part is wrong.
- The walk still reaches the answer, but with half the reach. The answer sits at the edge of the top 5 instead of near
  the top.
- D drops to 0 of 4. With a weaker relational term, the lures' similarity matters again.
- **Postmortem.** My share arithmetic assumed about 8 competing doors at every hop. Doors that carry neither relation
  are dearer than that by e^(β·Δcos). So the chain kept more share than I computed.
- **For bill's check against real cards walks:** the theory predicts a Jev walk on cards that reaches gold about half as
  often as on MuSiQue, for the same structure.

## Caveat (21 Nov, after RESULT-SRK's correction)

SR1c's γ 3.7 and β 1.0 are SR-J's fit on MuSiQue's first 40 questions in file order, an easy block. There, cosine top-1
is .62, against .42 over all 1,252. They're within-question contrasts, so they may carry over better than the block's
top-1 rates do, but that's untested. On cards (γ 1.6, β 1.7, amendment 1) the block issue doesn't arise. SR1c's carry-over
claim should be read as "at the conductance Jev showed on that block". A Jev refit on a random draw of questions would
settle it; its price would be probed before registering it.
