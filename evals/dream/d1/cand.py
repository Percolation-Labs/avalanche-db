"""D1 step 1: question-free candidate hubs from a store dump (d1-probe dump), one per passage, deduplicated.

The passage graph: two passages share weight 1/(df-1) per key they both hold (so each key adds 1 to a holder's
degree), plus 1 per next/near link (symmetrised). For each passage u, its neighbours are ordered by W[u,v]/deg(v)
(a one-step personalised PageRank) and the prefix of size 2-20 with the least conductance is the candidate.

    uv run --with scipy --with numpy python cand.py GRAPH.jsonl OUT.jsonl
"""
import json, sys
import numpy as np
import scipy.sparse as sp

graph, out = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(graph)]
ids = [r["d"] for r in rows]
ix = {d: i for i, d in enumerate(ids)}
n = len(ids)
kix, kdocs = {}, []
for i, r in enumerate(rows):
    for k in r["keys"]:
        j = kix.setdefault(k, len(kdocs))
        if j == len(kdocs):
            kdocs.append([])
        kdocs[j].append(i)
df = np.array([len(x) for x in kdocs])
ri = [i for j, ds in enumerate(kdocs) for i in ds]
ci = [j for j, ds in enumerate(kdocs) for i in ds]
A = sp.csr_matrix((np.ones(len(ri)), (ri, ci)), shape=(n, len(kdocs)))
Ak = A.multiply(1.0 / np.maximum(df - 1, 1)).tocsr()
W = (Ak @ A.T).tolil()
W.setdiag(0)
W = W.tocsr()
li, lj = [], []
for i, r in enumerate(rows):
    for x in r["next"] + r["near"]:
        if x in ix and ix[x] != i:
            li.append(i); lj.append(ix[x])
L = sp.csr_matrix((np.ones(len(li)), (li, lj)), shape=(n, n))
L = ((L + L.T) > 0).astype(float)
W = (W + L).tocsr()
W.eliminate_zeros()
deg = np.asarray(W.sum(axis=1)).ravel()
vol = deg.sum()
seen, cands = set(), []
for u in range(n):
    s, e = W.indptr[u], W.indptr[u + 1]
    nb, w = W.indices[s:e], W.data[s:e]
    if len(nb) == 0:
        continue
    order = nb[np.argsort(-(w / np.maximum(deg[nb], 1e-9)), kind="stable")][:19]
    S = np.concatenate([[u], order])
    sub = W[S][:, S].toarray()
    best, bk = None, None
    for k in range(2, len(S) + 1):
        inside = sub[:k, :k].sum() / 2
        v = deg[S[:k]].sum()
        cut = v - 2 * inside
        phi = cut / max(min(v, vol - v), 1e-9)
        if best is None or phi < best:
            best, bk = phi, k
    mem = S[:bk]
    key = frozenset(mem.tolist())
    if key in seen:
        continue
    seen.add(key)
    sub = sub[:bk, :bk]
    pairs = bk * (bk - 1) / 2
    held = {}
    for i in mem:
        for j in A.indices[A.indptr[i]:A.indptr[i + 1]]:
            held[j] = held.get(j, 0) + 1
    top = sorted(held.items(), key=lambda t: (-t[1], df[t[0]]))
    best_key_jacc = max((c / (bk + df[j] - c) for j, c in held.items()), default=0.0)
    if best_key_jacc >= 1.0:
        continue  # an existing key already holds exactly these passages
    cands.append({
        "members": [ids[i] for i in mem],
        "f": {
            "size": int(bk),
            "conductance": float(best),
            "cohesion": float((sub > 0).sum() / 2 / pairs),
            "density": float(sub.sum() / 2 / pairs),
            "mean_deg": float(deg[mem].mean()),
            "top_share": float(top[0][1] / bk) if top else 0.0,
            "top_df": float(df[top[0][0]]) if top else 0.0,
            "novelty": float(1 - best_key_jacc),
        },
        "label_keys": [t[0] for t in top[:3]],
    })
inv = {j: k for k, j in kix.items()}
with open(out, "w") as f:
    for c in cands:
        c["label_keys"] = [inv[j] for j in c["label_keys"]]
        f.write(json.dumps(c) + "\n")
print(n, "passages", len(kdocs), "keys", len(cands), "candidates", file=sys.stderr)
