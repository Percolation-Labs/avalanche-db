"""Score REGISTERED-P2.md from out/p2-*.jsonl.    python3 p2score.py DIR"""
import json, sys
from statistics import mean, median
import numpy as np

SETS = [("cards", "cards"), ("prs", "PR titles"), ("mq", "MuSiQue")]
KS = ("1", "3", "5", "10", "20")


def boot(a, b=None, n=2000, seed=0):
    r = np.random.default_rng(seed); a = np.array(a, float)
    if b is None:
        bs = [a[r.integers(0, len(a), len(a))].mean() for _ in range(n)]; return a.mean(), *np.percentile(bs, [2.5, 97.5])
    b = np.array(b, float)
    bs = [a[r.integers(0, len(a), len(a))].mean() - b[r.integers(0, len(b), len(b))].mean() for _ in range(n)]
    return a.mean() - b.mean(), *np.percentile(bs, [2.5, 97.5])


def m(v):
    v = [x for x in v if x is not None]; return mean(v) if v else float("nan")


def main(d):
    passed = 0
    for k, name in SETS:
        R = [json.loads(l) for l in open(f"{d}/p2-{k}.jsonl")]
        B = [r for r in R if r["recall_beyond_U"]["5"] is not None]
        L = [r["likeness"] for r in R]; C = [r["connection"] for r in R]
        print(f"== {name}: {len(R)} questions, {len(B)} with gold beyond the seeds")
        print(f"  likeness: entry points (seeds in S) mean {m([x['entry'] for x in L]):.2f}, ≥1 on {sum(x['entry'] >= 1 for x in L)}/{len(R)};"
              f" near seeds mean {m([x['near'] for x in L]):.2f}, ≥1 on {sum(x['near'] >= 1 for x in L)}/{len(R)};"
              f" coverage {m([x['coverage'] for x in L]):.3f}; seed→gold distance, median of medians {median([x['seed_dist_median'] for x in L if x['seed_dist_median'] is not None])}")
        gr = [v for x in L for v in x["gold_search_rank"].values()]
        print(f"  question→gold: gold in search's hits {sum(v is not None for v in gr)}/{len(gr)}, median rank {median([v for v in gr if v is not None]) if any(gr) else None},"
              f" in top 5 {sum(v is not None and v <= 5 for v in gr)}, top 50 {sum(v is not None and v <= 50 for v in gr)}")
        print(f"  connection (|S|≥2): mean pair distance {m([x['mean_pair_dist'] for x in C]):.2f} (shuffled {m([x['mean_pair_dist_shuffled'] for x in C]):.2f});"
              f" directly linked {m([x['direct_share'] for x in C]):.3f} (shuffled {m([x['direct_share_shuffled'] for x in C]):.3f});"
              f" in-S step {m([x['instep'] for x in C]):.4f} (shuffled {m([x.get('instep_shuffled') for x in C]):.4f})")
        print("  recall beyond the seeds, U's top k: " + ", ".join(f"k={kk} {m([r['recall_beyond_U'][kk] for r in B]):.3f}" for kk in KS)
              + f"; walk (5 reads) {m([r['recall_beyond_walk'] for r in B]):.3f}")
        # bar 2: by near seeds
        for lab, f in (("0", lambda n: n == 0), ("1–2", lambda n: 1 <= n <= 2), ("≥3", lambda n: n >= 3)):
            g = [r for r in B if f(r["likeness"]["near"])]
            print(f"    near seeds {lab:<3}: n {len(g):>3}, U recall@5 {m([r['recall_beyond_U']['5'] for r in g]):.3f}, walk {m([r['recall_beyond_walk'] for r in g]):.3f}")
        # bar 1: compactness thirds
        E = [r for r in B if r["n_gold_in_graph"] >= 2 and r["likeness"]["near"] >= 1 and r["connection"]["mean_pair_dist"] is not None]
        E.sort(key=lambda r: r["connection"]["mean_pair_dist"])
        t = len(E) // 3
        if t >= 3:
            lo, hi = E[:t], E[-t:]
            dd, a, b = boot([r["recall_beyond_U"]["5"] for r in lo], [r["recall_beyond_U"]["5"] for r in hi])
            ok = dd >= .10 and a > 0; passed += ok
            print(f"  bar 1, compactness: n {len(E)}; most compact third (pair dist ≤ {lo[-1]['connection']['mean_pair_dist']:.2f}) U@5 {m([r['recall_beyond_U']['5'] for r in lo]):.3f},"
                  f" least (≥ {hi[0]['connection']['mean_pair_dist']:.2f}) {m([r['recall_beyond_U']['5'] for r in hi]):.3f}: {dd:+.3f} [{a:+.3f}, {b:+.3f}] {'pass' if ok else 'fail'}")
            for kk in KS:
                print(f"     k={kk:>2}: compact {m([r['recall_beyond_U'][kk] for r in lo]):.3f}, middle {m([r['recall_beyond_U'][kk] for r in E[t:-t]]):.3f}, spread {m([r['recall_beyond_U'][kk] for r in hi]):.3f}")
        else:
            print(f"  bar 1, compactness: too few questions ({len(E)})")
        # bar 3: likeness against connection
        ent = [r for r in B if r["likeness"]["near"] >= 1]
        cur = m([r["recall_beyond_U"]["5"] for r in B])
        pl = m([r["recall_beyond_U"]["5"] for r in ent]); pc = len(ent) / len(B)
        lab = {"likeness-limited": 0, "connection-limited": 0, "reached": 0}
        for r in B:
            if r["likeness"]["near"] == 0: lab["likeness-limited"] += 1
            elif r["recall_beyond_U"]["5"] < .5: lab["connection-limited"] += 1
            else: lab["reached"] += 1
        print(f"  bar 3: U recall@5 now {cur:.3f}; perfect likeness (questions with a near seed) {pl:.3f}; perfect connection (share with a near seed) {pc:.3f}; labels {lab}")
        lab2 = {"likeness-limited": 0, "connection-limited": 0, "reached": 0}
        for r in B:
            if r["likeness"]["near"] == 0: lab2["likeness-limited"] += 1
            elif r["recall_beyond_walk"] < .5: lab2["connection-limited"] += 1
            else: lab2["reached"] += 1
        print(f"         same labels under the recorded walk: {lab2}")
        if k == "mq":
            print("  bar 4, seed sets (total recall at 10 reads = 5 seeds + U's top 5; entry points):")
            base = [r["seed_sets"]["single"]["total10"] for r in R]
            for v in ("single", "blind", "filled", "oracle"):
                x = [r["seed_sets"][v]["total10"] for r in R]
                dif = np.array(x) - np.array(base)
                rng = np.random.default_rng(0); bs = [dif[rng.integers(0, len(dif), len(dif))].mean() for _ in range(2000)]
                a, b = np.percentile(bs, [2.5, 97.5])
                extra = f"  vs single {dif.mean():+.3f} [{a:+.3f}, {b:+.3f}]" if v != "single" else ""
                print(f"     {v:<7} total@10 {mean(x):.3f}, entry {mean(r['seed_sets'][v]['entry'] for r in R):.2f}{extra}"
                      + ((" pass" if dif.mean() >= .03 and a > 0 else " fail") if v == "blind" else ""))
        print()
    print(f"bar 1 passes on {passed} set(s): {'pass' if passed >= 2 else 'fail'}")


if __name__ == "__main__":
    main(*sys.argv[1:])
