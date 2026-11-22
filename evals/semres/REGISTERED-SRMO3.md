# SR-MO3 (registered 22 Nov, before any Jev call): does related history narrow the gold's lead on BEAM, at one step?

*james. Follows SR-MO and SR-MO2 (#76, #81), on Sirsh's 11:34Z "own judgement" and bill's 11:46Z split. Script
`srmo3.py`. The Jev cap is $0.25.*

**Serves.** Kappa (`found`) is on by default in the product's walk. The kappa rounds (p8-subsystems
`meta/lab/results/kappa`) measured it at walk level: MuSiQue +.037–.046, BEAM **−.022 [−.040, −.001]** (K7, round
5). On BEAM, Jev's score change correlated +.118 with a door's overlap with the reads, and its top door led to gold less
often (.493 → .444). The MuSiQue gain's mechanism stayed open after three null checks.

At one step on MuSiQue, SR-MO and SR-MO2 found two things:
- question-related history inflates every option by about +.3 logit, while unrelated history does nothing;
- the answer's own price stays flat, so its lead narrows (h3 −.08 against non-gold +.34).

The inflation was uniform, with no pull toward the found item's thread (−.056). On BEAM, nearly every option resembles
the reads: one conversation, one topic. This asks whether the same history narrows gold's lead more there, as a
step-level account of BEAM's loss.

**Data.** The BEAM 1M fixture (`~/.cache/walklab/fixture-1M`, 288 questions, all conversations). This is a step test
on a recorded search order, not the kappa rounds' walk test, so both halves are used. A question is usable when:
- search order holds at least two gold messages;
- the next 19 after the first hold a gold other than the true-history message;
- they also hold at least one non-gold.

That's 113. In file order, **stage 0 is the first 4 usable questions and the registered set is the other 109.**

**Design (per question).** Read is the first gold message in search order. The options are the next 19 messages in
search order. Jev prices them with SR-J's passage task, unchanged, under these histories (`found`, K6 = the message's
first sentence):
- `none`, plus an identical repeat, `none2` (the noise floor);
- `true`: K6 of the second gold message in search order, a right but partial history (bill's review). With `related`,
  it separates resemblance from relevance, as true and wrong did on MuSiQue;
- `related`: K6 of search's top non-gold message other than the read, the question-nearest lure in search's terms;
- `irrelevant`: K6 of the read message of the next usable question from a different conversation.

That's 5 requests per question, all in one `ask_many` wave. The related and true messages themselves, if they're
options, are excluded from every measure (`self`).

**Primary: lead(related).** Per question, the mean Δlogit (related − none) over unread gold options minus the same over
non-gold options. Bootstrap 95% CI over questions. **H-B passes if the upper bound is below 0:** related history
narrows the gold's lead on BEAM.

**Secondary (CIs).**
- lead(true), and lead(related) − lead(true): does a wrong but resembling history narrow the lead more than a right
  one?
- lead(irrelevant): an unrelated control.
- shift(related) and shift(irrelevant) over non-gold options: SR-MO2's content effect on BEAM.
- rho(related) and rho(true): per question, the Spearman correlation over options between word overlap with the found sentence and Δlogit.
  That's round 5's statistic at one step. Positive means a resemblance pull.
- Top-1 gold under each history, with lost and gained flips against `none` and `none2` as the floor.

**Predictions.**
- lead(related) about −.3, H-B passes. On MuSiQue it was about −.4 for the single answer, but BEAM has several golds,
  some resembling the read too, which dilutes it.
- shift(related) about +.3 (SR-MO2), and shift(irrelevant) about 0.
- rho(related) is positive, about +.1 (round 5's +.118). On MuSiQue the analogous pull was null.
- Top-1 gold falls under `related` by .02–.05, beyond the `none2` floor.

**What a result would mean.**
- If H-B passes with a positive rho, kappa's BEAM loss has a step-level mechanism: related history raises the
  resembling non-gold more than the gold. That argues for a structure-dependent kappa (round 5's own conclusion), now
  with a measured cause.
- If H-B fails, the BEAM loss comes from the walk (what gets opened next), not the step's prices.

**Spend.** Stage 0: 4 × 5 requests, under $0.002. The wave: 545 requests of short messages, about $0.03. Cap $0.25.

**Scope.** One step, one history length, BEAM 1M (both halves), a recorded search order rather than a walk, and 109 questions.
The question types are mixed: contradiction, update, temporal, ordering and multi-session.

## Amendment 1 (bill's review, before any Jev call)

- A question is usable only if its options hold a **non-gold message other than the related one**. Otherwise, with the
  related message excluded as self, the non-gold mean is empty and the primary is NaN. The usable count and the
  registered set size are recomputed under this rule and reported in the output (stage 0 is still the first 4 usable).
