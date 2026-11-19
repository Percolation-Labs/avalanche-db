# J5 (registered before running): show Jev where each candidate answer leads

*19 Nov 2026, bill. Jev ≤ $0.10 (standing rule: registered runs ≤ $1 need no yes). Stage 0 first: 4 questions,
≤ $0.01.*

## Why

- J3 found that choosing the fill is choosing the door.
- J4 found that the gold door is the key spelled as the previous answer (66% against 3%), and that both connection
  and whole-question likeness separate it (AUC .84).
- J4b found that no constant-free ranking of those signals reaches Jev's fill (.20–.32 against .449).
- In J1, Jev chooses among candidate answers seeing only the sentence each came from. It doesn't see where each
  candidate leads.
- **Hypothesis:** showing Jev, for each candidate, what lies behind its door raises its choice accuracy and the
  recall that follows. That means how many passages carry it, and which of them best matches the whole question.

## Design

J1's setup, unchanged: MuSiQue test, the same 150 questions, J1's candidates (top 3 passages, ≤24 names and years),
the same rounds, and the same seeds and scoring. Only the text Jev sees per candidate changes:

- **J1:** `` `{a}`, from: {sentence} ``
- **J5:** `` `{a}`, from: {sentence} — leads to {n} passages; closest to the question: {title}: {first sentence} ``
  - n is the number of passages carrying the key equal to a (lower-cased), from L1's stored graph.
  - "Closest" means the highest BM25 of the whole question among those passages, excluding passages already read,
    with BM25 as in J3 and J4.
  - If a is not a key, or its key is held by more than 100 passages (outside the graph's doors), the text reads
    "leads nowhere in the graph" in place of the door. Both are properties of the stored graph, not chosen here.

No new constant is introduced. The 100 is the graph's stored door limit, and 3 passages and 24 candidates are J1's.

## Measures and bar

- **Primary:** total recall at 10 (5 seeds plus U's top 5), J5 against J1's J (.578), paired over questions.
- **Bar:** J5 − J1 J ≥ +.02, with the 95% paired bootstrap interval above 0.
- **Secondary:** Jev's accuracy where gold is a candidate (J1: 65/119), and the later-hop top-5 rate (J2's
  diagnostic, J1's F).
- **Stage 0:** the first 4 questions with 3 or more hops, ≤ $0.01. The arm continues only if the prompts render as
  designed and the cost per decision is within 3× J1's.

## Not tested

- Fitting any weighting of the signals.
- Changing the candidate set, which J2 covered.
