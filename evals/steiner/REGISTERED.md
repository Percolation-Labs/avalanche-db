# The Steiner cost and the encoding gap: two measures, registered before any run

*Registered 18 Nov 2026 by bill. Sirsh's focus M-20261118-164942-d93f. It keeps three things apart:
- the Steiner theory, which is about structure;
- the encoding layer, the information written into the graph;
- dreaming, which learns to write that information.
It asks what structure lets a walk find the Steiner substructure cheaply, and how to measure it. The split proposed to
james (M-20261118-170601-1895): bill the structure and its measure, james dreaming. $0, on the dev trace replays
(evals/width: cards-dev 100, prs-dev 65, musique-dev 101, k=10). Nothing is chosen or tuned.*

## (a) The Steiner cost: how cheap the answer is in the graph as built

For each question, the fewest reads that take a walk from search's 5 seeds to the gold, through the walk's own doors
as raised (`d6::doors_of`, cap 100). A door reads its targets in shown order (`D6::shown_order`). So reaching target x
through door d costs x's place in d's order.
- **Per gold:** the cheapest path from a seed, within 2 doors. Reaching x costs its place in d1, and the gold behind
  x's door adds its place in d2.
- **Per question:** the cost of reaching all gold, by greedy cover. Each step takes the cheapest remaining gold given
  what is already read. A greedy cover is an upper bound on the true Steiner cost, and it is reported as one.
- **Also:** the cost of reaching the first gold, and the share of gold reachable within the k=10 budget of 5 reads
  (the Steiner share).
- **Controls:**
  - random seeds, 5 per question (seed 1118);
  - target-shuffled doors, each keeping its width (seed 1118), as in evals/structure.
- **The test of the theory:** does the Steiner share predict the walk's recall across questions? Reported as Spearman
  ρ and as recall by Steiner-share tercile, for today's walk, the oracle and search. If it doesn't, the measure is not
  the graph number we want.

## (b) The encoding gap: whether the right door is distinguishable

At each recorded wave, take the doors that lead to unread gold (gold doors). Measure where the best of them sits in
Jev's ranking:
- the share of waves where a gold door is ranked first;
- the mean reciprocal rank;
- the read-weighted version: the gold the opened door returns, against the most a gold door would return within the
  remaining budget.
- **Controls, on the same batches:** search-order ranking, width ranking, and a random ranking (seed 1118). The
  oracle is 1 by definition.

The gap between Jev and the oracle on (b), restricted to questions whose Steiner share (a) is high, is the encoding
layer's fault, as Sirsh separates it. This is the number dreaming should move. It is computed per question, then
averaged over a log, so it needs no gold at product time only if dreaming has a proxy. Finding that proxy is
dreaming's question (james), not this one.

## Reported

- The per-corpus means, with the controls.
- Spearman ρ between (a) and the walk's recall.
- The share of each corpus's walk–oracle gap that falls on questions with a high Steiner share.
- A postmortem whatever the result. No default changes.
