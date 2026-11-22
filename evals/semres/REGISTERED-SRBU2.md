# SR-BU2 (registered 22 Nov, before any Jev call): at about equal spend, does the cheap walk reach the answer as often?

*james. Follows SR-BU (#98). bill said yes at 17:16Z, with two notes applied. Script `srbh.py --nocap --spare`, then
`srbu2.py` for the paired readout. Cap $0.10.*

**Question.** On the no-ceiling graph, the cheap walk at the hop count H uses 68% of Jev's full step's input, but
reaches the answer passage less often (A-last .800 against .835). With one spare read (H + 1), its input should be
about the full step's at H. At about equal spend, does it reach the answer passage as often?

**Two factors cross, on purpose** (bill's note 1). The step rule and the read count both change, so equal spend is
the comparison. To show the read factor alone, pass at H + 1 is reported too (cached from SR-BH2).

**Arms.** The same 200 chains as SR-BH, with H and H + 1 as oracles.
- cheap(no ceiling, H + 1): new requests for the extra step only.
- pass(H) and pass(H + 1): cached.
- cheap(no ceiling, H): cached from SR-BU.

**Primary. A-last, cheap(no ceiling, H + 1) − pass(H), paired bootstrap 95% CI, with input chars and returned-set
size beside it.**
- **H-U3:** the lower bound is above −.05, the carried margin.
- It is labelled **equal spend, not equal outcome for the reader** (bill's note 2). The cheap arm returns one more
  passage, and SR-AC found that a noise passage costs a reader about −.07.

**Secondary.**
- pass(H + 1) − pass(H): the read factor alone.
- cheap(no ceiling, H + 1) − pass(H + 1): equal reads, unequal spend.
- A-last per 10k input chars for every arm.

**Predictions.**
- The cheap walk at H + 1 is about .86 A-last (SR-BH2's cheap at H + 1 on today's graph was .86), at about 32k input
  against 37k. So cheap(H + 1) − pass(H) is about +.025, and H-U3 passes.
- At equal reads, cheap − pass at H + 1 is about −.03 (SR-BH2: −.030).

**Spend.** Only the extra step's requests are new, about $0.02. Cap $0.10. Stage 0 is skipped for the same reason as
SR-BU.

**Scope.** SR-BH's 200 chains, H given.
