"""$0 block check (21 Nov, after the first-40 correction): srj_look on a slice [A:B] of MuSiQue 2-hop dev. python srj_look_blocks.py DEV A B"""
import json, sys, numpy as np
from sentence_transformers import SentenceTransformer
rows = [json.loads(l) for l in open(sys.argv[1])]
rows = [r for r in rows if r["id"].startswith("2hop") and r["answerable"]][int(sys.argv[2]):int(sys.argv[3])]
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")
X, Y, out = [], [], []
for r in rows:
    d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p["title"] + ". " + p["paragraph_text"] for p in r["paragraphs"]}
    ids = sorted(P); E = m.encode(["Represent this sentence for searching relevant passages: " + r["question"]] + [P[i] for i in ids], normalize_embeddings=True)
    cos = dict(zip(ids, (E[1:] @ E[0]).tolist()))
    opts = [i for i in ids if i != h1]
    for i in opts: X.append(cos[i]); Y.append(int(i == h2))
    rk = 1 + sum(cos[i] > cos[h2] for i in opts)
    out.append((r["id"], round(cos[h1], 3), round(cos[h2], 3), round(max(cos[i] for i in opts if i != h2), 3), rk))
X, Y = np.array(X), np.array(Y)
from sklearn.linear_model import LogisticRegression
lr = LogisticRegression(C=1e6).fit(X[:, None], Y)
print("n options", len(X), "hop2 gold", Y.sum(), "Bayes slope β (nats per cos unit)", round(lr.coef_[0][0], 2), "intercept", round(lr.intercept_[0], 2))
print("cos hop1 mean", round(np.mean([o[1] for o in out]), 3), "hop2 mean", round(np.mean([o[2] for o in out]), 3), "best distractor mean", round(np.mean([o[3] for o in out]), 3))
rks = np.array([o[4] for o in out]); print("hop2 rank by cos among 19: median", np.median(rks), "top1", (rks == 1).mean().round(3), "top5", (rks <= 5).mean().round(3))
print("crossing cost (β·(best distractor − hop2)) median nats", round(float(np.median([lr.coef_[0][0] * (o[3] - o[2]) for o in out])), 2))

