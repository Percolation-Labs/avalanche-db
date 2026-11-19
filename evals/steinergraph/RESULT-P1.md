# P1: the graph's own avalanche from the seeds predicts the Steiner graph better than search; steering it by the question's words adds little, and hurts PR titles

*19 Nov 2026, bill. Registered first (REGISTERED-P1.md, fd13ce4). $0, no Jev. Output: `p1.txt` (test), `p1-dev.txt`;
per-node U and Q in `out/nodes-*`.*

Each predictor ranks passages that are not seeds. The cells give the share of a question's gold beyond the seeds that
lands in the predictor's top 5, the walk's budget past its seeds. Test only.

| test (questions) | S: search ranks 6+ | U: uniform avalanche | Q: question-aware avalanche | Q, shuffled links | recorded Jev walk (reference) |
|---|---|---|---|---|---|
| cards (135) | .144 | .203 | **.214** | .004 | .355 |
| PR titles (87) | .163 | **.380** | .227 | .002 | .098 |
| MuSiQue (133) | .086 | .130 | **.139** | .009 | .362 |

Recall@20 follows the same pattern: U .508 / .674 / .269 and Q .451 / .638 / .309.

**Verdict: fail.** Q beats search by .053–.070 on all three sets, but the bar also required Q to beat U on those sets,
and it doesn't on PR titles (.227 against .380). Q's lead over U elsewhere is only .009–.011.

## What it says about the Steiner graph

- **The graph predicts the Steiner graph better than search does, and with no model.** The uniform avalanche from the
  seeds beats search's next five on every set: about 1.4× on cards, 2.3× on PR titles and 1.5× on MuSiQue. Shuffled
  links fall to zero, so the prediction is the link structure, not the widths.
- **The avalanche peaks at step 1.** Gold mass is highest one step from the seeds and falls after that: U .019 → .008
  → .005 on cards, .029 → .007 → .004 on PR titles. The Steiner graph is one door from the seeds, as evals/steiner found.
  On cards and MuSiQue, Q holds its gold mass better over steps (about .015 and .009 at step 3, against .005 and
  .001 for U), so the question keeps the avalanche on track when it spreads.
- **PR titles: the question's words point away from the gold.** Steering steps toward passages that match the
  question lexically costs .153 of recall. That is the encoding fault again, now seen in the avalanche: on PR titles
  the gold doesn't share the question's words, and the graph's links find it better without them. It is also why
  Jev's walk on PR titles (.098) does worse than structure alone (.380), about 4×. Jev reads door text, and door text
  is words.
- **Where Jev wins, it wins clearly.** On cards and MuSiQue, Jev's walk (.355 and .362) beats every model-free
  predictor by .14–.22. So the question's semantics, read by Jev, carry what lexical weighting doesn't.

## Postmortem

- **The registered Q was a weak use of the question.** BM25 at each step rewards word overlap, and on PR titles word
  overlap is the problem. The bar tied Q's pass to beating U, which was the right test: it asked whether the question
  adds to the structure, and lexical weighting doesn't.
- **What this hands james's L1:** U is the prior to beat, and on PR titles it is already 4× the walk. Its learned
  blind arm (+.028 / +.093 / +.022 over U) is in the same units. james's U recall@5 (.207 / .380 / .122, from his own
  Python PPR) matches mine (.203 / .380 / .130) to within .01, so the two pipelines agree.
- **Against Sirsh's 10:25 test:** U and Q are online computations, one PPR per question at walk time. U is cheap.
  What a dreaming pre-computation would have to recover is the gap between U and Jev's walk on cards and MuSiQue, and
  the gap between the walk and U on PR titles. The first is semantic. The second says the walk should trust structure
  more where Jev's encoding is weak. A per-graph statistic learned from history (like V1's θ, or L1's fit) is exactly
  that kind of pre-computation.
