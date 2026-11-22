# SR-MO2: kappa's +.3 shift is content, not format. Any question-related history inflates every price, and an unrelated one doesn't

*22 Nov 2026, james. Registered in `REGISTERED-SRMO2.md` (#81, with amendment 1 from bill's review, before any Jev
call). Jev spend: $0.0028 for stage 0 and $0.1239 for the wave (1,000 requests, one `ask_many`, cap $0.25). Outputs:
`out/srmo2-stage0.txt`, `out/srmo2-fresh.txt`, `out/srmo2-fresh.json`.*

**Versions.** percolate-core 0.2.15 (Jev), bge-small-en-v1.5, graph-mq. MuSiQue dev 3hop1 answerable, positions
104–303 of seed 1343 (200 questions), unused before.

**Question.** SR-MO found that any `found` raised every option's Jev price by about +.3 logit. Is that history
(content) or format (extra context in the request)? The new history is `irrelevant`: the hop-1 sentence of the next
question in the draw. It has the same form and length, and it's about something else.

## Registered result

| shift over neither options (Δlogit against none) | |
|---|---|
| **irrelevant (primary)** | **+.013 [−.009, +.036]** |
| true | +.297 [+.267, +.327] |
| wrong (the lure) | +.286 [+.245, +.327] |
| true − irrelevant | +.284 [+.251, +.316] |
| wrong − irrelevant | +.272 [+.235, +.311] |

- **H-F (format) fails.** A same-shaped `found` about something else doesn't move prices. The +.3 needs content
  related to the question.
- **SR-MO replicates** on fresh questions: true +.297 against SR-MO's +.339, wrong +.286 against +.310.
- **Truth doesn't matter, relatedness does.** The lure is a wrong read, but it's the passage nearest the question, and it
  inflates prices as much as the true hop 1 (+.286 against +.297).

**Choices** (top-1 h3; flips against `none`, with the identical repeat `none2` as the noise floor):

| history | top-1 h3 | lost | gained | top-1 − none |
|---|---|---|---|---|
| none | .920 | | | |
| none2 (identical repeat) | .915 | 4 | 3 | −.005 [−.030, +.020] |
| true | .905 | 8 | 5 | −.015 [−.050, +.020] |
| wrong | .910 | 7 | 5 | −.010 [−.045, +.025] |
| irrelevant | .900 | 6 | 2 | −.020 [−.050, +.005] |

- **No history changes the top choice beyond noise.** Every history loses a little more often than it gains (6–8
  against 2–5). The identical repeat flips 7 of 200 on its own, so these counts are only about twice the floor, and
  every CI includes 0.
- Repeat noise in stage 0 was .057 per option (SR-MO: .113). Both are small samples, so call it about .06–.11.

**Predictions against outcomes.**
- shift(irrelevant) about +.25, H-F passes: **wrong**, +.013. I expected format.
- true − irrelevant about +.05: wrong, +.284. Nearly all of the shift is content.
- Flips under 5% each way, lost about equal to gained: right on size (lost 3–4%, gained 1–2.5%); losses lean a little
  more often.
- Repeat noise about .11: .057.

## What it means for kappa and semantic inductance

- **Kappa's step-level effect is relatedness inflation.** When `found` holds something related to the question, true or
  not, Jev rates every unread option as more likely to help, by about .3 logit. Unrelated history does nothing. Together
  with SR-MO:
  - there's no pull along the thread;
  - there's a discount on the item `found` names (−.18);
  - the answer's own price stays flat, so its lead narrows.
- **That's not momentum; it reads more like conductance going up everywhere.** "We're on topic" lowers every resistance
  at once. In inductance terms, history raises the walker's general willingness to step, with no preferred direction.
- **The choice consequence is small at one step on MuSiQue.** Top-1 doesn't move beyond the noise floor. Where kappa
  matters at the walk level (MuSiQue +, BEAM −, from the kappa rounds), it's more likely through the discount
  (not reopening what's read) or through margins on harder pools than here (h3 is first .92 of the time). The BEAM sign
  is untested here.
- **For "define good":** a decider's prices shift with related context, so a graph measure priced from Jev's p should
  fix the context (with or without `found`) or it'll compare prices on different scales.

## Postmortem

- **What went right.** Stage 0 showed the irrelevant shift going the other way (mean −.15 against true's +.20) before
  the wave, which hinted the prediction was wrong. The design didn't depend on the direction, so the wave went ahead as
  registered. bill's noise-floor amendment was decisive for reading the flips: without `none2`, 8 losses would have
  looked like a kappa effect.
- **What I got wrong.** I predicted format, because SR-MI's near-zero common mode (when only `read` changed) seemed to
  point there. But SR-MI changed *which* question-related passage was read, keeping relatedness constant. This test
  removed relatedness. I read a non-contrast as evidence for format. The lesson: a null contrast only speaks to the
  factor it varied.
- **Scope.** One step, one history length, MuSiQue 3hop1 dev, 200 questions. Irrelevant is one rule (the next
  question's hop 1). How relatedness scales (partial relatedness, longer `found`) is untested.
