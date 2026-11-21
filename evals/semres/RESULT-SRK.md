# SR-K result: a shared key door ranks the next hop as well as gold does, but it isn't Jev's whole price

*21 Nov 2026, bill. Registered at c107338 (REGISTERED-SRK.md) before scoring. $0, with no Jev calls. Output is in
`out/srk.txt`; the unregistered check is in `out/srk-str.txt`.*

**Serves.** THEORY-SR item 1. A graph measure should price the step Jev pays for. SR-J's bridge entity e carried that
step, but e needs the gold answer. The question here is whether the graph's own key doors carry it without gold.

**The answer for ranking is yes.** Given the entry, that is with the read passage being the gold hop 1, a passage that
shares a rare key door with what was read is the next hop in 95% of 40 MuSiQue questions. The bar passes.

| decider, 19 options after hop 1 | top-1 hop 2 |
|---|---|
| word overlap (question + read) | .33 |
| cos(question + read), the best vector | .62 |
| e, bridge entity (gold-aware, SR-J am. 2) | .90 |
| **k, shared new key door, weighted by Σ 1/(df − 1)** (gold-free) | **.95 [.88, 1.00]** |
| Jev | .97 |

- `k_new` (binary) has recall .93 and precision .39 for hop 2, marking 96 options over 40 questions. Rarity weighting is
  what picks the right one out of 2.4. `k_any`, which still counts keys the question already contains, has precision .13.
  So dropping the question's own keys does the work.
- The k-decider's pick equals Jev's argmax in 93% of questions.
- **Worked case.** "Who is the spouse of the Green performer?" The read passage is Steve Hillage's album *Green*. Of 19
  options, only Miquette Giraudy shares a new door key with it (`steve hillage`). Jev gave her .75 and the next best .30.
  Three cosine options about "Green" were above her.

**As a price it's not enough. Jev pays for something beyond the key door.**

| fit of logit p_Jev, 760 options, CIs from a bootstrap over questions | κ (key) | γ (is hop 2) |
|---|---|---|
| cos_q + hop 2 (SR-J) | — | +3.77 [+3.40, +4.15] |
| cos_q + k_new | +1.59 [+1.16, +2.24] | — |
| cos_q + k_new + hop 2 (registered) | +0.20 [+0.05, +0.36] | +3.61 [+3.23, +3.99] |
| cos_q + log(1 + k_str) + hop 2 (unregistered) | +0.87 [+0.26, +1.43] | +3.03 [+2.45, +3.65] |

With the key in the fit, the next-hop term falls only from 3.8 to 3.0–3.6 nats. A key door tells the walk *which* option
continues the chain. Jev also prices *how sure* it is that this option is the continuation. It pays about 3 nats for
the true hop over a key-sharing distractor, for example another passage that mentions the same studio but doesn't
answer the relation. The key door is a good ranker and an under-priced conductance.

**What this changes.**
- THEORY-SR item 1's hypothesis holds for ranking. A gold-free graph measure can use "shares a rare key door with what
  was read, not already in the question" as its relational term. It reaches .95 of the next hops, where cosine reaches
  .62.
- It doesn't hold as a price. A measure that needs Jev's magnitudes, such as T\* cost or reach probabilities, would put
  about 3 nats too little on the true hop and too much on key-sharing distractors (precision .39). The relation, which
  is what the world fits split off as γ_rel, is still the missing piece.

**Caveats.**
- The result is given the entry. The read passage is the gold hop 1. S1′'s entry miss isn't touched here, and the entry
  hop still has to be landed.
- MuSiQue 2-hop only, 40 questions. MuSiQue's 19 distractors per question are built from retrieval, not adversarially
  for key overlap. Cards have no key-door graph here.
- **Gold-freeness was checked** (james asked). All 510,121 keys in `graph-mq.jsonl` are token spans of their own
  passage's text. The 92 apparent misses are non-Latin scripts the check's tokenizer drops. The keys can't carry a
  question or an answer that isn't in the passage. Which spans the store chose to keep wasn't audited.
- The df range 2–100 is the graph's existing door definition, inherited and not tuned here.

**Postmortem.**
- **What went right.** The magnitude look before registering (k_new marks one option in 19/40 cases) showed the feature
  wasn't degenerate. That was the step missing from SR23.
- **What I'd do differently.** I registered the fit with binary `k_new`, but the decider uses the weighted `k_str`. So
  the registered fit understated how much of γ the key absorbs (0.2 against 0.9 nats). The fit should have used the same
  feature as the decider. The k_str fit is reported as unregistered.
- **The near miss.** The first scoring run died on a missing numpy, and the output file was empty under exit code 0
  (`tee`). I read the file before trusting the run.
