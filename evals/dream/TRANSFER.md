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
