# SR-KB (registered 21 Nov, before scoring): does a key-bundle probe find the next hop without an LLM?

*bill. REM-1341, extending SR-K. $0, no Jev calls. Script `srkb.py`; vector operations from james's `vecops.py`
(james/vecops 057bd7e, copied unchanged).*

**Serves.** REM-1341 asks whether cheap probes built in embedding space from key bundles can stand in for a generated
probe sentence. SR-K found that the read passage's rare keys rank the next hop lexically (.58 over all of MuSiQue,
against cos(q + read) .42). Here the same keys are carried into vector space. Does a probe built from their vectors
rank hop 2 better than embedding the question plus the read passage as text?

**Data.** 300 MuSiQue answerable 2-hop questions, drawn by a seeded permutation (seed 1341) of 41–1252. SR-J-R's 40 are
excluded as james's warp test set. Given the gold hop 1 as read, rank the other 19 passages for hop 2.

**The bundle.** The read passage's door keys (2 ≤ df ≤ 100 in the dream-d1 graph) that aren't contained in the
question. Each key phrase is embedded on its own with bge-small. The weights are vecops.idf(df, 21,100).

**Arms** (each takes the argmax of cos(probe, option)):
- `q`: the question.
- `qr`: question + read passage as one text. This is the baseline.
- `k`: SR-K's lexical decider, for reference.
- `kb`: combine(key vectors, idf), which is Average PRF.
- `rq`: rocchio(q, key vectors, idf), the question kept at equal weight.
- `rq_out`: pivot_out(rq, centre(the pool's 20 passages)), the drift control.

None has a free parameter.

**Gold-blind look.**
- Bundle sizes have a median of 21 keys and include generic phrases ("biographical", "american biographical"), so
  drift is a real risk.
- No bundle is empty.
- One case printed: for the Great Balls of Fire question, `kb`'s top 3 are about the lead actor's other film and rock
  and roll, while `qr`'s top 3 are other films.

**Primary.** Top-1 hop 2, `rq − qr`, with a paired bootstrap 95% CI over questions.

**Bar.**
- H1 (a key-bundle probe beats the text probe) passes if the CI lower bound of `rq − qr` is above 0.
- Secondary:
  - `kb − qr`.
  - `rq − k`: does the vector version beat the lexical one?
  - `rq_out − rq`: does removing the centre help against drift?

**Predictions.**
- rq > qr by .05–.15.
- kb ≈ qr: the bundle alone drifts.
- rq < k: lexical identity beats a blurred mean.
- rq_out ≥ rq.

**Scope.** Given the entry. In-pool, with 19 options. MuSiQue 2-hop only.
