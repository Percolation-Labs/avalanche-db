"""Rank stability across pools (registered 14 Nov, M-20261114-111532-ed39): for each pair of distinct
pools of one question sharing >= 3 keys: Spearman rho, label flips at 0.5, median scale shift; per pool AUC gold vs not."""
import json, sys, statistics, itertools, glob, os
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions")
gold = {}
for f in glob.glob(W + "/*.json"):
    d = json.load(open(f))
    if "set_data" in d: gold[d["question"]] = (os.path.basename(f)[:-5], set(d["gold"]))
pools = {}
for l in open(sys.argv[1]):
    d = json.loads(l)
    pools.setdefault((d["question"], d["pool"], frozenset(d["scores"])), d["scores"])
def ranks(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0]*len(v); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j+1]] == v[o[i]]: j += 1
        for k in range(i, j+1): r[o[k]] = (i+j)/2
        i = j + 1
    return r
def rho(a, b):
    ra, rb = ranks(a), ranks(b)
    if len(set(ra)) < 2 or len(set(rb)) < 2: return None
    return statistics.correlation(ra, rb)
def auc(s, g):
    pos = [v for k, v in s.items() if k in g]; neg = [v for k, v in s.items() if k not in g]
    if not pos or not neg: return None
    return sum((p > n) + 0.5*(p == n) for p in pos for n in neg) / (len(pos)*len(neg))
rows = []
for q, (name, g) in sorted(gold.items(), key=lambda x: x[1][0]):
    ps = [(p, s) for (qq, p, _), s in pools.items() if qq == q]
    aucs = [a for _, s in ps if (a := auc(s, g)) is not None]
    pr = []
    for (pa, a), (pb, b) in itertools.combinations(ps, 2):
        sh = sorted(set(a) & set(b))
        if len(sh) < 3: continue
        r = rho([a[k] for k in sh], [b[k] for k in sh])
        if r is None: continue
        flips = sum((a[k] >= .5) != (b[k] >= .5) for k in sh) / len(sh)
        shift = statistics.median(b[k] - a[k] for k in sh)
        gs = [k for k in sh if k in g]; ns = [k for k in sh if k not in g]
        order = None
        if gs and ns:  # does every gold key outrank every non-gold key in both pools?
            order = all(min(x[k] for k in gs) > max(x[k] for k in ns) for x in (a, b))
        pr.append((r, flips, abs(shift), order, len(sh)))
    if not pr: print(f"{name}: {len(ps)} pools, no comparable pair"); continue
    print(f"{name}: {len(ps)} pools, {len(pr)} pairs; median rho {statistics.median(x[0] for x in pr):.2f} (min {min(x[0] for x in pr):.2f}); "
          f"flip median {statistics.median(x[1] for x in pr):.2f} max {max(x[1] for x in pr):.2f}; |shift| max {max(x[2] for x in pr):.2f}; "
          f"AUC per pool {min(aucs):.2f}-{max(aucs):.2f} (n={len(aucs)}); gold-above-all in both: {sum(1 for x in pr if x[3])}/{sum(1 for x in pr if x[3] is not None)}")
    rows += pr
print(f"ALL: {len(rows)} pairs; median rho {statistics.median(x[0] for x in rows):.2f}; pairs with flip >= .15: {sum(1 for x in rows if x[1] >= .15)}; "
      f"among those median rho {statistics.median([x[0] for x in rows if x[1] >= .15] or [0]):.2f}")
