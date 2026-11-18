"""evals/structure/REGISTERED.md's measures from out/*.jsonl. $0."""
import collections, json, statistics as S, sys
GAIN = {"cards": "+.186 (I1+L1kS)", "prs": "-.042 (as merged)", "prs-m": "-.011 (M+H1)", "musique": "+.134"}
def band(r): return "top 10" if r and r <= 10 else ("11-100" if r and r <= 100 else ">100")
for name in ("cards", "prs", "prs-m", "musique"):
    rows = [json.loads(l) for l in open(f"out/{name}.jsonl")]
    gs = [g for r in rows for g in r["gold"]]
    n = len(gs)
    print(f"\n== {name}: {len(rows)} questions, {n} gold; walk - search at k=10 {GAIN[name]}")
    b = collections.Counter(band(g["rank"]) for g in gs)
    print("  search rank: " + ", ".join(f"{k} {b[k]/n:.2f}" for k in ("top 10", "11-100", ">100")))
    for lab, key in (("seeds", lambda g: g["link"]["d"]), ("random seeds", lambda g: g["random_seeds"])):
        d = collections.Counter(min(key(g), 3) for g in gs)
        print(f"  distance from {lab}: " + ", ".join(f"{k if k < 3 else '>2'}: {d[k]/n:.2f}" for k in range(4)))
    orth = [g for g in gs if band(g["rank"]) == ">100"]
    ol = [g for g in orth if g["link"]["d"] <= 2]
    ol1 = [g for g in orth if g["link"]["d"] == 1]
    print(f"  orthogonal (beyond search's top 100) {len(orth)/n:.2f}; orthogonal and at distance <=2: {len(ol)/n:.2f}; at distance 1: {len(ol1)/n:.2f}")
    k1 = collections.Counter((g["link"]["kind"]) for g in ol1)
    w1 = [g["link"]["width"] for g in ol1]
    if w1: print(f"  orthogonal at distance 1, by door kind: {dict(k1)}; door width median {S.median(w1)}")
    print(f"  frontier (docs within 1 of seeds) median {S.median(r['frontier'] for r in rows)} of {rows[0]['docs']}; random seeds {S.median(r['random_frontier'] for r in rows)}; shuffled links {S.median(r['shuffled_frontier'] for r in rows)}")
    d1 = sum(g['link']['d'] == 1 for g in gs) / n
    sd1 = sum(r['shuffled_d1'] for r in rows) / n
    print(f"  gold at distance 1: real links {d1:.2f}, shuffled links {sd1:.2f}")
    pr = [p for r in rows for p in r["pairs"]]
    if pr:
        lk = [p for p in pr if p["linked"]]
        kinds = collections.Counter(p["linked"]["kind"] for p in lk)
        ws = [p["linked"]["width"] for p in lk]
        print(f"  gold pairs directly linked {len(lk)}/{len(pr)} = {len(lk)/len(pr):.2f}; by kind {dict(kinds)}; width median {S.median(ws) if ws else '-'}")
        comp = []
        for r in rows:
            docs = [g["doc"] for g in r["gold"]]
            if len(docs) < 2: continue
            par = {d: d for d in docs}
            def f(x):
                while par[x] != x: x = par[x]
                return x
            for p in r["pairs"]:
                if p["linked"]: par[f(p["a"])] = f(p["b"])
            comp.append(len({f(d) for d in docs}) / len(docs))
        print(f"  components per gold doc (1/n = all joined, 1 = none): median {S.median(comp):.2f}")
