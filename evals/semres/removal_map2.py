"""Removal-value map v2 (james's review of #84): (1) earned split by question half, (2) equal-fraction removals.
Half = int(sha256(musique id)[:8], 16) % 2. Scored on D3's dev waves of half 1 only. earned_heldout = bridges of
half-0 questions that are NOT bridges of any half-1 question; earned_scored = bridges of half-1 questions.
Table A: equal count N per class (N = the smallest class size, rounded down to 1,000). Table B: 10% of each class.
Removal-value map (unregistered, $0, no Jev): what does removing a door membership cost walks, by kind? The
'priced on walks' target for dreaming (NOTE-D3M). The graph is MuSiQue dev graph-mq, and the walks are D3's dev waves
(dt-mq + b-mq, seen). The score is D3's own: width-matched AUC of read-set PPR, and the share of waves with a gold door.
Classes of door memberships (2 <= df <= 100) at G0:
  vote decile 1..10   D3's neighbourhood vote ratio at G0 (low decile = what D3 at q .05 removes first)
  earned              key shared by two consecutive gold hops (inertia look)
  related             key shared by two non-gold passages of one pool (inertia look's control), not earned
Per class, 5 draws each remove 7,000 members (the size of the smallest class, earned, rounded down) and rebuild. Each is
scored against G0. Report the mean change with its standard error over draws.
    cd <d1 scratchpad> && uv run --with scipy --with numpy python removal_map.py D3_SRC MUSIQUE_DEV"""
import hashlib, json, sys
import numpy as np
src = open(sys.argv[1]).read(); src = src[:src.index("TESTF = ")]; ns = {}; exec(src, ns)
G, score, votes, dev_waves = ns["G"], ns["score"], ns["votes"], ns["dev_waves"]
rows = [json.loads(l) for l in open("graph-mq.jsonl")]; g = G(rows); dev_all = dev_waves("mq")
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
df0 = g.df.copy(); door = (df0[g.mem[:, 1]] >= 2) & (df0[g.mem[:, 1]] <= 100)
memix = {(int(u), int(j)): i for i, (u, j) in enumerate(g.mem)}
half = lambda mid: int(hashlib.sha256(mid.encode()).hexdigest()[:8], 16) % 2
earned = np.zeros(len(g.mem), bool); related = np.zeros(len(g.mem), bool); eh = {0: np.zeros(len(g.mem), bool), 1: np.zeros(len(g.mem), bool)}
for r in map(json.loads, open(sys.argv[2])):
    if not r["answerable"]: continue
    P = {p["idx"]: p for p in r["paragraphs"]}; hops = [P[s["paragraph_support_idx"]] for s in r["question_decomposition"]]
    ids = [g.ix.get(hid(p)) for p in hops]
    for a, b in zip(ids, ids[1:]):
        if a is None or b is None: continue
        for k in set(rows[a]["keys"]) & set(rows[b]["keys"]):
            j = g.kix[k]
            if 2 <= df0[j] <= 100:
                earned[memix[(a, j)]] = earned[memix[(b, j)]] = True; eh[half(r["id"])][memix[(a, j)]] = eh[half(r["id"])][memix[(b, j)]] = True
    ng = [g.ix.get(hid(p)) for p in r["paragraphs"] if p not in hops]; ng = [x for x in ng if x is not None and x not in ids]
    for ai in range(len(ng)):
        ra = set(rows[ng[ai]]["keys"])
        for bi in range(ai + 1, len(ng)):
            for k in ra & set(rows[ng[bi]]["keys"]):
                j = g.kix[k]
                if 2 <= df0[j] <= 100: related[memix[(ng[ai], j)]] = related[memix[(ng[bi], j)]] = True
related &= ~earned
ratio, _ = votes(g); fin = door & np.isfinite(ratio)
edges = np.quantile(ratio[fin], np.linspace(0, 1, 11)); dec = np.clip(np.searchsorted(edges, ratio, side="right") - 1, 0, 9)
classes = {f"vote decile {d + 1}": fin & (dec == d) for d in range(10)}
import json as _j
wq = [_j.loads(l)["qid"].split(":", 1)[1] for l in open("b-mq.jsonl")]
dev = [w for w, q in zip(dev_all, wq) if half(q) == 1]
classes.update(earned_heldout=eh[0] & ~eh[1] & door, earned_scored=eh[1] & door, related=related & door)
k0, o0 = g.keep.copy(), set(g.owned)
base = score(g, dev)
print(f"vote ratio at G0: q .05 sits at percentile {np.mean(ratio[fin] < 0.05):.3f} of finite door memberships", flush=True)
print(f"half-1 scoring waves {len(dev)} of {len(dev_all)}; base on them: AUC {base[0]:.4f}, gold-door {base[1]:.3f}", flush=True)
R = 5; rng = np.random.default_rng(0); N = int(min(m.sum() for m in classes.values()) // 1000 * 1000)
for title, size in ((f"TABLE A: equal count, {N} per class", lambda n: N), ("TABLE B: equal fraction, 10% of each class", lambda n: n // 10)):
    print(title, flush=True)
    for name, mask in classes.items():
        idx = np.nonzero(mask)[0]; da, dg = [], []; m_ = size(len(idx))
        for _ in range(R):
            k = k0.copy(); k[rng.choice(idx, m_, replace=False)] = False; g.build(k, o0); s = score(g, dev)
            da.append(s[0] - base[0]); dg.append(s[1] - base[1])
        da, dg = np.array(da), np.array(dg)
        print(f"  {name:15s} n {len(idx):6d} removed {m_:6d} | ΔAUC {da.mean():+.4f} ± {da.std(ddof=1) / np.sqrt(R):.4f} | per 1,000 {1000 * da.mean() / m_:+.5f} | Δgold-door {dg.mean():+.4f} ± {dg.std(ddof=1) / np.sqrt(R):.4f}", flush=True)
g.build(k0, o0)
