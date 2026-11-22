# Open: when to stop

For the open-questions section of WRITEUP-WALK.md.

A walk has to decide when it has read enough to stop. If it knew the hop count, it would stop at about the right
place. No rule we've found does as well without it.

**Two rules come close, at different prices:**

- **Asking Jev whether the question can be answered yet** is cheap, but it stops early. It leaves the answer out
  about 7% more often than the hop-count oracle. Jev partly answers from what it already knows, so it stops before
  the answer passage has been read.
- **Asking the reader itself whether any returned sentence states the answer** stops in the right place more often.
  It's within about 3%, a difference that isn't significant. But it reads about 1.6 times as much, and in 6% of
  questions it never stops at all.

Reading one passage past the right point helps less than it seems. The answer passage is returned more often, but
the extra passage distracts the reader about as much as it helps.

**Still open:**

- **A rule that is cheap and stops in the right place.** One candidate is a reader check that runs only every
  other read, or only after a rescue. That's untested.
- **What to do with the questions where no stop rule fires.** These look like the questions the walk can't
  answer. Returning "not found" there may be the right behaviour, rather than reading on.
- **Whether a fixed read budget is acceptable.** It's a constant, so it's excluded unless Sirsh allows it.
- **Whether any of this holds on a whole corpus,** where reading on is no longer bounded by a pool of 20.

Details: APPENDIX-STEP-STOP.md.
