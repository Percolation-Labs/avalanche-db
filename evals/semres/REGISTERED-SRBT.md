# SR-BT (registered 21 Nov, before any Jev call or scoring): beyond the name, Jev only where the name leaves twins

*james. REM-1341, on Sirsh's 23:03Z steer ("look into what Jev's passage choice uses beyond the name"). Script
`srbt.py`. The Jev cap is $0.25. Pricing looks: `beyond_look.py` and `beyond_look2.py` (`out/beyond-look*.txt`).*

**Serves.** SR-BN showed that Jev naming the bridge, followed by a free lexical step, gets .68 for hop 2. Jev's own
passage choice gets .84, at about 12× the input. This asks where the remaining .16 comes from, and whether it can be
bought with a fraction of the passage request.

**Pricing ($0, SR-BN's fresh 300, now seen, from Jev's cached passage p's).**
- **Jev's extra is inside twins.** Where more than one option shares a gold bridge key (93 questions), Jev's p picks
  hop 2 .828 of the time. The cheap orders get .376 (qr), .430 (bge cos with the question) and .462 (overlap with the
  question's words outside the read and the name).
- So the second relation ("spouse of", "employer of") is what Jev reads and the cheap stages don't. Example: for "the
  spouse of Hagar", the named set holds Hagar, Keturah, Incest in the Bible and Ellen Hamlin, and only Keturah answers
  "marry after the death of Sarah".
- **Where the name leaves one passage, the lexical step wins.** Gold name alone (170): lexical 1.000, Jev's passage
  choice .906.
- **Approximated pipeline.** Name; then Jev over the named set only, when it has more than one member; k when it's empty.
  This gets .787, using cached p's restricted to the set. That's against .680 for the named lexical step and .843 for
  Jev's choice. It adds about 0.84 passages per question, against 19.

**Task (as SR-BN).** Gold hop 1 is the read. Rank the other 19 passages of the question's pool. Top-1 is hop 2.

**Arms.**
- `k`: SR-K's sum, ties broken by qr.
- `jev`: SR-BN's step (the named key, ties by k then qr). The naming request and the wording are unchanged.
- **`nt`**: S is the set of options sharing Jev's named key K.
  - If |S| = 0, use k.
  - If |S| = 1, take that option.
  - If |S| > 1, a second Jev request with SR-J's passage task over S's passages only, taking the argmax.
- `nt_cut`: as `nt`, with wave 1's passage p's restricted to S. This checks the $0 approximation.
- `jev_pass`: SR-J's passage request over all 19 (the reference).
- `ceiling_k` (gold, labelled): the bridge keys from gold, then the lexical step.

**Waves.**
- Wave 1 (one `ask_many`): naming and passage requests per question, the same requests as SR-BN, sharing its cache.
- Wave 2 (one `ask_many`): the twin requests. They depend on wave 1's names, so they can't be in the same wave.

**Data.** Dev 2-hop positions 0–903 of SR-KB's permutation are used. **Registered set: positions 904–1171** (268
questions), shared with bill's SR-BW, which scores a different task (a cosine entry, not gold hop 1). Both are
registered before either is scored. Stage 0 is positions 600–603 (SR-BN's set, seen): a smoke test, with wave-1
requests cached.

**Primary.** Top-1 hop 2, **`nt − jev`**, paired bootstrap 95% CI. H-T passes if the lower bound is above 0. That means a
Jev reading of only the named twins buys part of the second relation.

**Secondary (CIs).**
- `nt − jev_pass`: how much of Jev's full choice is recovered. Reported, with no bar.
- `nt − k`.
- `nt − nt_cut`: does a request over S alone behave like the full request restricted to S?

**Cost reported.** Wave-2 passages per question against 19. Total input characters, `nt`'s against `jev_pass`'s. Spend.

**Predictions.**
- `nt` is about .78, and `nt − jev` is +.09 or more. H-T passes.
- `nt − jev_pass` is about −.05, with the CI including 0 or just below.
- `nt − nt_cut` is within ±.03.
- Jev's naming is .65–.75 (SR-BN .697).

**Scope.** Given gold hop 1. In-pool, 19 options. MuSiQue 2-hop. Jev's wordings are SR-BN's and SR-J's, unchanged, with
no wording search. The pricing set (SR-BN's 300) is not reused for the claim.

## Amendment 1 (bill's review, before stage 0; readout only)

- `nt` and `jev` pick the same option when |S| ≤ 1. With one sharer it's that option; with none, both fall to k's order.
  So `nt − jev` is carried entirely by the |S| > 1 questions.
- `nt − jev` and `nt − jev_pass` are also reported **within |S| > 1**, with n. The primary is unchanged.

## Amendment 2 (after stage 0, before the wave; procedure only)

- Stage 0 (600–603) had no question with |S| > 1. So wave 2, the twin request, never ran: its code path was untested.
- **stage0t** adds a smoke test: the first 4 questions in SR-BN's set (604–899, seen) whose Jev-named set has 2+ members.
  Their wave-1 requests are cached, so only the twin requests go out live. No arm, bar or draw changes.
