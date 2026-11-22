"""SR-BH2 readout (REGISTERED-SRBH2.md): paired over SR-BH's 200 chains, from out/srbh-fresh.json (H reads) and
out/srbh-fresh-spare.json (H + 1 reads). Bootstrap as srbh.py's (seed 0, 2000 resamples)."""
import json
import numpy as np
load = lambda f: {x["id"]: x for x in json.load(open(f)) if "id" in x}
A, B = load("out/srbh-fresh.json"), load("out/srbh-fresh-spare.json"); ids = sorted(A)
ok = lambda x, w: float(set(x["hops"]) <= set(x["walk"][w]))
c0, p0 = np.array([ok(A[i], "cheap") for i in ids]), np.array([ok(A[i], "pass") for i in ids])
c1, p1 = np.array([ok(B[i], "cheap") for i in ids]), np.array([ok(B[i], "pass") for i in ids])
def boot(d, B_=2000):
    rng = np.random.default_rng(0); i = rng.integers(0, len(d), (B_, len(d))); m = d[i].mean(1)
    return f"{d.mean():+.3f} [{np.quantile(m, .025):+.3f}, {np.quantile(m, .975):+.3f}]", np.quantile(m, .025), np.quantile(m, .975)
print(f"all hops at H: cheap {c0.mean():.3f}, pass {p0.mean():.3f}; at H+1: cheap {c1.mean():.3f}, pass {p1.mean():.3f} (n {len(ids)})")
r1, lo1, _ = boot(p1 - p0); print(f"pass(H+1) − pass(H): {r1}")
print(f"cheap(H+1) − cheap(H): {boot(c1 - c0)[0]}")
print(f"cheap − pass at H+1: {boot(c1 - p1)[0]}")
r2, _, hi2 = boot((c1 - p1) - (c0 - p0)); print(f"DiD [(cheap − pass) at H+1] − [(cheap − pass) at H]: {r2}")
print(f"H-O (order shown): {'PASS' if lo1 > 0 and hi2 < 0 else 'FAIL'}")
ch = lambda X, w: np.mean([X[i]["ch"][w] for i in ids])
print(f"input chars at H+1: cheap {ch(B, 'cheap'):,.0f}, pass {ch(B, 'pass'):,.0f}, ratio {ch(B, 'cheap') / ch(B, 'pass'):.3f}")
# SR-BH's divergence classes: did the pass walk recover with the spare read?
for cls in ("skips", "off"):
    sel = []
    for i in ids:
        x = A[i]; H = x["hops"]; wc, wp = x["walk"]["cheap"], x["walk"]["pass"]
        if not (ok(x, "cheap") and not ok(x, "pass")) or wc == wp: continue
        k = next(k for k in range(len(wc)) if wc[k] != wp[k]); last = wc[k - 1]
        pp = H.index(wp[k]) + 1 if wp[k] in H else None; lp = H.index(last) + 1 if last in H else None
        c = "off" if pp is None else "skips" if lp and abs(pp - lp) > 1 else "adjacent"
        if c == cls: sel.append(i)
    print(f"SR-BH cheap wins where pass {cls}: {len(sel)}; pass completes with the spare read in {int(sum(ok(B[i], 'pass') for i in sel))}")
