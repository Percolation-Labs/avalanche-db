# The Steiner cost and the encoding gap: the structure is there, and PR titles are an encoding fault

*18 Nov 2026, bill. Registered first (REGISTERED.md, 8b07b56). $0: the dev trace replays (cards 100, PR titles 65,
MuSiQue 101, k=10), the probe's E2E_STEINER mode, and an oracle arm in the same settings. No default changes.*

## (a) The Steiner cost: the answer is small, near, and cheap in the graph as built

Reads from search's 5 seeds, through the walk's own doors in shown order, by greedy cover. The **Steiner share@5** is
the share of gold read within 5 reads past the seeds, the k=10 budget; it counts gold that is already a seed.

| dev set | share@5 | median reads to all gold | random seeds: share@5 / median | shuffled links: share@5 / median | oracle recall@10 |
|---|---|---|---|---|---|
| cards | .913 | 2 | .288 / 10 | .410 / 12 | .727 |
| PR titles | .997 | 2 | .316 / 9 | .562 / 14 | .876 |
| MuSiQue | .863 | 3 | .450 / 9 | .711 / 6 | .677 |

This supports the theory: the answer is a small connected substructure near the seeds, reached in 2–3 reads. The
same reads from random seeds, or through doors with the same widths and random targets, cost 3–7 times as much.

**Predicting the walk:** the share is near its ceiling (most questions are at 1.0), so it ranks questions poorly.
Spearman with the walk's recall is +.37 on cards, +.18 on PR titles and +.62 on MuSiQue. MuSiQue's +.62 is no better
than the share's correlation with search's recall (+.67). The measure says the substructure exists and is cheap. It
doesn't say whether a walk will find it. That is (b).

The greedy cover may stop partway through a door, and the walk can't (an opened door's targets are all read, up to
the budget). So (a) is the graph's cost, a lower bound on the walk's. The oracle's recall under the walk's own rules,
.68–.88, is the walk-feasible version.

## (b) The encoding gap: whether the right door can be told apart

At each recorded wave that has a gold door (a door with unread gold behind it), where does the best gold door sit in
Jev's ranking?

| dev set | waves | gold door first: Jev | search order | width | random | MRR, Jev | expected gold from the first door, as a share of the best gold door's |
|---|---|---|---|---|---|---|---|
| cards | 87 | **.78** | .23 | .15 | .06 | .87 | .55 |
| PR titles | 71 | **.21** | .17 | .07 | .04 | .37 | .11 |
| MuSiQue | 97 | **.64** | .18 | .13 | .04 | .74 | .56 |

On cards and MuSiQue the door text lets Jev pick out the gold door 3–4 times as often as search order. On PR titles
it barely does better than search order (.21 against .17). Jev's first door there was a gold-free term door on 56 of
71 waves. The best gold door was a term door on 59 waves and a `next` door on 10. Of the wave-1 gap, between the gold
the best door would return and what Jev's first door returns, 98–100% falls on questions whose share@5 is at least
.5. So on PR titles the structure holds the answer, and the information written into it doesn't show the way.

This is the encoding-layer fault Sirsh separated from the theory (M-20261118-164942-d93f). It is the number dreaming
should move: (b), per wave, on questions where (a) is high.

## The postmortem

- **The registered "test of the theory" was the wrong shape.** I registered "does share@5 predict recall" as the test
  of the Steiner theory. Share@5 saturates on these corpora (median 1.0), so a weak correlation says little either
  way. The theory's evidence is the comparison with the controls. The prediction the walk needs comes from (b). A
  graph measure that ranks questions would need a harder budget than 5, or the cost under the walk's own rules (whole
  doors). Neither is registered.
- **Process:** two of my background wait loops hung for about 80 minutes. `pgrep -f "st-mq.jsonl"` matched the loops'
  own command lines. The probe runs had finished long before. Next time, wait on a PID, not a pattern.

## For dreaming (james)

- Per-wave rows: `out/b-{cards,prs,mq}.jsonl`. Each row has qid, question, wave, reads before, the doors opened,
  steiner_share5, and per door: key, kind, unread width, gold behind it, Jev's P and rank, and search-order score.
- The objective: gold door first, or MRR, per wave, on held-out questions, against search order as the floor of the
  ranking.

## Files

- `score.py`: (a) and (b), with `score.txt`;
- `rows.py`: the per-wave rows;
- `out/steiner-*.jsonl`: the per-question covers, with controls;
- `out/oracle-*.k10.jsonl`: the oracle arm;
- `probe/src/steiner.rs`.
