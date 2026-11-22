# K-ans 3 (registered 22 Nov, before any Jev call): does a random one-read-per-wave state keep kappa's MuSiQue gain?

*james. Follows K-ans 2 (#89): on BEAM, the gain over K7 was the shorter state, not Jev's filter. bill said go ahead
(12:34Z). Same script and seed rule (`kappa_ans.py mq --rnd`, index sha256("20261122" + wave id) mod size). The Jev cap
is $0.10.*

**Question.** Before "one sentence per wave" can be offered to Sirsh as the hypothesis for kappa, it has to keep K7's
MuSiQue gain (+.037 over K0). K-ans did (+.034), but on MuSiQue the right sentence may matter where on BEAM only fewer
did.

**Data.** MuSiQue HELD-OUT, 286 replay pages, round 4's harness. The dry run (`out/kans3-dry.txt`) has 272 new door
requests for K-rnd, while K0, K7 and K-ans are cached.

**Primary.** NDCG@10, paired by question, **K-rnd − K0**, using the harness's bootstrap. **H-K3 passes if the lower bound
is above 0:** a random one-per-wave state keeps a gain on MuSiQue.

**Secondary.**
- K-ans − K-rnd on MuSiQue: does the filter matter here?
- K-rnd − K7.
- The differing-pick count and the within-subset contrast (bill's K-ans 2 readout).

**Predictions.**
- K-rnd − K0 is about +.02, and H-K3 is a coin flip.
- K-ans − K-rnd is about +.015. On MuSiQue the kept sentence may need to be the bridge, and REL can find a hop-1 passage.

**Spend.** 272 door requests, about $0.03. Cap $0.10.

**Scope.** MuSiQue HELD-OUT replay pages, one seed.
