"""$0 calibration: do the lexical arms move when graph-mq (Postgres-indexed, d1probe dump) is replaced by build_keys.py's
graph (percolate-core frequency in Python, same declared limits)? Seen sets only: SR-KB 0-299, SR-BN 600-899, SR-BT/BW 904-1171.
Arms: k (given gold hop 1, ties by qr), ceiling_k (gold bridge keys, ties by k then qr), cosdoor both-hops (SR-E2's walk).
    uv run --with sentence-transformers --with numpy python graph_calib.py MUSIQUE_DEV GRAPH_A GRAPH_B"""
import hashlib, json, re, sys, numpy as np
from collections import Counter
src, ga, gb = sys.argv[1:4]
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
held = set(np.random.default_rng(20261121).permutation(np.arange(40, len(qs)))[:40].tolist())
perm = [i for i in np.random.default_rng(1341).permutation(np.arange(40, len(qs))) if i not in held]
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
wd = lambda s: set(re.findall(r"[a-z0-9]+", s.lower()))
G = {}
for lab, g in (("A", ga), ("B", gb)):
    rows = [json.loads(l) for l in open(g)]; G[lab] = ({r["d"]: set(r["keys"]) for r in rows}, Counter(k for r in rows for k in r["keys"]))
emb = {}
def enc(qi, r, P, T, opts, h1):
    if qi not in emb:
        O = m.encode([T[i] for i in opts], normalize_embeddings=True)
        emb[qi] = (O @ m.encode([QP + r["question"] + " " + T[h1]], normalize_embeddings=True)[0],
                   m.encode([QP + r["question"]] + [T[i] for i in sorted(P)], normalize_embeddings=True))
    return emb[qi]
for name, sl in (("SR-KB 0-299", perm[:300]), ("SR-BN 600-899", perm[600:900]), ("SR-BT/BW 904-1171", perm[904:])):
    res = {(lab, a): [] for lab in G for a in ("k", "ceiling_k", "cosdoor")}
    for qi in sl:
        r = qs[qi]; d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
        P = {p["idx"]: p for p in r["paragraphs"]}; T = {i: P[i]["title"] + ". " + P[i]["paragraph_text"] for i in P}
        opts = sorted(i for i in P if i != h1); h = opts.index(h2); qt = wd(r["question"])
        qr, E = enc(qi, r, P, T, opts, h1); ids = sorted(P); cq = E[1:] @ E[0]; o = np.argsort(-cq); e = int(o[0])
        for lab, (keys, df) in G.items():
            W = lambda k: 1 / (df[k] - 1)
            R = {k for k in keys[hid(P[h1])] if 2 <= df[k] <= 100 and not set(k.split()) <= qt}
            B = {k for k in R if set(k.split()) <= wd(d[0]["answer"])}
            sh = [keys[hid(P[i])] & R for i in opts]; ks = np.array([sum(map(W, x)) for x in sh])
            tk = 1e-3 * ks / (ks.max() + 1e-9) + 1e-6 * qr
            res[lab, "k"].append(int((ks + 1e-6 * qr > (ks + 1e-6 * qr)[h]).sum()) == 0)
            cb = np.array([sum(W(k) for k in x if k in B) for x in sh]) + tk; res[lab, "ceiling_k"].append(int((cb > cb[h]).sum()) == 0)
            D = [{k for k in keys[hid(P[i])] if 2 <= df[k] <= 100 and not set(k.split()) <= qt} for i in ids]
            S = np.array([sum(W(k) for k in D[e] & D[v]) if v != e else -1.0 for v in range(len(ids))])
            s = max(np.nonzero(S == S.max())[0], key=lambda u: cq[u]) if S.max() > 0 else int(o[1])
            res[lab, "cosdoor"].append({ids[e], ids[s]} == {h1, h2})
    print(f"{name} (n {len(sl)}): " + "; ".join(f"{a} A {np.mean(res['A', a]):.3f} B {np.mean(res['B', a]):.3f}" for a in ("k", "ceiling_k", "cosdoor")))
