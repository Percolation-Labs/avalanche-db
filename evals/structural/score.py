"""evals/structural/REGISTERED.md: within-batch AUC of each structural property for gold doors, against Jev's P and
search order; the share of Jev's errors each orders correctly; shuffled-link control; per-question PPR.
    python3 score.py NAME FEATURES.jsonl TRACES.jsonl [NAME ...]"""
import json, sys
from collections import defaultdict
from statistics import mean

PROPS = {  # higher = more likely gold; directions fixed by the registration
    "jev P": lambda d, a: d["p"] if d["p"] is not None else -1,
    "search order": lambda d, a: -(d["search_rank"] or 10 ** 9),
    "narrow (−width)": lambda d, a: -d["width"],
    "cohesion": lambda d, a: d[a]["cohesion"] if d[a]["cohesion"] is not None else 0,
    "convergence": lambda d, a: d[a]["convergence"],
    "ppr (sum)": lambda d, a: d[a]["ppr"],
    "ppr (mean)": lambda d, a: d[a]["ppr_mean"],
}


def cmp(x, y):
    return 1.0 if x > y else .5 if x == y else 0.0


def one(name, fpath, tpath):
    B = defaultdict(list)
    for l in open(fpath):
        d = json.loads(l); B[(d["qid"], d["wave"])].append(d)
    res = {(p, a): [0.0, 0] for p in PROPS for a in ("real", "shuffled")}
    err = {(p, a): [0.0, 0] for p in PROPS for a in ("real", "shuffled")}
    wm = {(p, a): [0.0, 0] for p in PROPS for a in ("real", "shuffled")}  # not registered: width-matched pairs (within 2x)
    for ds in B.values():
        G = [d for d in ds if d["gold"]]; N = [d for d in ds if not d["gold"]]
        if not G or not N: continue
        for p, f in PROPS.items():
            for a in ("real", "shuffled"):
                s = 0.0
                for g in G:
                    fg = f(g, a)
                    for n in N:
                        c = cmp(fg, f(n, a)); s += c
                        if max(g["width"], n["width"]) <= 2 * min(g["width"], n["width"]):
                            wm[(p, a)][0] += c; wm[(p, a)][1] += 1
                        if (n["p"] or -1) > (g["p"] or -1):  # Jev ranks the gold-free door higher
                            err[(p, a)][0] += c; err[(p, a)][1] += 1
                res[(p, a)][0] += s / (len(G) * len(N)); res[(p, a)][1] += 1
    nb = res[("jev P", "real")][1]
    print(f"\n== {name}: {nb} batches with gold and gold-free doors")
    print(f"  {'property':<17} AUC real  shuffled   Jev's errors ordered right: real  shuffled   | width-matched pairs (not registered): real  shuffled")
    for p in PROPS:
        r, s = res[(p, "real")], res[(p, "shuffled")]; e, es = err[(p, "real")], err[(p, "shuffled")]
        same = p in ("jev P", "search order", "narrow (−width)")
        print(f"  {p:<17} {r[0]/r[1]:.3f}     {'  —  ' if same else f'{s[0]/s[1]:.3f}'}      {e[0]/max(1,e[1]):.3f} (n {e[1]})   {'  —' if same else f'{es[0]/max(1,es[1]):.3f}'}   | {wm[(p,'real')][0]/max(1,wm[(p,'real')][1]):.3f} (n {wm[(p,'real')][1]})  {'  —' if same else f"{wm[(p,'shuffled')][0]/max(1,wm[(p,'shuffled')][1]):.3f}"}")
    # per question: PPR from the seeds onto gold beyond the seeds
    Q = {json.loads(l)["qid"]: json.loads(l)["ppr"] for l in open(fpath + ".questions.jsonl")}
    T = {json.loads(l)["qid"]: json.loads(l) for l in open(tpath)}
    for arm in ("real", "random_seeds", "shuffled"):
        rk = [Q[q][arm]["best_gold_rank"] for q in Q if Q[q][arm]["best_gold_rank"] is not None or Q[q][arm]["gold_mass"] == 0]
        have = [x for x in rk if x is not None]
        n = sum(1 for q in Q if Q[q]["real"]["best_gold_rank"] is not None)
        top = lambda k: sum(1 for x in have if x <= k)
        print(f"  ppr from {arm:<13} best gold beyond the seeds: rank ≤10 {top(10)}, ≤100 {top(100)}, reached {len(have)} (of {n} questions with gold beyond the seeds by real PPR)")


if __name__ == "__main__":
    a = sys.argv[1:]
    for i in range(0, len(a), 3):
        one(*a[i:i + 3])
