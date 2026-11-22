# K-ans 2: the BEAM gain is the shorter state, not the filter. A random read per wave does as well, and picks more gold

*22 Nov 2026, james. Registered in `REGISTERED-KANS2.md` (#89, reviewed by bill before any Jev call, with his
differing-pick readout added before the run). Script: p8-subsystems `meta/lab/worlds/kappa_ans.py --rnd`. Jev spend:
$0.0525 (589 door requests). Output: `out/kans2-beam.txt`.*

**Question.** Is K-ans's BEAM gain over K7 (+.032) the relevance filter, or just a shorter state? The control, K-rnd,
keeps one random read per wave (index sha256("20261122" + wave id) mod size), with the same count, format, cap and
order.

## Registered result (BEAM HELD-OUT, 601 pages, NDCG@10 paired by question)

| state | NDCG@10 | gold share of kept reads |
|---|---|---|
| K0 (none) | .692 | |
| K7 (all reads) | .669 | .115 (all wave reads, pooled) |
| K-ans (Jev's argmax read per wave) | .702 | .181 |
| **K-rnd (a random read per wave)** | **.698** | **.229** |

| paired difference | NDCG |
|---|---|
| **K-ans − K-rnd (primary)** | **+.004 [−.010, +.018]** |
| K-rnd − K7 | **+.029 [+.004, +.047]** |
| K-rnd − K0 | +.006 [−.010, +.023] |
| within the 589 pages where some earlier pick differs (bill's readout) | +.004 [−.011, +.020] |

- **H-K2 fails.** Jev's relevance filter adds nothing over a random read per wave.
- **The gain is length.** K-rnd beats K7 by +.029, nearly all of K-ans's +.032. A state of one sentence per wave, any
  sentence, removes K7's BEAM loss.
- **It isn't dilution.** 589 of 601 pages have an earlier wave where the two picks differ, and the contrast there is the
  same (+.004).
- **Jev's filter picked less gold than chance.** K-rnd's kept reads are .229 gold against K-ans's .181. The per-wave
  pick weights small waves (seed waves are small and gold-rich) more than the pooled .115 does. So the fair baseline for
  K-ans is .229, and Jev's argmax falls *below* it. Asked "does this passage give information needed to answer…" over
  BEAM chat turns, Jev's top pick is, if anything, anti-informative about gold. That fits the median max p of about .5:
  it's guessing.

**Predictions against outcomes.**
- K-ans − K-rnd about +.015, a coin flip: +.004, a null.
- K-rnd − K7 about +.015 (half the gain is length): **+.029, all of it**.
- K-rnd gold share about .115: .229. I used the pooled base rate, but the random pick is per wave.

## What it means (with K-ans, #89)

- **Correcting #89's reading.** K-ans's result stands as measured (+.032 over K7), but its mechanism is a shorter state,
  not relevance. Kappa's BEAM loss came from K7 *saying too much*: a long list of related non-gold sentences. Cut to one
  sentence per wave, the loss disappears, whichever sentence is kept.
- **That's consistent with SR-MO3.** At one step, related non-gold `found` narrowed the gold's lead. More of it
  presumably narrows it more. The fix is less of it, and choosing it well doesn't help.
- **For the product: cap kappa's length per wave.** It needs no extra Jev request: the cheapest form of K-ans is a
  random (or first) read per wave. On MuSiQue, K-ans kept K7's gain (#89). Whether a *random* one-per-wave state also
  keeps it is untested, and that's the check before recommending it. MuSiQue's gain may need the right sentence, where
  BEAM's loss only needed fewer.

## Postmortem

- **What went right.** The control was registered after a passing primary, because the first postmortem couldn't
  separate the mechanisms, and it reversed the reading for $0.05. bill's differing-pick readout ruled out dilution.
  Reporting gold share for both arms showed the filter is worse than chance, which neither of us predicted.
- **What I got wrong.** I credited K-ans's gain to relevance in #89's "What it means" before the length control ran. I
  flagged it as untested, but the headline still said "the reads that answer". I also compared kept-read gold against a
  pooled base rate, which a per-wave pick doesn't face. The lesson: a filter's baseline is a random pick under the same
  sampling, not the population rate.
- **Scope.** BEAM HELD-OUT replay pages, one seed, one wording.
