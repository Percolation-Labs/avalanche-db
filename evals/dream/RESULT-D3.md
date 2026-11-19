# D3: removing door memberships by neighbourhood vote lowers the gold door's vote, in both directions

*18–19 Nov 2026, james. Registered first (REGISTERED-D3.md: 7f17edb, amended d6c6e15 to the split with bill, D3b
addendum 309c114). $0. No Jev: the gate failed.*

The vote is u's one-step walk weight to a door's other members through its other doors, plus .85 of the two-step
weight (top-30 sparsified), relative to u's median over its doors. The measure is the width-matched within-wave AUC
of mean read-set PageRank per target (bill's unconfounded measure). A second figure gives the share of waves that
still have a gold door. Outputs: `d3/d3-low.txt`, `d3/d3-high.txt`.

## D3: remove the least-vouched memberships (ratio < q)

| | cards | PR titles | MuSiQue |
|---|---|---|---|
| dev G0 | .819 | .731 | .808 |
| dev, q = .05 / .1 / .2 / .4 | .786 / .776 / .764 / .684 | .667 / .637 / .564 / .502 | .780 / .769 / .745 / .676 |
| **test G0** | .783 | .726 | .807 |
| **test G_edit** (q = .05, chosen on dev) | .731 (gold door .97) | .648 (1.00) | .765 (.96) |
| test, random removal of the same count | .793 (.99) | .731 (.98) | .789 (.97) |

The loop converges: memberships changed per round fall 13.2% → 3.3% → 1.2% → 0.5% on p8 at q = .05. What it
converges to is worse at every q, on every set, than G0 and than random removal.

## D3b: remove the most redundant memberships (ratio > h)

| | cards | PR titles | MuSiQue |
|---|---|---|---|
| **test G0** | .783 | .726 | .807 |
| **test G_edit** (h = 2 on p8 and 16 on MuSiQue, chosen on dev) | .748 (gold door **.55**) | .670 (**.55**) | .759 (.89) |
| test, random removal of the same count | .722 (.72) | .639 (.64) | .791 (.97) |

Dev chose h = 2 on p8 for PR titles' .809, but that edit removes 32% of memberships in round 1, still changes 17.6%
in round 4, and leaves a gold door on only .39 of dev waves. Every milder h is below G0.

**Verdict: both fail.** Neither beats G0 on any test set. D3b beats random removal on p8 only because both cut so
much, and it loses 45% of the gold doors.

## The add arm: hubs over passages that vote for each other but share no door

The criterion is mutual top 5 of the two-step vote with no shared door, merged into sets of at most 20.

| set | hubs written | test G0 | test, hubs (offered as doors when a member is read) | test, random hubs of the same sizes |
|---|---|---|---|---|
| cards | 3,705 hubs (p8; 18,068 pairs; 20,375 passages) | .783 | .782 | .784 |
| PR titles | (the same p8 hubs) | .726 | .729 | .727 |
| MuSiQue | 1,998 hubs (5,419 pairs; 7,172 passages) | .807 | .808 | .809 |

**Null.** Within ±.003 of G0 and of random hubs, on dev and test alike. Output: `d3/d3-add.txt`.

## Postmortem

- **The graph as built is a local optimum for removal under the walk's vote.** Removing memberships by any
  question-free vote, low or high, lowers the gold door's width-matched vote. Random removal of the same count barely
  moves it (±.02). The unvouched memberships turned out to be the specific links that make the gold door distinct.
  The redundant ones carry the vote to it. Both are needed.
- **Dev selection ignored the constraint the pass needs.** The registered reward was the AUC alone, so on p8 it chose
  the edit that wrecks reachability (gold door .43/.39 on dev). The reward must carry the gold-door constraint, as
  the pass does. AUC over surviving doors rewards deleting doors.
- **There is a hidden kind effect in D3b.** Owned doors (next/near) have higher vote ratios (median 3.1, against
  about 1 for keys), so "remove the most redundant" removed tens of thousands of them. No kind was a feature, but the
  edit fell on one kind anyway. Next time, report edits by kind.
- **The add arm doesn't move the vote either.** Hubs over mutually voting passages add mass where the vote already
  flows: their members are two steps apart already. Random hubs do as little. Under the uniform vote, G0 is a local
  optimum for every edit tried.
- **What is left:** bill's learned vote (evals/votes). If learned weights move the gold door's vote, materialising
  them is the edit: drop or add the memberships the weights push to zero or up. D3's pipeline re-runs with his θ.
