# W2 stage 0: fusing Jev's P with the per-target vote picks narrow gold-free doors; fail, no Jev

*19 Nov 2026, bill. Registered first (REGISTERED.md f2d17fe, amended before scoring 4b5f789). $0. Output: `w2.txt`.*

These are the first doors of recorded test waves (every wave with a gold door), using V1's rows. Each fusion combines
two rankings by reciprocal rank (60): Jev's P and X.

| test | P | P ⊕ vote | P ⊕ learned vote | P ⊕ shuffled vote | P ⊕ narrow | vote alone |
|---|---|---|---|---|---|---|
| cards (147) | **.687** | .190 | .320 | .354 | .095 | .136 |
| PR titles (95) | .126 | .116 | .200 | .189 | .042 | **.232** |
| MuSiQue (149) | **.591** | .262 | .262 | .242 | .195 | .081 |

The cells are the share of waves where the first door has gold behind it. Read-weighted (b) follows the same pattern
(cards .384 → .139, MuSiQue .416 → .221), with one exception: PR titles goes .020 → .062.

**Verdict: fail.** P ⊕ vote loses .497 on cards and .329 on MuSiQue, and gains nothing on PR titles. Stage 1, the live
Jev walk, doesn't run.

## Postmortem

- **Per target is not width-neutral for a decision, only for a comparison.** V1's measure compares doors within 2× of
  each other's width, and there the vote marks gold well (.73–.83). Dividing the mass by width to drop that pairing
  overcorrects. A one-target door next to a read passage holds concentrated mass, so the per-target vote ranks narrow
  doors first, and gold doors are wider on average. P ⊕ narrow, the width control, is as bad or worse. So the drop is
  width again, in the other direction. I picked this variant from evals/structural, where its all-pairs AUC was already
  .56–.69. I should have read that as a warning. A batch's first door is decided over all pairs, not width-matched ones.
- **Fusion by reciprocal rank lets a weak ranker veto a strong one.** When X is close to anti-informative across
  widths, the fused order loses most of P's lead on cards and MuSiQue. W1's summed vote failed more mildly, for the
  opposite reason: it rewards width.
- **PR titles stands out again.** The vote alone puts gold first .232 against Jev's .126. Read-weighted (b) is .232
  against .020, so the first door Jev picks on PR titles rarely carries gold per read. The learned θ also helps the
  fusion there (.116 → .200). This was not a registered arm's pass condition, so it is a lead, not a result: on the graph
  where Jev's encoding gap is largest, structure alone already chooses better.
- **What a width-neutral decision statistic needs:** the vote compared against doors of similar width, for example the
  door's vote percentile among the batch's doors in its width class. That fixes the pairing V1 measured instead of
  dividing it away. It would be a new registration, scored on dev first, not a re-run here.
