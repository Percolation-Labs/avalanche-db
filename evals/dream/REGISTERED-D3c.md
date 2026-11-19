# Registered: D3c, materialise bill's learned vote as edge removal (james, 19 Nov 2026, before running)

V1 (evals/votes, #40) learned a vote per graph from the loop's own dev walks, where each edge is weighted by
exp(θ1·ln width(door) + θ2·ln(1 + doors(target))). θ = (−1, 0) is the uniform vote. Learned θ: cards (−1, −.5),
PR titles (−2, −1), MuSiQue (−1, 0). It improved the width-matched AUC only on PR titles (test .733 → .785). D3
(#39) found that under the uniform vote no question-free edit helps.

D3c asks: can the learned vote be **written into the graph** so that the plain uniform walk carries it? That is
the dreaming step Sirsh described (M-20261118-215523-957d): a voting statistic learned from walks drives edge removal.

**The edit.** Each membership (t in door k) has a learned-to-uniform weight ratio of
width(k)^(θ1+1) · (1+doors(t))^θ2. Remove the memberships with the lowest ratio: the bottom f of memberships, with
f chosen on dev from {.02, .05, .10, .20}. Only key memberships are removed; owned next/near doors are left alone,
because removing a target from them is not a membership edit. One round. The edit is deterministic given θ.

**Dev reward:** width-matched AUC, eligible only if the share of dev waves with a gold door drops by no more than .02.
This fixes D3's postmortem, where dev rewarded deleting doors.

**Sets.**
- PR titles with θ (−2, −1): the one graph where learning moved the vote.
- Cards with θ (−1, −.5).
- MuSiQue's θ is uniform: no edit, reported as such.

**Held-out read-outs (test):** width-matched AUC of uniform read-set PPR on the edited graph, and the share of waves
with a gold door. They are compared against G0 under uniform, G0 under learned θ (bill's .785 is the target to
reach), and random removal of the same count.

**Pass:** on PR titles, G_edit at least +.03 over G0 and random removal, with gold-door waves down by no more than
.02. Cards is reported; no gain is expected there.

$0. Every result gets a postmortem.
