# S4: no question-free wave property predicts Jev's first door, and none explains PR titles

*19 Nov 2026, bill. Registered first (REGISTERED.md, ba163f0). $0. Output: `s4.txt`.*

The outcome is whether the door Jev ranks first holds unread gold. Each property is scored by its AUC for that outcome,
on test. In brackets: the same property on shuffled links.

| property | cards | PR titles | MuSiQue |
|---|---|---|---|
| gold share (the base rate) | .603 | .707 | .640 |
| vote margin (best gold door against the best gold-free door of similar width, in vote ranks) | .610 (.54) | **.729** (.56) | .532 (.53) |
| vote concentration (top-5 share of the vote) | .557 (.57) | .483 (.45) | .496 (.53) |
| choice size (fewer doors) | .519 | .481 | .524 |
| width spread (lower) | .501 | .516 | .419 |

**Verdict: none predicts.** The bar was .65 on two graphs, beating gold share on every graph, and controls below .65.
Vote margin comes closest: .73 on PR titles, .61 on cards, chance on MuSiQue. Its shuffled control sits at chance, so
what it does carry is structure. On dev it reaches .71 and .78 on cards and PR titles, but test is the registered read.

**Between graphs, structure doesn't explain PR titles.** Jev's gold-first is .687 (cards), .591 (MuSiQue) and .126 (PR
titles). PR-title waves look like cards waves:
- the same choice size (about 80 doors);
- gold share .065 against .081;
- vote concentration .264 against .274.

Vote margin is lowest on PR titles on test, but by about as much as MuSiQue, which Jev handles five times better. No
measured property puts PR titles alone at the bottom.

## Postmortem

- **(b)'s failure on PR titles is not in the structure the walk is offered.** This is the third independent way of
  showing it: V1 and W3 (structure alone ranks PR-title doors better than Jev), and now S4 (PR-title waves are
  structurally ordinary). It matches Sirsh's 16:49 separation: the PR-title fault is in the encoding layer, the door
  text Jev reads, not in the graph. Dreaming as structural edits can't fix it, and james's D1–D3 nulls agree.
- **When structure makes the gold door distinct, Jev finds it more often** (vote margin .73 on PR titles, .61 on
  cards). That is a correlation, not an effect. One reading: Jev's P and the vote partly see the same thing. Another:
  questions whose gold is structurally distinct are easier for both.
- **What the registration missed:** gold share as the "trivial baseline" is itself an AUC of .60–.71, because a wave
  with more gold doors is easier for any picker. Each structural property had to beat it on every graph, which is
  strict. Vote margin beats it on cards and PR titles, not on MuSiQue. A partial-correlation design (each property's
  effect given gold share) would have been fairer. It would be a new registration, not a re-score.
- **Stage 2 (spectral):** the registration said to run it only if stage 1 left the PR-titles gap unexplained, and it
  does. But S4 says wave structure on PR titles is ordinary. A spectral property of the seed neighbourhood would have
  to differ sharply on PR titles while the wave-level properties don't. That is unlikely, but it's the one question
  Sirsh named that remains untested, and it's cheap, so it's next (registered separately).
