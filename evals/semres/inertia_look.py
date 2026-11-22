"""Inertia look (unregistered, $0, no Jev): does dreaming's D3 operator keep 'earned' structure? Semantic inductance (3).
D3 (evals/dream/d3/d3.py, unchanged: q = .05 as its registered dev run chose for MuSiQue, rounds <= 4, stop under 1%)
removes door memberships (passage, key) whose neighbourhood vote is low, round after round. Its vote never sees gold.
Earned membership: (passage, key) where the key is a door key (2 <= df <= 100) shared by two consecutive gold hops of some
MuSiQue dev answerable question (all hop counts). Gold labels only; D3 never sees them.
Per round, among live door memberships: removal rate for earned against the rest; the same within passages that hold an
earned membership (each passage's earned against its own other memberships); and within df bands.
    uv run --with scipy --with numpy python inertia_look.py D3_SRC GRAPH_MQ MUSIQUE_DEV"""
import collections, hashlib, json, sys
import numpy as np
src = open(sys.argv[1]).read(); src = src[:src.index("def random_edit")]   # D3's classes and functions, not its driver
ns = {}; exec(src, ns); G, votes = ns["G"], ns["votes"]
rows = [json.loads(l) for l in open(sys.argv[2])]; g = G(rows)
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
df0 = g.df.copy(); door = (df0[g.mem[:, 1]] >= 2) & (df0[g.mem[:, 1]] <= 100)
memix = {(int(u), int(j)): i for i, (u, j) in enumerate(g.mem)}
earned = np.zeros(len(g.mem), bool); related = np.zeros(len(g.mem), bool); nq = 0   # related: kind-matched control (james)
for r in map(json.loads, open(sys.argv[3])):
    if not r["answerable"]: continue
    P = {p["idx"]: p for p in r["paragraphs"]}; hops = [P[s["paragraph_support_idx"]] for s in r["question_decomposition"]]
    ids = [g.ix.get(hid(p)) for p in hops]; nq += 1
    ng = [g.ix.get(hid(p)) for p in r["paragraphs"] if p not in hops]; ng = [x for x in ng if x is not None and x not in ids]
    for ai in range(len(ng)):
        ra = set(rows[ng[ai]]["keys"])
        for bi in range(ai + 1, len(ng)):
            for k in ra & set(rows[ng[bi]]["keys"]):
                j = g.kix[k]
                if 2 <= df0[j] <= 100: related[memix[(ng[ai], j)]] = True; related[memix[(ng[bi], j)]] = True
    for a, b in zip(ids, ids[1:]):
        if a is None or b is None: continue
        ra, rb = set(rows[a]["keys"]), set(rows[b]["keys"])
        for k in ra & rb:
            j = g.kix[k]
            if 2 <= df0[j] <= 100:
                for u in (a, b): earned[memix[(u, j)]] = True
related &= ~earned
# df-match the control to earned: sample related memberships so each df value has the same count as earned (seed 0)
rng = np.random.default_rng(0); dfm = df0[g.mem[:, 1]]; ctrl = np.zeros(len(g.mem), bool)
for v, cnt in zip(*np.unique(dfm[earned & door], return_counts=True)):
    pool_ = np.nonzero(related & door & (dfm == v))[0]
    if len(pool_): ctrl[rng.choice(pool_, min(cnt, len(pool_)), replace=False)] = True
print(f"control: door memberships on keys shared by two NON-gold passages of one question's pool: {(related & door).sum()}; df-matched sample {ctrl.sum()}")
print(f"{nq} dev questions; door memberships {door.sum()}, earned {(earned & door).sum()} ({(earned & door).sum() / door.sum():.4f})")
keep = g.keep.copy(); owned = set(g.owned); Q = 0.05
band = np.digitize(df0[g.mem[:, 1]], [3, 6, 11, 31])   # df bands 2, 3-5, 6-10, 11-30, 31-100 (descriptive only)
hasE = collections.defaultdict(bool)
for i in np.nonzero(earned & door)[0]: hasE[int(g.mem[i, 0])] = True
inE = np.array([hasE[int(u)] for u in g.mem[:, 0]])
for rnd in range(4):
    ratio, oratio = votes(g)
    drop = keep & (ratio < Q); odrop = {d for d in owned if oratio.get(d, np.inf) < Q}
    live = keep & door
    def rate(mask): return drop[live & mask].sum() / max((live & mask).sum(), 1)
    line = f"round {rnd + 1}: removed earned {rate(earned):.3f} vs df-matched related control {rate(ctrl):.3f} vs other {rate(~earned):.3f}; within earned-holding passages: earned {rate(earned & inE):.3f} vs their other {rate(~earned & inE):.3f}"
    line += " | by df band (earned/other): " + " ".join(f"{b}:{rate(earned & (band == b)):.3f}/{rate(~earned & (band == b)):.3f}" for b in range(5))
    print(line, flush=True)
    changed = (drop.sum() + len(odrop)) / (keep.sum() + len(owned)); keep = keep & ~drop; owned = owned - odrop; g.build(keep, owned)
    print(f"   changed {changed:.3%}; live earned {(keep & earned & door).sum()}, live other {(keep & ~earned & door).sum()}", flush=True)
    if changed < 0.01: break
f = keep & door
print(f"survived all rounds: earned {f[earned & door].mean():.3f}, df-matched related control {f[ctrl].mean():.3f}, all related {f[related & door].mean():.3f}, other {f[~earned & door].mean():.3f}")
