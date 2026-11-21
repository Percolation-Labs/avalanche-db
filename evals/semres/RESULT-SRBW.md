# SR-BW: in a full walk, naming the bridge adds +.09 to both hops, and Jev reading passages still leads by .10

*21 Nov 2026, bill. REM-1341, on Sirsh's 23:03Z steer. Registered in `REGISTERED-SRBW.md` (with amendment 1) and
reviewed by james before any Jev call. Script `srbw.py`. Outputs: `out/srbw-stage0.txt`, `out/srbw-fresh.txt`,
`out/srbw-fresh.json`.*

**Versions.** percolate-core 0.2.15 (Jev), bge-small-en-v1.5. MuSiQue answerable 2-hop dev, positions 904–1171 of
SR-KB's seed-1341 permutation (268 questions).

**Spend.** Stage 0 cost $0.00059 (4 seen questions). The wave was 536 requests in one `ask_many`: estimated $0.0359,
spent **$0.0408**, 13% over the estimate and under the $0.25 cap.

**Walk.** The entry is cosine's top passage, the same for every arm. The arms differ in the step from it. Nothing is
given from gold.

## Result

| step from the cosine entry | both hops | ordered | hop 2 found |
|---|---|---|---|
| `cos`, the second by cosine | .235 | .187 | .343 |
| `cosdoor`, strongest shared keys (SR-E2) | .478 | .429 | .575 |
| **`name`**: Jev names the bridge from the entry's keys, then a lexical step | **.563** | .511 | .660 |
| `nameset`: as name, then Jev's passage scores over the named set (approximated) | .612 | .556 | .746 |
| `pass`: Jev picks among the 19 passages | .668 | .597 | .817 |

- **Primary, `name − cosdoor` on both hops: +.086 [+.049, +.127]. H-W passes.** Naming the bridge improves the full
  walk, not just a single hop given the truth.
- `name − pass`: −.104 [−.164, −.045]. Jev reading passages still leads.
- `nameset − name`: +.049 [+.011, +.082]. Letting Jev's passage scores choose among the named set closes about half of
  that gap. `nameset − pass`: −.056 [−.104, −.011].
- `pass − cosdoor`: +.190 [+.131, +.250]. `cosdoor − cos`: +.243 [+.175, +.306]. SR-E2 replicates: .478 against .492.
- On hop 2 found, the same order holds: name − cosdoor +.086, nameset − name +.086, name − pass −.157.

**By entry.** Cosine's entry is hop 1 in .687 of questions, hop 2 in .108, and neither in .205.

| both hops, given | n | cos | cosdoor | name | nameset | pass |
|---|---|---|---|---|---|---|
| entry = hop 1 | 184 | .272 | .625 | **.745** | .810 | .870 |
| entry = hop 2 | 29 | .448 | .448 | .483 | .517 | .655 |

- **Given a right entry, the step transfers almost exactly** (james's join, checked by me). On the same 184
  questions, james's SR-BT, which hands over gold hop 1 as read, gets:

  | arm | SR-BT (gold hop 1) | this walk |
  |---|---|---|
  | k / cosdoor | .636 | .625 |
  | jev / name | .739 | .745 |
  | nt / nameset | .821 | .810 |
  | jev_pass / pass | .891 | .870 |

  These 184 are a selected subset (questions where cosine finds hop 1, likely easier), so compare them with each other,
  not with SR-BN's .680 on another draw.
- **The entry caps everything.** In 20.5% of questions the entry is neither hop, and no step can recover them. So the
  ceiling on both hops for any step from this entry is about .80. name reaches .563 of it, and pass .668.
- **From a hop-2 entry,** the naming question is ill-posed, but name still steps back to hop 1 about as often as cosdoor
  (.483 against .448, n 29, too small to read).

**Predictions against outcomes.**
- Entry = hop 1 at .65: it was .687.
- cos .22, cosdoor .48: both right (.235, .478).
- name .53: it was .563. pass .60: it was .668, higher. nameset .58: it was .612.
- `name − cosdoor` +.05, a coin flip: it was **+.086** and passed clearly. I discounted SR-BN's +.093 by the entry rate.
  But a right-entry walk gained more (+.120 given entry = hop 1) than SR-BN's single hop did, so the discount
  overshot.

## What it means for REM-1341

- **The cheap pipeline holds in a walk.** The pieces are a cosine entry, the lexical door proposing keys, one short Jev
  request naming the bridge (about 8% of a passage request's input, SR-BN), and a lexical step. That gets .563 both
  hops against .478 for the walk without the decision.
- **Spending on the twins pays.** Adding Jev's passage judgment only where the name leaves more than one candidate
  (25.7% of questions, with 3.4 sharers on average among those) gains another +.049. In production that's a second short
  request. james's SR-BT measured it directly on the same questions: nt − jev +.119 [+.075, +.168] given gold hop 1, and
  nt − nt_cut −.011 [−.030, +.004]. So the approximation used here holds.
- **The biggest remaining loss is the entry, not the step.** 20.5% of walks start on neither hop. A better entry (for
  example, Jev choosing among cosine's top few) is the next lever. It's untested.
- **Jev reading all 19 is still best** (.668), at about 12× the naming request's input. The cheap route reaches 84% of
  it (.563/.668), or 92% with the twin step (.612/.668).

## Postmortem

- **What went right.** The full chain held. There was a gold-blind look and a registration with james's review before
  any spend. Stage 0 ran on seen questions outside the set, then one wave at about 4 cents. The `nameset` arm came from
  james's pricing as an amendment *before* any Jev call, so it's registered, not post hoc.
- **What I got wrong.** I under-predicted the gain (+.05 against +.086) and Jev's passage arm (.60 against .67). I
  scaled the single-hop gain by the entry rate and assumed a wrong entry wipes out the step. But the right-entry subset
  gained more than SR-BN's, and a hop-2 entry still sometimes recovers. Next time, predict per entry case and add the
  cases up.
- **The spend ran 13% over its estimate** ($0.0408 against $0.0359). The estimator counts characters / 4 plus 200 per
  request. SR-BN's wave was under its own estimate. The difference is small, but the estimator isn't conservative for
  long passages.
- **Scope.** 2-hop only. In-pool, 20 passages. One entry rule. `nameset` is approximated from a request that saw all 19
  passages. SR-BT's nt − nt_cut (−.011) says the approximation is close. 268 questions, so the entry = hop 2 split (n 29) isn't readable.
