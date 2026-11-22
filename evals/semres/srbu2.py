"""SR-BU2 readout (REGISTERED-SRBU2.md): paired over SR-BH's 200 chains. A-last, returned-set size, input chars."""
import json
import numpy as np
L = lambda f: {x["id"]: x for x in json.load(open(f)) if "id" in x}
ARMS = {"cheap nocap H+1": (L("out/srbh-fresh-spare-nocap.json"), "cheap"), "cheap nocap H": (L("out/srbh-fresh-nocap.json"), "cheap"),
        "pass H": (L("out/srbh-fresh.json"), "pass"), "pass H+1": (L("out/srbh-fresh-spare-nocap.json"), "pass")}
ids = sorted(ARMS["pass H"][0])
def boot(d, B=2000):
    d = np.asarray(d, float); rng = np.random.default_rng(0); i = rng.integers(0, len(d), (B, len(d))); m = d[i].mean(1)
    return f"{d.mean():+.3f} [{np.quantile(m, .025):+.3f}, {np.quantile(m, .975):+.3f}] (n {len(d)})", np.quantile(m, .025)
al = {k: np.array([float(X[i]["hops"][-1] in X[i]["walk"][w]) for i in ids]) for k, (X, w) in ARMS.items()}
for k, (X, w) in ARMS.items():
    ch = np.mean([X[i]["ch"][w] for i in ids]); n = np.mean([len(X[i]["walk"][w]) for i in ids])
    print(f"{k:16s} A-last {al[k].mean():.3f}  returned set {n:.2f}  input {ch:,.0f}  A-last per 10k chars {al[k].mean() / ch * 1e4:.4f}")
r, lo = boot(al["cheap nocap H+1"] - al["pass H"])
print(f"PRIMARY (equal spend, not equal outcome for the reader) A-last cheap nocap H+1 − pass H: {r}; H-U3 {'PASS' if lo > -.05 else 'FAIL'}")
print(f"pass H+1 − pass H (reads alone): {boot(al['pass H+1'] - al['pass H'])[0]}")
print(f"cheap nocap H+1 − pass H+1 (equal reads): {boot(al['cheap nocap H+1'] - al['pass H+1'])[0]}")
