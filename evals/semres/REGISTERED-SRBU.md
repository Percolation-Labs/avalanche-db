# SR-BU (registered 22 Nov, before any Jev call): does the knob-free graph get the cheap walk to the answer?

*james. Follows NOTE-UNCAPPED-KEYS.md and NOTE-ANSWER-MEASURE.md (#98); bill said yes at 17:06Z, and his four notes are
applied. Sirsh at 17:07Z: the goal is that the answer is contained in what the walk returns, checked. Script
`srbh.py --nocap` with graph `graph-train-pc-nocap.jsonl`. Cap $0.20.*

**Question.** On the current graph, the cheap walk returns the answer passage less often than Jev's full step (A-last
.790 against .835, −.045 [−.095, .000], SR-BH re-scored). Its later steps fall back to the full request because the
graph has no keys for common-place bridges (df > 100). Without the ceiling, does the cheap walk reach the answer
passage as often as the full step, still at lower input?

**One factor.** Only the graph changes: every key with df ≥ 2 that is not contained in the question, with no upper
bound (bill's note 1). Everything else is SR-BH's exactly:
- the 200 chains (seed 1344);
- Jev's entry request;
- the nt_rescue step from the last read;
- the tasks.
- **H is an oracle**: each walk reads exactly the hop count.

The pass walk doesn't use keys, so its arm is SR-BH's, cached. The today-graph cheap arm is also SR-BH's, cached, and
its re-scoring is in `out/srbu-today.txt`. The questions are SR-BH's seen ones, so that the arms pair. No Jev quantity
was tuned on them, and the no-ceiling graph is the knob-free choice, not one picked from a look. A fresh draw follows
before any claim.

**Primary (Sirsh's measure).** A-last: the returned set contains the gold last-hop passage. The answer is in that
passage in 380 of 380 checked questions. Paired bootstrap 95% CI over the 200:
- **H-U1: cheap(nocap) − cheap(today) has a lower bound above 0.** The graph change helps the cheap walk reach the
  answer.
- **H-U2: cheap(nocap) − pass has a lower bound above −.05,** the non-inferiority margin carried from SR-BH, with net
  input chars beside it.

**Secondary.**
- All hops, and answer-string presence.
- The rescue rate per step, today against nocap (bill's note 2). The mechanism needs it to fall from .44 / .62 / .65.
  If A-last rises without that, something else is going on.
- **Naming accuracy (bill's note 3):** at keyed steps from an on-chain read, does the next hop share the named key,
  and is it the only passage that does? Today: .399 and .356, out of 306 steps.
- **Net input chars (bill's note 4):** longer name option lists against fewer rescue requests, by type.
- The returned sets are saved, for bill's AC reader check later.

**Predictions.**
- The rescue rate at later steps falls to about .35.
- Naming accuracy falls a little per option, from .40 to about .35, since there are twice the options, but it applies
  to far more steps.
- A-last cheap(nocap) is about .83, so H-U1 lands at about +.04 and is borderline. H-U2 passes.
- Net input falls further: fewer rescues outweigh longer name lists, giving a cheap / pass ratio of about .70.

**What follows.** If both pass, the cheap walk on the knob-free graph is offered to Sirsh as the step rule on his
measure, to be confirmed on a fresh draw. If H-U1 fails with the rescue rate down, the named keys lead somewhere other
than the answer, and the naming readout says where. Production is Sirsh's.

**Spend.** The dry run (`out/srbu-dry.txt`) estimates about $0.02–0.03. Stage 0 is skipped: the same script and
questions ran clean in SR-BH, and only the key file changes. Cap $0.20.

**Scope.** SR-BH's 200 chains, the hop count given.
