# Doors, deciders and the budget

*Proposed 15 Nov 2026 by james (M-20261115-210452-bce0), approved by Sirsh with one addition
(M-20261115-214829-2d55): doors carry attributes a decider can filter on, as Cypher edges do.*

A walk is likeness waves and connection waves ([p8ql.md](p8ql.md)). This spec is about one
moment in a connection wave: the walk is standing in front of a set of doors and has to pick
which to open. Three parts meet there, and each is replaceable on its own:

| Part | Owns | Never sees |
|---|---|---|
| **Door labeller** | what each door says: its attributes | the question, the gold |
| **Decider** | which doors to keep, and their order | the budget |
| **Caller** | the budget: how many reads, waves and doors | the decider's internals |

The walk layer owns none of the three judgements. It raises the doors, asks the labeller to
describe them, asks the decider to filter and rank them, opens the top of the ranking until
the budget runs out, and records all of it.

## A door is a typed edge with attributes

A door is the clue a read raises: `term:<t>`, `next:<doc>` or `near:<doc>` today, and any
typed link in the store generally. Like an edge in Cypher, it has a type and attributes, and
the attributes are what a decider may filter on:

- **Type**: the predicate it follows (`tagged`, `beside`, `near`, `authoredBy`, …).
- **Immediate**: what is right behind it, such as the targets' labels or openings.
- **Reachable**: a compressed summary of everything reachable through it, beyond the first hop.
- **Statistics**: graph numbers, such as how many unread targets it has, the term's postings
  (df), the targets' centrality and how specific the term is across the corpus.

**Integrity rule (Sirsh, 15 Nov, M-20261115-201816-ab76).** A door's attributes are derived
from the graph alone, never from the question or its gold. The labeller's signature has no
question argument, so the code enforces the rule. The decider is the only part that reads the
question, and choosing in the question's context is its job.

```rust
pub trait DoorLabeller {
    fn version(&self) -> String;                              // e.g. "graph-stats/1"
    fn label(&mut self, door: &Clue, g: &mut Graph) -> Result<Attrs>;
}
pub struct Attrs {
    pub kind: String,                        // the door's type
    pub immediate: Vec<String>,              // what is right behind it
    pub reachable: Option<String>,           // the compressed summary, when a labeller builds one
    pub stats: BTreeMap<String, f64>,        // targets, postings, centrality, specificity, ...
}
```

**Labels belong to construction.** Today a labeller runs at walk time over the graph. The
target is that labels are built once, at construction or by dreaming, and stored as facts
carrying the labeller's id and version, so the walk only reads them. A better labeller then
means rebuilding the labels, not changing code, and `AS OF T` shows which labels a walk saw.
Until that lands, the walk records the labeller version on every batch.

## The decider: filter, then rank

```rust
pub trait Decider {
    fn name(&self) -> String;
    /// Optional reduction over door attributes: the doors to keep, or None for all.
    fn filter(&mut self, b: &Batch) -> Result<Option<BTreeSet<String>>> { Ok(None) }
    /// The order to open the kept doors in, best first, with a score where it has one.
    /// A door it leaves out is unjudged, and is never opened.
    fn rank(&mut self, b: &Batch) -> Result<Vec<Ranked>>;
}
pub struct Batch<'a> { question, wave, doors: [(Clue, Attrs)], reads so far, label version }
```

Plain ranking is `rank` alone. **Filter-then-rank** is the addition Sirsh asked for, and it
is an idea to test, not a recipe. First the decider chooses which attributes matter, or ranks
them, and eliminates doors on them (for example "only `tagged` doors with fewer than 20
targets"). Then it ranks what is left. Both are one interface, and an evaluation can score
either pass alone.

The old `.5` gate is not part of the walk any more. It is a filter: `Gated { inner, at: 0.5 }`
keeps the doors whose score from `inner` is at least 0.5. That is how today's walks are
reproduced exactly (see Parity below), and no new walk needs it.

## The budget belongs to the caller

How many doors to open is not something a decider learns (Sirsh, M-20261115-204145-ce85).
The caller sets the budget:

- `waves` and `wave`: the walk reads at most `wave` documents per wave, `waves` times.
- `open`: at most this many doors opened per wave (default: no limit beyond the reads).

Each wave opens the top of the ranking, in order, until the wave's reads or its `open` cap run
out. The opening order is `order`:

- `rank` (the default) is the decider's order: by its score where it gave one, otherwise by
  position.
- `p`, `per_target` and `convergence` are the product's V0 orders over the decider's scores.
  They are kept only to reproduce recorded walks.

## Every wave records the whole batch

`Walk.batches` gets one entry per wave:

```json
{"wave": 3, "label_version": "graph-stats/1", "decider": "oracle",
 "doors": [{"key": "term:paris", "kind": "term", "targets": [...], "attrs": {...}}, ...],
 "kept": ["term:paris", ...] | null,
 "ranking": [{"key": "term:paris", "score": 0.91}, ...],
 "opened": ["term:paris"]}
```

This is the durable step that today's cache lacked. Scoring a new decider meant replaying
walks, and a replay stops as soon as the new decider opens a door the old walk never judged
(meta/lab/results/topk-open, #765). With whole batches recorded, any decider can be scored as
a ranker on every recorded batch at $0. `lab::rescore(walk, question, decider)` reranks the
recorded batches without walking, and `lab::rank_metrics(ranking, relevant, k)` returns MRR,
NDCG@k and recall@k against oracle labels. A door is relevant when one of its targets is gold.
That is the measurement Sirsh asked for on 15 Nov (M-20261115-204054-124e).

## Search at an equal budget is built in

`SearchOrder` is a decider: it ranks doors by the best search position among their targets.
Run under the same budget, it is the baseline every walk result is compared with (memory
`round-one-is-search`). The other fakes are `Oracle` (doors with gold targets first, the
upper bound on any decider for those doors), `Random` (seeded), `Scores` (fixed scores by
key, from a recording) and `AttrFilter` (a filter pass over one statistic). The real deciders,
Jev and the System One models, plug in through the same trait; that research is bill's.

## What changes where

- **`lab serve`** (JSON lines). The request may carry `"question"`, `"open"` and `"order"`. A
  judgement message now carries each door's `attrs` and the `label_version`. The answer may be
  `{"p": {key: P}}`, as before (scores; `gate` in the settings makes it the legacy filter),
  or `{"keep": [keys], "rank": [keys]}` for filter-then-rank. **Breaking:** a caller that
  relied on the default `.5` gate must now pass `"gate": 0.5` and `"order": "per_target"`.
  No caller in p8-subsystems main uses `lab serve` today.
- **P8QL `WALK FROM … BUDGET n`** runs `session::walk`, which ranks by fixed preference
  weights. Its convergence step is a `Decider` whose rank is the preference weights, with
  `BUDGET` as the caller's budget. A future `WALK … USING <decider>` names the decider, and
  `EXPLAIN` prints the decider, the labeller version and the budget.
- **MCP `step`** returns the batch it ranked (doors, attributes, ranking) instead of only the
  neighbours, so an agent acting as the decider sees what a decider sees.
- **`session.rs` and `explore.rs`** keep their own loops for now. `explore`'s draw from P is
  a `Random`-weighted decider, and `session`'s steer is a decider that takes the agent's
  choice. Both move onto the trait once the lab walk's batch log has been used for one
  evaluation, so the shape is tested before three loops depend on it.

## Parity

The refactor must not change any walk that today's code produces. `Gated { Scores, 0.5 }`
with `order: per_target` reproduces today's walk read for read. Two tests check this:
`tests/doors.rs` compares against a golden file captured from the pre-refactor engine, and
`evals/doors/parity.py` replays fixture-musique's 50 recorded search orders through the old
and new binaries.
