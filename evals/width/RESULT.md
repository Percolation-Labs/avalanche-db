# A door's width as budget spent: stage 0 fails, and the rule stops

*18 Nov 2026, bill. Registered first (REGISTERED.md, 0a3d78e). $0 on cards and PR titles (replayed from
decisions.jsonl). MuSiQue dev had no cached decisions, so its trace replays called Jev under today's rule: $0.17.
No default changes.*

## What was asked

Sirsh (M-20261118-150956-f539) asked for the structural side of the floor: count a door's width as budget spent.
The registered rule, `per_read`, opens the door with the highest `P / min(unread targets, budget left)`. It has no
parameter.

## Result (dev, k=10, Jev's recorded P re-used, the probe's E2E_REPLAY)

The simulation's `rank` arm reproduced the recorded walk on every dev question: 100/100 cards, 65/65 PRs, 101/101
MuSiQue. So the check that gates everything else passed.

| dev set | search | today (`rank`) | `per_read` | `per_read` − `rank` [95% CI] | questions below search: rank / per_read |
|---|---|---|---|---|---|
| cards (100) | .340 | .565 | .425 | **−.141** [−.219, −.065] | 3 / 8 |
| PR titles (65) | .508 | .507 | .528 | +.021 [−.031, +.071] | 11 / 11 |
| MuSiQue (101) | .496 | .616 | .602 | −.014 [−.040, +.011] | 6 / 5 |

**Gate: FAIL.** The rule must not fall more than .01 on any corpus; cards falls .141. Stage 1, the live Jev run,
does not happen. `per_target` (P / width, the V0 order, for reference) is worse again: −.168, +.001, −.031.

## Why (the postmortem)

1. **Jev already sees the width.** Every D6 door head states it: "term 'rem 10' · 13 unread", "2 unread beside a
   read one". Jev's P was formed knowing the door's size. Dividing by width again counts it twice.
2. **A door's P is not a per-door probability that can be divided.** On wave 1's doors, gold per read climbs
   steeply with P at every width (yield.txt). On cards, width-1 doors give .002 gold a read at P < .5, .082 at .5–.7
   and .340 at ≥ .7. `per_read` scores a width-1 door at P .45 as .45, and the card's id door (P .71, width 13, gold
   behind it) as .71/5 = .14, so the narrow door wins. The id door is where cards' gain comes from (evals/structure:
   orthogonal gold behind the id term at median width 13). `per_read` opened a door with lower P than today's first
   door on cards: median .63 against .78.
3. **What it does on PR titles is what the structure study pointed to,** opening the width-2 next/merge doors. But
   the +.021 is inside its noise and the rule's cost on cards is 7 times larger. A rule that helps only where its
   direction was seen is a dial.

**What the replay can't see.** A counterfactual walk that leaves the recorded path meets doors Jev never scored;
the simulation never opens them (`unscored doors met`). That can't rescue cards: the loss happens at the first
pick, among wave 1's scored doors, before any unscored door exists.

## What it means for the floor

Width doesn't belong in the pick rule as a divisor. A cost rule would need a calibrated gold-per-read curve in P,
and that is a curve fitted to a corpus, a dial. So it stops here. The floor stays on james's side: search's
continuation as a likeness door that Jev ranks beside the connection doors (M-20261118-151223-efab). There, width
enters only as text, the way it does for every door.

## Kept

- The probe's `E2E_REPLAY` mode (`probe/src/replay.rs`): any pick order re-run on recorded P at $0, with a check
  that it reproduces the recorded walk.
- trace_replay.py: resumable `midb walk --trace` replays, with a spend cap.
- `per_read.patch` for lab.rs: not merged; it's needed only to rerun this.
- `out/sim-*.jsonl`, `score.txt`, `yield.txt`.
