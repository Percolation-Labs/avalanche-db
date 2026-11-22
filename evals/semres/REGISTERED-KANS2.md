# K-ans 2 (registered 22 Nov, before any Jev call): relevant reads, or just fewer of them?

*james. A follow-up to K-ans (#89), from its postmortem and bill's review. Same script
(`meta/lab/worlds/kappa_ans.py --rnd`, p8-subsystems `james/kappa-ans`). The Jev cap is $0.15.*

**Question.** K-ans beat K7 on BEAM by +.032 [+.008, +.052], but its filter enriched gold only 1.6×. Is the gain the
filter's relevance, or just a shorter state (one sentence per wave, where K7 has every read)?

**Control: K-rnd.** One read per wave, chosen at random, with the same count, format, cap and order as K-ans. The pick
is the read at index sha256("20261122" + wave id) mod the wave's size, so the seed is fixed in the script before the run.
That adds one door request per page and no REL requests. K0, K7 and K-ans are all cached.

**Data.** BEAM HELD-OUT only, 601 pages (bill's review: the primary's corpus; MuSiQue had nothing to explain at
K-ans − K7 = −.003). A dry run counted the new requests (see out/kans2-dry.txt).

**Primary.** NDCG@10, paired by question, **K-ans − K-rnd**, using the harness's bootstrap. **H-K2 passes if the lower
bound is above 0:** the relevance filter matters beyond length.

**Secondary.**
- K-rnd − K7: how much of K-ans's gain is length alone.
- K-rnd − K0.
- The gold share of K-rnd's kept reads, which should be about the .115 base.

**Predictions.**
- K-ans − K-rnd is about +.015, and H-K2 is a coin flip.
- K-rnd − K7 is about +.015: roughly half the gain is length. A shorter state means fewer related non-gold sentences,
  which SR-MO3 says don't help.
- K-rnd's gold share is about .115.

**Spend.** 601 door requests, about $0.05. Cap $0.15.

**Scope.** BEAM HELD-OUT replay pages, one seed. A positive H-K2 shows Jev's filter matters on these pages, and a null
says the shorter state is what helps.
