"""D3 (REGISTERED-D3.md), $0: remove door memberships that a passage's neighbourhood doesn't vote for; score
read-set PPR (mean per target) by width-matched within-wave AUC, dev to choose q, test held out.

    uv run --with scipy --with numpy python d3.py   (from the scratchpad's dream/d1; needs repo at ~/code/avalanche-d1)
"""
import json, gzip, subprocess, collections, random, sys
import numpy as np, scipy.sparse as sp

REPO = "/Users/sirsh/code/avalanche-d1"
ALPHA, ITERS, BETA = 0.15, 25, 0.85
def golds(g): return set(g.keys()) if isinstance(g, dict) else set(g)
def git_gz(p): return [json.loads(l) for l in gzip.decompress(subprocess.run(["git", "-C", REPO, "show", f"origin/main:{p}"], capture_output=True).stdout).decode().splitlines() if l.strip()]

class G:
    def __init__(s, rows):
        s.ids = [r["d"] for r in rows]; s.ix = {d: i for i, d in enumerate(s.ids)}; s.n = len(s.ids)
        s.kix = {}; mem = []
        for i, r in enumerate(rows):
            for k in r["keys"]:
                mem.append((i, s.kix.setdefault(k, len(s.kix))))
        s.mem = np.array(mem)  # (passage, key) memberships
        s.own = {}  # owned doors: ("next"|"near", u) -> targets
        for i, r in enumerate(rows):
            for kind in ("next", "near"):
                t = [s.ix[x] for x in r[kind] if x in s.ix and s.ix[x] != i]
                if t: s.own[(kind, i)] = t
        s.build(np.ones(len(s.mem), bool), set(s.own))
    def build(s, keep, owned):
        s.keep, s.owned = keep, owned
        m = s.mem[keep]; nk = len(s.kix)
        s.A = sp.csr_matrix((np.ones(len(m)), (m[:, 0], m[:, 1])), shape=(s.n, nk))
        s.df = np.asarray(s.A.sum(0)).ravel()
        k = np.where(s.df >= 2, 1.0 / np.maximum(s.df - 1, 1), 0.0)
        s.k = k
        s.post = {}  # lazily: key -> members
        ri, ci, v = [], [], []
        for (kind, u) in owned:
            t = s.own[(kind, u)]
            ri += [u] * len(t); ci += t; v += [1.0 / len(t)] * len(t)
        s.O = sp.csr_matrix((v, (ri, ci)), shape=(s.n, s.n))
        nd = np.asarray((s.A[:, s.df >= 2]).sum(1)).ravel() + np.asarray((s.O > 0).sum(1)).ravel() * 0
        nown = np.zeros(s.n)
        for (kind, u) in owned: nown[u] += 1
        s.nd = nd + nown
        s.selfk = s.A @ k
        s.Ac = s.A.tocsc()
    def members(s, j):
        if j not in s.post: s.post[j] = s.Ac.indices[s.Ac.indptr[j]:s.Ac.indptr[j + 1]]
        return s.post[j]
    def step(s, P):  # P: n x m mass; returns T^T P
        Q = P / np.maximum(s.nd, 1)[:, None]
        out = s.A @ (s.k[:, None] * (s.A.T @ Q)) - s.selfk[:, None] * Q
        out += s.O.T @ Q
        return out
    def ppr(s, seeds):  # list of index lists
        R = np.zeros((s.n, len(seeds)))
        for c, ss in enumerate(seeds):
            if ss: R[ss, c] = 1.0 / len(ss)
        P = ALPHA * R.copy(); X = R.copy()
        for _ in range(ITERS):
            X = (1 - ALPHA) * s.step(X); P += ALPHA * X
        return P
    def targets(s, key, R):
        kind, x = key.split(":", 1)
        if kind == "term":
            j = s.kix.get(x)
            if j is None or s.df[j] < 2 or s.df[j] > 100: return None
            mem = set(s.members(j).tolist())
            if not (mem & R): return None
            return mem - R
        u = s.ix.get(x)
        if u is None or (kind, u) not in s.owned or u not in R: return None
        return set(s.own[(kind, u)]) - R

def score(g, waves):
    """waves: (R ids, [(key, gold set)] , gold) -> width-matched AUC of mean PPR, share of waves with a gold door"""
    W = []
    for R, keys, gold in waves:
        Ri = {g.ix[d] for d in R if d in g.ix}; Gi = {g.ix[d] for d in gold if d in g.ix}
        doors = []
        for k in keys:
            t = g.targets(k, Ri)
            if t: doors.append((k, t, bool(t & Gi)))
        W.append((sorted(Ri), doors))
    P = g.ppr([w[0] for w in W])
    right = tot = 0; hasg = 0; n = 0
    for c, (Ri, doors) in enumerate(W):
        if not doors: continue
        n += 1; hasg += any(d[2] for d in doors)
        sc = [(P[list(t), c].mean(), len(t), y) for _, t, y in doors]
        pos = [x for x in sc if x[2]]; neg = [x for x in sc if not x[2]]
        for a in pos:
            for b in neg:
                if max(a[1], b[1]) <= 2 * min(a[1], b[1]):
                    tot += 1; right += (a[0] > b[0]) + 0.5 * (a[0] == b[0])
    return right / max(tot, 1), hasg / max(n, 1), tot

def votes(g, K=30):
    """Membership vote: u's one-step walk weight to the door's other members through its OTHER doors, plus BETA times
    the two-step weight (top-K sparsified), averaged over those members, relative to u's median over its doors.
    Returns ratio per key membership and per owned door."""
    A, k = g.A, g.k
    Wk = (A.multiply(k).tocsr() @ A.T).tocsr()
    ri, ci = [], []
    for d in g.owned:
        for v in g.own[d]: ri += [d[1], v]; ci += [v, d[1]]
    L = sp.csr_matrix((np.ones(len(ri)), (ri, ci)), shape=(g.n, g.n))
    W = (Wk + L).tocsr(); W.setdiag(0); W.eliminate_zeros()
    deg = np.asarray(W.sum(1)).ravel()
    Wn = (sp.diags(1 / np.maximum(deg, 1e-9)) @ W).tocsr()
    r_, c_, v_ = [], [], []
    for u in range(g.n):
        s0, e0 = Wn.indptr[u], Wn.indptr[u + 1]
        t = np.argsort(-Wn.data[s0:e0])[:K]
        r_ += [u] * len(t); c_ += Wn.indices[s0:e0][t].tolist(); v_ += Wn.data[s0:e0][t].tolist()
    Wt = sp.csr_matrix((v_, (r_, c_)), shape=(g.n, g.n))
    W2 = (Wt @ Wt).tocsr()
    Ac = A.tocsc(); Ar = A.tocsr()
    mem_of = {}
    by_u = collections.defaultdict(list)
    for idx, (u, j) in enumerate(g.mem):
        if g.keep[idx] and 2 <= g.df[j] <= 100: by_u[u].append((idx, j))
    own_u = collections.defaultdict(list)
    for d in g.owned: own_u[d[1]].append(d)
    raw = np.full(len(g.mem), np.nan); oraw = {}
    d1 = np.zeros(g.n); d2 = np.zeros(g.n)
    for u in set(by_u) | set(own_u):
        a0, a1 = Wn.indptr[u], Wn.indptr[u + 1]; b0, b1 = W2.indptr[u], W2.indptr[u + 1]
        d1[Wn.indices[a0:a1]] = Wn.data[a0:a1]; d2[W2.indices[b0:b1]] = W2.data[b0:b1]; d2[u] = 0
        for idx, j in by_u[u]:
            M = Ac.indices[Ac.indptr[j]:Ac.indptr[j + 1]]; M = M[M != u]
            own = k[j] / max(deg[u], 1e-9)
            raw[idx] = (d1[M].sum() - own * len(M)) / len(M) + BETA * d2[M].mean()
        for d in own_u[u]:
            t = g.own[d]
            oraw[d] = (d1[t].sum() - len(t) / max(deg[u], 1e-9)) / len(t) + BETA * d2[t].mean()
        d1[Wn.indices[a0:a1]] = 0; d2[W2.indices[b0:b1]] = 0
    per_u = collections.defaultdict(list)
    for u, lst in by_u.items(): per_u[u] += [raw[i] for i, _ in lst]
    for d, v in oraw.items(): per_u[d[1]].append(v)
    med = {u: np.median(v) for u, v in per_u.items()}
    ratio = np.full(len(g.mem), np.inf)
    for u, lst in by_u.items():
        if med.get(u, 0) > 0:
            for i, _ in lst: ratio[i] = raw[i] / med[u]
    oratio = {d: (v / med[d[1]] if med.get(d[1], 0) > 0 else np.inf) for d, v in oraw.items()}
    return ratio, oratio

def edit(g, q, rounds=4, log=None, high=False):
    keep, owned = g.keep.copy(), set(g.owned)
    for r in range(rounds):
        ratio, oratio = votes(g)
        if high:
            drop = keep & np.isfinite(ratio) & (ratio > q); odrop = {d for d in owned if np.isfinite(oratio.get(d, np.inf)) and oratio[d] > q}
        else:
            drop = keep & (ratio < q); odrop = {d for d in owned if oratio.get(d, np.inf) < q}
        changed = (drop.sum() + len(odrop)) / (keep.sum() + len(owned))
        keep = keep & ~drop; owned = owned - odrop
        g.build(keep, owned)
        if log is not None: log.append(f"round {r+1}: removed {drop.sum()} key memberships and {len(odrop)} owned doors ({changed:.3%})")
        if changed < 0.01: break
    return keep, owned

def random_edit(g, keep, owned, seed=1):
    rng = np.random.default_rng(seed)
    nk = (~keep).sum(); no = len(set(g.own) - owned)
    k2 = np.ones(len(g.mem), bool); k2[rng.choice(len(g.mem), nk, replace=False)] = False
    allo = sorted(g.own); o2 = set(allo) - {allo[i] for i in rng.choice(len(allo), no, replace=False)}
    return k2, o2

def dev_waves(c):
    gold = {r["qid"]: golds(r["gold"]) for r in map(json.loads, open(f"../dt-{c}.jsonl"))}
    return [(set(w["reads_before"]), [d["key"] for d in w["doors"]], gold[w["qid"]]) for w in map(json.loads, open(f"b-{c}.jsonl"))]
def test_waves(c, tf, qf):
    gold = {r["qid"]: golds(r["gold"]) for r in map(json.loads, open(qf))}
    reads = {}
    for t in map(json.loads, open(tf)):
        for w in {d["wave"] for d in t["documents"]}:
            reads[(t["qid"], w)] = {d["id"] for d in t["documents"] if d["wave"] < w}
    keys = collections.defaultdict(list)
    for r in git_gz(f"evals/structural/out/ft-{c}.jsonl.gz"): keys[(r["qid"], r["wave"])].append(r["key"])
    return [(reads[qw], ks, gold[qw[0]]) for qw, ks in keys.items() if qw in reads]

TESTF = {"cards": ("../../floor/trace-cards.jsonl", "../../floor/q-cards.jsonl"), "prs": ("../../floor/trace-pr.jsonl", "../../floor/q-prs-test.jsonl"), "mq": ("../../floor/trace-mq.jsonl", "../../floor/q-musique-questions.jsonl")}
for gname, sets in [("p8", ["cards", "prs"]), ("mq", ["mq"])]:
    g = G([json.loads(l) for l in open(f"graph-{gname}.jsonl")])
    dev = {c: dev_waves(c) for c in sets}; test = {c: test_waves(c, *TESTF[c]) for c in sets}
    k0, o0 = g.keep.copy(), set(g.owned)
    res = {}
    base = {c: score(g, dev[c]) for c in sets}
    print(f"{gname}: dev G0 " + ", ".join(f"{c} {base[c][0]:.3f} (gold door {base[c][1]:.2f}, pairs {base[c][2]})" for c in sets), flush=True)
    best = None
    HIGH = "--high" in sys.argv
    for q in ((2, 4, 8, 16) if HIGH else (0.05, 0.1, 0.2, 0.4)):
        g.build(k0, o0); log = []
        keep, owned = edit(g, q, log=log, high=HIGH)
        d = {c: score(g, dev[c]) for c in sets}
        reward = np.mean([d[c][0] for c in sets])
        print(f"  q={q}: {'; '.join(log)} | dev " + ", ".join(f"{c} {d[c][0]:.3f} (gold door {d[c][1]:.2f})" for c in sets), flush=True)
        if best is None or reward > best[0]: best = (reward, q, keep, owned)
    _, q, keep, owned = best
    print(f"  chosen q={q} on dev", flush=True)
    for c in sets:
        g.build(k0, o0); t0 = score(g, test[c])
        g.build(keep, owned); te = score(g, test[c])
        rk, ro = random_edit(g, keep, owned); g.build(rk, ro); tr = score(g, test[c])
        print(f"  TEST {c}: G0 {t0[0]:.3f} (gold door {t0[1]:.2f}, pairs {t0[2]}) | G_edit {te[0]:.3f} (gold door {te[1]:.2f}) | random removal {tr[0]:.3f} (gold door {tr[1]:.2f})", flush=True)
    g.build(k0, o0)
