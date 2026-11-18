# Registered: D3, dreaming as learned PageRank voting that drives edge removal (james, 18 Nov 2026, before running)

Sirsh (M-20261118-215523-957d): the only graph operations are adding or removing edges and nodes. Dreaming should be
those operations, driven by PageRank-like voting statistics learned by reinforcement from the loop's own walks,
never set by hand. The aim is a structure in which the right door carries the vote. Width-neutral first, at $0.

## The vote

Bill's walk-PageRank (evals/structural), from the read set R with α = .15: a passage spreads its vote over its doors,
and each door spreads it over its other members. Bill spreads it uniformly over the doors. D3 lets the share each
door gets be learned: share ∝ exp(θ·φ(door)). φ is question-free and kind-free, and the same for every door:
- log postings (members);
- cohesion (the share of member pairs linked by another door);
- log of the passage's own door count.

θ = 0 is bill's uniform vote. The vote is computed by 30 power iterations over the passage–door graph.

## Learning θ, by reinforcement from walks

- **Episodes:** the recorded dev waves (bill's fd rows plus reads from b rows): read set, doors, gold behind each.
- **Reward:** the width-matched within-wave AUC of mean vote per target, gold doors against gold-free ones, for
  pairs within 2× width of each other (bill's unconfounded measure).
- **Search:** θ is searched by the cross-entropy method, 5 rounds of 16 samples. The 20% of dev questions held back
  pick the round. No test data is used.
- **Convergence:** report the reward per round and the movement of θ. Converged means θ moves less than 10% in the
  last round and the held-back reward stops rising.

## The structural edit

Materialise the vote as edges. Remove each passage–door membership whose learned share, at that passage, is below
a quarter of the uniform share (1/(4·doors)). Then plain uniform PageRank on the edited graph is re-scored. The
edited graph has to carry the vote by itself, with no learned weights at walk time.

## Held-out read-outs (test traces, cards 150, PR titles 93, MuSiQue 150; $0)

The width-matched AUC of mean vote per target, for these arms:
- G0, uniform vote;
- the learned vote;
- G_edit, uniform vote on the pruned graph;
- **controls:** a random θ of the same norm; random removal of the same number of memberships; shuffled links
  (width kept).

Also on G_edit: the share of test waves that still have a gold door. The edit must not cut the answer.

**Pass:** G_edit beats G0 on the width-matched AUC by at least .03 on at least two of the three sets, and beats
random removal by at least .03 on those sets. It may lose no more than .02 in waves with a gold door on any set. If
it passes, a Jev stage follows: walks on the edited stores (removal through the store's retraction), ≤$1, registered
as an addendum before running.

## Postmortem

Every result gets one.
