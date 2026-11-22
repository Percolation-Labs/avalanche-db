# SR-BA (registered 22 Nov, before scoring): does a bridge reward aimed at the answer passage help new questions?

*bill. Follows NOTE-REWARD-ALAST.md (a $0 look on SR-BC's already-scored test half: rewarding A-last +.022
[+.009, +.037], 10 gained / 0 lost). Script `srba.py --swap`. $0, no Jev. Serves Sirsh's 17:07Z decision: optimise the
dreaming reward toward the answer being in what the walk returns.*

**Why a swap.** The look learned on SR-BC's learn half (sha256 parity 0) and tested on its test half (parity 1), which
SR-BR, SR-BC and SR-RS had all scored. New questions can't be walked here (the train graph has keys only for this
corpus), so the fresh test is the other direction: **learn on half 1, test on half 0.** Half 0 was only ever used to
learn from, never scored as a test. SR-BX's 304 questions stay out of the test.

**Everything else is SR-BC's.** The data, the structural walk, the event (1/|S_k| to both ends of each shared key), and
the fixed-point update: replace each pass, until the rewarded set repeats.

**Arms.**
- none
- **T*alast**: reward = the walk's pair contains the gold last-hop passage (A-last), on the learn half only.
- T*pair: reward = the walk's pair is the gold pair, SR-BC's.

**Primary. A-last on the test half, T*alast − none, paired bootstrap 95% CI. H-BA: the lower bound is above 0.**

**Secondary.**
- T*alast − T*pair on A-last.
- Both hops for each arm.
- Flips both ways.
- Passes to the fixed point.

**Predictions.**
- T*alast − none about +.02, as the look found (+.022). H-BA is about two in three to pass: the look's lower bound was
  +.009, and the other direction may carry less bridge reuse.
- T*alast − T*pair about +.005, not significant.
- No losses, as in every structural reward so far.

**What follows.** If H-BA passes in both directions, the A-last reward replaces the gold-pair reward as the dreaming
proposal, reported to Sirsh as a hypothesis. If it fails here, the look's +.022 was direction-specific, and the
postmortem says so.

**Scope.** MuSiQue train 2-hop, the structural walk, gold labels as the stand-in for a confirmed answer.
