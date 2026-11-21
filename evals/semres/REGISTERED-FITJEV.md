# FITJEV: Jev's door conductance from SR-JW2 and SR-JW3's option sets (registered before the fit; $0, no calls)

- **Model:** logit p_Jev = c + β·cos + γ_rel·[the relation is r1/r2] + γ_type·[the door is of the answer's type] +
  γ_read·[the door is already read].
  - It's least squares on logit p (bill's SR-J form), fitted separately on SR-JW2 (doors hide their links) and SR-JW3
    (doors show them).
  - 95% bootstrap over option sets, with 32 sets each.
- **Predictions:**
  - γ_read is well below 0 in both.
  - γ_type is above 0 in both.
  - γ_rel is larger in SR-JW3 than in SR-JW2, because a door that names its link earns the relation term.
  - β ≈ 1, within bill's [.13, 1.74].
- **No bar.** This is a measurement, reported with intervals. Two things that would surprise me: a γ_read interval that
  covers 0, and a γ_rel that's no larger in SR-JW3 than in SR-JW2.
