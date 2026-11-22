# SR-BS4 (registered 22 Nov, before any Jev call): the reader-tied stop as a live walk on fresh questions

*james. Follows the R-stop replay check (#105): the reader-tied stop beat the knowledge stop by +.050 at the same set
size. Against oracle H it was −.023 [−.057, +.007], but 10% never fired, and the replay cut those at an H-dependent
length. bill said yes at 17:48Z, and his three notes are applied. Script `srbs4.py`. Cap $0.50.*

**Question.** Walked live, with no oracle in any cut, is the reader-tied stop within .05 of oracle H at the reader?

**Data.** 300 fresh answerable chains (100 each of 2-hop, 3hop1, 4hop1) from the full MuSiQue train file, SEED 1349.
Every earlier Jev study's questions are excluded, and the exclusion is asserted: SR-BX, SR-BE, SR-BH, SR-BS, SR-AC,
SR-BF, SR-BS2, and SR-BS3 and R-stop by id.

**Walk.** Jev's entry request, then the pass step. After each read: bill's reader request (srac.py, verbatim) plus
NONE. **Stop at the first read where a real sentence wins, or when the pool of 20 is empty.** There is no other cap.
The trajectory always reaches at least H reads, so oracle H is scored on the same walk.

**Primary (bill's note 2: like for like). AC (string or judge) of the returned set, using the standard reader request
with no NONE, R-stop − oracle H, paired bootstrap 95% CI, with returned passages and input beside it.**
- **H-S4 (non-inferiority):** the lower bound is above −.05. A fail means "not shown within .05, cost within the lower
  bound", not harm.

**Secondary.**
- **The never-fired walks (bill's note 1):** their count, their AC, their size, and the primary with them excluded.
  Live, their cost is the rule's real cost.
- The distribution of reads at the stop.
- The judge's yes counts.
- A-last.
- By hop type.

**Predictions, made now.**
- AC R-stop − oracle H is about −.02 (the replay's −.023), and H-S4 passes about half the time.
- **Never fired: about 10% (about 30 walks).** These read the whole pool of 20. Their AC is about .30, below the
  replay's 8 of 30 (.27) plus a little from the extra passages. SR-BS3's rival effect makes 20-passage sets worse for
  the reader than the passages up to H.
- Mean returned: about 2.6 for walks that fire, about 4 overall, because the never-fired 20s pull the mean up.

**Spend (bill's note 3).**
- The dry run with random scores estimates $0.15. Random scores fire early, so this misses the tail.
- A second dry run that never fires (`--dry-never`) prices a 20-read walk at about $0.0045 a question.
- At about 10% never-fired, the estimate is $0.30–0.35. At 20% it is about $0.45.
- Cap $0.50, with the per-wave guard. Stage 0 first.

**Scope.** MuSiQue train chains, one fresh draw of 300, the pass step, H hidden from the walk. Production is Sirsh's.
