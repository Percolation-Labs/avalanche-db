# MaxSim pricing look: a max over token points keeps a little identity, not enough to register

*21 Nov 2026, james. REM-1341, the last vector route bill named after SR-KB2. This is an unregistered pricing look on
SR-KB's 300 questions (seen; seed 1341 from 41–1252, minus SR-J-R's 40). $0. Script `ms_look.py`.*

**Question.** SR-KB (phrase means), SR-KB2 (holder means) and bill's dropped passage-level max all turned the key's
identity into topic. Does a max over *token* points, ColBERT's MaxSim with bge-small's own token embeddings and no new
model, keep it?

Hop 2 given gold hop 1, out of 19 options. The weight is w_k = 1/(df_k − 1), as in SR-K.

| arm | top-1 | top-3 | MRR |
|---|---|---|---|
| `qr`: question + read, encoded as one text | .393 | .653 | .559 |
| **`k`: lexical, shares rare door keys (SR-K)** | **.577** | **.783** | **.703** |
| `ms_pool`: Σ_k w_k · max over the option's tokens of cos(token, phrase vector) | .357 | .520 | .494 |
| `ms_tok`: Σ_k w_k · MaxSim(phrase tokens → option tokens) | .410 | .580 | .539 |
| SR-KB / SR-KB2's best mean-based probe (for reference) | .33–.37 | | |

**Reading.**
- Token-level max is the best vector route so far: .410, against the means' .32–.37. So it keeps some identity.
- It only matches the text probe (+.017 on top-1, below it on top-3 and MRR), and it stays .17 below lexical identity.
- bge-small's contextual token vectors for "Steve Hillage" in two different passages are similar, but not the same in
  the way the string is. The max picks up other names and words in the same field.
- A pooled phrase vector with a max over tokens (`ms_pool`) does worse than the text probe. The phrase's pooled vector
  is still a topic.

**Not registered.** On seen data the best arm sits at qr's level with no headroom, so there is no gain a registered test
could confirm.

**What this closes for REM-1341, with bill's results.** Five vector routes have now been tried on the same key bundles:
1. phrase means (SR-KB);
2. holder means (SR-KB2);
3. passage-level max (bill, dropped);
4. pooled-phrase max;
5. token MaxSim.

Every one lands between .32 and .41. The lexical key gets .58, and Jev .88 on a random draw. Identity is what carries
the next hop, and bge-small's vector space keeps only a trace of it. For the library, the operation that works is a
lexical one: shared rare keys, weighted 1/(df − 1). Vectors earn their place before it (cosine finds the entry, SR-E)
and after it (ordering a door-found shortlist for Jev to judge).

**Postmortem.** The look took one five-minute $0 run and settled the route without a registration, which was the
intent. A gap worth naming: all five routes used bge-small. A model trained for late interaction (ColBERT itself) might
keep more identity in its token vectors, and that's untested here. It would mean a new model, so it's a question for
Sirsh, not a $0 look.
