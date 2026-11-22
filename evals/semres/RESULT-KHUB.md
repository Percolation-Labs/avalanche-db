# K-hub result (22 Nov): a structure-chosen kappa read ties a random one

*james. Registered in REGISTERED-KHUB.md, reviewed by bill (16:02Z), with a stage-0 addendum and a revised prediction
committed at 16:05Z, before any score. Script p8 `kappa_ans.py --rnd --hub` (#861). Outputs: `out/khub-picks.txt`,
`out/khub-beam.txt`, `out/khub-mq.txt`. Jev spend $0.083 ($0.047 BEAM, $0.036 MuSiQue). A first attempt was
refused before any call because the Jev key wasn't bound to Jev's origin, and cost $0.*

**Serves.** The structure-dependent kappa state, as Sirsh directed at 15:52Z. Can the graph choose kappa's one read per
wave at no Jev cost?

## Results

NDCG@10, paired by question. The K0, K7, K-ans and K-rnd rows are reproduced exactly from the cache.

| state | BEAM | MuSiQue | gold share of picks (BEAM / MQ, per question) |
|---|---|---|---|
| K0, no state | .692 | .768 | — |
| K7, every read | .669 | .805 | — |
| K-ans, Jev's pick per wave | .702 | .802 | .145 / .208 |
| K-rnd, a random read per wave | .698 | .785 | .145 / .052 |
| **K-hub, the walk's most-linked read per wave** | **.696** | **.784** | **.108 / .026** |

- **H-KH1 fails, as revised at stage 0.** On MuSiQue, K-hub − K-rnd is −.001 [−.031, +.023]. Within the 259 pages
  where the picks differ, it's also −.001.
- **H-KH2 passes.** On BEAM, K-hub − K0 is +.004 [−.012, +.020]. The length fix holds with the structural pick, as it
  did with every one-per-wave arm.
- Against K-ans: −.005 [−.023, +.010] on BEAM and −.018 [−.050, +.008] on MuSiQue.
- K-hub − K0 on MuSiQue is +.016 [−.007, +.033], the same as K-rnd's +.017.

## What it means

- **Centrality isn't the bridge.** The read most linked to what the walk already holds is less often gold than a
  random read on both corpora (.108 against .145, .026 against .052). It is rarely the wave's highest-degree read (7 of
  83, 3 of 77), so this isn't hub-picking. It's the walk's own neighbourhood, as bill named before the scores: on a
  2-hop walk, the hop-1 cluster already gathered; on BEAM, the dense topic rather than the piece asked for.
- **Too few differing waves to tell whether gold share matters between them.** On MuSiQue, K-hub has half random's
  gold share at the same NDCG, but that's 2 gold picks against 4 of 77 waves. The only arm whose gold share differs by much is K-ans, 4× random,
  and it's the only one above random (+.017, n.s.). So the realistic reading on MuSiQue is unchanged: we can't rule
  out that gold content in the sentence is the lever, and nothing cheaper than Jev's pick has found it.
- **For the kappa hypothesis.** It's still the same two options for Sirsh: Jev's pick per wave, or a cheap pick that
  gets about half of MuSiQue's gain. The structural pick is no better than random, and costs more code.

## Predictions against outcomes

- **Registered:** BEAM hub gold share above random. Outcome: below (.108 against .145), a miss found at stage 0.
- **Registered:** MuSiQue K-hub − K-rnd about +.01, a coin flip. **Revised at 16:05Z:** ≤ 0. Outcome: −.001.
- **Registered:** BEAM K-hub − K0 about +.01. Outcome: +.004, passing H-KH2.

## Postmortem

- **What went right.** bill's stage-0 request (gold share at $0 before the call) predicted the null before the
  spend. It also exposed a pooled-gold error in K-ans 2, now corrected in place (RESULT-KANS2.md, RESULT-KANS3.md).
  The run confirmed the length fix under a third pick. It couldn't tell whether gold share matters between the random
  and structural picks: too few waves differ.
- **What I got wrong.**
  - I reasoned that "gold shares names with gold", so the centre of the walk would be gold. But the walk's reads are
    mostly non-gold (95–99% on BEAM), so the centre of the walk is the centre of the non-gold.
  - I should have computed the picks' gold share before writing the prediction, not after. It was $0.
  - The first run failed on the credential binding, which every earlier Jev run set. Copying the run line from the
    previous result's `out/` would have avoided it.
- **Mechanism for the null.** The structural pick looks backward at what the walk holds. The pick that helps on
  MuSiQue needs to look forward to the next hop, which on this evidence only the question-conditioned Jev request
  does. A structural pick conditioned on the question would be relevance again, not structure.
- **Not tested.** A forward-looking structural pick (a read linked to the most *unread* passages) was the obvious
  alternative and wasn't run. On this evidence it's unlikely to find the bridge without the question either.

**Scope.** Replay pages, one seed, two corpora. These are not live walks.
