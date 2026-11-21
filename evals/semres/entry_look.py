"""Entry look (unregistered, $0, all 1,252 MuSiQue dev answerable 2-hop questions, all seen). How often does cosine's
top-m pool contain hop 1 (or hop 2), for m = 1..5? It sizes an entry chooser that picks among cosine's top few.
    uv run --with sentence-transformers --with numpy python entry_look.py MUSIQUE_DEV"""
import json, sys
import numpy as np
from sentence_transformers import SentenceTransformer
qs = [r for r in map(json.loads, open(sys.argv[1])) if r["id"].startswith("2hop") and r["answerable"]]
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
h1in = np.zeros((len(qs), 5)); anyin = np.zeros((len(qs), 5))
for n, r in enumerate(qs):
    P = sorted(r["paragraphs"], key=lambda p: p["idx"]); ix = {p["idx"]: i for i, p in enumerate(P)}; d = r["question_decomposition"]
    h1, h2 = ix[d[0]["paragraph_support_idx"]], ix[d[1]["paragraph_support_idx"]]
    E = m.encode([QP + r["question"]] + [p["title"] + ". " + p["paragraph_text"] for p in P], normalize_embeddings=True)
    o = list(np.argsort(-(E[1:] @ E[0])))
    for k in range(5): top = o[:k + 1]; h1in[n, k] = h1 in top; anyin[n, k] = (h1 in top) or (h2 in top)
for k in range(5): print(f"top-{k + 1}: contains hop 1 {h1in[:, k].mean():.3f}, contains hop 1 or hop 2 {anyin[:, k].mean():.3f}")
