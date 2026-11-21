# SR1c: does Jev's measured conductance carry the walk to the answer? (registered before running)

*21 Nov 2026, james. Follows RESULT-SR1b and bill's RESULT-SRJ (#59). $0. No new Jev calls: this uses Jev's fitted numbers.*

**Conductance (net.conductance_jev).** bill's fit of Jev's choices on 40 MuSiQue questions:
- β ≈ 1.0 nats per cos unit for similarity.
- γ = 3.7 [3.3, 4.1] nats for "the next hop".

In the world, "the next hop" is a link whose relation the question names (r1 or r2). The world knows each link's
relation, the same way Jev reads it from text. So the step is ∝ exp(β·cos(x, v) + γ·[r_e ∈ {r1, r2}]). Direction memory
uses the same β.

**Everything else is SR1b's:** ATYPE, noise, α, 25 steps, the readouts and the gate. The seeds are fresh: 41001–41004.

**Pass.** comb ranks a in the top 5 in at least 3 of 4 seeds for **B and for C**, at γ = 3.7. γ = 3.3 and 4.1 (the
interval ends) are reported as sensitivity and are not part of the bar.

**Predictions.**
- **B and C pass.** About 1 in 4 random links carries r1 or r2, so a passage has about 2 matching doors among about 9.
  The chain's door wins 3.7 nats over the others, and its share is about e^3.7 / (e^3.7 + 8) ≈ .84 if it's the only
  match, or about .45 against one other match.
- **D:** the lure cluster is wired to s by r1, so the lures get the bonus too. Prediction: D still fails.
- **The chain formula now prices the walk better than in SR1b:** median exact/formula ≤ 1.5 on B.
- **The carry-over claim, if B and C pass:** the theory's walk, priced by Jev's measured conductance, reaches the answer
  that similarity can't. That is the vector stage carried over to what the decision model does.

## Amendment 1 (before running): cards' measured conductance

bill measured Jev on 40 cards (RESULT-SRJ amendment 3): β = 1.7 per cos unit on the option, and γ = 1.6 [1.4, 1.8]
nats relational. I run the same SR1c worlds with (γ 1.6, β 1.7). Nothing else changes.

**Prediction.**
- The weaker relational term loses to the other matching doors. The chain's share is about e^1.6/(e^1.6 + 8) ≈ .38
  against .84 at γ = 3.7.
- B falls below the bar: at most 2 of 4 seeds in the top 5.
- Reach at a drops by about half or more.
- That's a prediction of a weaker Jev walk on cards, which bill can check against the cards walks we already have.
