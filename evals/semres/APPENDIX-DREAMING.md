# Appendix: dreaming, a reward from walks that worked

*bill, 22 Nov 2026. Appendix to WRITEUP-WALK.md. Sources: DESIGN-BRIDGE-REWARD.md, RESULT-SRBR.md, RESULT-SRBC.md,
DESIGN-REWARD-SCALE.md, RESULT-SRRS.md, NOTE-REWARD-ALAST.md, RESULT-SRBA.md. All $0: no Jev calls, cached walks only.*

**Tested on.** MuSiQue train 2-hop questions (1,089 to 1,111, split into halves by a hash of the question id),
bge-small-en-v1.5, the structural walk: start at the closest passage by vector, then step through the strongest
weighted door key. The known gold chain stands in for "the user confirmed the answer".

## The idea

Sirsh's framing: define what a good walk is, measure it, and let dreaming move the graph towards it. Dreaming runs
between questions. It looks back at walks that succeeded and strengthens the door keys they passed through, so that a
later walk prefers doors that have led somewhere before.

**The reward.** For each successful walk on the learn half, every shared key on the walk is raised at both ends, in
inverse proportion to how many passages hold the key. A rare shared name gets more credit than a common one. Nothing
about the test questions is used.

## Does it converge?

**Yes, in two passes.** A reward changes walks, and changed walks earn different rewards, so we asked whether
repeating it settles. We tested two updates. One replaces the weights each pass from that pass's successes. The other
rewards each question once.

| learn half (652) | successful walks | weight change |
|---|---|---|
| unweighted | 302 | |
| pass 1 | 307 | |
| pass 2 | 307 | 1.1% |
| pass 3 | 307 | 0 |

Both updates stop at the same 307 walks and the same weights. The update settles because a reward only raises doors
that already won, so it changes the argmax for very few walks, and none for the worse. On another corpus it could
cycle; nothing guarantees convergence by construction.

## Does it help new questions?

**A little, and it never hurts.**

| reward learned from | test measure | gain over no reward | questions gained / lost |
|---|---|---|---|
| walks that got both passages (SR-BR, SR-BC) | both passages | +.017 [+.007, +.031] | 8 / 0 |
| walks whose set held the answer passage (look) | answer passage present | +.022 [+.009, +.037] | 10 / 0 |
| the same, halves swapped (SR-BA, registered) | answer passage present | +.012 [+.004, +.022] | 6 / 0 |

- **No test question was ever lost** to the reward, in any arm or direction.
- **The outcome signal matters.** Boosting the same number of randomly chosen walked keys gained less (+.011 less,
  [+.002, +.022]). Boosting the keys of *failed* walks gained nothing.
- **Rewarding the answer passage directly is at least as good** as rewarding the whole chain, and needs only "did the
  answer passage come back", which is closer to something a product could observe.

## Where the gain comes from: memory, not search

james asked for the gain split by whether a test question's answer passage had been reached by a rewarded learn
walk. MuSiQue reuses single-hop questions, so answer passages recur far more than whole chains do (136 of 489 test
questions, against 6 that share a whole chain).

| test questions | n | gain |
|---|---|---|
| answer passage reached by a rewarded learn walk | 136 | +.037 |
| not | 353 | +.003 |

**The reward works by remembering where answers were.** It helps a later question whose answer sits in the same
passage, and almost nothing else. Its value in use depends on how often real questions return to material an earlier
confirmed walk reached. MuSiQue has a lot of that by construction; a real workload may have more or less, and nothing
here measures it.

An earlier reading (SR-BR) said the gain "isn't memorising answers", because almost no test question shared a whole
chain with a learn question. That was true of chains. At the level of answer passages, the gain is recurrence.

## What didn't work

- **Penalising failures.** A version that also lowered doors on failed walks lifted the learn half's own success from
  .463 to about .51, six times the success-only gain there, but transferred less to new questions (+.011, against
  +.017). It also cycled: cutting a door redirects some walks, which then fail elsewhere and restore it. A failure is
  mostly a fact about that one question.
- **A unit-free scale.** The reward's size (one success = one unit of base door strength) is a convention. Replacing
  it with a measured success rate removed the unit but transferred less (+.011 against +.017, not significant). On
  this data, larger boosts lean towards transferring better. The scale is still a named convention, not a derived one.

## Limits

- **The structural walk only.** On the answer-passage measure, Jev's full step is now the better walk. Whether a door
  weight changes a walk where Jev chooses is untested.
- **Gold labels stand in for a confirmed answer.** In use, the signal would come from users or from the reader check,
  and would be noisier.
- **2-hop MuSiQue only**, where reaching the answer passage and reaching the whole chain nearly coincide. On longer
  chains, an answer-passage reward would also reward walks that skip the bridge.
