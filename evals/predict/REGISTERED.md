# S4: which structural properties of a wave predict whether Jev's first door holds gold?

*19 Nov 2026, bill. Registered before any run. $0. Sirsh's 18 Nov question (M-20261118-200827-fd14): which structural
properties, spectral and otherwise, predict a cheap walk? (a), the Steiner cost, is near its ceiling on all three
graphs and ranks questions poorly (evals/steiner). So the outcome here is (b) at the wave: does the door Jev ranks first
hold unread gold?*

**Data:** V1's test and dev rows (`evals/votes`): every recorded k=10 wave with a gold door, with each door's P,
width, gold and read-set vote (uniform θ).

**Properties, per wave, all question-free:**
1. **Choice size:** doors on offer (log).
2. **Gold share:** the share of the doors offered that hold gold. This is the base rate a blind pick faces.
3. **Vote margin:** the best gold door's vote minus the best gold-free door's vote at similar width (within 2×), in
   ranks within the batch. It says how distinct the right door is structurally.
4. **Vote concentration:** the share of the batch's total vote held by its top 5 doors. It says whether the read set
   points somewhere or everywhere.
5. **Width spread:** the coefficient of variation of the doors' widths.

**Read-outs:**
- Per graph, on test, the AUC of each property for "Jev's first door holds gold" (direction fixed in advance:
  higher is easier for 2, 3 and 4, lower for 1 and 5).
- Pooled across graphs: the same AUC, and whether the graph's mean of each property orders the graphs as Jev's
  gold-first does (cards > MuSiQue > PR titles).

**Bar:** a property "predicts" if its AUC is at least .65 on at least two graphs, and its controls stay below that.
There are two controls: the property computed on shuffled links (for 3 and 4, which use the vote), and gold share
(2), which is the trivial baseline any structural property has to beat to count as more than base rate. Dev is
reported alongside, and nothing is fitted.

**Spectral, stage 2, only if stage 1 leaves the PR-titles gap unexplained:** per question, the spectral gap of the
subgraph within one door of the seeds, and the conductance of the gold set in it. Registered separately.

**Postmortem:** every result gets one.
