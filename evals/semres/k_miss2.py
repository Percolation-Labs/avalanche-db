"""Follow-up to k_miss.py (an unregistered look on SR-KB's 300, seen data, $0). Knob-free reductions of the shared door keys, with qr as the tie-break:
  sum  : SR-K's strength, Σ 1/(df−1)
  max  : the rarest shared key alone, max 1/(df−1) (identity: one rare entity)
  count: the number of shared keys
  bridge (ceiling only, uses gold): Σ over shared keys whose words all appear in hop 1's answer. Not a door, since doors are
         never built from gold. It prices what naming the bridge would be worth.
    uv run --with sentence-transformers --with numpy python k_miss2.py MUSIQUE_DEV GRAPH_MQ"""
import hashlib, json, re, sys, numpy as np
from collections import Counter
src, gpath = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
held = set(np.random.default_rng(20261121).permutation(np.arange(40, len(qs)))[:40].tolist())
pool = [i for i in np.random.default_rng(1341).permutation(np.arange(40, len(qs))) if i not in held][:300]
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
W = lambda k: 1 / (df[k] - 1)
res = {a: [] for a in ("qr", "sum", "max", "count", "bridge")}; nb = 0
for qi in pool:
    r = qs[qi]; d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p for p in r["paragraphs"]}; T = {i: P[i]["title"] + ". " + P[i]["paragraph_text"] for i in P}
    opts = sorted(i for i in P if i != h1); qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    R = set(k for k in keys[hid(P[h1])] if 2 <= df[k] <= 100 and not set(k.split()) <= qt)
    at = set(re.findall(r"[a-z0-9]+", d[0]["answer"].lower())); B = {k for k in R if set(k.split()) <= at}; nb += bool(B)
    sh = [keys[hid(P[i])] & R for i in opts]
    O = m.encode([T[i] for i in opts], normalize_embeddings=True); eqr = m.encode([QP + r["question"] + " " + T[h1]], normalize_embeddings=True)[0]
    q = O @ eqr; tb = 1e-6 * q
    sc = dict(qr=q, sum=np.array([sum(map(W, s)) for s in sh]) + tb, max=np.array([max(map(W, s), default=0) for s in sh]) + tb,
              count=np.array([len(s) for s in sh]) + tb, bridge=np.array([sum(map(W, s & B)) for s in sh]) + tb)
    h = opts.index(h2)
    for a in res: res[a].append(int(1 + (sc[a] > sc[a][h]).sum()))
print(f"n {len(pool)}; questions whose read has a bridge key: {nb}")
for a, v in res.items():
    v = np.array(v); print(f"{a:7s} top-1 {np.mean(v == 1):.3f}  top-3 {np.mean(v <= 3):.3f}  MRR {np.mean(1 / v):.3f}")
