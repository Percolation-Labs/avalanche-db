"""$0: the vectors' Bayes slope of hop 2 on cos(read, passage) over the same 200 questions (β_B,r for amendment 1)."""
import json, sys, numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
rows = [r for r in map(json.loads, open(sys.argv[1])) if r["id"].startswith("2hop") and r["answerable"]][:200]
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); X, Y = [], []
for r in rows:
    d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p["title"] + ". " + p["paragraph_text"] for p in r["paragraphs"]}; ids = [i for i in sorted(P) if i != h1]
    E = m.encode([P[h1]] + [P[i] for i in ids], normalize_embeddings=True)
    for i, c in zip(ids, E[1:] @ E[0]): X.append(c); Y.append(int(i == h2))
lr = LogisticRegression(C=1e6).fit(np.array(X)[:, None], Y); print("β_B,r", round(lr.coef_[0][0], 2))
