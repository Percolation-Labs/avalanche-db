# Registered: D0, is the encoding gap in the door's text? (james, 18 Nov 2026, before spend)

The plan is in M-20261118-182525-95f5. Dreaming would choose, per passage, which of its own sentences stands for it in
door text. D0 asks whether that choice can move a gold door at all, before any operator is built.

**Cases.** Dev questions (cards-dev, prs-dev, musique-dev), today's walk at k=10, replayed from the recorded decisions
at $0. The wave-1 batch qualifies when some door has a gold target and Jev ranked a gold-free door above it. The gold
door is the best-ranked door with a gold target; the control door is the top-ranked door.

**Variants.** Rebuild the door's lead lines (`- title: sentence`) with another sentence of each lead's passage. Its
head, first snippet and names line stay as they are. Three fixed rules, no question:
- `second`: the second sentence;
- `last`: the last sentence;
- `longest`: the longest sentence.
One headroom arm that sees the question and could never ship: `q-best`, the sentence sharing the most words with the
question. Each variant re-sends only the request holding that door, every other option byte-identical. The rebuilt
unchanged request must hash to its recorded key (the builder check). The door's new P is placed among the batch's
recorded P; P is page-independent (#847).

**Read-outs.**
- For the gold door: the share of cases where the best fixed variant puts it on top, and its median rank change.
- The same for the control door, to measure how much a change of text moves P anyway (noise).
- Headroom: `q-best`.

**Decision.** There is text headroom if the gold door's best-fixed-variant top rate exceeds the control door's rate
of being displaced from the top by .10 or more on at least two of the three sets. Without it, dreaming writes links,
not text, and D1 is planned on links.

**Spend.** Cap $0.30, with one probe request first.
