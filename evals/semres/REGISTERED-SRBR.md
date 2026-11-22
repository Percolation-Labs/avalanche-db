# SR-BR (registered 22 Nov, before scoring): does dreaming that rewards walked bridges improve new questions' walks?

*bill. Design in `DESIGN-BRIDGE-REWARD.md` (#87, reviewed by james). Script `srbr.py`. $0, no Jev.*

**Serves.** Sirsh's "define good, let dreaming converge toward it". #84 found that walk value sits in question-specific
bridges, and that pruning ordinary memberships is about neutral. So dreaming should *reweight* bridges from walk
outcomes. This tests whether weights learned from one set of questions' successful walks improve walks on different
questions.

**Data.** MuSiQue train 2-hop answerable, from james's corpus and graph (#75). The split is by sha256(id) parity:
- **learn half: 652 questions;**
- **test half: 459 questions** (SR-BX's scored 300 and its stage 0 excluded).

Gold-blind look: **only 6 test questions share their exact gold pair with a learn question**, so memorising answers
can't explain a gain.

**Walk and weights** (as the design, unchanged).
- The entry is cosine's top passage. The step is the argmax of weighted door strength
  S_w[e, v] = Σ (1 + r(e,k))(1 + r(v,k)) / (df_k − 1), ties broken by cosine. With no door, it's the second passage by cosine.
- r is keyed by (passage id, key). Each walk event on a shared key k adds 1/|S_k| to both ends, where |S_k| is the
  number of pool passages other than the entry that share k.
- With no rewards, the walk is SR-BX's cosdoor (.473 on train).

**Weight sets, from the learn half.**
- `R`: rewarded walks only. The reward is that the walk's pair is the gold pair, a stated stand-in for a confirmed
  answer, used on the learn half only.
- `F`: failed walks only.
- **`RND`**: as many update events as R has, drawn at random from all walks regardless of outcome (james's control).
- `B`: all learn-half gold bridges, walked or not. This is the ceiling, labelled gold.
- `R2` and `R3`: R re-walked on its own weighted graph for 2 and 3 passes.

**Primary.** Both hops on the test half, **R − unweighted**, paired bootstrap 95% CI. **H-R passes if the lower bound is
above 0.**

**Secondary.**
- R − unweighted within the no-shared-pair stratum (453 questions); the shared stratum (6) is reported, not read.
- **R − RND**: does the outcome signal matter, beyond boosting walked memberships?
- R − F.
- B − R: the room left for a better reward.
- R3 − R, with the learn-half success and the relative weight change per pass as the convergence readout.
- The top 10 weights for R, R3 and B, to show hub dominance (james).

**Predictions.**
- R − unweighted about +.02 to +.04, so H-R is a coin flip. The weight can only act where a rewarded membership is in
  the test pool (about 65% of questions), and it changes the argmax in only some of those.
- R − RND is positive but small.
- B − R is positive.
- R3 − R is about 0: the learn half's success barely changes after pass 1, since rewarding the same walks again only
  sharpens them.

**Scope.** MuSiQue train 2-hop. A structural walk (no Jev). One reward stand-in (gold), one update rule. MuSiQue reuses
single-hop questions, which inflates bridge reuse (stated in the design), so a pass shows the mechanism, not the
production size.
