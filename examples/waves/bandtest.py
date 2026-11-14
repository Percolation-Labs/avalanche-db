"""Kept set vs ranked list with a borderline band (registered M-20261114-191028-1f60). Band .3-.7, cut .5, fixed."""
import json, sys, glob, os, itertools
W = os.path.expanduser("~/code/avalanche-db/examples/waves/questions")
gold = {}
for f in glob.glob(W + "/*.json"):
    d = json.load(open(f))
    if "set_data" in d: gold[d["question"]] = (os.path.basename(f)[:-5], set(d["gold"]))
for path in sys.argv[1:]:
    pools = {}
    for l in open(path):
        d = json.loads(l); pools.setdefault((d["question"], d["pool"], frozenset(d["scores"])), d["scores"])
    print(f"== {os.path.basename(path)}: {len(pools)} distinct pools")
    T = dict(err=0, inband=0, n=0, band=0, flip5=0, flipc=0, pairs=0)
    for q, (name, g) in sorted(gold.items(), key=lambda x: x[1][0]):
        ps = [s for (qq, _, _), s in pools.items() if qq == q]
        if not ps: continue
        err = inb = n = band = 0
        for s in ps:
            for k, p in s.items():
                n += 1; b = .3 <= p < .7; band += b
                if (p >= .5) != (k in g): err += 1; inb += b
        f5 = fc = pr = 0
        for a, b in itertools.combinations(ps, 2):
            for k in set(a) & set(b):
                pr += 1; f5 += (a[k] >= .5) != (b[k] >= .5)
                fc += (a[k] >= .7 and b[k] < .3) or (a[k] < .3 and b[k] >= .7)
        print(f"  {name:32s} pools {len(ps):3d} judged {n:5d}  cut errors {err:4d}, in band {inb:4d}  band share {band/n:.2f}"
              f"  shared pairs {pr:5d}: .5 flips {f5:4d}, confident flips {fc:4d}")
        for k, v in zip(T, (err, inb, n, band, f5, fc, pr)): T[k] += v
    print(f"  TOTAL: cut errors {T['err']}, in band {T['inband']} ({T['inband']/max(1,T['err']):.2f}); band share {T['band']/T['n']:.2f}; "
          f".5 flips {T['flip5']}/{T['pairs']}, confident flips {T['flipc']}/{T['pairs']}")
