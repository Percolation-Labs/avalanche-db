# J2: a wider candidate set raises the ceiling a little, and Jev keeps little of it; the limit is upstream, in what each sub-question's search reads

*19 Nov 2026, bill. Registered first (REGISTERED-J2.md, 8c56492). Jev spend $0.0241 (day total $0.0398). Output:
`j2.txt`, `j2pair.py`; rows in `out/j2/`.*

MuSiQue test, 150 questions, total recall at 10 reads (as in J1 and P2):

| seeds from | J1 candidates (top 3, ≤24) | J2 candidates (top 5, ≤40, no *and* joins, any number) |
|---|---|---|
| T: first candidate | .534 | .532 |
| J: Jev chooses | .578 | .586 |
| O: oracle chooses | .634 | .657 |
| gold answer is a candidate | 128/247 | 144/247 |
| Jev right, where it can be | 65/119 (55%) | 72/132 (55%) |

**Verdict: fail.**
- The $0 gate passed: O rose by +.023, against a gate of .02.
- J2's Jev beats J1's by only +.007 [−.016, +.031], against a bar of +.02 with the interval above 0. 9 questions went
  up and 6 went down.
- J2 still beats its own first candidate by +.054 [+.014, +.092], and blind sub-questions by +.081. It closes .31 of
  the decomposition gap, against J1's .28.

## What it says

- **More candidates means more distractors.** Jev's accuracy held at 55%, so the 16 extra decisions where the answer
  became available turned into about 7 more right picks. That is worth +.008, not the ceiling's +.023.
- **What still limits is search, at the hop.** In 103 of 247 decisions the gold answer isn't among the names and
  numbers of the top 5 passages for that sub-question. Wider extraction can't fix that. It is likeness again, now one
  hop in: whether each sub-question's search lands on the passage that holds its answer.
- **For the iteration argument (Sirsh 13:10):** J1 carries it, and J2 doesn't change it. Answer-then-search-again
  recovers ground that blind sub-questions don't (+.07 to +.08 over blind, in both runs). How much it recovers
  depends on each round's search finding the answer passage, and that improves only by learning from what was read.

## Postmortem

- **The gate was set at the edge, and this result sat on it.** A ceiling gain of .023 left at most about .012 for Jev
  to keep at 55% accuracy. That was below the +.02 bar before Jev ran. The gate should have been "ceiling gain ≥ bar ÷
  accuracy". Spend was small ($0.024), but the run could have been called at $0.
- **The next $0 check:** for the 103 decisions, is hop j's gold passage in the top 5 at all? If it usually isn't, the
  lever is the hop's search, for example the walk's own doors from what's been read, not the candidates.
