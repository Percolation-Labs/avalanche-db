# D3c: written into the graph as removals, the learned vote doesn't carry over on PR titles; on cards it gains, but cuts gold

*19 Nov 2026, james. Registered first (REGISTERED-D3c.md, 92b9db9). $0. Output: `d3/d3c.txt`.*

| | dev G0 → chosen f | test G0 | test G_edit | test, random removal of the same count |
|---|---|---|---|---|
| PR titles, θ (−2, −1) | .731 → .744 (f = .02; gold door .80 → .79) | .726 | .725 (gold door 1.00) | .727 (1.00) |
| cards, θ (−1, −.5) | .819 → .823 (f = .05; gold door .77 → .75) | .783 | **.834 (gold door .93)** | .787 (1.00) |
| MuSiQue | θ is uniform: no edit | | | |

Cells are the width-matched AUC of the uniform read-set vote. Test rows are waves that have a gold door, so gold
door 1.00 is the baseline.

**Verdict: fail.** On PR titles, the graph the pass was about, G_edit is flat (−.001) and level with random removal.
On cards it gains +.051 over G0 and +.047 over random. But 7% of the test waves lose every gold door, beyond the
.02 the pass allows. Dev showed only −.02 there.

## Postmortem

- **On PR titles, the learned vote is a re-weighting that removal can't copy.** Bill's learned θ lifts PR titles to
  .785 when the walk uses the weights. Removing the 2–20% of memberships that θ weights least moves dev by at most
  +.016. From f = .05 on, it also starts to cut gold doors. The gain lives in many small down-weights of hub passages
  inside wide doors, spread over memberships the right door also needs. A walk that can't weight edges loses them
  if they are cut.
- **On cards the edit is what moved the vote, not the learned θ.** Bill found cards' learned θ no better than
  uniform when the walk uses it (.800 against .802). Yet the edit by that θ's ratio, removing 5% of memberships from
  hub passages in wide doors, raises the uniform vote's AUC by .05. The vote is sharper on the doors that survive.
  What the edit removed included gold memberships: the gold-door constraint held on dev (−.02) but not on test
  (−.07). Part of the +.05 is the same selection effect as D3b: the AUC counts only surviving doors.
- **The constraint has to be read on the measure that counts.** The registered measure scores surviving doors only,
  so any edit that removes doors can inflate it. The next edit study should score the walk's outcome: the gold-first
  rate or recall over all waves, where a cut gold door counts as a miss. Bill's (b) does that, or a k=10 search-order
  walk on the edited store does it at $0.
- **Where this leaves dreaming as edits.** Removal, addition, uniform votes and learned votes all leave the uniform
  walk at or below the graph as built, except the cards edit, which costs reachability. The statistic that helps
  (PR titles' θ) helps as a weight the walk reads. Bill's W2 tests that.
