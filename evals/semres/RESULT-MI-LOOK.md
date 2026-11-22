# Mutual inductance, a first look: reading one branch pushes the parallel branch away, and pulls the join in

*22 Nov 2026, bill. Sirsh's 10:35Z note on semantic inductance, intuition (2): flow on one path induces flow on a
parallel one. An unregistered look, $0, no Jev. MuSiQue dev 3hop2 (192 questions, not used by semres before). Script
`mi_look.py`, output `out/mi-look.txt`. Graph is graph-mq (no pool passage missing).*

**Shape.** In 3hop2, two sub-questions don't depend on each other (branches A and B), and a third joins them (J). For
example: "When was the last time Duane Courtney's team beat the winner of the 1894–95 FA Cup?" Here A is Duane
Courtney's team, B is the cup winner, and J is the match record. MuSiQue dev has 351 questions with parallel branches
(3hop2 192, 4hop3 95, 4hop2 64), and james's train corpus has the same counts.

**What reading a branch does to the other passages.** Ranks are among the pool's 19 passages other than the one read
(1 is best).

| read → target | shares a door key | door rank, median (top-1) | cos(q), median (top-1) | cos(q + read), median (top-1) |
|---|---|---|---|---|
| A → **other branch B** | .31 | 3 (.11) | **1 (.70)** | **4 (.20)** |
| A → **join J** | .77 | 2 (.39) | 6 (.05) | 3 (.17) |
| A → random non-gold | .18 | 10 (.02) | 10 (.03) | 10 (.04) |
| B → **other branch A** | .31 | 4 (.09) | **1 (.70)** | **4 (.26)** |
| B → **join J** | .89 | 2 (.38) | 6 (.02) | 3 (.17) |
| B → random non-gold | .25 | 10 (.02) | 10 (.03) | 10 (.04) |

**What it shows.**
- **Anti-induction in vector space.** Before anything is read, the other branch is cosine's top passage in 70% of
  questions, because the question names both branches. After one branch is read, cos(q + read) drops it to median rank
  4 (top-1 .20–.26). Reading A pulls the probe toward A's topic and *away* from B.
- **The branches aren't directly coupled.** They share a door key in only 31% of questions, against 18–25% for a random
  passage. Each branch shares one with the join in 77–89%. So the coupling between parallel branches runs *through the
  join*, in series, not across.
- **The chain neighbour is induced.** Reading a branch lifts J by both routes: door top-1 .38–.39, and cos(q + read)
  median rank 6 → 3.

**For the inductance frame.** If "mutual inductance" means evidence on one branch energises its twin, then neither the
graph nor the vector probe shows it here. The vector probe shows the opposite sign, which is Lenz-like: the probe,
conditioned on what's been read, resists the parallel branch. The practical reading for split probes is to probe each
branch from the question alone, not from the other branch's evidence. Conditioning on history, the kind of momentum
james is testing in SR-MO, would hurt parallel branches. That's a direct link between intuitions (1) and (2).

**What it doesn't show.** Whether Jev behaves the same way. Jev reads the question's structure and may keep the other
branch high after reading one: "I still need the cup winner". That's the registered test to run, on train's parallel
questions with Jev, at small cost.

**Scope.** Dev 3hop2 only, gold used to label branches, no Jev, seen now. The 4-hop shapes aren't looked at.
