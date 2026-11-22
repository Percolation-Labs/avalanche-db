# Inertia, a first look: dreaming's D3 operator mostly keeps related structure, a little more for real hops, and the graph stiffens round by round

*22 Nov 2026, bill. Sirsh's 10:35Z note on semantic inductance, intuition (3): inertia over time, meaning that
well-earned structure resists restructuring. An unregistered look, $0, no Jev. Script `inertia_look.py`, output
`out/inertia-look.txt`. james pointed to D3 as the only multi-round dreaming operator available.*

**The operator.** D3 (`evals/dream/d3/d3.py`, run unchanged) removes door memberships (passage, key) whose
neighbourhood vote is below q, round after round. Its settings are the ones its registered dev run chose for MuSiQue:
q = .05, up to 4 rounds, stopping under 1% change. **The vote never sees gold or walks.**

**"Earned."** A membership (passage, key) where the key is a door key (2 ≤ df ≤ 100) shared by two consecutive gold hops
of some MuSiQue dev answerable question. All 2,417 dev questions are used, and all hop counts. That's 7,617 of 510,121
door memberships (1.5%). Gold is used as a label only.

## Result

Each cell is the share of live memberships D3 removes in that round:

| round | changed (all) | earned | other | earned, within passages holding one | their other memberships |
|---|---|---|---|---|---|
| 1 | 12.9% | **.008** | .136 | **.008** | .160 |
| 2 | 4.0% | .008 | .042 | .008 | .052 |
| 3 | 1.8% | .004 | .019 | .004 | .022 |
| 4 | 0.8% | .002 | .009 | .002 | .011 |

- **Survival after all rounds:** earned **.978**, other **.804**.
- **The gap holds in every df band** (round 1, earned against other):
  - df 2: .008 against .243
  - df 3–5: .002 against .039
  - df 6–10: .002 against .112
  - df 11–30: .004 against .144
  - df 31–100: .016 against .144
  So rarity doesn't explain it.
- **It holds within the same passage.** A passage's earned membership is removed at .008, and its other memberships at
  .160.

**Kind-matched control (james's review).** "Earned" is also "a key shared by two related passages of one pool", which
a neighbourhood vote should favour whether or not the passages are gold. The control is keys shared by two *non-gold*
passages of the same question's pool: 128,136 memberships, of which 7,617 are sampled to match earned's df counts
exactly (seed 0).

| membership kind | removed in round 1 | round 2 | survived all rounds |
|---|---|---|---|
| earned (gold-hop bridge) | .008 | .008 | **.978** |
| related control (non-gold pair, df-matched) | .039 | .016 | **.939** |
| all related (non-gold pairs) | | | .928 |
| other | .136 | .042 | .804 |

**Most of the protection is relatedness, and gold adds a little.** Being shared by two passages of one pool lifts survival
from .804 to .939. Being shared by the two passages that are consecutive gold hops lifts it further, to .978: removal
in round 1 is .008 against .039. With 7,617 in each group, that gap is well outside sampling noise (about ±.003).

## What it shows, and what it doesn't

- **Related structure resists restructuring, and useful structure a little more.** A gold-free structural vote mostly
  protects keys that link related passages (.939 survival against .804). The gold-hop bridges come out slightly ahead of
  related pairs of the same rarity (.978). So in Sirsh's frame there is inertia, and it's mostly inertia of
  *relatedness*, with a smaller extra for usefulness.
- **The graph stiffens.** The change per round falls from 12.9% to 0.8%. Each round leaves a graph that resists the
  next round more, which is convergence with decreasing plasticity.
- **But it's not inertia from history.** D3 has no memory of use: it re-votes from the current structure every round.
  So the earned memberships survive because *the neighbourhood already supports them*, not because they were used. In
  inductance terms, this is the resistance of the structure itself, not a memory term. A true inertia from earned use
  would have D3 (or a successor) weight its vote by recorded walk traversals, or by the bitemporal history of how long a
  membership has stood. Then you'd test whether that added memory changes what survives beyond the structural vote.
- **For "define good, then let dreaming converge toward it":** D3's vote leans toward "good" (low resistance to
  gold), mostly through relatedness. It keeps 97.8% of the gold-bridge memberships and 93.9% of related non-gold ones,
  while removing 19.6% of the rest. **But walks get worse.** D3's own registered result
  (`evals/dream/d3/d3-low.txt`, MuSiQue at q = .05):
  - Held-out test, width-matched AUC: .807 (unedited) → **.765 (D3)**, against **.789 for removing the same number of
    memberships at random**.
  - Dev: .808 → .780.

  So D3 keeps the gold bridges and still does worse than random pruning. The 19.6% of other memberships it removes
  carried context that walks used. Keeping the good isn't enough, and the vote's choice of what to remove is what
  hurts. A measure of "good" for dreaming to converge toward has to price the whole path's resistance, not just whether
  the bridge survives.

**Scope.** MuSiQue dev graph only. The control's "related" means a shared door key between two passages of the same
question pool, which MuSiQue builds partly as distractors. One operator (D3) at its chosen q. "Earned" is gold bridges, not recorded walk use:
the dev walk traces cover too few questions to count use per membership. Unregistered, with gold seen.

**Next, if Sirsh wants (3) taken further.** Give D3's vote a memory term (traversal count or tenure from the bitemporal
history), register on train's graph, and test whether memory protects earned structure *beyond* the structural vote
and whether walks improve. That's a new operator variant, $0, and it needs train walk traces.
