"""evals/predict/REGISTERED.md: AUC of question-free wave properties for "Jev's first door holds gold".
    python3 s4.py ROWS_DIR   (V1's full rows v-{dev,test}-{cards,prs,mq}.jsonl[.gz])"""
import gzip, json, math, os, sys
from collections import defaultdict
from statistics import mean, pstdev

SETS = [("cards", "cards"), ("prs", "PR titles"), ("mq", "MuSiQue")]


def load(d, sp, k):
    p = f"{d}/v-{sp}-{k}.jsonl"
    f = open(p) if os.path.exists(p) else gzip.open(p + ".gz", "rt")
    rows = [json.loads(l) for l in f]
    u = [tuple(t) for t in rows[0]["thetas"]].index((-1.0, 0.0))
    B = defaultdict(list)
    for r in rows[1:]:
        B[(r["qid"], r["wave"])].append(r)
    return u, list(B.values())


def margin(ds, v):
    o = sorted(range(len(ds)), key=lambda i: -v[i]); rk = {i: r for r, i in enumerate(o)}
    G = [i for i in range(len(ds)) if ds[i]["gold"]]; N = [i for i in range(len(ds)) if not ds[i]["gold"]]
    if not N:
        return 1.0
    g = min(G, key=lambda i: rk[i]); w = ds[g]["width"]
    near = [i for i in N if max(w, ds[i]["width"]) <= 2 * min(w, ds[i]["width"])] or N
    return (min(rk[i] for i in near) - rk[g]) / len(ds)


def conc(v):
    t = sum(v)
    return sum(sorted(v, reverse=True)[:5]) / t if t > 0 else 0.0


def props(ds, u, arm="real"):
    v = [d[arm][u] for d in ds]
    w = [d["width"] for d in ds]
    return {"choice size (−log)": -math.log(len(ds)), "gold share": sum(1 for d in ds if d["gold"]) / len(ds),
            "vote margin": margin(ds, v), "vote concentration": conc(v),
            "width spread (−cv)": -(pstdev(w) / mean(w) if mean(w) else 0.0)}


def first_gold(ds):
    o = sorted(range(len(ds)), key=lambda i: (-(ds[i]["p"] if ds[i]["p"] is not None else -1), ds[i]["key"]))
    return 1 if ds[o[0]]["gold"] else 0


def auc(xs, ys):
    P = [x for x, y in zip(xs, ys) if y]; N = [x for x, y in zip(xs, ys) if not y]
    if not P or not N:
        return float("nan")
    return sum(1.0 if p > n else .5 if p == n else 0.0 for p in P for n in N) / (len(P) * len(N))


def main(d):
    names = list(props([{"real": [0], "width": 1, "gold": 1}], 0).keys())
    for sp in ("test", "dev"):
        print(f"\n== {sp}: AUC for 'Jev's first door holds gold' (directions fixed by the registration)")
        print(f"  {'property':<22}" + "".join(f"{n:>22}" for _, n in SETS) + f"{'pooled':>10}")
        pooled = defaultdict(list); py = []; R = {}; means = defaultdict(dict); fg = {}
        for k, n in SETS:
            u, B = load(d, sp, k)
            y = [first_gold(ds) for ds in B]; fg[k] = mean(y); py += y
            X = [props(ds, u) for ds in B]; Xs = [props(ds, u, "shuffled") for ds in B]
            for p in names:
                xs = [x[p] for x in X]; pooled[p] += xs; means[p][k] = mean(xs)
                R[(p, k)] = (auc(xs, y), auc([x[p] for x in Xs], y), len(B), sum(y))
        for p in names:
            cells = "".join(f"{R[(p, k)][0]:>10.3f} (sh {R[(p, k)][1]:.2f})" if p in ("vote margin", "vote concentration") else f"{R[(p, k)][0]:>22.3f}" for k, _ in SETS)
            print(f"  {p:<22}{cells}{auc(pooled[p], py):>10.3f}")
        print("  waves (first door gold): " + ", ".join(f"{n} {R[(names[0], k)][2]} ({R[(names[0], k)][3]})" for k, n in SETS))
        order = sorted(fg, key=lambda k: -fg[k])
        print(f"  graphs by Jev gold-first: {', '.join(f'{k} {fg[k]:.3f}' for k in order)}")
        for p in names:
            o = sorted(means[p], key=lambda k: -means[p][k])
            print(f"    graph means of {p:<22}: " + ", ".join(f"{k} {means[p][k]:.3f}" for k in o) + ("   (same order)" if o == order else ""))
        if sp == "test":
            ok = [p for p in names if p != "gold share" and sum(R[(p, k)][0] >= .65 for k, _ in SETS) >= 2
                  and all(R[(p, k)][0] > R[("gold share", k)][0] for k, _ in SETS)
                  and (p not in ("vote margin", "vote concentration") or all(R[(p, k)][1] < .65 for k, _ in SETS))]
            print(f"  PREDICTS (bar): {ok or 'none'}")


if __name__ == "__main__":
    main(sys.argv[1])
