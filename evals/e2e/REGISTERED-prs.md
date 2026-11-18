# A second question type on the repository, with no id to lean on: registered before any run

*Registered 18 Nov 2026 by bill, before any measurement on these questions.*

**Why.** The repository claim in [RESULT.md](RESULT.md) is one question type: a board card's title, with gold commits
defined by the card's id. Most of the walk's gain came through the id door (`rem NNNN`), which is the gold's own
relation. This asks whether the walk, exactly as merged, still beats search when no id joins the question to the
answer.

## Questions

Built by `prs.py` from git alone, at p8-subsystems `039fac55b9b7`: the same pin and the same store (`e2e-p8i`, I1)
as the registered card test.
- A question is a merged pull request's title: "What work went into this, and why: {title}?"
- The gold is the PR's own commits, `merge^1..merge^2`, with merges and `board:` bookkeeping commits left out.
- A PR is eligible with 2–8 gold commits and a title of at least five words that names no id (`[letters]-[digits]`).
- 158 are eligible. Shuffled with seed 1118, the first 65 are dev (`dev/prs-dev.jsonl`, sha256 `cfb5cb7b2e0e8d09…`)
  and the other 93 are test (`prs-test.jsonl`, sha256 `7ab9dfec479afa6b…`). 2.86 gold commits per test question.

**What this type gives search, said up front.**
- The PR's merge commit is in the store, and its message carries the title verbatim. It isn't gold, so it costs
  search and the walk's seeds one slot alike.
- A PR's title is often its first commit's subject, so search can find one gold commit by wording. The rest of a PR's
  commits share a branch, which no door represents.
- So this is a type where wording carries much of the answer. A null here is informative, not a failure of the
  package.

## Nothing is tuned

The walk is the merged default: MCP `walk`, Jev 1.13.0, K6, F2 keys, D6/2 doors, seeds = ceil(k/2), `within`
`shown`. No candidate is chosen on these questions, so dev is used only for the $0 gate.

## Steps

1. **$0 on dev** (the probe with `run-configs.json` plus `within: shown`): search, oracle, search-order, width-only and
   coin at k = 5, 10 and 20.
   - **G1:** oracle − search at k=10 is at least .10. If it isn't, the doors can't reach this type's gold beyond
     search, the result is posted as a construction finding with a postmortem, and no Jev is spent.
2. **Jev on test, cap $1:** the MCP walk at k=10 on the 93 test questions, then k=5 and k=20 within the same cap.
   The $0 control arms on test.

## Bar and what is reported

- **W1** at k=10, walk − search, paired bootstrap 95% CI (10,000 resamples, seed 1118). PASS if the CI's lower bound
  is above 0.
- Reported: W2 (walk − width-only), k=5 and k=20, full support, and the split of gold commits by title-word overlap
  as in #19 (≤1 shared title word, ≥2).
- Which doors the gold came through, as in the card test's postmortem.
- Either way the result is posted with a postmortem. It doesn't change any default: the defaults were chosen on the
  card dev set and stay unless a later registration says otherwise.
