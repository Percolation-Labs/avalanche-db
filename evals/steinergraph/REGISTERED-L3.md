# L3: coherence learns one weight per key family (REM-1341, the warping)

*19 Nov 2026, james. Registered before the run. $0, no Jev. Follows L2 (PASS, #50) and bill's K1 (#51). In K1, key
families separate found from not-found walks on cards (number) and PR titles (Beside, phrase), with opposite signs for
number. So L3 has a ceiling above L2's three corpus-wide numbers.*

**What's learned:** start from L2's LC θ per corpus. Each key family f (bill's K1 surface-form families: number,
code, phrase, word) gets a multiplier e^{β_f} on its keys' step weight. Beside doors get e^{β_beside}. Near is
unchanged. So the spread's key weight is (df−1)^θ1 · e^{β_f}.

**Reward:** L2's coherence, unchanged. The strength matrix behind it stays family-blind and fixed, so β can't raise
the reward by rescaling the measure itself. It can only change which passages the spread reaches.

**Fit:** coordinate ascent on mean dev coherence over β_f ∈ {−2, −1, 0, 1, 2}, one family at a time in the order
above. Rounds repeat until nothing changes, at most 3. Ties go to the current value, so L2 stays the default. The
fit is per corpus. That's corpus-specific by design and is flagged as such, and it's allowed only because the
reward uses no gold.

**Arms, all scored on test recall@5 beyond the seeds:**
- **LC:** L2's fit, the baseline here.
- **LC3:** the fitted β on top of LC.
- **LC3-shuf:** the same fit with the reward scored against another question's seeds. It's the join control.
- **LC3-test:** fitted on the test questions' own coherence, which uses no gold. Secondary.
- Q and LQ are reported for reference.

**Bar.** PASS needs both:
1. LC3 − LC > 0 with its 95% bootstrap interval above 0 on at least one set. There are three chances, and the
   result will say so.
2. LC3 − LC's interval isn't wholly below 0 on any set.

**Prediction:** bill's open question is whether coherence moves the weights the way found walks favour. On cards
total coherence doesn't track found (.56), so I expect little there. I expect β_beside up and the number weight
down on PR titles, and nothing on MuSiQue (no code keys, no Beside, low power).

**Constants, named:** the β grid {−2…2} and the 3-round cap are chosen here; everything else is inherited from L2.
If the fitted β sits at a grid edge, that's reported, not chased.

**Postmortem:** every result gets one.
