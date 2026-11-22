# SR-BS4 result (22 Nov): live, the reader-tied stop is close to the oracle at the reader but costs more, not less

*james. Registered in REGISTERED-SRBS4.md (#106); bill said yes (17:51Z). Script `srbs4.py`. Outputs:
`out/srbs4-dry.txt`, `out/srbs4-dry-never.txt`, `out/srbs4-stage0.txt`, `out/srbs4-fresh.txt`, `out/srbs4-fresh.json`.
**Spend $0.286** ($0.003 stage 0, $0.283 the 300; cap $0.50). The exclusion of every earlier Jev study's questions is
asserted in the script.*

**Serves.** Sirsh's 17:07Z goal: a walk that returns the answer and decides for itself when to stop.

## Results

300 fresh chains (100 each of 2-hop, 3hop1, 4hop1), Jev's full step. After each read, the reader request plus NONE; stop
when a real sentence wins, or when the pool of 20 is empty.

| | AC (standard request) | A-last | returned | input chars |
|---|---|---|---|---|
| oracle H | .780 | .860 | 3.00 | 31.7k |
| **R-stop** | **.747** | .853 | **3.56** | **56.2k** |
| *oracle H + one final reader request* (bill's like-for-like row) | | | | *35.6k* |

- **Primary: AC R-stop − oracle H: −.033 [−.067, .000]. H-S4 fails:** not shown within .05; the cost is within .067.
- **Never fired: 18 of 300 (6%).** All 18 read the whole pool of 20. Their AC is **.167**. Excluding them, the
  primary is −.025 [−.060, +.007]. These 18 hit the pool bound (bill's 17:51Z readout), so any cap would bind there.
- **Reads at the stop:** 1 read in 90 walks, 2 in 128, 3 in 31, 4–19 in 33, and 20 in 18.
- **Input is 58% above the oracle walk counted like for like** (bill's note). In use, every walk hands its set to a
  reader once, and R-stop's last reader request is that call. So the comparison is 56.2k against 35.6k = 1.58×, or
  1.77× against the bare oracle walk (`out/srbs4-cost.txt`). Two things drive it: the reader request after every
  read, and the 18 walks that read all 20. On 4hop1 it's 81k against 44k.
- By type, AC R-stop against oracle H: 2-hop .760 against .800; 3hop1 .700 against .760; 4hop1 .780 against .780.
- The judge's yes counts are 13 against 12.

## What it means

- **The reader-tied stop stays close to the oracle at the reader** (−.033 live; −.023 in the replay). It doesn't save
  passages or input. It returns 0.56 more passages and needs 58% more input like for like, because it pays a reader request after
  every read, and because its hardest 6% run to the end of the pool and still score .167.
- **So no knob-free stop yet matches simply knowing the hop count, on any of reader accuracy, passages or cost.**
  - The knowledge check (S-check) is cheap but stops early: −.073.
  - The reader-tied check is accurate but costs more and runs away on hard questions: −.033, at 1.6× the input like
    for like.
- **The never-fired 18 are where a stop rule has to say "give up".** The reader can't find the answer even after 20
  passages (AC .167). A rule that returns the best set so far, rather than reading on, needs either a constant (a read
  cap) or a signal for when more reading stops helping. Neither is tested.
- **For Sirsh's goal, the practical reading:** the reader-tied stop is the best knob-free rule we have on accuracy,
  and the worst on cost. Whether a fixed read budget is acceptable instead (a constant, which his rules exclude unless
  he decides otherwise) is his call.

## Predictions against outcomes

- **AC R-stop − oracle H about −.02, H-S4 passing about half the time:** **−.033, fails.** ✗ narrowly.
- **Never fired about 10%, AC about .30:** **6%, AC .167.** ✗. Fewer, and worse than predicted: more passages didn't
  help the reader on these.
- **Mean returned about 4:** **3.56.** ✓ roughly.
- **Cost $0.30–0.35:** **$0.283.** ✓

## Postmortem

- **What went right.**
  - The replay (#105) predicted the live gap within .01.
  - bill's note to price the never-fired tail kept the cap honest.
  - His note to count walks at the pool bound names where a cap would bind.
- **What I got wrong.** I framed the reader-tied stop as a way to return fewer passages, carried over from S-check's
  2.6. Live, it returns more, because its stops happen on arrival or later, and the never-fired walks read everything.
  I should have predicted the input cost from the per-read reader request, which was knowable from the design.
- **Mechanism.** NONE wins until the reader sees an answer sentence. That's usually on arrival at the answer passage,
  so the stop is accurate. But it costs one reader request per read, and on the reader's hardest questions NONE never
  loses.
- **Not tested.** A stop that also gives up: return the best set when another read doesn't change the reader's choice.
  That needs care not to smuggle in a constant.

**Scope.** MuSiQue train chains, one fresh draw of 300, the pass step, H hidden from the walk. Production is Sirsh's.
