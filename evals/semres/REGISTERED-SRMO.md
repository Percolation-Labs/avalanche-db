# SR-MO (registered 22 Nov, before any Jev call): walk momentum. Does Jev's next-step price depend on the path so far?

*james. Sirsh's 10:35Z note on semantic inductance, intuition (1): once a walker follows a thread, changing direction
costs extra, so a step's price depends on the path so far. bill searched the recorded walks (read-only agent): none
prices the same option under two histories, so this needs a small paired test. Script `srmo.py`. The Jev cap is $0.25.*

**Serves.** If prices carry momentum, the walk's resistance isn't a fixed property of an edge. It depends on the
current's history, which is what inductance would add to the resistor model (SR-TW, SR-J). The product already sends
history to Jev as kappa (`found`, K6: one opening sentence per document read). The kappa rounds measured its effect
on whole walks (MuSiQue +, BEAM −; cornerstone RESULT). This isolates it at one step, with the history controlled.

**Data.** MuSiQue dev 3hop1 answerable (a chain h1 → h2 → h3; 568 questions, none used by semres before). A seeded
draw (seed 1343): **positions 0–99 registered**, stage 0 at 100–103. The graph is graph-mq.

**Design (paired, per question).** Jev reads h2 and prices the other 18 passages (the pool minus h1 and h2) with
SR-J's passage task, unchanged, under three histories:
- `none`: {question, read: h2, task}.
- `true`: plus `found`: [K6(h1)], where K6 is the title plus the first sentence, as the walker's kappa.
- `wrong`: plus `found`: [K6(lure)]. The lure is the pool passage outside the gold chain with the highest bge cosine to
  the question: the one a cosine walker would most likely have read instead. It's knob-free.

All 300 requests go out in one `ask_many` wave.

**Option classes,** from door keys (2 ≤ df ≤ 100, not inside the question):
- **lure-linked**: shares a key with the lure but not with h2.
- **neither**: shares no key with the lure or h2.
- **h2-linked**: the rest.

**Primary: pull.** Per question, the mean Δlogit p (wrong − none) over lure-linked options, minus the same over
neither options. Questions without both classes are dropped, with their count reported. The 95% bootstrap CI is over
questions. **H-M passes if the lower bound is above 0.** A wrong history raises the prices of options on its own
thread, beyond any general shift. That's momentum: the old current induces flow along its path. The neither class
controls for history making Jev more or less generous overall.

**Secondary (CIs).**
- Top-1 h3, `true − none`: does the right history help the step? Kappa's MuSiQue sign predicts +.
- Top-1 h3, `wrong − none`: does a wrong history cost the step?
- Δlogit p(h3), `true − none`.

**Noise floor (stage 0).** The `none` request is sent twice in stage 0's wave, so the mean |Δlogit| between identical
requests is Jev's own repeat spread. If it's comparable to the effects, I'll say so before reading the primary.

**Predictions.**
- Pull is positive and small, about +.2 logit. Jev reads `found` as context, and options sharing the lure's entities
  look more relevant.
- `true − none` top-1 is +.03 to +.08.
- `wrong − none` is −.02 to −.05.
- Repeat noise is under .1 logit. That is a guess: I have no earlier measurement of it.

**Spend.** Stage 0: 4 questions × 4 requests, about $0.001. The wave: 300 requests, about $0.03. Cap $0.25.

**Scope.** One step (hop 2 → hop 3), one history length (one earlier document), and one wrong-history rule.
MuSiQue only. A positive pull shows that Jev's prices depend on history at one step. It does not show that a walk
without kappa would be worse, which the kappa rounds measured separately.

## Amendment 1 (bill's review, before any Jev call)

- **The lure is its own class (`self`), excluded from pull.** Under `wrong`, `found` says the lure was already read, so
  its own price moves for a reason that isn't momentum. Its Δlogit (wrong − none) is reported separately: does Jev
  discount what `found` says it has read?
- **h3 is its own class too**, excluded from both pull classes. Its price moves with the chain, and the secondaries
  report it.
- **The noise floor may read 0** if Jev's server answers identical requests from a cache. The replicate index changes
  only the local cache key. Stage 0 reports how many repeat answers are byte-identical. If all are, a 0 spread means
  server-side caching, not zero noise.
