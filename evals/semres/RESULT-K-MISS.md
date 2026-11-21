# Where the lexical door misses: discrimination, not coverage. Naming the bridge is worth +.14

*21 Nov 2026, james. This is an unregistered pricing look on SR-KB's 300 (seed 1341, questions 41–1252 minus SR-J-R's
40). That is seen data. It cost $0 and made no Jev calls. Scripts: `k_miss.py`, `k_miss2.py`. Outputs:
`out/k-miss.txt`, `out/k-miss2.txt`.*

**Serves.** REM-1341 asks which cheap operation should do most of Jev's work. The lexical key door k (SR-K) is the best
cheap probe we have: .58 top-1 for hop 2, against .39 for the text probe and .88 for Jev. This look asks why k misses,
so the next operation targets the right failure.

## Where k's 127 misses come from

Read is gold hop 1. "Bridge" means the hop-1 answer.

| outcome | n | share |
|---|---|---|
| hit | 173 | .577 |
| the answer has a door, but a lure's is stronger | 103 | .343 |
| no door, and the bridge is in the answer's text | 15 | .050 |
| no door, and the bridge is absent | 9 | .030 |

- **Most misses aren't for lack of a door.** Only 24 of 127 have no shared key. On those 24, the qr fallback ranks the
  answer first only .08 of the time.
- **Lures win in two ways.** In 54 of the 103, the winning lure also names the bridge (a twin). In 49, it wins on a sum
  of other rare keys. For example, Mean Old Man beats the Dennis Quaid passage on "pioneer jerry", and the 1936
  election beats Eugene V. Debs on "popular vote" and "largest number".

## Can a knob-free reduction of the shared keys fix it?

qr breaks ties throughout.

| reduction | top-1 | top-3 | MRR |
|---|---|---|---|
| qr (text probe, for reference) | .393 | .653 | .559 |
| **sum, Σ 1/(df−1) (SR-K)** | **.577** | .783 | **.703** |
| max, the rarest shared key alone | .550 | .793 | .690 |
| count of shared keys | .537 | .760 | .672 |
| *bridge keys only (ceiling, uses gold)* | *.713* | *.873* | *.807* |

- **SR-K's sum stays best.** Taking only the rarest key, or counting keys, doesn't help.
- **Ceiling (gold, not a door).** If the walker knew which shared key is the hop-1 answer and walked only through it,
  top-1 would rise .58 → .71. That's what Jev does when it reads hop 1, and it's +.14 of the .30 gap to Jev. Of the
  300, 262 reads contain a bridge key.
- **Jev's remaining .17 is something else.** Jev is at .88, above even the gold ceiling (.71), so it must also use
  the question's second relation. In "spouse of ...", for instance, it prefers the passage about the bridge that says
  who they married.

## What it means for next steps

- The next cheap operation should **pick the bridge key out of the shared set**, not add keys or reweight them.
  Doing that without gold is a decision. Two options: a single Jev call per read passage ("which of these entities
  answers hop 1?"), or the question's wording. Either can be priced against the .71 ceiling.
- **Twins (54 cases) won't be separated by any key reduction.** They share the bridge. That matches SR-TW and W2: only the
  second relation or an ordered step separates them.
- For bill's ColBERT test, a token-level readout against the whole read passage could fail the same way as sum
  (many weak matches beating one identity). Scoring against the bridge's tokens is the version that could reach the
  ceiling.

## Postmortem

- **What went right.** It was a $0 look at the failure before proposing a fix, and it changed the target from coverage
  to discrimination.
- **What to watch.** The bridge ceiling uses gold. It sizes an opportunity and is not a method; any method that names
  the bridge must be registered and tested on a fresh draw. Word-set matching of keys to the answer is loose (a one-word answer can match a
  common key), so the ceiling is approximate. I didn't count how often that happens.
- **Scope.** This is seen data and one corpus (MuSiQue 2-hop). The orderings, not the levels, are what it rests on.
