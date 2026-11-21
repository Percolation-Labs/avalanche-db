# SR-BX: on fresh train questions, the cheap step comes within .05 of Jev's full choice at about 40% of the input; the title entry fails

*21–22 Nov 2026, bill (walk, entry) with james (train graph, rescue rule). REM-1341. Registered in `REGISTERED-SRBX.md`
(#74, with amendment 1, james's yes before any Jev call). Script `srbx.py`. Outputs: `out/srbx-stage0.txt`,
`out/srbx-fresh.txt/json`, `out/srbx-posthoc.txt`.*

**Versions.** percolate-core 0.2.15 (Jev), bge-small-en-v1.5. MuSiQue *train*, james's 2,417-question corpus (#75), the
first 300 answerable 2-hop questions of seed 1341. The door keys are from `graph-train-pc.jsonl`.

**Spend.** Stage 0 was $0.0016. The run was **$0.1200** in three `ask_many` waves (600, 904 and 92 requests), under the
$0.40 cap. Each wave came in above its estimate (wave 1 $0.043 against $0.039), so the estimator runs about 10% low,
as in SR-BW.

## Result

Both hops right (the pair {entry, step} = {hop 1, hop 2}), with 300 questions per cell:

| step ↓ / entry → | `e_cos` (cosine) | `e_title` (Jev over titles) |
|---|---|---|
| `cosdoor` | .473 | .483 |
| `name` | .523 | .530 |
| `nt` (+ Jev over named twins) | .617 | .610 |
| **`nt_rescue`** (+ Jev's full request when the name matches nothing) | **.723** | **.743** |
| `pass` (Jev over all 19) | .743 | .727 |

`e_pass × pass` (Jev over full passages at both steps) gets .750.

**Primary: `e_title × nt_rescue − e_cos × name` = +.220 [+.160, +.280]. It passes.** But the factors split it cleanly.
**All of the gain is the step, and none is the entry.**

**The step (registered secondaries):**
- Naming: `e_cos × name − e_cos × cosdoor` +.050 [+.013, +.087]. That replicates SR-BW's +.086 on train, smaller.
- Twins: `e_cos × nt − e_cos × name` +.093 [+.060, +.130]. That replicates SR-BT's +.119 in a walk.
- Rescue: `e_cos × nt_rescue − e_cos × nt` **+.107 [+.070, +.147]**. james's |S| = 0 rule, now registered and fresh.
- Against Jev reading everything: `e_title × nt_rescue − e_pass × pass` −.007 [−.053, +.037].

**The entry (registered secondaries):**
- `e_title − e_cos` on entry = hop 1: **−.130 [−.193, −.073]. The title entry is worse** (.593 against .723).
- `e_title × name − e_cos × name`: +.007 [−.033, +.047]. The title entry adds nothing to a walk.
- Jev over full passages (e_pass) does no better at hop 1 (.607).
- Both Jev entries pick hop 2 far more often than cosine does: .257 and .280, against .117. Asked "which passage should be
  read first to answer the question", Jev seems to go for the passage that holds the answer, not the one that starts
  the chain. Both hops is unordered, so those walks can still score when the step goes back to hop 1. That's why the
  title entry ties on both hops while losing on hop 1. The ordered metric shows it: e_title × nt_rescue .550 against
  e_cos × nt_rescue .650.

**By repeated titles** (james's readout):

| pools | n | e_cos | e_title | e_pass |
|---|---|---|---|---|
| with a repeated title | 143 | .594 | .455 | .510 |
| without | 157 | .841 | .720 | .694 |

The title entry is worse in both groups, by about .13, so the cosine tie-break inside repeated titles isn't the cause.
Repeated-title pools are harder for every entry.

**Post-hoc** (unregistered, `out/srbx-posthoc.txt`):
- `e_cos × nt_rescue − e_cos × pass`: −.020 [−.053, +.013]. The cheap step from cosine's entry is level with Jev reading all
  19.
- `e_cos × nt_rescue − e_pass × pass`: −.027 [−.077, +.023].
- `e_title × nt_rescue − e_cos × nt_rescue`: +.020 [−.023, +.067].
- From cosine's entry, the named set is empty in .28 of questions (the rescue fires), has one member in .50, and has
  2+ in .22, with 3.7 passages on average.

**Cost of the cheap walk** (`e_cos × nt_rescue`), in units of one 19-passage Jev request per question: naming about .08
(SR-BN) + rescue .28 × 1 + twins .22 × 3.7/19 ≈ .04. That's **about 0.4 requests**, against 1.0 for `pass`. The
entry is free (cosine).

**Predictions against outcomes.**
- e_title hop 1 .78: **wrong**, .593. I assumed titles name the entity the question starts from. I didn't consider that
  "read first" would be read as "where the answer is".
- e_cos hop 1 .68: .723.
- e_cos × name .56: .523. e_cos × nt_rescue .64: .723, higher. e_title × nt_rescue .72: .743. e_pass × pass .75: .750.
- Primary +.16: +.220. It passed for the step's reasons, not the entry's.

## What it means for REM-1341

- **The cheap walk is now: cosine entry; the door proposes keys; Jev names the bridge; then a lexical step, with two
  Jev fallbacks.** The fallbacks are a short request over the named twins when the name leaves several, and a full
  passage request only when the name matches nothing. On fresh train questions it gets .723 both hops. That's within
  about .05 of Jev reading every passage from the same entry (.743; −.020 [−.053, +.013], **post-hoc**), at about 40%
  of the input.
- **That's on both hops.** On ordered it's level (.650 against .653). On hop 2 found the gap is larger (.853 against
  .890), so Jev's full read still finds hop 2 more often.
- **The rescue was the biggest single piece** (+.107). Its trigger, "no other passage shares the name", is free and
  visible before any passage request.
- **The entry stays cosine.** A Jev entry, from titles or full passages, finds hop 1 less often. The open entry lever
  (cosine starts on neither hop in about 16% here) needs a different question to Jev. One option is "which passage does
  the question's first clause describe". That's untested, and it means a new wording, so it needs a registration.

## Postmortem

- **What went right.** The factorial design (entry × step) separated a passing primary into "step works, entry doesn't".
  A single crossed comparison would have credited the title entry with the gain. james's review caught a crash that
  would have hit after two paid waves, and asked for the repeated-title split, which rules out the tie-break as the
  cause.
- **What I got wrong.**
  - **The primary was a crossed comparison.** It passed, but it can't say which factor passed. The secondaries saved the
    reading. Next time, make the primary one factor at a time, with the crossed walk as the headline secondary.
  - **The entry wording wasn't priced.** I guessed .78 for a new Jev wording without a single stage-0 look at what it
    picks. Stage 0 showed e_pass choosing hop 2 in 3 of 4, and I noted it without acting on it. That was the signal. A
    stage-0 surprise should pause the wave, not just be noted.
- **Scope.** MuSiQue train 2-hop, in-pool, 300 questions. One wording per task. The train graph shifts k by up to .03
  against dev's graph-mq (#75), so levels aren't compared with dev's.
