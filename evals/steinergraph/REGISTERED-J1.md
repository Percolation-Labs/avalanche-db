# J1: can Jev, choosing from what's been read, turn MuSiQue's sub-questions into seeds that land on the Steiner graph?

*19 Nov 2026, bill. Registered before any Jev call. Approved by Sirsh 12:52 (M-20261119-125232-7523), Jev ≤ $1.
Follows P2 bar 4 on MuSiQue test (total recall at 10 reads): blind sub-questions .504, sub-questions filled with each
hop's gold answer .770.*

**The online computation it stands in for:** iterative retrieval. Answer sub-question 1, put the answer into
sub-question 2, search again. Jev only chooses; it never writes text.

**Procedure (MuSiQue test, 150 questions, MuSiQue's own decomposition):**
- Sub-questions are taken in order. Each `#j` in a sub-question is replaced by **fill[j]**, decided once sub-question j
  has been searched.
- fill[j] is one **candidate answer** read from the top 3 search hits for sub-question j (as filled so far). The
  **chooser** picks which one.
- Candidates are the names and years in those passages:
  - runs of capitalised words (joined by *of, the, de, and*) and 4-digit numbers;
  - minus any already in the sub-question;
  - in reading order, at most 24.
- If a later sub-question still holds an undecided `#j`, it is searched with the placeholder removed, as in the blind
  arm.
- The seeds are 5, round-robin over the sub-questions' searches with duplicates skipped (P2's rule).
- Total recall at 10 reads is the 5 seeds plus U's top 5 beyond them, on L1's graph (P2's measure).

**Choosers:**
- **J, Jev** (jev-1.13.0, systemone).
  - State: `question` = the sub-question as filled, and `task` = "Which of these is the answer to the question?".
  - One noul per candidate, keyed by the candidate, with the sentence it came from as the instructions.
  - The pick is the highest noul.
- **T, the first candidate** ($0): what an unaided pipeline would take.
- **O, oracle** ($0): the candidate equal to hop j's gold answer (case-insensitive), when one exists, else T. This is
  the best any candidate-choosing rule can do.
- Bounds from P2: **blind** .504 and **filled** .770, which fill with the gold answer string rather than a title.

**Measures:** total recall at 10; entry points (seeds in gold); and the chooser's accuracy (the pick equals hop j's gold
answer), out of the decisions where the gold answer is a candidate.

**Bar (95% paired bootstrap):** J beats blind by ≥ .05 with the interval above 0, and beats T by ≥ .03 with the interval
above 0. Reported either way: the share of the blind-to-filled gap that J closes.

**Spend:**
- Stage 0 first: 4 hand-picked questions, posted before the rest. The hand-picks are the first 4 test questions with
  3 or more hops, in file order.
- Then the full 150, capped at $1 in all.
- The run stops at the cap, and spend is reported.

**Amended before any Jev call** (13:10). A $0 dry run of T and O on the stage-0 questions showed that a hit's title is
its subject, not the answer: "What was Andrey Dashkov's birth country?" filled #1 with "Andrey Dashkov". So the
choice moved from among passages to among the answers those passages contain.

**Postmortem:** every result gets one.
