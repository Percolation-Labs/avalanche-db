"""evals/votes/REGISTERED.md: choose θ per graph on dev (width-matched AUC of the door vote), score the arms on test.
    python3 score.py OUT_DIR   (reads v-{dev,test}-{cards,prs,mq}.jsonl[.questions.jsonl], writes theta.json)"""
import json, sys
from collections import defaultdict
from statistics import mean

SETS = [("cards", "cards"), ("prs", "PR titles"), ("mq", "MuSiQue")]
UNIFORM = (-1.0, 0.0)


def load(path):
    rows = [json.loads(l) for l in open(path)]
    th = [tuple(t) for t in rows[0]["thetas"]]
    B = defaultdict(list)
    for d in rows[1:]:
        B[(d["qid"], d["wave"])].append(d)
    Q = [json.loads(l) for l in open(path + ".questions.jsonl")]
    return th, list(B.values()), Q


def cmp(x, y):
    return 1.0 if x > y else .5 if x == y else 0.0


def measures(batches, arm, i):
    """(width-matched AUC, AUC of the per-target vote) for grid point i on arm 'real' or 'shuffled'."""
    wm = [0.0, 0]; au = []
    for ds in batches:
        G = [d for d in ds if d["gold"]]; N = [d for d in ds if not d["gold"]]
        if not G or not N:
            continue
        s = 0.0
        for g in G:
            for n in N:
                s += cmp(g[arm][i] / g["width"], n[arm][i] / n["width"])
                if max(g["width"], n["width"]) <= 2 * min(g["width"], n["width"]):
                    wm[0] += cmp(g[arm][i], n[arm][i]); wm[1] += 1
        au.append(s / (len(G) * len(N)))
    return wm[0] / max(1, wm[1]), mean(au)


def top10(Q, i):
    return sum(1 for q in Q if q["gold_beyond_seeds"] and q["best_gold_rank"][i] is not None and q["best_gold_rank"][i] <= 10)


def main(d):
    data = {k: {sp: load(f"{d}/v-{sp}-{k}.jsonl") for sp in ("dev", "test")} for k, _ in SETS}
    th = data["cards"]["dev"][0]
    assert all(data[k][sp][0] == th for k in data for sp in data[k])
    u = th.index(UNIFORM)
    dev = {k: [measures(data[k]["dev"][1], "real", i)[0] for i in range(len(th))] for k in data}
    learned = {k: max(range(len(th)), key=lambda i: (dev[k][i], -abs(i - u))) for k in data}
    pooled = max(range(len(th)), key=lambda i: (mean(dev[k][i] for k in data), -abs(i - u)))
    json.dump({k: list(th[learned[k]]) for k in data} | {"pooled": list(th[pooled])}, open(f"{d}/theta.json", "w"))
    print(f"grid {len(th)} points; uniform θ = {UNIFORM}")
    print(f"learned θ (dev): " + ", ".join(f"{n} {th[learned[k]]} (dev {dev[k][learned[k]]:.3f} vs uniform {dev[k][u]:.3f})" for k, n in SETS)
          + f"; pooled {th[pooled]}")
    print(f"\n{'test':<10} {'arm':<24} {'width-matched AUC':>18} {'AUC per target':>15} {'gold top-10 / of':>17}")
    verdict = []
    for k, n in SETS:
        _, bt, Q = data[k]["test"]
        nq = sum(1 for q in Q if q["gold_beyond_seeds"])
        R = {i: measures(bt, "real", i) for i in range(len(th))}
        rnd = (mean(R[i][0] for i in R), mean(R[i][1] for i in R), mean(top10(Q, i) for i in R))
        sh = measures(bt, "shuffled", learned[k])
        rows = [("uniform " + str(th[u]), R[u] + (top10(Q, u),)), (f"learned {th[learned[k]]}", R[learned[k]] + (top10(Q, learned[k]),)),
                (f"pooled {th[pooled]}", R[pooled] + (top10(Q, pooled),)), ("random θ (grid mean)", rnd),
                ("learned, shuffled links", sh + (None,))]
        for name, (a, b, c) in rows:
            print(f"{n:<10} {name:<24} {a:>18.3f} {b:>15.3f} {('—' if c is None else f'{c:.1f}' if isinstance(c, float) else str(c)) + f' / {nq}':>17}")
        verdict.append((R[learned[k]][0] - R[u][0], R[learned[k]][0] > rnd[0], sh[0] < .56))
        print()
    gains = [v[0] for v in verdict]
    ok = sum(g >= .02 for g in gains) >= 2 and min(gains) >= -.01 and all(v[1] for v in verdict) and all(v[2] for v in verdict)
    print("learned − uniform (width-matched, test): " + ", ".join(f"{n} {g:+.3f}" for (k, n), g in zip(SETS, gains)))
    print("beats random θ: " + ", ".join(str(v[1]) for v in verdict) + "; shuffled < .56: " + ", ".join(str(v[2]) for v in verdict))
    print(f"VERDICT: {'pass' if ok else 'fail'}")


if __name__ == "__main__":
    main(sys.argv[1])
