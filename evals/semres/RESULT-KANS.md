# K-ans: keeping only the reads that answer turns kappa's BEAM loss into a tie and keeps its MuSiQue gain

*22 Nov 2026, james. Kappa round 7. Registered in `REGISTERED-KANS.md` (#89, reviewed by bill before any Jev call). The
script is p8-subsystems `meta/lab/worlds/kappa_ans.py` (branch `james/kappa-ans`, f2875e184 + the review commit),
run in bill's round-4/5 harnesses unchanged. Jev spend: $0.016 for stage 0 and $0.110 for the runs ($0.050 BEAM, $0.060
MuSiQue), under the $0.40 cap. Outputs: `out/kans-stage0.txt`, `out/kans-beam.txt`, `out/kans-mq.txt`.*

**Versions.** percolate-core 0.2.15 (Jev), with D6 doors, prompt P1 and presentation F2. These are BEAM HELD-OUT (601
pages) and MuSiQue HELD-OUT (286 pages), replayed pages with fixed reads.

**Validation.** K0 and K7 come from the rounds' cache, unchanged, and reproduce the published numbers exactly:
- BEAM: K0 .692, K7 .669, and K7 − K0 −.022 [−.040, −.001];
- MuSiQue: K0 .768, K7 .805, and K7 − K0 +.037 [+.008, +.068].

## Registered result (NDCG@10, paired by question)

| | K0 (no state) | K7 (sentences of all reads) | **K-ans (sentences of the reads that answer)** |
|---|---|---|---|
| BEAM HELD-OUT | .692 | .669 | **.702** |
| MuSiQue HELD-OUT | .768 | .805 | .802 |

| paired difference | BEAM | MuSiQue |
|---|---|---|
| **K-ans − K7** | **+.032 [+.008, +.052] (primary)** | −.003 [−.032, +.022] |
| K-ans − K0 | +.010 [−.008, +.029] | +.034 [+.013, +.056] |
| K7 − K0 (rounds 4 and 5, reproduced) | −.022 [−.040, −.001] | +.037 [+.008, +.068] |

- **H-K passes.** On BEAM, K-ans beats K7 by +.032. It recovers K7's loss entirely: it's level with no state at all
  (+.010, CI over 0).
- **On MuSiQue it keeps K7's gain.** K-ans is +.034 over K0, about K7's +.037, and K-ans − K7 is −.003. Filtering didn't
  drop the chain's passages that K7 relied on. bill's wording ("or identify something the answer depends on") was
  meant to protect exactly that.
- **One state now works on both corpora.** K7 helped one and hurt the other. K-ans helps MuSiQue and is neutral on BEAM.

**The filter.**
- BEAM gold share: all reads in the waves .115, and the kept reads **.181**, a 1.6× enrichment. Both are pooled over
  reads, not averaged per wave.
- **That's a different read set from #88's .008–.045.** #88 counted the 65 whole recorded walks in `walks-1m.jsonl`:
  up to 10 waves and about 500 reads each. The replay pages here are the rounds' pages: at most 4 rounds per question
  (≤ 150 reads), early in the walk, and kept only where some door leads to gold (`any(gains)`). Early, gold-reachable
  rounds are richer in gold. So #88's "95–99% non-gold" describes whole walks, and .115 describes these pages (bill's
  review).
- That's below #88's 3.5× price from search-order pools. Jev's per-read relevance is noisy at walk base rates.
- The max REL p per wave has quartiles .28 / .43 / .51 / .62 / .95 on BEAM (83 waves) and .24 / .47 / .53 / .64 / .90 on
  MuSiQue (77). In most waves Jev isn't confident: the median best read is about .5. So many kept reads are the "least
  bad" (bill's note), and the gain comes from a modestly cleaner state, not a gold-only one.

**Predictions against outcomes.**
- BEAM K-ans − K7 about +.02 with a CI touching 0: **+.032 with a CI above 0**, better than predicted.
- K-ans − K0 about 0 on BEAM: right (+.010, n.s.).
- Kept-read gold share about .10 against about .03: the shares were higher (.181 against .115), because these pages
  are early, gold-reachable rounds, not whole walks (see the filter section). The enrichment was 1.6×, not 3.5×.
- MuSiQue K-ans − K7 about −.01 to +.01: right (−.003). K-ans − K0 about +.03: right (+.034).

## What it means

- **What kappa should carry is the reads that answer, not everything read.** On BEAM, a state of related non-gold sentences
  (K7) cost walks. Filtering it through one short Jev request per wave removes the loss. SR-MO3 predicted this at one
  step: related non-gold `found` doesn't help, and gold content does.
- **For the product.** K-ans is one extra Jev request per wave over that wave's reads, a small fraction of the walk's
  own door requests. If kappa stays on by default, K-ans is the safer state across corpus types. This is a replay
  result, though, not a live walk, so the live walk's reads would also change.
- **The ceiling is unreached.** The enrichment is only 1.6×. A better filter (a threshold-free rule that keeps more than
  one read when several answer, or none when none does) is the obvious next step. That's untested.

## Postmortem

- **What went right.** The $0 look (#88) found why K7 fails on BEAM before any design. The dry run proved the re-keying
  matched bill's harness (0 uncached K0/K7) before any spend, and stage 0 ran on both corpora. bill's two review notes
  (via parity, and the max-p readout) cost nothing and made the filter's weakness visible.
- **What I got wrong.** I priced the enrichment from search-order pools (3.5×), and it came in at 1.6× on walk pages.
  The primary still passed, which means the gain is less about gold share than I'd assumed. A partly cleaner state
  already helps. I can't say from this which part of K-ans does the work (fewer sentences, or more relevant ones). A
  length-matched random-subset control (one random read per wave) would separate them. **That's the first follow-up.**
- **Scope.** Replayed pages (fixed reads), HELD-OUT only, one wording, one keep rule (argmax per wave), two corpora.
