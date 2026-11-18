# V1: does a vote learned from the loop's own walks mark the right door better than the uniform vote?

*18 Nov 2026, bill. Registered before any run. $0, no Jev. Follows Sirsh's 21:55 note (M-20261118-215523-957d): dreaming
is graph edits driven by PageRank-like voting statistics learned by reinforcement from the loop's own walks, never set by
hand; width-neutral versions first. Split with james (M-20261118-220608-c825): this is the learned vote; james's D3 is the
edit operator that reads it.*

## The vote

Personalized PageRank from the passages read so far (α .15, push to residual 1e-4). From passage u, the edge u→t through
door k (k one of u's doors, t one of k's targets) has weight

    w(u→t via k) = exp(θ1 · ln width(k) + θ2 · ln(1 + doors(t)))

where width(k) is k's target count (capped at 100) and doors(t) is t's door count. A step from u picks an edge in
proportion to w; edges through several doors add up. **θ = (−1, 0) is exactly the walk's uniform vote** (a door at
random, then a target at random), the PPR of evals/structural. θ1 says how much a wide door dilutes its vote. θ2 says
whether votes flow toward or away from hub passages. Both are structure only. Door kind is not a feature; a third
feature, whether t links back to u, was dropped before registration because it separates shared-term doors from
directed links, so it is a kind weight in disguise.

A door's vote at a wave is the PPR mass on its unread targets.

## Learning

The grid is θ1 ∈ {−2, −1.5, −1, −.5, 0, .5} and θ2 ∈ {−1.5, −1, −.5, 0, .5, 1, 1.5}, 42 points. **Per graph, θ is the grid
point that maximises the primary measure on the dev questions' recorded walks** (their batches and the gold their walks
were scored against). This is the loop's own walks on training questions. Test is untouched until θ is chosen. A pooled
θ, best on the mean over the three dev sets, is reported too.

## Data

The recorded k=10 walks of evals/width and evals/structural: dev and test for cards, PR titles and MuSiQue (traces in the
probe's E2E_FEATURES format). Every wave with at least one unread gold door and one gold-free door.

## Measures, on test

1. **Primary, width-matched AUC:** over all (gold door, gold-free door) pairs in the same batch whose widths are within 2×
   of each other, the share where the gold door has the larger vote (ties half). This is the width-neutral measure.
2. Within-batch AUC of the vote per unread target (mean), all pairs.
3. Per question, from search's top 5 as the read set: questions whose best gold beyond the seeds is in the top 10 of the
   vote.

## Arms, on test

- **uniform**: θ = (−1, 0), today's vote.
- **learned**: the per-graph θ from dev.
- **pooled**: the pooled θ from dev.
- **random θ**: the mean of the measure over all 42 grid points (what an unlearned θ gets on average).
- **learned, shuffled links**: the learned θ on links shuffled at the same widths (seeded as in evals/structural).

## Bar (fixed now)

Learned passes if, on test, its primary measure beats uniform by at least .02 on at least two of the three sets, falls
below uniform by no more than .01 on any set, beats random θ on all three, and the shuffled arm stays below .56 on all
three. Otherwise the uniform vote stands as the statistic james's D3 uses, and V1 is reported as a null with its
postmortem.

## What it is not

Not a walk: no decider runs, and nothing here touches Jev's P. A pass says the learned vote marks the gold door better at
equal width; whether edits driven by it (D3) or a walk using it help is a later, separately registered run.
