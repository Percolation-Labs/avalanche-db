# SR-MI (registered 22 Nov, before any Jev call): mutual inductance. Does reading one parallel branch raise Jev's price for the other?

*bill. Sirsh's 10:35Z note on semantic inductance, intuition (2). Script `srmi.py`. The Jev cap is $0.25. james
reviews.*

**Serves.** The $0 look (`RESULT-MI-LOOK.md`, dev 3hop2) found **anti-induction** in vector space. Before anything is
read, the other branch is cosine's top passage in 70% of questions. After one branch is read, cos(q + read) drops it to
median rank 4. Meanwhile the join passage is pulled up (rank 6 → 3), and the two branches share door keys barely more
than chance. So in the graph and the vector probe, the coupling runs through the join, in series. Jev reads the
question's structure and might do otherwise: having read one branch, it might know the other is still needed. That
would be mutual induction between parallel paths. This tests Jev's prices directly.

**Data.** MuSiQue *train* 3hop2 answerable, from james's train corpus (#75): 192 questions, never used. Seed 1344
permutation. **Positions 4–191 are registered (188 questions)**, and stage 0 is positions 0–3, outside the set. Gold is
used only to label the branches (A and B are the two independent sub-questions, J joins them), never as an input.

**Design (paired, per question).** Jev reads one passage and prices every other passage in the pool with SR-J's
passage task, unchanged. The three reads are:
- `A`
- `B`
- `L`, the control: the pool passage outside {A, B, J} nearest the question by bge cosine. It's knob-free.

That's 3 requests per question, all in one `ask_many` wave.

**Measures** (logit p, clipped to [1e-4, 1 − 1e-4]):
- **mutual**: per question, the mean of [logit p(B | read A) − logit p(B | read L)] and [logit p(A | read B) − logit p(A |
  read L)]. Positive means reading a branch raises the other branch's price above what an equally question-like
  passage does.
- **series**: the same for J: [logit p(J | read A) − p(J | read L)] and from B, averaged.
- **ranks**: Jev's rank of the other branch and of J after reading a branch, and after reading L.
- **vector**: the same contrasts with cos(q + read, ·), for comparison with the look.

**Primary.** `mutual`, bootstrap 95% CI over questions. **H-MI passes if the lower bound is above 0.** Jev shows mutual
induction between parallel branches.

**Secondary (CIs).**
- `series`.
- `series − mutual`: is coupling stronger along the chain than across?
- Vector mutual and vector series: does the look's anti-induction replicate on train?

**Noise.** james's SR-MO stage 0 measured Jev's repeat spread at a mean |Δlogit| of .113 per option, between identical
requests. Each question's mutual averages two differences of two options, so its noise is about .11. Over 188 questions
the noise on the mean is about .01.

**Predictions.**
- `mutual` +.3 logit, CI above 0, so H-MI passes, but it's small. Jev knows the other branch is still needed, but L is
  also question-like and keeps B's price up.
- `series` +1.5: Jev strongly lifts the join after reading a branch.
- `series − mutual` clearly positive.
- Vector mutual is negative (anti-induction replicates) and vector series positive.
- Jev's top-1 after reading a branch: J about .5, the other branch about .3.

**Spend.** Stage 0: 4 questions × 3 requests, about $0.001. The wave: 564 requests, about $0.045 at SR-BX's rate. Cap
$0.25.

**Scope.** One shape (3hop2), MuSiQue train, one step, one control rule. One earlier document only. This is a different
question from james's SR-MO, which varies `found` and holds `read` fixed.

## Amendment 1 (james's review, before any Jev call)

- **Common mode.** james's SR-MO found that any read or `found` shifts Jev's prices about +.3 logit on every option. Both
  `mutual` and `series` compare two different reads (branch against L), so a read-wide shift lands in both. Per question,
  `common` = the mean Δlogit (read branch − read L) over the options outside {A, B, J, L}, averaged over reading A and
  reading B.
- **The primary is now `mutual_c = mutual − common`**, and H-MI passes if its lower bound is above 0. Raw `mutual`,
  `common`, `series_c`, raw `series` and `series − mutual` are all reported with CIs.
- **L as a twin.** L is the nearest non-gold passage to the question, so it can be a twin of a branch. Reading it might
  lower that twin's price and inflate mutual. I report how often L shares a door key with A or B (train graph).
- **Prediction for the primary:** mutual_c about +.2, the raw +.3 less a small common mode. It's still a pass, but closer
  to a coin flip.
