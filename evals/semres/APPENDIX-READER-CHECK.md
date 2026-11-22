# Appendix: the reader check, a measure of "the answer is in what the walk returns"

*bill, 22 Nov 2026. Appendix to WRITEUP-WALK.md. Sources: DESIGN-ANSWER-MEASURE.md, RESULT-SRAC.md, NOTE-AC-JUDGE.md,
NOTE-AC-SPLIT.md, with the scripts and outputs they name. Total spend for this line of work $0.049 (Jev).*

**Tested on.** MuSiQue train, 150 fresh questions (50 each of 2-, 3- and 4-hop), percolate-core 0.2.15 (Jev).

## Why a string match isn't enough

Sirsh set the goal on 22 Nov: the answer is in what the walk returns, checked properly rather than by string match.
One walk shows why. For *"Who was the last person hanged in the country where Hill of Thieves' singer comes
from?"*, the walk returned the passage about the song, the passage about Robert McGladdery ("last person executed in
Northern Ireland"), and the passage about Ruth Ellis ("last woman hanged in the United Kingdom"). It didn't return the
passage saying where the singer is from. The answer string is in the set, and so is a rival answer. A string match
calls that a success. Whether it is one depends on which of the two a reader picks.

## The two measures

- **Answer passage present** (*A-last*): the returned set holds the passage that states the answer (the chain's last
  passage, which contains the answer in every question checked). It costs nothing and needs only the labels.
- **Reader's choice** (*AC*, "answer chosen"): Jev gets the question and the full text of the returned passages. Its
  options are every sentence of those passages, each prefixed with its passage's title. It picks the sentence that
  states the answer. AC = 1 if that sentence is right.

Sentences are the options because they cover every answer. The graph's door keys hold the answer for only 41–52% of
answer passages (dates, numbers and many names aren't keys); the answer passage's sentences hold it every time. Jev
chooses among sentences that exist and writes nothing.

## How "right" is judged

Three versions were tried, each fixing a failure found by reading cases by hand:

1. **String:** the chosen sentence contains the gold answer or an alias, after lower-casing and stripping punctuation.
   A hand read of 20 failures found 9 were measurement errors, not reader errors: a name written another way
   ("Thambidurai" for "M. Thambidurai"), a gold label that names something else, and sentences cut in the wrong place.
2. **String or judge:** when the string check fails, a second, two-option Jev request asks whether the sentence states
   the answer "possibly in other words". It accepted the name-form cases and rejected all 11 genuine wrong choices.
3. **A standard sentence splitter** (pysbd) instead of a regular expression. The regex split "(c. 1394 – 1460)" at
   "c.", cutting Prince Henry's name off the sentence the reader chose. pysbd fixes abbreviations and initials.

**Strict and lenient.** james then asked for the judge to see string hits too, not only misses. It rejected some:

| set | string hits the judge rejects |
|---|---|
| the whole gold chain | 9 of 134 |
| the answer passage alone | 14 of 138 |
| the answer passage + random passages | 6 of 125 |
| random passages only | 4 of 5 |

On random sets these are real accidents: a sentence about a mountain pass that mentions "the Himalaya". On gold sets
they're mixed: some accidents, and some cases where the judge is too strict on a sentence that does state the answer.

**So the reader check is reported as a range**: *lenient* (string or judge) and *strict* (judge only), with the count of
string hits the judge rejects. A decision that comes out differently at the two ends isn't settled.

## What it found

| returned set | AC, first version | AC, pysbd + lenient | answer string present |
|---|---|---|---|
| the whole gold chain | .867 | .927 | 1.000 |
| **the answer passage alone** | **.900** | **.953** | 1.000 |
| the answer passage + random passages, chain-sized | .827 | .867 | 1.000 |
| random passages, none on the chain | .033 | .047 | .073 |

- **The chain adds nothing to a reader holding the answer passage.** Whole chain minus answer passage alone: −.033
  [−.073, +.007] in the first version, −.027 [−.067, +.013] with pysbd, about +.007 strict. The conclusion holds at
  every version.
- **Unrelated passages mislead a little**: adding chain-sized random passages to the answer passage cost −.073
  [−.120, −.027] in the first version.
- **The measure has range**: gold chain minus random passages is +.833.
- **The two measures mostly agree**: on 534 of 600 sets. Where they differ, it is mostly "answer passage present but
  a rival sentence chosen" (61 sets, 14% of those holding the answer passage, about half of them measurement errors).

## Why the chain doesn't matter to the reader

The question already carries the constraint that the bridge passages would supply. "Last person hanged" matched
against "last person executed in Northern Ireland" is enough to pick the sentence, without being told the country.
Extra passages add only rival sentences. We predicted the reverse: that the chain would be worth about 15 points to the
reader. That prediction rested on one vivid case (Ruth Ellis), without checking how often a reader needs the bridge.

## How the two measures are used

- **A-last for sets of fixed size**, where the walk returns the same number of passages under every arm. It's free
  and agrees with the reader.
- **The reader check where set size changes** (stop rules, a second starting point, an extra read). There A-last
  rewards every extra passage and the reader penalises rivals, so the two can rank sets in opposite directions.
  Returning one passage more than the hop count raised A-last by .06 and lowered AC by .02 (SR-BS3).

## Limits

- One reader, Jev. A larger reader might use the bridge more, or be misled less.
- MuSiQue's questions are built by joining single-hop questions, so they tend to name enough to spot the answer
  sentence. A corpus whose questions are ambiguous without the chain would test the "chain doesn't matter" finding.
- AC's levels are a lower bound at the strict end and possibly lenient at the other, which is why it's a range.
