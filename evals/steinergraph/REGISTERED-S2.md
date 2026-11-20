# S2 and S3, registered: cut a link the oracle tree uses, then let walks find it again without the oracle

*20 Nov 2026, james. Answers Sirsh's 17:11Z brief: the drift case and the learning question. bill takes S1 (how
the walk uses the oracle tree) and S4 (when the tree emerges across seeds). $0, no Jev, no Claude-generated data.
Nothing is fitted, and nothing depends on a chosen constant: every number below is either a property of the
graph or the walk's existing budget (5 reads past the seeds, as in P1, P2, L1 and L2).*

## Objects

- **Graph:** L1's graphs (`graph-p8`, `graph-mq`). A link between two passages is a shared key held by 2–100
  passages, or a Beside or Near door. These are the doors L1's walk can step through. *(Amended before any scoring:
  the first draft left out Near, but the walk traverses it, so a pair joined by Near isn't singly joined.)*
- **The oracle tree T\*:** for each question, the terminals are its gold passages plus the seed set, contracted to one
  root so that any seed can attach it (bill's S1 definition). T\* is the shortest-path Steiner tree
  (Kou–Markowsky–Berman) over the unweighted link graph, with ties broken by passage id. On the graph as built it is
  checked against bill's exact Dreyfus–Wagner tree (`tstar-{set}.jsonl`), and any size gap is reported. Its **cost**
  is the number of passages it holds that aren't terminals.
- **Walk:** L1's PPR at UNI, from search's 5 seeds. **Recall** is the share of gold beyond the seeds in the top 5 (L1's
  recall@5).

## S2: drift

**Cut.** A gold pair is *singly joined* if exactly one link joins it: one shared key and no Beside or Near door either way. Removing that key
from one of the two passages is the drift. It is what an extractor that misses one entity does, and it also drops
that passage's link to every other holder of the key. The key is removed from the passage that isn't a seed. If
neither or both are seeds, it is removed from the one later in id order.

**Control cut.** From the same passage, remove the key of the same K1 family whose width is closest to the cut key's
(ties broken by key text) and that joins no gold pair. That is the same amount of damage to the same passage, off
the tree.

**Cases.** In the test split of cards and MuSiQue, the first four questions by qid with a singly joined gold pair.
PR titles has 7 such pairs on dev, too few to count, so it is reported only. The aggregate runs over every singly
joined test pair, one cut per question (the first such pair by id).

**Measured per case**, on the graph as built, after the cut, and after restoring the key:
- T\*'s cost and the passages it adds;
- the walk's recall, and the rank of the passage that lost the key;
- the same two measures after the control cut.

**Directional gate:** on at least 3 of 4 cases in each set, the cut raises T\*'s cost or lowers the cut passage's
rank, and the control cut does neither. Restoring the key brings back the original values exactly, which is a
check on the code. If the gate fails, I report it and stop before the aggregate.

**Aggregate bar:** the paired difference in recall, cut minus control, is below 0 with a bootstrap 95% interval
below 0 on both sets.

## S3: repair from walks alone

**Setting:** the drifted graph with every aggregate cut applied at once.

**Candidates come only from walks.** Run the walk for every question, dev and test, with no gold. Let R be the 5
seeds plus the top 5, as in L2. A candidate is a pair of passages that appear together in the R of at least two
different questions' walks and are not linked. Two is the smallest number at which separate starts agree, which is
P3b's reading of coherence. The candidate source is gold-free.

**Proposal and acceptance:**
- A repair adds the pair as a Beside link, the graph's existing direct link, so it needs no new weight.
- Each round, the candidate with the largest gain in L2's mean coherence over all walks is accepted, the walks are
  rerun, and the candidates are rebuilt.
- The loop stops when no candidate gains.
- The reward is L2's coherence, with its strength matrix taken from the drifted graph. Gold is never read.

**Scored after the loop stops:**
- (a) **Recovered:** the share of cut pairs that now have a direct link again.
- (b) **Rank:** the rank of each cut pair among the first round's candidates, ordered by gain.
- (c) **Recall:** walk recall on the cut questions, against the drifted graph and the graph as built.
- (d) **Collateral:** the same loop run on the graph as built, with nothing cut. How many links does it add, and
  does recall change? This is the false-repair rate.

**Controls:**
- *Random repair:* add as many links as the loop added, drawn uniformly from the same first-round candidate pool.
- *Hub repair:* the same number of candidates, taken by the product of the endpoints' degrees.

**Directional gate (4 cases, run first):** at least 2 of the 4 MuSiQue cut pairs and 2 of the 4 card cut pairs are
recovered within the rounds the loop takes. The random repair recovers fewer. If neither set passes, I report it and
stop.

**Bar:** recovered share above the random repair's share, with the cut questions' recall gaining back at least half
of what the cut cost, on at least one set. Collateral recall on the graph as built must not fall by more than its
bootstrap interval.

**What each outcome would mean:**
- **Pass:** walk co-occurrence plus coherence finds missing structure without the oracle. That is the "a learning
  process can bring it back" step of the story.
- **Fail with low rank:** coherence doesn't prefer the true repair.
- **Fail with the pair never a candidate:** walks never read both ends after the cut, so what is missing is the
  candidate source and not the reward. S4, on how many seed sets it takes before the tree shows up in co-reads, then
  says how much walk data a repair needs.
