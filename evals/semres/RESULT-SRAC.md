# SR-AC result (22 Nov): a reader holding the answer passage doesn't need the rest of the chain

*bill. Registered in REGISTERED-SRAC.md (#99) before any Jev call; reviewed by james. Script `srac.py`, outputs
`out/srac-dry.txt`, `out/srac-stage0.txt`, `out/srac-fresh.txt`, `out/srac-fresh.json`. **Spend $0.030** (stage 0
$0.0012, the 150 $0.0287; cap $0.30).*

**Serves.** Sirsh's 17:07Z decision that the goal is the answer being in what the walk returns, checked properly, and
his question of how the chain and the answer can be separated.

## Results

150 fresh MuSiQue train questions (50 each of 2-hop, 3hop1 and 4hop1). AC = Jev, reading the set, chooses the
sentence that states the answer, and that sentence holds the gold answer.

| set | AC | string present | chance (random scores) |
|---|---|---|---|
| G: the whole gold chain | .867 | 1.000 | .16 |
| **L: the answer passage alone** | **.900** | 1.000 | .41 |
| LR: the answer passage + random passages, chain-sized | .827 | 1.000 | .15 |
| R: random passages, no hop | .033 | .073 | .02 |

- **Primary. AC(G) − AC(L): −.033 [−.073, +.007].** The rest of the chain adds nothing to a reader who has the answer
  passage. By type: 2-hop +.020 [−.040, +.100], 3hop1 −.080 [−.160, −.020], 4hop1 −.040 [−.120, +.040].
- **Extra passages mislead a little:** AC(LR) − AC(L) −.073 [−.120, −.027].
- **The measure's range is wide:** AC(G) − AC(R) +.833 [+.773, +.893]; AC(R) sits at the string floor.
- **A-last and AC agree** on 534 of 600 sets. Contained but not chosen (A-last 1, AC 0): 61 of 450 (14%). Chosen
  without the answer passage: 5.

## The 20 hand-read failures

9 distinct questions, read in session:
- **Measurement artifacts: 9 of 20.**
  - Splitter: 2. "(c. 1394 – 1460)" was split at "c.", which cut Prince Henry's name from the chosen sentence.
  - Normalisation: 3. "Thambidurai Karur…" doesn't contain "m thambidurai".
  - Gold label: 4. "the Carolingian family" against a Charlemagne sentence; an Iron Maiden label that is a DVD title.
- **Wrong choices: 11 of 20.** The reader picked a sentence about the right subject without the asked-for fact (Italy's
  surrender without its date; "Flatline" without its release date), or a misleading noise passage (Denmark's borders).

The artifacts fall equally on G and L (they're the same questions and passages), so they lower both levels and leave
the primary contrast alone. AC's levels are understated by roughly 4–5 points.

## What it means, for Sirsh

- **Chain and answer separate because the answer passage usually carries enough on its own.** A reader given the
  question and the passage that states the answer picks it 90% of the time. Adding the bridge passages doesn't help,
  and adding unrelated passages hurts a little. The Ruth Ellis case is real but uncommon: about 14% of sets that
  contain the answer passage, about half of them artifacts.
- **So the measure is A-last: does the returned set contain the passage that states the answer.** It is labelled, $0,
  and agrees with the reader's choice on 89% of sets. AC stays as a secondary that catches "contained but not usable".
- **For the walks, this confirms james's flip.** On A-last, Jev's full step beats the cheap walk (it reaches the answer
  passage more often by skipping ahead), and skipping costs the reader almost nothing. The step, stop and reward work
  should now aim at reaching the answer passage, and at returning as little else as possible.

## Predictions against outcomes

- AC(G) about .85: **.867** ✓
- AC(L) about .70: **.900** ✗
- AC(G) − AC(L) about +.15, positive at every hop count: **−.033** ✗. The registered consequence applies: the chain
  doesn't matter to a reader on MuSiQue, and A-last is the measure.
- AC(LR) − AC(L) about −.03: **−.073** ✓ (larger)
- AC(R) about .05: **.033** ✓
- Contained but not chosen in 15–25%: **14%** ✗ (just under)

## Postmortem

- **What went right.** The validation ran before AC scored any walk, and its primary was the question Sirsh asked. A
  $0 ceiling check moved the options from graph keys (41–52% coverage) to sentences (100%) before any spend. Stage 0
  showed a real Ruth Ellis case and a title-prefix false positive, both read before the 150. The hand reads separated
  artifacts from reader errors.
- **What I got wrong.** I built a whole case on one vivid example (Ruth Ellis) and predicted the chain was worth +.15.
  I didn't check how often a reader actually needs the bridge. Jev, like any LLM reader, can often place the answer
  without being told the link, because the question names enough. The splitter's abbreviation case ("c.") was
  foreseeable.
- **Mechanism.** The question supplies the constraint the bridge would supply ("last person hanged" + a passage
  saying "last person executed in Northern Ireland"). The reader matches question to answer sentence directly, and
  extra passages only add rival sentences.
- **Not tested.** A reader other than Jev. Questions where the answer passage is ambiguous without the chain by
  construction. A corpus less redundant than MuSiQue.
- **Scope.** MuSiQue train, fixed gold-derived sets, one reader. Not walks. Production is Sirsh's.
