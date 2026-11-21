"""SR1a: the price of a crossing. $0, token-free. Worlds are swept by topic noise (cos to topic .7 → about .25).
For each world and case (B bridge, C hub lure), landing on s:
  exact   h(a), the exact reach (net.reach)
  formula (1−α)² P(s→b) P(b→a) / (1 − (1−α)² P(s→b) P(b→s)): the chain s → b → a, with the s ↔ b back-current as
          a resonance (each return is another try at the crossing); Q = 1 / (1 − (1−α)² P(s→b) P(b→s))
  cross   −log P(b→a), the crossing cost in nats
  L       under direction memory: the back share at b after arriving from s, q_back = Q[(s→b), (b→s)], and q_fwd
Readout 1: log-log slope of exact on formula, with a 95% bootstrap over (seed, case). Pass if it covers 1.
Readout 2: q_back under direction memory below P(b→s) in ≥ 3 of 4 seeds at every noise.
Gate: stop as degenerate if any world-case's exact h(a) < 1/20000 (below what Monte Carlo could see), before any bar.
    uv run --with numpy --with scipy python sr1a.py"""
import sys, json
import numpy as np
import gen, net

ALPHA = .15
NOISE = (1.0, 1.5, 2.0, 3.0, 4.0)


def main():
    lines = []
    def say(x): print(x, flush=True); lines.append(x)
    rows = []
    for nz in NOISE:
        for sd in gen.SEEDS:
            w = gen.world(sd, nz)
            for c in w["cases"][1:3]:
                s, b, a = c["s"], c["b"], c["a"]
                P, _ = net.conductance(w, c["probes"]["x"])
                h = net.reach(P, ALPHA)[s, a]
                k = (1 - ALPHA) ** 2
                Qf = 1 / (1 - k * P[s, b] * P[b, s])
                f = k * P[s, b] * P[b, a] * Qf
                Qm, states, _, _ = net.edge_walk(w, P)
                idx = {st: i for i, st in enumerate(states)}
                row = Qm.getrow(idx[(s, b)]).toarray().ravel()
                qb, qf = float(row[idx[(b, s)]]), float(row[idx[(b, a)]])
                rows.append(dict(noise=nz, seed=sd, case=c["name"], exact=float(h), formula=float(f), Q=float(Qf),
                                 cross=float(-np.log(P[b, a])), back=float(P[b, s]), q_back=qb, q_fwd=qf))
                say(f"noise {nz} {sd} {c['name']:<11} h(a) {h:.5f} formula {f:.5f} (Q {Qf:.2f}); cross {-np.log(P[b, a]):.2f} nats; "
                    f"P(b→s) {P[b, s]:.3f} → L {qb:.3f}, P(b→a) {P[b, a]:.4f} → L {qf:.4f}")
    if min(r["exact"] for r in rows) < 1 / 20000:
        bad = [(r["noise"], r["seed"], r["case"]) for r in rows if r["exact"] < 1 / 20000]
        say(f"DEGENERATE: {len(bad)} world-cases below 1/20000, e.g. {bad[:3]}; no bar read")
    else:
        x = np.log([r["formula"] for r in rows]); y = np.log([r["exact"] for r in rows])
        slope = np.polyfit(x, y, 1)[0]
        rng = np.random.default_rng(0); n = len(rows)
        bs = [np.polyfit(x[i], y[i], 1)[0] for i in (rng.integers(0, n, n) for _ in range(2000))]
        lo, hi = np.percentile(bs, [2.5, 97.5])
        say(f"READOUT 1: slope of log exact on log formula {slope:.3f} [{lo:.3f}, {hi:.3f}] (n {n}); "
            f"median exact/formula {np.median(np.exp(y - x)):.2f} — {'PASS' if lo <= 1 <= hi else 'FAIL'}")
        ok = []
        for nz in NOISE:
            rs = [r for r in rows if r["noise"] == nz]
            seeds = {sd for sd in gen.SEEDS if all(r["q_back"] < r["back"] for r in rs if r["seed"] == sd)}
            ok.append(len(seeds) >= 3); say(f"  noise {nz}: direction memory lowers the back share in {len(seeds)}/4 seeds")
        say(f"READOUT 2: {'PASS' if all(ok) else 'FAIL'}")
    open("out/sr1a.txt", "w").write("\n".join(lines) + "\n"); json.dump(rows, open("out/sr1a.json", "w"), indent=1)


if __name__ == "__main__":
    main()
