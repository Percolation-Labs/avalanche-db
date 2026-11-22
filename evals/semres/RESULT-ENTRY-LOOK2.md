# Entry look 2 (22 Nov, post hoc, $0): Jev's 20-passage entry request picks the right walk in 39 of 50 split questions

*bill. Script `entry_look2.py`, output `out/entry-look2.txt`. It rebuilds SR-BX's 300 scored walks from SR-BX's Jev
cache with the cap at $0 (no call made). These are seen questions, and six rules were tried, so this prices an idea for
SR-BE (registered alongside); it isn't a result.*

**Serves.** Sirsh's 15:52Z steer: the entry look. NOTE-D3M's addendum found that walking from both the cosine entry and
Jev's title entry would reach .817 both hops with an oracle choosing, against .723 for the cosine walk alone, and the
best gold-free rule then (.747) recovered a quarter of that.

## Why the entry misses

The cosine entry is neither hop in 48 of 300 questions; the title entry in 45.

| the wrong entry is… | cosine | title |
|---|---|---|
| linked to a hop by a door key (a neighbour) | 21 | 23 |
| a namesake of a hop (same title, other passage) | 13 | 13 |
| linked to neither hop | 14 | 9 |

- **A wrong entry is fatal.** The 2-hop walk recovers both hops in **0** of these, since the step can't come back.
- **Hop 1 is near the top.** Its median rank is 4 by cosine and 2 in Jev's 20-passage entry request. The entry
  request ranks the right passage high but, on its own, picks it less often (SR-BX: e_pass hop 1 .607).

## Choosing between the two walks

The walks agree on the pair in 231 questions. In 50, exactly one gets both hops (cosine 22, title 28).

| keep the walk whose… | both hops | − cosine walk | right of 50 |
|---|---|---|---|
| entry scores higher in Jev's 20-passage entry request | .780 | +.057 [+.023, +.093] | 39 |
| entry p × its step's p | .790 | +.067 [+.033, +.103] | 42 |
| entry p + step's entry p | .770 | +.047 [+.010, +.087] | 36 |
| chosen step has the higher pass p | .757 | +.033 [+.007, +.063] | 32 |
| entry's best pass p (NOTE-D3M's rule) | .747 | +.023 [−.003, +.050] | 29 |
| door strength between entry and step | .710 | −.013 [−.043, +.017] | 18 |
| *oracle* | *.817* | | *50* |

- **The entry request knows which entry is right better than it knows which passage is first.** Asked to choose among
  all 20, it lands on hop 1 61% of the time. Asked only to compare the two candidates, it is right 39 of 50 times.
  Cosine and the title request propose; Jev's entry request disposes.
- **Structure can't choose.** Door strength is worse than always taking cosine's walk.
- **NOTE-D3M asked the wrong request.** Its rule used the step request's confidence, which says how good the *next*
  passage looks, not whether the entry was right.

## Postmortem

- **What went right.** The $0 cap caught my first run on the wrong question file before any call (the cache missed,
  and the estimate stopped it). A miss breakdown before choosing rules showed that namesakes are only a quarter of the
  misses, so a title fix alone can't close the gap.
- **What I got wrong.** NOTE-D3M's addendum tried one selector and concluded "the selector is the bottleneck". It was,
  but the answer was already in its cache: the entry request it had paid for and didn't use.
- **Scope.** 300 seen questions; the best of six rules is optimistic. SR-BE tests the simplest rule (entry p) on a fresh
  draw, against the control that matters: if the entry request is paid for anyway, walk from its own argmax.
