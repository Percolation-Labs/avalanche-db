"""SR (1): reach probability under one conductance that joins structure and semantics. $0, token-free.
Gate first: the exact solver must match Monte Carlo walkers (the check that can fail). Then, for each world seed and
case type, from the landing passage s (the seed the question gives), the rank of the answer a and the bridge b among
all other passages under:
  struct    h with every conductance 1
  sem       cos(x, v): vector search, no graph
  comb      h with the Bayes conductance (net.conductance)
  comb+L    the edge walk (inductance), hit by the walk's budget of 25 steps
plus comb's hit-by-25 for a direct comparison with comb+L, and τ (steps to 1 − 1/e of the hit-by-25 value).
    uv run --with numpy --with scipy python sr1.py [--gate-only]"""
import sys, json
import numpy as np
import gen, net

ALPHA, ITERS = .15, 25  # L1's restart and the walk's step budget; stated, not chosen here


def rank(score, v, exclude):
    s = score.astype(float).copy(); s[list(exclude)] = -np.inf
    return int((s > s[v]).sum()) + 1


def tau(M):
    end = M[-1]
    return int(np.argmax(M >= (1 - np.exp(-1)) * end)) if end > 0 else -1


def gate(w, c):
    rng = np.random.default_rng(1)
    out = []
    for name, sem in (("struct", False), ("comb", True)):
        P, _ = net.conductance(w, c["probes"]["x"], semantic=sem)
        h = net.reach(P, ALPHA)[c["s"]]
        N = 20000; mc = net.monte_carlo(P, ALPHA, c["s"], N, rng)
        vs = sorted(set([c["b"], c["a"]] + list(np.argsort(-h)[1:11])))
        z = [abs(mc[v] - h[v]) / max(np.sqrt(h[v] * (1 - h[v]) / N), 1e-12) for v in vs]
        out.append((name, len(vs), max(z), sum(x > 3 for x in z)))
    return out


def main():
    lines = []
    def say(x): print(x, flush=True); lines.append(x)
    w0 = gen.world(gen.SEEDS[0])
    g = gate(w0, w0["cases"][1])
    for name, k, zmax, bad in g:
        say(f"GATE {name}: {k} passages, max |MC − exact| = {zmax:.2f} binomial s.d., {bad} beyond 3")
    if any(b > 0 for *_, b in g):
        say("GATE FAILED: stop"); open("out/sr1.txt", "w").write("\n".join(lines) + "\n"); sys.exit(1)
    if "--gate-only" in sys.argv: return
    res = []
    for sd in gen.SEEDS:
        w = gen.world(sd)
        for c in w["cases"]:
            s, a, b, x = c["s"], c["a"], c["b"], c["probes"]["x"]
            Ps, _ = net.conductance(w, x, semantic=False); Pc, _ = net.conductance(w, x)
            hs, hc = net.reach(Ps, ALPHA)[s], net.reach(Pc, ALPHA)[s]
            sem = w["V"] @ x
            n = len(w["V"])
            src = np.zeros(n); src[s] = 1
            Mc = net.arrival(Pc, ALPHA, src, list(range(n)), ITERS)
            Q, states, by_head, mu = net.edge_walk(w, Pc)
            m0 = net.edge_start(Pc, states, s)
            Ml = net.edge_arrival(Q, ALPHA, m0, s, by_head, list(range(n)), ITERS)
            r = dict(seed=sd, case=c["name"])
            for nm, sc in (("struct", hs), ("sem", sem), ("comb", hc), ("comb@25", Mc[-1]), ("comb+L@25", Ml[-1])):
                r[nm] = (rank(sc, a, {s}), rank(sc, b, {s}))
            r["tau_a"] = (tau(Mc[:, a]), tau(Ml[:, a])); r["hit_a@25"] = (float(Mc[-1, a]), float(Ml[-1, a]))
            hub_share = float(sum(hc[h] for h in w["hubs"])); r["hub_h_sum"] = (float(sum(hs[h] for h in w["hubs"])), hub_share)
            res.append(r)
            say(f"{sd} {c['name']:<15} rank of a (b): " + ", ".join(f"{k} {r[k][0]} ({r[k][1]})" for k in ("struct", "sem", "comb", "comb@25", "comb+L@25"))
                + f"; hit a by 25: {r['hit_a@25'][0]:.4f} → L {r['hit_a@25'][1]:.4f}; τ {r['tau_a'][0]} → {r['tau_a'][1]}; μ_nn {mu:.3f}")
    say("== per case type: seeds where a ranks in the top 5 (the walk's read budget)")
    for ct in ("A", "B", "C", "D"):
        rs = [r for r in res if r["case"].startswith(ct)]
        say(f"  {ct}: " + ", ".join(f"{k} {sum(r[k][0] <= 5 for r in rs)}/{len(rs)}" for k in ("struct", "sem", "comb", "comb@25", "comb+L@25"))
            + f"; L raises hit-by-25 on {sum(r['hit_a@25'][1] > r['hit_a@25'][0] for r in rs)}/{len(rs)}")
    open("out/sr1.txt", "w").write("\n".join(lines) + "\n"); json.dump(res, open("out/sr1.json", "w"), indent=1)


if __name__ == "__main__":
    main()
