# SR-BN (registered 21 Nov, before any Jev call or scoring): name the bridge, then step through it

*james (namer) and bill (matcher). REM-1341. Scripts: `srbn_name.py` (james) and `srbn_match.py` (bill). Jev cap is
$0.25. This is registered before stage 0.*

**Serves.** K-MISS (#69) and SR-CB (#70) point at one decision. The lexical door k (.58) and every vector route
(.28–.46) lose to lures that win on a sum of weak or rare matches. But if the bridge is handed over (hop 1's answer, from
gold), the walk finds hop 2 at .71 lexically and .81 with a 33M ColBERT. So the open question is whether something
other than gold can name the bridge, and what the named bridge is worth to each second stage. REM-1341 wants cheap vector
work to do most of the job, with Jev judging only a short list. Here the short list is the read passage's door keys
(median 22), not 19 passages.

**Task (as SR-KB and SR-CB).** Gold hop 1 is the read. Rank the other 19 passages of the question's pool. Top-1 is hop 2.

**Data.** SR-KB's permutation (seed 1341 over answerable 2-hop questions 41–1252, minus SR-J-R's 40). **Registered set:
positions 600–899** (300 questions), which no one has scored. Stage 0 uses positions 900–903, outside the set. The
stage-0 cases are printed with their gold for this review and aren't reused.

## Namer half (james)

R is SR-KB's bundle: the read's door keys, with 2 ≤ df ≤ 100 and not inside the question. Each namer picks one key K
from R.
- **`jev`**: one Jev request per question, with the question, the read and the task "Each option is a name or phrase
  that appears in `read`. Which option is the thing that `question` needs `read` to identify, so that the next passage
  to read is about it?" The options are the keys in R, and K is argmax p. The options come from the read passage, never
  from the question or gold.
- **$0 controls**, priced on SR-KB's first 300 (seen, `namer_look.py`, `out/namer-look.txt`):
  - `cosq`: bge cos(question, key). It names a bridge key .153 of the time.
  - `cbq`: a-ColBERT MaxSim(question, key). .087.
  - `rare`: the rarest key. .053.
  - The namer ceiling is .873: that's how often the read's door keys contain the bridge at all.
- **Same-draw Jev reference, `jev_pass`**: a second request per question with SR-J's passage task over the 19
  options. This puts Jev's own hop-2 top-1 on this draw instead of SR-J-R's 40.
- Both requests for all questions go out in **one wave** through `Jev.ask_many`.

**Second stage (lexical, james).** score(v) = 1/(df_K − 1) if v shares K, else 0. Ties are broken by k (SR-K's sum) and
then qr, in that order. That's lexicographic, with no weight. On the seen 300, the gold version (`ceiling_k`, K = the
bridge keys) gets .700, `rare_k` .583, `cosq_k` .507, and k .577.

**Namer primary.** Top-1 hop 2, `jev − k`, paired bootstrap 95% CI. H-N passes if the lower bound is above 0: a
decision naming the bridge lets one key beat the sum of keys.

**Namer secondary** (all with CIs):
- `jev − cosq` (hop 2).
- Naming accuracy, jev against cosq (share of questions where K is a bridge key; gold is used for scoring only).
- `jev − jev_pass`: is naming and then stepping lexically as good as Jev choosing the passage outright?
- `ceiling_k − jev`: how much the namer leaves on the table.

**Predictions (james).**
- Jev names a bridge key .60 of the time (ceiling .873).
- `jev` .63, so `jev − k` is +.06 and H-N is a coin flip.
- `jev_pass` is about .85, so `jev − jev_pass` is clearly negative. Jev reading passages beats Jev naming plus a
  lexical step, but the naming request is a fraction of the tokens.
- **Cost:** the naming request is short (~25 phrases) against the passage request (19 passages). I'll report the token
  ratio.

**Amendment 1 (bill's review, before stage 0).**
- The wave goes through `ask_many` (it was `asyncio.gather` over `ask`).
- B (bridge keys) is word-set ⊆ the answer's words, so a one-word key such as "american" counts as a bridge key for
  "American Football League". Naming accuracy is therefore slightly generous for every namer. The comparisons are
  paired, so the differences stand.

## Matcher half (bill)

**Input.** The namer's K per question (`out/srbn-names-fresh.json`, qi → {R, jev, cosq, cbq, rare, p, pj}).
**Arms**, all scored against K only (none uses gold):
- `m_x`: mean over K's tokens of max over v of cos, with mxbai-edge-17m, encoding the 19 options on demand. This is the
  cheap production arm.
- `m_a`: the same with answerai-small-33m, as the reference.
- `m_lex`: the fraction of K's words in v, ties broken by qr.
- `m_title`: title equals K first, then m_lex, then qr.

**Ceilings, labelled gold.** The same four with K = the hop-1 answer (recomputed on this draw).

**Matcher primary.** Top-1, `m_x − m_title` given Jev's K, paired bootstrap. It passes if the lower bound is above 0:
the token matcher earns its cost over the best lexical second stage, given the same named key.

**Matcher secondary.**
- `m_a − m_x`: does the 33M model pay?
- `m_x` against k: do naming and matching beat the door alone?
- `m_x` against `jev_pass`.

**Prediction (bill).** `m_x − m_title` is about +.06, smaller than the gold-name margin, because a wrongly named key hurts
both. `m_x` beats k only if the namer's accuracy is above about .7.

**Cost reported.** The per-question on-demand encode for x (19 passages; SR-CB measured 0.24 s including the keys).

## Procedure

1. bill reviews this registration.
2. Stage 0 (4 questions, about $0.001), with the spend reported.
3. One wave over the 300, capped at $0.25 (estimated about $0.05).
4. Both halves are scored from the same `srbn-names-fresh.json`, with a joint result and a postmortem.

**Scope.** Given the entry (gold hop 1 as read). In-pool, 19 options. MuSiQue 2-hop only. One Jev wording, with no
wording search.
