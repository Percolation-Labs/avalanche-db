# SR-BN: Jev can name the bridge from a list of phrases, and stepping through that one name beats the sum of keys

*21 Nov 2026, james (namer) and bill (matcher). Registered in `REGISTERED-SRBN.md` (#71, with amendment 1) before
stage 0. Jev spend: $0.0006 for stage 0 and $0.0449 for the wave (599 requests through `ask_many`, cap $0.25).
Outputs: `out/srbn-stage0.txt`, `out/srbn-fresh.txt`, `out/srbn-names-fresh.json`, `out/srbn-name-fresh.json`.*

**Versions.** percolate-core 0.2.15 (Jev), bge-small-en-v1.5, answerdotai/answerai-colbert-small-v1 via pylate (for
`cbq`). MuSiQue answerable 2-hop dev, positions 600–899 of SR-KB's seed-1341 permutation, unscored before this run.

## Namer half (james)

**Naming.** The read's door keys contain the bridge in .897 of questions, a median of about 22 phrases.

| namer | picks a bridge key |
|---|---|
| **Jev** (one request over the phrases) | **.697** |
| cosq, bge cos(question, key) | .147 |
| rare, the rarest key | .063 |
| cbq, a-ColBERT MaxSim(question, key) | .053 |

Naming accuracy `jev − cosq` is **+.550 [+.493, +.610]**. Bridge keys use the loose word-set test (amendment 1), so
every namer's accuracy is a little generous.

**Hop 2 (top-1), stepping lexically through the named key** (ties broken by k, then qr):

| arm | top-1 | top-3 | MRR |
|---|---|---|---|
| k (SR-K's sum, no naming) | .587 | .790 | .711 |
| **jev (Jev names, lexical step)** | **.680** | .863 | .784 |
| cosq | .520 | .757 | .662 |
| cbq | .483 | .733 | .635 |
| rare | .587 | .790 | .711 |
| *ceiling_k (gold names)* | *.720* | *.877* | *.811* |
| jev_pass (Jev picks the passage outright) | .843 | .960 | .902 |

- **Primary, `jev − k`: +.093 [+.060, +.130]. H-N passes.** A decision that names one identity beats summing every rare
  key.
- `jev − cosq`: +.160 [+.117, +.203]. A wrong cheap name is worse than no name: cosq and cbq fall below k.
- `ceiling_k − jev`: +.040 [+.017, +.063]. Jev's naming reaches most of the gold ceiling. The 30% it names wrong cost
  only .04. Counted afterwards at $0 (`srbn_wrong.py`, `out/srbn-wrong.txt`, bill's suggestion):

  | Jev's name | n | hop-2 top-1 |
  |---|---|---|
  | right (a bridge key) | 209 | .789 |
  | wrong, and no option shares it | 62 | .419 |
  | wrong, but hop 2 shares it | 17 | .765 |
  | wrong, and only lures share it | 12 | .000 |

  Most wrong names (62 of 91) are shared by no option, so the step falls through to k's tie-break. Only 12 send the
  walk to a lure. A wrong name is mostly harmless because the lexical step can tell when it's unused.
- `jev − jev_pass`: **−.163 [−.220, −.107]**. Jev reading the passages outright stays well ahead.

**Cost.** The naming request is about 840 characters per question (question, read, phrases), against about 10,000 for the
passage request. That makes it **about 8% of the input**. Jev's naming and then a free lexical step gets .68. Jev's
passage choice gets .84 for about 12× the tokens. Neither touches a vector beyond qr's tie-break.

**Predictions against outcomes.**
- Jev names a bridge .60: it was **.697**, higher.
- `jev` .63 with `jev − k` +.06 as a coin flip: it was **.680** and +.093, passing clearly.
- `jev_pass` about .85: it was .843. Right.
- `jev − jev_pass` clearly negative: right (−.163).

## Matcher half (bill)

*`srbn_match.py`, outputs `out/srbn-match-fresh.txt/json`. $0. The same 300 questions and the same Jev key K per
question. The models are mixedbread-ai/mxbai-edge-colbert-v0-17m (`x`) and answerdotai/answerai-colbert-small-v1
(`a`), via pylate on CPU. Each scores the 19 options against K alone.*

| arm (K = Jev's named key) | top-1 | top-3 | MRR | | gold ceiling (K = hop 1's answer) | top-1 |
|---|---|---|---|---|---|---|
| `m_x`, 17M ColBERT, on demand | .643 | .797 | .741 | | `g_x` | .807 |
| `m_a`, 33M ColBERT | .673 | .820 | .765 | | `g_a` | .827 |
| `m_lex`, K's words in v | .640 | .837 | .755 | | `g_lex` | .757 |
| `m_title`, title = K, then words | .643 | .837 | .757 | | `g_title` | .770 |
| *james's lexical step `jev`, for reference* | *.680* | | | | | |

- **Matcher primary, `m_x − m_title`: +.000 [−.043, +.043]. It fails.** Given the same named key, the 17M token matcher
  ties the best lexical second stage exactly.
- `m_a − m_x`: +.030 [−.010, +.070]. The 33M model doesn't clearly pay.
- `m_x − k`: +.057 [−.007, +.117]. That's not a clear gain over the door alone. james's lexical step through the same
  key does pass (+.093).
- `m_x − jev_pass`: −.200 [−.263, −.140].
- Gold ceiling, `g_x − g_title`: +.037 [−.003, +.077]. The 17M model's edge with the true name is smaller than the 33M's
  in SR-CB.
- **Unregistered, paired against james's lexical step `jev` on the same questions:**
  - `m_x − jev`: −.037 [−.093, +.017].
  - `m_a − jev`: −.007 [−.057, +.047].
  - `m_title − jev`: −.037 [−.080, +.007].
  - `g_a − g_title`: +.057 [+.020, +.097]. The 33M twin edge with the true name holds here, but smaller than SR-CB's
    +.087.

**Prediction against outcome.** I predicted `m_x − m_title` at about +.06, smaller than the gold-name margin. It was
.000. A wrongly named key (30%) hurts every matcher alike, as predicted. But with the right key, the 17M model's twin
edge is only +.04 even at the ceiling, and naming errors wash that out.

**Cost, which answers Sirsh's question.** `m_x` encodes the 19 options and K on demand in **0.087 s per question** on
CPU, with no index. But it doesn't beat the free lexical step. **With naming in place, no token index is needed:** the
14–23× storage of a ColBERT index (SR-CB) buys nothing measurable here. The only ColBERT gain left is the 33M model's
gold-name twin edge (+.06), and real naming doesn't yet deliver it.

## What it means for REM-1341 (namer half)

- **The library's working shape is now propose, name, step.** The lexical door proposes the read's rare keys (free).
  One short decision names the identity (8% of a passage judgment). A step through that identity (lexical here, with
  bill's token matcher to follow) then finds hop 2.
- **Naming is not a vector operation.** Every cheap namer (bge, ColBERT, rarity) picks the bridge at .05–.15 out of
  about 22. The question names the bridge's *role* ("the actor portraying ..."), not the bridge itself, and cosine scores the
  role's topic.
- **Where Jev's .84 still comes from.** Jev's passage choice is +.12 above even the gold-named lexical step (.72), which
  is the second-relation share K-MISS supposed. That's now on the same draw.

## Postmortem (namer half)

- **What went right.** The $0 namer look (seen 300) priced the cheap namers before any spend, so the registration
  predicted a pass only for Jev. Stage 0 used four questions outside the set. The wave stayed under its estimate's cap,
  and bill caught the `ask_many` rule before stage 0.
- **What I got wrong.** I under-predicted Jev's naming (.60 against .70). I anchored on the size of the list (about 22).
  But the question constrains the role tightly, so the list is effectively much shorter for a reader.
- **Scope.** Given the entry (gold hop 1 as read), in-pool, MuSiQue 2-hop only, one wording. The named step isn't yet
  a walk: in a walk the read passage is itself chosen, and a wrong hop 1 makes every name wrong.

## What it means (matcher half)

- **The step is lexical.** Once Jev names the key, stepping through it lexically, with SR-K's sum to break ties (james,
  .680), is as good as or better than every token matcher (.643–.673). So the working pipeline is entirely lexical
  except for one short decision: the door proposes, Jev names, and the door steps.
- **ColBERT's one measured advantage** is separating twins when handed the true name: the 33M model by +.06 over
  title-first words, and the 17M by +.04, not significant. It doesn't survive real naming. That's worth revisiting only if a
  namer gets close to the ceiling. Even then the 17M on-demand route (0.09 s per question, no index) is the cheap way
  to buy it, not a stored index.
- **For Sirsh's cost question:** this readout justifies no late-interaction index in production.

## Postmortem (matcher half)

- **What went right.** The registration put the matcher against the best lexical second stage under the *same* named
  key, so the null is clean. The on-demand cost was measured, not assumed.
- **What I got wrong.** I predicted +.06. I carried SR-CB's 33M gold-name margin (+.087 over title-first words) over to
  the 17M model and to real naming without discounting either. SR-CB had already shown the 17M model .04 below the 33M at
  the ceiling. The lesson is the one from SR-CB: put the gaps you've already measured into the prediction.
- **Scope.** As the namer half. The tie-break matters: james's step breaks ties by k, and the matchers by qr. Part of
  `jev`'s .037 lead over `m_title` may be the tie-break, not the step. That's untested.
