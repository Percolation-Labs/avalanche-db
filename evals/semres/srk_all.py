"""SR-K extended (unregistered correction check): the k-decider and the cos(q + read) decider on every MuSiQue dev
answerable 2-hop question, given the gold hop 1. $0, no Jev. Reports by block of file order.
    uv run --with sentence-transformers --with numpy python srk_all.py MUSIQUE_DEV GRAPH_MQ"""
import hashlib, json, re, sys
from collections import Counter
import numpy as np
rows = [json.loads(l) for l in open(sys.argv[2])]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(sys.argv[1])) if r["id"].startswith("2hop") and r["answerable"]]
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); res = []
for r in qs:
    d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p for p in r["paragraphs"]}; T = {i: P[i]["title"] + ". " + P[i]["paragraph_text"] for i in P}
    opts = sorted(i for i in P if i != h1); qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    R = {k for k in keys[hid(P[h1])] if 2 <= df[k] <= 100 and not set(k.split()) <= qt}
    ks = np.array([sum(1 / (df[k] - 1) for k in keys[hid(P[i])] & R) for i in opts])
    E = m.encode(["Represent this sentence for searching relevant passages: " + r["question"] + " " + T[h1]] + [T[i] for i in opts], normalize_embeddings=True)
    cqr = E[1:] @ E[0]; h = opts.index(h2)
    res.append(dict(k=int(np.argmax(ks + 1e-6 * cqr) == h), v=int(np.argmax(cqr) == h), kr=int(ks[h] > 0)))
def line(sub): return f"n {len(sub):4d}  k-decider {np.mean([x['k'] for x in sub]):.2f}  cos(q+read) {np.mean([x['v'] for x in sub]):.2f}  hop 2 shares a door {np.mean([x['kr'] for x in sub]):.2f}"
for a, b in ((0, 40), (40, 200), (200, 700), (700, 1252)): print(f"q{a + 1}-{b}: " + line(res[a:b]))
print("all : " + line(res))
k = np.array([x["k"] - x["v"] for x in res], float); rng = np.random.default_rng(0)
bt = [k[rng.integers(0, len(k), len(k))].mean() for _ in range(4000)]
print(f"k − cos(q+read), all: {k.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]")
