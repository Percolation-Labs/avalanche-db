# SR-JW2: Jev's door choices on fairly rendered worlds (registered before any Jev call; bill reviews first)

*21 Nov 2026, james. Follows RESULT-SRJW, whose hop-2 result is withdrawn after bill's review (board M-20261121-135227).*

**bill's three fixes.**
1. **The type isn't stated.** A passage is "<Name> is known for its <three topic words>." There is no "is a <type>"
   sentence. b gets two decoys (gen.world(decoys=True)):
   - one of the answer's type, by another relation;
   - one by the needed relation r2, of another type.
   So only a is both.
2. **String readers are registered control rows.** All are computed at $0 and shown before any call. Uniquely first at hop 1 / hop 2, of 16:
   - type word literal in the door: 0 / 0
   - relation phrase or start name in the door: 0 / 0
   - a read sentence links here to the door by a needed relation: 7 / 0
   - the same, plus the generator's own type dictionary (topic word lists): **4 / 9**
3. **Doors show only their own text.** Links become visible only once a passage is read (render.render2).

**Worlds.** Fresh seeds 51001–51004, with SR1b's ATYPE and noise. There are 4 cases × 2 hops = 32 option sets, and 7 doors at each hop 2.

**Everything else is SR-JW's:**
- the TASK wording;
- one batched wave per stage;
- the theory's shares, exp(β·cos + γ·[the relation is r1 or r2]) with MuSiQue's β = 1.0 and γ = 3.7;
- the readouts, now **split by hop** (SR-JW's postmortem).

**Spend.** Stage 0 is 8 requests (seed 51001) and stage 1 is 24. Each is about $0.001, capped at $0.05.

**Bar (hop 2, where the relation has to be read and the type inferred).** Jev's chain door is uniquely first in more
cases than the dictionary reader's 9 of 16. If it is, Jev reads the relation from what it has read *and* infers the type
from the door's words, without the generator's word lists.

**Also reported:** the per-hop log(Jev/theory) with intervals, and the way-back share at hop 2.

**Predictions.**
- Jev is uniquely first at hop 2 in at least 12 of 16. The type inference (orchestra, concert → composer) is world
  knowledge.
- The hop-1 deficit against the theory repeats (Jev hedges before any read).
- The way-back share stays well under the theory's, because s is read.
