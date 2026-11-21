# REM-1341, james's part: four pricing looks. No warp or probe operation earned a registration

*21 Nov 2026, james. All are unregistered looks on seen data, run before any registration as the pricing step. None
touches the held-out SR-J-R 40, whose 4 stage-0 cases weren't opened and are excluded from any future test. $0, with no
Jev calls. Scripts: `w1_look.py`, `w1_look2.py`, `w2_look.py`, `w3_look.py`. Library: `vecops.py`.*

**Serves.** Sirsh's REM-1341 note asks for a library of vector operations that do most of Jev's work cheaply, so that Jev
judges only a shortlist. My part was (i) the library, (ii) a warp bending cosine toward Jev's price, and (iii)
separating relational twins along the relation and type directions. Before registering any of them, I priced each one on
data we'd already seen. None had headroom, so none is registered. That is the result.

## The four looks

**W1, a warp taught by Jev.** A diagonal warp (fit_diag on q⊙v and r⊙v) was fitted to Jev's cached p on SR-J's 40
questions and cross-validated by question (8 folds).

| probe | hop-2 top-1 | top-1 = Jev's pick | Jev's pick in top 5 | Spearman with Jev |
|---|---|---|---|---|
| cos_q | .20 | .20 | .60 | .18 |
| cos(q + read text), SR-J's qr | **.62** | **.62** | **.85** | **.30** |
| cos_read | .55 | .55 | .80 | .26 |
| warp on q⊙v | .12 | .12 | .50 | .15 |
| warp on q⊙v and r⊙v | .12 | .12 | .23 | .00 |

It's worse than no warp. 384–768 weights on 760 labels from 40 questions don't generalise across questions.

**W1b, a warp taught by the graph (the dreaming version).** No gold and no Jev.
- The teacher is SR-K's key-door strength from cosine's entry to each option, as a share.
- Training covers 1,142 questions (41–1252, minus SR-J-R's 40), 21,696 rows. C 0.1 was chosen by grouped CV.
- Judged by Jev on SR-J's block: the q⊙v and r⊙v warp gets top-1 = Jev's pick .40, Jev's pick in the top 5 .82, and
  Spearman .27.
- The plain text probe qr is .62, .85 and .30.

So it learns something (better than the Jev-taught warp), but stays below the unwarped text probe. A reweighting of
dimensions can't say "shares a rare entity with what was read". That's identity, not direction, and it's what the key
door says lexically (SR-K).

**W2, separating twins along the type direction** (semres worlds 41001–41004, at SR-J-R's price β 3.8, γ 3.2). The
type direction is the centroid of the answer topic's passages.

| D: rank of a [best lure] | x | type | x + type | x without s | (x without s) + type |
|---|---|---|---|---|---|
| 41001 | 10 [1] | 5 [1] | 10 [1] | 10 [1] | 9 [1] |
| 41002 | 10 [1] | 9 [1] | 10 [1] | 10 [1] | 10 [1] |
| 41003 | 10 [1] | 4 [1] | 10 [1] | 10 [1] | 10 [1] |
| 41004 | 10 [1] | 9 [1] | 10 [1] | 10 [1] | 10 [1] |

A lure ranks first under every probe. The trap is structural: one named-relation door from s, then saturation inside
the clique. No change of probe direction reaches into a clique's hit probability. This matches SR-TW's pricing, so the
twins aren't a probe problem.

One side lead from W2: removing the start passage's direction from the probe helped case A (a ranked 12→6, 4→2, 6→2,
15→6) and didn't hurt B or C. W3 checks it on real data.

**W3, pivot out what was read, on MuSiQue** (SR-J's 40, read = gold hop 1).

| probe | hop-2 top-1 | Spearman with Jev |
|---|---|---|
| q | .20 | .18 |
| pivot_out(q, read) | .07 | −.04 |
| rocchio(q, read), vector sum | .40 | .24 |
| rocchio(pivot_out(q, read), read) | .20 | .17 |
| **q + read encoded as one text** | **.62** | **.30** |

The side lead reverses on real data. In MuSiQue the read passage's direction carries the bridge, so removing it hurts.
More useful: **adding vectors loses to encoding the joint text** (.40 against .62). The encoder's own composition beats
arithmetic on its outputs.

## What this answers for REM-1341

- **The cheapest strong probe is already a text probe.** Concatenating the question with what was read and embedding
  that once needs no LLM and no generation. On this block it beats every vector operation I tried by .22 or more.
  Vector arithmetic on stored vectors is cheaper again (no encoder call), but it gives up a third of the hits.
- **The gap to Jev is identity, not geometry.** Jev pays for "this option names what hop 1 resolved". SR-K gets most of
  that lexically, by key identity. A diagonal warp or a pivot can't recover it from dense vectors. bill's SR-KB tests
  whether the keys' own vectors carry it, and that's the right next test of the vector route.
- **Twins need the ordered step, not a better probe.** That's now shown three ways: SR-TW (nulls), SR-TW (b) (the type
  term in the walk) and W2 (type-pivoted probes).

What vecops still offers is the shared operations and their contracts, which SR-KB uses unchanged.

## Postmortem

- **What went right.** I priced before registering, four times, and nothing was registered that the price had already
  killed. The SR-TW lesson ("price both factors before naming a primary") was applied.
- **What I'd do differently.** W1 should never have been looked at as a 768-weight fit on 40 questions. Counting
  parameters against labels takes a minute and would have skipped it. W2's side lead was a synthetic-world artefact: in
  gen, s's direction is noise for the hop-2 answer. In MuSiQue the read passage carries the bridge. A synthetic lead
  should be checked against the corpus feature it stands in for before it's called a lead.
- **Scope.** All of this is seen data: SR-J's easy block and the seen semres seeds. The conclusions are "no headroom",
  which a seen block can show, not "a gain", which it can't.
