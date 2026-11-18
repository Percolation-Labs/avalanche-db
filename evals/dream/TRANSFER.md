# Do harmful doors recur from a training log to new questions? Almost never ($0, 18 Nov 2026)

On each dev question's wave-1 batch, a "harm" door is a gold-free door Jev ranked above the best gold door. On the
held-out test sets' wave-1 batches, the same question is asked of the doors above gold: were any of them harm doors
on dev?

| | cards | PR titles | MuSiQue |
|---|---|---|---|
| test batches where a gold-free door outranks gold | 40 | 74 | 53 |
| doors above gold that were dev harm doors | 1/117 | 52/901 | 20/286 |
| batches where every door above gold was a dev harm door | 1 | 1 | 4 |

## Postmortem

- **Expected:** a dreaming operator that adds or prunes link instances from a training log of walks.
- **Found:** it can't reach new questions. Each question raises its own doors (its seeds' terms, their neighbours),
  so a log of 65–101 questions sees almost none of the instances a new question will meet.
- **Where learning can work:**
  - (i) a log that covers the graph: walks the dreaming process makes itself over every region, not only where
    questions happened to go;
  - (ii) a learned function of what a door is (its structure), which generalises across instances. This must not
    become a per-kind weight or a corpus base rate, so it needs Sirsh's ruling on the line.
- **Next:** dreaming learns from self-generated walks over the whole graph.

## Addendum: does a larger self-play pool cover new questions? Slowly (cards, $0)

The pool is the eligible cards that are neither dev nor test: 265 of 515, built by `cards.py` at the pinned commit.
`raise1.py` raises each pool card's wave-1 doors with no key (wave 1 depends only on the seeds, so this is $0).

- The pool raises 34 (.29) of the 117 test doors that outrank gold. Dev's 100 questions raised 20 (.17).
- 29 of those 34 were gold-free on every pool question that raised them.
- The pool raises .42 of all test wave-1 doors.
- 265 questions raise 18,670 distinct doors.

Coverage grows sublinearly with the pool, because doors are long-tailed. Learning door by door from structure-derived
questions would need a pool far larger than the corpus offers (515 eligible cards in all). Dreaming has to learn
something that generalises across doors, or make its probes from every passage. The latter is about 48,636
pseudo-questions on p8, which is $0 to raise but costs dollars to rank with Jev.
