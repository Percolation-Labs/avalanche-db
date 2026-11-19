# K1: key families separate found from not-found where total coherence doesn't, but the sign flips between corpora

*19 Nov 2026, bill, for james's L3. Registered first (REGISTERED-K1.md, 4bc4b89). $0, dev only. Output: `k1.txt`.*

Dev questions at L2's fitted θ. Each value is the AUC of found (gold in the top 5 beyond the seeds) against not found.
A star marks an interval that excludes .5.

| | cards (100, 36 found) | PR titles (65, 38) | MuSiQue (101, 13) |
|---|---|---|---|
| **total coherence (L2's reward)** | .562 | **.775*** | .527 |
| number: share | **.708*** | **.278*** (reversed) | .611 |
| number: ratio | .683* | .269* (reversed) | .615 |
| code: share / ratio | .515 / .531 | .429 / .446 | (no code keys) |
| phrase: share / ratio | .484 / .603 | .444 / **.717*** | .519 / .621 |
| word: share / ratio | .590 / .581 | .389 / .596 | .467 / .457 |
| beside: share / ratio | .438 / .401 | **.727*** / **.845*** | (no next links) |

**Verdict, by the registered rule: a family separates on two sets, so L3's ceiling is above L2.** The
caveat below decides whether L3 can reach that ceiling without gold.

## What it says

- **On cards, total coherence doesn't separate (.56), but number keys do (.71).**
  - Walks that find gold carry more of their strength through numbers: card ids, dates, `rem 505`.
  - On cards L2 recovered 64% of L1's gain, not significantly. *Hypothesis, since contradicted:* a number-family
    weight is the part of the signal L2's single reward dilutes. L3 (avalanche-db #52, RESULT-L3.md) fitted
    coherence per family, pushed the number weight down on cards (β −1), and lost −.061 held-out. Coherence doesn't
    reward what found walks favour there.
- **On PR titles, Beside carries it.** Its ratio (.845) is above total coherence (.775), as is the phrase ratio
  (.717). PR walks that find gold stay within linked sequences.
- **The number family flips sign between the two p8 sets.**
  - On cards a high number share goes with finding gold. On PR titles it goes with missing it (.28): there,
    numbers are version strings and PR numbers that join unrelated changes.
  - **One weight per family therefore has to be learned per corpus.** That is the corpus-specific fit Sirsh asked
    to be flagged (14 Nov). It is legitimate only because the reward needs no gold, so the product can fit it on
    its own corpus.
- **MuSiQue shows nothing,** with only 13 of 101 dev walks finding gold, so the power is low. MuSiQue has neither
  code keys nor next links.

## For L3

- **The ceiling exists** on cards (number) and on PR titles (Beside, phrase).
- **The open question is the one K1 can't answer.** Would maximising coherence with per-family weights move those
  weights in the direction found walks favour? Coherence and found agree in total on PR titles (.775) and not on
  cards (.562).
  - If L3's reward is coherence, on cards it may pick a number weight for coherence's sake rather than for
    finding gold.
  - A $0 check before L3: on dev cards, does the number family's ratio correlate with total coherence across θ? If
    raising the number weight raises coherence, the reward will find it.

## Postmortem

- **Families were fixed by surface form, before looking.** The sign flip was unexpected. It means "number" isn't one
  kind of door: card ids and version strings share a form and differ in meaning. A finer family set would need
  types the ingester knows (ids, dates, versions), which would be new labels rather than forms.
- **Multiple chances.** There are 30 family AUCs (5 families × 2 measures × 3 sets), with 7 stars. Share and ratio
  for the same family are strongly correlated, so these are closer to 15 tests. The stars fall on 4 family-by-set
  cells (cards number; PR titles number, phrase and Beside), against about .75 expected by chance. The signal is
  real, but any single cell isn't secure. *Corrected after james's review:* I first counted 8 stars, which included
  PR titles' total coherence, and that isn't one of the 30.
