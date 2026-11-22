# SR-BH (registered 22 Nov, before any Jev call): does the cheap walk hold past 2 hops?

*james. Follows the hops look (NOTE-HOPS-LOOK.md, #94), with bill's review (16:29Z) applied. Script `srbh.py`. Cap
$0.40. Serves Sirsh's 23:03Z ask: the cheap pipeline in a full walk.*

**Question.** On 2-hop questions, Jev's entry request followed by the cheap step (nt_rescue) matched Jev's full step
(SR-BE: .750 against .743 both hops) at 24% less input. Past 2 hops, the look found that later bridges are mostly
places the graph has no key for (keyed reachability .44–.52 on later chain steps, against .78 on 2-hop). Does the
cheap walk still match the full step there, and what does it save?

**Data.** MuSiQue train answerable chains, 3hop1 and 4hop1, from `train-corpus.jsonl` with the train graph
`graph-train-pc.jsonl`, using each question's own pool of 20.
- The draw uses SEED 1344, a permutation of each type: 'fresh' is the first 100 of each; stage 0 is positions 100–101 of
  each.
- No Jev quantity has been computed on any 3- or 4-hop question before. SR-BX, SR-BE, SR-BR and SR-BC were all 2-hop.

**Walks.** Both walks start from Jev's 20-passage entry request (ENTRY_TASK, argmax). Then H − 1 steps, where H is the
question's hop count.
- **This uses an oracle.** A real walk doesn't know H (bill's note 1). A stopping rule's cost is a later test.
- At each step, `read` is the last passage read (chains depend only on it; the look).
- The options are every passage not yet read.
- **cheap (nt_rescue):** Jev names K from the last read's door keys; S is the unread passages sharing K.
  - |S| = 1: step to it.
  - |S| ≥ 2: Jev's PASS_TASK over S.
  - |S| = 0, or no keys: PASS_TASK over all unread (the rescue).
- **pass:** PASS_TASK over all unread.
- Tasks, the key filter (2 ≤ df ≤ 100, not contained in the question) and Jev batching are srbe.py's, unchanged.

**Primary. All hops (the walk's read set contains every hop), cheap − pass, both types pooled, paired bootstrap 95%
CI, reported with the input-chars ratio cheap / pass beside it.**
- **A tie** is a CI that includes 0.
- **H-H (non-inferiority): the lower bound is above −.05.** The margin is carried over from SR-BX's 2-hop result
  (cheap − Jev reading every passage: −.020 [−.053, +.013], post hoc), not tuned here. At n = 200 the half-width is about .05, so H-H needs
  the point estimate at about 0 or above.

**Secondary.**
- All hops and per-hop recall, by type, for both walks.
- The rescue rate per step (the look predicts well over half of later steps).
- The entry's hop position (hop 1, a middle hop, or off the chain), with all-hops by position, so that a loss from a
  mid-chain entry isn't read as a step failure (bill's note 2).
- Mean input chars per question, by type.

**Predictions.**
- cheap − pass is about 0. With the rescue on most later steps, the two walks often make the same request, so a tie is
  nearly by construction (bill's note 3). H-H passes about two times in three.
- The rescue rate is about .35 at step 1 (like 2-hop) and .55–.65 at later steps.
- The input ratio cheap / pass is .85–.95, against .76 on 2-hop. The saving shrinks with each later step.
- All-hops levels: 3hop1 about .45, 4hop1 about .25, for both walks. The entry is on hop 1 in about half the
  questions.

**What follows.**
- **If H-H passes and the ratio is under 1:** the cheap walk extends to chains at a smaller saving, and the df-100
  limit is named as what limits that saving: a graph question for dreaming.
- **If cheap falls below pass:** the postmortem says at which step, and whether at a keyed or a rescued step.
- **Fresh-sub-question types** (3hop2, 4hop2, 4hop3) need a second entry and are a separate design.
- Production is Sirsh's.

**Spend.** The dry run (`out/srbh-dry.txt`, random scores) estimates about $0.10 for the 200. Stage 0 (4 questions)
comes first. Cap $0.40.

**Scope.** MuSiQue train chains, one draw of 200, the hop count given.
