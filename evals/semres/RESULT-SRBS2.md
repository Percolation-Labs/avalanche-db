# SR-BS2 result (22 Nov): rewording the check doesn't stop Jev answering from its own knowledge

*james. Registered in REGISTERED-SRBS2.md (#101) after bill's review (17:29Z: a seed clash with SR-AC was fixed
before any call). Script `srbs2.py`. Outputs: `out/srbs2-stage0.txt`, `out/srbs2-fresh.txt`, `out/srbs2-fresh.json`,
`out/srbs2-handread.txt`. **Spend $0.137** ($0.003 stage 0, $0.133 the 180; cap $0.30).*

**Serves.** Sirsh's 17:07Z goal: return the answer passage with as few passages as possible.

## Results

180 fresh chains (60 each of 2-hop, 3hop1, 4hop1) from the full train file. Jev's full step, with the hop count hidden
from the walk.

| stop | A-last | returned | input | early / exact / late (against H) |
|---|---|---|---|---|
| oracle H | .856 | 3.00 | 32.6k | — |
| oracle H + 1 | .906 | 4.00 | 42.5k | — |
| S-check ("can be answered from these passages") | .772 | **2.43** | 30.1k | 121 / 43 / 16 |
| S-state ("these passages state the answer") | .783 | 2.71 | 33.7k | 114 / 49 / 17 |

- **H-B2 fails. S-state − S-check: +.011 [−.017, +.039].**
- Against oracle H: S-state −.072 [−.122, −.022]; S-check −.083 [−.139, −.033].
- **Measured against the first arrival at the answer passage**, the two checks behave almost identically:

  | | at arrival | before | after | never reached |
  |---|---|---|---|---|
  | S-check | 121 | 27 | 18 | 14 |
  | S-state | 124 | 25 | 17 | 14 |

  S-check replicates SR-BS's look (116 at arrival on the cheap walk).
- "Early against H" is mostly a good thing here. The full step often reaches the answer passage before read H, so a
  stop at arrival counts as early against H while returning fewer passages.
- Stops after one read: S-check 56, S-state 58.

## The hand read (registered: 10 S-state stops before arrival, read in session)

- **In 9 of 10, the answer string is nowhere in what was read.** Examples: "record label of the performer of *From the
  Cradle*" (Atco Records) after reading only the album's passage; "cigars named for the capital of…" (Havana) after one
  passage about Somalis; Puerto Rico's 1898 after a passage on Alaska. Jev stops because it knows the answer, and asking
  whether the passages *state* it doesn't change that.
- In 1 of 10 (*I'd Like to Teach the World to Sing*), the gold answer "America" appears in a read by coincidence.
- One gold label looks wrong (Henry English Read, "America", answer passage about a different person). That's a
  MuSiQue artefact, noted and not corrected.

## What it means

- **The check's early stops are Jev's own knowledge, and wording doesn't move them.** Both checks stop at the right
  read about two times in three, and early about one time in seven. Every early stop we read was one where Jev already
  knew the answer.
- **Whether that's a failure depends on the final reader.** If the LLM that reads the returned set knows the answer
  too, a knowledge stop costs nothing, and A-last can't see that. bill's AC reader on the saved stopped sets (a
  registered secondary) is the test. It's queued for him.
- **Against oracle H, the checks trade about .08 A-last for about 0.5 fewer passages.** SR-AC put a noise passage at
  about −.07 to a reader, so on the reader's measure this may be close to even. Only AC on these sets can say.

## Predictions against outcomes

- **S-state stops early less (about 25 against about 42):** 25 against 27 before arrival. ✗ on the difference. My 42
  came from the cheap walk in SR-BS; on the pass walk, S-check was already at 27.
- **A-last S-state − S-check about +.05, H-B2 passing two times in three:** **+.011, fails.** ✗
- **S-state within about .03 of oracle H:** **−.072.** ✗

## Postmortem

- **What went right.**
  - bill caught the seed clash before any call. Rebuilding every earlier draw also caught a bug in my own exclusion
    logic, verified against SR-BS's and SR-BH's actual ids.
  - The registered hand read is what named the mechanism. Without it, H-B2's null would just say "the wording
    doesn't matter".
- **What I got wrong.** I sized the prediction from the cheap walk's early-stop count (42) and applied it to the pass
  walk, whose count was already lower. And I assumed a wording could tell Jev not to use what it knows. It can't, at
  least not this wording.
- **Mechanism.** A completeness question asked of an LLM is answered with its own knowledge in the loop. Any knob-free
  stop built on "is this enough?" will stop where the model already knows the answer. That's right for Sirsh's goal
  only if the final reader knows it too.
- **Not tested.** AC on the stopped sets (bill, queued). A check that hides the question's entities from the reader,
  to stop knowledge use, which would be a different design.

**Scope.** MuSiQue train chains, one draw of 180, the pass step, H hidden. Production is Sirsh's.
