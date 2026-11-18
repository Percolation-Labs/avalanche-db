"""D1 $0 pre-gate: a logistic model of a raised hub's structure, fit on dev waves (does it hold unread gold),
scored on held-out test waves against a random raised hub and the existing doors."""
import json, collections, random, math, statistics as st
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
def golds(g): return set(g.keys()) if isinstance(g, dict) else set(g)
FE = ["size", "conductance", "cohesion", "density", "mean_deg", "top_share", "top_df", "novelty"]
def X(f): return [math.log(f["size"]), f["conductance"], f["cohesion"], f["density"], math.log1p(f["mean_deg"]), f["top_share"], math.log1p(f["top_df"]), f["novelty"]]
def dev_waves(c):
    gold = {r["qid"]: golds(r["gold"]) for r in map(json.loads, open(f"../dt-{c}.jsonl"))}
    return [(w["qid"], set(w["reads_before"]), gold[w["qid"]]) for w in map(json.loads, open(f"b-{c}.jsonl"))]
def test_waves(c, tf, qf):
    gold = {r["qid"]: golds(r["gold"]) for r in map(json.loads, open(qf))}
    out = []
    for t in map(json.loads, open(tf)):
        docs = t["documents"]; ws = sorted({d["wave"] for d in docs if d["wave"] > 0})
        for w in ws:
            out.append((t["qid"], {d["id"] for d in docs if d["wave"] < w}, gold[t["qid"]]))
    return out
for g, devs, tests in [("p8", ["cards", "prs"], [("cards", "../../floor/trace-cards.jsonl", "../../floor/q-cards.jsonl"), ("prs", "../../floor/trace-pr.jsonl", "../../floor/q-prs-test.jsonl")]),
                       ("mq", ["mq"], [("mq", "../../floor/trace-mq.jsonl", "../../floor/q-musique-questions.jsonl")])]:
    C = [json.loads(l) for l in open(f"cand-{g}.jsonl")]
    M = [set(c["members"]) for c in C]
    XX = np.array([X(c["f"]) for c in C])
    by = collections.defaultdict(list)
    for i, m in enumerate(M):
        for d in m: by[d].append(i)
    def inst(waves):
        rows = []
        for q, R, G in waves:
            if not (G - R): continue
            for i in {i for d in R for i in by.get(d, [])}:
                rows.append((q, i, int(bool((M[i] - R) & G))))
        return rows
    D = [w for c in devs for w in dev_waves(c)]
    I = inst(D)
    qs = sorted({q for q, _, _ in I}); random.Random(0).shuffle(qs); hold = set(qs[: len(qs) // 5])
    tr = [r for r in I if r[0] not in hold]; va = [r for r in I if r[0] in hold]
    mu, sd = XX.mean(0), XX.std(0) + 1e-9
    Z = (XX - mu) / sd
    m = LogisticRegression(max_iter=1000).fit(Z[[i for _, i, _ in tr]], [y for *_, y in tr])
    va_auc = roc_auc_score([y for *_, y in va], m.decision_function(Z[[i for _, i, _ in va]]))
    s = m.decision_function(Z)
    print(f"{g}: dev instances {len(I)} (pos {sum(y for *_, y in I)/len(I):.3f}) | held-back dev AUC {va_auc:.2f} | coef " + ", ".join(f"{n} {c:+.2f}" for n, c in zip(FE, m.coef_[0])))
    for c, tf, qf in tests:
        T = test_waves(c, tf, qf)
        top, rnd, n, auc_y, auc_s = [], [], 0, [], []
        for q, R, G in T:
            if not (G - R): continue
            raised = list({i for d in R for i in by.get(d, [])})
            if not raised: continue
            n += 1
            ys = [int(bool((M[i] - R) & G)) for i in raised]
            top.append(ys[int(np.argmax(s[raised]))]); rnd.append(st.mean(ys))
            auc_y += ys; auc_s += list(s[raised])
        print(f"   test {c}: waves {n} | top-scored raised hub holds unread gold {st.mean(top):.2f} vs a random raised hub {st.mean(rnd):.2f} | instance AUC {roc_auc_score(auc_y, auc_s):.2f}")
