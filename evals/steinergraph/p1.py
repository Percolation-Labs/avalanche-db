"""evals/steinergraph/REGISTERED-P1.md: recall of gold beyond the seeds under S, U, Q and Q on shuffled links; the walk as
reference; the avalanche by step.    python3 p1.py DIR [split]   (g-{split}-{cards,prs,mq}.jsonl; split default test)"""
import json, sys
from statistics import mean, median

SETS = [("cards", "cards"), ("prs", "PR titles"), ("mq", "MuSiQue")]
ARMS = ["S", "U", "Q", "Q_shuffled"]


def main(d, sp="test"):
    res = {}
    print(f"== {sp}: recall of gold beyond the seeds (questions with gold beyond the seeds)")
    print(f"  {'set':<10} {'arm':<12} {'recall@5':>9} {'recall@20':>10} {'best gold rank, median':>23}   (Jev walk, 5 reads: recall)")
    for k, n in SETS:
        R = [json.loads(l) for l in open(f"{d}/g-{sp}-{k}.jsonl")]
        R = [r for r in R if r["gold_beyond"] > 0]
        walk = mean(r["walk_at5"] / r["gold_beyond"] for r in R)
        res[k] = {}
        for a in ARMS:
            r5 = mean(r[a]["at5"] / r["gold_beyond"] for r in R)
            r20 = mean(r[a]["at20"] / r["gold_beyond"] for r in R)
            best = median(r[a]["best"] if r[a]["best"] is not None else 10 ** 6 for r in R)
            res[k][a] = r5
            print(f"  {n:<10} {a:<12} {r5:>9.3f} {r20:>10.3f} {best:>23}   " + (f"({walk:.3f}, n {len(R)})" if a == "S" else ""))
        for a in ("U", "Q"):
            st = [[r["avalanche"][a][i] for r in R] for i in range(3)]
            print(f"  {'':<10} avalanche {a}: " + "; ".join(
                f"step {i + 1}: gold mass {mean(x['gold_mass'] for x in s):.4f}, best gold in top 10 {sum(1 for x in s if x['best'] is not None and x['best'] <= 10)}/{len(R)}"
                for i, s in enumerate(st)))
        print()
    if sp == "test":
        g = {k: res[k]["Q"] - res[k]["S"] for k, _ in SETS}
        up = [k for k in g if g[k] >= .03]
        ok = len(up) >= 2 and all(res[k]["Q"] > res[k]["U"] and res[k]["Q"] > res[k]["Q_shuffled"] for k in up)
        print("Q − S, recall@5: " + ", ".join(f"{n} {g[k]:+.3f}" for k, n in SETS))
        print(f"P1: {'pass' if ok else 'fail'}")


if __name__ == "__main__":
    main(*sys.argv[1:])
