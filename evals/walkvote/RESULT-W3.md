# W3: no structural vote helps Jev's first door except on PR titles; dev rejects every variant on cards and MuSiQue

*19 Nov 2026, bill. Registered first (REGISTERED-W3.md, c793067). $0, no Jev. Output: `w3.txt`.*

For each graph, dev chose among three votes fused with P: summed, per-target and within-width. A variant was eligible
only if it didn't cut dev read-weighted (b) by more than .02. Test was scored once.

| | dev choice | test P | test P ⊕ chosen | its shuffled arm | P ⊕ within width |
|---|---|---|---|---|---|
| cards | none (summed: gold-first +.057 but (b) −.032) | .687 | (P stands) | — | .680 |
| PR titles | summed | .126 | **.284** | .242 | .200 |
| MuSiQue | none (every variant below P) | .591 | (P stands) | — | .423 |

Cells are the share of waves where the first door has gold behind it.

**Verdict: fail.** Only PR titles gains (+.158, +.042 over shuffled), and the bar was two sets. The dev guard worked: on
cards and MuSiQue it kept P, so test shows no loss there.

## Postmortem

- **Three fusion variants, one answer.** Summed (W1), per-target (W2) and within-width (W3) all fail to improve Jev's
  first door on cards and MuSiQue. Jev already ranks those graphs' doors at .69 and .59 gold-first, and every way of
  adding the vote costs read-weighted (b). On those two graphs the structure the vote sees is already in Jev's P, or
  the vote adds noise to it.
- **PR titles is the one graph where structure helps.** Dev chose the summed vote on its own, and test confirmed it
  (.126 → .284). This is W1's PR-titles number again, now chosen by dev and not by me. But .242 of it is shuffled,
  so structure beyond width is .042, and read-weighted (b) barely moves (.020 → .025). The fused first door holds gold
  more often but thinly. Width does most of the work.
- **The within-width vote is weaker than V1's measure suggested.** V1's .73–.83 counts pairs within 2× width across
  the whole batch. Most classes here hold one or two doors, so X is often .5. That leaves the order to P's tie-break,
  which is why "within width alone" (.680 on cards) sits right next to P. I didn't see that before registering; the
  .680 is mostly P.
- **What this says for dreaming:** using the vote at decision time doesn't close the encoding gap on two of three
  graphs, and on the third it buys mostly width. Read with V1 and james's D3, the vote marks gold at equal width but
  doesn't translate into better first doors. My next step is the question Sirsh asked on 18 Nov: what structural
  property of a graph predicts a cheap walk, and why PR titles differs. It is not a fourth fusion.
