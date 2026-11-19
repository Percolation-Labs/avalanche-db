# J1: can Jev, choosing from what's been read, turn MuSiQue's sub-questions into seeds that land on the Steiner graph?

*19 Nov 2026, bill. Registered before any Jev call. Approved by Sirsh 12:52 (M-20261119-125232-7523), Jev ≤ $1.
Follows P2 bar 4 on MuSiQue test (total recall at 10 reads): blind sub-questions .504, sub-questions filled with each
hop's gold answer .770.*

**The online computation it stands in for:** iterative retrieval. Answer sub-question 1, put the answer into
sub-question 2, search again. Jev only chooses; it never writes text.

**Procedure (MuSiQue test, 150 questions, MuSiQue's own decomposition):**
- Sub-questions are taken in order. Each `#j` in a sub-question is replaced by **fill[j]**, decided once sub-question j
  has been searched.
- fill[j] is the title of one of the top 5 search hits for sub-question j (as filled so far). The **chooser** picks
  which one.
- If a later sub-question still holds an undecided `#j`, it is searched with the placeholder removed, as in the blind
  arm.
- The seeds are 5, round-robin over the sub-questions' searches with duplicates skipped (P2's rule).
- Total recall at 10 reads is the 5 seeds plus U's top 5 beyond them, on L1's graph (P2's measure).

**Choosers:**
- **J, Jev** (jev-1.13.0, systemone). State: `question` = the sub-question as filled; `task` = "Which passage answers
  the question?". One noul per hit, keyed by its title, with the passage text (first 300 characters) as the
  instructions. The pick is the highest noul.
- **T, search's first hit** ($0): what an unaided pipeline would take.
- **O, the gold passage's title** ($0, where hop j's gold passage is among the 5): the best any title-choosing rule can
  do.
- Bounds from P2: **blind** .504 and **filled** .770, which fill with the gold answer string rather than a title.

**Measures:** total recall at 10; entry points (seeds in gold); and the chooser's accuracy (the pick is hop j's gold
passage), out of the decisions where that passage is among the 5.

**Bar (95% paired bootstrap):** J beats blind by ≥ .05 with the interval above 0, and beats T by ≥ .03 with the interval
above 0. Reported either way: the share of the blind-to-filled gap that J closes.

**Spend:**
- Stage 0 first: 4 hand-picked questions, posted before the rest. The hand-picks are the first 4 test questions with
  3 or more hops, in file order.
- Then the full 150, capped at $1 in all.
- The run stops at the cap, and spend is reported.

**Postmortem:** every result gets one.
