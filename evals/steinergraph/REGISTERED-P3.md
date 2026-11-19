# P3: does "the seeds became connected" tell the walk it has found the answer?

*19 Nov 2026, james. Registered before any run. $0, no Jev. From Sirsh's 12:36Z item 3 and 12:40Z note
(M-20261119-123655-2e56, M-20261119-124001-cd37): once the walk joins its seeds through the Steiner graph it has in
effect percolated, and coherent signals meeting from separate starts are evidence of meaning. The measure must beat
chance, so that generic hubs can't fake it.*

**Data:** the recorded k=10 test walks (evals/width): cards 150, PR titles 93, MuSiQue 150, on the graphs as built
(d1 dumps). R_w is the read set after wave w: search's 5 seeds, then the walk's reads. Links are direct door links
between passages (a shared key under the cap, Beside, Near). The induced graph is R_w's passages and the links among
them.

**Signals per walk and wave (structure only; no gold, no question):**
- **joined:** the share of seeds in the largest connected component of R_w's induced graph that holds a seed.
- **component:** that component's size.
- **coherence:** the induced graph's link count divided by its expectation under a degree-preserving null,
  Σ_{u<v∈R} d_u·d_v / (2m), with d each passage's degree in the full graph and m its link count. Hubs are expected to
  link, so they don't raise it.
- **raw links:** the induced link count (the hub-prone baseline).
- **mean degree:** R_w's mean degree (the "generic hubs" baseline).

**Outcome:** gold found, meaning R_final holds at least one gold passage beyond the seeds. Recall beyond the seeds is
secondary.

**Measures:**
1. **Primary:** AUC of each signal at the final wave for gold found, per set, with a 95% bootstrap interval over
   walks.
2. **Search, no walk:** the same AUC on search's top 10 as the read set. This says whether the signal works where
   only likeness acts, or needs the walk's connection.
3. **Wave by wave:** per wave, the share of walks with joined = 1 against the share that have found gold so far, and
   the gain in joined at the wave gold is first read, against waves that read no gold.
4. **Control, shuffled reads:** for each walk, the walk's reads replaced by an equal number of random passages within
   1 door of the seeds. Coherence there should not predict, since gold is only rarely among them.

**Bar:** coherence is evidence of the answer if its final-wave AUC is ≥ .65, with the interval above .5, on at least
two sets, and above both raw links and mean degree on those sets. Joined and component are reported against the same
bar.

**Postmortem:** every result gets one.
