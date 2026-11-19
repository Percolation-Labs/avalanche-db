# P3b: convergence on narrow links as evidence of the answer

*19 Nov 2026, james. Registered after P3's failure (RESULT-P3.md) and before this run. $0, no Jev.*

P3 scored connectivity over every door. A walk reads only through doors, so its read set is connected by
construction. P3b asks Sirsh's question with links a walk doesn't make by reading: narrow links only.

**Links:** two passages are narrowly linked if they are Beside each other, or share a key held by at most 5
passages. Near (5 nearest by wording) is excluded, since it is a door the walk opens. The width 5 is fixed here and
not tuned; widths 2 and 10 are reported as a sensitivity check, not barred.

**Signals over R_w's induced narrow graph:**
- **converged:** the largest number of seeds in one component.
- **narrow coherence:** narrow links among R over their expectation under the narrow graph's degree null.
- **narrow links:** the raw count.
- **mean narrow degree:** the hub baseline.

**Data, outcome and measures:** P3's. Test walks; gold found beyond the seeds at the final wave; AUC with 95%
bootstrap; search's top 10 as a no-walk read set.

**Bar:** P3's. Converged or narrow coherence needs final-wave AUC ≥ .65, with the interval above .5, on at least two
sets, and must beat mean narrow degree there.

**Postmortem:** every result gets one.
