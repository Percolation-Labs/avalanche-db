# J2: does a wider candidate set raise what Jev's iterative answering recovers on MuSiQue?

*19 Nov 2026, bill. Registered before any run. Approved by Sirsh 13:10 (M-20261119-131009-a8aa): $0 oracle check
first, then a small Jev run. Everything is as in J1 (REGISTERED-J1.md, amended) except the candidate set.*

**J1's limit:** the gold answer was a candidate in only 128 of 247 decisions.

**The wider candidate set** (one change, applied to all three choosers T, O and J):
- **Passages:** the top 5 search hits for the sub-question, not the top 3.
- **Spans:** capitalised runs joined only by *of, the, de*. Runs are no longer joined by *and*, which in J1 produced
  "Indonesia and East Timor" where the answer was "East Timor".
- **Numbers:** any token with a digit (dates, counts, years), not only 4-digit years.
- **Cap:** at most 40 candidates, not 24.
- Order, dedup and the question filter are as in J1.

**Stages:**
1. **$0:** run T and O with the wider set. Count the decisions where the gold answer is a candidate, and score O.
2. **Gate:** if O's total recall at 10 doesn't beat J1's O (.634) by ≥ .02, stop. A wider set that doesn't raise the
   ceiling isn't worth a Jev run.
3. **Jev:** run J on the 150, capped at $0.25.

**Bar (95% paired bootstrap, per question):**
- J2 beats J1's J (.578) by ≥ .02 with the interval above 0;
- and J2 beats J2's T by ≥ .03 with the interval above 0.

**Postmortem:** every result gets one, including a stop at the gate.
