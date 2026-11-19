# P3 result: "the seeds became connected" is no evidence of the answer on the doors as built

*19 Nov 2026, james. $0, no Jev. Registered in REGISTERED-P3.md (b3ffd87) before the run. Code: p3.py. Output:
out/p3.txt.*

**Verdict: FAIL on every set.** No percolation signal of the walk's final read set predicts whether it found gold
beyond the seeds. Test AUC with 95% bootstrap:

| final wave | cards (135) | PR titles (87) | MuSiQue (133) |
|---|---|---|---|
| joined | .482 [.402, .558] | .557 [.457, .633] | .526 [.437, .616] |
| component | .484 | .557 | .542 |
| coherence (over the degree null) | .525 [.428, .622] | .612 [.381, .829] | .545 [.440, .643] |
| raw links | .546 | .656 | .587 |
| mean degree | .488 | .431 | .473 |

The bar was AUC ≥ .65 with the interval above .5 on two sets. Nothing reaches it. On search's top 10, coherence is
.632 on cards and .609 on PR titles, both with intervals that touch or include .5. Raw links does no better.

**Mechanism.**
1. *A walk's reads are connected by construction.* Every read comes through a door from a passage already read, so
   the read set's induced graph is connected whether or not the reads hold gold. Component size then tracks the
   budget, not the answer.
2. *The seeds start joined.* At wave 0 the five seeds are already one component in 67% of card walks, 75% of PR
   walks and 49% of MuSiQue walks. Joined rises only to 1.00 / 1.00 / .67 by the last wave. It rises by +.026, +.000
   and +.039 at the wave gold is first read, against +.021, +.020 and +.029 at other waves. Seeds join whether or not
   gold arrives.
3. *The graph is an expander at the scale of any door.* Bill's S5 found the seeds' neighbourhoods dense on all three
   graphs. With up to 100 passages behind one shared key, two passages one door apart are linked about as often as
   chance allows, and the degree null removes only the hubs' share of that.

**Postmortem.**
- *Design fault, mine:* I scored connectivity over every door, but the walk only ever reads through doors, so the
  signal was close to a tautology. I should have seen it before registering.
- *What Sirsh's idea needs is convergence on a specific link:* separate seeds reaching the same passage through
  narrow doors (a rare key, Beside). That is a different measure and goes in P3b, registered before running.
- *The shuffled-reads control is uninformative:* random reads one door from the seeds almost never hold gold (1% on
  cards and PR titles, 0% on MuSiQue), so their AUCs rest on one or two positives.
- *The wave-by-wave shares fall at late waves* because fewer walks have those waves. They are reported but not read
  as a trend.
