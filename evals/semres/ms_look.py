"""MaxSim pricing look (before registering), on SR-KB's 300 (seen): does a max over points keep the key's identity
where SR-KB's and SR-KB2's means turned it into topic? bge-small token embeddings, no new model, $0.
Given gold hop 1 as read and its door-key bundle R (2 <= df <= 100, not in the question), for each option v:
  ms_pool(v) = Σ_k w_k · max_t cos(tok_t(v), phr(k))                  phr = the phrase's pooled vector
  ms_tok(v)  = Σ_k w_k · mean_{s in k's tokens} max_t cos(tok_t(v), tok_s(k))   ColBERT's MaxSim per key
with w_k = 1/(df_k − 1) (SR-K's weight). References: qr (question + read, text) and k (lexical SR-K).
    uv run --with sentence-transformers --with numpy python ms_look.py MUSIQUE_DEV GRAPH_MQ"""
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
def toks(texts):
    out = m.encode(texts, output_value="token_embeddings")
    return [t.numpy() / np.linalg.norm(t.numpy(), axis=1, keepdims=True) if hasattr(t, "numpy") else t / np.linalg.norm(t, axis=1, keepdims=True) for t in out]
res = {a: [] for a in ("qr", "k", "ms_pool", "ms_tok")}
for qi in pool:
    r = qs[qi]; d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p for p in r["paragraphs"]}; T = {i: P[i]["title"] + ". " + P[i]["paragraph_text"] for i in P}
    opts = sorted(i for i in P if i != h1); qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    R = sorted(k for k in keys[hid(P[h1])] if 2 <= df[k] <= 100 and not set(k.split()) <= qt)
    O = m.encode([T[i] for i in opts], normalize_embeddings=True); eqr = m.encode([QP + r["question"] + " " + T[h1]], normalize_embeddings=True)[0]
    ks = np.array([sum(1 / (df[k] - 1) for k in keys[hid(P[i])] & set(R)) for i in opts])
    sc = dict(qr=O @ eqr, k=ks + 1e-6 * (O @ eqr))
    w = np.array([1 / (df[k] - 1) for k in R]); OT = toks([T[i] for i in opts])
    PH = m.encode(R, normalize_embeddings=True); KT = toks(R)
    sc["ms_pool"] = np.array([w @ (ot @ PH.T).max(0) for ot in OT])
    sc["ms_tok"] = np.array([sum(wk * (ot @ kt.T).max(0).mean() for wk, kt in zip(w, KT)) for ot in OT])
    h = opts.index(h2)
    for a in res: res[a].append(int(1 + (sc[a] > sc[a][h]).sum()))
for a, v in res.items():
    v = np.array(v); print(f"{a:8s} top-1 {np.mean(v == 1):.3f}  top-3 {np.mean(v <= 3):.3f}  MRR {np.mean(1 / v):.3f}")
