# Stop rules on the answer measure (22 Nov, $0, post hoc on SR-BS's cached walks)

*james. Sirsh's 17:07Z goal re-scores SR-BS (#97). Its stop rules were judged on all hops, and this re-reads them on
A-last (the gold answer passage is returned) and on returned-set size, which the reader pays for (SR-AC: about −.07
per noise passage). Seen walks, so a look, not a result.*

| walk | stop | A-last | returned | input |
|---|---|---|---|---|
| cheap | oracle H | .856 | 3.00 | 25.6k |
| cheap | oracle H + 1 | .933 | 4.00 | 33.9k |
| cheap | S-in | .983 | 15.5 | 95.7k |
| cheap | S-check | .767 | 2.62 | 26.6k |
| pass | oracle H | .900 | 3.00 | 32.0k |
| pass | oracle H + 1 | .933 | 4.00 | 41.7k |
| pass | S-in | .867 | 4.59 | 37.8k |
| pass | S-check | .767 | 2.27 | 26.9k |

**S-check is much better on A-last than all hops said.**
- On the cheap walk it stops **at the very read where the answer passage arrives** in 116 of 180 questions, after it
  in 22, and **before it** in 42.
- Its 'stop' decisions are right 137 of 179 times on A-last, against 53 on all hops.
- It returns 2.6 passages against the oracle's 3.0.
- The cost is the 42 early stops: −.09 A-last against oracle H.

**What the early stops look like** (read by hand, in session, 6 of the 42):
- **The answer is in an off-chain passage.** "When did the Indian city where Northern Railway is headquartered first
  host the Asian Games?" It stopped after *New Delhi* and *India at the Asian Games*. The second passage very likely
  states 1951. A-last is a lower bound, and some of the 42 are A-last's misses, not the rule's.
- **Jev answers from its own knowledge.** "What is the currency in the place *Overheard 2* is set?" It stopped after
  the film's passage (set in Hong Kong). Hong Kong dollar follows from world knowledge, not from the reads. The same
  goes for David Allyn's university founder and Brexit's date: it stopped one hop in.
- Of the 42, 18 stopped after one read: 7 on hop 1, 6 off-chain, 5 on hop 2.

**What follows.** S-check's question, "`question` can be answered from these passages", lets Jev count what it
already knows. A wording that asks whether the passages *state* the answer would test that mechanism. It's a wording
change, so under the held-out rule it needs registering on a fresh draw. Proposed SR-BS2:
- Fresh chains, pass walk only (the better step on A-last at equal reads, SR-BU2).
- Stop rules: S-check as registered against S-state ("these passages state the answer to `question`" / "`question`
  needs a passage not yet read"), with oracle H as the reference.
- Primary: A-last, S-state − S-check, with returned-set size beside it.
- About $0.15. Cap $0.30. Dropping S-in (the cheap walk's runaway) and the cheap walk makes it cheaper than SR-BS.
