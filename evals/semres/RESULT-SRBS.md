# SR-BS result (22 Nov): neither knob-free stop rule works, and S-check stops when the answer string is in view

*Registered by bill in REGISTERED-SRBS.md (#96), with amendment 1 (the S-check task line, STOP_OPT on the rescue
request when the read has no keys, the draw shrunk to 60 per type to fit the cap). Script `srbs.py` (james, #97).
Outputs: `out/srbs-dry.txt`, `out/srbs-stage0.txt`, `out/srbs-fresh.txt`, `out/srbs-fresh.json`, and
`out/srbs-check-why.txt` (post hoc, $0). **Spend $0.400** ($0.015 stage 0, $0.385 the 180; cap $0.50). A trajectory
ends once S-in, S-check and H + 1 have all fired. Where S-in never fires, it runs to the 20-read bound, and that is
where most of the spend went.*

**Serves.** Sirsh's 23:03Z ask, a full walk. SR-BH and SR-BH2 gave the walk its hop count. This asks whether it can
stop on its own.

## Results

180 fresh MuSiQue train chains (60 each of 2-hop, 3hop1 and 4hop1), with the hop count H hidden from the walk.

| | all hops | reads | input chars | all hops per 10k chars | early / exact / late |
|---|---|---|---|---|---|
| cheap, oracle H | .506 | 3.00 | 25.6k | .198 | — |
| cheap, oracle H+1 | .683 | 4.00 | 33.9k | **.201** | — |
| cheap, S-in | .839 | 15.5 | 95.7k | .088 | 23 / 9 / 148 |
| **cheap, S-check** | **.300** | 2.62 | 26.6k | .113 | **106** / 43 / 31 |
| pass, oracle H | .439 | 3.00 | 32.0k | .137 | — |
| pass, oracle H+1 | .650 | 4.00 | 41.7k | .156 | — |
| pass, S-in | .378 | 4.59 | 37.8k | .100 | 92 / 32 / 56 |
| pass, S-check | .194 | 2.27 | 26.9k | .072 | 126 / 35 / 19 |

- **Primary: H-S fails. cheap × S-check − cheap × oracle(H): −.206 [−.283, −.133].**
- pass × S-check − oracle(H): −.244. cheap × S-in: +.333, but it reads 15.5 of 20 passages, so it isn't a stop
  rule. pass × S-in: −.061 [−.144, +.017].
- Under the same stop rule, the cheap walk still beats the pass walk: S-check +.106 [+.061, +.156].
- **Sanity checks.**
  - S-check stops after one read in 63 of 180 questions (35%), on both walks. Every chain needs 2 or more reads.
  - S-in wins at step 1 on 17 cheap walks and 54 pass walks.
- **The oracle(H) arms are consistent with SR-BH on its types.** 3hop1 cheap .483 against SR-BH's .51, pass .367
  against .44; 4hop1 cheap .317 against .28, pass .250 against .19. The STOP_OPT option on the step requests didn't
  visibly move the walks.

## What S-check was judging (post hoc, $0)

**S-check's confusion table on the cheap walk** (each check: decision × all hops read):

| | complete | incomplete |
|---|---|---|
| stop | 53 | 126 |
| continue | 58 | 235 |

**It stops when the answer string is in view.**
- With the gold answer (or an alias) somewhere in the reads, it stops at 146 of 232 checks (.63). Without it, at 33 of
  240 (.14).
- Of its 126 'stop, incomplete' decisions, 93 had the answer string in the reads already. The walk had reached the
  passage that states the answer, often the last hop by a skip or directly from the entry, without the chain that
  supports it.

**Scored by 'answer string in the reads at the stop'** (a weak proxy: a string match isn't an answer):

| | oracle H | oracle H+1 | S-in | S-check |
|---|---|---|---|---|
| cheap | .867 | .939 | .983 | .817 |
| pass | .928 | .950 | .906 | .817 |

- S-check is still below the oracle arms on this proxy. Stopping early costs the answer too, not just the chain.
- **At oracle H, the pass walk has the answer string more often than the cheap walk (.928 against .867), while the
  cheap walk has the whole chain more often (.506 against .439).** That's SR-BH's mechanism seen from the other side.
  The pass request skips toward the answer, and the named bridge reads the chain in order. Which one is better depends
  on whether the answer needs its chain, a question all-hops can't settle.

## What it means

- **The walk can't yet stop on its own.** S-check stops too early, and S-in either never stops (cheap) or stops early
  (pass). The oracle H + 1 remains the best per character (.201) and on all-hops among real stop rules. The value
  SR-BH2 found in a spare read isn't reachable without knowing H.
- **S-check answered the question it was asked.** "`question` can be answered from these passages" is true, in
  surface terms, once a passage states the answer. Jev judges answerability by the answer's presence, not by whether
  the chain that licenses it has been read. A completeness check that knows the chain would need the decomposition,
  which the walk doesn't have.
- **The step comparison survives the stop rule.** Under every stop rule except the cheap walk's runaway S-in, the
  cheap walk gets whole chains more often than the pass walk.

## Predictions against outcomes

bill's registered predictions:
- **S-in stops too early:** pass ✓ (92 early); cheap ✗, it almost never stops (148 late, 15.5 reads).
- **S-check near oracle(H), stopping late more than early, H-S a coin flip:** ✗. It's −.206, with 106 early and 31
  late.
- **S-check stops after one read under 10%:** ✗. It's 35%.
- **S-check input about 1.5× the oracle walk's:** ✗. About 1.04×, because it stops early.

## Postmortem

- **What went right.** The dry run and stage 0 priced the run twice, and the registered shrink rule kept it under the
  cap without anyone choosing a number. bill's risk note ("can be answered may be judged on surface overlap") named
  the failure before the run, and the confusion table, which he required, showed it.
- **What we got wrong.** We treated "can be answered from these passages" as a completeness test. For a model, it's an
  answer-presence test. On the cheap walk the stop option sat among names and phrases, where Jev almost never picked
  it, and I flagged that only as a step-1 sanity check, not as a reason it might never fire.
- **Mechanism.** Both stop rules ask Jev a question about the *answer*. The walk's measure asks about the *chain*.
  Where the two differ (the answer passage read without its chain), S-check stops and all-hops counts a miss.
- **Not tested.**
  - Whether the answer can actually be produced from the stopped reads. That needs a reader, not a string match.
  - A stop rule built from the walk's own structure, for example stopping when the cheap walk's named key no longer
    leads to any unread passage.
  - Whether all-hops or answer presence is the right target. That is a question for Sirsh's definition of "good".

**Scope.** MuSiQue train chains, one draw of 180, H hidden from the walk. Production is Sirsh's.
