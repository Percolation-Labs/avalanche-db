# SR-JW: does the theory, priced by Jev's measured conductance, predict Jev's own choices on unseen worlds? (registered before any Jev call)

*21 Nov 2026, james. Follows RESULT-SR1c and bill's RESULT-SRJ (#59). This is the carry-over in Sirsh's 13:16 brief.*

**Setup.**
- SR1c's 4 worlds (seeds 41001–41004) are rendered as text by render.py. It's token-free, uses fixed word lists, and
  invents its entity names.
- Each passage names its entity, its type and topic words, and every link ("X is owned by Y.").
- Each question names the start, both relations and the answer's *type* (e.g. "university"). It never uses a word from
  any topic list; that's asserted in the code, following bill's review.

**The two hops of each chain (srjw.py).** Jev reads the question and the passages read so far, and scores each door's passage.
- Hop 1 is at s, with s read, over s's doors.
- Hop 2 is at b, with s and b read, over b's doors, which include the way back to s.
- One batched request per option set, all in flight together. The TASK wording is bill's.

**Theory's prediction, fixed before any call:**
- **Share of a door:** exp(β·cos + γ·[the door's relation is r1 or r2]) normalised over the doors. It uses MuSiQue's β = 1.0
  and γ = 3.7, and bge-small cos(question, passage).
- **Jev's share:** its odds, p/(1−p), normalised.

**Spend.**
- Stage 0 is 1 world × 4 cases × 2 hops = 8 requests.
- Stage 1 is the other 3 worlds, 24 requests.
- The estimated cost is well under $0.01 per stage, capped at $0.05 per stage and probed by the stage-0 run.

**Readouts.**
1. The median log(Jev's share / the theory's share) at the chain door, with a 95% bootstrap over hops. **Pass if the
   interval covers 0**: the theory is calibrated to Jev on worlds neither has seen.
2. The chain door ranked first by Jev, by the theory, by cos and by word overlap (bill's control), plus chance.
3. Each case's chain reach h(a) from Jev's shares against the theory's, via SR1a's formula.

**Predictions.**
- Jev ranks the chain door first at most hops, as on MuSiQue.
- Its share is *above* the theory's, because the theory credits every r1/r2 door equally, while Jev can use the answer's
  type to split two doors with the same relation.
- So readout 1's median is positive, and its interval may sit above 0. That would mean the theory, as measured, is a
  lower bound on Jev, and the missing term is the type match.
- Word overlap ranks the chain door first at hop 2 more often than cos does, because the type word appears in the answer.
