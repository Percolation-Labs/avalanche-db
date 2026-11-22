# SR-MO3: on BEAM any history narrows the gold's average lead by about .1, and a true history still raises the top choice by .10

*22 Nov 2026, james. Registered in `REGISTERED-SRMO3.md` (#85, with amendment 1 from bill's review, before any Jev
call). Jev spend: $0.0013 for stage 0 and $0.0318 for the wave (545 requests, one `ask_many`, cap $0.25). Outputs:
`out/srmo3-stage0.txt`, `out/srmo3-fresh.txt`, `out/srmo3-fresh.json`.*

**Versions.** percolate-core 0.2.15 (Jev). The BEAM 1M fixture (`~/.cache/walklab/fixture-1M`), all conversations,
recorded search order. 113 usable questions: stage 0 is the first 4 and the registered set the other 109.

**Question.** Kappa's sentence state cost BEAM walks −.022 (kappa round 5). At one step on MuSiQue, question-related
history inflates every option by about .3 and narrows the answer's lead (SR-MO, SR-MO2). Does related history narrow
the gold's lead on BEAM? Jev has read the first gold message search finds and prices the next 19, under these histories
(K6, a message's first sentence):
- `none`, and its repeat `none2`;
- `true`: another gold message;
- `related`: search's top non-gold message;
- `irrelevant`: a message from another conversation.

## Registered result

| Δlogit against none | lead: gold minus non-gold | shift over non-gold | rho (overlap with found, Δ) |
|---|---|---|---|
| **related (primary lead)** | **−.118 [−.178, −.058]** | −.019 [−.058, +.021] | −.081 [−.138, −.021] |
| true | −.105 [−.169, −.043] | +.067 [+.016, +.122] | −.054 [−.109, +.002] |
| irrelevant | −.139 [−.203, −.075] | **−.205 [−.246, −.167]** | −.050 [−.100, .000] |
| related − true | −.013 [−.067, +.039] | | |

| top-1 gold | rate | lost / gained against none | − none |
|---|---|---|---|
| none | .495 | | |
| none2 (identical repeat) | .495 | 4 / 4 | .000 [−.046, +.055] |
| **true** | **.596** | 9 / 20 | **+.101 [+.009, +.193]** |
| related | .468 | 15 / 12 | −.028 [−.119, +.064] |
| irrelevant | .477 | 14 / 12 | −.018 [−.110, +.073] |

- **H-B passes as registered:** related history narrows the gold's average lead (−.118). **But it isn't specific to
  related history.** A true history narrows it about as much (−.105; related − true −.013 [−.067, +.039]), and so does an
  irrelevant one (−.139). On BEAM, adding *any* `found` lowers unread gold relative to non-gold by about .1 logit on
  average.
- **The common mode differs from MuSiQue.** Related history barely moves non-gold here (−.02, against +.29 on
  MuSiQue). Irrelevant history *deflates* everything (−.205), where on MuSiQue it did nothing (+.013).
  One guess, untested: on BEAM another conversation's turn reads as conflicting context (other people, other
  facts), not as noise. So SR-MO2's "content, not format" holds for MuSiQue. On BEAM even unrelated `found` moves
  prices.
- **There's no resemblance pull at one step.** rho is slightly negative for every history: options that share words with
  `found` gain a little *less*. Round 5's +.118, a walk-level door statistic, doesn't appear as a per-option effect here.
- **A true history improves the choice. It's an oracle arm:** `found` is a gold message's first sentence, so Jev is
  shown part of the answer's thread, not just a right history (bill's review). Top-1 gold rises from .495 to .596 (+.101, gained 20 against lost 9, against
  the 4/4 floor). Related and irrelevant histories leave it unchanged within noise. So while the *average* gold lead
  narrows, the *best* gold rises. A true history seems to help Jev find the one most relevant unread message and
  lower the rest.

**Predictions against outcomes.**
- lead(related) about −.3, H-B passes: it passed, at −.118, a third of the size.
- shift(related) about +.3: **wrong**, −.019. The MuSiQue inflation doesn't carry to BEAM.
- shift(irrelevant) about 0: **wrong**, −.205.
- rho(related) about +.1: **wrong sign**, −.081.
- top-1 gold falls under related by .02–.05: −.028 [−.119, +.064], the right direction but within noise.

## What it means for kappa

- **At one step, BEAM gives no clean mechanism for kappa's walk-level loss.** The registered primary passes, but every
  history narrows the average gold lead, a right one included. The only history that changes choices is the oracle
  `true` one, and it *helps* (+.10).
- An inference, not tested: kappa's BEAM loss (−.022 over walks) more likely comes from **what the walk reads** than from the step prices. In
  BEAM walks the reads are mostly the user's own on-topic messages, so `found` is related but not gold. Here related
  `found` leaves the top choice unchanged, so a related-but-not-gold state doesn't help, and every state lowers the
  average gold a little. A state built from *gold-like* reads might help, as the oracle `true` arm does here. That points to round 5's
  own conclusion, a structure-dependent state ("what not to read again" for many-piece questions), now with a step
  measurement under it.
- **Corpora differ in how Jev reads `found`.** On MuSiQue, related history inflates everything (+.3) and unrelated does
  nothing. On BEAM, related does nothing and unrelated deflates (−.2). A decider's response to context depends on the
  corpus, so graph measures priced from Jev's p need the context fixed per corpus, as SR-MO2 said.

## Postmortem

- **What went right.** Stage 0 flagged the surprise (lead positive in 3 of 4; Jev's top pick non-gold in all 4 under
  none). I posted it before the wave, and the design was sign-agnostic, so the wave ran as registered. bill's true arm
  turned a passing primary into an honest reading: the narrowing isn't about relatedness. Without it, H-B would have
  been reported as the mechanism.
- **What I got wrong.** Four of five directional predictions were wrong. I transferred MuSiQue's step effects to BEAM
  without a stage-0-sized look at how Jev reads `found` on BEAM's chat messages. And a primary that passes for a
  reason the controls share isn't a mechanism. The lesson: make the primary a contrast against the control
  (related − irrelevant, or related − true), not a level against `none`.
- **Scope.** One step, one history length, BEAM 1M, recorded search order (not a walk), 109 questions of mixed types.
  "Lead" averages over unread gold, and top-1 is the best gold, so the two can move in opposite directions, as `true`
  shows.
