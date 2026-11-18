# How the graph lets a walk reach the answer: a descriptive study, registered before any run

*Registered 18 Nov 2026 by bill. Sirsh's steers M-20261118-103300-ceb0 (study the structure: reachability, path
length, how fragments connect) and M-20261118-103637-390f (semantic orthogonality: a link earns its place only if it
leads where search wouldn't). The split with james, agreed on the board (M-20261118-103347-a17b): james takes the
walk's floor, bill the structure. $0. No Jev; nothing is chosen or tuned.*

## Corpora and questions (the registered test sets; no new questions)

| | store | questions |
|---|---|---|
| p8 cards | `e2e-p8i` | `cards.jsonl`, 150 |
| p8 PR titles | `e2e-p8i`, and `e2e-p8m` (with merge edges) | `prs-test.jsonl`, 93 |
| MuSiQue | `e2e-mq3` | `musique-questions.jsonl`, 150 |

## The graph

**Links** are the walk's own doors, exactly as raised (`d6::doors_of`, term cap as in the walk):
- term doors;
- `next` doors;
- `near` doors;
- merge doors, on `e2e-p8m`.

Two documents are linked when one's door lists the other. All four kinds are symmetric by construction except `near`,
which is treated as undirected here, and that is said with the numbers.

## Measures, per gold document, then per question and corpus

1. **Semantic findability.** The gold's rank in full-text search for the question: top 10, 11–100, beyond 100.
   - **Orthogonal gold** is gold beyond search's top 100.
   - The orthogonal share is the corpus's share of gold that semantics doesn't reach.
2. **Link distance from the seeds.**
   - The seeds are search's top 5, the k=10 walk's seeds.
   - Distance is 0 for a seed, 1 if a seed's door lists the gold, 2 if a document one hop out does. Distance 2 is
     computed as an intersection: the docs within 1 of the seeds against the docs whose doors list the gold.
   - Beyond 2 is reported as ">2".
   - Reported by the kind of the last door on a shortest path.
3. **Frontier size.** The number of distinct documents within 1 hop of the seeds, the denominator of how lucky
   reaching the gold is.
4. **Orthogonal and linked.** The share of gold that is beyond search's top 100 and at distance ≤ 2. This is the
   share a walk can earn that search can't, by Sirsh's test.
5. **How fragments connect.**
   - Per question with 2 or more gold: the share of gold pairs directly linked, and the number of connected
     components among the gold under links.
   - The links that join gold pairs, by kind and by door width (a door listing 3 documents is a specific link; one
     listing 200 is a hub).

## Controls

- **Random seeds:** 5 documents drawn at random per question (seed 1118), the same measures 2–4. "Reachable from the
  seeds" means more than "reachable from anywhere".
- **Shuffled links:** each door keeps its size, its targets drawn at random from the corpus (seed 1118), with
  measures 2–5 rerun. "Reachable" means more than "the graph is dense".

## What it will be used for

- To state each corpus's walk gain at k=10 against its orthogonal-and-linked share (measure 4), in the write-ups.
- To decide, with james's floor study, what the walk needs: which links carry orthogonal gold and at what width,
  and where the share is near zero, so the walk holds search's floor.
- Any change that follows is registered separately.
