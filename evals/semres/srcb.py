"""SR-CB (REGISTERED-SRCB.md), REM-1341, $0: does a small late-interaction (ColBERT-style) model keep the identity that
carries the next hop? Same task as SR-KB: given the gold hop 1 as read, rank the other 19 passages of the pool for hop 2.
Models (CPU, via pylate): a = answerdotai/answerai-colbert-small-v1 (33M, 96-dim tokens),
                          x = mixedbread-ai/mxbai-edge-colbert-v0-17m (17M, 48-dim tokens).
Each model, in its own trained modes: the question is encoded as a query, passages and key phrases as documents.
MaxSim(T, v) = Σ_{t in T} max_{s in v} cos(t, s).
Arms per model M:
  M_q    MaxSim(question tokens, v)
  M_qr   MaxSim(question tokens ∪ read-passage tokens, v)     (the whole read passage: the late-interaction qr)
  M_k    Σ_k w_k · mean_{t in key k} max_{s in v} cos(t, s), w_k = 1/(df_k − 1), over SR-KB's bundle (keys only)
Reference arms (bge-small, from SR-KB): qr = cos(q + read, v); k = SR-K's lexical door decider, ties by qr.
Draw: SR-KB's own permutation (seed 1341 over answerable 2-hop 41–1252, SR-J-R's 40 excluded).
  SET=kb     its first 300 (SR-KB's, seen)      SET=fresh  the next 300 of the same permutation (registered set)   --look: gold-blind, 3 questions
    uv run --with pylate --with numpy python srcb.py MUSIQUE_DEV GRAPH_MQ SET"""
import hashlib, json, re, sys, time
from collections import Counter
import numpy as np
src, gpath, SET = sys.argv[1], sys.argv[2], sys.argv[3]
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
held = set(np.random.default_rng(20261121).permutation(np.arange(40, len(qs)))[:40].tolist())
perm = [i for i in np.random.default_rng(1341).permutation(np.arange(40, len(qs))) if i not in held]
pool = perm[:300] if SET == "kb" else perm[300:600]
LOOK = "--look" in sys.argv; pool = pool[:3] if LOOK else pool   # gold-blind: one case's top 3 and timing, no ranks
from sentence_transformers import SentenceTransformer
from pylate import models
bge = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
CB = {"a": models.ColBERT("answerdotai/answerai-colbert-small-v1", device="cpu"),
      "x": models.ColBERT("mixedbread-ai/mxbai-edge-colbert-v0-17m", device="cpu")}
ARMS = ["qr", "k"] + [f"{M}_{a}" for M in CB for a in ("q", "qr", "k", "gb")]
maxsim = lambda T, D: (T @ D.T).max(1)
out, secs = [], {M: 0.0 for M in CB}
for n_, qi in enumerate(pool):
    r = qs[qi]; d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p for p in r["paragraphs"]}; T = {i: P[i]["title"] + ". " + P[i]["paragraph_text"] for i in P}
    opts = sorted(i for i in P if i != h1); qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    R = sorted(k for k in keys[hid(P[h1])] if 2 <= df[k] <= 100 and not set(k.split()) <= qt)
    w = np.array([1 / (df[k] - 1) for k in R])
    E = bge.encode([QP + r["question"] + " " + T[h1]] + [T[i] for i in opts], normalize_embeddings=True)
    O = E[1:]; ks = np.array([sum(1 / (df[k] - 1) for k in keys[hid(P[i])] & set(R)) for i in opts])
    sc = dict(qr=O @ E[0], k=ks + 1e-6 * (O @ E[0]))
    for M, m in CB.items():
        t = time.time()
        Q = np.asarray(m.encode([r["question"]], is_query=True)[0])
        D = [np.asarray(x) for x in m.encode([T[i] for i in opts] + [T[h1], d[0]["answer"]] + R, is_query=False)]
        Dv, Dr, Db, K = D[:len(opts)], D[len(opts)], D[len(opts) + 1], D[len(opts) + 2:]
        QR = np.vstack([Q, Dr])
        sc[f"{M}_q"] = np.array([maxsim(Q, v).sum() for v in Dv])
        sc[f"{M}_qr"] = np.array([maxsim(QR, v).sum() for v in Dv])
        sc[f"{M}_gb"] = np.array([maxsim(Db, v).mean() for v in Dv])   # amendment 1: GOLD CEILING, the hop-1 answer's tokens
        sc[f"{M}_k"] = np.array([sum(wk * maxsim(Kk, v).mean() for wk, Kk in zip(w, K)) for v in Dv]) if R else sc[f"{M}_q"]
        secs[M] += time.time() - t
    if n_ == 0:
        print(f"-- {r['question']}\n   read: {P[h1]['title']}; bundle size {len(R)}")
        for a in ("qr", "a_qr", "a_k", "x_qr"): print(f"   {a:5s} top 3: {[P[opts[j]]['title'] for j in np.argsort(-sc[a])[:3]]}")
    if LOOK: continue
    h = opts.index(h2)
    out.append(dict(qi=int(qi), nkeys=len(R), **{a: int(1 + (sc[a] > sc[a][h]).sum()) for a in ARMS}))
if LOOK: sys.exit(f"look: per-question seconds " + ", ".join(f"{M} {secs[M] / len(pool):.3f}" for M in CB))
nq = len(out)
print(f"\nSET={SET}: {nq} questions; per-question encode+score seconds (20 passages + question + keys): "
      + ", ".join(f"{M} {secs[M] / nq:.3f}" for M in CB))
rng = np.random.default_rng(0)
for a in ARMS: print(f"{a:5s} top-1 {np.mean([o[a] == 1 for o in out]):.3f}  top-3 {np.mean([o[a] <= 3 for o in out]):.3f}  MRR {np.mean([1 / o[a] for o in out]):.3f}")
for a, b in (("a_qr", "qr"), ("a_k", "k"), ("a_qr", "k"), ("a_k", "qr"), ("x_qr", "qr"), ("x_k", "k"), ("a_q", "a_qr"), ("a_gb", "a_qr")):
    dd = np.array([(o[a] == 1) - (o[b] == 1) for o in out], float); bt = [dd[rng.integers(0, nq, nq)].mean() for _ in range(4000)]
    print(f"top-1 {a} − {b}: {dd.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]")
json.dump(out, open(f"out/srcb-{SET}.json", "w"))
