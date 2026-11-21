"""SR-J amendment 2, $0: does the bridge entity's presence in v explain Jev's hop-2 term γ? Jev answers from out/srj-n40.json."""
import json, re, sys
import numpy as np
STOP = {"the", "and", "of", "in", "on", "for", "with", "from", "that", "this", "were", "was", "are"}
src, res = sys.argv[1], json.load(open(sys.argv[2]))
rows = {r["id"]: r for r in map(json.loads, open(src))}
X, E, G, Y, Q, QR = [], [], [], [], [], []
top1, prec, rec = [], [], []
for qi, c in enumerate(res["cases"]):
    r = rows[c["id"]]; ans = r["question_decomposition"][0]["answer"]
    P = {p["idx"]: (p["title"] + ". " + p["paragraph_text"]).lower() for p in r["paragraphs"]}
    toks = [t for t in re.findall(r"[a-z0-9]+", ans.lower()) if len(t) >= 4 and t not in STOP]
    def has(t): return ans.lower() in t or (toks and all(x in t for x in toks))
    e = np.array([int(has(P[i])) for i in c["opts"]]); h = c["h2"]
    p = np.clip(np.array(c["p"]), 1e-4, 1 - 1e-4); lp = np.log(p / (1 - p))
    for j in range(len(p)): X.append(c["cos"][j]); E.append(e[j]); G.append(int(j == h)); Y.append(lp[j]); Q.append(qi)
    rec.append(e[h]); prec.extend([int(j == h) for j in range(len(e)) if e[j]])
    s = e + 1e-3 * np.array(c["cos_qr"]); top1.append(int(np.argmax(s) == h))
X, E, G, Y, Q = map(np.array, (X, E, G, Y, Q))
def fit(ix, cols): return np.linalg.lstsq(np.c_[tuple(v[ix] for v in cols) + (np.ones(len(ix)),)], Y[ix], rcond=None)[0]
rng = np.random.default_rng(0); nq = Q.max() + 1; byq = [np.nonzero(Q == i)[0] for i in range(nq)]; al = np.arange(len(Y))
for name, cols in (("cos_q + e + hop2", (X, E, G)), ("cos_q + e", (X, E)), ("cos_q + hop2 (stage 1)", (X, G))):
    f = fit(al, cols); B = [fit(np.concatenate([byq[i] for i in rng.integers(0, nq, nq)]), cols) for _ in range(2000)]
    lo, hi = np.percentile(B, [2.5, 97.5], 0)
    print(f"{name:24s} " + ", ".join(f"{k} {f[i]:+.2f} [{lo[i]:+.2f}, {hi[i]:+.2f}]" for i, k in enumerate(name.split(" + "))))
print(f"e: recall for hop 2 {np.mean(rec):.2f}, precision {np.mean(prec):.2f} over {len(prec)} options with e = 1; e-decider top-1 {np.mean(top1):.2f}")
