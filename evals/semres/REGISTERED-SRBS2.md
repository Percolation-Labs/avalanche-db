# SR-BS2 (draft for bill's review; no Jev call yet): does asking whether the passages *state* the answer stop the walk at the answer passage?

*james. Follows NOTE-STOP-ALAST.md (#101). Script `srbs2.py`, built from srbs.py. Cap $0.30. Serves Sirsh's 17:07Z
goal: the answer in what the walk returns, with fewer passages better for the reader (SR-AC).*

**Question.** Re-read on A-last, SR-BS's check ("`question` can be answered from these passages") stopped the walk at
the very read where the answer passage arrived in 116 of 180 questions, and before it in 42. The early stops look like
Jev answering from its own knowledge. Does a wording that asks whether the passages *state* the answer stop early
less?

**Data.** A fresh draw: SEED 1346, 60 each of 2-hop, 3hop1 and 4hop1 train answerable chains. Questions used by SR-BX,
SR-BE, SR-BH and SR-BS are removed first (asserted in the script). Stage 0 is positions 80–81 per type.

**Walk.** Jev's entry request, then **the pass step** (PASS_TASK over all unread from the last read). It's the better
step on A-last at equal reads (SR-BU2). The hop count is used only to score.

**Stop rules.** Each is a two-option request after every read, over the full text of every read passage. Stop on the
argmax.
- **S-check:** SR-BS's wording, unchanged.
- **S-state:** "these passages state the answer to `question`" against "`question` needs a passage not yet read".
- References: oracle H and oracle H + 1.
- A trajectory ends once both checks have fired and H + 1 reads are in, or the pool (20) is empty.

**Primary. A-last, S-state − S-check, paired bootstrap 95% CI, with returned-set size and input beside it.**
- **H-B2:** the lower bound is above 0.

**Secondary.**
- S-state − oracle(H), and S-check − oracle(H).
- For each check: stop against the first arrival at the answer passage (before, at, after, never). Its decisions
  against "the answer passage has been read". Stops after one read.
- By hop type.
- A hand read in session of 10 S-state early stops, to tell its own misses (A-last's lower bound: an off-chain passage
  states the answer) from real early stops.

**Predictions.**
- S-state stops early less often (about 25 against about 42), and late a little more often.
- A-last S-state − S-check is about +.05, so H-B2 passes about two times in three.
- S-state is within about .03 of oracle(H), with fewer passages returned.

**Spend.** The dry run (`out/srbs2-dry.txt`, random scores) estimates $0.11. Stage 0 first. Cap $0.30.

**Scope.** MuSiQue train chains, one draw of 180, the pass step, H hidden from the walk.
