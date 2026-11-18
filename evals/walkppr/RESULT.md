# W1: fusing read-set PageRank with Jev's P helps cards and PR titles, but harms MuSiQue, and on PR titles it is mostly width

*18 Nov 2026, james. Registered first (REGISTERED.md, 3ddc70d). $0: bill's recorded test batches, first door per
wave.*

| set (waves with a gold door) | P | P+PPR | P+shuffled PPR | P+width | PPR alone | search order |
|---|---|---|---|---|---|---|
| cards (147) | .687 | **.796** | .442 | .415 | .571 | .490 |
| PR titles (95) | .126 | **.284** | .253 | .211 | .274 | .211 |
| MuSiQue (149) | **.591** | .497 | .389 | .362 | .389 | .289 |

The cells are gold-door-first rates. MRR follows the same pattern. On the read-weighted measure (the first door's
gold rate as a share of the best gold door's), P+PPR equals P on cards (.389 against .384) and PR titles (.025
against .020), and halves it on MuSiQue (.184 against .416). Output: `w1.txt`.

**Verdict: fail.** The bar was +.05 over P on two sets, +.03 over shuffled on those sets, and no set down by more
than .03. Cards passes (+.109; +.354 over shuffled). PR titles passes by the narrowest margin (+.158; +.031 over
shuffled). MuSiQue drops by .094.

## Postmortem

- **Summed PPR rewards width, and so does what it gains on PR titles.** P+shuffled PPR alone gets PR titles from .126
  to .253. That is the width effect bill flagged on Jev's own errors. Only .031 of the .158 is structure beyond width.
  On MuSiQue, fusion promotes wide doors with some gold behind them, which is why the first door's gold rate
  collapses (.42 → .18). The gold-first count hides it, the read-weighted measure shows it.
- **Cards is the real structural gain:** +.354 over shuffled. Cards is also where Jev was already strong (.687).
- **The registration chose the summed variant** because it passed bill's AUC bar. Bill's width-matched result was
  in hand and pointed to the mean-per-target variant as the width-neutral one. I should have registered both. A
  mean-PPR arm, or a width-matched fusion, is the next registration, not a re-run here.
- **The scope caveat stands:** this is the first door of recorded waves, not a walk. And whether the walk may use
  structure next to P is Sirsh's call (asked with this result).
