# Search's tail against the first door ($0, 18 Nov; Sirsh M-20261118-164404-1519)

Test sets. Search's top 50 is from a no-key walk (`--reads 50 --seeds 50`). Today's walks are from the trace replays,
which match their recordings 393/393. Numbers are in tail.txt, from tail.py.

| | cards | PR titles | MuSiQue |
|---|---|---|---|
| gold per read, search ranks 1–5 / 6–10 / 11–20 / 21–50 | .073 / .043 / .017 / .006 | .215 / .052 / .028 / .007 | .205 / .028 / .025 / .007 |
| gold beyond search's top 50 | .56 | .36 | .38 |
| ranks 6–10 when the seeds hold 0 / 1 / 2+ gold | .038 / .059 / .025 | .080 / .052 / .029 | .059 / .025 / .006 |
| gold per read behind Jev's first door | .117 | .030 | .100 |
| that door's gold outside search's top 50 | 53/80 | 0/12 | 36/62 |

## Postmortem

- **Expected:** search's tail pays only when its top is rich.
- **Found:** it runs the other way. A rich top predicts a poorer tail, because the question's few gold documents are
  already taken. The tail is richest when the seeds miss, and even then it is thin (.04–.08 a read).
- **Doors against the tail:** on cards and MuSiQue the first door beats the tail by 2.7–3.6× a read, and most of its
  gold is gold search would never reach. On PR titles it does worse than the tail and reaches no gold outside search's
  top 50.
- **Where the fault is:** links to PR-title gold do exist (the structure study, evals/structure). The fault is in
  which door is described and chosen, not in the graph's reach.
