"""Unregistered sensitivity for SR1b (bill's block check, out/srj-look-blocks.txt): SR1b recalibrated to MuSiQue dev
questions 201–1252 instead of the first 200 (β 9.3 against 8.7; hop gap .688 − .584 = .104 against .146).
ATYPE is re-bisected on calib.py's discarded seeds to the new gap; SR1b then reruns unchanged on its own seeds.
    uv run --with numpy --with scipy python sr1b_blocks.py"""
import json, numpy as np
import calib, sr1b
calib.TARGET = .688 - .584
lo, hi = 0.0, 1.5
for _ in range(20):
    mid = (lo + hi) / 2
    if calib.gap(mid) > calib.TARGET: lo = mid
    else: hi = mid
print(f"atype {mid:.4f}: median gap {calib.gap(mid):.4f} (target {calib.TARGET:.3f})")
sr1b.BETA, sr1b.ATYPE = 9.3, mid
_open = open
def redirect(p, *a, **k): return _open(p.replace("out/sr1b.", "out/sr1b-blocks."), *a, **k)
sr1b.open = redirect
sr1b.main()
