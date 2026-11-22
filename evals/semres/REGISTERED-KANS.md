# K-ans (registered 22 Nov, before any Jev call): does a kappa state of the reads that answer fix BEAM's loss?

*james. Design in `NOTE-KAPPA-STATE.md` (#88, reviewed by bill). This is kappa round 7. The script is
`meta/lab/worlds/kappa_ans.py` in p8-subsystems (branch `james/kappa-ans`). It runs in bill's round-4/5 harnesses
unchanged. The Jev cap is $0.40.*

**Serves.** Kappa's sentence state (K7) helped MuSiQue walks (+.037 to +.046) and cost BEAM walks
(−.022 [−.040, −.001], round 5). The $0 look in #88 found that BEAM walk reads are 95–99% non-gold, whatever their
route or door price. SR-MO3 found that only gold content as `found` improves Jev's choice. So K7 on BEAM is a state of
related non-gold sentences, which doesn't help. K-ans keeps only the reads Jev judges to answer.

**The state.**
- For each walk round, the reads added since the same question's previous round form one wave.
- One Jev request per wave asks "Does this passage give information needed to answer `question`, or identify something
  the answer depends on?" (bill's wording) over that wave's reads. Its **argmax** read is kept.
- **K-ans** at a page is `kappa_state.relations` over the kept reads of every wave before the page, with the same
  per-sentence cap (200), total cap (6,000) and order arguments as that corpus's K7:
  - BEAM: most recent first, no door-first;
  - MuSiQue: id order, no door-first.
- It's knob-free: argmax per wave, and every other setting is K7's.

**Harness.** These are the round-5 (BEAM HELD-OUT, 601 pages) and round-4 (MuSiQue HELD-OUT, 286 pages) replays, with
D6 doors, prompt P1 and presentation F2, unchanged. K0 and K7 are re-keyed exactly as there. A dry run confirmed every
K0 and K7 request is already cached (0 of 601 and 0 of 286 uncached), so only K-ans is new.

**Primary.** BEAM HELD-OUT NDCG@10, paired by question, **K-ans − K7**, using the harness's bootstrap. **H-K passes if
the lower bound is above 0.**

**Secondary (CIs from the same bootstrap).**
- BEAM: K-ans − K0. Does K-ans turn BEAM's loss into a gain?
- MuSiQue: K-ans − K7 (does filtering keep MuSiQue's gain?) and K-ans − K0.
- BEAM gold share of the kept reads against all wave reads: does the filter enrich gold? The #88 price was about .10
  if Jev's 3.5× enrichment holds at walk base rates.

**Predictions.**
- BEAM: K-ans − K7 is about +.02, with a CI touching 0, so H-K is a coin flip. K-ans − K0 is about 0. That would recover
  K7's loss, not add a gain.
- Kept-read gold share on BEAM is about .10, against about .03 for all reads.
- MuSiQue: K-ans − K7 is about −.01 to +.01. Filtering may drop hop-1 passages, and the wording was chosen to limit
  that. K-ans − K0 is about +.03.

**Procedure.**
1. bill reviews this registration.
2. Stage 0 is the first 4 questions of each corpus (`--stage0`) and costs under $0.01. It isn't scored as a result.
3. One run per corpus, under one $0.40 cap in total.
4. The result and a postmortem follow.

**Spend.**
- REL requests: 83 BEAM waves (565k characters) and 77 MuSiQue waves (2.0M characters), about $0.03.
- Door requests: 601 + 286 for K-ans only, about $0.12 at round 5's rate.
- Total about $0.15.

**Scope.**
- These are replayed pages (fixed reads), not live walks: K-ans changes the state, not which reads the walk made.
- HELD-OUT only. One wording, one keep rule.
- Round 5's pages are seen for K0 and K7, but K-ans is new on them.
