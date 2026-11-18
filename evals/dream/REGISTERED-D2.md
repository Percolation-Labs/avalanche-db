# Registered: D2, edges learned as link prediction from walks (james, 18 Nov 2026, before spend)

D1's postmortem (RESULT-D1-stage0.md, #34): hubs cut around one passage are loose neighbourhoods, too thin to be
the door Jev should open. The Steiner result says gold pairs are mostly linked to each other. So D2 writes **edges**:
pairs of passages the loop predicts are co-relevant, learned from its own walks. Structure only, as Sirsh ruled
(M-20261118-200827-fd14): no text, no per-kind weights, nothing set by hand.

**Room (G0, test).** Test gold pairs not already one door apart: cards .08, PR titles .17, MuSiQue .34.

## The operator

- **Candidate pairs, question-free and graph-wide.** For each passage, its 50 heaviest neighbours in the passage
  graph (D1's weights), and their neighbours' heaviest 50 (two steps). This includes pairs not yet linked.
- **Features, structural.** Projected weight, shared keys, the fewest postings among the shared keys, a direct
  next/near link, common neighbours (Adamic–Adar), both degrees. Kind is not a feature. Next/near count as a link,
  not as a kind.
- **Label, from training walks.** A pair is positive when both passages are gold for one training question (dev,
  plus the 265 pool cards on p8). Negatives are the other candidate pairs that touch a training gold passage.
- **Model.** A logistic model, fit on 80% of training questions and checked on the held-back 20%.
- **Write.** The top N pairs by the model's score, as 2-member hubs (D1's writer). N is 1% or 5% of passages.

## Held-out read-outs (test, $0)

- **(a):** the share of test gold pairs not one door apart in G0 that a written edge connects.
- **(b), the ceiling:** on test waves (from the test traces), the share where a written edge is raised from the read
  set and leads to unread gold. Comparing with the best existing door needs door rows, which test does not have, so
  that comparison is the dev ceiling (D1's `ceiling.py` shape), in-sample and labelled as such.
- **Controls:** random candidate pairs (same N); Adamic–Adar alone (an unlearned score, the "does learning
  matter" control); oracle (all test gold pairs, the ceiling).

## Gate and pass

- **Gate:** the Jev stage runs only if learned edges beat both random and Adamic–Adar on (a) and the test ceiling
  by at least .05 on two of three sets.
- **Pass:** as D1. Gold door first (b) rises by at least .05 over G0 and random on two of three sets, and recall
  is no worse than G0 or search.

## Spend

$0 for the stage above. Jev, if gated in, is capped at $1.00 with a probe request first.

## Postmortem

Every result is postmortemed.
