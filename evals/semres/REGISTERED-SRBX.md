# SR-BX (registration text; it takes effect when james posts the graph calibration and signs off, before any Jev call)

*bill (walk, entry) and james (train graph, rescue rule). REM-1341. Script `srbx.py`.*

**Serves.** SR-BW put the cheap pipeline into a full walk: cosine entry, then the door proposing keys, Jev naming the
bridge, and a lexical step. It got .563 both hops against .478 without naming, and .668 for Jev reading all 19. Two
losses remain, each with a free or cheap signal:
1. **Entry.** Cosine's top passage is neither hop in 20% of walks, and no step can recover those.
   - On dev (all 1,252, seen; `out/entry-look.txt`), cosine's top-1 holds hop 1 .679 of the time, top-3 .856 and
     top-5 .901.
   - The room is there, but "Jev picks among the top m" puts a knob (m) in the design.
2. **Failed names (|S| = 0).** When no other passage shares Jev's name, the lexical step falls to k (.375 in SR-BT).
   Jev's full passage request gets .896 on the same questions. That signal is free.

**Data.** MuSiQue *train*.
- james's corpus `~/.cache/walklab/mq-train/train-corpus.jsonl`: 2,417 train questions (seed 1342), stratified to dev's
  exact hop mix, with their pools' passages only.
- The registered draw is the first 300 of `np.random.default_rng(1341).permutation` over its answerable 2-hop questions.
  Stage 0 is positions 300–303, outside the set.
- Door keys come from `graph-train-pc.jsonl` (25,406 passages), built by james's `build_keys.py` with the fixture
  manifest's declared extractor limits unchanged, plus 2 ≤ df ≤ 100. Nothing is fitted to graph-mq or to train.
- **The corpus is about 20% bigger than dev's** (fewer passages shared across train pools), so df and doors differ
  somewhat from dev's. Dev numbers are context, not a baseline.
- Gold-blind look: no pool passage is missing from the graph, and the cosine entry's door keys have a median of 19 (dev 22).

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

**Walks scored.** {e_cos, e_title} × {cosdoor, name, nt, nt_rescue, pass}, and e_pass × pass. That's 11 walks. Jev runs
three dependent `ask_many` waves: (1) the entry requests; (2) name and passage requests from each distinct entry; (3) the
twin requests. `nt_rescue` reuses wave 2's passage p, so it costs nothing extra here. In production it's one full passage
request, sent only when |S| = 0. Metrics are as in SR-BW: both hops, ordered and hop 2 found.

**Primary.** Both hops, `e_title × nt_rescue − e_cos × name`, paired bootstrap 95% CI.

**Secondary.**
- `e_title − e_cos` on entry = hop 1.
- `e_title × name − e_cos × name`: the entry alone.
- `e_cos × nt − e_cos × name` and `e_cos × nt_rescue − e_cos × nt`: the step alone (james's SR-BT, in a walk).
- `e_cos × name − e_cos × cosdoor`: SR-BW's primary, replicated on train.
- `e_title × nt_rescue − e_pass × pass`: the cheap walk against Jev reading everything at both steps.
- Cost: requests and spend per wave, as the script prints them. The per-walk cost in production is stated in passage-request
  units in the result, from the counts.

**Predictions** (per entry case, added up, as SR-BW's postmortem asked).
- **Entry hop 1:** e_cos about .68 (dev's rate). e_title about .78: titles are mostly the entity a passage is about, and
  the question names hop 1's entity in its first clause.
- **Given entry = hop 1:**
  - e_cos × name about .74 (SR-BW .745).
  - nt about .81.
  - nt_rescue about .87, adding james's |S| = 0 rescue (SR-BT: .896 against .375 on 18% of questions).
- **Both hops:**
  - e_cos × cosdoor about .48.
  - e_cos × name about .56.
  - e_cos × nt_rescue about .64.
  - **e_title × nt_rescue about .72.**
  - e_pass × pass about .75.
- **Primary** `e_title × nt_rescue − e_cos × name`: about +.16. A pass is very likely if the train corpus behaves like dev.
  The risk is in e_title, which nobody has measured.

**Spend.**
- Stage 0: 4 questions, about $0.002.
- The wave set is up to 3 entries × (one passage request plus one naming request) per question, plus one entry request
  over 20 passages, one over 20 titles, and the twins. Repeated entries are cached once.
- At SR-BW's rate (about $0.00015 per passage request), that's between $0.09 (most entries agree) and $0.18 (none agree).
- **Cap $0.40**, within the $1 rule. The script refuses to start a wave whose estimate would cross the cap.

**Scope.** MuSiQue train 2-hop, in-pool, 20 passages. One wording per task. SR-J's, SR-BN's and the new entry wording
aren't searched. 300 questions.

**Graph calibration (james, #75, posted before this takes effect).** On dev's seen sets, the rebuilt extractor moves k
by −.015 to −.034 against graph-mq, ceiling_k by ±.01, and cosdoor by 0 to −.03. The predictions above are dev-based. The
arms that lean on k (cosdoor, and name/nt through k ties) may run about .02 low on this graph. The predictions are
left unchanged, and this note is the stated allowance.

## Amendment 1 (james's review of #74, before any Jev call)

- **A bug, fixed.** The reference walk (`e_pass × pass`) looked up a naming request that wave 2 never sends. Wherever
  e_pass differed from both other entries, the run would have died after two paid waves. `from_entry(..., names=False)`
  now computes only the passage step for e_pass.
- **Repeated titles.** **143 of the 300 pools contain a repeated title** (MuSiQue titles repeat within pools). With titles
  as options, Jev faces identical strings. The rule is knob-free: Jev picks a title, and among the passages carrying
  that title, e_title is the one nearest the question by bge cosine. This was set before any Jev call. It means
  e_title isn't purely a Jev choice when titles repeat. It's Jev's title choice, then cosine within that title.
- **Readout added (james):** entry accuracy for each entry rule, split into the 143 repeated-title pools and the 157 others.
- **Prediction unchanged** (e_title hop 1 about .78). The repeats add risk to it, since a title shared by hop 1 and a
  same-name lure leaves the split to cosine.
