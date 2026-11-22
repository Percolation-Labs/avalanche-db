# SR-AC (registered 22 Nov, before any Jev call): validating AC, a reader's-choice measure of "the answer is in what the walk returns"

*bill. Design DESIGN-ANSWER-MEASURE.md (#99), reviewed by james 17:10Z. Script `srac.py`. Cap $0.30. Serves Sirsh's
17:07Z decision: the goal is that the answer is contained in what the walk returns, checked properly.*

**Measure.** AC: Jev reads the question and the full text of every returned passage, and chooses, among every
sentence of those passages, the one that states the answer. AC = 1 if the chosen sentence holds the gold answer or an
alias after normalisation. A-last (james, #98) is its gold-side upper bound: the set holds the last-hop passage.
AC = 0 with A-last = 1 is "contained but not usable".

**james's four notes, fixed here.**
1. **Sentence splitter:** a boundary is end punctuation (. ! ?), whitespace, then a capital, digit, quote or bracket.
   **Every option is prefixed with its passage's title** ("Title: sentence"), so an answer carried only by a title is
   scorable, and each passage's text is title-prefixed in `reads`.
2. **Option order:** passage order within the set, then sentence order. Argmax ties go to the earlier option.
3. **Normalisation:** lower case, alphanumeric tokens joined by spaces, so '3,000' becomes '3 000' on both sides and
   'in 1958' contains '1958'. From 20 hand-read failures, I report how many chosen sentences hold the answer in a form
   this misses.
4. The primary below leads the result.

**Data.** MuSiQue train answerable 2-hop, 3hop1 and 4hop1, 50 of each (150), SEED 1346, excluding every question SR-BX,
SR-BE, SR-BH and SR-BS used. Stage 0 is positions 50–51 of each type.

**Fixed sets per question.**
- **G:** every hop passage, in hop order.
- **L:** the last-hop passage alone.
- **LR:** L plus random non-hop passages from the question's pool, to the chain's size.
- **R:** random non-hop passages, the chain's size (the floor).
Random picks are seeded by sha256(question id + set name).

**Primary. AC(G) − AC(L), paired bootstrap 95% CI**: what the rest of the chain is worth to a reader who already has
the answer passage. This is the plain-terms number for Sirsh's "how can chain and answer be separated?".

**Secondary.**
- AC per set and type; string presence per set.
- AC(LR) − AC(L): do non-bridge passages mislead a reader holding the answer?
- **AC(G) − AC(R): the measure's range.** AC is usable as the walk's measure only if this lower bound is well above 0
  and AC(R) is near the string-presence floor.
- A-last × AC agreement over all sets.
- 20 AC failures read by hand in session (not a batch call): wrong sentence chosen, right sentence with the answer in
  a form norm() misses, or a gold-label problem.

**Chance level** (the dry run's random scores, `out/srac-dry.txt`): AC G .16, L .41, LR .15, R .02. A set with fewer
sentences makes a random choice likelier to hit, so L's chance level is the highest.

**Predictions.**
- AC(G) about .85; AC(L) about .70; **AC(G) − AC(L) about +.15**, positive at every hop count, largest on 4hop1.
- AC(LR) − AC(L) slightly negative (−.03): rivals mislead a little.
- AC(R) about .05, at the string floor (.07 in the dry run).
- A-last = 1 with AC = 0 in 15–25% of A-last sets.

**What follows.** If AC's range is wide and the hand reads hold, AC becomes the primary for SR-BU (james) and the
bridge reward (mine), with A-last beside it. If AC(G) − AC(L) is near 0, the chain doesn't matter to a reader on
MuSiQue, A-last alone is the measure, and Sirsh is told so.

**Spend.** The dry run estimates $0.026 for 600 requests. Stage 0 (6 questions) first. Cap $0.30.

**Scope.** MuSiQue train, fixed gold-derived sets, one reader (Jev). Not walks.
