# SR-J result: Jev doesn't price a crossing the way the vectors do. It's about 10× softer on cosine and carries 3.7 nats the vectors can't see

*21 Nov 2026, bill. Registered in REGISTERED-SRJ.md (e5a6b58), with amendment 1 (868251b) made before stage 1. Jev
spend: stage 0 $0.00045 and stage 1 $0.00395, so **$0.0044 in total today**. No Claude data.*

## Result: 40 MuSiQue 2-hop dev questions, 19 options each, after reading the hop-1 passage

**Rank of the true hop-2 passage among the 19:**

| decider | mean rank | top 1 |
|---|---|---|
| chance / coin | 10.0 / 10.4 | .00 / .03 |
| word overlap (question + read) | 4.9 | .33 |
| search: cos(question, v) | 6.2 | .20 |
| cos(read, v) | 3.3 | .55 |
| cos(question + read, v), one probe | 3.0 | .62 |
| **Jev** | **1.0** | **.97** |
| oracle | 1.0 | 1.00 |

**Jev's log-odds as a conductance** (logit p_Jev, 760 options, 95% bootstrap over questions):

| fit | β_q (nats per cos) | β_r (nats per cos) | γ, hop 2 (nats) |
|---|---|---|---|
| cos_q only | +1.00 [+.13, +1.74] | — | +3.77 [+3.38, +4.14] |
| cos_q + cos_r | +.29 [−.70, +1.22] | +.88 [−.03, +1.84] | +3.70 [+3.29, +4.08] |
| *the vectors' own Bayes slopes* | *8.7* | *10.2* | — |

**The registered bar fails on both parts.** β_r's interval touches 0, and adding cos_r leaves γ almost unchanged (3.77 to
3.70, not halved). A vector conductance with the walker's state as probe is **not** a fair model of Jev's choice.

## What it means for the theory

1. **Jev is a near-perfect next-hop chooser here.** It puts the true hop 2 first in 97% of questions, where the best
   vector decider manages 62%. The step's "semantic resistance" is low for Jev, and not because the passage looks like
   the question: hop 2 is usually *less* like the question than the best distractor (.559 against .616 in the $0 look).
2. **Jev's dependence on cosine is about 10× softer than the vectors'.** β is about 1 nat per cos unit, against the
   vectors' Bayes 8.7–10.2. Across the spread of cosines among the options, that's well under 1 nat. To Jev, looking
   like the question or like the read passage barely matters.
3. **3.7 nats of Jev's preference are invisible to the vectors.** That's odds of about 40:1 for the true next hop,
   beyond anything bge-small cosine explains, and word overlap doesn't explain it either.
   - This is Sirsh's "a decider works roughly in semantic space, though it isn't that simple", now with a number: the
     vector part is small and the rest is large.
   - In the electrical picture, Jev's conductance is roughly exp(1·cos)·exp(3.7·[link continues the chain]). The second
     factor is a property of the *link*: does v hold the thing that `read` leads to? A node's position in vector space
     doesn't capture it.
4. **This reframes the vector stage.**
   - SR1 and SR23 priced crossings with cosine, giving 6–10 nats in the synthetic world and about 0.5 nats for MuSiQue
     vectors.
   - Jev doesn't pay that price, so a theory that prices Jev's walk from vectors alone will misprice it.
   - The term the theory needs is an *edge* semantic, one that relates `read` to v by relation, not by similarity. This
     matches gen.py's relation vectors r_e, but it has to be computed from text, not given.

## Postmortem

- **Predicted:**
  - "β_J > 0 but below β_B": yes, about 1 against 8.7.
  - "γ large": yes.
  - "Jev beats the controls": yes, by far.
  - Amendment 1 predicted that cos_r would carry Jev's choice. It doesn't. The read passage helps the *vector* deciders
    (top 1 rises from .20 to .55–.62), but not as an account of Jev.
- **Could a $0 look have stopped it?** Not this time. The question was what Jev does, and that costs a call. The stage
  ladder worked: stage 0 cost $0.00045, showed the surprise, and stage 1 was re-aimed before it ran.
- **The caveat that matters most.** MuSiQue's distractors are built to look like the question. That favours a decider
  that ignores question-similarity, so "β ≈ 1" may be specific to MuSiQue's construction. It needs checking on cards and
  PRs before it is called a property of Jev.
- **Constants.** p is clipped to [1e−4, 1−1e−4] for the logit; 5 of 760 values hit the clip. Nothing was fitted to a
  result.

## Next (proposed)

1. **Measure the edge term from text.** Score cos(relation of `read` → v), meaning the bridge entity named in `read` as it
   appears in v, against Jev's γ. If an entity-level vector explains γ, the theory's conductance is complete in vector
   form. That's $0, plus a stage-0 Jev replay from the cache.
2. **The same fit on cards and PRs,** 40 questions each, about $0.01. This checks whether β ≈ 1 is MuSiQue's
   construction or Jev.
3. **For james's (a):** the carry-over prediction should use Jev's (β ≈ 1, γ ≈ 3.7), not the vectors' β. Then Jev's hit
   rate along a chain is predicted by exp(−Σ (crossing cost − 3.7·[true link])) per step.
