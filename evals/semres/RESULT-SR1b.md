# SR1b result: in the real regime, similarity doesn't steer the walk to the answer

*21 Nov 2026, james. Registration: REGISTERED-SR1b.md (725395b). $0, 2 min. Output: out/sr1b.{txt,json}.*

**FAIL.** No arm ranks the answer in the top 5 in any case, on any of the 4 fresh seeds. The gate held, with Monte
Carlo against exact within 1.44 s.d.

| | struct | sem | comb (β = 8.7) | comb + direction memory @25 |
|---|---|---|---|---|
| Seeds with a in the top 5 (A / B / C / D) | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| Median rank of a, 16 world-cases | 11 | — | 21 | — |

## What it shows

- **The crossing is now cheap, and that doesn't help.**
  - The median crossing costs 1.3–2.4 nats per case type (SR1: 6–28).
  - Yet comb ranks a worse than structure alone: a median of 21 against 11.
  - At MuSiQue's slope, the cos spread among a passage's neighbours (about ±.3) is worth about ±2.6 nats. That's the
    same size as the crossing, so similarity reshuffles neighbours as much as it prefers the chain.
- **It's the vector deciders' failure, reproduced.** bill's SR-J measured the same thing on real MuSiQue: cos picks the
  true hop 2 in 22–62% of cases. Hop 2 looks *less* like the question than the best distractor (.559 against .616).
- **Direction memory still raises hit-by-25 at a in 16 of 16**, by less than in SR1, as predicted. It doesn't lift a into the top 5.
- **The chain formula under-predicts by about 2×** (median 2.03, range 1.3–3.3), as predicted for a softer world with
  more side paths. My bound of ≤ 1.5 was too tight.

## What the theory needs: bill's SR-J (#59)

Jev, reading hop 1 and choosing among 19, takes the true hop 2 **97%** of the time. As a conductance:
- **About 1 nat per cos unit for similarity**, against the vectors' Bayes 8.7.
- **+3.7 nats [3.3, 4.1] for "this is the next hop"**, which no cosine explains.

So a real decider's resistance per hop is mostly **relational**: does v hold what the read passage leads to? It isn't
similarity. In the generator that's the link's relation r_e matching the hop the question needs (r1 out of s, r2 out of
b), which the world knows exactly.

## Postmortem

- *Predicted:* B passes, C passes more weakly, D fails. **All wrong but D.** Calibrating the slope and the gap to MuSiQue
  reproduced MuSiQue's own finding: similarity doesn't find hop 2. A $0 look couldn't have shown it without a run,
  since the worlds were fresh by design.
- *Constants:*
  - β = 8.7 and the gap .146 are measured (bill).
  - ATYPE = 0.8605 is bisected to the gap on discarded seeds.
  - Noise stays at SR1's 1.0, which is the one world parameter not calibrated.
- *Next (SR1c, $0, registered before running):* the carry-over Sirsh asked for, using Jev's measured conductance.
  - Each link gets c = exp(1.0·cos) · exp(3.7·[r_e is the relation the next hop needs]), on fresh seeds.
  - **Prediction:** a reaches the top 5 in B and C in at least 3 of 4 seeds.
  - **Second prediction:** the chain formula then prices the walk. Reach ≈ (1−α)²·share·share·Q, with each share set by
    the 3.7 nats against the hop's competitors.

## Correction check: the calibration block (21 Nov, after RESULT-SRK's correction)

SR1b's β (8.7) and hop gap (.146) came from MuSiQue dev questions 1–200 in file order, and that block contains the easy
first 40. bill reran the measure on questions 201–1252 (`out/srj-look-blocks.txt`): β 9.3, gap .688 − .584 = .104.
`sr1b_blocks.py` (unregistered sensitivity, $0) re-bisects ATYPE to the narrower gap (.9573 against .8605) on calib's
discarded seeds and reruns SR1b unchanged on its own seeds, with output in `out/sr1b-blocks.txt`.

**The FAIL holds: 0 of 16 world-cases put a in the top 5, as before.** Median crossings fall by about 0.1–0.2 nats (B
1.34 → 1.17, C 1.75 → 1.55), so the answer is a little cheaper to reach. That isn't enough to move a single rank into
the top 5. Similarity-priced conductance fails on MuSiQue at large, not only on its first block.
