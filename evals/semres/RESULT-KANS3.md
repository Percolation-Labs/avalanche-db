# K-ans 3: on MuSiQue a random one-read-per-wave state keeps about half of kappa's gain, not significantly

*22 Nov 2026, james. Registered in `REGISTERED-KANS3.md` (#89) before the run. Script `kappa_ans.py mq --rnd`, with the
same seed rule as K-ans 2. Jev spend: $0.0413 (272 door requests). Output: `out/kans3-mq.txt`.*

## Registered result (MuSiQue HELD-OUT, 286 pages, NDCG@10 paired by question)

| state | NDCG@10 | − K0 |
|---|---|---|
| K0 (none) | .768 | |
| K7 (all reads) | .805 | +.037 [+.008, +.068] |
| K-ans (Jev's argmax read per wave) | .802 | +.034 [+.013, +.056] |
| **K-rnd (a random read per wave)** | **.785** | **+.017 [−.005, +.040] (primary)** |

- **H-K3 fails.** A random one-per-wave state doesn't keep a significant gain on MuSiQue. Its point estimate is about
  half of K7's or K-ans's.
- K-ans − K-rnd is +.017 [−.009, +.046], and +.018 [−.010, +.048] within the 272 pages with a differing pick. That's
  positive but not significant, so on MuSiQue we can't rule out that Jev's pick matters, and can't show it either.
- K-rnd − K7 is −.021 [−.057, +.014].

**Predictions against outcomes.** K-rnd − K0 about +.02, a coin flip: +.017 with a CI touching 0, as predicted. K-ans −
K-rnd about +.015: +.017, n.s.

## Across K-ans, K-ans 2 and K-ans 3

| − K0 | BEAM (601) | MuSiQue (286) |
|---|---|---|
| K7, all reads | −.022 [−.040, −.001] | +.037 [+.008, +.068] |
| K-ans, Jev's pick per wave | +.010 [−.008, +.029] | **+.034 [+.013, +.056]** |
| K-rnd, a random pick per wave | +.006 [−.010, +.023] | +.017 [−.005, +.040] |

- **Only K-ans is never worse than no state, and significantly better on one corpus.**
  - K7 loses on BEAM.
  - K-rnd is neutral on BEAM and not significant on MuSiQue.
  - K-ans is neutral on BEAM and keeps MuSiQue's full gain.
- **The mechanisms differ by corpus.** On BEAM, the fix is length: K-ans 2 showed the filter adds nothing there and
  picks less gold than random. On MuSiQue, we can't rule out that the sentence matters: K-ans − K-rnd is +.017, n.s. MuSiQue's gain plausibly
  needs the chain's passage in the state, and a random read often isn't it.
- **The hypothesis for Sirsh to decide** (research phase, not a product change): K-ans is the state that helps where
  kappa helped and stops hurting where it hurt, at one extra short Jev request per wave. The cheaper random state is
  safe on BEAM but gives up about half of MuSiQue's gain, and that difference is itself not significant at 286 pages. To
  settle it would take a larger MuSiQue replay or a live walk.

## Postmortem

- **What went right.** Three registered steps, each reviewed, cost $0.22 in all. Each was triggered by the previous
  one's open mechanism, and the second reversed the first's reading before it reached Sirsh. The cross-corpus table is
  the honest summary.
- **What to watch.** These are replayed pages with fixed reads, not live walks. A live K-ans walk would read
  differently. The MuSiQue contrasts are underpowered at 286 pages (K-ans − K-rnd's CI spans −.009 to +.046).
