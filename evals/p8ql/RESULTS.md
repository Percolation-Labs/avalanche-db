# P8QL agent eval: results

## Round 1, 8 Nov 2026: directional, one run per question

**Versions:** avalanche-db 32f555d (P8QL stages 1-3), billing example with Bob and Chen
(bda7b94). The agent was Claude Sonnet in both arms, with lower effort and the same prompt
apart from the command list. Raw answers and call logs are in `runs/2026-11-08/`.

| q | tier | baseline recall | P8QL recall | baseline calls | P8QL calls |
|---|---|---|---|---|---|
| Q1 | record select | 0.50 | 0.50 | 1 | 1 |
| Q2 | fuzzy lookup ("Bobby") | 1.00 | 1.00 | 7 | 3 |
| Q3 | graph pattern (who works with Bob) | 1.00 | 1.00 | 12 | 2 |
| Q4 | graph pattern (issues fixed in Chen's files) | 1.00 | 1.00 | 8 | 2 |
| Q5 | iterated (why a cent off) | 1.00 | 1.00 | 1 | 5 |
| mean | | 0.90 | 0.90 | 5.8 | 2.6 |

**Both arms reached the same answers. P8QL needed fewer calls on pattern questions, and
more on the open "why" question.**

- **Patterns fold into one statement.** For "who works with Bob?" the baseline agent ran
  `edges` twelve times, record by record: Bob, his commits, their files, those files'
  commits, and those commits' authors. The P8QL agent read the schema and wrote one
  statement over the `works_with` path. Q4 went the same way, 8 calls against 2.
- **Fuzzy lookup worked in both arms, but by different routes.** No person is named Bobby.
  The P8QL agent tried `person = 'Bobby'`, which was refused, then `LIKE 'Bobby'`, which
  matched Bob at 0.60. The baseline agent got there through `search` and `edges` on
  `person:Bob`. Both agents said in their answers that they had assumed Bobby meant Bob.
- **The native walk was not trusted on its own.** For Q5, the baseline's `why` answered in
  one call. The P8QL agent's `WALK FROM` returned the same tree, but the agent then ran a
  record select on four of its records before answering. P8QL's walk output prints the plan
  and trace above the tree, which may read as less final than `why`. That is a hypothesis,
  not tested.
- **Q1 is a defect in the question, not in either arm.** "What did ADR-007 decide about"
  was meant to be answered by the file it governs (`decides -> file:src/invoice/round.rs`).
  Both agents named the decision itself and P-3, and mentioned round.rs only in prose. The
  question now reads "Which file does decision ADR-007 govern". Round 1 used the old
  wording.

**What this does not show.** One run per question, on a ten-commit example, cannot separate
the arms on accuracy, and the call counts could swing from run to run. Keys scanned were not
compared. Next: replicates (three per question per arm), the reworded Q1, and the same tiers
on Percolate's own history, where a pattern touches hundreds of records rather than ten.

*Since 0.2.0 the CLI is `midb`; round 1 ran when it was still called `ava`, so the call logs say `ava`.*
