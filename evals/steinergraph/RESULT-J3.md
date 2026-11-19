# J3: the doors of what has been read don't replace the fill; choosing the fill is choosing the door

*19 Nov 2026, bill. Registered first (REGISTERED-J3.md, 00a129d). $0, no Jev. Output: `j3.txt`; per-sub-question
ranks are written to the run dir as `j3-hops.jsonl`.*

MuSiQue test, the 247 later sub-questions (hop 2 onward). Share whose own gold passage is in that hop's top 5:

| how the later hop is searched | top 5 |
|---|---|
| probe search, sub-question filled with the gold answer (P2's dumps) | .806 |
| **F:** probe search, filled with Jev's pick (J2) | **.449** |
| **DO:** BM25 of the unfilled sub-question among the doors of the earlier gold passages | .397 |
| **D:** the same, among the doors of what was actually read | .348 |
| **B:** BM25 of the unfilled sub-question over the whole corpus | .320 |
| probe search, unfilled (P2's dumps) | .291 |

**Verdict: fail at the gate.**
- DO − F = −.053 [−.121, +.012], against a gate of +.05. Even reading the right passages, searching their doors
  with the unfilled sub-question lands less often than Jev's fill does.
- By the registration D wasn't scored against the bar. Its line prints with the table, which costs nothing at $0.
  D − B is +.028.

## What it says

- **The gold is among the doors, but the doors don't say which one.**
  - Around what D has read, the gold of the next hop is among the neighbours 81% of the time.
  - But there are about 2,500 neighbours (12% of the corpus). The unfilled sub-question ("Who is the spouse of") can't
    tell the right one from the rest.
  - Restricting to the doors adds only +.03 over searching everywhere (D − B), and +.08 with perfect reads (DO − B).
  - That is P2's step result again: about 530 links per passage, mostly wide entity doors, dilute any move that
    doesn't know which door to take.
- **The fill is the door choice.** The door to the next hop is the answer entity, and naming it is what the fill
  does.
  - With the right answer filled, later hops land as often as hop 1 (.806 against .81).
  - With nothing filled, they land a third as often (.291).
  - So deciding hop j's answer and choosing which door to walk through are the same decision. No search over the
    neighbourhood avoids it.
  - Jev's 55% accuracy at that decision is why J2 sits at .449, between the two.
- **This explanation has no constant in it** (Sirsh, 15:09). The gap from .291 to .806 is the value of one decision per
  hop. The compounding J2 measured is that decision going wrong and the next search inheriting it. Better hops need a
  better choice among the doors; more breadth won't do it.
- **The ranker is not the confound.** My BM25 and the probe agree on unfilled text (.320 against .291), so F and D are
  comparable across rankers within about .03.

## Postmortem

- **The gate was right to be set on the oracle, and it closed at $0.**
- **I registered the hypothesis without its cheapest check.**
  - The probe's unfilled-text rate (.291) was already in P2's dumps. With it, the gold-filled rate (.806) shows the
    fill worth about .5 of top 5, more than any neighbourhood restriction could plausibly recover.
  - A one-line check before registering would have predicted the gate. The rule from P2 applies again: look at the
    dev spread of what you already have before registering a bar.
- **What's left is what Jev does at each hop: pick the answer, which is to pick the door.** J1 and J2 measured that
  (55% where the answer is a candidate). Raising it is a question of what Jev is shown about each candidate door, its
  presentation. It isn't a question of widening anything.
