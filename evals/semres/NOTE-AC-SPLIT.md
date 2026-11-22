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

**Judging string hits too (james's knob-free check, `ac_equiv.py --hits`, `out/ac-equiv-pysbd-hits.txt`, $0.003).**
Every chosen sentence gets the two-option judge, not only string misses. (The "with judge" totals in that file
double-count under `--hits`; read the rejection lines.)
- String hits the judge rejects: **G 9 of 134, L 14 of 138, LR 6 of 125, R 4 of 5.**
- **On random sets the rejections are real accidental containment** (a Rohtang Pass sentence mentioning the
  Himalaya; a prime-minister sentence mentioning the United Kingdom).
- **On gold sets they are mixed.** Some are accidental (a Clinton County sentence for "Franklin County"); some are the
  judge being strict on a sentence that does state the answer ("Moldavanka … in the Odessa Oblast").
- With the judge as the only scorer (strict), AC(G) ≈ .867 and AC(L) ≈ .860, so the primary is about +.007 instead of
  −.027. **The conclusion is the same either way**: the chain adds nothing to a reader holding the answer passage.

**So AC is reported as a band from here on:** lenient (string or judge) and strict (judge only), with the
string-hit-judge-no count per arm. Where a decision would differ between the two, it isn't settled. This replaces a
length cut on long segments.
