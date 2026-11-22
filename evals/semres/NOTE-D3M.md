# The dreaming memory term is the wrong lever: D3 already keeps what walks use, and any vote-directed pruning loses to random

*22 Nov 2026, bill. Follows the inertia look (#79), on Sirsh's 11:34Z steer ("the memory term for dreaming if you think
it's the right lever"). $0, no Jev. Gold-blind power check: `d3m_power.py` (`out/d3m-power.txt`). Plus a reading of
D3's own registered results (`evals/dream/d3/d3-low.txt`, `d3-high.txt`). Not registered, because nothing was scored.*

**The plan.** Give D3's vote a memory: exempt from removal the memberships that gold-free walks actually traversed.
Then score on D3's held-out MuSiQue test against D3 and count-matched random removal.

**The power check killed it before any scoring.**
- The memory is 557 (passage, key) memberships traversed by 249 of SR-BW's cosine-entry, Jev-named walks. The 19 SR-BW
  questions that are in D3's test are excluded.
- **D3 removes only 18 of those 557 (3.2%)**, out of 98,606 removals in all.
- Only 12 of the 18 touch a key that D3's test waves offer as a door.
- So protecting used structure can't change D3's outcome: D3 already keeps it. That fits the inertia look, where
  related and earned memberships survive at .94–.98. Growing the memory with more walks scales the 18 roughly in
  proportion, which stays far below the 98,606 removals that drive the result.

**Where D3's harm comes from** (D3's registered MuSiQue test, width-matched AUC):

| edit | test AUC |
|---|---|
| none (G0) | .807 |
| D3, remove **low**-vote memberships (q .05, chosen on dev) | .765 |
| D3, remove **high**-vote memberships (q 16, chosen on dev) | .759 |
| random removal, count-matched to each | .789 / .791 |

- **Removing low-vote and removing high-vote memberships both lose to random removal**, by .02–.03, while random removal
  itself costs little (.807 → about .79).
- I'd expected one direction to be benign: low-vote memberships as non-redundant shortcuts, which would make removing
  them uniquely harmful. That's not supported, because the high-vote direction is just as harmful.
- The reading that fits both is that **a vote-directed removal concentrates damage** on whichever passages or regions
  the vote singles out, while random removal spreads it thinly over a redundant graph. That's an inference from two
  registered results, not a test.

**What it means for "define good, let dreaming converge toward it."**
- The vote doesn't measure what walks need at the margin. Pruning by it, in either direction, does worse than chance, and
  protecting walk-used memberships can't fix that, because they aren't what gets pruned.
- A dreaming operator aimed at "good" needs a target measured *on walks*: the change in a path's resistance to gold
  when a membership is removed, priced on dev walks. A neighbourhood vote is only a proxy for that. That's a
  counterfactual measure per membership: expensive to compute exactly, but sampleable. It's a design question, and not
  yet a test.

**Postmortem.**
- **What went right.** The power check ran before registration and before any scoring, and it stopped a test that could
  only have returned D3's own number. Reading D3's high-vote result, which already existed, answered the follow-up
  without a run.
- **What I got wrong.** The inertia look showed D3 keeps earned and related structure (.94–.98 survival). That should
  have told me directly that a "protect what's used" memory had nothing to protect. I proposed the memory term before
  connecting the two.
- **Scope.** MuSiQue dev graph, one operator (D3) in two directions, D3's own test set. The concentration reading is
  inferred.
