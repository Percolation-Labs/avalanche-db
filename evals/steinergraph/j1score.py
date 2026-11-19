"""Score REGISTERED-J1.md.    uv run --with scipy --with numpy python j1score.py SCRATCH J1DIR"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l1 import G, load, UNI  # noqa: E402

scr, jd = sys.argv[1:3]
g = G([json.loads(l) for l in open(f"{scr}/dream/d1/graph-mq.jsonl")])
_, test = load(scr, g, "mq")
gold = {q: gi for q, _, gi, _, _ in test}; order = [q for q, *_ in test]
p2 = {r["qid"]: r for r in map(json.loads, open("out/p2-mq.jsonl"))}
res = {v: [p2[q]["seed_sets"][v]["total10"] for q in order] for v in ("single", "blind", "filled")}
ent = {v: [p2[q]["seed_sets"][v]["entry"] for q in order] for v in ("single", "blind", "filled")}
acc = {}
for ch in ("T", "O", "J"):
    R = {r["qid"]: r for r in map(json.loads, open(f"{jd}/j1-{ch}.jsonl"))}
    seeds = [[g.ix[d] for d in R[q]["seeds"] if d in g.ix] for q in order]
    P, _ = g.run(seeds, UNI)
    tot, en = [], []
    for c, (q, s) in enumerate(zip(order, seeds)):
        p = P[:, c].copy(); p[s] = -1
        top = [int(t) for t in np.argsort(-p)[:5] if p[t] > 0]
        tot.append(len(gold[q] & (set(s) | set(top))) / len(gold[q])); en.append(sum(1 for x in s if x in gold[q]))
    res[ch] = tot; ent[ch] = en
    picks = [p for r in R.values() for p in r["picks"]]
    ok = [p for p in picks if p["gold_is_cand"]]
    acc[ch] = (sum(p["correct"] for p in ok), len(ok), len(picks))

def boot(a, b, n=2000):
    d = np.array(a) - np.array(b); r = np.random.default_rng(0)
    bs = [d[r.integers(0, len(d), len(d))].mean() for _ in range(n)]
    return d.mean(), *np.percentile(bs, [2.5, 97.5])

print("MuSiQue test, 150 questions: total recall at 10 reads (5 seeds + U's top 5), entry points")
for v in ("single", "blind", "T", "J", "O", "filled"):
    extra = f"  chooser right {acc[v][0]}/{acc[v][1]} (gold answer a candidate; {acc[v][2]} decisions)" if v in acc else ""
    print(f"  {v:<7} {np.mean(res[v]):.3f}  entry {np.mean(ent[v]):.2f}{extra}")
for a, b in (("J", "blind"), ("J", "T"), ("O", "blind"), ("J", "single")):
    m, lo, hi = boot(res[a], res[b]); print(f"  {a} − {b}: {m:+.3f} [{lo:+.3f}, {hi:+.3f}]")
m1, lo1, _ = boot(res["J"], res["blind"]); m2, lo2, _ = boot(res["J"], res["T"])
print(f"  gap closed, (J − blind) / (filled − blind): {(np.mean(res['J']) - np.mean(res['blind'])) / (np.mean(res['filled']) - np.mean(res['blind'])):.2f}")
print("J1:", "pass" if m1 >= .05 and lo1 > 0 and m2 >= .03 and lo2 > 0 else "fail")
