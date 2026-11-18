# The merge door's text: registered before any run (18 Nov, bill)

**Why.**
- In round 2 ([RESULT.md](RESULT.md), "PR-title questions, round 2"), 123 of the 164 merge doors Jev was shown named a
  gold commit, against 2.3% of term doors.
- Jev's mean P for a gold merge door was .53, against .58 for a gold term door (p8-subsystems
  `meta/lab/results/door-overlap`).
- The head said `7 commits merged with this one by commit e6b3ef9 "Merge pull request #5 from
  percolating-sirsh/open-sql"`. That names a commit and a branch path, not what the door holds.
- james (M-20261118-094448-7471) asked for the text route before any per-kind prior, since text is free of dials.

## Candidates

Both are on M's construction (`evals/e2e/prs/candidates-N-M.patch`, the `merges` predicate). Both are question-blind,
from git's own merge subject.

| | merge-door head |
|---|---|
| **M** (round 2) | `N commits merged with this one by commit {sha7} "{merge subject}"` |
| **H1** | `one pull request's work: the N other commits merged with this one in #{pr} (branch {branch})`. From the merge commit itself: `one pull request's work: the N commits merged in #{pr} (branch {branch})`. `{pr}` and `{branch}` are parsed from `Merge pull request #{pr} from {owner}/{branch}`. Any other merge subject keeps M's head. The kind suffix (`· N commits`) is dropped for merge doors, because the head already says it. |

## Steps

1. **PR dev, Jev, cap $0.30.** The MCP walk at k=10 on the 65 dev PR questions, with H1.
   - Its recall@10 and merge-open rate are compared with M's round-2 run (.532, opened 1 of 65) and B's (.507).
   - H1 goes forward only if it beats B by at least .03 and opens a merge door on more walks than M did.
2. **Cards dev, no harm, Jev, cap $0.50.** On james's rule that the claim must hold on other question types:
   - H1 at k=10 on the 100 card dev questions, on the merge store.
   - It goes forward only if recall@10 is at least L1kS's .565 − .03.
   - MuSiQue has no merge commits, so its pages are unchanged. That is said with the result; it isn't rerun.
3. **PR test, run once, cap $1.** The 93 test questions at k=10, 5 and 20, with the $0 controls.
   - **Bar:** W1 at k=10, CI above 0, with the scope "the walk follows git's merge relation".
   - **If it passes:** M and H1 become the default, and the README says so with that scope.
   - **Either way:** posted with a postmortem.
