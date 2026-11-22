# Design (not registered): reward-driven bridge weighting, dreaming that learns from walk outcomes

*22 Nov 2026, bill. The "define good, let dreaming converge" lever, after #82 (the memory term is the wrong lever)
and #84 (walk value is concentrated in question-specific bridges, and pruning ordinary memberships is about neutral). For
james's review before any registration.*

## The idea

Dreaming shouldn't prune by structure. It should **raise the weight of door memberships that carried walks to confirmed
answers**, with diminishing returns where a hop has parallel bridges (#84: the first bridges removed are worth most).
Walks then read door strength with those weights. That's an RL loop: walk, observe the outcome, reweight, walk again.

## Power check, done ($0, gold only to label bridges; `bridge_overlap.py`, `out/bridge-overlap.txt`)

Learned weights help a new question only through bridges that earlier questions also used. Questions are split by
sha256(id) parity.

| corpus | half-1 bridge memberships also half-0 bridges | half-1 questions touching a half-0 bridge |
|---|---|---|
| dev (graph-mq) | .373 | .816 |
| train (graph-train-pc) | .298 | **.652** |

So there's room. Two-thirds of train's held-out questions touch at least one bridge that the other half also used. **A
caveat to state up front:** MuSiQue builds multi-hop questions by composing shared single-hop questions, so bridge reuse
is partly by construction. Real query logs may reuse less, or more for popular entities. A positive result here shows
the mechanism works, not the size of the gain in production.

## Proposed test ($0, no Jev; MuSiQue train, james's corpus and graph)

- **Split.** Half 0 (sha256 parity) is the learn half, and half 1 the test half. 2-hop answerable only, so the walk is
  SR-BW/SR-BX's.
- **The walk.** Cosine entry, then the `cosdoor` step: argmax door strength from the entry, ties by cosine. It needs no Jev,
  so the graph's weights are the only thing that changes between arms. SR-BX had cosdoor at .473 both hops on train.
- **Learn.** Walk every learn-half question once on the unweighted graph. **Reward** = the walk's pair equals the gold
  pair. That's the stand-in for an answer confirmed by feedback, and gold is used on the learn half only. For each rewarded
  walk, for each shared key k between the entry e and the step s: r(e,k) and r(s,k) each go up by 1/|S_k|, where |S_k| is
  how many pool passages other than e share k (the diminishing returns over parallel bridges).
- **Weighted door strength.** S_w[e,v] = Σ_k (1 + r(e,k))·(1 + r(v,k)) / (df_k − 1). That's the unweighted strength when
  nothing is rewarded. The unit is the reward count itself, so there's no free weight.
- **Arms, on the test half:**
  - `cosdoor`, unweighted (baseline).
  - **`cosdoor_R`**: weights from rewarded learn-half walks (the method).
  - `cosdoor_F`: the same update applied to *failed* learn-half walks (control: does success matter, or does any
    walked membership get a boost?).
  - `cosdoor_B`: weights from *all* learn-half gold bridges, walked or not (the supervised ceiling, labelled gold).
- **Primary.** Both hops, `cosdoor_R − cosdoor` on the test half, paired bootstrap. A secondary is `cosdoor_R − cosdoor_F`.
- **Rounds.** One learn pass is registered. Iterating (re-walk the learn half on the weighted graph, reward again) is the
  "converge" part. Report it as a secondary at 2 and 3 passes, with the change in weights per pass as the convergence
  measure.
- **Size.** Train 2-hop questions split about 626 / 626. The test half excludes SR-BX's 300 (scored). Expect about
  470 test questions.

## Predictions (to fix at registration)

- `cosdoor_R − cosdoor` about +.02 to +.04. The weight can only change the step where a rewarded membership is in the
  test pool, which is about 65% of questions, and only some of those flip.
- `cosdoor_R − cosdoor_F` is positive: success matters.
- `cosdoor_B − cosdoor_R` is positive, and is the room left for a better reward signal.

## Open for review

- **Reward from gold on the learn half.** That's a feedback stand-in. A gold-free alternative is Jev's confirmation (the
  step's pass p above the request's median, say), but that brings a threshold, so I'd keep gold as the stated stand-in.
- **Whether to put the weight into the Jev pipeline** (name's tie-break and the |S| = 0 fallback) too. It's not in the
  first test, which keeps it $0 and clean.
