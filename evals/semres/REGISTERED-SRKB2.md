# SR-KB2 (registered 21 Nov, before scoring): the holder-mean reading of "vectors behind keys"

*bill. REM-1341, the follow-up to SR-KB, using james's reading. $0. Script `srkb2.py`. Graph vectors are in
`~/.cache/walklab/mq-graph-bge.npy` (21,100 passages, bge-small, graph order, 188 s to build).*

**Arms.** As in SR-KB, but each key's vector is the mean of the stored vectors of the graph passages that hold it.
- **Leak excluded (james):** the question's own 20-passage pool is left out of every holder set, because hop 2 holds the
  shared key by construction. A key with no outside holder is dropped.
- `hm` = combine(holder means, 1/(df − 1)).
- `rhm` = rocchio(q, holder means, 1/(df − 1)).
- References, unchanged: `qr` (question + read as text), `k` (lexical), `rq_s` (SR-KB's phrase version with the same
  weight).

**Data.** SR-KB's 300 questions (seed 1341, from 41–1252, minus SR-J-R's 40), so the comparison is paired with SR-KB's
arms.

**Gold-blind look.**
- A median of 20 keys per question have outside holders; no question has zero.
- The printed case ("Great Balls of Fire") shows `hm`'s top 3 as Jerry *Lewis* comedies. That's a topical confusion,
  the same pattern as SR-KB's look, which preceded a fail.

**Primary.** Top-1 hop 2, `rhm − qr`, with a paired bootstrap 95% CI.

**Bar.** H1 passes if the CI lower bound is above 0.

**Secondary.** `hm − qr`, `rhm − rq_s` and `rhm − k`.

**Prediction: H1 fails.** rhm − qr is in [−.08, +.03], and rhm is well below k. This applies SR-KB's postmortem: the look
shows topic, not identity.
