"""SR1b calibration, on seeds that are then discarded: bisect the question's answer-type weight until the planted
chain's median cos(x, s) − cos(x, a) equals MuSiQue's measured hop-1 against hop-2 gap (bill: .705 − .559 = .146)."""
import numpy as np, gen
CAL = tuple(range(9001, 9009)); TARGET = .705 - .559


def gap(at):
    g = []
    for sd in CAL:
        w = gen.world(sd, 1.0, at)
        for c in w["cases"][1:]:
            x = c["probes"]["x"]; g.append(float(w["V"][c["s"]] @ x - w["V"][c["a"]] @ x))
    return float(np.median(g))


lo, hi = 0.0, 1.5
for _ in range(20):
    mid = (lo + hi) / 2
    if gap(mid) > TARGET: lo = mid
    else: hi = mid
print(f"atype {mid:.4f}: median gap {gap(mid):.4f} (target {TARGET:.3f})")
