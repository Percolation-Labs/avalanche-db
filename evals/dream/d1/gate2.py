"""Graph-wide version: write the top N candidates by the dev-fit score (N a share of passages) vs N at random;
on held-out test waves, what the written hubs offer the walk."""
import json, random, statistics as st, sys
import numpy as np
exec(open("gate.py").read().split("for g, devs, tests in")[0])
from sklearn.linear_model import LogisticRegression
for g, devs, tests in [("p8", ["cards", "prs"], [("cards", "../../floor/trace-cards.jsonl", "../../floor/q-cards.jsonl"), ("prs", "../../floor/trace-pr.jsonl", "../../floor/q-prs-test.jsonl")]),
                       ("mq", ["mq"], [("mq", "../../floor/trace-mq.jsonl", "../../floor/q-musique-questions.jsonl")])]:
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
    m = LogisticRegression(max_iter=1000).fit(Z[[i for i, _ in I]], [y for _, y in I])
    s = m.decision_function(Z); order = np.argsort(-s)
    npass = len({d for x in M for d in x})
    for c, tf, qf in tests:
        T = [w for w in test_waves(c, tf, qf) if w[2] - w[1]]
        out = []
        for frac in (0.01, 0.05, 0.2):
            N = int(frac * npass)
            for name, H in [("learned", set(order[:N].tolist())), ("random", set(random.Random(1).sample(range(len(C)), N)))]:
                offer, anyg, dens = [], 0, []
                for q, R, G in T:
                    raised = {i for d in R for i in by.get(d, []) if i in H}
                    offer.append(len(raised))
                    gd = [len((M[i] - R) & G) / max(len(M[i] - R), 1) for i in raised]
                    anyg += any(x > 0 for x in gd); dens += gd
                out.append(f"{name}@{frac:.0%} N={N}: hubs offered/wave {st.mean(offer):.1f}, waves with a gold hub {anyg/len(T):.2f}, gold density {st.mean(dens) if dens else 0:.3f}")
        print(f"{c} (test waves {len(T)}):\n  " + "\n  ".join(out))
