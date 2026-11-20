# S2c result: PASS. Cutting the tree's own link costs the walk the passage; a matched cut off the tree doesn't

*20 Nov 2026, james. Registered in REGISTERED-S2c.md (11c9190). $0, no Jev. Code `s2c.py`; output `out/s2c.json`,
`out/s2c.txt` and `out/s2c-cases.txt`.*

**Count first.** This is the third cut definition. Each was registered before it was scored. S2 cut the one key
joining two gold passages, counted in hops, and failed its gate. S2b used the same cut, priced by step cost, and
failed its gate. S2c, cutting the tree's own link, is the one that passed. Read it as one success among three
registered tries.

## Result (test)

| | MuSiQue | cards |
|---|---|---|
| gate (4 cases) | 4/4 | 4/4 |
| qualifying questions (paired with a control) | 133 (132) | 133 (117) |
| log rank of the cut passage: cut / control | +0.480 / +0.017 | +0.548 / +0.051 |
| **cut − control** | **+0.463 [+0.370, +0.557]** | **+0.497 [+0.385, +0.622]** |
| recall@5, cut − control | −0.071 [−0.114, −0.033] | −0.013 [−0.040, +0.014] |
| T\*'s added cost (UNI nats): cut / control | +0.83 / −0.01 | +0.85 / +0.00 |

- **Bar met on both sets:** the cut pushes the passage down by a factor of about 1.6 in rank (e^0.46–0.50). The same
  amount of damage to the same passage, off the tree, does almost nothing.
- **Recall falls on MuSiQue and not on cards.** On cards the cut passage usually sits outside the top 5 even before
  the cut (median rank in the hundreds), so pushing it further down doesn't change recall@5.
- **The gate cases understated MuSiQue:** +1 to +6 ranks on 4 cases, but +0.46 log rank over 132.
- **PR titles, reported only:** 2/4. 31 of 56 tree edges there are door-only (Beside or Near), so there is no key to
  cut. On PR titles the tree runs on adjacency, as K1 found.

## What it says for Sirsh's story

"We can measure how far a graph has drifted from good" now has a working instrument: T\*'s cost in the walk's own
nats. A real drift on the tree adds about 0.8 nats, which is a factor of about 2.3 in the probability that the walk
takes the tree's path, and a control drift adds 0. The walk's loss follows the tree's cost, not the size of the
damage.

## Postmortem

1. **Two failed definitions came before this one, and both were predictable from data in hand.** P2's saturation
   predicted S2. bill's 4 cases, which showed gold reached from the seeds, predicted S2b. The lesson that worked: read
   the tree's edges on one case before choosing what to damage.
2. **The rank-based gate was right.** By construction the cut raises T\*'s cost, so a gate on cost would have been a
   tautology. The walk's rank is the independent check, and it agreed.
3. **Control coverage:** 16 of 133 cards had no eligible control key and are dropped from the paired test. They
   aren't selected on outcome. The rule is on keys alone.
4. **Next is S3:** can walks and coherence put these links back without the oracle? bill's S4 predicts the candidate
   source is the weak point. S3 reports that before any ranking.
