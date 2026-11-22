# SR-MO: no walk momentum at one step. Any history raises every price by about .3 and narrows the answer's lead

*22 Nov 2026, james. Semantic inductance, intuition (1). Registered in `REGISTERED-SRMO.md` (#76, amendment 1 from
bill's review, before any Jev call). Jev spend: $0.0017 for stage 0 and $0.0384 for the wave (300 requests, one
`ask_many`, cap $0.25). Outputs: `out/srmo-stage0.txt`, `out/srmo-fresh.txt`, `out/srmo-posthoc.txt`,
`out/srmo-fresh.json`.*

**Versions.** percolate-core 0.2.15 (Jev), bge-small-en-v1.5, graph-mq. MuSiQue dev 3hop1 answerable, positions 0–99 of
seed 1343, unused before this run.

**Question.** Does Jev's price for the next step depend on the path so far? Jev reads hop 2 and prices the other 18
passages for hop 3 under three histories, carried as kappa's `found` (title plus first sentence):
- none;
- the true hop 1;
- a wrong earlier read: the non-chain passage nearest the question.

## Registered result

- **Primary, pull: −.056 [−.115, +.009] (n 78). H-M fails.** A wrong history doesn't raise the prices of options on its
  own thread, relative to options on neither thread. The point estimate is slightly the other way.
- The lure itself (`found` says it was read): Δlogit **−.177 [−.245, −.110]**. Jev discounts what it's told it has
  already read.
- Top-1 h3: none .85, true .84, wrong .85. true − none is −.010 [−.070, +.050], and wrong − none is .000 [−.050, +.050].
- Δlogit p(h3), true − none: **−.079 [−.156, −.007]**. The right history slightly *lowers* the answer's price.
- **Noise (stage 0).** None of the 4 repeat answers were identical, and the mean |Δlogit| per option between identical
  requests was .113. Jev's answers carry real repeat noise, about the size of the effects here, before averaging
  over options.

## Post-hoc (added after scoring, unregistered, $0 from the cache)

Mean Δlogit against `none`, by option class:

| history | neither | lure-linked | h2-linked | h3 (registered) |
|---|---|---|---|---|
| true | +.339 [+.292, +.386] | +.267 | +.271 | −.079 |
| wrong | +.310 [+.253, +.365] | +.270 | +.245 | — |

- **Any history raises every option's price by about .3 logit,** whether it's true or wrong, and on- or off-thread.
- The answer's price stays put or falls (−.079). So **history narrows the answer's lead over the field by about .4
  logit** without changing the top choice here (h3 was already first .85 of the time).
- So the effect is a general inflation of Jev's prices, not momentum along a thread. The thread classes move together.
  If anything the lure-linked class moves a little *less* (the negative pull), which fits Jev discounting what's
  already been covered.

## What it means

- **Intuition (1) isn't supported at one step on MuSiQue.** Jev's next-step prices don't carry the direction of the
  path. They carry a uniform shift, plus a discount on what it's told it has read. In circuit terms there's no
  inductance on the edge. History acts like lowering every resistance at once, plus raising the resistance back to
  where you came from.
- **Whether the +.3 shift is history at all is untested** (bill's review). Both `true` and `wrong` add a `found` field
  of about one sentence, so the shift could come from the request's shape or length: any extra context might make Jev
  more generous. A history effect should depend on content, and a format effect wouldn't. An irrelevant-`found`
  control (a sentence from another question's pool, one more request per question) separates them.
- **For kappa,** sending history doesn't steer Jev here. It compresses its margins. That's a candidate mechanism for
  kappa's mixed record (MuSiQue +, BEAM −): when the answer's margin is large, compression is harmless; when lures
  are close, compression could flip choices. **That's untested.** A test would look at questions where h3's margin
  under `none` is small.
- Momentum might still exist over longer histories, or in how the walker opens doors (D6 option texts list unread
  targets, bill's search). This test covers one earlier document and one step.

## Predictions against outcomes

- Pull about +.2: **wrong**, −.056. I expected entity overlap with `found` to raise on-thread prices. Jev seems to read
  `found` as covered ground.
- true − none top-1 +.03 to +.08: wrong, −.01. The answer was already first .85 of the time, so there was little room.
- wrong − none −.02 to −.05: about right (.000), within the CI.
- Repeat noise under .1: close (.113), and I'd flagged it as a guess.

## Postmortem

- **What went right.** bill's review caught a design bug: the lure was in its own pull class, and its −.18 discount
  would have dragged the primary's sign by itself. It was fixed before any spend. Stage 0 measured Jev's repeat noise
  instead of assuming it (the cache key alone would have hidden server caching), and I reported it before reading
  the primary.
- **What I got wrong.** The primary was a contrast between classes, so it couldn't see a shift common to all classes.
  The biggest effect in the data (+.3 everywhere) was only found post hoc. Next time, register the per-class levels
  next to the contrast, so a common-mode effect is a registered readout, not a discovery.
- **Scope.** One step, one earlier document, one wrong-history rule, MuSiQue 3-hop dev, 100 questions. The margin
  compression is post hoc and needs its own registration.
