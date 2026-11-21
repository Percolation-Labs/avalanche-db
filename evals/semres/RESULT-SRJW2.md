# SR-JW2 result: on fair text, Jev picks the answer's door by type and relation together, but doesn't follow a relation it has read

*21 Nov 2026, james. Registration: REGISTERED-SRJW2.md (455a87e). The bar was amended to ≥ 13/16 before stage 0, per
bill's review. Jev spend: $0.00019 + $0.00056 = **$0.00075**. Outputs: out/srjw2-{0,1}.{txt,json}; the cache is
~/.cache/walklab/srjw2-jev-cache.jsonl.*

**PASS.** At hop 2, Jev's chain door is uniquely first in **14 of 16** (the bar is ≥ 13).

Chain door uniquely first, of 16:

| | Hop 1 (at s) | Hop 2 (at b) |
|---|---|---|
| **Jev** | **1** | **14** |
| Theory (β 1, γ 3.7) | 10 (first, ties allowed) | 0 |
| cos | 4 (first) | 0 |
| Literal type word in the door | 0 | 0 |
| Relation phrase or start name in the door | 0 | 0 |
| A read sentence links to the door by a needed relation | **7** | 0 |
| The same + the generator's type dictionary | 4 | 9 (**16 counting ties**) |

| | Hop 1 | Hop 2 |
|---|---|---|
| log(Jev share / theory share), median | **−1.58 [−1.99, −0.97]** | **+0.34 [+0.23, +0.67]** |
| Way-back share at b (Jev / theory) | — | **.098 / .286** |

## What it shows

1. **At the bridge, Jev uses relation and type together.**
   - Each of b's two decoys matches one of the two: the answer's type by another relation, or the needed relation to
     another type.
   - Relation alone ties a with the second decoy (0 of 16). Type alone ties a with the first.
   - The dictionary reader, with the generator's own word lists, reaches the top in 16 of 16 but ties there in 7.
   - Jev separates a uniquely in 14 of 16, without the word lists. It infers "composer" from "orchestra, opera, concert"
     and takes the relation from b's read text.
   - With the literal giveaway gone, the type term (γ_type) is real here.
2. **Jev still doesn't go back.** The way-back share is .098 against the theory's .286. Jev knows s is read.
3. **At the start, Jev doesn't follow the relation it has read.**
   - s's read text says "s <r1> b". A one-rule string reader takes that door uniquely in 7 of 16. Jev does so in 1.
   - Jev's top door at hop 1 is neither the asked type (4 of 16) nor linked by a needed relation (5 of 16). Its shares
     are near uniform (.03–.35 over 4–7 doors).
   - **Mechanism, as I read it (not measured):** the TASK asks whether reading a door "gives information needed". Under
     fix 3, b's own text is just topic words, so no door at hop 1 shows anything the question needs. Jev scores the
     doors' content and doesn't credit the relation sentence it has read. On real text, a bridge passage carries its own
     links, and SR-J on MuSiQue (97% first) had that.
   - So the hop-1 failure is partly the renderer, but it also says something real: Jev prices a door by what the door
     shows, not by what the read text says about it.

## For the theory

The conductance of a door, as Jev prices it on these worlds:
- **+ the door's own match to the question's needs** (type, with relation when the read text names it). That's strong:
  hop 2 is +0.34 nats over a theory that already gives 3.7 for the relation.
- **− already read.** The way-back share is a third of the theory's.
- **No credit for a relation the read text asserts about a door whose own text shows nothing.** So a bridge that "looks
  like nothing" is high resistance to Jev, even when the read passage points straight at it.
- That last point is the semantic version of the single-seed chain miss. The way in to a chain is the dear step.

## Postmortem

- *Predicted:*
  - Hop 2 ≥ 12 of 16: right, 14.
  - The hop-1 deficit repeats: right, and larger (−1.58).
  - The back share stays low: right.
  - I didn't predict that a one-rule string reader beats Jev at hop 1 (7 against 1).
- *Process:* this time bill reviewed before any call and amended the bar, as agreed after SR-JW.
- *Spend:* $0.00075. Today's Jev total for james is about $0.0023.
- *Next:* test the hop-1 mechanism. The same worlds and calls, but each door shows its own links: one door's text says
  what it connects to, as real passages do. **Prediction:** Jev's hop-1 unique-first rises from 1 toward the
  relation-sentence reader's 7 or above. About $0.0004, and I'd register it with bill's review first.
