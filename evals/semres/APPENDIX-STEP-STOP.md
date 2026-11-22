# Appendix: when to stop

Part of the walk write-up (WRITEUP-WALK.md). A walk returns the passages it has read. It needs a rule for when to
stop reading. Every result below is MuSiQue, 2–4 hops, in a 20-passage pool, scored on whether the answer is in
what was returned.

- **A-last:** the returned set contains the gold last-hop passage. That passage contains the answer in 380 of 380
  checks. It's a lower bound on "the answer is there".
- **AC:** a reader (Jev) picks the sentence that states the answer from the returned set, and a string match or a
  judge checks it. AC is primary whenever a rule changes how many passages come back, because an extra passage
  can raise A-last while hiding the answer from the reader (APPENDIX-READER-CHECK).

## The reference: stop at the hop count

**"Oracle H"** reads exactly as many passages as the question has hops. We can't do that in use, since the hop count
isn't known. It's the bar every stop rule is measured against.

- **Fresh 300 (SR-BS3, SR-BS4):** AC about .78, A-last .86, 3.0 passages, about 31–36k characters.
- **One more read (H+1)** raises A-last by +.060 [+.037, +.087] but lowers AC by −.020 [−.053, +.010] (SR-BS3).

## Rules tried

None uses a tuned constant.

| Rule | How it decides | AC − oracle H | Input | Source |
|---|---|---|---|---|
| S-in | "stop" offered as one option in the step request | — (cheap walk never stopped: 15.5 reads; full step stopped early) | 95.7k (cheap) | SR-BS |
| S-check | Jev: "can be answered from these passages" against "needs a passage not yet read" | **−.073** [−.110, −.037] | ≈ H | SR-BS3, n 300 |
| S-state | Jev: "these passages state the answer" | ties S-check (A-last +.011 [−.017, +.039]) | ≈ H | SR-BS2 |
| R-stop | The reader itself, offered NONE ("no sentence states the answer"); stop when a real sentence wins | **−.033** [−.067, .000] | 1.58× oracle H | SR-BS4, n 300, live |
| first rescue | structural: stop when the walk first needs a rescue | all hops .217 against .506 | — | NOTE-STRUCT-STOP |

**Why S-check stops too early.** Jev judges "answerable" partly from what it already knows. It stops before the
answer passage has been read in 48 of 300 cases. In 67 of its stops the answer passage isn't in the set (SR-BS3).

**Why R-stop is better but costs more.** It asks the question we actually care about: does a returned sentence
state the answer? It's within .033 of the oracle, and its confidence interval touches zero. But it calls the reader
after every read, so input is 1.58× the oracle's like for like. And 6% of walks never stop: 18 of 300 read all 20
passages, and their AC is .167. These are the questions where the reader never finds an answer sentence.

## Where this leaves stopping

- **Cheap and early:** S-check, −.073.
- **Close but dearer:** R-stop, −.033 at 1.6× input, with a 6% runaway tail.
- **A fixed read budget** (for example "read 3") would be a constant, which the project's rules exclude. It's an open
  question to Sirsh, not tested.

The full open question is in OPEN-WHEN-TO-STOP.md.
