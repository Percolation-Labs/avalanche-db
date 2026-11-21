# SR-E (registered 21 Nov, before scoring): does landing on an entry that names its link find the chain?

*bill. THEORY-SR item 2. $0, no Jev calls. Script `sre.py`. james reviews before scoring.*

**Serves.** THEORY-SR item 2 says the entry hop is likely a graph property, and repair should present entry doors whose
passage names its link. SR-K showed the link is visible without gold *given* the entry: a rare shared key door, leaving
out the question's own keys, ranks hop 2 first in .95. SR-E turns that around. Choose the entry *by* whether it has such a
link and whether entry plus link jointly cover the question. Does that land the 2-hop chain more often than cosine?

**Data.**
- MuSiQue dev, the first 200 answerable 2-hop questions. Each has its own pool of 20 passages, and the dream-d1 graph
  covers every passage.
- The first 40 are SR-K's questions. SR-K looked at their hop 2 given hop 1, not at the entry. Results are also reported
  on questions 41–200 alone.

**Arms.** Each picks an unordered pair and an entry. q is bge-small's query embedding, and ê is a passage's unit
embedding.
- `cos` (baseline): the pair is the top 2 by cos(q, ·), and the entry is the top 1.
- `door`:
  - Each passage v's link u\*(v) is the passage with the most shared door strength, Σ 1/(df − 1) over door keys
    (2 ≤ df ≤ 100) not contained in the question's words, exactly as in SR-K.
  - The pair is argmax over v of cos(q, ê_v + ê_u\*(v)).
  - The entry is the pair member with the higher cos(q, ·).
- `vec` (control for "any link"): as `door`, but u\*(v) is v's nearest passage by cosine.

No arm has a parameter. The df range is the graph's own, as in SR-K.

**Gold-blind look before registering.**
- A first design scored each v by v plus its link, without choosing the entry. On the first question it picked the
  hop-2 passage as the entry, because a pair scores the same from either end. That's why the entry is now the member
  with the higher cos(q, ·).
- `door`'s entry equals `cos`'s entry in 82% of questions. So the entry metric can move in at most 18%, and the pair
  metrics carry the test.
- 721 of 3,999 passages have no door link.
- Question 1: `door` picks {Green (Steve Hillage album), Miquette Giraudy}, which is the chain. `cos` picks
  {The Odd Life of Timothy Green, Green (Steve Hillage album)}.

**Outcomes** (per question; paired bootstrap 95% CI over questions, 4,000 resamples):
1. **Primary:** `both`, meaning the pair = {hop 1, hop 2}, the 2-hop Steiner tree.
2. `entry`: the entry is hop 1.
3. `has1`: hop 1 is in the pair.

**Bar.** H1 passes if, on `both`, `door − cos` and `door − vec` both have CI lower bounds above 0, on all 200 and on
41–200 alone. A pass on `door − cos` alone means "any link helps", not "the door helps".

**Predictions:**
- `both`: door > vec > cos.
- `entry`: a small effect, at most ±.10, because the entry changes in only 18%.
- `has1`: door ≥ cos minus .05. The pair gives up the second-best cosine passage, which is sometimes hop 1.

**Scope.** In-pool retrieval: 20 candidates per question, not the 21,100-passage graph. MuSiQue 2-hop only. No walk and
no Jev. This tests whether the door picks the right *pair*. It doesn't test whether a walker presented with that door
takes it.
