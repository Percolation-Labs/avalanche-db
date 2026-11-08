# Architecture

Everything Avalanche does sits in one of three layers, over one store.

| Layer | What it does | Code | Calls a model |
|---|---|---|---|
| **Construct** | Builds the data. Adapters record what sources say outright (`ingest`); dreaming decides what a mention means (`dream`); a person takes a link back (`retract`). | `src/construct/` | only `dream`, through infer |
| **Infer** | The decision model. Typed questions go in; one choice with a probability comes out; nothing is generated. Every request is recorded and replayed. | `src/infer.rs` | yes, and nowhere else |
| **Walk** | Uses the data. Search draws the circle; a walk steps through a frontier of open questions ranked by a priority policy; `why` prints the result; the suite replays kept questions; `mcp` serves the walk to an agent. Pure algorithm. | `src/walk/` | never (a test checks) |
| Store | An append-only log of typed facts with two times, indexed four ways on redb. | `src/store.rs`, `src/model.rs` | |

The line matters. What the walk can find is bounded by what construction wrote, and
construction is where the cost and the judgement are. The walk itself is cheap, exact and
repeatable, so it can be measured.


## Your own history

The same commands run on real work. This is the configuration used on Percolate's own
history (REM-1185): board cards read from a git revision, two repositories, and their merged
pull requests, whose titles, bodies and branch names say which card they carry out.

```toml
tenant = "percolate"

[[source]]
adapter = "markdown"
path = "../p8-subsystems"
rev = "origin/main"            # read at a revision, so a stale checkout does not matter
dir = "board/cards"

[[source]]
adapter = "git"
path = "../percolate"
rev = "origin/main"

[[source]]
adapter = "github"             # merged PRs, through `gh`
repo = "Percolation-Labs/percolate"

[ids]
REM = "card"
```

`midb dream --since 2026-10-01` limits a dream to recent sources.

