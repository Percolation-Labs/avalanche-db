# Registered: D3, graph edits driven by PageRank votes (james, 18 Nov 2026, before running)

Sirsh (M-20261118-215523-957d): the only graph operations are adding or removing edges and nodes. Dreaming should be
those operations, driven by PageRank-like voting statistics learned by reinforcement from the loop's own walks,
never set by hand. The aim is a structure in which the right door carries the vote. Width-neutral first, at $0.

## Split (M-20261118-215648-b1dc, M-20261118-220608-c825)

Bill learns the voting statistic: per-edge transition weights as a function of structure, learned from dev walks,
in the style of supervised random walks (evals/votes). D3 is the edit operator driven by a vote. It runs on bill's
uniform read-set PPR first, and on his learned weights once they are posted. D3 learns no vote of its own. The draft
that did (7f17edb) is withdrawn.

## The vote, question-free

The passages rate each other. u's vote for v is the two-step walk mass from u to v: one step to a door uniformly,
then to a member uniformly, with α = .15. Paths through the door being judged are excluded.

## The edits

- **Remove.** Drop the membership (u, d) when u's vote for d's other members, through every other door, falls below
  a threshold q of u's mean vote over its own neighbours. Such a door connects u to passages its neighbourhood
  doesn't vouch for.
- **Add (second arm).** A hub over passage pairs or small sets that vote for each other strongly (mutual top 5) but
  share no door. Members are capped at 20, and the label is D1's rule.
- **The one parameter.** q, taken from {.05, .1, .2, .4}, is chosen by the dev reward: the width-matched AUC of mean
  read-set PPR per target, on the edited graph, over the dev waves. It is learned from walks in that sense. Test is
  never used.
- **Convergence.** The edits are re-applied on the edited graph, with votes recomputed, until fewer than 1% of
  memberships change, for at most 4 rounds. Changes per round are reported.

## Held-out read-outs (test traces, cards 150, PR titles 93, MuSiQue 150; $0)

The width-matched AUC of mean read-set PPR per target (uniform, then bill's learned weights), for these arms:
- G0;
- G_edit, removal;
- G_edit, removal plus hubs;
- **controls:** random removal of the same number of memberships; random hubs of the same count and sizes;
  shuffled links (width kept).

Also on G_edit: the share of test waves that still have a gold door. The edit must not cut the answer.

**Pass:** G_edit beats G0 on the width-matched AUC by at least .03 on at least two of the three sets, and beats
random removal by at least .03 on those sets. It may lose no more than .02 in waves with a gold door on any set. If
it passes, a Jev stage follows: walks on the edited stores (removal through the store's retraction), ≤$1, registered
as an addendum before running.

## Postmortem

Every result gets one.

## Addendum, D3b (registered before running, after D3's removal arm harmed dev and test)

Removing the memberships the neighbourhood doesn't vouch for lowers the width-matched AUC at every q. So the
specific, unvouched links are what tell the gold door apart. D3b tests the mirror edit, same pipeline and controls:
remove the memberships whose vote ratio is **highest**. Those are redundant links to passages the neighbourhood
already reaches, and they spread the vote wide.
- **The threshold:** a ratio above h, with h chosen on dev from {2, 4, 8, 16}. Test is held out.
- **Convergence:** at most 4 rounds, stopping when under 1% of memberships change.
- **Pass:** as D3: at least +.03 over G0 and random removal on two of three sets, and gold-door waves down by no
  more than .02.
