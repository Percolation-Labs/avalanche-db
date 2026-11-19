# J4b: no constant-free combination of the doors' signals reaches Jev's fill; the case for presenting them to Jev stands

*19 Nov 2026, bill. Registered first (REGISTERED-J4b.md, 0941052). $0. Output: `j4b.txt` (the J4b block of
`j4.py`).*

MuSiQue later sub-questions (247). Gold's top-5 rate among the doors, counting gold outside the doors as a miss:

| ranking of the doors | RO: earlier gold read (median 711 doors) | RD: J3's D reads (median 2,622) |
|---|---|---|
| strength alone | .146 (median rank 41) | .077 (120) |
| whole-question BM25 alone | .304 (17) | .243 (33) |
| Borda (sum of ranks) | .206 (23) | .126 (59) |
| **rank product** | **.320** (10) | **.198** (25) |
| *J3 D: unfilled sub-question BM25 among the doors* | | *.348* |
| *F: probe search, Jev's fill* | *.449* | |
| *probe search, gold fill* | *.806* | |

**Verdict: no.** Neither combination reaches F's .449, so the registered case for a Jev arm stands.

## What it says

- **The rank product helps on the gold reads, and Borda hurts.** The product rewards being near the top of either list.
  Borda averages a good rank with a bad one, so it lands between the two.
- **With what was actually read, the doors multiply (2,622) and every ranking falls.** Even the best combination puts
  gold in the top 5 for only a fifth of the sub-questions.
- **High AUC is not top 5.** AUCs of .84 coexist with median ranks of 10–120, so ranking measures overstate what a
  door signal buys at a 5-read budget.
- **Within the doors, the sub-question (.348) beats the whole question (.243) at the top.** The whole question does
  better on AUC but worse in the top 5. It's good at pushing gold out of the tail, poor at putting it first.
- **So Jev's job is as big as it looked.** The parameter-free bound sits at .20–.35, against .449 for Jev's fill and
  .806 for the right fill. The gap is the answer decision itself: naming the door (J4's diagnostic: the key equals
  the previous answer in 66% of cases).

## Postmortem

- **I misread an AUC as a rank in J4** ("around 400th"). This run corrected it, and RESULT-J4.md now says so. Rule:
  when the budget is 5 reads, report the top-5 rate next to any AUC.
- **Scope.** Two signals, two constant-free combiners, and MuSiQue only. A fitted combination might do better, but
  it would bring the constants Sirsh ruled out.
