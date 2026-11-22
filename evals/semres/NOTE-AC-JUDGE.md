# AC scoring fix, look (22 Nov, $0.003): a two-option Jev judge for answers stated in another form

*bill. Script `ac_equiv.py`, output `out/ac-equiv.txt`. On SR-AC's 600 cached decisions; only the 206 string-check
failures are judged. james asked for the fix (match beyond the one-directional string check) before AC is anyone's
primary.*

**Rule.** AC = 1 if the chosen sentence contains the gold answer or an alias after normalising (unchanged), **or**, when
it doesn't, Jev's argmax over two options says the sentence states the gold answer "possibly in other words". No
threshold and no token rule.

**Check against the 20 hand reads** (RESULT-SRAC.md):
- **The 11 wrong choices: judged "no" in all 11.** The judge doesn't rescue a reader error.
- The 3 normalisation misses ("Thambidurai" for "M. Thambidurai"): judged "yes" in all 3.
- The 4 gold-label cases: "yes" for the two Charlemagne sentences against "the Carolingian family" (lenient, but
  defensible). "No" for the Hohenzollern sentence (correctly: it names a different dynasty) and for the DVD-title label.
- The 2 splitter cases ("c. 1394 – 1460" cut the name off): "no", correctly, since the chosen fragment lacks the name.
  **The splitter needs its own fix**; the judge can't repair a sentence that was cut.

**Effect on SR-AC.** Each of G, L and LR gains 6; R gains 2.

| set | AC (string) | AC (string or judge) |
|---|---|---|
| G | .867 | .907 |
| L | .900 | .940 |
| LR | .827 | .867 |
| R | .033 | .047 |

AC(G) − AC(L) is unchanged: −.033 [−.073, +.013]. SR-AC's conclusion stands, at levels about 4 points higher.

**Proposal.** AC from now on = string or judge, with the judge's yes count reported. The splitter moves to a standard
sentence segmenter before AC is anyone's primary. The two R gains should be read by hand when AC is next used, since
those are the only places a lenient judge could inflate the floor.
