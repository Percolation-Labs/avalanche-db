# SR-KB2 result: FAIL, as predicted. Holder-mean key vectors are no better than phrase vectors

*21 Nov 2026, bill. Registered at 60d1a77 before scoring. $0. The same 300 questions as SR-KB. Output is in
`out/srkb2.txt` and `out/srkb2.json`.*

| arm, hop 2 given hop 1 | top-1 | top-3 | MRR |
|---|---|---|---|
| `qr` (question + read as text) | .393 | .653 | .559 |
| `k` (lexical rare keys, SR-K) | **.577** | **.783** | **.703** |
| `rq_s` (phrase vectors, SR-KB) | .340 | .607 | .514 |
| `hm` (holder means) | .277 | .517 | .446 |
| `rhm` (rocchio q + holder means): primary | .320 | .540 | .481 |

- **Primary:** rhm − qr is **−.073 [−.127, −.020]**. The prediction was a fail in [−.08, +.03], and that's what happened.
- **Secondary:**
  - hm − qr: −.117 [−.173, −.060].
  - rhm − rq_s: −.020 [−.063, +.023].
  - rhm − k: −.257 [−.323, −.190].

**Reading.** A key's holder passages, outside the pool, carry their own whole content. Averaged, that's the key's
*neighbourhood topic*: for "dennis quaid", his other films. It isn't the identity "names Dennis Quaid". The printed case
showed it before scoring, where `hm`'s top 3 were Jerry Lewis comedies. Both readings of "vectors behind keys" now fail
in the same way. With SR-KB and james's W-LOOKS, four vector routes to Jev's next-hop term have failed for one reason:
it's an identity term, and averaging turns identity into topic.

**What this changes for REM-1341's library.**
- Combining, weighting and centre removal over key vectors, whether phrase vectors or holder means, isn't a cheap
  next-hop probe on MuSiQue.
- What works cheaply is the lexical door (.58), then vectors among the candidates it admits. SR-E2 measured that
  order end to end.
- A vector op that keeps identity would have to keep many points rather than one mean: for example a max over a bundle
  ("is any of these keys' passages close"), in the spirit of ColBERT's late interaction. That's untested, and it's the
  next idea if this line continues.

**Postmortem.** SR-KB's lesson was applied: read the look for identity against topic before predicting. The look
showed topic, I predicted a fail, and it failed within the stated range. The open question that SR-KB left was cheap
to close ($0, about 15 minutes including the 188 s embedding).
