# Registered: the likeness door (search's continuation as one more door)

Registered 18 Nov 2026 by james, before any spend, on Sirsh's yes (M-20261118-150956-f539).

## Why

Sirsh's floor (M-20261118-103300-ceb0): the walk should generally do at least as well as search, fixed as a property
of the walk, never per question type. At k=10 the walk loses to search on 16/93 PR-title, 13/150 card and 10/150
MuSiQue test questions. On every losing walk the first door took all five reads and found no gold, while the gold
lost sat at search ranks 6–10 (floor step 1, $0). No fixed split between door and search reads works (PR loses at
every split, cards and MuSiQue gain as the door reads more), and no score threshold or convergence vote separates
bad first doors from good ones (floor step 2, $0). So the choice has to be made per question, by the one part that
sees the question: Jev's ranking.

In the see-also framing (M-20261118-103637-390f): a connection door earns its place only where it reaches gold that
search would not. The likeness door lets Jev weigh "follow a link" against "keep searching" every wave, so where the
semantically orthogonal share is low (PR titles, .30) it can keep search's results, and where it is high
(cards .51, MuSiQue .36; evals/structure/RESULT.md) it can follow links.

## What changes (`Settings.like`, `midb walk --like <head>`; off by default)

Each wave, one more door, `search:<wave>`, of kind `like`. Its targets are the next unread passages in search's
order, as many as the budget has left, so opening it reads exactly what search would. D6 describes it like any
door, from its targets alone (first snippet, leads, names). Only its membership comes from search, as the seeds'
does. The previous wave's untaken likeness door is withdrawn. Its reads count as search reads (K6, `via`).
Nothing else changes: k=10, seeds ceil(k/2), one door a wave, within shown, K6, F2, Jev 1.13.0.

## The one choice made on dev: the head

Sirsh: the door must be described so Jev weighs it fairly, neither favoured nor buried by its wording. Three fixed
heads (the rest of the door's text is D6's):

- `match`: "5 unread that best match the question's words"
- `search`: "5 unread next in a full-text search for the question"
- `plain`: "5 unread"

Dev: cards-dev (100), musique-dev (101), prs-dev (65), at k=10, four arms (`none`, today's walk, and the three
heads), stores e2e-p8i (cards, PR titles) and e2e-mq3 (MuSiQue), as in bill's runs. The chosen head is the one with
the largest smallest-over-the-three-sets mean of (arm − search) recall@10. The open rate of the likeness door and
its P against the top door's are reported per head, to show whether a wording favours or buries it.

## The held-out test (run once, chosen head only)

The test sets: PR-title walk-test (93), cards and MuSiQue leads test (150 each), at k=10, on the same stores.
Baselines are the recorded test logs: search (ctl k10) and today's walk (walk-test.jsonl, leads/test/walk-*.jsonl).
They replay identically on main (floor step 2: 393/393 same). Recall@10, paired bootstrap 95%.

- **L1, floor.** like − search ≥ −.01 on each of the three sets.
- **L2, gains kept.** like − today's walk ≥ −.02 on cards and on MuSiQue.
- **L3, the choice beats a coin.** like − coin > 0 on each set. The coin is the per-question mean of today's walk
  and search, the expected result of choosing between them at random.
- Reported, not bars: like − today's walk on PR titles, and losses to search per set against 16/13/10. Also the
  oracle, max(today's walk, search) per question: +.067 / +.047 / +.023 over today's walk. The gain is stated
  against each set's orthogonal share (.30 / .51 / .36).

It passes on L1, L2 and L3 together. Only then is `like` made the default, in its own PR.

## Spend

Dev cap $0.90 (probe: $0.0005 a walk, 1.3 s). Test cap $0.50. Each is a registered run of $1 or less. The spend is
reported in RESULT.md.
