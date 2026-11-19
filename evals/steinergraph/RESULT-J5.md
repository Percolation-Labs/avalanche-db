# J5: showing Jev where each candidate leads doesn't help, because the passage it was shown is rarely the next hop

*19 Nov 2026, bill. Registered first (REGISTERED-J5.md, 7bc3948). Jev spend $0.0208 (stage 0 $0.0007, full run
$0.0201). Day total $0.0606. Output: `j5.txt`, `j5diag.py`.*

MuSiQue test, 150 questions, J1's candidates, total recall at 10 reads:

| Jev sees per candidate | total recall | right where gold is a candidate |
|---|---|---|
| J1: the answer and its sentence | .578 | 65/119 |
| **J5: the same, plus how many passages it leads to and the one closest to the question** | **.574** | **69/119** |

**Verdict: fail.** J5 − J1 = −.004 [−.033, +.026], against a bar of +.02. 10 questions went up and 13 went down.
The 4 extra right picks are noise.

## Why ($0 diagnostic, not registered)

- Of the 119 decisions where the gold answer was a candidate, the gold answer has a door (a key held by 2–100
  passages) in 93 (78%).
- But the door's "closest to the question" passage, the one Jev was shown, is the next hop's gold in only **12
  (10%)**.
- So for most right answers, the extra text described an unrelated passage. It said nothing in favour of the right
  candidate, and Jev ignored it, rightly.

## What it says

- **A high AUC didn't make a good pointer.** J4 measured whole-question likeness at AUC .84 among the doors. J4b
  measured it alone at .243–.304 in the top 5 (single signals: .077–.304). Here, at top 1, behind a single door, it picked the next gold 10% of the time.
  A signal that orders 2,500 candidates well can still fail to name the one passage worth showing. I registered the
  presentation from J4's AUC, and J4b had already warned against that.
- **The door count alone carries little.** "Leads to 59 passages" doesn't tell Jev whether the right one is among
  them.
- **What would carry it** is a description that names the next hop: the passage behind the door that matches the
  *next sub-question*. J4b found the sub-question better at the top of the ranking (.348 against .243). That's the
  same decision as J3's fill, made one hop earlier. This is a registration of its own, and I'm not running it now.

## Postmortem

- **I chose the "closest passage" from the measure that ranked well (AUC), not the one that ranked well at the
  top.** J4b's own table showed whole-question likeness weaker at the top than the sub-question. A $0 count of the
  diagnostic above, before the Jev run, would have shown 10% and stopped it. That makes four results today where a
  look at data already in hand would have predicted the outcome (P2, J3, J4, J5).
- **The standing rule I'm adding: before a Jev run whose presentation shows a computed pointer, measure at $0 how
  often the pointer is right.**
- **Scope.** One presentation, MuSiQue only, J1's candidates. J5 is the third presentation scored on the same 150 test
  questions as J1 and J2. That's mild reuse of the held-out set. It doesn't change a null, but the next registration
  draws its questions fresh, or from dev.
