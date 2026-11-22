# Design note: a structure-dependent kappa state. Feed back the reads that answer, not the reads that resemble

*22 Nov 2026, james. Split with bill: (b) a structure-dependent kappa state. This is a design, not a result. The look
below is $0 on recorded walks (seen data, unregistered).*

**What constrains the design.**
- At one step, a `found` history changes Jev's top choice only when it's the right content. On BEAM an oracle gold
  sentence raised top-1 gold by +.10 [+.009, +.193], while related non-gold and unrelated histories changed nothing
  (SR-MO3). On MuSiQue no history moved top-1 beyond noise (SR-MO2), and h3 is already first .92 of the time there.
- At walk level, K7 (opening sentences of all reads) helped MuSiQue (+.037–.046) and cost BEAM (−.022) (kappa round 5).
- **The $0 look, which explains why.** On BEAM, the reads a walk makes are almost all non-gold (`walks-1m.jsonl`, gold
  from `fixture-1M/items.jsonl`):

| reads | n | gold share |
|---|---|---|
| via search, arm P | 13,667 | .008 |
| via search, arm S | 1,678 | .045 |
| via a door, arm P | 6,333 | .030 |
| via a door, arm S | 3,652 | .031 |
| door reads, door's Jev p in [.4, .6) | 3,833 | .019 |
| door reads, door's Jev p in [.6, .8) | 5,354 | .037 |
| door reads, door's Jev p in [.8, 1.0] | 616 | .045 |

  A K7 state built from BEAM reads is about 95–99% non-gold, related sentences: exactly the history that SR-MO3 found
  doesn't help, and that narrows the average gold lead by about .1. Filtering by route (door against search) or by the
  door's Jev price barely changes the gold share (.019 → .045). On MuSiQue, by contrast, the reads that carry the chain
  are a large share of a short walk, so K7 is closer to the oracle history.

**The design: a state that keeps only reads that answer.**
- **K-ans.** After each wave, one extra Jev request over that wave's new reads, with the question and the task "Does this
  passage give information needed to answer `question`, or identify something the answer depends on?" (bill's
  wording, so a MuSiQue hop-1 passage that identifies the bridge isn't rejected).
- `found` keeps **the argmax read of each wave**, one per wave. That's knob-free (bill's review chose between the two
  rules first offered).
- That's one short request per wave, the size of the reads, not of the options.
- **Why it should help on both corpora.** It approximates the oracle arm (gold content) without gold. On BEAM it would
  drop the 95% related-non-gold reads, which SR-MO3 says are inert or mildly harmful. On MuSiQue it keeps the chain's
  passages, which K7 already mostly contains.
- **The "what not to reopen" alternative** (round 5's suggestion for many-piece questions) is weaker on this evidence.
  SR-MO showed Jev already discounts what `found` names (−.18). The problem on BEAM isn't reopening. It's that the state
  is mostly non-gold.

**What a first test would be** (to register, not yet).
1. **Step level ($0.05, a fresh BEAM or MuSiQue draw, SR-MO3's design):**
   - `found` = K7 of the walk's actual reads up to that wave, from recorded walks;
   - against `found` = K-ans (the same reads filtered by one Jev request);
   - against `none`.

   Primary: top-1 gold, K-ans − K7, against a `none2` floor.
2. **Only if (1) passes:** a walk-level replay on BEAM and MuSiQue HELD-OUT, with the kappa rounds' harness (K0, K7,
   K-ans). That's the real test of kappa's BEAM sign.

**Risks.**
- Jev's per-read relevance may be as noisy as its door prices: high-p doors still read gold only .045 of the time. Then
  K-ans keeps as little gold as K7 does, and (1) fails cheaply.
- **A partial $0 price** (bill's point 3). SR-MO3's cached passage p's are Jev's per-message relevance on BEAM. Under
  `none`, Jev's argmax is gold .495 of the time, among options whose gold base rate is .141 (109 questions). That's
  3.5× enrichment. But those are search-order pools. Walk reads run at about .03 gold, and at that base rate the same
  enrichment would give an argmax gold share of only about .1, unless Jev's precision holds up when gold is scarce.
  That's the number step (1) has to beat.
- On MuSiQue, filtering can drop a hop-1 passage that doesn't *look* answer-bearing, since bridges are relations, not
  answers. Step (1) on MuSiQue would show it.
