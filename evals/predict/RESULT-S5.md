# S5: the seeds' neighbourhood is a dense, well-connected expander on all three graphs; nothing spectral predicts the walk or singles out PR titles

*19 Nov 2026, bill. Registered first (REGISTERED-S5.md 1d26e86, amended before running 38f5714). $0. Output: `s5.txt`.
λ2 is checked by a unit test on known graphs: K10 gives 10/9, two disjoint cliques give 0, and one bridge gives a
small gap.*

H is search's 5 seeds plus every target of their doors (capped at 3,000 passages), with door co-membership as edges.

| test | AUC: spectral gap | AUC: seed coherence | AUC: lower density | median gap | median density (edges per passage) | walk found gold beyond the seeds |
|---|---|---|---|---|---|---|
| cards | .550 | .425 | .429 | .232 | 55 | 70 / 150 |
| PR titles | .419 | .535 | .508 | .213 | 52 | 11 / 93 |
| MuSiQue | .493 | .485 | .557 | .384 | 83 | 62 / 150 |

The AUCs are for "the recorded walk read gold beyond the seeds".

**Verdict: null on both bars.** No property reaches .65 on any graph. On the question-free properties PR titles sits
between or next to cards: gap .213 against .232, density 52 against 55, coherence .156 against .166.

The two gold-using diagnostics do set PR titles apart, but toward easier, not harder:
- **More gold near the seeds:** 2.72 gold passages in H on average, against 2.06 on cards and 2.31 on MuSiQue.
- **Slightly tighter gold:** gold conductance .978, against .989 and .996.

## Postmortem

- **Gold is not a spectral community.** Gold conductance is .98–1.00. Almost every edge from a gold passage leaves the
  gold set, in a neighbourhood of 1,000–2,000 passages with 50–80 edges each. So the Steiner substructure is a few short
  paths through a dense, well-mixed neighbourhood, not a cluster. Its spectral gaps of .21–.38 are those of a good
  expander. A global spectral property can't see a two-passage answer inside that.
- **Why the spectral angle failed:** spectral measures describe how a graph mixes, and all three graphs mix well. What
  separates the right door is local and question-relative: which of 80 doors leads to two particular passages. The
  vote's width-matched AUC (.73–.83) already measures that, and it is the only structural signal this week's six
  studies found.
- **PR titles, for the last time on structure:** five studies (V1, W2, W3, S4, S5) find PR-title structure ordinary or
  easier. The PR-title gap is in the encoding layer. Its walk reads gold beyond the seeds on 11 of 93 test questions,
  against 70 of 150 on cards, with as much gold within one door.
- **What I'd do differently:** S4's partial-correlation point applies here too. More importantly, after V1 the
  structural line had told us what it could. I ran S4 and S5 because Sirsh had named spectral analysis, and both cost
  minutes. The result is a clear negative to report, not a reason for a sixth variant.
