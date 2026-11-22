# SR-BS (registered 22 Nov, before any Jev call): can the walk stop on its own, with no threshold?

*bill, with james (script `srbs.py`, built from srbh.py). Design DESIGN-STOP-RULE.md (#96), reviewed by james 16:52Z.
Cap $0.50. Serves Sirsh's 23:03Z ask, the cheap pipeline in a full walk: SR-BH's walks were told their hop count.*

**Data.** MuSiQue train answerable chains from `train-corpus.jsonl` and `graph-train-pc.jsonl`: 2-hop, 3hop1 and
4hop1, 80 of each (240), drawn with SEED 1345 as a permutation within each type; 'fresh' is the first 80 of each, stage
0 is positions 80–81 of each. Questions used by SR-BX (seed 1341), SR-BE (1341, 304–603) and SR-BH (1344, first 100
plus 100–101) are removed before the draw.

**Walks.** As SR-BH: Jev's entry request, then steps from the last read, every read passage excluded from the options.
Step rules: **cheap** (nt_rescue) and **pass** (PASS_TASK over all unread). The only bound on reads is the pool (20).

**Stop rules** (argmax over options that include stopping; no threshold).
- **S-in:** one option added to the step request the walk already makes (the name request for cheap, the pass request
  for pass): "Nothing more: what has been read already answers `question`." Stop when it wins. For the cheap walk,
  if the name request's argmax is the stop option, the walk stops before any rescue.
- **S-check:** after each step, a two-option request whose context holds the question and **the full text of every
  passage read**: "`question` can be answered from these passages" against "`question` needs a passage not yet read".
  Stop on the argmax.
- **oracle(H)** and **oracle(H+1)**: SR-BH's and SR-BH2's fixed lengths, as references.

**Primary. All hops, cheap × S-check − cheap × oracle(H), paired bootstrap 95% CI over the 240, with input characters
per question beside it. H-S (non-inferiority): the lower bound is above −.05**, the margin carried from SR-BH.

**Secondary.**
- The same contrast for cheap × S-in, and for pass × S-check and pass × S-in.
- Reads used against H: stopped early, exact, late, with all-hops within each.
- All hops per 10k input characters for every arm.
- By hop type (2, 3, 4).
- **S-check's confusion table:** at each stop, did the read set contain every hop?
- **Sanity checks (james):** how often S-in wins at the first step after the entry, and how often S-check stops
  after one read. Every chain needs 2+ reads, so both are always wrong there. They are readouts, not rules.

**Predictions.**
- S-in stops too early: all-hops well below oracle(H), and its stop option wins on more than a few step-1 requests.
- S-check is near oracle(H) and stops late more often than early. H-S is about a coin flip. Input about 1.5× the
  oracle walk's.
- S-check × cheap scores at or above oracle(H) on all-hops but below it per character.
- S-check stops after one read in under 10% of questions.

**What follows.** If H-S passes, the walk no longer needs H, and the full walk Sirsh asked for exists as cheap step +
S-check, reported to him as a hypothesis. If S-check stops early, its confusion table says whether it misjudges
completeness or misreads the question. Production is Sirsh's.

**Spend.** A dry run with random scores prices it before stage 0 (S-check's full-passage context grows with reads).
If the estimate exceeds the cap, the draw shrinks evenly across types; the rules don't change. Cap $0.50.

**Scope.** MuSiQue train chains, one draw of 240, H hidden from the walk but used to score.

**Amendment 1 (16:56Z, before stage 0; james's implementation, reviewed by bill).**
- **One trajectory per step rule.** Each walk runs once with the stop option appended to its step request; the step
  is the argmax over the real options only, so stopping never changes a step. Each stop rule (S-in, S-check, H, H+1)
  cuts that trajectory, keeping the arms paired. The trajectory ends once every stop rule has fired. The oracle arms'
  requests carry one extra option, so oracle(H) is reported beside SR-BH's .395 / .315 as a check.
- **S-check's task line:** "Which statement is true of the passages in `reads`?", with the two registered options.
- **Cheap walk with no door keys on the last read:** there's no name request, so the stop option rides on the rescue
  pass request, the request the walk actually makes.
- **Draw:** the random-score dry run priced 80 per type at $0.56, over the cap, so the draw shrinks evenly to **70 per
  type (210)**, estimate $0.49, rules unchanged, as registered. It isn't re-grown after stage 0.
