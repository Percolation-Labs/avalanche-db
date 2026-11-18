# Result: D0, the encoding gap is not in which sentence stands for a passage (18 Nov 2026, $0.177)

**No text headroom on any of the three sets (registered rule: 0 of 3 pass).** Dreaming therefore writes links, not
lead sentences, and D1 is planned on links. The numbers are in d0-score.txt. There are 89 cases: dev wave-1 batches
where Jev ranked a gold-free door above a door with gold (18 cards, 45 PR titles, 26 MuSiQue). The request builder
reproduces every recorded request's bytes (sha check), and only the changed door's request was re-sent.

| | cards | PR titles | MuSiQue |
|---|---|---|---|
| gold door to the top by the best of 3 fixed sentence rules | .39 | .11 | .12 |
| ... by the question-matched sentence (`q-best`, could never ship) | .50 | .11 | .08 |
| top gold-free door displaced by some rule | .56 | .69 | .38 |
| gold door's mean P change across the rules | −.007 to +.008 | −.015 to .000 | −.013 to −.003 |
| top door's mean P change across the rules | −.034 to −.017 | −.064 to −.029 | −.020 to −.018 |
| gold door's leads that had another sentence to choose | .51 | .63 | .89 |

## Postmortem

- **Expected:** a gold door ranked low because its passages were shown by the wrong sentence; a better sentence
  existed, and dreaming could learn to pick it.
- **Found:**
  - The gold door's P barely moves when its leads change, within ±.015 on average. Even the sentence sharing the
    most words with the question doesn't move it, so no learned sentence choice could.
  - What moves is the top gold-free door. Any change from its first sentences lowers its P (−.02 to −.06). Its
    "displacement" is that door getting worse, not the gold door getting better.
  - First sentences are already what Jev values most, and that holds for every door alike.
- **Mechanism:** Jev's P responds to what a door is (its head, its width and kinds, its names) and to the batch,
  not to which sentence of a passage it is shown. This agrees with bill's earlier null on question echo (P doesn't
  follow word overlap with the question).
- **What it rules out:** sentence-level text as the thing dreaming writes.
- **What remains:** the graph's links themselves. Which doors exist, how wide they are, and what they connect is the
  structure that decides whether the right door can be told apart. bill's structure study shows PR-title gold sits
  behind width-2 next/merge doors.
