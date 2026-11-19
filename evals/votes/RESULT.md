# V1: a vote learned from the loop's own walks helps only on PR titles; the uniform vote is already near its best

*19 Nov 2026, bill. Registered first (REGISTERED.md, 706d22f). $0, no Jev. Output: `score.txt`, `out/theta.json`, rows
in `out/`: `slim-*` keeps the uniform, learned and pooled θ only. The full 42-point rows (39 MB) are left out; they
regenerate at $0 with `E2E_VOTES=TRACES e2e-probe STORE x OUT`.*

The vote is PageRank from the passages read so far, with each edge weighted by
exp(θ1 · ln width(door) + θ2 · ln(1 + doors(target))). θ = (−1, 0) is today's uniform vote. θ was chosen per graph on the
dev walks, then scored once on test.

| test | uniform (−1, 0) | learned θ | learned | pooled (−1, −1) | random θ | learned, shuffled links |
|---|---|---|---|---|---|---|
| cards | .802 | (−1, −.5) | .800 | .787 | .780 | .504 |
| PR titles | .733 | (−2, −1) | **.785** | .765 | .709 | .534 |
| MuSiQue | .826 | (−1, 0) | .826 | .825 | .793 | .520 |

Cells are the width-matched AUC: in pairs of doors within 2× of each other's width, the share where the gold door gets
the larger vote.

**Verdict: fail.** The bar was +.02 over uniform on two sets. Learned gains +.052 on PR titles, −.002 on cards and .000 on
MuSiQue, where dev chose the uniform θ itself. The other conditions hold: learned beats a random θ on all three sets,
and the shuffled arm stays near chance (.50–.53). The uniform vote stays the statistic for james's D3, with PR titles'
learned θ as the one graph where learning moved it.

## Postmortem

- **Uniform is already near the top of this family.** On dev, uniform is within .002 of the best on cards and is the best
  on MuSiQue. The dev surface spans .61–.82, so the grid could move the measure; the walk's own door-then-target
  rule just sits near its peak on two graphs. A two-parameter family over width and hubness has no headroom there.
- **PR titles is a real, transferable gain.** Dev +.065 became test +.052, and the dev winner is also the test winner. The
  learned θ makes wide doors dilute their vote more (θ1 −2) and steers votes away from passages with many doors
  (θ2 −1). On the PR-title graph, hub passages collect votes that don't lead to gold. Pooled θ (−1, −1) carries half of
  that gain to PR titles but costs cards .015, so one θ for all graphs is worse than a θ per graph. That is what dreaming
  should learn: a per-graph statistic learned from that graph's walks.
- **The per-target measure disagrees with the primary.** On MuSiQue, uniform scores .563 per target against .611 for a
  random θ. Per-target AUC rewards a vote concentrated on narrow doors, which the width-matched measure deliberately
  ignores. I registered width-matched as primary, so this doesn't change the verdict, but anyone using the vote per target
  should expect it to rank differently.
- **Per question, learning doesn't reach more gold.** Gold in the vote's top 10 from search's top 5 is 59/58 (cards),
  55/55 (PR titles) and 37/37 (MuSiQue), uniform against learned. The PR-titles gain is in ordering doors, not in reach.
- **Next, if anything:** richer features would test whether the family is too small, but each one has to be structure
  and not a stand-in for kind (I dropped back-links for that reason). The more direct route is for D3's edits to
  change the graph so the uniform vote marks gold better. This result says the statistic is fine as it is on two
  graphs.
