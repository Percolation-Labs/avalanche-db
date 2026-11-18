# How the graph lets a walk reach the answer (18 Nov, bill, $0)

Registered in [REGISTERED.md](REGISTERED.md) (5e2cfad) before any run. Output: `out/`, `score.txt`. The probe is
`E2E_STRUCTURE=1 evals/e2e/probe`, in `src/structure.rs`. `prs-m` used the probe built with
`evals/e2e/prs/candidates-M-H1.patch`, so that its doors include merge doors.

**Deviation from the registration.** The shuffled-links control is measured at distance 1 only: each seed door keeps
its width, and its targets are drawn at random. Distance 2 under shuffling would need a shuffled copy of the whole
graph. The random-seeds control has all of measures 2–4.

| k=10 test sets | cards | PR titles | PR titles + merge | MuSiQue |
|---|---|---|---|---|
| walk − search at k=10 | **+.186** | −.042 | −.011 | **+.134** |
| gold in search's top 10 | .27 | .47 | .47 | .44 |
| **orthogonal gold** (beyond search's top 100) | **.51** | .30 | .30 | .36 |
| orthogonal and 1 link from the seeds | .49 | .27 | .30 | .27 |
| orthogonal and ≤ 2 links | .51 | .30 | .30 | .36 |
| gold 1 link from the seeds: real links / shuffled | .80 / .04 | .58 / .04 | .62 / .04 | .48 / .14 |
| gold 1 link from random seeds | .06 | .04 | .04 | .17 |
| docs 1 link from the seeds (median frontier) | 1,155 of 48,636 | 1,096 | 1,096 | 2,113 of 21,100 |
| door carrying orthogonal gold at 1 link | term (145 of 155) | term 37, next 33 | merge 34, next 32, term 13 | term (100 of 108) |
| its width, median | 13 | 2 | 2 | 19 |
| gold pairs directly linked | .92 | .83 | 1.00 | .66 |

**Findings.**

1. **Every corpus has orthogonal gold, and the links reach all of it.** Between 30% and 51% of the gold is beyond
   search's top 100, and none of it is more than two links from search's five seeds.
   - The links are specific. The same seed doors with shuffled targets reach 4% of the gold (14% on MuSiQue), against
     48–80% for the real ones.
   - Five random seeds reach 4–17% at one link.
   - So "reachable" is a property of the question's seeds and the corpus's links, not of a dense graph.
2. **The answer is one hop away, behind a narrow door.** On every set, almost all orthogonal gold is at distance 1,
   behind a door of median width 2–19, in a frontier of about 1,100–2,100 documents.
   - The walk's whole problem is choosing that door out of a few hundred.
   - Path length isn't the issue: the walk never needs to go deep, only to choose right at the first step.
3. **A question's gold is linked among itself.** 66–100% of gold pairs share a direct link, mostly a narrow one (median
   width 2–19). So once one fragment is read, the rest is one more narrow door away. That is the percolation the walk
   exploits.
4. **The PR-title null isn't a lack of orthogonal gold.** By Sirsh's test (M-20261118-103637-390f), the walk's gain
   should track the orthogonal share. It does on cards (.51, +.186) and MuSiQue (.36, +.134), but not on PR titles
   (.30, −.042).
   - The PR orthogonal gold is behind width-2 `next` and merge doors: a commit's neighbours in its branch.
   - On cards and MuSiQue it is behind term doors of width 13–19.
   - Jev opens term doors and rarely opens `next` or merge doors (RESULT.md in evals/e2e). So the share is there, and
     the walk doesn't take it.

**What it suggests for the walk.** Not registered, and nothing is hard-coded per kind (Sirsh, M-20261118-103300-ceb0):
- A generic property of the graph, not of a corpus: the orthogonal gold is behind narrow doors joined to the seeds.
- Two candidates follow from that, for the walk that james owns:
  - A floor that keeps search's later ranks unless a door beats them.
  - Treating a door's width, the number of documents it would spend, as part of the choice, so a width-2 door costs
    2 of the budget against a width-13 door's 13.
- Both are to be registered, with the oracle and controls, on all three sets.
