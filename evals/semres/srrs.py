"""SR-RS (REGISTERED-SRRS.md), bill. Reward scale without a unit: each door membership (passage, key) is weighted by its
success rate over the learn walks that used it, shrunk toward the corpus rate rho = W/N with prior strength 2
(Laplace's convention): m = (w + 2 rho) / ((n + 2) rho). n = 0 gives exactly 1. 'Used' = both ends (e, k) and (s, k)
of every shared key k the step crossed, as SR-BC's event. S_m[e, v] = sum_k m(e,k) m(v,k) / (df_k - 1).
Arms: none; T* (SR-BC's fixed point); RATE (failures and successes); RATE-W (successes only, n = w).
RATE's iteration: weights from the current walks of all learn questions; run until the walk tuple repeats; period 1 =
fixed point, else the test arm is the mean of the cycle's multipliers.
    uv run --with numpy --with sentence-transformers python srrs.py TRAIN_CORPUS GRAPH_TRAIN"""
import hashlib, json, re, sys
from collections import Counter, defaultdict
import numpy as np
src, gpath = sys.argv[1], sys.argv[2]; LOOK = "--look" in sys.argv
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
half = lambda mid: int(hashlib.sha256(mid.encode()).hexdigest()[:8], 16) % 2
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
bx = set(np.random.default_rng(1341).permutation(len(qs))[:304].tolist())   # SR-BX's 300 + stage 0
learn = [i for i in range(len(qs)) if half(qs[i]["id"]) == 0]
test = [i for i in range(len(qs)) if half(qs[i]["id"]) == 1 and i not in bx]
import os
cache = os.environ.get("SRBC_CACHE", "srbc-emb.npz"); Ec = dict(np.load(cache)) if os.path.exists(cache) else {}
C = {}; m = None; QP = "Represent this sentence for searching relevant passages: "
for i in learn + test:
    r = qs[i]; P = sorted(r["paragraphs"], key=lambda p: p["idx"]); ids = [hid(p) for p in P]
    qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    D = [{k for k in keys.get(x, ()) if 2 <= df[k] <= 100 and not set(k.split()) <= qt} for x in ids]
    if r["id"] not in Ec:
        if m is None:
            from sentence_transformers import SentenceTransformer
            m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")
        E = m.encode([QP + r["question"]] + [p["title"] + ". " + p["paragraph_text"] for p in P], normalize_embeddings=True)
        Ec[r["id"]] = E[1:] @ E[0]
    d = r["question_decomposition"]; ix = {p["idx"]: j for j, p in enumerate(P)}
    C[i] = dict(ids=ids, D=D, cq=Ec[r["id"]], h1=ix[d[0]["paragraph_support_idx"]], h2=ix[d[1]["paragraph_support_idx"]])
if m is not None: np.savez(cache, **Ec)
pair = lambda c: frozenset((c["ids"][c["h1"]], c["ids"][c["h2"]]))
lpairs = {pair(C[i]) for i in learn}
shared = {i for i in test if pair(C[i]) in lpairs}
print(f"2-hop questions {len(qs)}; learn {len(learn)}; test {len(test)} (SR-BX's 304 excluded); test questions sharing a learn gold pair {len(shared)}")
def walk(c, r):
    n = len(c["ids"]); e = int(np.argmax(c["cq"])); ue = c["ids"][e]
    S = np.array([sum((1 + r.get((ue, k), 0)) * (1 + r.get((c["ids"][v], k), 0)) / (df[k] - 1) for k in c["D"][e] & c["D"][v]) if v != e else -1.0 for v in range(n)])
    s = max(np.nonzero(S == S.max())[0], key=lambda u: c["cq"][u]) if S.max() > 0 else [v for v in np.argsort(-c["cq"]) if v != e][0]
    return e, int(s)
def events(c, e, s):
    out = []
    for k in c["D"][e] & c["D"][s]:
        nS = sum(1 for v in range(len(c["ids"])) if v != e and k in c["D"][v])
        out += [((c["ids"][e], k), 1 / nS), ((c["ids"][s], k), 1 / nS)]
    return out
def apply(r, evs):
    r = dict(r)
    for key, w in evs: r[key] = r.get(key, 0) + w
    return r
ok = lambda c, e, s: {e, s} == {c["h1"], c["h2"]}


def walkm(c, M):
    n = len(c["ids"]); e = int(np.argmax(c["cq"])); ue = c["ids"][e]
    S = np.array([sum(M.get((ue, k), 1.0) * M.get((c["ids"][v], k), 1.0) / (df[k] - 1) for k in c["D"][e] & c["D"][v]) if v != e else -1.0 for v in range(n)])
    s = max(np.nonzero(S == S.max())[0], key=lambda u: c["cq"][u]) if S.max() > 0 else [v for v in np.argsort(-c["cq"]) if v != e][0]
    return e, int(s)
def used(c, e, s): return [(c["ids"][e], k) for k in c["D"][e] & c["D"][s]] + [(c["ids"][s], k) for k in c["D"][e] & c["D"][s]]
def rate(walks, succ_only):
    n, w = Counter(), Counter(); W = sum(ok(C[i], *walks[i]) for i in learn); rho = W / len(learn)
    for i in learn:
        o = ok(C[i], *walks[i])
        if succ_only and not o: continue
        for key in used(C[i], *walks[i]): n[key] += 1; w[key] += o
    return {key: (w[key] + 2 * rho) / ((n[key] + 2) * rho) for key in n}, rho
def iterate(succ_only, lab):
    M = {}; seq = []; seen = {}; p = 0
    while True:
        walks = {i: walkm(C[i], M) for i in learn}; tup = tuple(walks[i] for i in learn)
        sr = np.mean([ok(C[i], *walks[i]) for i in learn])
        if tup in seen:
            cyc = seq[seen[tup]:]; period = len(cyc)
            print(f"{lab}: walk tuple repeats after pass {p}; " + ("FIXED POINT" if period == 1 else f"CYCLE of period {period}"))
            if period == 1: return cyc[0]
            ks = set().union(*cyc); return {k: sum(m.get(k, 1.0) for m in cyc) / period for k in ks}
        seen[tup] = len(seq)
        M, rho = rate(walks, succ_only); seq.append(M); p += 1
        vals = np.array(list(M.values()))
        print(f"{lab} pass {p}: learn success under previous weights {sr:.3f}; rho {rho:.3f}; memberships {len(M)}; "
              f"m < 1: {(vals < 1).sum()}, m > 1: {(vals > 1).sum()}; median n=1 success m {np.round((1 + 2*rho)/(3*rho), 3)}")
# T*: SR-BC's fixed point (one pass of R plus the 5-question adjustment); rebuild as srbc.py does
def succ(r): return frozenset(i for i in learn if ok(C[i], *walk(C[i], r)))
r = {}; S = succ(r)
while True:
    r_new = apply({}, [ev for i in sorted(S) for ev in events(C[i], *walk(C[i], r))]); S_new = succ(r_new)
    if S_new == S: break
    r, S = r_new, S_new
Tstar = r_new
Mr = iterate(False, "RATE"); Mw = iterate(True, "RATE-W")
res = {"none": np.array([int(ok(C[i], *walk(C[i], {}))) for i in test]),
       "Tstar": np.array([int(ok(C[i], *walk(C[i], Tstar))) for i in test]),
       "RATE": np.array([int(ok(C[i], *walkm(C[i], Mr))) for i in test]),
       "RATE-W": np.array([int(ok(C[i], *walkm(C[i], Mw))) for i in test])}
assert abs(res["Tstar"].mean() - 0.418) < 0.0015, "T* must reproduce SR-BC's .418"
for k, v in res.items(): print(f"test both hops {k:7s} {v.mean():.3f}")
rng = np.random.default_rng(0)
def ci(d, lab):
    bt = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]
    print(f"{lab}: {d.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}] (n {len(d)})")
ci(res["RATE"] - res["Tstar"], "PRIMARY RATE − T*")
for a, b in (("RATE", "none"), ("RATE-W", "Tstar"), ("RATE-W", "none"), ("RATE", "RATE-W")): ci(res[a] - res[b], f"{a} − {b}")
for k in ("Tstar", "RATE", "RATE-W"):
    d = res[k] - res["none"]; print(f"flips vs unweighted {k}: gained {(d > 0).sum()}, lost {(d < 0).sum()}")
d = res["RATE"] - res["Tstar"]; print(f"flips RATE vs T*: gained {(d > 0).sum()}, lost {(d < 0).sum()}")
json.dump({k: v.tolist() for k, v in res.items()} | {"test": test}, open("out/srrs.json", "w"))
