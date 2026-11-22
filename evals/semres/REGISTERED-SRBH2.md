# SR-BH2 (registered 22 Nov, before any Jev call): with one spare read, does Jev's full step recover?

*james. Follows SR-BH (RESULT-SRBH.md, #94), at bill's request (16:35Z), before anything about order versus choice
goes to Sirsh. Script `srbh.py --spare`. Cap $0.10.*

**Question.** In SR-BH both walks read exactly H passages, and the cheap walk got all hops +.080 more often. At the
first divergence, the pass walk skipped a hop along the chain in 10 of the 24 cheap wins and left the chain in 9.
With exactly H reads, a skip is a lost hop. If the pass walk's loss is **order** (it reads the right passages in the
wrong sequence), one spare read should recover much of it. If it's **choice** (it reads wrong passages), it won't.

**Design.** The same 200 questions, walks and rules as SR-BH, with H + 1 reads for both walks: one more step from the
last read, by each walk's own rule.
- The first H reads are SR-BH's exactly (cached, deterministic).
- The extra step's requests are new. The dry run (`out/srbh2-dry.txt`) shows 400 name and pass requests and about 100
  twin and rescue requests, about $0.04.
- Re-using SR-BH's questions is deliberate. This tests a mechanism on the walks it was seen on, not a new effect. A
  mechanism confirmed here still needs a fresh draw before any claim beyond these 200.

**Primary.** All hops, paired bootstrap 95% CI.
- **H-O (order), amended before the run at bill's review (16:37Z):** order is *shown* only if both hold.
  - pass(H+1) − pass(H) has a lower bound above 0.
  - The paired difference-in-differences [(cheap − pass) at H+1] − [(cheap − pass) at H], bootstrapped over the 200
    questions, has an upper bound below 0.
- Computed by `srbh2_did.py` from `out/srbh-fresh.json` and `out/srbh-fresh-spare.json`.

**Secondary.**
- cheap(H+1) − cheap(H).
- cheap(H+1) − pass(H+1), with the input ratio.
- Of SR-BH's 10 'pass skips' questions, how many the pass walk completes with the spare read.
- The same for the 9 'pass leaves the chain' questions.

**Predictions.**
- pass(H+1) − pass(H) is about +.06. The skipped-hop questions mostly recover, since the skipped passage still shares
  the chain's entities and the pass request ranks it high once its successor is read.
- cheap(H+1) − cheap(H) is about +.03.
- cheap − pass at H+1 is about +.04, still positive: the leave-the-chain losses don't recover.
- H-O passes. Of the 10 skips, about 6 recover; of the 9 leaves, about 2.

**What follows.**
- **If H-O passes:** the summary to Sirsh is "the cheap walk orders the chain. Jev's full step finds the same passages
  given a spare read, so with a stopping rule the cheap walk's case is input, not accuracy".
- **If it fails:** the summary is "the named bridge chooses better, not just in a better order", to be confirmed on a
  fresh draw before it's a claim.

**Scope.** SR-BH's 200 chains, the hop count + 1 given (an oracle).
