# Structural stop look (22 Nov, $0, post hoc on SR-BS's walks): stopping when the named key runs out fails past 2 hops

*james. Data: SR-BS's cached cheap-walk trajectories (`out/srbs-fresh.json`, 180 chains). No Jev call. This was the
next step promised to Sirsh at 17:02Z. A look at seen walks, not a result, and it doesn't go to registration.*

**Rule.** Stop the cheap walk at the first step where the named key leads to no unread passage, i.e. where it would
rescue. No threshold. A variant also requires at least 2 reads, which is a constant and is shown only to bound the
idea.

| rule | 2-hop | 3hop1 | 4hop1 | all | reads | early / exact / late |
|---|---|---|---|---|---|---|
| first rescue | .583 | .067 | .000 | .217 | 2.02 | 135 / 26 / 19 |
| first rescue after 2 reads | .850 | .117 | .000 | .322 | 2.62 | 102 / 47 / 31 |
| *oracle H (SR-BS)* | *.717* | *.483* | *.317* | *.506* | *3.00* | |

**Why it fails.** The hops look (NOTE-HOPS-LOOK.md) already showed why: after the first step, a chain's bridge is
usually a place with no key (keyed reachability .44–.52 on later steps). So the key runs out mid-chain, and the rule
stops there. On 2-hop it's competitive (.850 with the 2-read floor), because 2-hop walks end after one keyed step.

**What it means.** The walk's structure can't tell "the chain is done" from "the graph has no key for the next link".
A structural stop rule needs keys for the bridges the graph drops at df > 100, the same limit that shrinks the cheap
walk's saving. It points back at the graph (a dreaming question), not at a new rule. Not registered; no spend.
