"""Key-level structure, question-free: for each term key in bill's dev rows, over the key's whole postings:
df, cohesion (share of posting pairs also linked by next/near or by another shared key)."""
import json, sys, itertools, collections
g = sys.argv[1]; sets = sys.argv[2:]
need = set()
for c in sets:
    for w in map(json.loads, open(f"b-{c}.jsonl")):
        for d in w["doors"]:
            if d["kind"] == "term": need.add(d["key"][5:])
keys, post, link = {}, collections.defaultdict(set), collections.defaultdict(set)
for r in map(json.loads, open(f"graph-{g}.jsonl")):
    keys[r["d"]] = set(r["keys"])
    for k in r["keys"]: post[k].add(r["d"])
    for x in r["next"] + r["near"]:
        link[r["d"]].add(x); link[x].add(r["d"])
out = {}
for k in need:
    P = sorted(post.get(k, ()))
    if len(P) < 2: continue
    pairs = list(itertools.combinations(P, 2))
    if len(pairs) > 3000:
        import random; random.seed(0); pairs = random.sample(pairs, 3000)
    co = sum(1 for a, b in pairs if b in link[a] or len(keys[a] & keys[b]) > 1)
    out[k] = {"df": len(P), "cohesion": co / len(pairs)}
json.dump(out, open(f"keyfeat-{g}.json", "w"))
print(g, len(need), "keys needed,", len(out), "found")
