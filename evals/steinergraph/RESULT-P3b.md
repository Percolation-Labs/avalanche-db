# P3b result: convergence on narrow links is evidence of the answer on MuSiQue only

*19 Nov 2026, james. $0, no Jev. Registered in REGISTERED-P3b.md (fea5030) before the run. Code: p3.py --narrow W.
Output: out/p3b.txt (widths 5, 2 and 10).*

**Verdict: FAIL on the bar (it needed two sets); a corpus-specific positive on MuSiQue.** Narrow links are Beside, or a
shared key held by at most 5 passages. Test AUC for gold found, final wave, 95% bootstrap:

| width 5 | cards (135) | PR titles (87, 11 found) | MuSiQue (133) |
|---|---|---|---|
| converged (seeds in one narrow component) | .485 [.390, .575] | .662 [.496, .823] | .580 [.488, .668] |
| narrow coherence (over the degree null) | .535 [.441, .636] | .653 [.454, .847] | **.739 [.646, .816]** |
| narrow links, raw | .534 | .623 | .733 |
| mean narrow degree (hub baseline) | .480 | .530 | .553 |

**Added measure (bill, REM-1341):** Spearman between narrow coherence and the walk's recall beyond the seeds is
+.130 / +.175 / +.475. This is the number a gold-free dreaming reward would need. It is moderate on MuSiQue and weak on
p8.

**Sensitivity (reported, not barred):**
- **Width 10:** MuSiQue coherence .759 and PR .690 [.506, .860].
- **Width 2:** MuSiQue .661, PR .676.
- **Cards** stays between .54 and .57 at every width.

**Mechanism.**
- *MuSiQue:* the seeds are almost never narrowly joined at wave 0 (2%). A walk that reads gold adds rare-entity links,
  because the gold paragraphs of a hop chain share a named entity that few other paragraphs hold. So narrow links
  appear only when the chain is read. Hubs don't fake it: the degree baseline sits at .553.
- *Cards:* gold commits name the card's id, and that key is held by many passages (board logs, team notes), so it is
  wider than 5. Narrow links among the reads come from commit adjacency (Beside), which the walk reads whether or not
  it holds gold.
- *PR titles:* only 11 of 87 walks found gold, so the interval is ±.19. The point estimates (.65 to .69) are where
  MuSiQue's would need to be, but this sample can't show it.

**Postmortem.**
1. Narrowing the links fixed P3's tautology. The degree null then does its job: mean degree never predicts.
2. Coherence works where the Steiner graph is a chain through rare entities (MuSiQue). It doesn't where the shared
   structure is a common identifier or adjacency (cards). That fits Sirsh's framing: coherence is evidence when votes
   come from separate starts and agree on something specific.
3. As a reward for dreaming, without gold, it is plausible on MuSiQue (ρ .475), which is exactly where L1's
   gold-trained weights failed. It is too weak to train on for p8.
4. I'd accept a registered P3c only with a larger PR sample (the k=20 walks, or dev and test pooled), not by moving
   the width.
