import json, random, statistics as st
def auc(pos, neg):
    if not pos or not neg: return float("nan")
    s = 0
    for p in pos:
        for q in neg: s += (p > q) + 0.5 * (p == q)
    return s / len(pos) / len(neg)
for c, g in [("cards","p8"),("prs","p8"),("mq","mq")]:
    F = json.load(open(f"keyfeat-{g}.json"))
    W = [w for w in map(json.loads, open(f"b-{c}.jsonl")) if any(d["gold"] for d in w["doors"])]
    pos, neg, jp, jn = [], [], [], []
    for w in W:
        for d in w["doors"]:
            if d["kind"] != "term": continue
            f = F[d["key"][5:]]["cohesion"]
            (pos if d["gold"] else neg).append(f)
    allc = sorted(pos + neg)
    def first(w, keep):
        ds = [d for d in w["doors"] if keep(d)]
        if not ds: return 0, False
        top = min(ds, key=lambda d: d["rank"])
        return int(top["gold"] > 0), any(d["gold"] for d in ds)
    base = st.mean(first(w, lambda d: True)[0] for w in W)
    line = [f"{c}: waves {len(W)} | term-door cohesion AUC gold vs not {auc(pos,neg):.2f} (gold {st.median(pos):.2f}, not {st.median(neg):.2f}) | gold first: none pruned {base:.2f}"]
    for q in (0.25, 0.5, 0.75):
        th = allc[int(q * len(allc))]
        keep = lambda d: d["kind"] != "term" or F[d["key"][5:]]["cohesion"] >= th
        r = [first(w, keep) for w in W]
        rnd = []
        for s in range(20):
            rng = random.Random(s); drop = {}
            def keepr(d):
                if d["kind"] != "term": return True
                return drop.setdefault(d["key"], rng.random() >= q)
            rnd.append(st.mean(first(w, keepr)[0] for w in W))
        line.append(f"prune {int(q*100)}%: {st.mean(x[0] for x in r):.2f} (gold door survives {st.mean(x[1] for x in r):.2f}; random {st.mean(rnd):.2f})")
    print(" | ".join(line))
