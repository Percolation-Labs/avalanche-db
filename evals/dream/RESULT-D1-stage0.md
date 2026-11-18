# D1, stage 0: hubs learned from walks find gold-bearing clusters, but too thin to close the encoding gap

*18 Nov 2026, james. Registered first (REGISTERED-D1.md, #33). $0: store dumps, dev rows from bill's (b), test traces.
No Jev was spent, and the Jev stage was not run (see the decision below).*

## What was built

- **`d1probe`:** dumps a store's passage–key graph and writes hubs (one `tagged` literal per member) into a copy.
  The write half was built but not used.
- **`d1/cand.py`:** for each passage, a one-step personalised PageRank over the passage graph (shared keys weighted
  1/(df−1), plus next/near links), then a sweep cut at the least conductance, size 2–20. This gives 44,074 candidates
  on p8 and 18,696 on MuSiQue.
- **The model:** a logistic model over each candidate's structure (size, conductance, cohesion, density, mean
  degree, top-key share, top-key postings, novelty). It is fit on dev waves: is a raised hub holding unread gold?
  Kind is not a feature, and nothing was set by hand.

## Results (`d1/stage0.txt`)

**1. What the model learns from dev walks carries over to test, per wave.** On held-out test waves, the top-scored
raised hub holds unread gold more often than a random raised hub:

| set | top-scored | random | AUC |
|---|---|---|---|
| cards | .26 | .14 | .69 |
| PR titles | .25 | .17 | .63 |
| MuSiQue | .16 | .06 | .69 |

The held-back dev AUC was .64 on p8 and .77 on MuSiQue.

**2. Written graph-wide, the hubs are thin, and on PR titles learning doesn't help.** Writing the top 5% of
passages' worth of hubs, on test waves:

| set | gold per unread member: learned | random | test waves with a gold hub: learned | random |
|---|---|---|---|---|
| cards | .055 | .011 | .19 | .12 |
| MuSiQue | .021 | .008 | .25 | .10 |
| PR titles | .030 | .026 | .11 | .23 |

On PR titles the learned hubs are offered less often than random ones, so random wins on reach. The doors already
on offer reach .28–.65 at the best gold door (dev).

**3. Ceiling on (b).** These are the dev waves where Jev's first door is gold-free (cards 19, PR titles 56,
MuSiQue 35). Suppose Jev always opened a written hub whenever one held unread gold. Gold-first would rise by at
most:

| set | learned, 5% | learned, 20% | random, 20% |
|---|---|---|---|
| cards | +.07 | +.08 | +.08 |
| PR titles | +.06 | +.10 | +.46 |
| MuSiQue | +.10 | +.14 | +.05 |

The learned hub is as dense as the best gold door on 0–21% of these waves. Random hubs reach further on PR titles
only by offering about 7 hubs a wave, which Jev would also have to tell apart.

**4. Pruning is null.** Cutting keys whose postings are incoherent doesn't help Jev. Cohesion separates gold term
doors from gold-free ones only weakly (AUC .58–.65). With Jev's ranking applied, cutting the least coherent 25–75%
of keys puts gold first no more often than cutting at random (PR titles .21 → .21, .21, .11; random .23, .20, .19).
Jev's wrong top doors are coherent too.

## Decision

The Jev stage is not run. Pass needed +.05 on (b) against both G0 and random hubs on two of three sets. The
generous ceiling allows that on cards and MuSiQue only if Jev opened nearly every gold-holding hub. On PR titles,
the set the encoding gap is about, random hubs beat learned ones.

**Deviation from the registration:** the registered $0 measures were not run on written stores (share@5, the
oracle's recall@10 and bill's AUC). Share@5 is already .86–1.0 in G0, so it can't separate arms. The ceiling above
bounds what any arm could add to (b). This is stated here, not hidden.

## Postmortem

- **The reward taught the wrong thing.** "Holds unread gold" rewards clusters that sit near relevant material. That
  carries over (AUC .63–.69), but it is not the encoding objective. A hub is worth writing only if it becomes the
  door that is both gold-dense and preferred. The reward never asked for density relative to the competing doors,
  or for anything Jev could see.
- **Why the clusters are thin.** Conductance of the chosen cuts is .86–.94. Shared keys are so dense that a local
  PageRank sweep can't find a closed community, so the cut is a loose neighbourhood, not the answer's substructure.
  The Steiner result says gold pairs are mostly linked to each other. A cluster of 2–20 around one passage is the
  wrong unit for that.
- **What it suggests next.** Write **edges, not clusters**, learned as link prediction. From training walks: which
  pairs of passages turn out co-relevant (both gold), as a function of their structure (shared keys and their
  postings, next/near, common neighbours). Then write the top-scoring pairs graph-wide. The $0 test on held-out
  questions: the share of test gold pairs that are not yet one door apart and that the written edges connect,
  against common-neighbour and random controls. Fewer reads between gold is bill's (a), measured directly.
- **Process:** about 2 hours, $0. The pre-gate should have been the registered gate. A ceiling on (b) is cheaper
  and more decisive than the saturated share@5.

## Files

All under `d1/`; run from the scratchpad that holds the dumps and traces:
- `cand.py`: the candidates;
- `reach.py`: raised hubs vs doors on dev;
- `keyfeat.py` and `prune.py`: pruning;
- `gate.py`: per wave;
- `gate2.py`: graph-wide;
- `ceiling.py`: the ceiling on (b);
- `stage0.txt`: the output;
- `../d1probe/`: the dump and write tool.
