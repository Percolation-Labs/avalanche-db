"""SR-TW: a null for relational twins (THEORY-SR item 3). $0, token-free. See REGISTERED-SRTW.md.

The walk is SR1c's: Jev's measured conductance (β 1.0, γ 3.7) on gen's worlds, landing on s, reach h = G/diag(G).
The relational null is the same walk with γ = 0. That's the mean-field expectation over random relation labels: replacing
each link's bonus by its mean scales every conductance by the same factor, which cancels in P. The surprise
    rel(v) = log h_γ(s→v) − log h_0(s→v)
measures how far the question's relations *selected* the route to v over its alternatives. A uniform bonus on every door
of a region changes no current split inside it (only ratios at a node matter), so relations that are merely present
score nothing. relKL(v) = h_γ · rel is v's term in KL(h_γ ‖ h_0); it has no parameter.
Conditions on case D (the cluster lure), built after gen.world so its draws are unchanged:
  clean   gen's D.
  labels  every link inside the cluster relabelled r1 or r2 at random: relations present everywhere, selecting nothing.
  chain   lure0–lure1 relabelled r2 and lure0's other cluster links to unnamed relations: a twin of s –r1→ b –r2→ a.
Arms: raw h_γ (SR1c's comb), rel, relKL, and cs.py's degree null (mean h_γ from the starts of s's degree), as deg, degKL.
    uv run --with numpy --with scipy python srtw.py"""
import json
import numpy as np
import gen, net
from sr1 import rank, ALPHA

BETA, GAMMA, ATYPE, NOISE = 1.0, 3.7, 0.8605, 1.0  # SR1c's, all measured or calibrated there
SEEDS = (61001, 61002, 61003, 61004)  # fresh
ARMS = ("raw", "rel", "relKL", "deg", "degKL")


def relabel(w, c, cond, rng):
    """returns a copy of w's rel list with case c's cluster relabelled per cond."""
    rel = list(w["rel"]); L = set(c["lures"]); r1, r2 = c["r1"], c["r2"]
    other = [r for r in range(gen.RELS) if r not in (r1, r2)]
    for e, (u, v) in enumerate(w["edges"]):
        if u in L and v in L:
            if cond == "labels": rel[e] = int(rng.choice([r1, r2]))
            elif cond == "chain":
                l0, l1 = c["lures"][0], c["lures"][1]
                rel[e] = r2 if {u, v} == {l0, l1} else (int(rng.choice(other)) if l0 in (u, v) else rel[e])
    return rel


def degree_null(w, s, H):
    deg = np.zeros(len(w["V"]), int)
    for u, v in w["edges"]: deg[u] += 1; deg[v] += 1
    by = {}
    for i, d in enumerate(deg): by.setdefault(int(d), []).append(i)
    own = [j for j in by[int(deg[s])] if j != s]
    if not own:
        dd = min((d for d in by if d != deg[s]), key=lambda d: (abs(d - deg[s]), d)); own = by[dd]
    return H[own].mean(0)


def score(w, c, rel):
    ww = dict(w, rel=rel); s, x = c["s"], c["probes"]["x"]
    Pg, _ = net.conductance_jev(ww, c, x, BETA, GAMMA); P0, _ = net.conductance_jev(ww, c, x, BETA, 0.0)
    H = net.reach(Pg, ALPHA); p = H[s]; q = net.reach(P0, ALPHA)[s]; qd = degree_null(w, s, H)
    lg = lambda z: np.log(np.maximum(z, 1e-300))
    rl, dg = lg(p) - lg(q), lg(p) - lg(qd)
    return dict(raw=p, rel=rl, relKL=p * rl, deg=dg, degKL=p * dg)


def main():
    lines, res = [], []
    def say(t): print(t, flush=True); lines.append(t)
    for sd in SEEDS:
        w = gen.world(sd, NOISE, ATYPE)
        for c in w["cases"]:
            conds = ("clean", "labels", "chain") if c["name"].startswith("D") else ("clean",)
            for cond in conds:
                rel = relabel(w, c, cond, np.random.default_rng(sd + 2)) if cond != "clean" else list(w["rel"])
                sc = score(w, c, rel); ex = {c["s"]}
                r = dict(seed=sd, case=c["name"][0], cond=cond)
                for k in ARMS:
                    r[k] = dict(a=rank(sc[k], c["a"], ex), b=rank(sc[k], c["b"], ex),
                                lure=min((rank(sc[k], u, ex) for u in c["lures"]), default=None))
                res.append(r)
                say(f"{sd} {c['name'][0]} {cond:<6} rank a (b) [best lure]: " + ", ".join(
                    f"{k} {r[k]['a']} ({r[k]['b']})" + (f" [{r[k]['lure']}]" if r[k]["lure"] else "") for k in ARMS))
    say("== a in the top 5, by case/condition (of 4 seeds); and D: a above every lure")
    for ct, cond in (("A", "clean"), ("B", "clean"), ("C", "clean"), ("D", "clean"), ("D", "labels"), ("D", "chain")):
        rs = [r for r in res if r["case"] == ct and r["cond"] == cond]
        say(f"  {ct} {cond:<6}: " + ", ".join(f"{k} {sum(r[k]['a'] <= 5 for r in rs)}/4" for k in ARMS)
            + ("; a above lures: " + ", ".join(f"{k} {sum(r[k]['a'] < r[k]['lure'] for r in rs)}/4" for k in ARMS) if ct == "D" else ""))
    open("out/srtw.txt", "w").write("\n".join(lines) + "\n"); json.dump(res, open("out/srtw.json", "w"), indent=1)


if __name__ == "__main__":
    main()
