# J4: the gold door is the previous answer's key; connection separates it as well as likeness does

*19 Nov 2026, bill. Registered first (REGISTERED-J4.md, e04e1f6). $0, no Jev, nothing fitted. Output: `j4.txt`;
per-sub-question AUCs are written to the run dir as `j4.json`.*

MuSiQue test, later sub-questions. Candidates are the neighbours of the read set, a median of about 2,500. Each
attribute's AUC for the gold candidate within its sub-question, averaged, with a 95% interval:

| attribute | RO: earlier gold read | RD: J3's D reads |
|---|---|---|
| *gold among the doors* | 213/247 | 201/247 |
| **connection** | | |
| strength (Σ 1/(df−1) over shared keys) | **.842** [.809, .871] | **.841** [.808, .873] |
| narrow (narrowest shared key) | .811 [.779, .840] | .799 [.763, .832] |
| fan-in (reads it links to) | .554 [.533, .577] | .733 [.697, .766] |
| beside | .500 (MuSiQue has no next links) | .500 |
| **likeness** | | |
| question (BM25 of the whole question) | **.842** [.809, .876] | **.859** [.824, .894] |
| passage (BM25 of the unfilled sub-question) | .798 [.760, .836] | .810 [.770, .849] |
| near (wording door) | .605 [.578, .633] | .596 [.568, .624] |
| door text (keys named in the sub-question) | .510 [.502, .520] | .536 [.519, .556] |

**Diagnostic:** a shared key equals the previous hop's answer for 66% of gold candidates (RO), against 3% of the
others. With D's reads it's 50% against 0.6%.

## What it says

- **J3's "the fill is the door" holds at the level of keys.** In two thirds of the cases where the right passage was
  read, the door to the next hop is a key spelled exactly as the previous answer. Fewer than 3 in 100 other doors
  carry it. The answer names the door.
- **Connection separates as well as likeness, and without the question.**
  - Strength and narrowness reach .81–.84 using only the graph: narrow keys shared with what was read point to the
    next hop.
  - That is the gold-free signal James's L2 rewards. Here it ranks individual doors rather than whole spreads.
- **Likeness separates through the whole question, not the unfilled sub-question's door words.**
  - The whole question (.84–.86) beats the sub-question (.80). The other hops' entities in it act as anchors.
  - Matching keys to the sub-question's words is near chance (.51–.54). The sub-question names the relation, not
    the door.
- **Fan-in depends on the read set.** It is weak over the gold reads (.55), where there are one or two reads, and
  useful over D's 10 (.73). That is a property of breadth, not of the door.
- **Scale check.** No single attribute reaches J3's top 5. *Corrected after J4b:* I first wrote that an AUC of .84
  leaves gold around 400th. That is the mean, but the ranks are skewed, and J4b measured the median at 17–120
  depending on the attribute and read set. The conclusion stands that the decision has to combine them.

## What the door description should show Jev

Per candidate answer and door:
1. the key's width (df), or the summed strength over what's been read (connection);
2. the passage's match to the whole question (likeness);
3. whether the key is a candidate answer, which ties the description to the fill J1 already asks Jev to choose.

Presenting those is a registration of its own: a Jev arm, ≤$0.05, on J1's candidates. That's for Sirsh to steer.

## Postmortem

- **The prediction was half right.**
  - Likeness was strongest, as predicted, but in the form of the whole question. The unfilled sub-question came
    second.
  - Narrow and strength did beat fan-in, as predicted.
  - I didn't predict connection would tie likeness.
- **Beside was registered without checking that MuSiQue has any next links. It has none.** A one-line count on the
  graph would have dropped it, the same rule P2 and J3 taught: look at what you already have before registering.
- **Scope.** These are AUCs on MuSiQue test with gold sub-question boundaries, and nothing is combined. They say
  which signals exist, not what Jev would do with them.
