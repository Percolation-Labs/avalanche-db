# SR-J: Jev's semantic conductance against the vectors' (registered before any Jev call)

*21 Nov 2026, bill. Brief: Sirsh, 13:15Z and 13:16Z: show the theory in vector space, then show that it carries over to
what a decision model actually does, with Jev, least spend, registered first. Code: `srj.py`; the $0 look is
`srj_look.py`.*

## The $0 look (done before this registration)

The data is MuSiQue 2-hop dev, the first 200 answerable questions, embedded with bge-small-en-v1.5. For each question
there are 19 options left after the hop-1 passage.
- **The vectors' Bayes slope.** Gold hop 2 regressed logistically on cos(question, passage) gives **β_B = 8.7 nats per cos
  unit** (3,799 options).
- **Typical cosines.** Hop 1 sits at .705, hop 2 at .559, and the best distractor at .616.
- **The median crossing cost,** β_B·(best distractor − hop 2), is **0.52 nats**.
- **Hop 2 by cos alone** ranks a median 4th of 19 (top 1: 22%).

So the magnitudes are healthy, not degenerate.

## The question

When Jev chooses the next passage, does it follow the vectors?
- **β_J > β_B:** Jev is sharper than cosine, and a crossing costs Jev more.
- **β_J < β_B:** Jev is softer.
- **γ.** Whatever Jev knows beyond the cosine, from the read passage's bridge entity, is a hop-2 term γ in nats. This is
  Sirsh's "a decider works roughly in semantic space, though it isn't that simple", made a number.

## Stage 0

- **Cases.** 4 questions, the first 4 of the 200, with hop-2 cos ranks 7, 4, 3 and 16. That's one batched request each,
  all in flight together.
- **Prompt.** Jev's state is {question, read = the hop-1 passage, task}. Each option is a Noul over the passage text.
- **Fit.** logit p_Jev = β_J·cos + γ·[hop 2] + c, by least squares over the 76 options, with p clipped to [1e−4, 1 − 1e−4].
- **Controls.** The rank of hop 2 among the 19 under chance, coin, word overlap (question + read passage), search cos,
  Jev and oracle.
- **Spend.** Cap $0.05, estimated about $0.001. The spend is stated in the result.
- **Stage-0 readout, magnitudes and direction only, with no bar.**
  - The signs and sizes of β_J and γ.
  - Jev's hop-2 rank against the controls.
  - A check that Jev's p isn't degenerate: if every p sits within .05 of 0 or 1, that is reported and stage 1 isn't
    proposed.
- **Predictions.**
  - β_J > 0, but below β_B. Jev reads text, so similarity matters to it less than to the vectors.
  - γ > 0 and large, because Jev sees the bridge entity in `read`.
  - Jev ranks hop 2 better than search cos and word overlap.

## Stage 1, if stage 0 shows direction

Stage 1 covers 40 questions, at about $0.01. It is registered as an amendment with bootstrap intervals on β_J and γ, and
needs no further yes under the $1 rule.
- **The carry-over test:** james's (a) formula, with Jev's crossing cost (β_J in place of β_B) predicting Jev's hit rate.

## Stage 0 result (spend $0.00045)

- **Jev ranks hop 2 first in all 4 questions.** Search cos ranks it 7, 4, 3 and 16. Word overlap ranks it 11, 3, 7 and 1.
- p_Jev(hop 2) ranges .48–.85, and the best other option .11–.30, so it isn't degenerate.
- **β_J = −0.15**, against β_B = 8.7. Jev ignores the cosine to the question.
- **γ = +3.24 nats.** Every bit of Jev's preference is in the hop-2 term.
- Predictions:
  - "β_J below β_B": yes, but far below. It's about 0, not merely softer.
  - "γ > 0 and large": yes.
  - "Jev beats the controls": yes.

## Amendment 1: stage 1 (registered before it runs)

Stage 0 suggests Jev's semantic space isn't the question's. Its state includes the passage it has read, so its
conductance should follow cos(read, option), the walker's state. That's direction memory in vector form.

- **Cases.** The first 40 of the 200 questions (stage 0's 4 included, answered from cache). One wave of requests.
- **Spend.** Cap $0.05, estimated about $0.004.
- **Fit.** logit p_Jev = β_q·cos(question, v) + β_r·cos(read, v) + γ·[hop 2] + c, with bge-small and no query prefix for
  read. Each is reported with a bootstrap 95% interval over questions (2,000 resamples).
  - The same fit with only cos_q is also reported, to compare with stage 0.
- **Vector-space deciders,** ranking hop 2 among the 19:
  - cos_q (search);
  - cos_r;
  - cos to (question + read) as one probe.
  These run beside Jev and the five controls. Rank is reported as top-1 share and mean rank.
- **Carry-over readouts.**
  - (i) β_r against β_B,r: the vectors' own Bayes slope of hop 2 on cos_r, fitted on the 200 the same way as β_B.
  - (ii) Whether adding cos_r shrinks γ. That's the share of Jev's hop-2 knowledge that the state vector explains.
- **Directional bar.**
  - β_r's interval is above 0 and β_q's covers 0.
  - γ falls by at least half when cos_r is added.
  - If both hold, a vector conductance with the walker's state as probe is a fair model of Jev's choice. Otherwise, the
    result says how much of the choice vectors don't explain.

## Amendment 2: is γ the bridge entity? (registered before it runs; $0, Jev answers from the stage-1 cache)

**The feature.** e(v) = 1 if the hop-1 answer (MuSiQue's `question_decomposition[0].answer`, or any of its words of ≥4
letters that aren't stopwords, all present) appears in v's text, case-folded.

This is an upper-bound probe: it uses the decomposition's answer, which a walker would have to read off `read`. The
question is whether the extra knowledge Jev shows is *the bridge entity named in the next passage*.

**Fit.** On the same 760 options with the same bootstrap:
- logit p_Jev = β_q·cos_q + δ·e + γ·[hop 2] + c;
- the same without γ, to see what e alone carries.

Also reported:
- e's precision for hop 2: the share of e = 1 options that are hop 2;
- e's recall: hop 2 has e = 1;
- the e-decider's top-1 share, with ties broken by cos(question + read).

**Directional bar.** γ falls by at least half when e is added, and δ's interval is above 0. If both hold, the edge term
is "v names what `read` resolved", an entity-level relation computable from text (by NER or the walk's own doors). If
γ stays, Jev knows something beyond the entity string.
