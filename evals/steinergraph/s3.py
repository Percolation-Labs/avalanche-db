"""S3 (REGISTERED-S2.md S3, with S2b/S2c amendments), $0: repair S2c's cuts from walks alone.
Candidates: passage pairs read together (seeds + top 5) by >= 2 questions' walks with no Beside door between them.
Gain: change in mean L2 coherence over the walks, strength matrix fixed from the drifted graph; greedy until no gain.
    uv run --with scipy --with numpy python s3.py SCRATCH SDIR SET [--time-only]"""
import json, sys, os, time, random, collections, itertools
import numpy as np, scipy.sparse as sp
import l1, l2, s2
from l1 import G, UNI, load, load_s, Fmat, recall5, boot, mean_ok
from s2b import costs
from s2c import tree_edges


def add_beside(g, pairs):
    g.Ori = np.concatenate([g.Ori] + [np.array([a, b]) for a, b in pairs]) if pairs else g.Ori
    g.Oci = np.concatenate([g.Oci] + [np.array([b, a]) for a, b in pairs]) if pairs else g.Oci
    g.Owid = np.concatenate([g.Owid, np.ones(2 * len(pairs))])
    for a, b in pairs: g.nd[a] += 1; g.nd[b] += 1


def main():
    scr, sdir, c = sys.argv[1], sys.argv[2], sys.argv[3]
    time_only = "--time-only" in sys.argv
    gname = "mq" if c == "mq" else "p8"
    rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gname}.jsonl")]
    s2c = json.load(open("out/s2c.json"))[c]["cases"]
    g0 = G(rows)
    cuts = collections.defaultdict(set)
    for q in s2c: cuts[g0.ix[q["v"]]].add(q["key"])
    rd = list(rows)
    for v, ks in cuts.items(): rd[v] = dict(rows[v], keys=[k for k in rows[v]["keys"] if k not in ks])
    cutpairs = {q["qid"]: (g0.ix[q["u"]], g0.ix[q["v"]]) for q in s2c}
    txt = []
    def say(s): print(s, flush=True); txt.append(s)
    dev, test = load(scr, g0, c)
    Sd, St = load_s(sdir, "dev", c, g0), load_s(sdir, "test", c, g0)
    qs = [(q, s_, gi, "dev") for q, s_, gi, *_ in dev] + [(q, s_, gi, "test") for q, s_, gi, *_ in test]
    seeds = [s_ for _, s_, _, _ in qs]
    Fa = np.hstack([Fmat(g0, [q for q, *_ in dev], Sd), Fmat(g0, [q for q, *_ in test], St)])
    def mk(rr, extra=()):
        g = G(rr); add_beside(g, list(extra)); return g
    gd = mk(rd); W, s, m2 = l2.strength(rd, gd)
    Ld = s2.links(gd)
    beside = set()
    for i, r in enumerate(rd):
        for x in r["next"]:
            j = g0.ix.get(x)
            if j is not None: beside.add((min(i, j), max(i, j)))
    def walks(g, cols=None):
        cols = list(range(len(qs))) if cols is None else cols
        P, _ = g.run([seeds[i] for i in cols], UNI, F=Fa[:, cols])
        return P, l2.tops(P, [seeds[i] for i in cols])
    def cohs(T, cols): return [l2.coherence(W, s, m2, seeds[i], t) for i, t in zip(cols, T)]
    def cands(T, added):
        cnt = collections.Counter()
        for i, t in enumerate(T):
            R = sorted(set(seeds[i]) | set(t))
            for a, b in itertools.combinations(R, 2): cnt[(a, b)] += 1
        return {p: n for p, n in cnt.items() if n >= 2 and p not in beside and p not in added}
    say(f"== S3 {c}: {len(cuts)} cut passages, {len(qs)} walks (dev+test), strength fixed from the drifted graph")
    def loop(rbase, label):
        added = []
        g = mk(rbase); allc = list(range(len(qs)))
        P, T = walks(g); C = cohs(T, allc); first = None; rounds = 0
        while True:
            t0 = time.time()
            cd = cands(T, set(added))
            holders = collections.defaultdict(list)
            for i, t in enumerate(T):
                for x in set(seeds[i]) | set(t): holders[x].append(i)
            gains = {}
            for p in cd:
                cols = sorted(set(holders[p[0]]) | set(holders[p[1]]))
                g2 = mk(rbase, added + [p]); _, T2 = walks(g2, cols)
                gains[p] = sum(cohs(T2, cols)) / len(qs) - sum(C[i] for i in cols) / len(qs)
            dt = time.time() - t0; rounds += 1
            if first is None: first = (dict(cd), dict(gains))
            best = max(gains.items(), key=lambda kv: (kv[1], -kv[0][0], -kv[0][1]), default=(None, 0))
            say(f"  [{label}] round {rounds}: {len(cd)} candidates scored in {dt:.0f}s; best gain {best[1]:+.5f}")
            if time_only or best[1] <= 0: break
            added.append(best[0]); g = mk(rbase, added); P, T = walks(g); C = cohs(T, allc)
        return added, first, g
    added, (cd1, gn1), gr = loop(rd, "drifted")
    if time_only: open(f"out/s3-{c}-time.txt", "w").write("\n".join(txt) + "\n"); return
    order = sorted(gn1, key=lambda p: -gn1[p])
    tq = [(i, q) for i, (q, _, _, sp_) in enumerate(qs) if sp_ == "test" and q in cutpairs]
    canon = lambda u, v: (min(u, v), max(u, v))
    say(f"  accepted {len(added)} links")
    cand_n = sum(canon(*cutpairs[q]) in cd1 for _, q in tq)
    rec_n = sum(canon(*cutpairs[q]) in set(added) for _, q in tq)
    trivial = sum(any(set(cutpairs[q]) <= set(seeds[i]) for i in range(len(qs))) for _, q in tq)
    say(f"  (a) cut pairs recovered: {rec_n}/{len(tq)}; candidates at all in round 1: {cand_n}/{len(tq)}; trivially co-read as seeds of one walk: {trivial}")
    ranks = [order.index(canon(*cutpairs[q])) + 1 for _, q in tq if canon(*cutpairs[q]) in gn1]
    say(f"  (b) rank among {len(order)} round-1 candidates by gain: {sorted(ranks)[:20]}{' …' if len(ranks) > 20 else ''}")
    rng = random.Random(0); pool = sorted(cd1)
    k = len(added)
    arms = {"built": mk(rows), "drifted": mk(rd), "repaired": gr,
            "random": mk(rd, rng.sample(pool, min(k, len(pool)))),
            "hub": mk(rd, sorted(pool, key=lambda p: (-(gd.nd[p[0]] * gd.nd[p[1]]), p))[:k]),
            "count": mk(rd, sorted(pool, key=lambda p: (-cd1[p], p))[:k])}
    cols = [i for i, _ in tq]
    res = {}
    for nm, g in arms.items():
        P, _ = walks(g, cols)
        rec = recall5(P, [(seeds[i], qs[i][2]) for i in cols])
        rk = []
        for j, (i, q) in enumerate(tq):
            p_ = P[:, j].copy(); p_[seeds[i]] = -1; rk.append(int((p_ > p_[cutpairs[q][1]]).sum()) + 1)
        Cg = costs(g, UNI); tc, mh = [], []
        for i, q in tq:
            tot, par = tree_edges(Cg, seeds[i], {x for x in qs[i][2] if x >= 0})
            tc.append(tot); mh.append(max((Cg[u, v] for v, u in par.items()), default=0) if par else float("inf"))
        rs = set(map(lambda p: canon(*p), added)) if nm == "repaired" else None
        res[nm] = dict(recall=rec, rank=rk, tcost=tc, maxhop=mh)
        say(f"  (c) {nm:9s} recall {mean_ok(rec):.3f}; median rank of v {int(np.median(rk))}; T* cost {np.mean(tc):.2f} nats, dearest hop {np.mean(mh):.2f}")
    for nm in ("repaired", "random", "hub", "count"):
        d, lo, hi = boot(res[nm]["recall"], res["drifted"]["recall"])
        dl = boot([np.log(x) for x in res["drifted"]["rank"]], [np.log(x) for x in res[nm]["rank"]])
        say(f"      {nm} − drifted: recall {d:+.3f} [{lo:+.3f}, {hi:+.3f}]; log-rank gain {dl[0]:+.3f} [{dl[1]:+.3f}, {dl[2]:+.3f}]")
    cost_cut = mean_ok(res["built"]["recall"]) - mean_ok(res["drifted"]["recall"])
    back = mean_ok(res["repaired"]["recall"]) - mean_ok(res["drifted"]["recall"])
    say(f"      the cut cost {cost_cut:+.3f} recall; repair won back {back:+.3f}")
    # (d) collateral on the graph as built
    addb, _, gb = loop(rows, "built")
    tc_ = [i for i, (_, _, _, sp_) in enumerate(qs) if sp_ == "test"]
    Pb, _ = walks(mk(rows), tc_); Pr, _ = walks(gb, tc_)
    rb = recall5(Pb, [(seeds[i], qs[i][2]) for i in tc_]); rr = recall5(Pr, [(seeds[i], qs[i][2]) for i in tc_])
    d, lo, hi = boot(rr, rb)
    say(f"  (d) collateral on the built graph: {len(addb)} links added; test recall repaired − built {d:+.3f} [{lo:+.3f}, {hi:+.3f}] over {sum(x is not None for x in rb)} questions")
    json.dump(dict(added=[[rows[a]["d"], rows[b]["d"]] for a, b in added], added_built=[[rows[a]["d"], rows[b]["d"]] for a, b in addb],
                   recovered=rec_n, candidates=cand_n, n=len(tq), trivial=trivial, ranks=ranks,
                   arms={k: {kk: (mean_ok(vv) if kk == "recall" else float(np.mean(vv))) for kk, vv in v.items()} for k, v in res.items()},
                   collateral=(d, lo, hi)), open(f"out/s3-{c}.json", "w"), indent=1)
    open(f"out/s3-{c}.txt", "w").write("\n".join(txt) + "\n")


if __name__ == "__main__":
    main()
