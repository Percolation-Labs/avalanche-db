# Edge types and edge attributes

*16 Nov 2026, james. Sirsh asked (M-20261116-213631-c91b, point 2) for this before anything
filters doors on attributes: when should a distinction be its own edge type, and when should it
be a categorical attribute on a shared type? His framework (M-20261116-214238-37f1) fixes the
boundary: attributes come from the data, like typed edges in Cypher, and never from graph
statistics, the question, the gold or the answers. Dates are shelved.*

Cypher draws the line we need. `(a)-[:AUTHORED_BY]->(p)` and `(a)-[:TOUCHES]->(f)` are two
types. `(a)-[:SHARES_TERM {term: 'jackie jackson', kind: 'PERSON'}]->(b)` is one type with
attributes, where a query can write `WHERE r.kind = 'PERSON'` or leave the filter out and still
make sense. This note says which of our distinctions belong on which side, from the stores we
have, and what that means for the filter pass in [doors.md](doors.md).

## The test

A distinction is a **separate edge type** when any one of these holds:

1. **It reaches a different kind of node.** `authoredBy` goes Commit→Person and `touches` goes
   Commit→File (`src/model.rs:97-98`). A hop's type fixes its range, so the store refuses an
   ill-typed fact at write and P8QL refuses an ill-typed hop at compile. An attribute can't do
   either.
2. **Its direction, symmetry or cardinality differs.** `parent` is Commit→Commit with one or two
   per commit. `mergedAs` is one PR to one commit. `same-as` is symmetric and `is-a` is not
   (`specs/decision-walks/relations.builtin.json`). The walk reads these with different scans and
   different inverses (`Pred::inverse`), so they can't share a name.
3. **Its values change what the edge means, and the vocabulary is small and closed.** `adopts`
   and `rejects` both go Decision→Proposal, and so do `supports` and `challenges` from a claim. A
   walk that followed "any decision edge" would treat opposites as one, so dropping the distinction
   is not a neutral default. Polarity is a type.
4. **A query names it as a hop.** If people write it in a path (`<-authoredBy- commit
   -touches->`), it's a type.

A distinction is a **categorical attribute on a shared type** when all of these hold:

1. **It is the same relation between the same kinds of node.** Every shared-term door connects
   two documents that both use a term. Whether the term is a person or a place refines the door.
   It doesn't change what the door is.
2. **Ignoring it still gives a valid walk.** An unfiltered walk is correct, just less selective.
3. **The vocabulary is open or large, or there are many values per edge.** Terms, NER labels,
   relation phrases and tags. Making each value a type would grow the enumerated predicate set
   without limit, and `model.rs` refuses an unknown predicate at write, so the schema could never
   keep up with the data.
4. **The decider would filter or rank on it**, rather than the query author naming it.

In short: a **type** is a different relation; an **attribute** is a different flavour of the
same relation.

## Our data, case by case

**Git and the billing example: already right.** `authoredBy`, `touches`, `parent`, `mergedAs`,
`fixes`, `implements` and `mentions` all pass type rule 1 or 2. Each has its own domain and
range in `model.rs`, and the billing example's walk ("why is the invoice a cent off?") names them
as hops. No change.

**Percolate claims: our schema has both patterns, and one is wrong.** `supports` and
`challenges` are types (`model.rs:119-120`), which is correct by rule 3. But a claim's stance
toward a question is stored as `claim -stance-> Lit` on the claim node, beside `claim -answers->
question` (`src/construct/ingest.rs:247`). By the test, stance is a closed, polarity-carrying
distinction on the `answers` relation, so it should travel with the edge. As a node fact, a claim
that answers two questions can hold only one stance. Recorded as a finding here and not changed:
it's product schema, and no walk reads stance today.

**Tags in the reachability world: an attribute pattern by construction.** `tagged` is
Item→Lit, and "a tag is an edge between the items that share it, so it is a value, not a node"
(`model.rs:124`). Two items sharing tag `t` meet at the value `t`, so the tag is already the
attribute of that connection. This is the shape every shared-term door has. See the MuSiQue
case below and the first surprise.

**BEAM: `beside` and `near` are types; turn role is an attribute.** `beside` (same sitting,
within the walk's span) and `near` (nearest in meaning) reach the same kind of node (Item), but
they differ in how the edge is made and in symmetry. `beside` is ordered and local, while `near`
is a top-k list one way. Rule 2 makes them separate types, and they already are. Whether the
target turn is the user's or the assistant's is an attribute: the same relation, a closed
two-value vocabulary, and a walk that ignores it is still valid. It is derived from the
transcript at import. Turn distance would be an attribute too, but it is temporal, so it is
shelved with dates.

**MuSiQue: one type, three attributes.** The walk's doors are `term:<t>` (two documents
holding term `t`, with df ≤ 100), `near:<doc>` (the ten nearest by embedding) and `next:<doc>`.
`beside` is empty for all 21,100 MuSiQue documents, so MuSiQue has no `next` doors. Take
question `2hop__832795_350510`, "What group was the performer of Be the One a member of?"
The gold is "Be the One (album)" → "Jackie Jackson (album)". The first document reads
*"Be the One is the second studio album by Jackie Jackson, … The musicians included Paul
Jackson, Jr., Jeff Lorber, Robert Brookins and Gerald Albright."* It shares three terms with the
second gold document: `jackie jackson` (df 4), `jackie` (df 25) and `jackson` (df 165, over the
cap, so not a door). Its other doors include `paul jackson`, `robert`, `gerald`, `albright`,
`studio album`, `1989` and `september 9`. All of them are the same relation, "both documents use
this term". The difference between the right door and the rest is in three attributes, each
derivable at ingestion:

| Attribute | Values | Derived at ingestion from | In the example |
|---|---|---|---|
| **kind**: the term's entity type | spaCy's `PERSON ORG GPE LOC FAC NORP PRODUCT EVENT WORK_OF_ART LANGUAGE`, or `none` for a plain phrase (`DATE` is shelved) | The entity strategy already runs spaCy `en_core_web_sm` over each document's first 3,000 characters at index time (`percolate_core/walk/terms.py:69`, `graph-entities.json`). It keeps the term and **drops the label**. Keep the label per mention, and give the term its majority label. | `jackie jackson`, `paul jackson`, `gerald`: PERSON. `studio album`: none. `1989`, `september 9`: DATE (shelved) |
| **role**: where the term sits in each document | `title` (the term is the document's title, with any "(album)" disambiguator removed), `lead` (first sentence), `body` | The document's own text and title | In "Jackie Jackson (album)" the term is the title. In "Be the One (album)" it is in the lead sentence. |
| **relation**: what the source says about the term | The dependency phrase that links the document's subject to the term, mapped to the built-in relation catalogue where it fits (`member-of`, `part-of`, `is-a`, …), otherwise its lemma (`by`, `include`) | A spaCy dependency parse of the sentence holding the term, at index time | "album **by** Jackie Jackson" → `by`. "the musicians **included** Paul Jackson, Jr." → `include` |

None of the three reads the question, the gold or the answers. All are open or large
vocabularies on one relation, so by the test they are attributes, not types. `SHARES_PERSON`,
`SHARES_PLACE` and their siblings would be eleven types for one relation, and `relation` alone
would add an open set.

`near` doors get one data-derived attribute: **same_subject**, true when the two documents'
title heads match. MuSiQue repeats titles (three documents are titled "Macbeth"), so a near door
between two paragraphs of one article is a different situation from a near door between two
articles. A near door's cosine rank is a graph statistic, so it goes in the description (below),
not here.

## Descriptions and attributes: the split

Sirsh's framework separates two things a door carries, and [doors.md](doors.md) now follows it.
Both are built at ingestion and never see the question.

- **Description** (framework point 4) is graph-derived. It says what is immediately behind the
  door (the targets' titles and openings), gives a compressed summary of what is reachable
  through it, and carries the door's **statistics**: unread target count, the term's postings
  (df), centrality and specificity. The decider reads the description, which is what it ranks on.
- **Attributes** (point 3c) are data-derived categories: the door's **type** (its predicate) and
  categorical values such as `kind`, `role`, `relation` and `same_subject`. The filter pass
  selects on attributes.

`jackie jackson` has df 4 and `jackson` has df 165. That is a statistic, so it goes in the
description. That `jackie jackson` is a PERSON who is the title of one target is an attribute.

## A shared-term door is not an edge in our store

In avalanche-db a shared-term door is not an edge between two documents. It is two `tagged`
facts that meet at a term value: `doc_a -tagged-> "jackie jackson" <-tagged- doc_b`
(`src/construct/lab.rs:71`). So the attributes split by what they belong to:

- **kind** belongs to the term. One fact on the term node, `"jackie jackson" -kind-> PERSON`, is
  the same for every door through it.
- **role** and **relation** belong to each mention, one document's use of the term. They need a
  fact about a fact. A quad's fourth position is the named graph, used today for provenance, so
  the candidates are a mention node (`doc -mentionsTerm-> m`, `m -term-> t`, `m -role-> lead`) or a
  graph per mention. The mention node costs a hop on every term door, which the walk would have to
  skip in its scans. Deciding this is part of building 3c.

## What the filter-then-rank test (3c) needs first

1. **Keep the NER label at index time.** It is already computed. Store the term's majority kind,
   and add role and relation for each mention. A graph-build change in percolate-core's
   `walk/terms.py` and the fixture builder, with a fixture rebuilt on a new version. This is
   the graph that is genuinely different from today's, which the framework asks for before
   claiming generality.
2. **Store attributes as facts.** `kind` on the term node, and role and relation on a mention node
   (or the alternative above). Add the predicates to `model.rs` with their signatures.
3. **The filter pass reads categories, not statistics.** `Attrs` gains `categories:
   BTreeMap<String, String>`, its `stats` move to a `Description`, and the `AttrFilter` fake
   filters on one category. The decider interface already has `filter` (avalanche-db #1).
4. **Controls in the same run:** chance, the coin model, word overlap, search and the oracle,
   each under plain ranking and under filter-then-rank, on the same questions and budget.

**Registered prediction, for that later test.** On MuSiQue HELD-OUT, a filter that keeps term
doors whose `kind` is the question's answer type or the bridge entity's type, plus all `near`
doors, will remove at least half of each wave's doors while keeping at least 90% of the oracle's
recall@10. Ranked after that filter, Jev's MRR of the gold door rises over plain ranking, and so
does word overlap's, with the oracle unchanged. The filter is a decider step: choosing which kinds
matter reads the question, which only the decider may do. If kinds cut doors without keeping the
oracle's recall, the attribute is the wrong cut, and that is the answer to Sirsh's question for
MuSiQue.

## What surprised us

- **The door we most wanted to type isn't an edge at all.** In a quad store, two documents
  sharing a term meet at a value. The useful attributes split between the term (kind) and each
  document's use of it (role, relation). In Cypher this would be one relationship, and here it
  is not.
- **We already compute entity kinds and throw them away.** The entity strategy runs spaCy over
  every document at index time and keeps only the string.
- **A shared term almost never leads to the term's own page.** Of 782,953 (term, document)
  links in MuSiQue's term graph, 3,976 (0.5%) reach a document titled by the term. 1,685 of 86,149
  terms are exactly some document's title. "argentina" is held by 64 documents, and none is titled
  Argentina. So `role = title` is rare and should be specific when it fires.
- **Our own schema was inconsistent before we asked the question.** It types polarity correctly
  (`supports` and `challenges`), and puts a claim's stance on the claim node instead of on the
  `answers` edge it qualifies.
