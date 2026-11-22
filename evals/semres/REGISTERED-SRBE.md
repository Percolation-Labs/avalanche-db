# SR-BE (registered 22 Nov, before any Jev call): does Jev's entry request choose between the cosine and title walks?

*bill. Follows the entry look (RESULT-ENTRY-LOOK2.md, post hoc). Script `srbe.py` (srbx.py with the changes below).
Cap $0.40. Sirsh at 15:52Z: carry on with the entry look.*

**Data.** MuSiQue train answerable 2-hop, james's `train-corpus.jsonl` and `graph-train-pc.jsonl`, as SR-BX. A fresh
draw: positions 304–603 of SR-BX's seed-1341 permutation (SR-BX scored 0–299, stage 0 was 300–303). Stage 0 is
604–607. SR-BR's Jev-free test half overlaps this draw; no Jev quantity was tuned on it.

**Walks.** SR-BX's rules unchanged. The step is `nt_rescue` from each of three entries:
- `e_cos`: cosine's top passage.
- `e_title`: Jev's title request (namesake nearest by cos).
- `e_pass`: Jev's 20-passage entry request's argmax. *New:* it is now walked with the name steps too (SR-BX walked it
  only with `pass`).

**Selectors** (ties, i.e. the same entry, keep cosine's walk).
- **SE:** keep the walk whose entry has the higher p in Jev's 20-passage entry request.
- SEP: the same with entry p × the p of the walk's step in its entry's pass request.

**Primary. H-E: both hops, SE − e_cos×nt_rescue, paired bootstrap 95% CI, lower bound above 0.**

**Secondary.**
- **SE − e_pass×nt_rescue**: once the entry request is paid for, does the second walk add anything over walking from
  its argmax?
- SEP − e_cos; SE − e_title; e_pass − e_cos (all × nt_rescue); SE − e_pass×pass.
- The split questions and how many each selector gets right.

**Predictions.**
- SE − e_cos about +.03 (the look's +.057, shrunk for six rules tried on seen data). H-E is about a coin flip.
- SE − e_pass×nt_rescue about +.02, not significant: the entry request ranks hop 1 near the top but its argmax is
  often hop 2 or a neighbour, so choosing between two proposals should beat its own argmax, by a small margin.
- SEP ≥ SE by under .01.

**Cost.** Per question: the title and 20-passage entry requests, name and pass from up to three entries, and twins.
SR-BX's 300 cost $0.12 with two entries walked, so about $0.15–0.18. Cap $0.40. Stage 0 first (4 questions).

**What follows.** If H-E passes and SE beats e_pass×nt_rescue, the walk's entry becomes "two proposals, Jev's entry
request chooses", reported to Sirsh as a hypothesis. If SE ties e_pass×nt_rescue, the second walk isn't needed and the
entry is e_pass. Production is Sirsh's.

**Scope.** MuSiQue train 2-hop, the cheap walk, one draw of 300.
