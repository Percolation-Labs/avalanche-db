# L1 result: learned link weights raise the avalanche's reach of the Steiner graph on cards and PR titles

*19 Nov 2026, james. $0, no Jev. Registered in REGISTERED-L1.md (c71fa7f) before any run. Code: l1.py, and l1diag.py
for the unregistered diagnostic. Output: out/l1-blind.txt, out/l1-q.txt, out/l1-diag.txt.*

**Verdict: PASS on bar (i) for cards and PR titles; MuSiQue fails, and is harmed.** Dreaming learns three link weights
per graph from past questions' outcomes: door width, target degree and teleport. Under those weights, the
question-aware avalanche (LQ) reaches more of held-out questions' gold beyond the seeds than the same avalanche on
uniform links (Q, P1's online computation).

Test recall@5 of gold beyond search's top 5 (95% paired bootstrap):

| | cards | PR titles | MuSiQue |
|---|---|---|---|
| S, search ranks 6–10 | .144 | .163 | .086 |
| U, uniform avalanche | .207 | .380 | .122 |
| L, learned, question-blind | .235 | .473 | .144 |
| Q, question-aware (online prior) | .219 | .227 | .145 |
| **LQ, Q on learned weights** | **.306** | **.611** | .094 |
| LQ − Q | **+.087 [+.010, +.168]** | **+.384 [+.280, +.489]** | −.051 [−.090, −.019] |
| H, LQ × dev-gold history | .319 | .611 | .132 |
| Jev walk, 5 reads (reference) | .355 | .098 | .362 |

Learned θ1, θ2, α: cards (0, −1.5, .5); PR titles (−2, −1.5, .3); MuSiQue (−1, +.5, .15).

**What was tested.** Sirsh's 10:25 test (M-20261119-102537-f47f) asks for the online computation first. Here that is Q:
per question, spread probability from the seeds toward passages that match the question. Dreaming can't see future
questions. It learns from past attempts (dev seeds and their gold) which links the spread should favour, and stores
that as weights on the links. The test was whether those stored weights let the same cheap computation reach held-out
questions' Steiner graphs more often.

**Bars:**
- (i) needed LQ − Q ≥ +.03 with its interval above 0 on two sets, and LQ above its shuffled-reward fit there. Cards
  and PR titles pass.
- (ii) needed L to close half the Q − U gap. It passes on the letter on cards and MuSiQue, but vacuously: the gap is
  .012 and .023, and L's own gains there have intervals that include 0. On PR titles, Q is below U, so there is no
  gap to close. Only (i) carries the result.

**Mechanism.**
- **PR titles:** 64 of LQ's 77 test gold hits are passages Beside a seed: the commits next to the PR's search hits.
  Narrow doors (θ1 = −2) and low-degree targets (θ2 = −1.5) send the spread down those short links, not into wide term
  doors. Question words alone push it the other way: Q < U, P1's failure. The learned weights undo that.
- **Cards:** the weights do the same, more mildly. They favour targets with few doors and teleport more (α .5), so mass
  stays near the seeds. That is where the Steiner graph lies, since gold pairs are mostly direct links.
- **Avalanche, PR:** the gold mass reached after 1, 2 and 3 steps is .099, .064 and .098 under LQ, against .035, .014
  and .014 under Q. The weights keep mass on gold as it spreads, not just at the first step.

**Diagnostic (not registered).** LQ's test recall at all 60 grid points, to tell learning from "any θ would do":
- **Cards:** dev's pick ranks 1st of 60 on test, and dev and test recall correlate at .92.
- **PR titles:** dev's pick ranks 4th, with correlation .98. The median θ already beats uniform (.432 against .227),
  so uniform is a poor point on this graph.
- **MuSiQue:** dev's pick ranks 45th, with correlation .46. The best test θ (.148) barely beats uniform (.145), so
  there is little to learn there, and dev's 101 questions picked noise.

**Postmortem.**
1. *What worked:* the reward. Scoring the walk's reach, not a door AUC over surviving doors, turned the same weight
   family that failed in V1 and D3c (cards and MuSiQue at uniform, PR +.052 width-matched) into +.087 and +.384.
   D3's lesson held: score what the walk reaches.
2. *What failed:* selection on MuSiQue. A 60-point argmax over 101 dev questions with a +.03 dev gain is within noise,
   and it chose θ2 = +.5, a direction no other set took. Rule for the next registration: keep uniform unless dev's
   gain clears its own paired bootstrap above 0.
3. *The shuffled-reward control was weak.* Another question's gold is almost never reachable from these seeds, so
   those fits found nothing and fell back to uniform. The grid diagnostic is the stronger control, and it supports
   cards and PR titles.
4. *H, the history prior,* adds +.012 on cards and +.038 on MuSiQue (where 73 of 245 test gold were dev gold) and
   nothing on PR titles (0 of 166). It is memory of past answers, worth what the overlap is worth and no more.
5. *Scope:* this is a ranking at the walk's 5-read budget, not a walk. LQ beats search at equal budget on all three
   sets (MuSiQue by .008), and beats the Jev walk on PR titles (.611 against .098). It doesn't beat the walk on cards
   (.306 against .355) or MuSiQue. The reward used dev gold. In the product, the reward has to come from walk
   outcomes without gold, such as what the caller used. That is untested.

**Next.**
- A walk that gives LQ's top unread passages to Jev as one more option each wave, registered, $0 replay first, then
  Jev ≤ $1. PR titles is where it should show.
- MuSiQue stays at uniform under the bootstrap rule above.
