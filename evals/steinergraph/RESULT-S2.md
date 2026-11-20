# S2 result: directional FAIL. Counted in hops, the oracle tree is trivial, so cutting one link can't change it

*20 Nov 2026, james. Registered in REGISTERED-S2.md (e60b0f2, amended 4e1b0ba before scoring). $0. Code: `s2.py
--cases-only`. Output: `out/s2-cases.txt` and `.json`. The unregistered diagnostic is in the scratchpad's
`s2diag.py`, and its numbers are below. Per the registration, I stopped before the aggregate and S3.*

## The gate

The gate needed 3 of 4 cases to agree in each set. A case agrees when the cut raises T\*'s cost or lowers the cut
passage's rank, and the control cut leaves both alone.

| set | cases agree |
|---|---|
| MuSiQue | 0/4 |
| cards | 0/4 |
| PR titles (reported only) | 1/4 |

Restoring the key gave back the exact as-built values in all 12 cases, which is the code check.

- **T\*'s cost was 0 before the cut in all 12 cases.** It rose in one case, to 1 (MuSiQue, 'tang').
- **The cut passage's rank fell in 7 of 12 cases.** Sometimes it was large (card REM-185: 7,678 → 26,169), more often
  small (10 → 11).
- **The control cut did about as much in two cases.** 'great britain' moved its passage 10 → 11, the same as the real
  cut 'north american'.
- **Recall@5 didn't change in any case.**

## Why: in hops, the tree is the gold passages themselves

Diagnostic on the test split, not registered:

| test | T\* cost 0 / 1 / 2 | gold beyond the seeds with a direct link to a seed |
|---|---|---|
| MuSiQue (133) | 120 / 11 / 2 | 193 / 245 |
| cards (135) | 134 / 1 / 0 | 254 / 264 |
| PR titles (87) | 84 / 3 / 0 | 153 / 166 |

With 325 links per passage on p8 and 530 on MuSiQue, nearly every gold passage is one door from a seed. So the
minimal reachability set is the terminals and nothing else. Cutting the one key that joins two gold passages leaves
each attached to the seeds through other keys, at the same cost. This is P2's finding again, now in tree terms:
distance is saturated, and what limits the walk is the step probability. A hop-counted Steiner tree can't show
drift on these graphs, because it is the same with or without the cut.

## Postmortem

1. **The registration measured T\* in the wrong unit.** I took "minimal reachability set" to mean fewest passages. P2
   had already shown that every question sits at distance 1, so the outcome was predictable from a merged result.
   That should have been checked before registering. It took one 30-second diagnostic.
2. **The control was weaker than registered:** 9 of 28 card cases and 5 of 11 PR cases had no key of the same
   family that missed gold. That isn't the reason for the fail (MuSiQue had controls for 61 of 63), but a rerun
   needs a fallback.
3. **What carries over:** the cut's effect shows up only in the walk's *probability*, as a fall in rank, never in
   hops. So the tree has to be weighted by what a step costs the walk.

## What I'd do next (to be registered before anything runs)

Weight each link by the walk's own one-step cost. That is −log of its UNI transition probability, so a link through a
key of width w costs about log w more than a narrow one. Then T\* is the *most probable* tree connecting seeds and
gold, and cutting a narrow key forces the tree through wider ones. That should show drift where hops couldn't. It
adds no constant: the weights are the reference walk's transition probabilities, and the L2-fitted θ is reported
beside them (bill's point 2). S3's repair loop and bill's four review points (a co-read-count control, LC θ beside
UNI, flagging pairs that are trivially co-read as seeds, and a paired collateral test) carry into S2b/S3 unchanged.
