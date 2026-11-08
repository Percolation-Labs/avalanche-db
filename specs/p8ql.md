# P8QL: iterated queries over a memory you walk

*Proposal, 7 Nov 2026. Nothing below is built until Sirsh approves it.*

## Why not SQL or Cypher

It is tempting to rebuild SQL or Cypher on top of Avalanche, because both are familiar. But
both assume that a query is one statement which a planner runs to completion, out of the
caller's sight. Avalanche's unit is the opposite: a **step**, pinned to a transaction,
returning a continuation token, with the caller reasoning between steps
([engine.md](engine.md), "Queries"). A Cypher query compiled onto Avalanche would hide the
very thing the engine exists to show.

P8QL starts from the walk instead. It is SQL-like on the surface, because an agent reads and
writes SQL fluently. Underneath, every clause is one native step, and the plan is a list of
those steps that the agent can read before running it and run one step at a time.

## Two routes, two kinds of step

*There Are Only Two Ways to Know a Thing* (Sirsh, 6 Nov) argues that every route to
knowledge is one of two questions: what is this **like**, and what is it **connected to**.
"Likenesses remind you, connections lead you." P8QL has one clause for each route, and each
is a different kind of step:

| Route | Clause | What the step does | Native operation |
|---|---|---|---|
| Likeness | `LIKE` | finds records by resemblance: words in a label, a fuzzy name, a nearby vector | label search, fuzzy name match, `near` neighbours |
| Connection | `WALK … -[pred]->` | follows typed links from records already in hand | prefix range scan on `spog` / `ospg` / `psog` |

Every query alternates between the two. The usual shape is one likeness step to find where
to start, then connection steps. The essay's point holds here: a system that uses only one
route hides the other in how it was made. Search alone hides the links, and a graph query
alone hides how it chose its starting node. P8QL writes both in the query.

## The formal walk

A P8QL statement reads like SQL. Each clause compiles to one step, in order:

```sql
SELECT   <what to return>
FROM     <kind> [LIKE '<words>' | = '<id>'] AS <name>         -- likeness or an exact record
WALK     <name> <-pred- <kind> -pred-> <kind> ... AS <name>    -- connection, one hop per arrow
WHERE    <filters on what is in hand>
AS OF    T<n>  [VALID AT '<date>']                             -- the snapshot and the world-time
GROUP BY ... ORDER BY ... LIMIT ...
```

- `FROM` is always the first step. `= 'id'` looks up a name in the dictionary, and `LIKE`
  runs a likeness step.
- Each arrow in `WALK` is one hop. `-authoredBy->` follows a link forward, and
  `<-authoredBy-` follows it backward. Predicates are the engine's typed, enumerated ones,
  so a misspelled or ill-typed hop is refused at compile time, not as an empty result.
- `AS OF` pins the whole query to one transaction, as a session token does. If it is left
  out, the query uses the head at compile time and the plan names that T.
- Named paths are macros over hops, defined once per store:
  `PATH works_with = <-authoredBy- commit -touches-> file <-touches- commit -authoredBy->`.
  `WALK b -[works_with]- person` expands to four hops in the plan.

`EXPLAIN` returns the plan without running it. `PREPARE` returns the plan and a token for
its first step. `STEP <token>` runs one step and returns its rows, its statistics and the
next token, exactly as `ava step` does today.

## Four queries, compiled

These examples use the billing example. Until 8 Nov
every commit was Ana's; stage 1 added Bob and Chen to `make.sh`, three commits after the rest.

### 1. Record select

```sql
SELECT * FROM decision = 'ADR-007';
```

```text
plan  T3
  1  lookup   decision:ADR-007                   dict  1 key
  2  edges    decision:ADR-007  out, in          spog + ospg  prefix scans
```

This is no different from SQL's `WHERE id = …`, and it takes one step. It returns the
record's label, pointer and every link, each with its two times.

### 2. Fuzzy entity lookup

```sql
SELECT p FROM person LIKE 'bob' AS p;
```

```text
plan  T3
  1  like     person  'bob'   names + labels of kind person, fuzzy   ranked candidates
```

The result is a ranked list, not a single row: `person:Bob` 1.00, then
`person:Bobby Tables` 0.71 if there were one. Likeness never silently picks a winner. The
agent sees the candidates and their scores and decides which ones to carry forward. That is
the point of iterating.

### 3. Who works with Bob (a graph pattern, as Cypher would write it)

```sql
SELECT colleague, count(*) AS shared_files
FROM   person LIKE 'bob' AS b
WALK   b -[works_with]- person AS colleague
WHERE  colleague <> b
GROUP BY colleague ORDER BY shared_files DESC;
```

```text
plan  T3
  1  like     person 'bob'                          → b (candidates; carries the top 1 unless told otherwise)
  2  hop      b <-authoredBy- commit                ospg  prefix (authoredBy, b)
  3  hop      commit -touches-> file                spog  prefix (commit, touches)
  4  hop      file <-touches- commit                ospg  prefix (touches, file)
  5  hop      commit -authoredBy-> person           spog  prefix (commit, authoredBy)
  6  filter   colleague <> b
  7  group    colleague, count(file)
```

This is the two-step question from the brief: find Bob by likeness, then follow "works with"
by connection. `works_with` is a named path, so the plan shows all four hops it expands to,
and the agent can see why a colleague was returned (the shared file). Cypher would write the
same pattern as
`MATCH (b:Person {name:'Bob'})<-[:AUTHORED_BY]-(:Commit)-[:TOUCHES]->(f)<-[:TOUCHES]-(:Commit)-[:AUTHORED_BY]->(c) RETURN c, count(f)`.
P8QL reads the same way, but the agent can pause after any hop.

### 4. An iterated walk: why is the invoice a cent off?

Some questions have no fixed pattern: you do not know the path in advance. That is the
native walk, and P8QL gives it a clause of its own:

```sql
WALK FROM (SELECT r FROM record LIKE 'invoice a cent off from the spreadsheet' AS r LIMIT 1)
FOLLOW because 1.0, rejects 0.9, implements 0.8, fixes 0.8, challenges 0.8, supports 0.7
UNTIL  frontier EMPTY  BUDGET 20
RETURN PATH;
```

```text
plan  T3
  1  like     record 'invoice a cent off…'          → issue:BUG-12 (top 1)
  2  frontier start at issue:BUG-12, policy as written, budget 20
  3+ step     best open question, one per STEP      (stops when the frontier empties or the budget runs out)
```

This compiles to `ava ask` followed by `ava step` calls. The `FOLLOW` weights are the walk's
`--prefer` policy. `RETURN PATH` prints what `ava why` prints. Because the walk is native,
its plan is short and its work happens at run time: the agent watches the frontier and can
`TAKE` any open question or change a weight between steps, as it can today.

## How an agent uses it

Over MCP, three tools are added beside today's four (`search`, `ask`, `step` and `why`):

| Tool | In | Out |
|---|---|---|
| `p8ql_explain` | a statement | the plan: steps, the scans each uses, the pinned T, and refusals for ill-typed hops |
| `p8ql_run` | a statement, or a token | the rows, statistics per step, and a token if the query paused (a budget hit, or likeness with several close candidates) |
| `p8ql_schema` | nothing | the kinds, the predicates and the kinds each joins, the named paths, and counts per kind |

An agent that is unsure explains first, reads the plan, and edits the query. It does not run
a query and guess from an empty result. Every statement, plan and step is written to the
usage log, so a query an agent wrote can be replayed after a rebuild, as `ava suite` replays
questions now.

## Evals: querying through agents

The test is whether an agent answers questions better, and more cheaply, through P8QL than
through search plus the raw walk tools. The suite has three tiers, all with gold answers as
record ids:

| Tier | Example question | Gold | What it tests |
|---|---|---|---|
| Record select | "What did ADR-007 decide, and what did it reject?" | `file:src/invoice/round.rs`, `proposal:P-3` | exact lookup and one hop |
| Fuzzy lookup | "What has Bobby worked on?" (the person is `Bob`) | Bob's commits and files | a likeness step whose candidates the agent must choose between |
| Graph pattern | "Who works with Bob?" / "Which bugs were fixed in files Ana touched?" | the people or issues | multi-hop patterns, named paths, grouping |
| Iterated | "Why is the invoice a cent off?" | `decision:ADR-007`, `proposal:P-3` | the native walk and steering |

Each question runs in two arms, with the same agent and model: **P8QL** (the three tools
above) and **baseline** (today's `search`, `ask`, `step`, `why`). Score per question:
recall and precision of the gold ids, tool calls, keys scanned (from the step statistics),
and whether the final query is valid P8QL when replayed. The first run is directional: 3-4
questions per tier on the billing example, with both arms run before any claim is made.
After that comes Percolate's own history (REM-1185's configuration), where questions such
as "who works with bill on the board?" have real answers to check.

## What it is not

- It is not SQL. There are no tables and no joins between them. `FROM` names a kind of
  record, and connection only happens through typed links.
- It is not a planner that reorders steps. The plan runs in the order the query is written,
  because the agent wrote it in that order and reads it that way. The compiler only refuses
  steps and expands named paths.
- It has no semantics inside a query. Likeness steps use labels, names and stored vectors.
  No model is called on the read path ([engine.md](engine.md)), and `LIKE` never asks one.

## Build, in stages

Each stage ends with its own tests and stories added to [docs/stories.md](../docs/stories.md).

1. **Example and schema.** Add Bob and Chen to the billing example. Add `p8ql_schema` and
   named paths, with `works_with` defined in `avalanche.toml`.
2. **Parser and `EXPLAIN`.** Compile all four example statements to plans. Ill-typed hops
   are refused.
3. **Run and step.** Add `p8ql_run` and `STEP` over the existing scans and sessions, with
   tokens that pin T. `like` gains a fuzzy name match over the `names` table.
4. **Agent evals.** The two-arm suite above, run directionally first.

## Open questions

- **How many candidates `LIKE` carries forward.** The options are the top 1, every candidate
  above a score, or pausing and letting the agent choose. The proposal is to pause when the
  top two are within 0.1, and otherwise carry the top 1.
- **Where named paths live:** `avalanche.toml`, or as facts in the store. As facts they
  would be bitemporal and replayable. In `avalanche.toml` they are simpler.
- **Whether `GROUP BY` and `count` belong in the core,** or whether rows are returned and
  the agent counts them. Grouping is cheap and keeps answers small, but it is the first step
  toward a planner.
