import json, sys
sys.path.insert(0, ".")
from score import paired, rec
qs = {q["qid"]: q for q in map(json.loads, open("dev/cards-dev.jsonl"))}
search = {json.loads(l)["qid"]: json.loads(l)["search"] for l in open("../../../leads/i-L0.jsonl")}
arms = {}
for name in ("L0", "L1k", "L1kS"):
    arms[name] = {r["qid"]: r for r in map(json.loads, open(f"leads/jev-{name}.jsonl"))}
ids = [q for q in qs if all(q in a for a in arms.values())]
r = {"search": [rec(search[q], qs[q]["gold"], 10) for q in ids]}
for n, a in arms.items():
    r[n] = [rec(a[q]["docs"], qs[q]["gold"], 10) for q in ids]
print(f"n={len(ids)}  " + "  ".join(f"{n} {sum(v)/len(v):.3f}" for n, v in r.items()))
for a, b in (("L0", "search"), ("L1k", "search"), ("L1kS", "search"), ("L1kS", "L0")):
    print(f"  {a} - {b}: %+.3f [%+.3f, %+.3f]" % paired(r[a], r[b]))
print("spend", {n: round(sum(x["cost_usd"] for x in a.values()), 3) for n, a in arms.items()})
