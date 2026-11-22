# Walking a graph to the answer, cheaply: what we found (November 2026)

*bill and james, 22 Nov 2026. A readable account of the walk research to date. The numbers and their caveats are in the
appendices; every claim names the study it comes from in the list at the end.*

**Tested on.** MuSiQue train (multi-hop questions over Wikipedia paragraphs), each question with its own pool of 20
candidate passages. Jev (percolate-core 0.2.15) is the model that chooses; bge-small-en-v1.5 gives the vectors. Every
result here is on that one dataset.

## What we set out to do

A question like *"Who was the last person hanged in the country where Hill of Thieves' singer comes from?"* can't be
answered from one passage. You need the passage about the song, which names the singer, then one about the singer,
which names the country, then one about executions there. Each passage holds the name that leads to the next.

Asking a model to read every candidate passage at every step finds these chains well, but it is expensive: the model
reads the whole pool again for each hop. **We wanted a cheap way to walk from the question to the answer**, with the
model making small choices rather than reading everything.

## The cheap walk

The walk we ended with has three parts.

- **Start** from the passage closest to the question by vector similarity.
- **Step** along a shared name. From the passage just read, Jev picks which of its names (people, places, titles) the
  question needs next, and the walk moves to the passage that also holds that name. This is a **lexical step**: it
  follows a word the two passages share, not a similarity score.
- **Rescue.** When the chosen name leads nowhere, Jev reads the remaining passages in full, once, for that step.

The names that link passages are **door keys**, kept in a graph built ahead of time. Jev never writes anything during
the walk: every decision is a choice among options that exist.

## How close it gets

**The cheap walk comes close to Jev reading everything, for a fraction of the input.**

- On two-hop questions, the cheap walk got both passages in about 70% of questions, using about a quarter of the
  input that Jev reading every passage at both steps used, which got about 74%.
- Starting from Jev's choice of first passage, instead of the closest vector, the cheap walk matched Jev reading
  everything (75% against 74%) with a quarter less input.
- On three- and four-hop chains, with exactly as many reads as hops, the cheap walk got the whole chain more often than
  Jev reading everything (40% against 32%), for 78% of the input. With one spare read the two tie, and the cheap walk
  still uses about a fifth less input.

Each improvement to the step was measured separately: letting Jev name the link, then adding passages that share the
name, then the rescue. Each added several points, and none was a tuned setting.

## The goal is the answer

Partway through, Sirsh changed what counts as success. Finding every passage of the chain is our measure, not the
user's. **What matters is whether the answer is in what the walk returns**, because the walk hands its passages to a
model that has to answer.

We checked this two ways:
- **Answer passage present**: the returned passages include the one that states the answer. It is cheap and exact on
  this dataset.
- **Reader's check**: Jev reads the returned passages and chooses the sentence that states the answer, and the choice
  is scored against the known answer, including the answer stated in other words. ([Appendix: the reader
  check](APPENDIX-READER-CHECK.md).)

The reader's check gave the surprise of the work. **A reader holding the passage that states the answer doesn't need
the rest of the chain.** Given only that passage, Jev picked the answer about 90% of the time; given the whole chain, no
more often. Unrelated extra passages lowered it by a few points. The question itself usually carries enough to
recognise the answer sentence without the links in between.

That changes what a good walk is:
- **Reaching the answer passage is what counts, by whatever route.** On this measure, Jev reading everything at each
  step is the better step: it often skips straight to the answer passage. The cheap walk reaches it as often only by
  returning one more passage, for about 12% less input. Its case is now cost, not accuracy.
- **Returning less is better, as long as the answer is in.** Every extra passage is a chance to mislead the reader.

## Dreaming: improving the graph from walks that worked

Between questions, the graph can learn. **Dreaming** here means: after a walk whose returned set held the answer,
strengthen the door keys it used, and leave everything else alone. The next walk then prefers doors that have led
somewhere before.

- The update **settles**: repeated passes stop changing the weights after two or three, so there is no schedule to tune.
- It **helps a little and never hurts**: about 1 to 2 points more answer passages reached on new questions, with no
  question lost in any test.
- **It works by memory, not by learning to search.** Nearly all of the gain is on questions whose answer sits in a
  passage an earlier successful walk already reached. Questions on new ground gain almost nothing. So its value in use
  depends on how often real questions come back to the same material.
- Penalising doors on failed walks didn't help new questions; a failure is mostly a fact about that one question.

([Appendix: dreaming](APPENDIX-DREAMING.md).)

## Open

**Where to start.** On two-hop questions, the walk's answer rate is capped by its first passage: once the first
passage is on the chain, the step reaches the answer almost always. Jev choosing the first passage beats the closest
vector by a few points. Walking a second starting point gets the answer passage in more often, but the reader keeps
only half of that gain, because the extra passages mislead it. A better single start is the open lever, not more
starts. ([Appendix: where to start](APPENDIX-ENTRY.md).)

**When to stop.** The walk has to decide how many passages to return. Knowing the true number of hops in advance is
the best rule we have, and it isn't available in use. Of the rules that decide for themselves:
- asking Jev whether it can already answer stops too early and costs the reader about 7 points;
- asking the reader after every read whether the answer is there comes within about 3 points, but uses about 60% more
  input and on a few hard questions never stops.

A fixed read budget would solve the runaway cases, but it is a chosen constant, so whether to allow one is Sirsh's
call. ([Appendix: steps and stopping](APPENDIX-STEP-STOP.md); [when to stop](OPEN-WHEN-TO-STOP.md).)

**Whether it holds beyond MuSiQue.** Everything above is on one dataset with a pool of 20 passages per question.
MuSiQue builds its questions by joining single-hop questions, so its answer passages recur and its questions name
enough to recognise the answer. An open corpus, with many more candidates per step, would test whether common names
still pick out one passage, whether the reader still needs only the answer passage, and how often real questions
return to the same ground for dreaming to help.

## What surprised us

- The reader didn't need the chain. We expected the links between passages to matter most to the final answer, and
  predicted they were worth about 15 points; they were worth nothing measurable.
- The cheap walk's best argument changed from accuracy to cost once the goal became the answer.
- Dreaming's gain is real and never harmful, but it is memory of where answers were, not a better way to search.

## Appendices

- [The reader check](APPENDIX-READER-CHECK.md): how answer presence is measured, and why it is reported as a range.
- [Dreaming](APPENDIX-DREAMING.md): the reward, its fixed point, and where its gain comes from.
- [Where to start](APPENDIX-ENTRY.md): first-passage choice and the second-start test.
- [Walk cost](APPENDIX-WALK-COST.md) (james): the cheap walk against Jev reading everything, by input.
- [Steps and stopping](APPENDIX-STEP-STOP.md) (james): step rules and stop rules.

## Sources

Cheap walk on two hops: SR-BX, SR-BE. On chains: SR-BH, SR-BH2. Answer passage as the measure, cheap against full
step: SR-BU2. Reader check: SR-AC, NOTE-AC-JUDGE, NOTE-AC-SPLIT. Dreaming: SR-BR, SR-BC, SR-RS, NOTE-REWARD-ALAST,
SR-BA. Entry: RESULT-ENTRY-LOOK2, SR-BE, NOTE-ENTRY-ALAST, SR-BF. Stopping: SR-BS3, SR-BS4. Keys without a frequency
ceiling: NOTE-UNCAPPED-KEYS. Each is a `RESULT-*.md` or `NOTE-*.md` file in this folder, with its registration and
postmortem.
