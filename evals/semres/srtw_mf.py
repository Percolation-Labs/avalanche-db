"""SR-TW, unregistered check (bill's review 1): how far the γ = 0 mean-field null is from E_labels[h_γ].
All four seeds, D clean/labels/chain (descriptive, unregistered). 40 relabellings: each non-'is_a' link's relation drawn uniformly from the RELS relations
('is_a' links keep theirs, as in gen). Reports rank of a and the best lure under rel with each null."""
import numpy as np, gen, net, srtw
from sr1 import rank, ALPHA
def run(sd, cond):
    w = gen.world(sd, srtw.NOISE, srtw.ATYPE); c = w["cases"][3]; s, x = c["s"], c["probes"]["x"]
    base = srtw.relabel(w, c, cond, np.random.default_rng(sd + 2)) if cond != "clean" else list(w["rel"])
    wb = dict(w, rel=base); rng = np.random.default_rng(7); isa = w["isa"]; hs = []
    for _ in range(40):
        rel = [r if r == isa else int(rng.integers(gen.RELS)) for r in base]
        P, _ = net.conductance_jev(dict(w, rel=rel), c, x, srtw.BETA, srtw.GAMMA); hs.append(net.reach(P, ALPHA)[s])
    E = np.mean(hs, 0)
    P0, _ = net.conductance_jev(wb, c, x, srtw.BETA, 0.0); h0 = net.reach(P0, ALPHA)[s]
    Pg, _ = net.conductance_jev(wb, c, x, srtw.BETA, srtw.GAMMA); hg = net.reach(Pg, ALPHA)[s]
    lg = lambda z: np.log(np.maximum(z, 1e-300)); ex = {s}; out = []
    for nm, q in (("h0", h0), ("E", E)):
        r = lg(hg) - lg(q); ra = rank(r, c["a"], ex); rl = min(rank(r, u, ex) for u in c["lures"])
        out.append(f"{nm} a {ra} lure {rl}{' a>lures' if ra < rl else ''}")
    d = lg(E) - lg(h0); d[s] = np.nan
    print(f"{sd} D {cond:<6} log E/h0 median {np.nanmedian(d):+.2f}; rel under " + "; ".join(out), flush=True)
for sd in srtw.SEEDS:
    for cond in ("clean", "labels", "chain"): run(sd, cond)
