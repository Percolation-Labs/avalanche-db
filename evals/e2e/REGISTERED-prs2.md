# PR-title questions, second round: a door Jev will open, registered before any run

*Registered 18 Nov 2026 by bill, before any candidate is built or run, after the null in
[RESULT.md](RESULT.md) ("A second question type: pull-request titles, no id"). james reviewed the design on the board
(M-20261118-085311-16dc, M-20261118-085435-33cc).*

**Why.**
- On the 65 dev PR questions, the oracle reached gold through a `next` door on 42 of them.
- Jev opened a `next` door on 0 of the 93 test walks.
- In this store a commit's `next` door is its first parent and its first-parent children, which along a branch are
  the PR's other commits.
- Its head, "N unread beside a read one, in the same file or history", says neither which read one nor that the
  targets are commits from the same line of work.

## Candidates

Both are question-blind and built from git alone, at ingestion or from ingestion-time data.

| | What changes | Kind |
|---|---|---|
| **B** (as merged) | nothing | – |
| **N** | A `next` door whose source is a commit gets the head `N commits just before and after commit {sha7} "{subject}"`. Other `next` doors are unchanged, so MuSiQue and files are untouched. | presentation |
| **M** | The `documents` adapter adds a predicate `merges`, from each merge commit to the commits its second parent brought in: the second parent and its first-parent ancestors, up to the first commit on HEAD's first-parent line. The walk raises it as a `merge` door both ways. From a merge it reads `N commits merged by commit {sha7} "{merge subject}"`. From a merged commit it reads `N commits merged with this one by commit {sha7} "{merge subject}"`, and lists the merge and its other commits. | construction |
| **NM** | N and M together | both |

**Scope carried with M** (james): it follows git's own merge relation, which is also how the gold is defined. A gain
from M reads "the walk follows git's merge relation", not "the walk understands the PR". The merge subject is git's
own text (`Merge pull request #N from owner/branch`). The PR title in the merge body is never put in the head.

## Choosing, on the 65 dev PR questions only

1. **$0.** The oracle and search-order at k=10 for each candidate, on a fresh I1 store with M where M is in.
   Reported, not a gate. M's oracle is near 1 by construction and tests nothing.
2. **Jev, cap $1 across the four.** The MCP walk at k=10 on the 65 dev questions for B, N, M and NM.
   - **Pick rate** (james): the share of walks that open a `next` door (N), a `merge` door (M), or either (NM). Reported
     beside recall.
   - The pick has the highest dev recall@10, and must beat B by at least .03. If none does, the result is posted with a
     postmortem and the test isn't run.
   - Between candidates within .01, the one with less construction wins, in the order N, M, NM.
3. **No regression on cards, Jev, cap $0.50.** The pick at k=10 on the 100 card dev questions, against L1kS's .565.
   It must not drop by more than .03. If it does, the result is posted and the test isn't run.

## The test, run once

- The 93 PR test questions (`prs-test.jsonl`), MCP, Jev, k = 10, 5 and 20, cap $1.
- The $0 controls on the same store.
- **Bar:** W1 at k=10, walk − search, paired bootstrap 95% CI above 0.
- **If it passes:** the pick becomes the default, and the README states the scope above.
- **Either way:** the result is posted with a postmortem.
- The card test isn't rerun on test cards. The dev check above stands in for it, and that is said with the result.
