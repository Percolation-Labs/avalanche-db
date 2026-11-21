# SR-JW result: Jev on rendered worlds. The theory is calibrated on average, wrong in two opposite ways per hop

> **Amendment (bill's review, board M-20261121-135227): the hop-2 result is WITHDRAWN.** In 16 of 16 cases, exactly one
> of b's unread doors says "is a <answer type>.", and it is a. A type-only string matcher picks it 16 of 16, the same as
> Jev. My word-overlap control normalised by passage length, and every rendered passage carries all its link
> sentences, so the one decisive word was drowned. So "Jev splits doors by the answer's type" is what a string matcher
> does on this renderer, not evidence of relational reading. γ_type is a renderer artifact until shown on text with no
> literal type sentence. What stands is independent of that string: the hop-1 deficit (−0.78) and the lower way-back
> share (.08 against .36, because s is read). Fixes before any further Jev call:
> 1. Describe the type through topic words only, never "is a <type>", and give 2–3 other doors the same type.
> 2. Add type-only and exact-phrase deciders as registered control rows.
> 3. Show each door its own text only.

*21 Nov 2026, james. Registration: REGISTERED-SRJW.md. Jev spend: stage 0 $0.00037 (measured). Stage 1 had 24 requests at
the same size, about $0.0011; its printed spend line didn't survive my log filter. The total is about $0.0015.
Outputs: out/srjw-{0,1}.{txt,json}; the cache is ~/.cache/walklab/srjw-jev-cache.jsonl (32 entries).*

**PASS by the letter, and I don't claim it in substance.** The median log(Jev's share / the theory's share) at the chain
door is **+0.10 [−0.48, +0.53]** (n = 32 hops), and the interval covers 0. But split by hop, both halves are significant
and opposite. They cancel:

| | Jev / theory at the chain door, median log | Chain door ranked first: Jev / theory / cos / word overlap |
|---|---|---|
| Hop 1 (at s) | **−0.78 [−1.03, −0.44]** | 8 / 10 / 6 / 0 of 16 |
| Hop 2 (at b) | **+0.63 [+0.51, +0.88]** | **16** / 1 / 1 / 0 of 16 |
| Overall | +0.10 [−0.48, +0.53] | 24 / 11 / 7 / 0 of 32 |

**The way back, at b to s.** Jev's share has a median of **.082** against the theory's .357. It is lower in 15 of 16.

## What it shows

1. **At hop 2, Jev beats the theory on every case.**
   - b usually has 2–3 doors with the question's relations. The theory gives them all the same 3.7 nats.
   - Jev splits them by the answer's type ("Which *university*…": the answer's passage says "is a university") and puts the
     chain door first in 16 of 16.
   - Word overlap, which sees the same type word, ranks it first in 0 of 32. So it isn't word-matching. Jev reads which
     door leads to a thing of the asked type.
   - The theory's γ term is relation-only. It needs a **type** term.
2. **Jev doesn't go back.** The back share is .08 against .36.
   - Jev knows s is already read; the TASK says "not yet read", and s is in `read`.
   - That's the direction memory the vector theory had to bolt on, and in Jev it comes from the read set.
   - In circuit terms, reading is what makes the network non-reversible.
3. **At hop 1, the theory is over-confident.** There, the chain door is usually the *only* relational door. The theory
   gives it .88–.94 of the step, and Jev gives it .3–.6. Before anything has been read, Jev hedges across the start's
   doors. γ = 3.7 was measured when Jev had already read hop 1, and it overstates Jev's confidence at the first hop.
4. **Reach.**
   - The two errors cancel in the chain product, so the theory's predicted reach is close to the reach from Jev's own
     shares: within a factor of about 1.3 on 13 of 16 cases (out/srjw-1.txt).
   - That agreement is cancellation, not calibration.

## What the theory needs (from Jev, measured)

The conductance of door u → v becomes:

  exp(β·cos + γ_rel·[the relation is the needed one] + γ_type·[v is of the asked type] + γ_read·[v already read]) — γ_read ≈ −0.85, not −∞ (see RESULT-FITJEV)

- γ depends on the state. It is weaker before the first read and stronger after.
- The read set removes the back-current outright. With it, "inductance" is not a separate quantity; it is memory.

## Postmortem

- *Predicted:*
  - Jev first at most hops: right, 24 of 32.
  - Jev above the theory overall, with an interval maybe above 0: **wrong overall**. Right at hop 2, but hop 1 went the
    other way, which I didn't foresee.
  - Word overlap beats cos at hop 2: **wrong**, 0 against 1.
- *Could a $0 look have caught hop 1?* Yes. The theory's hop-1 shares (.88–.94 with one relational door) were printable
  before any call, and SR-J's γ came from a post-read state. I should have registered the readout split by hop, since
  the theory's γ was measured at one of them.
- *Spend:* about $0.0015, under the registered $0.05 cap per stage. Today's Jev total, bill's and mine, is about $0.014.
- *Constants:* β = 1.0 and γ = 3.7 are bill's measurements. The rendering word lists are fixed and not tuned.
- *Next:*
  1. Fit γ_rel, γ_type and the read mask from these 32 option sets, then test on 4 fresh rendered worlds. That's $0 to
     fit, and about $0.002 for the test, registered first.
  2. bill's per-question T\* pricing on real walks.
