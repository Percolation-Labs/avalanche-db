# SR-MO2 (registered 22 Nov, before any Jev call): is kappa's +.3 shift history or format, and does it flip choices?

*james. Follows SR-MO (#76), on Sirsh's 11:34Z "own judgement". Script `srmo2.py`. The Jev cap is $0.25.*

**Serves.** Kappa (`found`, K6) is on by default in the product's walk. SR-MO found that any `found`, true or wrong,
raised every option's price by about +.3 logit, while the answer's price stayed flat. bill's review asked whether that's
history (content) or format (the request just carries more context). SR-MI's common mode was about zero when only `read`
changed. If it's format, kappa's effect at a step is mostly a margin compression unrelated to what was read. That bears
on kappa's mixed record (MuSiQue +, BEAM −) and on whether `found` should carry history at all.

**Task (as SR-MO).** MuSiQue dev 3hop1 answerable, seed 1343's permutation. Jev reads h2 and prices the other 18
pool passages with SR-J's passage task, unchanged.

**Histories,** carried as `found`, K6 form (title plus first sentence):
- `none`
- `true`: K6(h1).
- `wrong`: K6(lure), where the lure is the non-chain pool passage nearest the question (SR-MO's rule).
- **`irrelevant`**: K6 of the hop-1 passage of the *next question in the draw's order*. It's a real, well-formed hop-1
  sentence about something else, with the same form and similar length. It's knob-free.

All requests go out in one `ask_many` wave.

**Data.** Positions **104–303** (200 questions) are registered. SR-MO used 0–99 (scored) and 100–103 (stage 0). Stage 0
is 304–307, with the `none` request repeated to re-measure repeat noise.

**Measures** (logit p, clipped to [1e-4, 1 − 1e-4]):
- **shift(h):** per question, the mean Δlogit (h − none) over **neither** options. These share no door key with h2, the
  lure or the irrelevant passage, and exclude h3 and the lure. This is the common mode.
- **top-1 h3** per history, and **flips** against `none`: lost (h3 first under none, not under h) and gained.

**Primary.** shift(irrelevant), bootstrap 95% CI over questions. **H-F (format) passes if the lower bound is above 0.**
An irrelevant `found` inflates prices too, so the shift doesn't need related history.

**Secondary (CIs).**
- shift(true) and shift(wrong): replicate SR-MO's +.34 and +.31.
- shift(true) − shift(irrelevant) and shift(wrong) − shift(irrelevant): is there a content-specific part beyond format?
- top-1 h3 for true − none, wrong − none and irrelevant − none, with the flip counts. Does any `found` change choices,
  and is losing more common than gaining?

**Predictions.**
- shift(irrelevant) is about +.25 and H-F passes: mostly format.
- shift(true) − shift(irrelevant) is about +.05, with a CI that may include 0.
- Flips are rare (under 5% each way), with lost about equal to gained. SR-MO's top-1 didn't move (.85 against .84).
- Repeat noise is about .11 (SR-MO stage 0: .113).

**What a result would mean for kappa.**
- If format, the +.3 is a property of request shape. A no-op `found` would reproduce it, so kappa's walk-level effects
  come from elsewhere: the discount on read items (−.18 in SR-MO), and what the walk then opens.
- If content, history does shift Jev, but uniformly, not along the thread. SR-MO's pull was null either way.

**Spend.** Stage 0: 4 questions × 5 requests, about $0.002. The wave: 800 requests, about $0.10 (SR-MO's rate). Cap
$0.25.

**Scope.** One step, one history length, MuSiQue 3hop1 dev. The irrelevant history is one rule (next question's hop 1).
A length-matched filler (not a sentence) isn't tested.
