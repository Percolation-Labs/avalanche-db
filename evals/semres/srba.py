"""SR-BA (look, $0, post hoc), bill. Sirsh 17:07Z: the target is the answer in the returned set. A-last (james, #98):
the walk's pair contains the gold last-hop passage (on 2-hop, h2). Re-scores SR-BC's fixed-point reward on A-last, and
runs the same fixed-point update with the reward itself defined as A-last instead of the gold pair.
    uv run --with numpy --with sentence-transformers python srba.py TRAIN_CORPUS GRAPH_TRAIN"""
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


alast = lambda c, e, s: c["h2"] in (e, s)
def fixed_point(okr, lab):
    succ = lambda r: frozenset(i for i in learn if okr(C[i], *walk(C[i], r)))
    r = {}; S = succ(r); p = 0
    while True:
        p += 1; r_new = apply({}, [ev for i in sorted(S) for ev in events(C[i], *walk(C[i], r))]); S_new = succ(r_new)
        print(f"{lab} pass {p}: rewarded {len(S)}; learn rate now {len(S_new)/len(learn):.3f}")
        if S_new == S: return r_new
        if p > len(learn): sys.exit("no fixed point")   # cannot happen without a cycle; reported if it does
        r, S = r_new, S_new
W = {"none": {}, "T*pair": fixed_point(ok, "reward=gold pair"), "T*alast": fixed_point(alast, "reward=A-last")}
rng = np.random.default_rng(0)
def ci(d):
    bt = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]
    return f"{d.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]"
res = {}
for name, w in W.items():
    wk = [walk(C[i], w) for i in test]
    res[name, "both"] = np.array([int(ok(C[i], *x)) for i, x in zip(test, wk)])
    res[name, "alast"] = np.array([int(alast(C[i], *x)) for i, x in zip(test, wk)])
for m in ("alast", "both"):
    print(f"-- test measure {m}: " + ", ".join(f"{n} {res[n, m].mean():.3f}" for n in W))
    for n in ("T*pair", "T*alast"):
        d = res[n, m] - res["none", m]; print(f"   {n} − none {ci(d)}  gained {(d>0).sum()} lost {(d<0).sum()}")
    print(f"   T*alast − T*pair {ci(res['T*alast', m] - res['T*pair', m])}")
json.dump({f"{a}|{b}": v.tolist() for (a, b), v in res.items()} | {"test": test}, open("out/srba.json", "w"))
