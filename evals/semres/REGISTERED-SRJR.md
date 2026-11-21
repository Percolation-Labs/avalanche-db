# SR-J-R (registered 21 Nov, before any Jev call): does Jev's MuSiQue price survive a random draw?

*bill. Correction study after RESULT-SRK's block finding. Code: `srj.py` with a SEED argument; otherwise unchanged.*

**Why.** SR-J fitted Jev's conductance on MuSiQue's first 40 answerable 2-hop questions in file order, an easy block
(cosine top-1 .62 there, .42 overall). SR1c, THEORY-SR and james's coming warp all use that fit: β_q +1.00, γ +3.77
[+3.39, +4.16]. The question is whether γ, the next-hop term, and Jev's top-1 survive a random draw.

**Draw.** 40 questions drawn by `np.random.default_rng(20261121).permutation` over answerable 2-hop questions 41–1252,
taking the first 40. Stage 0 is the first 4 of the same permutation, so stage 1 reuses their cache.

**The same as SR-J:** task wording, 19 options after reading gold hop 1, one batched request per question, all in flight
together, the fit logit p = β_q cos_q + γ hop2 + c (and + β_r cos_r), and a bootstrap over questions.

**Spend.**
- Stage 0: 4 requests, estimated about $0.0005.
- Stage 1: 36 more, estimated about $0.004.
- Cap $0.05 per stage. This is within the $1 rule.

**Outcomes and bar.**
1. **γ survives** if the random-draw γ's 95% CI overlaps SR-J's [+3.39, +4.16] *and* its lower bound is above +2.0.
   That would mean the next-hop term is still several nats. If γ's CI lies wholly below 3.39, SR1c and the theory are
   restated at the new γ.
2. Jev top-1 for hop 2, against cos(q + read) top-1, on the same 40. Prediction: Jev stays at least .25 above cosine.
3. β_q, reported with its CI.

**Predictions.**
- γ 2.5–4.
- Jev top-1 .75–.90, below .97.
- cos(q + read) about .40.
