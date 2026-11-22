# Hops look (22 Nov, $0, no Jev): past hop 2, the bridge is usually a place the graph has no key for

*james. Script `hops_look.py`, output `out/hops-look.txt`. The data is the train corpus (`train-corpus.jsonl`, 2,417
answerable questions), with door keys from the train graph `graph-train-pc.jsonl` (#75), as in SR-BX. Everything since
SR-BX has been 2-hop. This look asks where the cheap walk's step (name one bridge key from the last read, then step
to a passage sharing it) stops fitting 3- and 4-hop questions, before any design or spend. It uses the gold
decomposition, so it is a look, not a result.*

**Serves.** Sirsh's 23:03Z ask (the cheap pipeline in a full walk), which bill and I split at 16:25Z, with his three
design notes.

## What the decompositions say

MuSiQue's hop questions reference earlier answers as `#j`. Of 1,165 answerable 3- and 4-hop train questions:

| type | questions | shape |
|---|---|---|
| 3hop1 | 568 | a chain: each hop depends on the last read only |
| 4hop1 | 246 | a chain |
| 3hop2 | 192 | hop 2 is a fresh sub-question (no ref); hop 3 depends on hops 1 and 2 |
| 4hop2 | 64 | one fresh hop; one hop depends on two reads |
| 4hop3 | 95 | one fresh hop; one hop depends on two reads |

- **Chains are 70% (814 of 1,165).** In a chain, every step depends only on the last read. So for chains, NAME_TASK's
  `read` is the last passage, which answers bill's note 2 from the data.
- **The other 30% aren't walks from one entry.** A third to half of their steps are fresh sub-questions, which only a
  second entry from the question can reach. They need a different design and stay out of the first test.

## Where the key goes missing

The step can only follow a door key that the read and the next hop share. Per chain step, the share of steps where
they share one:

| step | 2hop | 3hop1 | 4hop1 |
|---|---|---|---|
| 1 → 2 | .78 | .72 | .67 |
| 2 → 3 | | .46 | .44 |
| 3 → 4 | | | .52 |

- **The first step looks like 2-hop. Later steps lose about a third of their keys.**
- **It's not that the bridge is absent from the text.** On later steps, the previous hop's answer string appears in the
  next passage 85% of the time (903 of 1,060), but is one of its door keys only 33% of the time (350).
- **It's the graph's frequency limits.** The later bridges are places: Switzerland, North Carolina, Rome, Belgium,
  Boston. Where the answer is in the passage but isn't a key, the answer string appears in a median of about 200 of the
  25,405 passages. The train graph keeps no key above df 100, the fixture's declared limit, so no country, state or
  major city is a key at all.
- Excluding question words costs almost nothing (6 late steps).

## What it means for the design

- **On chains, the cheap walk should degrade toward Jev's full step, not fail.** Where no passage shares the named
  key, nt_rescue already falls back to the passage request. From the table, about half of later steps have no shared
  key, against .22 on 2-hop, where SR-BE measured the rescue at 34–37% (naming misses add to the unkeyed steps). So
  expect the rescue on well over half of later steps. The expected cost is accuracy held, at a higher input.
- **The df ceiling is the obvious next lever, and it is a constant.** Raising it would let place bridges become keys,
  but 100 is the fixture's declared limit. Changing it is a graph question for the dreaming design, not a knob to turn
  for this test. The test runs on the graph as built.
- **bill's notes, carried into the design:**
  1. The hop count comes from the data, an oracle a real walk doesn't have. It is stated as one, and a stopping rule's
     cost is reported later.
  2. `read` is the last passage, as the chain structure says.
  3. Per-hop recall is reported alongside all-hops.

## Proposed next (for registration, after bill's review)

- **SR-BH:** chains only (3hop1 and 4hop1), a fresh draw, Jev's entry request, then nt_rescue at each step from the
  last read, against Jev's full step (pass) at each step from the same entry.
- **Primary:** all-hops recall, cheap step − pass, as non-inferiority with the CI reported.
- **Secondary:** per-hop recall; the rescue rate per step against this look's prediction (about half of later steps);
  input chars per question.
- Cost by SR-BE's rates: about $0.10 for 200 questions. Cap $0.40.
