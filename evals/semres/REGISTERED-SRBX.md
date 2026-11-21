# SR-BX (DRAFT, not registered): the cheap walk with a chosen entry and james's rescue rule, on MuSiQue train

*bill (walk, entry) and james (train graph, rescue rule). REM-1341. A draft for james's review. It becomes a
registration only once james's train graph calibration is posted and both of us sign off, before any Jev call.*

**Serves.** SR-BW put the cheap pipeline into a full walk: cosine entry, then the door proposing keys, Jev naming the
bridge, and a lexical step. It got .563 both hops against .478 without naming, and .668 for Jev reading all 19. Two
losses remain, each with a free or cheap signal:
1. **Entry.** Cosine's top passage is neither hop in 20% of walks, and no step can recover those.
   - On dev (all 1,252, seen; `out/entry-look.txt`), cosine's top-1 holds hop 1 .679 of the time, top-3 .856 and
     top-5 .901.
   - The room is there, but "Jev picks among the top m" puts a knob (m) in the design.
2. **Failed names (|S| = 0).** When no other passage shares Jev's name, the lexical step falls to k (.375 in SR-BT).
   Jev's full passage request gets .896 on the same questions. That signal is free.

**Data.** MuSiQue *train*, answerable 2-hop. A seeded draw (seed and size fixed here once james posts the pool count).
Door keys come from james's train graph, built with the extractor setting fixed by his dev rebuild (not tuned on train).
Dev numbers are calibration only.

**Entry arms** (each picks e from the question's 20 passages):
- `e_cos`: argmax cos(question, ·), bge-small. This is SR-BW's entry.
- **`e_title`**: one Jev request whose options are the 20 passages' **titles only**. The task: "Each option is the title of
  a passage. Which passage should be read first to answer `question`?" e = argmax p. No knob, and the input is about the
  size of a naming request.
- `e_pass` (reference): the same task over the 20 full passages. That's about a full passage request in cost.

**Step arms** from e (SR-BW's and SR-BT's, unchanged):
- `cosdoor`
- `name`
- `nt` (name, then Jev over the named twins)
- **`nt_rescue`**: nt, except when |S| = 0, where s is Jev's full passage request over the 19 others (james's rule)
- `pass`

**Walks scored.** The primary pair is `e_title × nt_rescue` against `e_cos × name` (SR-BW's walk). Every entry × step
cell is also reported. Metrics are as in SR-BW: both hops, ordered, hop 2 found, plus Jev input characters per question.

**Primary (draft).** Both hops, `e_title × nt_rescue − e_cos × name`, paired bootstrap 95% CI.

**Secondary (draft).**
- `e_title − e_cos` on entry = hop 1.
- `nt_rescue − nt` (james).
- `e_title × nt_rescue − e_pass × pass`: the cheap walk against Jev reading everything at both steps.
- Cost: characters per question for each walk.

**Predictions (draft; to fix at registration).**
- e_title hits hop 1 about .78, above cosine's .68. MuSiQue titles are mostly the entity a passage is about.
- `e_title × nt_rescue` both hops about .70, against `e_cos × name` about .55.

**Spend estimate.**
- Per question: one title request (small), one naming request, a twin request in about 25% of questions, a full passage
  request in about 18%, and the references (`e_pass`, `pass`).
- At SR-BW's rate, about $0.0002 per question all in. 300 questions comes to about $0.06. The cap will be fixed at registration
  (≤ $0.25).

**Open for james.**
- The train pool count and the draw size.
- Whether the title-only entry belongs in this registration or in a separate one first.
