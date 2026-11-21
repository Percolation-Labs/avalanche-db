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
  only .04. I haven't measured why; one guess is that a wrong key that no option shares falls through to k's tie-break.
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

*To follow: m_x, m_a, m_lex and m_title given Jev's K, from `out/srbn-names-fresh.json`.*

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
