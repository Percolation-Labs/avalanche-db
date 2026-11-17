# Seeds at k=5, after #18: registered before any run

*Registered 17 Nov 2026 by bill, before any run.*

**Why.** After #18 the walk beats search at k=10 and k=20 on p8-subsystems. At k=5 it doesn't: +.034 [−.027, +.095].
At k=5 the walk takes ceil(5/2) = 3 seeds and reads 2 documents through doors. It gained 35 gold commits and gave up
26 that search's ranks 4–5 held. The seeds rule was chosen before I1 and `within = "shown"` existed; then, p8
preferred 2 seeds at k=5 by .019.

**Question.** With I1, L1k doors and `shown`, does a different seed count at k=5 lift the walk, without a different
rule at each k?

**$0 step, dev cards and dev MuSiQue only.**
- Probe k=5 settings with seeds 1, 2, 3 and 4, on the I1 stores.
- Measure oracle and search-order recall@5.
- The seeds rule changes only if one rule over k, such as floor(k/2) or ceil(k/2) − 1 with a minimum of 1, beats
  ceil(k/2) on the oracle at k=5 on both corpora, and doesn't lower it at k=10 or k=20 by more than .01.
- Otherwise ceil(k/2) stays, and k=5 is reported as the budget where the walk equals search.

**Jev step, only if the rule changes.** The 150 test cards at k=5, cap $0.50; W1 at k=5 is the bar.
