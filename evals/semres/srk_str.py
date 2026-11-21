"""SR-K (REGISTERED-SRK.md), $0: is a shared key door a gold-free stand-in for SR-J's next-hop term?
    python3 srk.py MUSIQUE_DEV.jsonl GRAPH_MQ.jsonl out/srj-n40.json"""
import hashlib, json, re, sys
from collections import Counter
import numpy as np
src = {r["id"]: r for r in map(json.loads, open(sys.argv[1]))}
rows = [json.loads(l) for l in open(sys.argv[2])]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"]); res = json.load(open(sys.argv[3]))
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
door = lambda ks: {k for k in ks if 2 <= df[k] <= 100}
X, K, G, Y, Q = [], [], [], [], []
top, agree, rec, prec, ka_rec, ka_prec = [], [], [], [], [], []
for qi, c in enumerate(res["cases"]):
    r = src[c["id"]]; P = {p["idx"]: p for p in r["paragraphs"]}
    h1 = next(p for p in r["paragraphs"] if p["title"] + ". " + p["paragraph_text"] == c["read"])
    R = door(keys[hid(h1)]); qt = set(re.findall(r"[a-z0-9]+", c["q"].lower()))
    new = {k for k in R if not set(k.split()) <= qt}
    sh = [keys[hid(P[i])] & new for i in c["opts"]]
    ka = np.array([int(bool(keys[hid(P[i])] & R)) for i in c["opts"]])
    kn = np.array([int(bool(s)) for s in sh]); ks = np.array([sum(1 / (df[k] - 1) for k in s) for s in sh])
    h = c["h2"]; p = np.clip(np.array(c["p"]), 1e-4, 1 - 1e-4)
    pick = int(np.argmax(ks + 1e-6 * np.array(c["cos_qr"])))
    top.append(int(pick == h)); agree.append(int(pick == int(np.argmax(p))))
    rec.append(kn[h]); prec.extend(int(j == h) for j in np.nonzero(kn)[0])
    ka_rec.append(ka[h]); ka_prec.extend(int(j == h) for j in np.nonzero(ka)[0])
    for j in range(len(p)):
        X.append(c["cos"][j]); K.append(np.log1p(ks[j])); G.append(int(j == h)); Y.append(np.log(p[j] / (1 - p[j]))); Q.append(qi)
    pass
X, K, G, Y, Q = map(np.array, (X, K, G, Y, Q)); top = np.array(top)
rng = np.random.default_rng(0); nq = len(top)
bt = [top[rng.integers(0, nq, nq)].mean() for _ in range(2000)]; lo, hi = np.percentile(bt, [2.5, 97.5])

print(f"2. logk recall {np.mean(rec):.2f}, precision {np.mean(prec):.2f} over {len(prec)} marked options  (e: .90, .97)")
print(f"   k_any recall {np.mean(ka_rec):.2f}, precision {np.mean(ka_prec):.2f} over {len(ka_prec)} marked options")
print(f"3. k-pick = Jev's argmax in {np.mean(agree):.2f}")
byq = [np.nonzero(Q == i)[0] for i in range(nq)]; al = np.arange(len(Y))
def fit(ix, cols): return np.linalg.lstsq(np.c_[tuple(v[ix] for v in cols) + (np.ones(len(ix)),)], Y[ix], rcond=None)[0]
for name, cols in (("cos_q + logk", (X, K)), ("cos_q + logk + hop2", (X, K, G))):
    f = fit(al, cols); B = [fit(np.concatenate([byq[i] for i in rng.integers(0, nq, nq)]), cols) for _ in range(2000)]
    l, u = np.percentile(B, [2.5, 97.5], 0)
    print(f"4. {name:22s} " + ", ".join(f"{k} {f[i]:+.2f} [{l[i]:+.2f}, {u[i]:+.2f}]" for i, k in enumerate(name.split(" + "))))
