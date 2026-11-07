# The engine: design principles

Avalanche DB is a research engine that tests whether the Percolate pattern holds on its own.
Percolate's production system runs on Postgres and stays there. If an engine designed around
these principles makes them simpler, sharper or cheaper than an application that enforces
them, the pattern is real. The theory may be wrong, and so may this implementation, so the
aim is to test the idea in the lightest and most portable form possible.

This file states the principles from the engine spec, Sirsh's *Avalanche DB: a portable
graph engine for the Percolate pattern*, and marks what is built and what is not. **Built**
names the code that carries a principle. **Not yet** means the principle is part of the
design but has no code.

## The pattern

1. **Many representations of memory in one store.** Claims, questions, decisions, commits,
   cards and the usage log of queries all live in one store as typed facts.
2. **Beyond semantics.** Meaning is extracted into graph structure when data is written.
   Queries are purely structural and never rely on semantics.
3. **Queries are iterative and durable.** A query is a reasoning session over a structured
   graph, not one multi-hop traversal.
4. **Ingestion and reading are two sides of one coin.** Ingestion runs from source to
   structure. Reading runs the other way, from a question back through structure to source.
5. **History is kept.** Lineage, decisions and rejected ideas are facts, never overwritten.
6. **Isolation by user and org from the start.**

## Data model

- **Every fact is a quad:** subject, predicate, object, graph. **Built:** `src/model.rs`,
  `src/store.rs`.
- **Bitemporal.** Each fact carries two times: valid time, when it was true in the world,
  and transaction time, when the engine learned it. That is what lets a query ask what the
  graph knew then (story 6). **Built:** every index key ends in the transaction; every value
  carries `valid_from` and `valid_to`.
- **Append-only. Nothing is updated in place, and a retraction is itself a fact.**
  Retracting a link writes another key. The rejected link stays on record (story 7).
  **Built:** `ASSERT` and `RETRACT` ops in `src/store.rs`.
- **A graph of references, not of content.** Document text and embeddings live elsewhere,
  in files, Postgres or a code repository. A fact points back to where its content lives and
  carries only a short label. **Built:** adapters copy labels, not text. A node's vector can
  be imported for search, but it is outside the bitemporal log.
- **Typed, enumerated predicates.** A model may propose anything while extracting, but only
  facts that fit the type system are written. A node's kind is the prefix of its name
  (`commit:…`, `decision:…`), and each predicate names the kinds it may join. **Built:**
  `Kind` and `Pred` in `src/model.rs`.

## Storage

- **Rust and redb, one file on disk.** redb is an embedded, pure-Rust, ACID key-value store
  with copy-on-write B-trees. Readers never block, there is one writer at a time, and
  everything is in one file. It suits memory, which is read-heavy and receives writes in
  batches. Write-heavy workloads are not its strength, and this design does not ask them of
  it. **Built:** Rust 2024 edition, redb 4.
- **The truth is an append-only, ordered log per tenant.** **Built:** the `log` table,
  keyed by tenant, transaction and sequence number.
- **Names are interned** to integer ids in a dictionary table. **Built:** the `dict` and
  `names` tables.
- **Four key orders, so any graph step is a prefix range scan.** Each fact is written
  subject first, object first, predicate first and graph first. **Built:** the `spog`,
  `ospg`, `psog` and `gspo` tables.
- **The tenant is the first part of every key**, so isolation is which keys you can scan.
  **Built.**
- **Indexes are immutable files, one per transaction T.** **Not yet.** The four indexes are
  written into the same redb file as the log, in the same transaction. An as-of-T read scans
  the same keys and ignores those past T.

## Queries

- **A session is pinned to a snapshot at transaction T.** Each step is a small pattern, such
  as "start at X and follow `because`". It returns its results with a continuation token
  that holds the snapshot, T and the position. The agent can reason for as long as it likes
  between steps, and the graph will not move under it. **Built:** `src/walk/session.rs`.
- **The reasoning stack is part of the core.** As a session walks, the questions it has yet
  to resolve build up on a frontier, like a percolation front. The stack runs within a
  budget and is durable. **Built:** a frontier ranked by a priority policy, a budget, and
  sessions stored in the `sessions` table.
- **Query statistics are part of the core.** Every step returns the state of the stack and
  statistics about the graph around it: fan-out, depth and how often a path has been used.
  **Built:** the `stats:` line on every step (story 8).
- **Queries are durable.** Every step, its token and its outcome are appended to a usage
  log. That gives three things: metrics come from querying the log, a re-index can be tested
  by replaying old questions against the new graph (story 9), and any answer can be
  explained by what the graph knew when it ran. **Built:** each tenant has a usage log,
  `<tenant>#usage`, and `ava suite` replays kept questions.
- **The only semantic step on the read path is finding where to start.** The words of the
  question are resolved to a starting node once, never across the store. **Built:** `ava
  search` draws the circle and the walk starts from it. A test checks that `src/walk/` never
  reaches the model (`tests/engine.rs`).
- **Query languages are translators onto one small core** of pattern matching, path walks
  and time filters. SPARQL, Cypher, SQL or GQL could each be added without changing the
  core. **Not yet.**

## Construction and the model

- **Adapters share one contract:** read the source, emit typed facts, and point back to where
  the content lives. **Built:** git, markdown, Percolate and GitHub pull requests
  (`src/construct/`). **Not yet:** Postgres through logical replication, and a file watcher.
- **The model works when data is written, never on the query path.** A decision model in
  the style of Jev decides what each mention means, while data is written and re-indexed.
  Typed questions go in and one choice with a probability comes out; nothing is generated.
  The bet is that decision models will become much cheaper and faster within a few years,
  and the engine is shaped to take advantage when they do. **Built:** `src/infer.rs` is the
  only code that calls a model. Every request is recorded, keyed by a hash of its exact
  body, and replayed, so anything built on a recording is offline and deterministic.
- **Re-extraction is driven by query statistics.** When a query recovers material that
  carries meaning, that material can be re-read and its new facts written back. Which
  statistic triggers this is still open. **Not yet.**

## Isolation

- **Each tenant has its own log.** **Built.**
- **Each tenant also has its own snapshots and its own encryption key.** Deletion is
  crypto-shredding: destroy the tenant's key, and its facts become unreadable everywhere they
  were copied, while the log stays append-only. **Not yet.**

## Packaging and distribution

- **One binary, three roles.** Embedded: a library inside an app or agent, with a local
  file. Sidecar: a small process beside Postgres, a repository or a folder. Cluster: the same
  binary running as writer, builder and reader on Kubernetes. It sits beside whatever else
  you run and replaces nothing. **Built:** the library and the `ava` CLI, plus `ava mcp`
  for agents. **Not yet:** the sidecar and cluster roles.
- **Distribution is copying.** Writers append to per-tenant logs. Builders turn log tails
  into immutable snapshots in object storage. Readers pull snapshots and replay the recent
  tail. Because a continuation token pins the snapshot and T, any replica can serve a
  session's next step. Most queries never cross machines, because every key starts with the
  tenant. A step that crosses tenants or shards fans out explicitly, so the agent knows it is
  paying for it. With one log per user, team or project there are many single writers and
  never one global writer, so writes scale with the number of tenants and reads scale by
  copying immutable files. **Not yet:** the first spike is single-node by design.
- **The coordinator is thin.** As in Datomic, the client does the intelligence. The
  coordinator orders writes and grants one writer lease per tenant. It also keeps the
  catalog (each tenant's latest snapshot, its T and where it lives), routes cross-shard
  steps, parks durable sessions that must outlive a client, collects query statistics and
  schedules builds. It never runs queries, reasons, calls the model or stores the graph. If
  it goes down, reads continue from snapshots already held. **Not yet.**

## Known costs

- One writer per tenant caps each tenant's write throughput.
- The log grows and needs compaction.
- Encrypted values cannot be indexed directly, so searchable fields need care.
- Key management becomes critical: losing a key deletes data.
- Translation quality when data is written bounds what structure can answer. The measured
  results in [plan.md](plan.md) show that judging links, not walking the graph, is where
  the work is hard.
