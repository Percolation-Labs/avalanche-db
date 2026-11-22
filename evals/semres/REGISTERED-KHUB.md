# K-hub (registered 22 Nov, before any Jev call): can graph structure choose kappa's one read per wave?

*james. Follows K-ans 1–3 (#89). Sirsh at 15:52Z: carry on with the structure-dependent kappa state, and make the
call with a small experiment instead of waiting. The script is p8 `meta/lab/worlds/kappa_ans.py --rnd --hub`
(branch james/k-hub). The Jev cap is $0.30.*

**Question.** One read per wave removed kappa's loss on BEAM, whichever read was kept. On MuSiQue, Jev's pick
(K-ans, +.034 over K0) did about twice as well as a random pick (+.017), but the gap is inside the noise. Jev's pick
costs one extra request per wave, and on BEAM it held *less* gold than random (.181 against .229). Can the graph
choose the read for free, and choose it better?

**Arm K-hub.** It picks the same way as K-ans and K-rnd: one read per wave, in the same `relations` format, cap and
order as that corpus's K7. The kept read is the one in the wave most linked to every other read the walk has made
up to and including that wave:

    hub(wave i) = argmax over d in wave i of  Σ_{s read in waves 0..i, s ≠ d}  Σ_{n ∈ names(d) ∩ names(s), df(n) ≥ 2}  1/(df(n) − 1)

- `names` are the ingestion-time entity names, the same ones the doors use (BEAM `beam-ents.json`, MuSiQue
  `musique-ents.json`).
- `df` counts each name over the fixture.
- The 1/(df − 1) weight is the lexical door k's, with no cap and no new constant.
- Ties go to the larger sha256("20261122" + wave id + doc id), fixed before the run.
- The pick never sees the question, the gold or the door options. It reads what the walk has gathered and keeps the
  read at its centre.

**Why this read.** A many-piece BEAM question's gold shares names with other gold. A MuSiQue bridge passage shares
its entity with the hop-1 reads and the hop-2 target. If the read at the centre of the walk is more often gold or the
bridge than a random one, K-hub should match K-ans without the extra request.

**Data.** The same replay pages as K-ans 2 and 3: BEAM HELD-OUT, 601 pages, round 5's harness; MuSiQue HELD-OUT,
286 pages, round 4's. The dry run (`out/khub-dry.txt`) shows 525 new door requests on BEAM and 235 on MuSiQue. K0,
K7, K-ans and K-rnd are cached.

**Primary.** NDCG@10, paired by question, using the harness's bootstrap.
- **H-KH1 (MuSiQue): K-hub − K-rnd, lower bound above 0.** Structure picks better than chance where the sentence may
  matter.
- **H-KH2 (BEAM): K-hub − K0, upper bound above 0** (not significantly worse than no state). The length fix holds
  under the new pick.

**Secondary.**
- K-hub − K0 on MuSiQue.
- K-hub − K-ans on both corpora.
- BEAM gold share of the K-hub picks, against .181 (K-ans) and .229 (K-rnd).
- The count of pages where K-hub's pick differs from K-rnd's in an earlier wave, and K-hub − K-rnd within those
  pages.

**Predictions.**
- BEAM: K-hub − K0 is about +.01, like the other one-per-wave arms (length is the lever), so H-KH2 passes.
- BEAM gold share is above random's .229, since gold pieces share names.
- MuSiQue: K-hub − K-rnd is about +.01. H-KH1 is a coin flip at best: K-ans − K-rnd was +.017 and not significant,
  and K-hub has to beat that size to clear zero.

**What follows.** If H-KH1 passes, a free structural pick is offered to Sirsh as the kappa hypothesis in place of
Jev's pick. If K-hub ties K-ans within noise on both corpora, the cheaper pick is the default hypothesis (equal
evidence, lower cost). If K-hub falls below K-rnd, centrality picks something systematically off the answer, which
the postmortem names.

**Spend.** 760 door requests. The K-ans 2 and 3 rates give about $0.09. Cap $0.30.

**Scope.** Replay pages, one seed, two corpora. These are not live walks.
