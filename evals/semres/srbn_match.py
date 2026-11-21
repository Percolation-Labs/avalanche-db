"""SR-BN matcher half (REGISTERED-SRBN.md), bill. Given the key K a namer picked from the read's door keys, rank the 19
options for hop 2 by K alone. Same task and draw as the namer half (gold hop 1 as read; perm 600-899 of SR-KB's order).
Arms (K = the Jev namer's key; none uses gold):
  m_x      mean over K's tokens of max over v of cos, mxbai-edge-colbert-v0-17m, the 19 options encoded on demand
  m_a      the same with answerai-colbert-small-v1 (reference)
  m_lex    fraction of K's words in v, ties by qr
  m_title  v's title == K first, then m_lex, then qr
Ceilings (gold, labelled): the same four with K = hop 1's answer string (g_x, g_a, g_lex, g_title).
References from the namer file: k (SR-K's sum, ties by qr), jev_pass (Jev's own passage pick, same draw).
A question whose bundle is empty (no K) falls back to qr for every arm.
    uv run --with pylate --with numpy python srbn_match.py MUSIQUE_DEV GRAPH_MQ SET      (SET: stage0 | fresh)"""
import hashlib, json, re, sys, time
from collections import Counter
import numpy as np
src, gpath, SET = sys.argv[1], sys.argv[2], sys.argv[3]
names = {int(k): v for k, v in json.load(open(f"out/srbn-names-{SET}.json")).items()}
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
held = set(np.random.default_rng(20261121).permutation(np.arange(40, len(qs)))[:40].tolist())
perm = [i for i in np.random.default_rng(1341).permutation(np.arange(40, len(qs))) if i not in held]
pool = {"stage0": perm[900:904], "fresh": perm[600:900]}[SET]
assert set(pool) == set(names), "names file is not this draw"
from sentence_transformers import SentenceTransformer
from pylate import models
bge = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
CB = {"x": models.ColBERT("mixedbread-ai/mxbai-edge-colbert-v0-17m", device="cpu"),
      "a": models.ColBERT("answerdotai/answerai-colbert-small-v1", device="cpu")}
wd = lambda s: re.findall(r"[a-z0-9]+", s.lower()); norm = lambda s: " ".join(wd(s))
ARMS = ("k", "jev_pass", "m_x", "m_a", "m_lex", "m_title", "g_x", "g_a", "g_lex", "g_title")
out, secs = [], 0.0
for qi in pool:
    r = qs[qi]; d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p for p in r["paragraphs"]}; T = {i: P[i]["title"] + ". " + P[i]["paragraph_text"] for i in P}
    opts = sorted(i for i in P if i != h1); h = opts.index(h2); nm = names[qi]
    E = bge.encode([QP + r["question"] + " " + T[h1]] + [T[i] for i in opts], normalize_embeddings=True); qr = E[1:] @ E[0]
    R = set(nm["R"] or []); ks = np.array([sum(1 / (df[k] - 1) for k in keys[hid(P[i])] & R) for i in opts])
    sc = dict(k=ks + 1e-6 * qr, jev_pass=np.array(nm["pj"]))
    def lex(K):
        kw = set(wd(K)); lx = np.array([len(kw & set(wd(T[i]))) / max(len(kw), 1) for i in opts]) + 1e-6 * qr
        return lx, np.array([float(norm(P[i]["title"]) == norm(K)) for i in opts]) + 1e-3 * lx
    for pre, K in (("m", nm["jev"]), ("g", d[0]["answer"])):
        if not K:
            for a in ("x", "a", "lex", "title"): sc[f"{pre}_{a}"] = qr
            continue
        sc[f"{pre}_lex"], sc[f"{pre}_title"] = lex(K)
        for M, m in CB.items():
            t = time.time()
            D = [np.asarray(v) for v in m.encode([K] + [T[i] for i in opts], is_query=False)]
            sc[f"{pre}_{M}"] = np.array([(D[0] @ v.T).max(1).mean() for v in D[1:]])
            if pre == "m" and M == "x": secs += time.time() - t
    out.append(dict(qi=int(qi), named=nm["jev"], **{a: int(1 + (sc[a] > sc[a][h]).sum()) for a in ARMS}))
nq = len(out)
print(f"SET={SET}: {nq} questions; m_x on-demand encode+score per question {secs / nq:.3f} s (19 options + K)")
for a in ARMS: print(f"{a:8s} top-1 {np.mean([o[a] == 1 for o in out]):.3f}  top-3 {np.mean([o[a] <= 3 for o in out]):.3f}  MRR {np.mean([1 / o[a] for o in out]):.3f}")
if SET == "fresh":
    rng = np.random.default_rng(0)
    for a, b in (("m_x", "m_title"), ("m_a", "m_x"), ("m_x", "k"), ("m_x", "jev_pass"), ("g_x", "g_title")):
        dd = np.array([(o[a] == 1) - (o[b] == 1) for o in out], float); bt = [dd[rng.integers(0, nq, nq)].mean() for _ in range(4000)]
        print(f"top-1 {a} − {b}: {dd.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]")
json.dump(out, open(f"out/srbn-match-{SET}.json", "w"))
