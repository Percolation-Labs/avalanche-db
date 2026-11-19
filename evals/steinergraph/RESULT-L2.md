# L2 result: a gold-free coherence reward recovers L1's learned link weights

*19 Nov 2026, james. Registration: REGISTERED-L2.md (ac1eacb, amended before scoring at f99a32a). $0, no Jev.
Output: out/l2.txt, out/l2.json; diagnostic out/l2-diag.txt (not registered).*

**PASS.** Dev coherence chose the link weights with no gold. That fit matched L1's gold-fitted weights on held-out PR
titles and stayed level with uniform on MuSiQue, where L1's gold fit had hurt. The bar had two chances (cards and
PR titles); PR titles cleared it, and cards didn't.

Test recall@5 beyond the seeds, with the difference against Q and its 95% bootstrap interval:

| | cards | PR titles | MuSiQue |
|---|---|---|---|
| Q (uniform θ) | .219 | .227 | .145 |
| **LC (coherence, no gold)** | .275, +.056 [−.018, +.133] | **.621, +.394 [+.288, +.497]** | .140, −.004 [−.046, +.037] |
| LQ (L1, dev gold) | .306, +.087 [+.010, +.168] | .611, +.384 [+.280, +.489] | .094, −.051 [−.090, −.019] |
| LH (hub control) | .163, −.056 | .052, −.175 | .075, −.070 |
| LL (locality control) | .227, +.007 | .227, +.000 | .137, −.008 |
| LC-shuf (other question's seeds) | .231, +.011 | .621, +.394 | .094, −.051 |

LC chose θ (width −1, doors −1.5, α .15) on cards and PR titles, and (−1, −1, .15) on MuSiQue. Fitting on the test
questions' own coherence (LC-test, legitimate because no gold is used) gave the same θ on cards and PR titles.

**What it shows:**
- **The reward needs no gold and still finds the weights gold finds.** It recovered L1's whole gain on PR titles
  and 64% of it on cards (not significant). Across the 60 grid points, dev coherence rank-correlates with dev
  recall at +.94 on PR titles and +.66 on cards.
- **It isn't hubs and it isn't locality.** Rewarding hubs (LH) hurts everywhere. Rewarding T for sitting one link
  from a seed (LL, bill's confound) does nothing. Coherence is negatively correlated with locality across the grid.
- **It knew where not to move on MuSiQue.** L1's gold fit chose a θ that hurt MuSiQue (−.051). The coherence fit
  didn't (−.004). The shuffled-seeds fit chose L1's harmful θ there, so on MuSiQue joining this question's own seeds
  is what kept it level.
- **On PR titles, the join isn't question-specific.** LC-shuf picks the same θ as LC there. So the reward found a
  corpus-level setting: prefer passages with few doors, reached through narrow keys and Beside.

**Two readings, both kept (bill):** as a dreaming objective, coherence works. Dreaming tunes the graph once, and a
corpus-level θ is what it needs. As a per-question mechanism it's weak. The diagnostic below, not registered and run
after scoring, asks whether per-question coherence tracks per-question recall at a fixed θ. On PR titles under LC it
does: Spearman +.30, and AUC .76 for any gold in the top 5. Elsewhere it doesn't (cards +.15/.57; MuSiQue −.02/.49;
everything under uniform θ ≈ 0). So coherence isn't yet a general confidence or stopping signal. P3 and P3b
found the same.

**Iteration paying off (Sirsh, 13:10Z):** L1 showed that learning from past walks helps where the learning is
sound. L2 shows the learning signal can come from the walks themselves. That removes the open point from L1: in
the product, the reward has to be gold-free, and here it is.

**Postmortem:**
- *What went right:* bill's review before scoring added the locality control, and that control is what rules out
  the cheapest explanation. Dropping the seed–seed pairs cost nothing.
- *What I'd have got wrong:* my prediction was a gain on PR titles, nothing on cards, and near Q on MuSiQue. Those
  held, but I didn't predict the MuSiQue protection. The likely mechanism is that MuSiQue's titles-as-keys make wide
  keys look connected only under raw counts. 1/(df−1) and the null both discount them. That's untested, not shown.
- *Constants:* all inherited (Beside = 1, 1/(df−1), df 2–100, top 5, 5 seeds, L1's grid). None was chosen here. The
  grid's 60 points are the remaining knob, and LC's θ sits at the grid's most negative doors value on two sets.
  So the optimum may lie beyond it, and I won't widen the grid to chase it.
- *Next:* coherence as the dreaming objective for REM-1341's probe-space warping, which is a reshaping and not a
  re-weighting. It also needs a per-question signal that works beyond PR titles before percolation can serve as a
  stopping rule.
