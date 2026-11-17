import json, sys
qs={q["qid"]:q for q in map(json.loads,open(sys.argv[1]))}
def rec(d,g,k=10): return len(set(d[:k])&set(g))/len(g)
for n in ("graph","postings","shown"):
    rows=[json.loads(l) for l in open(f"{sys.argv[2]}.{n}.jsonl")]
    o=sum(rec(r["walks"]["oracle"],r["gold"]) for r in rows)/len(rows)
    so=sum(rec(r["walks"]["search-order"],r["gold"]) for r in rows)/len(rows)
    s=sum(rec(r["search"],r["gold"]) for r in rows)/len(rows)
    print(f"{n:9s} n={len(rows)} search {s:.3f} oracle {o:.3f} search-order {so:.3f}")
