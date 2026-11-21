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

## Amendment 2 result: the bridge entity carries Jev's choice as a decider, but the fit can't split the two terms ($0)

The feature is e(v): v names the hop-1 answer. Output: `out/srj-entity.txt`.

| fit (760 options) | cos_q | e (bridge entity in v) | γ, hop 2 |
|---|---|---|---|
| cos_q + hop 2 (stage 1) | +1.00 | — | +3.77 [+3.39, +4.16] |
| cos_q + e | +.96 | **+3.80 [+3.41, +4.20]** | — |
| cos_q + e + hop 2 | +.93 | +1.19 [+.73, +1.59] | +2.70 [+2.40, +3.00] |

- e finds hop 2 with recall .90 and precision .97 (36 of 37 e = 1 options are hop 2).
- An e-decider, with ties broken by cos(question + read), takes hop 2 first in **.90** of questions. Jev scores .97, and the
  best vector decider .62.

**The registered bar fails by the letter.** γ falls from 3.77 to 2.70, which is 28%, not half, though δ is above 0.

**But the bar was badly posed, and I should have seen it before registering.** e and hop 2 coincide on 90% of hop-2
options and 97% of e options. With collinear regressors, the split between δ and γ is set by the handful of options
where they disagree, so "γ halves" was never a stable test. The precision and recall were computable at $0 before the
fit.

**What the data does say:**
- e alone carries as much of Jev's log-odds as the oracle label does: 3.80 against 3.77 nats.
- The e-decider recovers 90 of Jev's 97 points of top-1.

So, as a decider, "v names what `read` resolved" reproduces most of what Jev knows beyond cosine. As a theory term, that's
an entity-level edge conductance of about 3.8 nats, which text can compute through NER or the walk's own key doors. It
needs the bridge entity *read off `read`*, not taken from the decomposition. That is the next $0 step: use the keys `read`
shares with v (the L1 graph's doors) in place of e.

**Postmortem addition.** A collinearity check (e's precision and recall against hop 2) belongs before any registered
bar that splits two regressors. That's the same lesson as this morning's, in a new place: look at the numbers the bar
depends on before writing the bar.

## Amendment 3 result: on cards, Jev is still softer on similarity than the vectors, but its relational term is half MuSiQue's

The run covered 40 dev cards, 19 options each (gold commits plus the commits nearest the question). Jev spend: stage 0
$0.00077, stage 1 $0.00741. **Today's total is $0.0126.** Output: `out/srj-cards-n{4,40}.{txt,json}`.

| on the same option sets | β_q (nats per cos) | β_r (nats per cos) | γ, gold (nats) | top 1 is gold |
|---|---|---|---|---|
| vectors' Bayes slope | −6.15 (selection effect) | 6.75 | — | search .17, cos read .25 |
| Jev, cos_q + gold | +3.13 [+1.77, +4.73] | — | +1.62 [+1.44, +1.79] | **.75** (coin .03) |
| Jev, cos_q + cos_r + gold | +2.19 [−.18, +5.15] | +1.73 [−1.21, +4.52] | +1.58 [+1.39, +1.75] | |

**The registered directional readout, part by part:**
- **"β_r well below the vectors'."** It holds in the point estimate, 1.7 against 6.8, but the interval reaches 4.5. So it
  is softer by about 4× here, against about 12× on MuSiQue.
- **"γ ≥ 2 nats."** It fails: γ is 1.6 [1.4, 1.8].
- **Overall,** the "soft on similarity, strong on relation" picture holds on cards in direction but is weaker. Cards
  have up to 3 gold per question, and the relation from card to commit is looser than MuSiQue's bridge entity.
  - Jev still takes gold first in 75% of cards, against 17–25% for the vector deciders.
- **Unlike MuSiQue, Jev's slope on question-cosine is positive (+3.1)** where the vectors' is negative on these hand-hard
  option sets. On cards, Jev does follow the question's wording somewhat, so MuSiQue's β ≈ 1 is partly that corpus's
  construction.

**What carries into the theory**, across two corpora:
- **The similarity slope.** Jev's is about 1–3 nats per cos unit, against the vectors' Bayes slope of 7–10. That's
  softer, consistently.
- **The relational term.** It's real on both corpora but depends on the corpus: about 3.7 nats on MuSiQue's single-entity
  bridges and about 1.6 on cards.
- **Consequence.** James's SR1c conductance should carry γ as a corpus-measured number, not a constant. The carry-over
  test then predicts a weaker Jev walk on cards than on MuSiQue, which can be checked against the L1 walks we already
  have.
