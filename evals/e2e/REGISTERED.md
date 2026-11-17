# End to end: install, ingest, ask, documents back, against search

*Registered 17 Nov 2026 by bill, before any score, for Sirsh's packaging brief (M-20261117-183639-31e2,
M-20261117-183730-e0ed). james owns the walk and MCP tools under test; bill owns this test.*

**The question.** Someone installs `midb`, connects it to Claude, has Claude ingest their source, and asks
questions. Do the documents that come back hold the answer more often than search would return at the same
number of documents?

## The path under test

The path is exactly what Claude does, with no hand-wiring:

1. `install.sh --local`.
2. `midb mcp install`.
3. The MCP tool `ingest` on a folder (the `documents` adapter, D6 doors from ingestion-time data).
4. The MCP tool `walk` (question, budget), which returns documents with their paths.
5. `read_document` on what came back.

The numbers come from driving those MCP tools over stdio JSON-RPC, the same calls Claude makes. A handful of
hand-picked questions are also asked in a real Claude Code session, to show the path working. Those are a
demonstration, not a measurement: no batch run uses Claude.

## Two corpora, both with known answers

**A. MuSiQue reference world.**
- Corpus: the fixture's 21,100 real paragraphs as a `.jsonl` of `{id, title, text}`
  (`musique.jsonl`, sha256 `56d59fc70caab615…`), ingested by the same `documents` adapter.
- Questions: 150 fresh dev questions in `musique-questions.jsonl` (sha256 `c5fcebfcd4d3c1d4…`).
  - Sampled with `rw_musique.questions`, seed 1118, stratified by hop type.
  - Every qid already used in `~/.cache/walklab/refworld/` (259) is excluded.
  - 2.65 hops on average.
- Gold: MuSiQue's supporting paragraphs, with hop order.

**B. A real repository, p8-subsystems at `039fac55b9b7`.**
- Ingested whole: 12,331 files and 18,509 commits, which make 48,636 passages.
- Questions: 150 board cards in `cards.jsonl` (sha256 `be6398e20256173b…`), built by `cards.py` from git alone,
  seed 1118, out of 515 eligible.
  - The question is the card's title: "What was done about this, and why: {title}?".
  - The gold is the commits whose message names the card's id, less `board:` bookkeeping commits, which name the
    card and often carry its title verbatim.
  - A card is eligible with 1–8 gold commits and a title of at least five words that names no id.
  - 2.13 gold commits per question.
  - The question never contains the id, so search can't match on it. A walk can reach the commits from the card
    through the term door `rem NNNN` or through wording.

## Arms, at the same number of documents returned (k = 5, 10, 20)

| Arm | What returns the k documents |
|---|---|
| **search** | full-text BM25 (`walk::text::FullText`), top k |
| **walk** | the MCP `walk` tool: D6 doors, Jev ranking door batches, opened until k documents are read |
| width-only | the same walk, doors ranked by unread targets (no text read) |
| coin | the same walk, doors in a fixed random order |
| search-order | the same walk, doors ranked by their best target's BM25 rank (no Jev) |
| oracle | the same walk, doors ranked by gold targets behind them: the construction's ceiling |

All walk arms share james's settings at the time of the run, recorded with the result. The walk's seeds count
toward its k, so a walk is credited only beyond search at equal budget.

## Measures

- **Primary:** recall@10, the share of a question's gold documents among the k=10 returned. Compared paired per
  question, with a bootstrap 95% CI (10,000 resamples, seed 1118).
- **Reported:** recall@5 and recall@20; full support (every gold document returned); and, on A, last-hop gold
  recall.

## Gates, in order

**G0, construction, at $0, before any Jev call.** This is the door-signal check every reference world must pass,
run on the graph this ingester builds:
- Seed the 3 search passages per question, raise their doors, and call a door gold when a gold passage is behind
  it.
- Requirement: on A, question-word overlap with the D6 door text separates gold doors from the rest at AUC ≥ .55.
  The lab's MuSiQue graph scored .569 under the reference-world gate.
- Width and overlap are both reported, for A and B.
- If G0 fails, the construction is fixed and G0 rerun before anything else runs. That outcome is a construction
  finding, not a verdict on walking.

**G1, oracle ceiling, at $0.** On A, oracle − search recall@10 is at least .10. If the oracle can't beat search,
the graph doesn't carry the answer, and the walk arms aren't scored on that corpus.

**W1, the claim.** walk − search recall@10 > 0, with the paired CI above 0. Judged separately on A and on B.

**W2, Jev reads the text.** walk − width-only recall@10 > 0, with the paired CI above 0, on A and on B.

W1 is what the package can claim. W1 without W2 means the gain comes from the graph and not from reading.
A miss on either is written up with its mechanism.

## Spend

The Jev decider is called only through the walk, in batches. A pilot on 5 questions per corpus comes first, with
its price stated. The cap is $1.00 per corpus, and spend is reported with the result.

## What would change the plan

Nothing about the questions, gold or measures changes after a score is seen. Settings that change after a pilot
are recorded as such, and apply to every arm.
