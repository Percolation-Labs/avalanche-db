# What a door membership is worth to walks: bridges matter most, mostly for their own questions; pruning the rest is about neutral

*22 Nov 2026, bill. The "priced on walks" measurement that NOTE-D3M (#82) called for, following james's suggestion. An
unregistered look, $0, no Jev. Script `removal_map.py`, output `out/removal-map.txt`. The graph is MuSiQue dev
graph-mq. The walks and score are D3's own dev waves and scorer: width-matched AUC of read-set PPR, plus the share of waves
with a gold door. They're seen data.*

**Method.** Door memberships (2 ≤ df ≤ 100) are split into classes. For each class, 5 draws each remove **7,000**
members (the size of the smallest class, rounded down) and rebuild the graph. Each draw is scored against the unedited
graph G0 (AUC .8079, gold-door share .674). Removing the same count from every class makes the harms comparable per
membership.

| class (size) | ΔAUC (± s.e., 5 draws) | Δ gold-door share |
|---|---|---|
| **earned**: key shared by two consecutive gold hops (7,617) | **−.0536 ± .0018** | **−.153 ± .002** |
| related: key shared by two non-gold pool passages (128,136) | +.0018 ± .0011 | −.003 ± .003 |
| D3 vote decile 1, lowest (51,012) | −.0011 ± .0008 | −.001 |
| vote decile 2 | −.0016 ± .0006 | −.003 |
| vote deciles 3–9 | −.0022 to +.0006 | 0 to −.007 |
| vote decile 10, highest | −.0035 ± .0019 | −.007 |

D3's q = .05 sits at the 13.5th percentile of the vote, so D3 removes about the lowest decile and a third of the next.

**This first table is circular, as james's review found.** "Earned" was built from all dev questions' gold chains,
and the scoring waves are questions in that same set. So removing it removes the very bridges being scored, and the 7,000
was also 92% of that class against 5–14% of the others. The corrected run is below. Read it, not this table, for value
per membership.

## Corrected run (`removal_map2.py`, `out/removal-map2.txt`)

**Split.** Questions are split in two by sha256 of the MuSiQue id. Only half 1's D3 dev waves are scored (65 of 144
waves; base AUC .8142, gold-door .692).
- **earned_heldout:** bridges of half-0 questions that are *not* bridges of any half-1 question (2,829).
- **earned_scored:** bridges of the scored questions (4,788). It's the circular reference.

Table A removes an equal count (2,000) from each class, and Table B an equal fraction (10%). Each has 5 draws.

| class | A: ΔAUC per 1,000 removed | B: ΔAUC per 1,000 removed | Δgold-door (A / B) |
|---|---|---|---|
| **earned_scored** (bridges of scored questions) | **−.0070** | **−.0170** | −.080 / −.015 |
| **earned_heldout** (bridges of *other* questions) | **−.0021** | **−.0041** | 0 / 0 |
| vote deciles 1–10 | −.0007 to +.0008 | −.0009 to +.0008 | about 0 |
| related (non-gold pairs) | +.0001 | +.0003 | about 0 |

- **Most of the bridge value is question-specific.** Per membership, a scored question's own bridges cost about 3–4×
  what other questions' bridges cost, and only they dent gold-door coverage. That's now *shown*: bridges are
  question-conditioned.
- **General bridges still carry some value.** Bridges of other questions cost about 3–5× a typical vote-decile
  membership (−.002 to −.004 per 1,000, against |≤ .0009|), with no coverage effect. That's real but small: a key that
  bridged hops for some question tends to matter for neighbouring walks too.
- **Pruning ordinary memberships is about neutral at these sizes.** No vote decile or related class has a reliable cost
  or gain per 1,000. D3's dev loss (−.028 over 98,606 removals) is larger than these per-1,000 rates suggest. From the
  first table's low deciles (−.0011 and −.0016 per 7,000), the low-vote removals account for **most of** it
  (−.014 to −.023), and the rest is probably the interaction of removing so many at once. That's an inference.
- **The first bridges removed are worth most** (james's observation). Per 1,000, the cost roughly doubles when fewer are
  removed: held-out −.0041 at 282 against −.0021 at 2,000, and scored −.017 at 478 against −.007 at 2,000. So bridges are
  partly redundant with one another. A dreaming reward could let a bridge's marginal value fall with the number of
  parallel bridges for the same hop, which echoes SR-MI's "series beats parallel".
- **Power.** 65 scoring waves, 5 draws per cell. The vote-decile cells' standard errors (about .0005–.003) are as large
  as their means, so single deciles aren't readable. Only the class-level contrasts are.

**What it means for "define good, let dreaming converge toward it."**
- **"Good" is concentrated in bridges, and mostly in a question's own bridges.** The corrected run shows it: a question's
  own bridges are worth 3–4× other questions' bridges, which are worth 3–5× an ordinary membership. The neighbourhood vote doesn't see questions, so it can't rank them, whether pruning or
  adding.
- The signal that *does* find bridges is a question-time decision. Jev, shown a passage's keys and a question, names the
  bridge .70 of the time (SR-BN), against .05–.15 for cosine, ColBERT or rarity.
- So the RL loop that Sirsh's frame describes would learn from **walk outcomes on real questions**. When a named key
  carries a walk to an answer that's later confirmed, that membership's weight rises. That's a reward-driven reweighting
  of bridges, not a structural prune. Pruning ordinary memberships is about neutral, so there's little to gain there.
- That is a design proposal. Testing it needs questions with outcomes (train, with a feedback signal) and a weight term
  in the walk's step. That's not done here.

**Scope.** MuSiQue dev graph only, D3's dev waves and scorer (seen), 7,000 removals per class, 5 draws. "Earned" uses
gold. The concentration is partly built into the gold-door metric. Classes overlap (vote deciles include earned and
related members).
