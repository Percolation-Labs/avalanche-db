# What a door membership is worth to walks: almost all the value is in the 1.5% that bridge consecutive hops

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

**What it shows.**
- **Value is extremely concentrated.** Removing 7,000 bridge memberships costs .054 AUC and 15 points of gold-door
  coverage. Removing 7,000 from any other class costs between +.002 and −.004. Per membership, bridges are worth
  about 20–50× the rest. **A caveat about the metric:** a "gold door" is defined by keys linking the read set to gold, so
  some of this concentration is built into the score. The size of the gap is still the point.
- **Pruning can only lose, a little at a time.** No class has a reliably positive value from removal. The low-vote deciles
  cost about −.001 to −.002 per 7,000. Over D3's 98,606 removals that adds up to roughly its dev loss (−.028). Pruning
  buys nothing for walks here.
- **D3's vote doesn't find the bridges either.** D3's add arm (`d3add.py`, registered) builds hubs from strong mutual
  votes. On MuSiQue test it gets .808 against .807 unedited and .809 for random hubs: nothing.

**What it means for "define good, let dreaming converge toward it."**
- **"Good" is concentrated in bridges, and bridges are question-conditioned.** A bridge is the key that links one hop to
  the next *for some question*. The neighbourhood vote doesn't see questions, so it can't rank them, whether pruning or
  adding.
- The signal that *does* find bridges is a question-time decision. Jev, shown a passage's keys and a question, names the
  bridge .70 of the time (SR-BN), against .05–.15 for cosine, ColBERT or rarity.
- So the RL loop that Sirsh's frame describes would learn from **walk outcomes on real questions**. When a named key
  carries a walk to an answer that's later confirmed, that membership's weight rises. That's a reward-driven reweighting
  of bridges, not a structural prune. In this corpus the room is large (bridges are 1.5% of memberships and carry most
  of the value), and pruning the rest is at best neutral.
- That is a design proposal. Testing it needs questions with outcomes (train, with a feedback signal) and a weight term
  in the walk's step. That's not done here.

**Scope.** MuSiQue dev graph only, D3's dev waves and scorer (seen), 7,000 removals per class, 5 draws. "Earned" uses
gold. The concentration is partly built into the gold-door metric. Classes overlap (vote deciles include earned and
related members).
