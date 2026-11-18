"""Ceiling on what written hubs could add to (b): on dev waves with a gold door where Jev's first door is gold-free,
the share where a written hub (learned top 5% / 20%, or random) is raised and holds unread gold. In-sample for the
learned set (fit on these waves), so generous."""
import json, random, statistics as st
import numpy as np
exec(open("gate.py").read().split("for g, devs, tests in")[0])
from sklearn.linear_model import LogisticRegression
for g, devs in [("p8", ["cards", "prs"]), ("mq", ["mq"])]:
    C = [json.loads(l) for l in open(f"cand-{g}.jsonl")]
    M = [set(c["members"]) for c in C]
    XX = np.array([X(c["f"]) for c in C]); Z = (XX - XX.mean(0)) / (XX.std(0) + 1e-9)
    by = collections.defaultdict(list)
    for i, m in enumerate(M):
        for d in m: by[d].append(i)
    I = []
    for q, R, G in [w for c in devs for w in dev_waves(c)]:
        if not (G - R): continue
        for i in {i for d in R for i in by.get(d, [])}:
            I.append((i, int(bool((M[i] - R) & G))))
    s = LogisticRegression(max_iter=1000).fit(Z[[i for i, _ in I]], [y for _, y in I]).decision_function(Z)
    order = np.argsort(-s); npass = len({d for x in M for d in x})
    for c in devs:
        gold = {r["qid"]: golds(r["gold"]) for r in map(json.loads, open(f"../dt-{c}.jsonl"))}
        rows = [w for w in map(json.loads, open(f"b-{c}.jsonl")) if any(d["gold"] for d in w["doors"])]
        gap = [w for w in rows if not min(w["doors"], key=lambda d: d["rank"])["gold"]]
        out = [f"{c}: waves with a gold door {len(rows)}, Jev's first gold-free on {len(gap)} ({len(gap)/len(rows):.2f})"]
        for frac in (0.05, 0.2):
            N = int(frac * npass)
            for name, H in [("learned", set(order[:N].tolist())), ("random", set(random.Random(1).sample(range(len(C)), N)))]:
                hit = 0; beat = 0
                for w in gap:
                    R = set(w["reads_before"]); G = gold[w["qid"]]
                    best_door = max(d["gold"] / d["width"] for d in w["doors"] if d["width"])
                    dens = [len((M[i] - R) & G) / max(len(M[i] - R), 1) for i in {i for d in R for i in by.get(d, []) if i in H}]
                    hit += any(x > 0 for x in dens); beat += any(x >= best_door for x in dens)
                out.append(f"{name}@{frac:.0%}: a gold hub on {hit/len(gap):.2f} of them, as dense as the best gold door on {beat/len(gap):.2f} -> (b) ceiling +{hit/len(rows):.2f}")
        print(" | ".join(out))
