# SR-KB result: FAIL. Putting the keys into vector space loses what made them work

*21 Nov 2026, bill. Registered at fd6b101, with amendment 1 (james) before scoring. $0, no Jev calls. 300 questions,
seeded random draw (seed 1341) from 41–1252, excluding SR-J-R's 40. Output is in `out/srkb.txt` and `out/srkb.json`.*

**Serves.** REM-1341: can a probe built in embedding space from a key bundle replace a generated probe sentence?

Hop 2 given the gold hop 1, out of 19 options:

| arm | top-1 | top-3 | MRR |
|---|---|---|---|
| `q` (question) | .267 | .487 | .429 |
| `qr` (question + read, as text): baseline | .393 | .653 | .559 |
| **`k` (SR-K, lexical: shares rare keys)** | **.577** | **.783** | **.703** |
| `kb` (Average PRF of key vectors, idf) | .370 | .540 | .509 |
| `rq` (rocchio: q + key vectors, idf): primary | .327 | .610 | .504 |
| `rq_out` (rq minus the pool centre) | .323 | .587 | .498 |
| `kb_s` (key vectors, 1/(df − 1)) | .353 | .530 | .495 |
| `rq_s` (rocchio, 1/(df − 1)) | .340 | .607 | .514 |

- **Primary:** rq − qr is **−.067 [−.120, −.013]**. The key-bundle probe is *worse* than embedding the question with the
  read passage. H1 fails.
- **Secondary:**
  - kb − qr: −.023 [−.077, +.030].
  - rq − k: −.250 [−.317, −.187].
  - rq_out − rq: −.003 [−.057, +.050].
  - rq_s − rq: +.013 [−.017, +.043].
  - rq_s − qr: −.053 [−.107, .000].
  - rq_s − k: −.237.
- **Predictions.**
  - Wrong: rq > qr.
  - Right: kb ≈ qr, rq < k.
  - No effect where I predicted one: rq_out ≥ rq and rq_s > rq.
  - The drift controls (the rarity weight and centre removal) move nothing.
- SR-K's lexical number reproduces on a fresh random draw: .577 here, against .58 over all 1,252.

**Mechanism (a reading, not tested here).** The key works lexically because it's an *identity* test: the option
contains the string "dennis quaid" or it doesn't. Its embedding is a *topic* direction, "an American actor in a
biopic", which every film and actor passage in the pool shares to some degree. Averaging 21 such directions, even
weighted, gives the pool's topic again, which the read passage already supplies better as text. Neither the rarity
weight nor removing the centre turns topic back into identity. In SR-J's terms, the next-hop term γ is an identity term,
and bge's vectors put it in the β (similarity) channel, where it's worth about a tenth as much.

**What this changes.**
- For REM-1341's library of vector operations: combining key *phrase* vectors isn't a cheap probe for the next hop.
  The lexical door should stay lexical.
- Where vectors help is after the door has found the candidates. SR-E2's cosdoor is that order.
- james's reading of "vectors behind keys", the mean of the stored vectors of each key's holder passages, is untested
  and different. A holder passage's vector carries its whole content, not the key's topic. That's the follow-up arm.
- For the warp: if the next-hop term is identity, a linear warp of bge space can only recover the part of it that is
  linearly encoded. james's W1 already priced dead on its own data, and this points the same way.

**Caveats.**
- bge-small only.
- Phrases were encoded without the query prefix (stated in amendment 1).
- Given the entry, in-pool with 19 options, MuSiQue 2-hop only.

**Postmortem.**
- **What went right.** It was registered, reviewed and amended before scoring, on a random draw. SR-K's number
  reproduced as a free control.
- **What I got wrong.** I predicted rq > qr by .05–.15 without pricing it. The $0 look printed one case, where `kb`'s top
  3 were topical neighbours of the bridge entity, not the entity's own passage. That was the mechanism in plain sight. I
  read it as "drift risk" when it was "identity becomes topic". Next time, when a look shows the probe's top options,
  check whether hop 2 is among them before writing the prediction.
