# SR-CB (registered 21 Nov, before scoring): does a small late-interaction model keep the identity bge-small loses?

*bill. REM-1341, on Sirsh's 21:19Z steer. $0, no Jev calls. Script `srcb.py`, costs `srcb_cost.py`.*

**Serves.** SR-KB, SR-KB2 and james's MaxSim put five vector routes on the same task at .32–.41 top-1, against the
lexical key decider at .58 and Jev at .88 (random draw). The joint reading is that the next hop is carried by identity
(the read passage names something the next passage also names), and bge-small's single pooled vector keeps only a trace
of it. A ColBERT-style model keeps one vector per token, trained for token-to-token matching. If identity survives
anywhere in vector space cheaply, it should survive there. Sirsh also needs the price, since an expensive model can't go
to production.

**Task (as SR-KB).** Given the gold hop 1 as read, rank the other 19 passages of the question's pool for hop 2. Top-1 is
hop 2.

**Models.** Both run on this Mac's CPU through pylate, each in its own trained modes: the question is encoded as a
query, and passages and key phrases as documents.
- `a`: answerdotai/answerai-colbert-small-v1 (33M parameters, 96-dim tokens).
- `x`: mixedbread-ai/mxbai-edge-colbert-v0-17m (17M, 48-dim).

**Arms.** MaxSim(T, v) = Σ over t in T of the max over v's tokens s of cos(t, s).
- `M_q`: MaxSim(question tokens, v).
- `M_qr`: MaxSim(question tokens ∪ read-passage tokens, v). This scores against **the whole read passage**, as a
  late-interaction version of `qr`.
- `M_k`: Σ_k w_k · mean over key k's tokens of max over v of cos, with w_k = 1/(df_k − 1). It uses SR-KB's bundle
  (the read passage's door keys, 2 ≤ df ≤ 100, not contained in the question). This scores against **the keys only**.
  An empty bundle falls back to `M_q`.
- References, recomputed on the same questions: `qr` (bge-small cos of question + read) and `k` (SR-K's lexical door
  decider, ties broken by qr).

None has a free parameter. Model lengths are the models' own (a: query 32, document 300; x: 48 and 512).

**Data.** SR-KB's own permutation (seed 1341 over answerable 2-hop questions 41–1252, SR-J-R's 40 excluded). The
registered set is **the next 300** of that permutation, positions 300–599, which nobody has scored. SR-KB's first 300
(seen, james's MaxSim set) are run after, for continuity only.

**Gold-blind look, done before this registration.** 3 questions, no ranks.
- Per question, encoding 20 passages, the question and the keys then scoring takes 0.65 s (a) and 0.18 s (x).
- One case printed ("What league includes the sports team that has Maycon Carvalho Inez?"): `a_k`'s top 3 includes
  "Premier League" twice. Keys like "football" pull toward the answer's type, not the bridge team. The other arms'
  top 3 are about as unrelated as `qr`'s.

**james's miss look (SR-KB's 300, seen) bears on this.** k misses 127. Of those, 103 lose to a lure with more door
strength, and only 24 have no door. In 54 of the 103 the lure names the hop-1 answer too. So the lexical gap is
discrimination, and a token model scoring the whole read passage can fail the same way.

**Primary.** Top-1 hop 2, `a_qr − qr`, paired bootstrap 95% CI over questions.

**Bar.**
- H1 (token-level matching keeps identity the pooled vector loses) passes if the CI's lower bound is above 0.
- Secondary, reported with CIs:
  - `a_k − k`: does ColBERT's soft key match reach the exact one?
  - `a_qr − k`.
  - `a_k − qr`.
  - `x_qr − qr` and `x_k − k`: the 17M model.
  - `a_q − a_qr`: does reading the passage help.
- "ColBERT closes the gap to lexical" needs `a_qr − k` or `a_k − k` with an upper bound at or above 0.

**Predictions.**
- a_qr about .45, above qr (about .39) by .03–.10. H1 is a coin flip.
- a_k about .45–.50, below k (about .58). Soft matching blurs rare names into their type, as in the look.
- Both below k: the gap stays open.
- x is within .05 of a.

**Costs reported** (`srcb_cost.py`, run while this is under review, with no scores): encode time for the 21,100
graph passages against bge-small's, tokens per passage, and fp16 index size against bge-small's 384-dim single vector.
Per-question latency comes from the scored run.

**Scope.** Given the entry. In-pool, 19 options. MuSiQue 2-hop only. Two small CPU models, not ColBERTv2 or larger.

## Amendment 1 (james's suggestion, 21:26Z, before scoring)

- **A gold-ceiling arm, labelled as such.** `M_gb` = mean over the hop-1 answer's tokens of the max over v of cos.
  The answer comes from MuSiQue's decomposition, so this is the bridge entity, and it is **not a decider**: it uses gold.
- It asks whether ColBERT finds hop 2 when handed the right identity. If `a_gb` is high and `a_qr` low, the model can
  match the name but can't pick it out of the read passage. If `a_gb` is low too, the token space doesn't carry the name
  either.
- Compare it with james's lexical gold ceiling (walking only through the bridge key) of .713 on SR-KB's 300
  (K-MISS, #69). Reported as `a_gb − a_qr`.
- Prediction: a_gb about .65, below the lexical ceiling, and well above a_qr.

## Amendment 2 (james's review, 21:28Z, wording only, before scoring)

- **M_qr mixes modes.** The read passage is encoded as a document (the document marker, no query padding) and its tokens
  are then used as query tokens beside the question's query-mode tokens. That's a fair choice, but it isn't how either
  model was trained. A fail on `M_qr` therefore doesn't show that ColBERT can't do this.
- **M_qr is mostly the read passage.** The read has about 10× the question's tokens, so `M_qr` is close to
  MaxSim(read, v). By K-MISS, that's the "many weak matches" readout that loses to lures with summed keys. So
  `a_qr ≤ qr` would be expected, not surprising. **`a_k` and `a_gb` are the informative arms.** The primary is unchanged.
