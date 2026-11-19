"""evals/walkvote/REGISTERED.md stage 0: first door of each recorded test wave under P fused with X by reciprocal rank.
    python3 w2.py ROWS_DIR THETA.json   (ROWS_DIR holds V1's full rows v-test-{cards,prs,mq}.jsonl[.gz])"""
import gzip, json, os, sys
from collections import defaultdict
from statistics import mean

SETS = [("cards", "cards"), ("prs", "PR titles"), ("mq", "MuSiQue")]


def load(d, k):
    p = f"{d}/v-test-{k}.jsonl"
    f = open(p) if os.path.exists(p) else gzip.open(p + ".gz", "rt")
    rows = [json.loads(l) for l in f]
    th = [tuple(t) for t in rows[0]["thetas"]]
    B = defaultdict(list)
    for r in rows[1:]:
        B[(r["qid"], r["wave"])].append(r)
    return th, list(B.values())


def p_order(ds):  # Jev's order: P desc, ties by key (unscored last)
    return sorted(range(len(ds)), key=lambda i: (-(ds[i]["p"] if ds[i]["p"] is not None else -1), ds[i]["key"]))


def fused(ds, x):
    po = p_order(ds)
    rp = {i: r for r, i in enumerate(po)}
    xo = sorted(range(len(ds)), key=lambda i: (-x[i], rp[i]))
    rx = {i: r for r, i in enumerate(xo)}
    return sorted(range(len(ds)), key=lambda i: (-(1 / (61 + rp[i]) + 1 / (61 + rx[i])), rp[i]))


def readout(B, order_of):
    first, mrr, rw = [], [], []
    for ds in B:
        o = order_of(ds)
        dens = [d["gold"] / d["width"] for d in ds]
        first.append(1.0 if ds[o[0]]["gold"] else 0.0)
        mrr.append(next(1 / (r + 1) for r, i in enumerate(o) if ds[i]["gold"]))
        rw.append(dens[o[0]] / max(dens))
    return mean(first), mean(mrr), mean(rw)


def main(d, tpath):
    T = json.load(open(tpath))
    res = {}
    print(f"{'test':<10} {'arm':<20} {'gold first':>10} {'MRR':>7} {'read-weighted (b)':>18}   waves")
    for k, n in SETS:
        th, B = load(d, k)
        u, l = th.index((-1.0, 0.0)), th.index(tuple(T[k]))
        arms = {
            "P": p_order,
            "P ⊕ vote": lambda ds: fused(ds, [x["real"][u] / x["width"] for x in ds]),
            "P ⊕ learned vote": lambda ds: fused(ds, [x["real"][l] / x["width"] for x in ds]),
            "P ⊕ shuffled vote": lambda ds: fused(ds, [x["shuffled"][u] / x["width"] for x in ds]),
            "P ⊕ narrow": lambda ds: fused(ds, [-x["width"] for x in ds]),
            "vote alone": lambda ds: sorted(range(len(ds)), key=lambda i: -ds[i]["real"][u] / ds[i]["width"]),
        }
        res[k] = {a: readout(B, f) for a, f in arms.items()}
        for a, (g, m, r) in res[k].items():
            print(f"{n:<10} {a:<20} {g:>10.3f} {m:>7.3f} {r:>18.3f}   {len(B)}")
        print()
    gain = {k: res[k]["P ⊕ vote"][0] - res[k]["P"][0] for k, _ in SETS}
    drop_b = {k: res[k]["P ⊕ vote"][2] - res[k]["P"][2] for k, _ in SETS}
    up = [k for k in gain if gain[k] >= .03]
    ctrl = all(res[k]["P ⊕ vote"][0] - res[k][c][0] >= .02 for k in up for c in ("P ⊕ shuffled vote", "P ⊕ narrow"))
    ok = len(up) >= 2 and min(gain.values()) >= -.02 and min(drop_b.values()) >= -.02 and ctrl
    print("P ⊕ vote − P, gold first: " + ", ".join(f"{n} {gain[k]:+.3f}" for k, n in SETS))
    print("P ⊕ vote − P, read-weighted (b): " + ", ".join(f"{n} {drop_b[k]:+.3f}" for k, n in SETS))
    print(f"beats both controls by .02 where it gains: {ctrl}")
    print(f"STAGE 0: {'pass' if ok else 'fail'}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
