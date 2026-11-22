# SR-BS3 result (22 Nov): on fresh questions the answerability stop costs the reader about 7 points; SR-BS2 was optimistic

*james. Registered in REGISTERED-SRBS3.md (#103) before any Jev call; bill said yes at 17:40Z, and his three notes were
applied before the run. Scripts `srbs3.py` and `srbs2_ac.py`. Outputs: `out/srbs3-stage0.txt`, `out/srbs3-fresh.txt`,
`out/srbs3-fresh.json`, `out/srbs3-ac.txt`, `out/srbs3-fresh-ac.json`, `out/srbs3-ac-extra.txt` (string only and by
type, $0). **Spend $0.235** ($0.003 stage 0, $0.182 walks, $0.050 AC; caps $0.40 and $0.15).*

**Serves.** Sirsh's 17:07Z goal. It confirms or rejects SR-BS2's "a knob-free stop isn't distinguishable from the
oracle at the reader".

## Results

300 fresh chains (100 each of 2-hop, 3hop1 and 4hop1), Jev's full step, with the hop count hidden from the walk.

| stop | AC (string or judge) | judge yes | A-last | returned | input |
|---|---|---|---|---|---|
| oracle H | .783 | 15 | .857 | 3.00 | 31.0k |
| oracle H + 1 | .763 | 13 | .917 | 4.00 | 40.4k |
| **S-check** | **.710** | 12 | .777 | **2.59** | 30.2k |

- **Primary: AC, S-check − oracle H: −.073 [−.110, −.037]. H-S3 fails, and the CI excludes 0.** By the registered
  consequence ("if the point estimate is much worse, SR-BS2's reading was optimistic"), the stop rule costs the reader,
  about 7 points for about 14% fewer passages.
- String only: −.063 [−.103, −.023]. The judge's yes counts are close (12 against 15), so leniency isn't the
  difference.
- A-last: −.080 [−.123, −.040], the same as SR-BS2's −.083. **The gold measure replicated, and the reader measure
  didn't.**
- By type, AC S-check − H: 2-hop −.040 [−.090, +.010]; 3hop1 −.110 [−.190, −.050]; 4hop1 −.070 [−.140, .000].
- S-check stops: at the answer passage's arrival 201, before it 48, after it 32, never reached 19. Stops after one read:
  98. When it stopped before arrival, the reader was still right in 12 of 48.
- **One more passage hurts the reader slightly:** AC H + 1 − H is −.020 [−.053, +.010], while A-last gains +.060
  [+.037, +.087]. The extra passage adds the answer passage sometimes and rivals more often (A-last = 1, AC = 0 in 50
  at H + 1, against 30 at H).

## What it means

- **SR-BS2's "not distinguishable" was the lucky end of its interval.** On 300 fresh questions the reader pays about 7
  points when Jev decides when to stop. The cause is the one SR-BS2 found: early stops on Jev's own knowledge. Here
  they're more frequent, especially on 3-hop (81 of 100 stop before the hop count).
- **The reader prefers fewer passages, but not fewer than the answer needs.** H + 1 loses a little at the reader
  through rivals, and S-check loses more through early stops. Oracle H is the best of the three at the reader, which
  leaves a stop rule that knows the answer passage is in hand as the open problem.
- **A-last and AC diverge most when sets grow.** At H + 1, A-last rises by .06 and AC falls by .02. Sirsh's measure
  ("contained") and the reader's ("usable") can rank sets in opposite directions. That's for him to know, since he
  chose "contained".

## Predictions against outcomes

- **AC S-check − H about −.03, H-S3 failing two times in three, the point within SR-BS2's CI:** **−.073, fails,**
  just outside SR-BS2's CI (−.072 lower bound). ✗ on the size.
- **2.4 passages against 3.0:** **2.59.** ✓ roughly. **Stops at arrival two in three:** **201 of 300.** ✓

## Postmortem

- **What went right.** We confirmed before claiming. SR-BS2's summary to Sirsh said "not distinguishable at n = 180,
  not equal", and this run is why that wording mattered. bill's note fixed the meaning of a fail before the run, and
  the result is a clear fail on the other side, so there's nothing to interpret after the fact.
- **What I got wrong.** I took SR-BS2's point estimate (−.028) as the expected value, though its CI reached −.072, and
  sized the prediction from it. The honest prior was the A-last gap (−.08), which replicated exactly. I also reported
  SR-BS2 to Sirsh as "the first stop rule that holds up on his measure" in the result file, and that was premature.
- **Mechanism.** The check stops on Jev's knowledge (SR-BS2's hand read: 9 of 10 early stops had no answer string in
  the reads). On fresh questions the reader can't recover those, because a reader credited only for a sentence in the
  set has nothing to pick.
- **Not tested.** A stop that asks whether a *specific returned sentence* states the answer (AC's own request) rather
  than whether the set answers the question. That ties the stop to what the reader can use, not to what Jev knows.

**Scope.** MuSiQue train chains, one draw of 300, the pass step, H hidden. Production is Sirsh's.
