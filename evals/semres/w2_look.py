"""W2 pricing look (before registering), seen worlds 41001–41004 at SR-J-R's price (β 3.8, γ 3.2): does a probe
pivoted toward the asked type separate the answer from relational twins (case D)? The type direction is the centroid
of the passages of the answer's topic (estimated from the world's passages, not gen's T). Probe operations from vecops.
Reports rank of a and the best lure, per case."""
import numpy as np, gen, net, vecops as V
from sr1 import rank, ALPHA
BETA, GAMMA, ATYPE = 3.8, 3.2, 0.8605
for sd in (41001, 41002, 41003, 41004):
    w = gen.world(sd, 1.0, ATYPE); top = np.array(w["topic"])
    for c in w["cases"]:
        s, b, a, x = c["s"], c["b"], c["a"], c["probes"]["x"]
        T = V.combine(w["V"][top == top[a]]); S = w["V"][s]
        probes = dict(x=x, type=T, x_plus_type=V.rocchio(x, T[None]), x_out_s=V.pivot_out(x, S[None]),
                      x_out_s_plus_type=V.rocchio(V.pivot_out(x, S[None]), T[None]))
        line = []
        for nm, pr in probes.items():
            P, _ = net.conductance_jev(w, c, pr, BETA, GAMMA); h = net.reach(P, ALPHA)[s]
            ra = rank(h, a, {s}); rl = min((rank(h, u, {s}) for u in c["lures"]), default=0)
            line.append(f"{nm} {ra}" + (f"[{rl}]" if rl else ""))
        print(sd, c["name"][0], ", ".join(line))
