# L3 result: per-family weights let coherence be gamed

*19 Nov 2026, james. Registration: REGISTERED-L3.md (7c8a63d). $0, no Jev. Output: out/l3.txt, out/l3.json.*

**FAIL.** The bar had three chances, and none cleared. Cards broke the second condition: LC3 − LC is wholly below 0
there.

Test recall@5 beyond the seeds; differences are against L2's LC, with 95% bootstrap intervals:

| | cards | PR titles | MuSiQue |
|---|---|---|---|
| LC (L2) | .275 | .621 | .140 |
| **LC3 (family β, dev coherence)** | **.214, −.061 [−.102, −.023]** | .660, +.039 [−.008, +.089] | .135, −.005 [−.030, +.023] |
| LC3-shuf | .262, −.013 | .661, +.040 [+.011, +.072] | .135, −.005 |
| LC3-test | .228, −.047 | .666, +.045 [+.000, +.096] | .140, .000 |

Fitted β (e^β multiplies the family's step weight):
- cards: number −1, code −2, word −2, Beside +2.
- PR titles: number −2, phrase −2, Beside +1.
- MuSiQue: number −1, word −1.

Seven of the eleven fitted values sit at a grid edge, and the ascent changed direction between rounds.

**What it shows:**
- **More freedom let coherence rise without recall.** On cards, dev coherence went from 1561 to 1835, and test recall
  fell by .061. Raising Beside and suppressing code and word keys keeps the top 5 among adjacent cards, which are
  tightly joined to each other and rarely the answer.
- **Bill's question is answered: no.** On cards, K1 found that number keys mark found walks (AUC .71). Coherence
  pushed the number weight down. At this grain, the reward and the outcome point in different directions.
- **On PR titles the small gain isn't the join.** LC3-shuf gains as much as LC3, with an interval above 0. That's
  the same corpus-level setting L2 found, pushed further along Beside, not a question-specific signal.
- **So L2's three numbers are the honest ceiling for this reward.** Coherence works as a dreaming objective when the
  thing it shapes is coarse, but a finer warping needs a reward that coherence alone doesn't supply. That's the
  answer to REM-1341's warping question, for now: not from coherence by itself.

**Postmortem:**
- *Predicted:* little on cards, a Beside gain on PR titles, nothing on MuSiQue. The PR and MuSiQue parts held. I
  didn't predict harm on cards. I should have: K1 showed total coherence doesn't track found on cards (.56), and that
  is exactly when optimising it harder should overshoot.
- *Could a $0 look have stopped it?* Partly. Bill's suggested check, whether raising the number weight raises
  coherence on cards, was the fit's first step. It came out "no" in round 2, before any test score. I ran the
  registered design rather than stopping at it, and that was right once the design was registered. The lesson for
  next time goes in the design: make the cheap direction check a gate in the registration.
- *Constants:* the β grid and the 3-round cap were chosen here, and the fit hit their edges, so I've reported that
  and not chased it. Widening the grid would only let coherence move further from recall.
- *Next:* none on the warping from this reward. Coherence stays as the L2-level dreaming objective. A finer reward
  needs a signal that tracks found walks per question, which P3, P3b and L2's diagnostic found only on PR titles.
