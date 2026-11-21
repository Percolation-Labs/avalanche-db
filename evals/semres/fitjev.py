"""$0 fit of Jev's door conductance on the 64 option sets of SR-JW2 (doors hide their links) and SR-JW3 (doors show them):
logit p_Jev = c + β·cos + γ_rel·[door's relation is r1/r2] + γ_type·[door is of the answer's type] + γ_read·[door already read],
least squares on logit p (bill's SR-J form), with a 95% bootstrap over option sets. Registered in REGISTERED-FITJEV.md."""
import json, hashlib, numpy as np
import gen, srjw2, srjw3
from sr1b import ATYPE, NOISE


def rows(mod):
    H = mod.hops(1)
    cache = {json.loads(l)["k"]: json.loads(l)["p"] for l in open(mod.CACHE)}
    key = lambda h: hashlib.sha256(json.dumps([h["q"], h["read"], h["texts"], mod.TASK]).encode()).hexdigest()
    W = {sd: gen.world(sd, NOISE, ATYPE, decoys=True) for sd in mod.SEEDS}
    out = []
    for g, h in enumerate(H):
        w = W[h["seed"]]; c = next(c for c in w["cases"] if c["name"] == h["case"]); ta = w["topic"][c["a"]]
        read = {c["s"]} if h["hop"] == 2 else set()
        p = np.clip(np.array(cache[key(h)]), 1e-4, 1 - 1e-4)
        for j, v in enumerate(h["opts"]):
            out.append((g, np.log(p[j] / (1 - p[j])), h["cos"][j], h["match"][j], int(w["topic"][v] == ta), int(v in read)))
    return np.array(out)


def fit(R):
    X = np.column_stack([np.ones(len(R)), R[:, 2], R[:, 3], R[:, 4], R[:, 5]]); y = R[:, 1]
    return np.linalg.lstsq(X, y, rcond=None)[0][1:]


for name, mod in (("SR-JW2 (doors hide links)", srjw2), ("SR-JW3 (doors show links)", srjw3)):
    R = rows(mod); b = fit(R); gs = np.unique(R[:, 0]); rng = np.random.default_rng(0)
    bs = np.array([fit(np.vstack([R[R[:, 0] == g] for g in rng.choice(gs, len(gs))])) for _ in range(1000)])
    lo, hi = np.percentile(bs, [2.5, 97.5], axis=0)
    print(f"{name}: {len(gs)} option sets, {len(R)} doors")
    for k, nm in enumerate(("β (cos)", "γ_rel", "γ_type", "γ_read")):
        print(f"  {nm:<8} {b[k]:+.2f} [{lo[k]:+.2f}, {hi[k]:+.2f}]")
