"""SR (2), (3) and storage (REGISTERED-SR23.md), bill. $0, token-free, james's gen.py and net.py.
For each world seed × case type, every arm at the walk's budget of 25 steps (L1's ITERS) and restart α = .15:
  (2) probes vs the whole question at equal mass: hit-by-25 at a for x alone vs OR over k probes, each launched
      w.p. 1/k (expected walkers = 1 in both arms); comb (node walk) and comb+L (edge walk).
  (3) collision vs coverage: rank of a among all passages under mean pair collision h_i·h_j (raw, and log over the
      degree-null landing) vs under OR; P(all gold {s, b, a} reached) by OR, and by collision (≥2 probes each).
  (L) storage: expected visits to D's lures within 25 steps, comb vs comb+L.
Each probe lands on its search top 1 (argmax cos), as the question's walk does.
    uv run --with numpy --with scipy python sr23.py"""
import json
import numpy as np
import gen, net
from sr23core import matched_mass, collision, rank_of

ALPHA, ITERS = .15, 25


def probes_of(w, c):
    """james's probes, plus 'r2+type' (the questioner knows the answer's type, not the answer): R[r2] + the centroid of
    the answer topic's other passages, if gen.py doesn't already carry it. Registered as an assumption."""
    pr = dict(c["probes"])
    if "r2+type" not in pr:
        top = np.array(w["topic"]); same = np.nonzero(top == top[c["a"]])[0]; same = same[same != c["a"]]
        cen = w["V"][same].mean(0)
        v = w["R"][c["r2"]] + cen / np.linalg.norm(cen); pr["r2+type"] = v / np.linalg.norm(v)
    return pr


def deg_class_src(w, land, n):
    """uniform landing over passages with the landing passage's link count (the degree null)."""
    deg = np.zeros(n, int)
    for u, v in w["edges"]: deg[u] += 1; deg[v] += 1
    cls = np.nonzero(deg == deg[land])[0]; cls = cls[cls != land]
    if not len(cls):
        d = np.unique(deg[deg != deg[land]]); dd = d[np.argmin(np.abs(d - deg[land]))]; cls = np.nonzero(deg == dd)[0]
    src = np.zeros(n); src[cls] = 1 / len(cls); return src


def node_visits(P, land, nodes, steps):
    m = np.zeros(P.shape[0]); m[land] = 1; tot = 0.0
    for _ in range(steps):
        m = (1 - ALPHA) * (m @ P); tot += m[nodes].sum()
    return float(tot)


def edge_visits(Q, m0, by_head, nodes, steps):
    idx = [q for v in nodes for q in by_head[v]]
    m = (1 - ALPHA) * m0; tot = float(m[idx].sum())
    for _ in range(steps - 1):
        m = (1 - ALPHA) * (Q.T @ m)  # row mass times Q, as net.edge_arrival
        tot += float(m[idx].sum())
    return tot


def main():
    lines, res = [], []
    def say(x): print(x, flush=True); lines.append(x)
    for sd in gen.SEEDS:
        w = gen.world(sd); n = len(w["V"])
        for c in w["cases"]:
            s, b, a = c["s"], c["b"], c["a"]; gold = [s, b, a]
            pr = probes_of(w, c); names = list(pr)
            H, Hn, HL, lands = {}, {}, {}, {}
            for k in names:
                P, _ = net.conductance(w, pr[k]); land = int(np.argmax(w["V"] @ pr[k])); lands[k] = land
                src = np.zeros(n); src[land] = 1
                H[k] = net.arrival(P, ALPHA, src, list(range(n)), ITERS)[-1]
                Hn[k] = net.arrival(P, ALPHA, deg_class_src(w, land, n), list(range(n)), ITERS)[-1]
                Q, states, by_head, _ = net.edge_walk(w, P)
                HL[k] = net.edge_arrival(Q, ALPHA, net.edge_start(P, states, land), land, by_head, gold, ITERS)[-1]
                if k == "x" and c["lures"]:
                    vis = (node_visits(P, land, c["lures"], ITERS), edge_visits(Q, net.edge_start(P, states, land), by_head, c["lures"], ITERS))
            sub = [k for k in names if k != "x"]
            Hs = np.array([H[k] for k in sub]); Hns = np.array([Hn[k] for k in sub])
            HLs = np.array([HL[k] for k in sub])
            r = dict(seed=sd, case=c["name"], lands={k: int(v) for k, v in lands.items()},
                     land_is_gold={k: lands[k] in gold for k in names})
            # (2) at a: x alone vs probes at equal mass, node and edge walks
            r["x@a"] = float(H["x"][a]); r["probes@a"] = float(matched_mass(Hs)[a])
            r["xL@a"] = float(HL["x"][2]); r["probesL@a"] = float(matched_mass(HLs)[2])
            ex = set(lands.values())
            bl = [i for i, k in enumerate(sub) if k != "r2+type"]  # the registered second readout: james's probes only
            r["probes@a_blind"] = float(matched_mass(Hs[bl])[a]); r["probesL@a_blind"] = float(matched_mass(HLs[bl])[2])
            r["rank_a_blind"] = {"OR": rank_of(1 - np.prod(1 - Hs[bl], 0), [a], ex)[0], "collision": rank_of(collision(Hs[bl]), [a], ex)[0]}
            # (3) rank of a under OR vs collision (raw and over the degree null), over all passages but the landings
            ex = set(lands.values())
            OR = 1 - np.prod(1 - Hs, 0); col = collision(Hs)
            with np.errstate(all="ignore"):
                coll = np.where((col > 0) & (collision(Hns) > 0), np.log(col / collision(Hns)), np.nan)
            r["rank_a"] = {"OR": rank_of(OR, [a], ex)[0], "collision": rank_of(col, [a], ex)[0], "collision/null": rank_of(coll, [a], ex)[0]}
            orf = 1 - np.prod(1 - Hs[:, gold], 0)
            two = np.array([1 - np.prod(1 - Hs[:, g]) - sum(Hs[i, g] * np.prod(np.delete(1 - Hs[:, g], i)) for i in range(len(sub))) for g in gold])
            r["cover_OR"] = float(np.prod(orf)); r["cover_collide"] = float(np.prod(two))
            r["per_probe_a"] = {k: round(float(H[k][a]), 4) for k in names}
            if c["lures"]: r["lure_visits"] = vis
            res.append(r)
            say(f"{sd} {c['name']:<15} landings {r['land_is_gold']}; a hit by 25: x {r['x@a']:.4f}, probes {r['probes@a']:.4f}"
                f" | +L: x {r['xL@a']:.4f}, probes {r['probesL@a']:.4f}; per probe {r['per_probe_a']}")
            say(f"{'':25s} rank a: OR {r['rank_a']['OR']:.0f}, collision {r['rank_a']['collision']:.0f}, over null {r['rank_a']['collision/null']:.0f};"
                f" P(all gold) OR {r['cover_OR']:.4f}, collide(≥2) {r['cover_collide']:.6f}"
                + (f"; lure visits {vis[0]:.3f} → +L {vis[1]:.3f}" if c["lures"] else ""))
    say("== bars (≥3 of 4 seeds per case type)")
    for ct in "ABCD":
        rs = [r for r in res if r["case"].startswith(ct)]
        say(f"  {ct}: probes beat x at a, comb {sum(r['probes@a'] > r['x@a'] for r in rs)}/4, comb+L {sum(r['probesL@a'] > r['xL@a'] for r in rs)}/4;"
            f" collision ranks a worse than OR {sum(r['rank_a']['collision'] > r['rank_a']['OR'] for r in rs)}/4"
            + f" | without r2+type: probes beat x comb {sum(r['probes@a_blind'] > r['x@a'] for r in rs)}/4, comb+L {sum(r['probesL@a_blind'] > r['xL@a'] for r in rs)}/4,"
              f" collision worse than OR {sum(r['rank_a_blind']['collision'] > r['rank_a_blind']['OR'] for r in rs)}/4"
            + (f"; +L lowers lure visits {sum(r['lure_visits'][1] < r['lure_visits'][0] for r in rs)}/4" if ct == "D" else ""))
    open("out/sr23.txt", "w").write("\n".join(lines) + "\n"); json.dump(res, open("out/sr23.json", "w"), indent=1)


if __name__ == "__main__":
    main()
