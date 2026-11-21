# A MuSiQue train door-key graph for fresh draws, and its calibration against dev's graph-mq

*21 Nov 2026, james. $0, with no Jev calls. Scripts: `build_keys.py`, `train_corpus.py`, `graph_calib.py`. Output:
`out/graph-calib.txt`.*

**Why.** Dev 2-hop is used up: positions 0–1171 of SR-KB's permutation are all scored. The |S| = 0 rescue rule
(SR-BT) and a better entry (SR-BW) need a fresh draw. MuSiQue train has the same construction, but dream-d1's graph
covers dev only.

**How dev's keys were made.** The fixture's manifest (`~/.cache/walklab/fixture-musique/manifest.json`) records:
- percolate-core 0.2.16's `frequency` strategy, with max_n 3, min_df 2, df_floor 20, df_share .02 and nest .9;
- indexed in Postgres and imported to an avalanche store;
- then dumped by d1probe with 2 ≤ df ≤ 100.

The Postgres store is gone. `build_keys.py` runs the same strategy in Python at the **declared limits, unchanged**, with
the same df window and ids. No setting is fitted to graph-mq. It doesn't reproduce graph-mq exactly: it shares 87% of
graph-mq's keys, and graph-mq keeps some unigrams nested in bigrams. So both corpora are rebuilt with it.

**Train corpus.** `train_corpus.py` draws 2,417 train questions (seed 1342), stratified to dev's exact count per hop
type, so df and the cap act on a corpus of the same make-up. Their pools hold 25,406 passages, against dev's 21,100,
because train pools share fewer passages. That's 20% larger, so the cap of 100 is slightly tighter relative to the
corpus.

**Calibration** (dev, seen sets; A is graph-mq, B is the rebuild):

| set | k A | k B | ceiling_k A | ceiling_k B | cosdoor A | cosdoor B |
|---|---|---|---|---|---|---|
| SR-KB 0–299 | .577 | .563 | .700 | .710 | .473 | .477 |
| SR-BN 600–899 | .587 | .553 | .720 | .713 | .493 | .463 |
| 904–1171 | .549 | .534 | .687 | .687 | .478 | .478 |

- k drops .015–.034 on the rebuild. The ceiling moves ±.01, and cosdoor 0 to −.03.
- Arms compared within one graph are paired, so a graph-wide shift of this size doesn't bias a difference. It does
  mean train-graph levels shouldn't be compared against graph-mq's levels on dev.

**Paths** (local cache, not in git):
- `~/.cache/walklab/mq-train/musique_ans_v1.0_train.jsonl`: public MuSiQue train, sha256 83a75b1e….
- `train-corpus.jsonl`: the 2,417 sampled questions.
- `graph-train-pc.jsonl`: the train graph.
- `graph-dev-pc.jsonl`: dev, rebuilt the same way.
