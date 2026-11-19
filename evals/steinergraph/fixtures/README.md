# Steiner fixtures

One JSON file per held-out test question: cards 150, PR titles 93, MuSiQue 150. They are built at $0 from the graphs
as stored, by `fixtures.py`. `examples.py` names worked examples by fixed rules (`examples.json`) and draws one SVG
per example (`svg/`).

**Each file holds:**
- `question`, `gold`, and `seeds` (search's top 5). Each seed carries `doors_to_gold`, its door distance to the
  nearest gold: where the seeds land.
- `steiner`, the actual connectivity: an approximate Steiner tree over the gold, plus the path in from the nearest
  seed.
  - Kou's method: shortest door paths between terminals, a minimum spanning tree, then the paths expanded. Paths
    take the fewest doors, and among equals the narrowest.
  - Each link lists the doors that make it: a shared key with its width, Beside, or Near.
  - Also: `cost` (links), `gold_pair_doors`, `entry` and `detached_gold`.
- `potential`, the potential connectivity: how many passages lie within 1 and 2 doors of the seeds, how many gold
  among them, and the uniform spread's top 20.
- `walk_reads`: the recorded k=10 Jev walk's reads, by wave.
- `top5` and `recall5`: the top 5 beyond the seeds under search (S), the uniform avalanche (U), the question-aware
  avalanche (Q, P1) and Q on L1's learned weights (LQ).

`<set>/index.jsonl` has one summary row per question, keyed on `qid`, to join with bill's P2 rows.

**Things to know when reading them:**
- The shortest door path between two gold passages is often incidental. A MuSiQue pair joined in the text by a
  university joins in the graph through a quarterback's paragraph on "football quarterback", because the university's
  key is held by more than the 100-passage cap.
- Within 2 doors of the seeds lies most of the graph (MuSiQue 18–19k of 21,100), so "potential" is close to
  everything at depth 2.
- No card question has its nearest seed 2 or more doors from gold, so `cards-misses` is empty.
