# Design (22 Nov): a checked measure of "the answer is in what the walk returns"

*bill. Sirsh at 17:07Z: the goal is the answer. The walk returns passages to an LLM, so the measure is whether the
answer is contained in what it returns, checked properly rather than by string match. Stop rule, step rule and
dreaming reward are then optimised toward it. Design for james's review; nothing is run.*

## Why chain and answer diverge

SR-BS, 3hop1: "Who was the last person hanged in the country where Hill of Thieves' singer comes from?" (Robert
McGladdery). Jev's full step read *Hill of Thieves* (Irish folk singer Cara Dillon), then *Robert McGladdery* ("last
person executed in Northern Ireland") and *Ruth Ellis* ("last woman hanged in the United Kingdom"). It skipped the
passage saying where Cara Dillon is from. The answer string is in the returned set, and so is a rival. The passage
that tells a reader which one to pick isn't. The cheap walk read all three hops.

**So the measure must be a reader's choice, not a string's presence.** A string match scores that set as a success.
Whether it is one depends on whether a reader, given the set, picks McGladdery over Ellis.

## The measure: AC, "answer chosen"

- **Request.** Context: the question and the full text of every returned passage (`reads`). Options: every sentence of
  the returned passages. Task: "Each option is a sentence from `reads`. Which sentence states the answer to
  `question`?" Jev's argmax is the reader's choice. One request per (question, returned set), batched with ask_many.
- **Scoring.** AC = 1 if the chosen sentence contains the gold answer or an alias (normalised). The string match only
  checks the *chosen* sentence; the choice is the reader's, made with rivals in view.
- **Why sentences, not entity names.** The graph's keys contain the gold answer for only 41–52% of answer passages
  (`out/ac-ceiling.txt`; dates, numbers and many names aren't keys), while the answer string is in its passage's text
  in 100%. Sentences cover every answer, need no option list we design, and keep the rival sentences in the choice.
- **Choose, not generate.** Jev picks among sentences that exist; no answer is written.

## Validation (before AC scores any walk)

On a fresh draw of 2-hop, 3hop1 and 4hop1 questions, AC on four fixed sets per question:
- **gold chain**: every hop passage. AC's ceiling; it should be high.
- **answer passage only**: the last hop's passage alone. The gap to the gold chain is the divergence Sirsh asked about,
  measured.
- **answer passage + random pool passages**, to the chain's size: does noise without the bridge mislead the reader?
- **random pool passages** of the chain's size, excluding the answer passage: the floor (AC should be near 0; a
  sentence can contain the gold string by accident).

Plus agreement with string presence, and the share of AC failures where the chosen sentence is a rival that states
a same-type answer (the Ruth Ellis case). I'll read 20 failures by hand, in session, to check the scoring.

## Then

1. Re-score the cached arms (SR-BH, SR-BH2, SR-BS) with AC, so every step and stop result has an answer reading.
2. Re-aim: the stop rule (james) can ask the AC request itself ("stop when the reader's choice stops changing" is one
   knob-free form), and the bridge reward (mine) rewards walks whose returned set passes AC, not the gold pair.

**Cost.** Each request carries the returned set (about 1–3k characters per passage) plus its sentences as options, so
about twice the set's text. The validation (4 sets × 150 questions) should be under $0.10; re-scoring the cached arms
under $0.20. Each is priced by a dry run first and capped.
