# SR-TW: does a relational null stop relational twins? (registered before scoring)

*21 Nov 2026, james. THEORY-SR item 3. $0, token-free, with no Jev calls. bill reviews this before it's scored.*

**Serves.** The graph measure we're after, call it coherence or a repair reward, has to credit the relations a question
actually selects. It can't credit any region where those relations happen to sit. In SR1c, a cluster joined to s by r1
took the relational bonus and outranked the answer in 2 of 4 worlds. The surprise-coherence null was matched on degree,
so it discounts hubs but not this. If a null priced on the relational term can tell selection from presence, then
"surprise over a relational null" is the coherence reading to carry over to the decider. If it can't, we learn where
relations stop helping and the question's type has to take over.

**Walk.** This is SR1c's walk, unchanged:
- Jev's measured conductance: β 1.0, γ 3.7.
- ATYPE .8605, noise 1.0, α .15.
- Exact reach h from s.

The seeds are fresh: 61001–61004.

**Relational null.** The null is the same walk with γ = 0.
- Why that's the null: average each link's bonus over random relation labels. Every conductance then scales by the same
  factor, which cancels in P. So the γ = 0 walk is the mean-field null over labels exactly, not an approximation chosen
  here.
- rel(v) = log h_γ(s→v) − log h_0(s→v).
- relKL(v) = h_γ(v) · rel(v), v's term in KL(h_γ ‖ h_0).
- Neither has a parameter.

**Arms:**
- raw (SR1c's comb).
- rel.
- relKL.
- deg and degKL: cs.py's degree null, the mean h_γ from the starts that have s's degree.

**Conditions on D**, applied after `gen.world` so the world's draws don't change. Cases A–C run on the clean world only.
- **clean:** gen's case D.
- **labels:** every link inside the cluster gets r1 or r2 at random. The relations are present everywhere but select
  nothing.
- **chain:** lure0–lure1 becomes r2, and lure0's other cluster links get relations the question doesn't name. This builds
  an exact relational twin of s –r1→ b –r2→ a.

**Theory, stated before the run.**
- The current split at a node depends only on the ratios of its doors' conductances.
- An r1 or r2 label raises h at v only where it lifts v's door against unlabelled siblings. That's selection.
- In clean D, rel(lure) ≈ the lift at s's r1 door, the same as rel(b). a gets that lift plus b's r2 lift. So rel ranks a
  above every lure.
- In labels, every door in the cluster is lifted, so rel(lure) doesn't change.
- In chain, lure1 gets the same two lifts as a, so the relations alone can't tell them apart. The only separation left
  is similarity, and the lures were built to look like x. So that condition should fail.
- Pure rel grows with every lifted hop. Far passages at the end of long matched chains could then outrank a, so I expect
  rel alone to be noisy. relKL weights by reach to stop that.

**Primary bar (relKL).**
- On D clean plus D labels (8 world-cases), relKL ranks a above every lure in at least 7 of 8 and in the top 5 in at
  least 6 of 8.
- And on A–C (12 cases), relKL's top-5 count is at least raw's count minus 1. The relational null must not cost the
  cases raw already wins.

**Predictions:**
- raw ranks a above every lure in at most 4 of 8 on D clean plus labels (SR1c had 2 of 4 in top 5 on clean).
- labels doesn't move rel or relKL ranks by more than 2 at a on any seed.
- deg doesn't fix D. Its random starts rarely reach the cluster, so the lures look surprising: at most 4 of 8 above
  every lure.
- **The limit, predicted to fail:** in D chain, relKL ranks some lure above a in at least 3 of 4.

**What a pass would mean.** A relational null separates relations that are present from relations that are selected.
That makes it the coherence null for the relational twins that the degree null misses. The chain condition shows what
it doesn't do: a full relational twin needs the question's type (the β·cos term through ATYPE) or some other evidence.
Carrying this over to the decider would mean SR-J's fitted γ. The null is then "Jev without its next-hop term", so the
carry-over test would need the γ = 0 Jev prices, which we have from SR-J's fit. That's not part of this run.

**Not in scope.** Coverage against collision across the three probes. MuSiQue. Any Jev call.
