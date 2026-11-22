# SR-MI: Jev shows mutual induction between parallel branches, which the vector probe reverses

*22 Nov 2026, bill. Semantic inductance, intuition (2). Registered in `REGISTERED-SRMI.md` (#77; amendment 1 from
james's review and the stage-0 note, all before the wave). Jev spend: stage 0 $0.0014, wave **$0.0721** (564 requests,
one `ask_many`, cap $0.25). The registration's prose guessed about $0.045, while the script's own estimate was $0.0708.
Outputs: `out/srmi-stage0.txt`, `out/srmi-fresh.txt/json`, `out/srmi-posthoc.txt`.*

**Versions.** percolate-core 0.2.15 (Jev), bge-small-en-v1.5. MuSiQue *train* 3hop2 answerable (james's corpus, #75),
seed 1344, positions 4–191 (188 questions), unused before. Door keys come from graph-train-pc.

**Question.** In 3hop2, two sub-questions are independent (branches A and B) and a third joins them (J). Having read one
branch, does Jev price the *other branch* higher than it does after reading a control passage L, the non-gold passage
nearest the question? That's mutual induction: flow on one path energising a parallel path.

## Registered result

| contrast (read a branch − read L) | Δlogit, 95% CI |
|---|---|
| **mutual_c**: the other branch, minus the common mode (**primary**) | **+.233 [+.170, +.296]** |
| mutual, raw | +.204 [+.145, +.266] |
| common mode: options outside {A, B, J, L} | −.029 [−.066, +.008] |
| series_c: the join J, minus the common mode | +.522 [+.420, +.622] |
| series − mutual | +.289 [+.181, +.399] |
| *vector* mutual, Δcos(other branch) | **−.055 [−.064, −.046]** |
| *vector* series, Δcos(J) | −.014 [−.026, −.003] |

- **H-MI passes.** Reading a branch raises Jev's price for the other branch by about .23 logit beyond what an equally
  question-like passage does. The common mode is about zero here, so the correction barely moves it. That differs from
  SR-MO, where adding `found` shifted everything by +.3. Here the read changes, not the request's shape.
- **The coupling is stronger along the chain** (series − mutual +.29). Jev lifts the join more than the twin branch.
- **The vector probe goes the other way.** cos(q + read) *lowers* the other branch against reading L (−.055), which
  replicates the dev look's anti-induction on train. So Jev does what the vector doesn't.

**Ranks** (Jev's order over the pool's other 19 after the read):

| after reading | other branch: median rank, top-1 | join J: median rank, top-1 |
|---|---|---|
| a branch | 2, .223 | **1, .598** |
| L | 3, .207 | 2, .447 |
| *cos(q + branch), for comparison* | 7, .082 | 4, .210 |

**Post-hoc** (unregistered; james's twin note, `out/srmi-posthoc.txt`). L shares a door key with a branch in .532 of
questions.
- mutual_c is +.210 [+.129, +.294] when L is a twin, and +.259 [+.163, +.361] when it isn't. So a twin L doesn't inflate
  the effect, which is if anything larger without one.
- series_c is +.353 with a twin L and +.715 without: a twin L already carries some of the join's pull.

**Predictions against outcomes.**
- mutual_c about +.2: right (+.233).
- series +1.5: **wrong**, +.52. Stage 0 warned of this, since Jev already puts J high after reading L.
- series − mutual clearly positive: right.
- Vector mutual negative: right (−.055). Vector series positive: **wrong** (−.014). The dev look compared against
  cos(q) alone. Against an equally question-like read, the join isn't pulled up.
- Jev's top-1 after a branch, J about .5: .598. The other branch about .3: .223.

## What it means for semantic inductance

- **Mutual induction exists in Jev's prices, and it's small.** Evidence on one branch makes Jev value the parallel branch
  more, about a quarter of a logit. The vector probe shows the opposite sign: it follows what was read away from the
  parallel branch (Lenz-like). So for split probes, **the combination happens in the decider, not in the vectors.**
  Conditioning a vector probe on one branch's evidence hurts the other branch. A Jev judgment conditioned on it helps
  slightly.
- **Series beats parallel.** The join gets about twice the lift. Jev's prices mostly flow along the chain toward the
  answer passage. SR-BX's entry and this test's stage 0 showed the same: Jev heads for the passage that answers the
  question.
- **With james's SR-MO, as a hypothesis, not a finding.** History carried as `found` gave no momentum along a thread
  there, only a uniform shift. The passage being read here does induce: it lifts its chain neighbour strongly and its
  parallel twin a little. One reading is that the inductance-like coupling sits in what is *read now*, not in what was
  read before. But the two studies differ in corpus (dev 3hop1 against train 3hop2), in shape, and in what was varied
  (`found` with the read fixed, against the read with no `found`). Only one registered design that varies the read and
  `found` together, on one draw, can check it.
- **SR-MO's format question, corrected after SR-MO2 (#81).** I first read the near-zero common mode here as fitting a
  *format* explanation of SR-MO's +.3 shift. james's SR-MO2 then tested it directly: an irrelevant `found` shifts prices
  by only +.013 [−.009, +.036], while true and wrong histories shift them by about +.29. So **the +.3 is question-related
  content, not format.** This study can't speak to it, because the read here was always question-related (a branch or
  L), so relatedness was held constant. My earlier clause was wrong for that reason.

## Postmortem

- **What went right.** james's common-mode amendment, from his own SR-MO lesson, made the primary robust before spend,
  and it turned out not to matter here (−.03), which is itself informative. The stage-0 surprise (J top-1 regardless of
  read) was written into the registration before the wave, as SR-BX's postmortem asked. The vector replication on train
  came free with the same run.
- **What I got wrong.**
  - The series prediction (+1.5): I took the dev look's vector pattern as a guide to Jev's. Jev already ranks J high from
    any question-like read, so the contrast had little room.
  - The spend guess in the registration's prose ($0.045) was a third below the script's estimate ($0.071). Train
    passages are longer. The script's estimate is the one to quote.
- **Scope.** MuSiQue train 3hop2 only, one step, one control rule, 188 questions. The twin split is post hoc. 4-hop
  parallel shapes and longer walks aren't tested.
