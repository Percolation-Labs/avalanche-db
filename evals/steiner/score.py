"""evals/steiner/REGISTERED.md: (a) the Steiner cost and (b) the encoding gap, on the dev trace replays.
    python3 score.py NAME TRACES.jsonl STEINER.jsonl [ORACLE_CTL.jsonl] [NAME ...]"""
import json, random, sys
from statistics import mean


def gl(r):
    return list(r["gold"]) if isinstance(r["gold"], list) else list(r["gold"].keys())


def rec(d, g, k=10):
    return len(set(d[:k]) & set(g)) / len(g) if g else 0.0


def spearman(x, y):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
            for t in range(i, j + 1): r[o[t]] = (i + j) / 2
            i = j + 1
        return r
    a, b = rk(x), rk(y); ma, mb = mean(a), mean(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = (sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b)) ** .5
    return num / den if den else float("nan")


def share(c, B=5):
    v = c["arrival"]
    return sum(1 for x in v if x is not None and x <= B) / len(v) if v else 0.0


def one(name, tpath, spath, opath=None):
    T = {json.loads(l)["qid"]: json.loads(l) for l in open(tpath)}
    St = {json.loads(l)["qid"]: json.loads(l) for l in open(spath)}
    O = {}
    if opath:
        for l in open(opath):
            r = json.loads(l); O[r["qid"]] = r["walks"]["oracle"]
    ids = [q for q in T if q in St and St[q]["gold"]]
    print(f"\n== {name}: {len(ids)} questions with gold in the store")
    # (a)
    for arm in ("real", "random_seeds", "shuffled"):
        sh = [share(St[q][arm]) for q in ids]
        full = [St[q][arm]["all"] for q in ids]
        reach = [x for x in full if x is not None]
        med = sorted(reach)[len(reach) // 2] if reach else None
        print(f"  (a) {arm:<13} Steiner share@5 {mean(sh):.3f}   all gold covered within {60} reads {len(reach)}/{len(ids)}, median reads {med}")
    walk = {q: [d["id"] for d in T[q]["walk"]["documents"]] for q in ids}
    R = [rec(walk[q], St[q]["gold"]) for q in ids]
    Ss = [share(St[q]["real"]) for q in ids]
    srch = [rec([None] * 0 + [], St[q]["gold"]) for q in ids]  # placeholder, search below
    print(f"  (a) Spearman(Steiner share@5, walk recall@10) {spearman(Ss, R):+.3f}")
    srank = {q: St[q]["search_rank"] for q in ids}
    S10 = [sum(1 for x in srank[q] if x is not None and x <= 10) / len(srank[q]) for q in ids]
    print(f"  (a) Spearman(Steiner share@5, search recall@10) {spearman(Ss, S10):+.3f}")
    if O:
        Rc = [rec(O[q], St[q]["gold"]) for q in ids if q in O]
        print(f"  (a) Spearman(Steiner share@5, oracle recall@10) {spearman([s for s, q in zip(Ss, ids) if q in O], Rc):+.3f}")
    order = sorted(range(len(ids)), key=lambda i: Ss[i]); n = len(ids)
    for t, part in enumerate((order[: n // 3], order[n // 3: 2 * n // 3], order[2 * n // 3:])):
        print(f"      tercile {t+1}: share@5 {mean(Ss[i] for i in part):.2f}  walk {mean(R[i] for i in part):.3f}  search {mean(S10[i] for i in part):.3f}  walk-search {mean(R[i]-S10[i] for i in part):+.3f}")
    # (b)
    rnd = random.Random(1118)
    agg = {a: {"top1": [], "rr": [], "got": [], "best": []} for a in ("jev", "search-order", "width", "random")}
    hi_gap = []; all_gap = []
    for i, q in enumerate(ids):
        t = T[q]["walk"]["trace"]; g = set(St[q]["gold"])
        reads = t["reads"]
        for b in t["batches"]:
            before = {r["doc"] for r in reads if r["wave"] < b["wave"]}
            left = 10 - len(before)
            if left <= 0: continue
            doors = {d["key"]: [x for x in d["targets"] if x not in before] for d in b["doors"]}
            exp = {k: (len(set(v) & g) * min(len(v), left) / len(v) if v else 0.0) for k, v in doors.items()}
            gd = {k for k, v in doors.items() if set(v) & g}
            if not gd: continue
            so = St[q]["search_order"]
            ranks = {
                "jev": [x["key"] for x in b["ranking"] if x["key"] in doors],
                "search-order": sorted(doors, key=lambda k: (so.get(k) is None, so.get(k) or 0, k)),
                "width": sorted(doors, key=lambda k: (-len(doors[k]), k)),
                "random": rnd.sample(sorted(doors), len(doors)),
            }
            best = max(exp.values())
            for a, rk in ranks.items():
                pos = next((j for j, k in enumerate(rk) if k in gd), None)
                agg[a]["top1"].append(1.0 if pos == 0 else 0.0)
                agg[a]["rr"].append(1 / (pos + 1) if pos is not None else 0.0)
                agg[a]["got"].append(exp[rk[0]] if rk else 0.0); agg[a]["best"].append(best)
            if b is t["batches"][0]:
                gap = best - exp[ranks["jev"][0]]
                all_gap.append(gap)
                if Ss[i] >= .5: hi_gap.append(gap)
    for a, v in agg.items():
        print(f"  (b) {a:<13} waves with a gold door {len(v['top1'])}: gold door first {mean(v['top1']):.3f}  MRR {mean(v['rr']):.3f}  expected gold from the top door {sum(v['got'])/max(1e-9,sum(v['best'])):.3f} of the best")
    if all_gap:
        print(f"  (b) wave-1 gap (best gold door's expected gold − Jev's first door's): all {sum(all_gap):.1f} over {len(all_gap)} waves; on Steiner share@5 ≥ .5: {sum(hi_gap):.1f} ({sum(hi_gap)/max(1e-9,sum(all_gap)):.0%})")


if __name__ == "__main__":
    a = sys.argv[1:]
    i = 0
    while i < len(a):
        name, tp, sp = a[i:i + 3]; op = None; i += 3
        if i < len(a) and a[i].endswith(".jsonl") and not a[i].startswith("dev-"):
            op = a[i]; i += 1
        one(name, tp, sp, op)
