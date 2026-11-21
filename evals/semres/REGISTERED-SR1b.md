# SR1b: reach in the real regime (registered before any look at its worlds)

*21 Nov 2026, james. Follows RESULT-SR1, RESULT-SR1a and bill's MuSiQue measurements (board M-20261121-133015). $0.*

**Why.** SR1's world was about 15× sharper than MuSiQue.
- The real crossing to hop 2 costs about 0.5 nats. In gen.py it cost 6–28.
- Part of that was my construction:
  - the relations were noise-free;
  - the per-probe Bayes μ swung from −4 to 32 with the landing;
  - the question carried no trace of the answer.
- Noise alone couldn't fix it: the cos gap stayed at about .53 for noise 1 to 6.

**Changes, all calibrated to measurements and not chosen.**
- **One semantic slope**, β = 8.7 nats per cos unit, for passages, links and direction memory. It's bill's logistic
  Bayes slope of hop-2 gold on cos, over 200 MuSiQue dev questions and 3,799 options with bge-small.
- **Links carry their own semantics:** relation + the passages' noise.
- **The question carries the answer's type** with weight ATYPE = 0.8605. That was bisected on 8 discarded seeds
  (9001–9008, calib.py) so that the chain's median cos(x, s) − cos(x, a) equals MuSiQue's .705 − .559 = .146.
- **The world** is SR1's otherwise, with noise 1.0. α = .15 and 25 steps are L1's.

**Seeds.** 31001–31004, never generated before this registration.

**Gate.** Monte Carlo against exact reach on the first world's case B, within 3 s.d. The formula comparison is exact
against exact and needs no gate.

**Pass.** comb (h), or comb@25, ranks a in the top 5 in at least 3 of 4 seeds for **B and for C**. D is reported, not
gated.

**Predictions.**
- **B passes.** At about 1 nat per crossing, the chain is a few steps of moderate share.
- **C passes more weakly.** Hubs drain mass.
- **D fails.** The cluster that looks like the question still wins.
- **Direction memory raises hit-by-25** at a, but less than in SR1, because there is less back-current to remove.
- **The formula's median exact/formula on B is ≤ 1.5.** It is less exact than in SR1, because the softer world has more
  side paths.
