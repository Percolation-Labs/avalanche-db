# SR-BW (registered 21 Nov, before any Jev call or scoring): the cheap pipeline in a full walk

*bill. REM-1341, on Sirsh's 23:03Z steer. Script `srbw.py`. Jev cap $0.25. james reviews.*

**Serves.** SR-BN showed the cheap pipeline works for one hop given the *true* hop 1. The lexical door proposes the read
passage's rare keys, one short Jev request names the bridge from them, and a lexical step through that one name finds
hop 2 (.680 against the door's .587). Sirsh asks whether that holds in a full walk, where hop 1 is chosen, not given.
A wrong entry makes every name wrong. The baseline to beat is SR-E2's cosdoor: entry by cosine, then the door
(both hops .492 on questions 201–700, .50 over all 1,252).

**Walk.** Per question, over its pool of 20 (MuSiQue answerable 2-hop).
- **Entry e** = argmax cos(question, ·) with bge-small, the same for every arm (SR-E2's cosdoor entry).
- **Step arms**, each picking one other passage s; the walk's pair is {e, s}:
  - `cos`: the second passage by cosine (SR-E's baseline).
  - `cosdoor`: argmax door strength S[e, ·] = Σ 1/(df − 1) over shared door keys, ties broken by cosine (SR-E2).
  - **`name`**: Jev names one key K from e's door keys R. The wording is SR-BN's naming task, unchanged. s = argmax
    1/(df_K − 1) · [v shares K], ties broken by S[e, ·], then by cos(question + e's text, ·). That's SR-BN's lexical
    step, james's rule. If R is empty, s is cosdoor's step.
  - `pass`: Jev picks s among the 19 others with SR-J's passage task, unchanged, read = e's text. This is the
    reference, at about 12× the tokens.

None has a free parameter. Every request of a set goes out in one `ask_many` wave.

**Metrics.**
- `both`: {e, s} = {hop 1, hop 2}, unordered as in SR-E.
- `ordered`: e = hop 1 and s = hop 2.
- `hop2`: hop 2 is in {e, s}.
- Also reported: entry accuracy, and `both` given entry = hop 1 and given entry = hop 2.

**Data.** SR-KB's permutation (seed 1341 over 41–1252, minus SR-J-R's 40). The **registered set is positions
904–1171**, the 268 left after SR-BN's 600–899 and james's stage 0 (900–903). No name or pass arm has been scored on
them. The cos and cosdoor arms were scored earlier on overlapping questions (SR-E2's 201–700 in file order and the
all-1,252 check), but nothing was tuned on them. Stage 0 is positions 0–3: seen data (SR-KB's first four), outside the
set.

**Gold-blind look, done before this registration.** Every entry has door keys (median 22, none empty). One case: an
entry about Hampartsoum Limondjian offers keys such as "armenian apostolic" and "classical music".

**Primary.** `both`, `name − cosdoor`, paired bootstrap 95% CI. H-W passes if the lower bound is above 0: naming the
bridge improves a full walk, not only a given hop.

**Secondary,** with CIs:
- `name − pass` (both): how far the cheap step stays behind Jev reading passages.
- `pass − cosdoor` (both).
- `cosdoor − cos` (both): SR-E2's replication.
- The same four on `hop2`.

**Predictions.**
- Entry = hop 1 about .65.
- `both`: cos about .22, cosdoor about .48, name about .53, pass about .60.
- `name − cosdoor` about +.05, about SR-BN's +.093 scaled by how often the entry is hop 1. So H-W is a coin flip.
- Given entry = hop 2, the naming question is ill-posed. Jev might still name the bridge, since the hop-2 passage is
  about it, and step back to hop 1. That's unknown; I'll report it.

**Spend.**
- Stage 0: 4 questions, 8 requests, about $0.0006.
- The wave: 268 names plus 268 passages, about $0.04 by SR-BN's rate. Cap $0.25. Within the $1 rule.

**Scope.** 2-hop only. In-pool, with 20 passages per question. One fixed entry rule (cosine). This is not a multi-wave
walk, and it doesn't cover 3- or 4-hop questions.

## Amendment 1 (before any Jev call; from james's 23:06Z pricing on SR-BN's seen 300)

- **A fifth arm, `nameset`.** It's the same as `name`, except when two or more other passages share K. Then s is the
  one Jev's passage request scores highest *among that set only*. With one sharer, s is that passage. With none, s is
  `name`'s step.
- It costs no extra Jev calls here: it reads the `pass` request's p over all 19. In production it would be a Jev
  request over the named set only. james prices that at about 0.84 extra passages per question, about 4% of a passage
  request. Because Jev saw all 19 in context here, the arm is an **approximation**, and I'll label it so.
- **Secondary:** `nameset − name` and `nameset − pass` on `both`, plus the named set's size.
- **Prediction.** On SR-BN's 300 with gold hop 1, james's approximation gets .787, against name .680 and pass .843. In
  the walk, nameset is about .58: between name (.53) and pass (.60), closer to pass.
- **Shared draw.** james will register "beyond the name" (gold hop 1 as read) on the same 904–1171, before either of us
  scores. It's a different task, and neither of us will look at the other's outcomes before both are registered.
