# R-stop replay check (registered 22 Nov, before any Jev call; amended at bill's review 17:46Z, before the run): does the reader's own request know when the answer is in hand?

*james, on bill's suggestion (17:43Z). Script `reader_stop.py`. A replay on SR-BS3's cached pass-walk trajectories
(`out/srbs3-fresh.json`), so no walk is rerun. Cap $0.15. Serves Sirsh's 17:07Z goal. Following bill's 17:43Z rule,
**AC is the primary for any rule that changes set size**, and A-last is the secondary.*

**Question.** SR-BS3's check ("can be answered from these passages") stops on Jev's own knowledge, which costs the
reader −.073 against oracle H. bill's reader request asks Jev to pick the sentence that states the answer. With one
extra option, NONE ("No sentence in `reads` states the answer to `question`"), it can say nothing is there yet. Stop
at the first read where a real sentence beats NONE. That ties the stop to a sentence the reader can use.

**Rule.** After each read prefix of the cached trajectory: bill's srac.py reader request, verbatim, plus NONE as the
last option. Argmax, with no threshold. The stop is at the first prefix where the argmax isn't NONE, and the chosen
sentence is the reader's answer. If NONE always wins, the walk runs to the end of its cached trajectory (H + 1 reads,
or S-check's stop if that was later), and that count is reported.
- **Limit of a replay:** the trajectories were walked to max(H + 1, S-check's stop). A rule that wants to read further
  is cut there. The never-stopped count bounds this.

**Primary (amended, bill's note 2: like for like). AC (string or judge, #102) of the stopped set scored with the
**standard** reader request (no NONE), as oracle H's was, R-stop − oracle H, paired bootstrap 95% CI over the 300,
with returned passages beside it.** Oracle H's AC is SR-BS3's (`out/srbs3-fresh-ac.json`).
- **H-R (non-inferiority):** the lower bound is above −.05.
- **A fail means "not shown within .05"**, stated with the point estimate and lower bound, not as evidence of harm.

**Secondary.**
- **Sensitivity row (bill's note 1):** the primary with never-stopped walks excluded, with their count. Their cut point
  depends on H, so if they're more than a few percent, the replay can't settle the question.
- AC of the NONE-request's own choice.
- R-stop − S-check (AC).
- A-last.
- Stops after one read, and never stopped.
- The judge's yes count.
- By hop type.

**Predictions.**
- NONE wins often on early prefixes, so R-stop stops later than S-check: about 2.8 passages.
- AC R-stop − oracle H is about −.02, and H-R passes about half the time.
- R-stop − S-check is about +.05.
- Never stopped: under 10%.

**Spend.** One wave per prefix length, only for walks not yet stopped. The dry run's worst case (all prefixes) is $0.08,
plus about $0.003 for the judge. Cap $0.15.

**Scope.** A replay check on SR-BS3's 300 chains and trajectories, the questions where the idea came from (bill's note
3). A pass needs a fresh draw before it's a claim.
