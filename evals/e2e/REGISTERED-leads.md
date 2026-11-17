# D6's leads on a repository: registered before any run

*Registered 17 Nov 2026 by bill, before any measurement of the candidates, for Sirsh's steer
(M-20261117-212302-b5b2): on our own repository the walk should beat search at the default 10 documents.*

**Why.** In [RESULT.md](RESULT.md), W1 failed on p8-subsystems at k=10 (+.032 [−.025, +.088]). The postmortem:
- the card's id door (`rem NNNN`) leads to the gold commits;
- Jev opened it on 6 of 150;
- D6 shows a door's five leads ordered by how many names each target mentions, and on a repository those are board
  logs, team logs and the card's own other sections, so the door reads as bookkeeping.

## Candidates

Each is built from ingestion-time data only, never from the question. A **file** is a passage id up to `#`, and
a commit is its own file.

| | Leads (up to five, after today's first snippet) | Head |
|---|---|---|
| **L0** (today) | most names first, sha-256 tie | `term 'x' · N unread` |
| **L1** | fewest names first, sha-256 tie; a lead whose text repeats one already shown is skipped | as L0 |
| **L2** | one lead per file, files in sha-256 order; repeated text skipped | as L0 |
| **L0k, L1k, L2k** | as above | adds what kind of passages are behind the door: `· 12 commits, 23 passages in 6 files` (only the parts that are non-zero) |

## Amendment, 17 Nov ~21:50Z, before any run with it: ids as terms (I1)

**What the $0 step showed.** The $0 step on the dev cards, with leads only (L0–L2k), found that the id door is raised
on only 16 of the 100 dev cards.
- `documents::words` keeps a number only when it has exactly four digits, meant for years.
- So `REM-103`, `REM-11`, `ADR-007` and any five-digit id never become the term `rem 103`, and no door joins a
  card to the commits that name it.
- Only REM-1000 to REM-9999 have the door.
- RESULT.md's "the term door exists for most cards" was wrong. It holds for about one card in six.

**I1.** At ingestion, a token of letters, a hyphen and digits (`REM-103`, `ADR-007`, `BUG-12`) also gives the term
`{letters} {digits}`. Nothing else changes.

**How the steps change.**
- Every store with I1 is a fresh `midb ingest` of the same sources.
- The $0 step is rerun on the I1 store for the lead candidates.
- The Jev dev slice compares the package as merged (L0 on the old store) with I1 plus the lead pick.
- The test is unchanged, with the same bar.

## How one is chosen: the dev cards only

The 100 dev cards (`dev/cards-dev.jsonl`), none in the test's 150.

1. **$0.** Seed search's top 5 (the k=10 walk's seeds), raise their doors, and label them with each candidate.
   - **Shown:** among doors with a gold commit behind them, the share whose text shows one (snippet or lead).
   - **Overlap AUC:** question–door-text word overlap, gold doors against the rest (G0's measure).
   - The pick has the highest Shown. Within .02 of the best, the higher overlap AUC wins. Head variants are kept
     only if they don't lower either measure.
2. **Jev, ≤ $0.50.** The MCP walk at k=10 on the 100 dev cards: L0 against the pick.
   - The pick goes forward only if its dev recall@10 is higher than L0's.
   - If it isn't, the result is posted with a postmortem and the test isn't run.

## The test

- The p8 B arm of REGISTERED.md again: the same 150 cards, the same store, MCP, Jev, k = 5, 10, 20, cap $1.
- The control arms don't read door text, so their rows from the registered run stand.
- **Bar:** W1 at k=10 on p8, walk − search, paired bootstrap 95% CI above 0.
- **No regression on MuSiQue:** the A arm at k=10 again with the pick, cap $0.50. It must still pass W1.
- **If it passes**, the pick becomes D6's default and the result is posted beside the first run, which still
  stands.
- **If it fails**, the result is posted with a postmortem.
