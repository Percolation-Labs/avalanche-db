# AC splitter fix, look (22 Nov, $0.013): a standard segmenter instead of the regex

*bill. `srac.py --pysbd` (pysbd, English, clean=False), outputs `out/srac-fresh-pysbd.txt`, `out/srac-fresh-pysbd.json`,
and `out/ac-equiv-pysbd.txt` (the judge on top). On SR-AC's 150 questions; only the 231 of 600 reader requests whose
options changed were re-asked.*

**Why.** The regex split at every ". " before a capital or digit, so "Dr. B.R. Ambedkar" and "(c. 1394 – 1460)" were
cut mid-name (2 of SR-AC's 20 hand-read failures). pysbd splits 17.5% of the corpus's passages differently, mostly at
abbreviations and initials.

| set | regex | pysbd | pysbd + judge |
|---|---|---|---|
| G | .867 | .893 | .927 |
| L | .900 | .920 | .953 |
| LR | .827 | .833 | .867 |
| R | .033 | .033 | .047 |

- **SR-AC's primary is unchanged:** AC(G) − AC(L) −.027 [−.067, +.013] (regex −.033).
- Flips regex → pysbd: 12 up, 4 down. The Prince Henry case is fixed ("Prince Henry the Navigator of Portugal (d. 1460)
  sent expeditions…").
- **One new risk:** pysbd keeps table-like text (the Lok Sabha deputy-speaker list) as one long segment holding many
  names, so a choice of that segment contains the answer easily. Read long chosen segments by hand when AC is next a
  primary, as with the judge's R gains.

**Proposal.** AC = pysbd segmentation + string-or-judge from now on, with the judge's yes count and any chosen segment
over a few sentences long reported. SR-AC's conclusion (the answer passage alone suffices for a reader) stands at
levels 2–6 points higher than first reported.
