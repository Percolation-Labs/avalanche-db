# SR-BT: Jev reading only the named twins adds +.12. The gap left to Jev's full choice is mostly failed names

*21 Nov 2026, james. Registered in `REGISTERED-SRBT.md` (#72; amendments 1 and 2 before the wave). Jev spend:
$0.00015 for stage 0 (stage0t; stage 0 itself was all cached) and $0.0439 for the wave (536 wave-1 and 75 wave-2
requests through `ask_many`, cap $0.25). Outputs: `out/srbt-stage0.txt`, `out/srbt-stage0t.txt`, `out/srbt-bw.txt`,
`out/srbt-bw.json`.*

**Versions.** percolate-core 0.2.15 (Jev) and bge-small-en-v1.5. MuSiQue answerable 2-hop dev, positions 904–1171 of
SR-KB's seed-1341 permutation (268 questions, shared with SR-BW's walk task). Gold hop 1 is the read.

**Serves.** Sirsh asked what Jev's passage choice uses beyond the name. The pricing said it was the second relation, inside
the named twins. This tests whether a Jev request over only those twins buys it, at a fraction of a full passage request.

## Result

| arm | top-1 hop 2 |
|---|---|
| k (SR-K's sum) | .549 |
| jev (Jev names, lexical step; SR-BN) | .649 |
| **nt (name, then Jev over the named twins only)** | **.769** |
| nt_cut ($0 approximation: full-request p restricted to the twins) | .780 |
| jev_pass (Jev picks among all 19) | .884 |
| *ceiling_k (gold names, lexical step)* | *.687* |

- **Primary, `nt − jev`: +.119 [+.075, +.168]. H-T passes.**
- Within the 75 questions with twins: `nt − jev` +.427 [+.280, +.573] (.720 against .293).
- `nt − jev_pass`: −.116 [−.168, −.063] overall, and −.093 [−.173, −.027] within twins (.720 against .813).
- `nt − k`: +.220 [+.164, +.276].
- `nt − nt_cut`: −.011 [−.030, +.004]. A request over the twins alone behaves like the full request restricted to them,
  so Jev scores options close to independently.
- Jev named a bridge key .743 of the time (SR-BN: .697).
- **Cost.** Wave 2 read 0.89 passages per question, against 19 for `jev_pass`. With the naming request, nt's Jev input is
  roughly an eighth of `jev_pass`'s (SR-BN measured the naming request at about 8% of a passage request).

**Where the remaining gap is** (by the size of the named set S, not registered, descriptive):

| \|S\| | n | Jev named a bridge | k | jev | nt | jev_pass |
|---|---|---|---|---|---|---|
| 0 (no option shares the name) | 48 | .083 | .375 | .375 | .375 | **.896** |
| 1 | 145 | .890 | .759 | .924 | .924 | .917 |
| 2+ (twins) | 75 | .880 | .253 | .293 | .720 | .813 |

- **Most of nt's deficit is the |S| = 0 questions.** Jev's name there is almost always wrong (.083). nt falls back to k
  (.375), while Jev's full choice gets .896. That's about 25 of the 31 questions between nt and jev_pass.
- **Where the name leaves one passage,** the free lexical step matches Jev's full choice (.924 against .917).
- **Within twins,** Jev over the twins alone (.720) is still below Jev over all 19 (.813). The cut approximation agrees
  (overall −.011), so the loss isn't the request's shape. My guess is that it's twins where hop 2 isn't among them,
  since S holds options sharing the *named* key and the name can be a near miss. That's untested.

**Predictions against outcomes.**
- nt about .78: it was .769. Right.
- `nt − jev` +.09 or more: it was +.119. Right.
- `nt − jev_pass` about −.05: it was −.116. The gap was twice what I predicted, because the pricing set had fewer
  failed names. SR-BN's 300 had 67 k-fallbacks at .433; here 48 at .375, against jev_pass's .896.
- `nt − nt_cut` within ±.03: right.
- Naming .65–.75: right (.743).

## What it means

- **Jev's passage choice uses the name and the second relation, and it recovers when naming fails.** The cheap
  pipeline recovers the second relation (twins, +.43 within) at less than one passage per question. What it doesn't
  recover is the |S| = 0 case, where Jev's name points nowhere and Jev reading passages finds hop 2 anyway, .896 of the
  time.
- **That |S| = 0 signal is free and visible before any passage request.** No option shares the name. The next registered
  step is the obvious one: when |S| = 0, send Jev's full passage request. On these numbers that would reach about
  .86 (.769 plus about 25/268), with Jev reading about 0.18 × 19 + 0.89 ≈ 4.3 passages per question instead of 19.
  That's post-hoc arithmetic on this set, so it needs a fresh draw. Dev 2-hop is used up, so it needs 3-hop questions
  or another split.
- bill's SR-BW shows the same shape in a full walk (nameset − name +.049 on both hops).

## Postmortem

- **What went right.** The $0 look on cached p's predicted nt within .01 and caught that Jev's extra lives in twins.
  Stage 0 had no twins, so the wave-2 code path was untested. I caught that and added a twin smoke test as a registered
  amendment before the wave, rather than discovering a bug in the paid run.
- **What I got wrong.** I under-predicted the gap to jev_pass. The pricing set's fallback rate wasn't the registered set's.
  The lesson: price a fallback branch's *size* as well as its accuracy, and give the prediction a range wide enough to
  cover a different mix.
- **Scope.** Given gold hop 1. In-pool, MuSiQue 2-hop, one wording per task. The |S| table is descriptive, and the
  fallback rule is a hypothesis for the next registration.
