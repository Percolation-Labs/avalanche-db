# Answer presence, checked (22 Nov, $0): the measure Sirsh asked for, and why it ranks the walks differently

*james. Sirsh at 17:07Z: the walk returns passages to an LLM, so the measure is whether the answer is contained in
what the walk returns, properly checked, not a string match. Script: inline, output `out/answer-measure-look.txt`.
Data: the cached walks of SR-BH, SR-BH2 and SR-BS. No Jev call.*

## The measure

**A-last: the returned set contains the gold last-hop passage.**
- In MuSiQue, each question's answer is the answer to its last sub-question, and the last hop's passage is the gold
  passage that states it.
- **Checked:** the gold answer (or an alias) appears in the gold last-hop passage in 380 of 380 cached questions.
- So A-last never counts a passage that only mentions the answer string by coincidence.
- It is a lower bound. Another returned passage may state the answer too. On the cached walks, a string match without
  the last hop occurs in 1–5% of questions. Those cases are unchecked, and a Jev judge per case ("does this passage
  state `answer` as the answer to the last sub-question?") would settle them for a few cents.

## Why chain and answer diverge, plainly

The answer is stated in the **last** passage of the chain. To return it, the walk has to reach that passage; it
doesn't have to read every passage before it.

- **Jev's full step** is asked, at each step, "would this passage help answer the question?". The passage that helps
  most is the one holding the answer, so it often jumps straight there. On SR-BH's 200 at the hop count, it reached
  the answer passage 167 times, and in 104 of those it skipped a middle hop on the way.
- **The cheap walk** follows the named link from the passage it just read, one link at a time. It reads the chain in
  order, so it skips less (79 of 158), but it reaches the end less often (158 of 200). When it misses, it usually ran
  out of reads on the chain or wandered off it (32 of 42).
- So the old "all hops" measure rewarded reading in order. Answer presence rewards getting to the end.

## The walks on answer presence (A-last), paired

| run | cheap | pass | cheap − pass |
|---|---|---|---|
| SR-BH, at the hop count | .790 | .835 | −.045 [−.095, +.000] |
| SR-BH2, one spare read | .860 | .890 | −.030 [−.075, +.010] |
| SR-BS, at the hop count | .856 | .900 | −.044 [−.100, +.011] |
| SR-BS, one spare read | — | — | +.000 [−.044, +.039] |

- **On answer presence, Jev's full step leads by about .04 at the hop count.** That's borderline (the CIs touch 0),
  and the gap closes with a spare read.
- The cheap walk's input saving (about 20%) is unchanged. So on Sirsh's measure, with a spare read, the cheap walk
  returns the answer as often as the full step at about 80% of the input. At the exact hop count it gives up about .04.
- **What changes for the open questions.**
  - **The stop rule:** S-check, which stopped when the answer was in view, was closer to right than "all hops" said.
    On A-last it scores .767 against .856 for the oracle hop count, still lower.
  - **The step rule:** the cheap walk's order advantage doesn't count on its own any more. What counts is reaching the
    last hop, and the full step heads there.
  - **The dreaming reward:** SR-BR, SR-BC and SR-RS rewarded "both hops found". They should be rescored on answer
    presence (bill's side).
