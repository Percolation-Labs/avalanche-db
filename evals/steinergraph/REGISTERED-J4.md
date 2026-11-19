# J4 (registered before running): what a door already carries that separates the gold door from the rest

*19 Nov 2026, bill. $0: no Jev, nothing fitted, no thresholds. Proposed by james (M-20261119-152325-796f) after
J3 found that choosing the fill is choosing the door.*

## Question

After hop j has been read, the next hop's gold passage is among roughly 2,500 linked passages (J3). Which attributes
the graph and text already provide rank the gold candidate above the others? Whatever separates is what a door's
description should show Jev.

## Units

- MuSiQue test, later sub-questions (hop ≥ 2).
- **Read set R:** two versions, both reported:
  - **RO:** the earlier hops' gold passages, as in J3's DO;
  - **RD:** what J3's D arm actually read.
- **Candidates:** the neighbours of R under L1's graph (a key held by 2–100 passages, or next/near), excluding R. Only
  sub-questions whose gold is among the candidates are scored.
- **Score per attribute:** the AUC within each sub-question (the share of non-gold candidates the gold candidate
  beats, with ties counted as half), averaged over sub-questions, with a 95% bootstrap interval over sub-questions
  (2000 resamples, seed 0). No threshold is involved.

## Attributes, kept apart as Sirsh asked at 12:34

**Connection.** Structure only; no question text.
- **narrow:** the minus-df of the narrowest key the candidate shares with R. A candidate linked only by next/near
  gets −∞.
- **strength:** Σ over reads r of Σ 1/(df−1) over the keys shared with r, plus 1 for each Beside link (james's L2
  strength).
- **fan-in:** how many passages of R the candidate links to.
- **beside:** whether there is a next link either way with a read passage.

**Likeness.** Text.
- **near:** whether there is a near link with a read passage (a wording door).
- **passage:** BM25 of the unfilled sub-question against the candidate passage, i.e. J3's ranker.
- **door text:** how many of the shared keys have every token in the unfilled sub-question.
- **question:** BM25 of the whole original question against the candidate passage.

**Diagnostic, gold-using, not an attribute.** The share of gold candidates for which a shared key equals the
previous hop's answer (lower-cased, exact), against the same share among non-gold candidates. This tests J3's "the
fill is the door" directly.

## Prediction and what counts

- **Prediction:**
  - passage likeness is the strongest single attribute, at about .8 (J3's top-5 rate implies a high AUC);
  - question likeness is second;
  - among connection attributes, narrow and strength beat fan-in, and beside is weak because most candidates have
    no next link.
- **What counts as an attribute worth showing Jev:** its interval lies above .5. An attribute whose interval
  overlaps .5 doesn't separate. The ranking is reported as measured, whether or not it matches the prediction.
- **Not done here:** combining attributes, which would need fitting and belongs to a later registration on dev.
