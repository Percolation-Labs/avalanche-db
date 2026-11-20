# S2b result: directional FAIL again. The tree never used the link we cut

*20 Nov 2026, james. Registered in REGISTERED-S2b.md (1001db0). $0. Code `s2b.py --cases-only`; output
`out/s2b-cases.txt`/`.json`. Stopped before the aggregate and S3, per the registration.*

## The gate

The gate needed 3 of 4 cases in each set where the cut adds more step cost (nats, UNI with no F) to T\* than the
control does.

| set | cases agree | added cost, cut (control) |
|---|---|---|
| MuSiQue | 1/4 | 'north american' +0.00 (+0.14); 'niro' 0 (0); 'tang' **+2.76** (0); 'maine' 0 (0) |
| cards | 2/4 | 'rem 152' −0.04 (0); 'rem 185' +0.06 (0); 'rem 19' −0.03 (−0.02); 'rem 193' +0.44 (0) |
| PR titles (reported only) | 1/4 | one agreement is +0.004 against 0, a tie in effect |

- **Row 0, the hop tree:** +0 passages before and after the cut in 11 of 12 cases, as in S2.
- **Restoring the key gave back the built values exactly** in all 12 cases.
- **The second reference** (LC θ with search F) agrees in direction with UNI in every case.

## Why: T\* reaches each gold passage from the seeds, not from the other gold

The cut removes the one key joining two *gold* passages. But the cheapest tree from the seed root reaches every gold
passage directly from a seed in 11 of 12 cases (row 0: +0 passages). The gold–gold link is never on it, so cutting
it barely moves the tree. Sometimes the cost even falls: dropping a key from a passage removes it from that
passage's denominator too, and its other links become more probable (REM-152 −0.04). The one clear case, 'tang', is
the one where row 0 went from +0 to +1, the only cut that hit a link the tree used.

## Postmortem

1. **Two registrations made the same wrong assumption.** I treated "gold pair joined by one key" as "an edge of the
   tree". In a tree rooted at search's seeds, the edges are seed → gold. Gold–gold links are on it only when one gold
   is reached through another. That happens in about 10% of MuSiQue questions (row 0's 13/133) and almost never on
   p8. I should have read the tree's edges off one case before choosing what to cut. bill's 4 cases had already shown
   the shape ("gold one or two hops out", reached from the seeds).
2. **The cost change is still the right instrument.** The one tree-edge cut ('tang') is +2.76 nats against a control
   of 0, with the cut passage falling from rank 1,421 to 1,994. The measure sees drift when the drift is on the tree.
3. **Cost isn't monotone in cuts.** Removing a key renormalises the passage's other links. Any drift measure on p
   has to report signed changes, and so it does here.

## What I'd do next (to be registered first)

**S2c: cut the tree's own link.** For each question, take T\*'s most probable edge into a gold passage and drop the
key that carries it, from the gold passage. The control drops the nearest-width key from the same passage that isn't
on T\*. T\*'s cost will rise by construction, so the gate has to be on the *walk*: the cut passage's rank and recall
fall, and the control's don't, on 3 of 4 cases per set. Then S3 repairs those cuts. The candidate source stays
walks only, with bill's four controls.
