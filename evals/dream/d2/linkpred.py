"""D2 (REGISTERED-D2.md), $0: edges learned as link prediction from training walks' co-gold pairs, scored on test.

    uv run --with scipy --with numpy --with scikit-learn python linkpred.py   (from the scratchpad's dream/d1)
"""
import json, itertools, collections, random, math, statistics as st
import numpy as np, scipy.sparse as sp
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

def golds(g): return set(g.keys()) if isinstance(g, dict) else set(g)
def qs(p): return [(q["qid"], golds(q["gold"])) for q in map(json.loads, open(p))]
K1, K2 = 30, 30
SETS = [("p8", ["../dt-cards.jsonl", "../dt-prs.jsonl", "../pool-cards.jsonl"],
         [("cards", "../../floor/trace-cards.jsonl", "../../floor/q-cards.jsonl"), ("prs", "../../floor/trace-pr.jsonl", "../../floor/q-prs-test.jsonl")]),
        ("mq", ["../dt-mq.jsonl"], [("mq", "../../floor/trace-mq.jsonl", "../../floor/q-musique-questions.jsonl")])]
for g, trains, tests in SETS:
    rows = [json.loads(l) for l in open(f"graph-{g}.jsonl")]
    ids = [r["d"] for r in rows]; ix = {d: i for i, d in enumerate(ids)}; n = len(ids)
    kix, kd = {}, []
    for i, r in enumerate(rows):
        for k in r["keys"]:
            j = kix.setdefault(k, len(kd))
            if j == len(kd): kd.append([])
            kd[j].append(i)
    df = np.array([len(x) for x in kd])
    A = sp.csr_matrix((np.ones(sum(df)), ([i for ds in kd for i in ds], [j for j, ds in enumerate(kd) for _ in ds])), shape=(n, len(kd)))
    W = (A.multiply(1.0 / np.maximum(df - 1, 1)).tocsr() @ A.T).tolil(); W.setdiag(0); W = W.tocsr()
    li, lj = [], []
    for i, r in enumerate(rows):
        for x in r["next"] + r["near"]:
            if x in ix and ix[x] != i: li.append(i); lj.append(ix[x])
    L = sp.csr_matrix((np.ones(len(li)), (li, lj)), shape=(n, n)); L = ((L + L.T) > 0).astype(float).tocsr()
    W = (W + L).tocsr(); W.eliminate_zeros()
    deg = np.asarray(W.sum(1)).ravel()
    # top-K1 neighbours per row
    r_, c_, v_ = [], [], []
    for u in range(n):
        s, e = W.indptr[u], W.indptr[u + 1]
        nb, w = W.indices[s:e], W.data[s:e]
        t = np.argsort(-w)[:K1]
        r_ += [u] * len(t); c_ += nb[t].tolist(); v_ += (w[t] / max(deg[u], 1e-9)).tolist()
    Wk = sp.csr_matrix((v_, (r_, c_)), shape=(n, n))
    W2 = (Wk @ Wk).tocsr()
    cand = set()
    for u in range(n):
        for M_ in (Wk, W2):
            s, e = M_.indptr[u], M_.indptr[u + 1]
            nb, w = M_.indices[s:e], M_.data[s:e]
            for v in nb[np.argsort(-w)[:K2 if M_ is W2 else K1]]:
                if v != u: cand.add((min(u, v), max(u, v)))
    cand = sorted(cand)
    Ak = [set(A.indices[A.indptr[i]:A.indptr[i + 1]]) for i in range(n)]
    def feats(u, v):
        sh = Ak[u] & Ak[v]
        return [W[u, v], W2[u, v] + W2[v, u], len(sh), math.log1p(min((df[j] for j in sh), default=200)), float(L[u, v] > 0), math.log1p(deg[u]) + math.log1p(deg[v]), abs(math.log1p(deg[u]) - math.log1p(deg[v]))]
    F = np.array([feats(u, v) for u, v in cand]); ci = {p: k for k, p in enumerate(cand)}
    linked = np.array([1.0 if (Ak[u] & Ak[v] or L[u, v] > 0) else 0.0 for u, v in cand])
    print(f"{g}: {n} passages, {len(cand)} candidate pairs, {linked.mean():.2f} already one door apart", flush=True)
    # training labels
    trq = [q for p in trains for q in qs(p)]
    tq = random.Random(0).sample(range(len(trq)), len(trq) // 5); hold = set(tq)
    def labelled(qlist):
        pos, touch = set(), set()
        for _, G in qlist:
            gi = sorted(ix[d] for d in G if d in ix)
            touch |= set(gi)
            for a, b in itertools.combinations(gi, 2): pos.add((a, b))
        idx = [k for k, (u, v) in enumerate(cand) if u in touch or v in touch]
        return idx, np.array([int(cand[k] in pos) for k in idx]), pos
    tr_idx, tr_y, tr_pos = labelled([q for k, q in enumerate(trq) if k not in hold])
    va_idx, va_y, _ = labelled([q for k, q in enumerate(trq) if k in hold])
    mu, sd = F.mean(0), F.std(0) + 1e-9; Z = (F - mu) / sd
    m = LogisticRegression(max_iter=2000, class_weight="balanced").fit(Z[tr_idx], tr_y)
    s = m.decision_function(Z)
    print(f"  train pairs {len(tr_idx)} (pos {tr_y.sum()}), held-back AUC learned {roc_auc_score(va_y, s[va_idx]):.2f} vs common-neighbour score {roc_auc_score(va_y, F[va_idx, 1]):.2f}")
    print("  coef " + ", ".join(f"{a} {c:+.2f}" for a, c in zip(["w1", "w2", "shared", "logmindf", "link", "degsum", "degdiff"], m.coef_[0])))
    allq = [q for p in trains for q in qs(p)]
    for c, tf, qf in tests:
        TQ = qs(qf); gp = []
        for _, G in TQ:
            gi = sorted(ix[d] for d in G if d in ix)
            gp += list(itertools.combinations(gi, 2))
        unl = [p for p in gp if not (Ak[p[0]] & Ak[p[1]] or L[p[0], p[1]] > 0)]
        cov = sum(1 for p in unl if p in ci) / max(len(unl), 1)
        tw = []
        gold = dict(TQ)
        for t in map(json.loads, open(tf)):
            docs = t["documents"]
            for w in sorted({d["wave"] for d in docs if d["wave"] > 0}):
                R = {ix[d["id"]] for d in docs if d["wave"] < w and d["id"] in ix}
                G = {ix[d] for d in gold[t["qid"]] if d in ix} - R
                if G: tw.append((R, G))
        out = [f"  test {c}: gold pairs {len(gp)}, unlinked {len(unl)} (in candidates {cov:.2f})"]
        for frac in (0.01, 0.05):
            N = int(frac * n)
            arms = {"learned": np.argsort(-s)[:N], "common-nb": np.argsort(-F[:, 1])[:N], "random": np.array(random.Random(1).sample(range(len(cand)), N))}
            for name, top in arms.items():
                E = {cand[k] for k in top}
                adj = collections.defaultdict(set)
                for u, v in E: adj[u].add(v); adj[v].add(u)
                a = sum(1 for p in unl if p in E) / max(len(unl), 1)
                b = st.mean(any(adj[r] & G for r in R) for R, G in tw)
                out.append(f"{name}@{frac:.0%} (N={N}): (a) unlinked gold pairs connected {a:.3f} | test waves where a written edge leads from a read passage to unread gold {b:.3f}")
        print("\n".join(out), flush=True)
