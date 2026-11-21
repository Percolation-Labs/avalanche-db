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
