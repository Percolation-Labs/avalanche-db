# SR-J-R result: Jev's next-hop term survives a random draw (γ 3.2), but its similarity slope is about 4× SR-J's

*21 Nov 2026, bill. Registered at 094589b before any Jev call; james reviewed it. Stage 0 (4 questions) cost $0.00058.
Stage 1 (40 questions) cost $0.00430. **Total $0.0049.** Output is in `out/srjr-stage0.txt` and `out/srjr-n40.txt`.
Per the agreement with james, the per-case JSON is held back until his warp is registered, because these 40 are its
held-out test.*

**Serves.** RESULT-SRK's correction: SR-J's fit came from MuSiQue's easy first block. Every downstream use (SR1c,
THEORY-SR, the coming warp) needs to know whether Jev's price holds on MuSiQue at large.

| | SR-J (first 40, the easy block) | **SR-J-R (random 40 from 41–1252, seed 20261121)** |
|---|---|---|
| γ, next hop (nats) | +3.77 [+3.39, +4.16] | **+3.24 [+2.79, +3.71]** |
| β_q, similarity (nats per cos unit) | +1.00 [+.13, +1.74] | **+3.79 [+2.20, +5.42]** |
| β_r when added | +.88 [−.03, +1.84] | +.81 [−1.00, +2.81] |
| Jev top-1, hop 2 | .97 | **.88** |
| cos(q + read) top-1 | .62 | .35 |
| search cos top-1 | .20 | .40 |

**The bar passes.** γ's CI overlaps SR-J's and its lower bound (2.79) is above 2.0. The next-hop term is still about 3
nats on MuSiQue at large, so it falls by about half a nat off the block.

**Predictions.** All held: γ in 2.5–4, Jev top-1 in .75–.90, and cos(q + read) about .40 (it was .35). Jev's lead over
the best vector decider is +.48 (.88 against search cos .40), against +.35 on the block.

**Not predicted: β_q is about 4× SR-J's, and the intervals don't overlap.** Off the easy block, Jev leans on similarity to
the question at 3.8 nats per cos unit. That's still well under the vectors' Bayes slope (8.7–9.3), but not "≈ 1". A
plausible reading, unchecked: on the easy block the true hop already led on cosine for many questions, so γ absorbed
what β carries elsewhere. So THEORY-SR's "β ≈ 1" for MuSiQue is a block artifact. The corrected statement is that Jev's
conductance on MuSiQue is about 3.8 nats per cos unit plus about 3.2 nats for the true next hop.

**What this changes.**
- SR1c and THEORY-SR used β 1.0, γ 3.7. They should be restated at β 3.8, γ 3.2. A higher β makes similarity matter
  more in Jev's walk, which moves it part of the way toward the vector walk that failed in SR1b.
- Whether SR1c's carry-over survives at these values is a $0 rerun of SR1c's code. james owns SR1c, so I've asked him.
- The warp (james, REM-1341) has a sharper target: bend cosine toward a price whose similarity term is about 3.8 and
  whose next-hop term is about 3.2.

**Caveats.**
- 40 questions; the β CI is wide (2.2–5.4).
- The read passage is the gold hop 1, as in SR-J.
- Cards weren't redrawn. They were also the first 40 in file order (james's #62 review note).

**Postmortem.**
- **What went right.** A $0.005 redraw settled a question that three downstream results depended on. Registering it,
  stage 0 first, and james checking the draw indices kept it clean.
- **What I got wrong.** I registered predictions only for γ and top-1, and gave none for β, although β is the term a
  block would most plausibly move. When a correction study reruns a fit, predict every fitted term.
