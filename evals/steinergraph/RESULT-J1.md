# J1: Jev choosing each sub-question's answer from what's been read closes 28% of the decomposition gap on MuSiQue

*19 Nov 2026, bill. Registered first (REGISTERED-J1.md, 95552f9, amended 1ea6224 before any Jev call). Jev spend
$0.0157 in all (stage 0 $0.0005, full run $0.0152). Output: `j1.txt`; per-question queries, picks and seeds in
`out/j1-{T,O,J}.jsonl`.*

MuSiQue test, 150 questions. Total recall at 10 reads is the 5 seeds plus the uniform avalanche's top 5, as in P2.

| seeds from | total recall at 10 | seeds in gold | right answer chosen, where it was a candidate |
|---|---|---|---|
| the single question (P2) | .475 | 1.03 | |
| blind sub-questions (P2) | .504 | 1.13 | |
| T: first candidate | .534 | 1.22 | 19/118 |
| **J: Jev chooses** | **.578** | **1.31** | **65/119** |
| O: oracle chooses | .634 | 1.50 | 128/128 |
| sub-questions filled with the gold answer (P2) | .770 | 1.81 | |

**Verdict: pass.**
- J against blind: +.074 [+.045, +.107]. J against T: +.044 [+.009, +.081].
- J closes .28 of the gap from blind to filled.
- Against the single-question search the walk uses today, J adds +.103 [+.063, +.144].

## What it says

- **Likeness improves when the question is asked in order.** Each sub-question is searched after the previous one has
  been answered by choosing among what was read. That raises the seeds landing on gold from 1.13 to 1.31. That is
  Sirsh's 12:36 hypothesis, with one condition: decomposition helps when it is iterative, not when the sub-questions are
  searched blind (+.029, P2).
- **Jev's choice is worth about as much as the candidate set allows it to be.** Jev picks the right answer in 55% of
  the decisions where it is a candidate, against 16% for the first candidate. The oracle chooser reaches .634, so with
  these candidates, perfect choice would close about half the gap.
- **The other half is the candidate set.** The gold answer was among the candidates in only 128 of 247 decisions.
  Either it wasn't in the top 3 passages read, or it wasn't a capitalised span or a year.

## Postmortem

- **The registered design was wrong once, and the $0 dry run caught it before any spend.** Choosing a passage title
  repeats the subject ("Andrey Dashkov" for "Ukraine"). Running the free arms first, on the stage-0 questions, is what
  surfaced it.
- **Jev's misses are mostly near-misses of span, not of meaning.**
  - "North America" for "North American", and "Stallman" for "Richard Stallman", are scored wrong by exact match but
    search as well.
  - "Kentucky" for "Fort Mitchell" and "India" for "ISRO" are the containing entity rather than the answer.
  - The accuracy figure therefore understates what the fill is worth to search.
- **Scope.**
  - MuSiQue only, because it ships its own decomposition. Cards and PR titles have none, and producing one needs a
    model that writes, which the walk doesn't use.
  - The decomposition is MuSiQue's gold decomposition, so this measures iterative answering given good
    sub-questions, not decomposing.
  - The recall is a ranking at 10 reads, not a walk.
- **What the next spend would buy.** A wider candidate set: more passages per sub-question, and spans beyond
  capitalised words. It is $0 to measure with O (the ceiling moves first), and then a Jev run of about $0.02.
