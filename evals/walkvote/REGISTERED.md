# W2: does the whole walk find more gold when it ranks doors by Jev's P fused with the width-neutral vote?

*19 Nov 2026, bill. Registered before any run. Stage 0 is $0 (replay on recorded P); stage 1 is one Jev walk, ≤$1, only
if stage 0 passes. Sirsh approved the walk using read-set PageRank (M-20261118-215523-957d), width-neutral versions
first. Split with james (M-20261119-083725-ab67): james re-runs D3's edits with V1's θ; this is the walk side.*

## Why this and not W1 again

james's W1 (#38) fused P with the **summed** vote on the first door of recorded waves. It failed on MuSiQue, and on PR
titles most of its gain was width. V1 (#40) found the vote marks the gold door at equal width (.73–.83) and that
learning its form helps only PR titles. W2 changes two things: the vote is **per unread target** (mass ÷ width, so a
wide door gets no credit for being wide), and it is scored on **whole walks**, so later waves count.

## Walk

The k=10 walk as recorded (5 seeds from search, one door a wave, targets in shown order, no fill, 10 reads), re-run with
`order: rank` on Jev's recorded P (E2E_REPLAY). A door no recorded batch scored stays unranked and is never opened, in
every arm alike; each arm reports how many such doors it met (`unknown`).

## Arms (one fixed fusion, nothing tuned)

At each wave, over the doors with a recorded P: score = 1/(60 + rank by P) + 1/(60 + rank by X), ties by P. 60 is the
standard constant, the same one W1 used.

- **P**: X absent, today's walk replayed.
- **P ⊕ vote**: X = mean PageRank per unread target from the passages read so far, uniform θ (−1, 0). Primary.
- **P ⊕ learned vote**: X as above with V1's per-graph θ (cards (−1, −.5), PR titles (−2, −1), MuSiQue (−1, 0)).
- **P ⊕ shuffled vote**: X from links shuffled at the same widths (as in evals/structural). Structure control.
- **P ⊕ narrow**: X = fewest unread targets. Width control: the per-target vote could favour narrow doors.

## Read-outs, held-out test walks only

Per question, the share of its gold found in the 10 reads (gold recall@10), and whether any gold beyond the seeds was
found. Search's own top 10 is shown for reference (round one is search).

## Bar (fixed now)

P ⊕ vote passes stage 0 if its mean gold recall@10 beats P by at least .03 on at least two of the three sets, falls
below P by no more than .02 on any set, and beats both P ⊕ shuffled vote and P ⊕ narrow by at least .02 on the sets
where it gains. Unknown doors can only be passed over, never opened, so they restrict an arm to doors the recorded walk
saw. If more than half of a set's questions meet an unknown door under P ⊕ vote, that set is reported as unreliable,
not as a gain. A pass leads to stage 1: the fused walk live with Jev on the test questions of the set with the largest
gain, ≤$1, against P live on the same questions.

**Postmortem:** every result gets one.

## Amendment, 19 Nov, before any scoring

A smoke test on three PR-title test questions (wiring only, no measure computed) showed the whole-walk replay can't
serve as stage 0: once a fused arm leaves the recorded walk it meets 15–270 doors Jev never scored. Those doors can
never be opened, so every set would be "unreliable" by the rule above. Scoring those doors means calling Jev (kappa K6
changes the request whenever the reads differ), which costs about $1 per arm per set. So:

- **Stage 0 ($0)** is the first door of each recorded wave, as in W1, on V1's test rows (`evals/votes`, every wave with
  a gold door). Arms as above. The fusion is the same, over every door in the recorded batch.
  - Read-outs:
    - gold door first;
    - MRR of the best gold door;
    - read-weighted (b): the first door's gold per unread target as a share of the best door's.
  - Pass: P ⊕ vote beats P on gold-first by at least .03 on at least two sets, without falling more than .02 on any
    set, and without falling more than .02 on read-weighted (b) on any set. On the sets where it gains, it beats
    P ⊕ shuffled and P ⊕ narrow by at least .02.
- **Stage 1 (≤$1)**, only on a stage 0 pass: the whole walk live with Jev, P ⊕ vote against P, on the test questions of
  the set with the largest stage 0 gain. The read-out is gold recall@10, and the bar above applies to that set.
