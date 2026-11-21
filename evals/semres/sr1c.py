"""SR1c: SR1b's worlds under Jev's measured conductance (net.conductance_jev). Otherwise SR1b; see REGISTERED-SR1c.md.
SR1b's docstring follows.
SR1b: SR1's reach question in the real regime. $0, token-free. Calibrated to MuSiQue, not derived from the generator:
  - semantic slope β = 8.7 nats per cos unit (bill's Bayes slope of hop-2 gold on cos, 200 dev questions, bge-small),
    the same for passages, links and direction memory (net.conductance_beta, net.edge_walk_beta);
  - the question's answer-type weight ATYPE, bisected on discarded seeds (calib.py) to MuSiQue's hop-1 − hop-2 cos gap .146.
Fresh seeds, never looked at before this registration. Landing on s, per world-case:
  rank of a (b) under struct, sem, comb, comb@25, comb+L@25; hit-by-25 at a under comb and comb+L; exact h(a) against
  the chain formula (1−α)² P(s→b) P(b→a) / (1 − (1−α)² P(s→b) P(b→s)).
Gates: Monte Carlo against exact on the first world's case B (for the reach numbers); the formula comparison is exact
against exact and needs none.
    uv run --with numpy --with scipy python sr1b.py"""
import json
import numpy as np
import gen, net
from sr1 import rank, ALPHA, ITERS

BETA, ATYPE, NOISE = 1.0, 0.8605, 1.0  # β is Jev's (MuSiQue); argv[2] overrides with another corpus's measured β
SEEDS = (41001, 41002, 41003, 41004)
import sys
GAMMA = float(sys.argv[1]) if len(sys.argv) > 1 else 3.7  # Jev's γ; 3.3 and 4.1 are its interval ends (sensitivity, not a fit)
if len(sys.argv) > 2: BETA = float(sys.argv[2])
TAG = f"{GAMMA}" + (f"-b{BETA}" if len(sys.argv) > 2 else "")


def main():
    lines = []
    def say(x): print(x, flush=True); lines.append(x)
    w0 = gen.world(SEEDS[0], NOISE, ATYPE); c0 = w0["cases"][1]
    P0, _ = net.conductance_jev(w0, c0, c0["probes"]["x"], BETA, GAMMA); h0 = net.reach(P0, ALPHA)[c0["s"]]
    N = 20000; mc = net.monte_carlo(P0, ALPHA, c0["s"], N, np.random.default_rng(1))
    vs = sorted(set([c0["b"], c0["a"]] + list(np.argsort(-h0)[1:11])))
    z = max(abs(mc[v] - h0[v]) / max(np.sqrt(h0[v] * (1 - h0[v]) / N), 1e-12) for v in vs)
    say(f"GATE: max |MC − exact| {z:.2f} s.d. over {len(vs)} passages")
    if z > 3: say("GATE FAILED"); open(f"out/sr1c-{TAG}.txt", "w").write("\n".join(lines) + "\n"); return
    res = []
    for sd in SEEDS:
        w = gen.world(sd, NOISE, ATYPE); n = len(w["V"])
        for c in w["cases"]:
            s, b, a, x = c["s"], c["b"], c["a"], c["probes"]["x"]
            Ps, _ = net.conductance(w, x, semantic=False); Pc, _ = net.conductance_jev(w, c, x, BETA, GAMMA)
            hs, hc = net.reach(Ps, ALPHA)[s], net.reach(Pc, ALPHA)[s]
            src = np.zeros(n); src[s] = 1
            Mc = net.arrival(Pc, ALPHA, src, list(range(n)), ITERS)
            Q, states, by_head = net.edge_walk_beta(w, Pc, BETA)
            Ml = net.edge_arrival(Q, ALPHA, net.edge_start(Pc, states, s), s, by_head, list(range(n)), ITERS)
            k = (1 - ALPHA) ** 2; f = k * Pc[s, b] * Pc[b, a] / (1 - k * Pc[s, b] * Pc[b, s])
            r = dict(seed=sd, case=c["name"], exact=float(hc[a]), formula=float(f), cross=float(-np.log(max(Pc[b, a], 1e-300))),
                     hit25=(float(Mc[-1, a]), float(Ml[-1, a])))
            for nm, sc in (("struct", hs), ("sem", w["V"] @ x), ("comb", hc), ("comb@25", Mc[-1]), ("comb+L@25", Ml[-1])):
                r[nm] = (rank(sc, a, {s}), rank(sc, b, {s}))
            res.append(r)
            say(f"{sd} {c['name']:<15} rank a (b): " + ", ".join(f"{k_} {r[k_][0]} ({r[k_][1]})" for k_ in ("struct", "sem", "comb", "comb@25", "comb+L@25"))
                + f"; hit a by 25 {r['hit25'][0]:.4f} → L {r['hit25'][1]:.4f}; cross {r['cross']:.2f} nats; h(a) {r['exact']:.5f} formula {f:.5f}")
    say("== seeds (of 4) where a ranks in the top 5")
    for ct in "ABCD":
        rs = [r for r in res if r["case"].startswith(ct)]
        say(f"  {ct}: " + ", ".join(f"{k_} {sum(r[k_][0] <= 5 for r in rs)}/4" for k_ in ("struct", "sem", "comb", "comb@25", "comb+L@25"))
            + f"; median crossing {np.median([r['cross'] for r in rs]):.2f} nats")
    open(f"out/sr1c-{TAG}.txt", "w").write("\n".join(lines) + "\n"); json.dump(res, open(f"out/sr1c-{TAG}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
