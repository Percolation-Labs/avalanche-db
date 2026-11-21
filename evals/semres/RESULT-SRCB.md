# SR-CB: a small ColBERT can't find the bridge in the read passage, but given the bridge it finds hop 2 best of anything cheap

*21 Nov 2026, bill. REM-1341, on Sirsh's 21:19Z steer. Registered in `REGISTERED-SRCB.md` (with amendments 1 and 2,
both before scoring). $0, no Jev calls. Scripts: `srcb.py`, `srcb_cost.py`, `srcb_lexgb.py` (post-hoc). Outputs:
`out/srcb-fresh.txt/json`, `out/srcb-kb.txt/json`, `out/srcb-cost.txt`, `out/srcb-lexgb-fresh.json`.*

**Versions.** pylate (latest on 21 Nov, via uv) with answerdotai/answerai-colbert-small-v1 (`a`, 33M parameters, 96-dim
tokens) and mixedbread-ai/mxbai-edge-colbert-v0-17m (`x`, 17M, 48-dim). bge-small-en-v1.5 for the references. CPU on
this Mac.

**Task.** Given the gold hop 1 as read, rank the other 19 passages of the pool. Top-1 is hop 2. The 300 questions are
positions 300–599 of SR-KB's seed-1341 draw, unscored before this run.

## Result (registered set, 300 fresh questions)

| arm | what it scores against | top-1 | top-3 | MRR |
|---|---|---|---|---|
| `qr` (bge-small, reference) | question + read, one pooled vector | .397 | .620 | .554 |
| `k` (SR-K, reference) | shared rare keys, lexical | **.537** | .757 | .676 |
| `a_q` | question tokens | .287 | .513 | .446 |
| `a_qr` | question + read-passage tokens | .310 | .560 | .479 |
| `a_k` | key-phrase tokens, weighted 1/(df−1) | .420 | .633 | .560 |
| `x_qr` | question + read-passage tokens | .277 | .533 | .446 |
| `x_k` | key-phrase tokens | .360 | .543 | .502 |
| *`a_gb` (gold ceiling)* | *the hop-1 answer's tokens* | ***.807*** | *.950* | *.879* |
| *`x_gb` (gold ceiling)* | *the hop-1 answer's tokens* | *.767* | *.927* | *.852* |

Paired differences in top-1, with bootstrap 95% CIs:
- **Primary, `a_qr − qr`: −.087 [−.140, −.033]. H1 fails.** Token-level matching against the whole read passage does
  worse than bge-small's pooled text probe.
- `a_k − k`: −.117 [−.163, −.070]. ColBERT's soft key match falls short of the exact lexical one.
- `a_k − qr`: +.023 [−.033, +.080]. The keys in ColBERT are level with the text probe.
- `a_qr − k`: −.227 [−.287, −.167]. The gap to lexical stays open, so "ColBERT closes the gap" fails on both arms.
- `x_qr − qr`: −.120 [−.177, −.063]. `x_k − k`: −.177 [−.233, −.123]. The 17M model is .03–.06 below the 33M one.
- `a_q − a_qr`: −.023 [−.080, +.037]. Adding the read passage's tokens barely helps.
- `a_gb − a_qr`: **+.497 [+.433, +.557]**.

**Predictions against outcomes.**
- a_qr about .45: wrong. It was .31, below qr as james's amendment-2 note expected.
- a_k .45–.50: a little high. It was .42.
- Both below k: right.
- x within .05 of a: right on `qr` (−.03), and just outside on `k` (−.06).
- a_gb about .65: wrong the other way. It was .81.

## The post-hoc finding: given the name, ColBERT separates twins better than words do

The ceiling was registered as gold and as a sizing number, not a decider. It came out higher than predicted, so I added
a lexical ceiling on the same 300 questions *after* scoring. `srcb_lexgb.py` takes the fraction of the hop-1 answer's
words present in each option, with ties broken by qr. It's labelled post-hoc and isn't a registered pass.

| on the same 300 | top-1 |
|---|---|
| lexical, answer words in the option | .700 |
| `x_gb`, 17M ColBERT, answer tokens | .767 |
| `a_gb`, 33M ColBERT, answer tokens | **.807** |

- `a_gb − lex_gb`: **+.107 [+.063, +.147]**. `x_gb − lex_gb`: +.067 [+.027, +.107].
- **Why the words fall short.** Hop 2 contains the whole answer string in 89% of these questions. But in 31%, another
  option contains it too: a twin. Word overlap can't order twins, and ColBERT's mean of max token similarity does better
  there. These numbers don't show the mechanism. One guess is the title position or the answer's own context tokens. That's
  untested.
- James's lexical *key* ceiling (.713, K-MISS) is on SR-KB's 300, not these, so it isn't compared directly.

## What it means

- **Identity survives in ColBERT's token space.** Handed the bridge entity, a 33M CPU model ranks hop 2 first 81% of
  the time. Jev is at .88 on a different random 40. The vector-route failures today were never about whether vectors can
  match a name.
- **What fails is picking the bridge out of the read passage.** Every arm that doesn't know the bridge lands at .28–.54.
  ColBERT against the whole read passage (.31) is worse than pooling (.40), as K-MISS predicted: many weak token
  matches. ColBERT against the rare keys (.42) is worse than counting the same keys exactly (.54).
- **This agrees with K-MISS from the other side.** James priced naming the bridge at +.14 lexically, and the ColBERT
  ceiling says it's worth more if the matching is token-level. Both point at one decision: **which entity in the read
  passage answers hop 1?** That's a selection over a short list, the kind of choice our grammar gives Jev or a cheap
  decider. Then a small token matcher can do the walking.
- **For REM-1341's library:** the working operations are a lexical door to propose candidates, a decision to name the
  bridge, then a token MaxSim against the bridge for the step. ColBERT doesn't replace the door. It's the better second
  stage *after* a name is chosen. This is a hypothesis to register, not a result.

## Costs (21,100 MuSiQue graph passages, this Mac's CPU, `out/srcb-cost.txt`)

| model | encode all | tokens per passage | fp16 index, raw | against bge-small |
|---|---|---|---|---|
| bge-small (1 × 384) | 196 s | 1 | 16 MB | 1× |
| `a`, 33M (96-dim) | 306 s | 94 mean, 83 median | 381 MB | **23×** |
| `x`, 17M (48-dim) | 92 s | 110 mean, 96 median | 222 MB | **14×** |

- **Encoding is cheap.** The 17M model encodes in half bge-small's time, and the 33M in 1.6×.
- **Storage is the cost.** A raw token index is 14–23× a single-vector one. Standard compression (PLAID residuals,
  token pooling) usually cuts that a few-fold, but we didn't measure it here.
- **Per question,** encoding 20 passages, the question and its keys from scratch and scoring took 0.84 s (a) and
  0.24 s (x). With a stored index, only the query side is encoded.
- **For production, if the bridge-then-match route holds:** the matcher only needs to score a short candidate list from
  the door. So it could encode those few passages on demand rather than index the whole corpus, at about 10 ms per
  passage for `x`. That would avoid the 14–23× storage entirely. It's untested, and it's a design option, not a
  measurement.

## Continuity (SR-KB's 300, seen; not a registered readout)

Seen data, reported so this can be read next to SR-KB, KB2 and MaxSim (`out/srcb-kb.txt`). It shows the same pattern.

| arm | top-1 | arm | top-1 |
|---|---|---|---|
| qr | .393 | k | .577 |
| a_qr | .327 | a_k | .457 |
| x_qr | .303 | x_k | .403 |
| *a_gb* | *.833* | *x_gb* | *.817* |

- `a_qr − qr` is −.067 [−.113, −.017].
- `a_k − qr` is +.063 [+.007, +.120]. Here the ColBERT key arm edges past the text probe, but only on seen data. On
  the fresh set it was level (+.023).
- On this set james's lexical *key* ceiling (K-MISS) is .713, against `a_gb` .833. The two use different gold
  constructions (keys that are the answer, against the answer's own tokens), so this is a direction, not a paired test.
- The five vector routes on this set now span .32–.46: SR-KB's rq .327 and rhm .320, james's MaxSim .410, and `a_k`
  .457. ColBERT's key arm is the best of them and still .12 below k.

## Postmortem

- **What went right.** We registered with james's review before scoring. His two notes (mixed modes, read-dominated
  MaxSim) correctly predicted the primary's failure, and his gold-ceiling suggestion turned out to be the informative
  arm.
- **What I got wrong.** I predicted a_qr above qr, against K-MISS's evidence, which I had already cited in the
  registration. I gave the generic prior ("token-level keeps names") more weight than the specific finding in hand. That
  repeats the lesson from SR-KB: read your own cited evidence into the prediction.
- **The ceiling came in .16 above prediction.** I had anchored on the lexical ceiling (.71) and assumed vectors would be
  worse. The lexical control was added after scoring, so its +.107 is post-hoc. The next study should register a
  bridge-then-match arm, where something other than gold names the bridge, on a fresh draw.
- **Scope.** MuSiQue 2-hop only, given the entry, in-pool with 19 options, two small CPU models. Jev's .88 is on SR-J-R's
  40, a different draw.
