# Familiar queries as durable walks

Two databases whose graph is already known: a relational one, where tables are node kinds and
foreign keys are edges, and a Neo4j-style property graph. On each, a question is answered as the
query you would write anyway, one join or one relationship at a time, with a decision model
between the hops. At each hop the decider reads the question, the path so far and the rows the
join returned, and keeps the ones that bear on the question. The next join runs from those.
Switch the decider off (`--no-decider`) and you get the declarative query back: every row goes
forward, and nothing is chosen.

```sh
python3 make.py                                        # bank.db and graph.json, fixed seeds
python3 walk.py run questions/skimming.json            # one walk, with the decider
python3 walk.py run questions/skimming.json --no-decider
python3 walk.py start questions/skimming.json          # the first wave, and a token
python3 walk.py step <token>                           # one more hop, from the token
```

`walk.py` is a sketch beside midb, not part of it. midb's store takes only its own kinds of record
(commits, cards, files, decisions), so customers and accounts don't fit without an ontology
change, and this ground comes before that. The decider here is Claude on the subscription,
`claude -p`, as a stand-in for Jev, which had no credit on 9 November 2026. Every decision is
recorded in `.waves/decisions.jsonl` against its exact prompt, so the runs below replay offline
and call nothing.

## The data

- **`bank.db`** (SQLite): 40 customers, 100 accounts, 804 transactions in November 2026, and 12
  merchants. Two customers are planted as unusual: C17 makes six night-time payments of about
  490 to a new money-transfer payee, and C29 gets eleven refunds of 1 to 3 in one afternoon from
  merchants he never used (card testing). A decoy, C05, pays 48,500 with the memo "house purchase
  completion". Northgate Fuel reports skimming from 12 November. Card payments there on or after
  that date (C08, C21, C33) are at risk, and those before it (C02, C14) are not.
- **`graph.json`**: Person, Project, Component, Vulnerability and DataClass nodes, with WORKS_WITH,
  LEADS, DEPENDS_ON, AFFECTED_BY and HANDLES relationships. AFFECTED_BY links every log4j-core
  version to Log4Shell, as a naive scanner would, including 2.17.2, which is fixed.

## What happened

| question | data | without the decider | with it | decider calls |
|---|---|---|---|---|
| which projects led by Ana's collaborators have an RCE in the version they use | graph | 3 projects, precision 0.67 | 2, both right | 1 |
| which of Ana's collaborators lead a project with personal data | graph | 3 people, all right | the same 3 | 1 |
| who may have been skimmed at Northgate Fuel from 12 Nov | relational | 5 customers, precision 0.60 | 3, all right | 1 |
| whose accounts show unusual activity, judged row by row | relational | all 40, precision 0.05 | 22 (then 20 by account), precision 0.10 | 13 |
| the same, judged on per-account summaries | relational | all 40 | C17, C29 and the decoy C05, precision 0.67 | 1 |

**Where the question has a condition the schema doesn't state, the decider is that
condition.** "Affects the version they use" is not an edge, and neither is "on or after the
12th". In each case one call at the right hop dropped the rows a declarative query would have
kept: log4j 2.17.2 and a disputed denial of service, and two fuel payments made before the
skimming started. The decider explained each cut in one sentence.

**Where the schema already states the condition, the decider adds nothing.** "Personal data" is
a property, so the WHERE clause answers it. The decider kept all four rows and said why. A walk
whose decider always agrees is the declarative query, as it should be.

**A judgement about a whole population fails when made row by row.** "Unusual activity" is a
property of an account's transactions taken together, and it is relative to everyone else's.
Shown 60 transactions at a time, the decider found the oddest rows in every chunk: two
same-day charges, an identical fare paid twice. It kept 152 to 232 rows, depending on the
wording, and 20 or more customers. Grouping each account's rows did not help, because a chunk
still holds only about eight accounts, and the oddest of eight is not unusual. What worked was
the analyst's move: first an aggregate per account (payments before 6am, refunds, the largest
payment and its memo, merchants used), then one judgement over all 100 summaries at once. That
took one call and returned the two planted customers. It also kept the decoy, noting that the
house purchase "may be a legitimate one-off", which is a fair reading of "unusual".

**The decider reads whatever leaks.** In the first data, the planted transactions had been
numbered last, and the decider cited "an out-of-sequence id" as evidence. It also judged opaque
foreign keys (`merchant_id: M06`) until the hop joined in the merchant's name and category, the
way an analyst would. A decider prunes on what it is shown, so a hop should show what a person
would read, and nothing a person would ignore.

## Durable

`start` runs the first wave and saves a token: the question, the plan, the wave, every choice
so far, and a copy of the data with its fingerprint. `step <token>` runs one more hop, from
anywhere, and prints the way the walk came. On 9 November the skimming walk was started and
taken one hop, and then a new Northgate payment was written to the live `bank.db`. The next two
steps printed "the data has changed since this walk started; it goes on reading the data as it
was", and the walk answered C08, C21 and C33 as of its start. A new walk on the changed data
answered C08, C21, C33 and C39. A walk never mixes two versions of the data.

## Not shown

Four questions on two small databases, each run once with one stand-in decider: this is a
direction, not a measurement. Recall was 1.00 everywhere, because these walks prune only at
the last hop or two, where little can be lost. A decider pruning early, on a wave of
thousands, could drop the answer before it is reached, and that has not been tried here. The
decider's cost is calls, not keys: one call per hop that needs judgement, plus one per chunk of
60 rows when a wave is wider.
