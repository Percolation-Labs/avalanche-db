"""$0 follow-up to SR-BN (bill's review): when Jev names a wrong key, is it one no option shares (so the step falls
through to k's tie-break)? Reads out/srbn-names-fresh.json and out/srbn-name-fresh.json; no models, no Jev.
    python3 srbn_wrong.py MUSIQUE_DEV GRAPH_MQ"""
import hashlib, json, re, sys
from collections import Counter
src, gpath = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
N = json.load(open("out/srbn-names-fresh.json")); rk = json.load(open("out/srbn-name-fresh.json"))["ranks"]
wd = lambda s: set(re.findall(r"[a-z0-9]+", s.lower())); c = Counter()
for j, (qi, v) in enumerate(N.items()):   # same order as the scored cases
    r = qs[int(qi)]; d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    K = v["jev"]
    if K is None: c["no keys"] += 1; continue
    if set(K.split()) <= wd(d[0]["answer"]): c["right", rk["jev"][j] == 1] += 1; continue
    P = {p["idx"]: p for p in r["paragraphs"]}; opts = [i for i in P if i != h1]
    sharers = [i for i in opts if K in keys[hid(P[i])]]
    kind = "wrong, shared by none" if not sharers else ("wrong, shared incl. hop 2" if h2 in sharers else "wrong, shared by lures only")
    c[kind, rk["jev"][j] == 1] += 1
for kind in ("right", "wrong, shared by none", "wrong, shared incl. hop 2", "wrong, shared by lures only"):
    n = c[kind, True] + c[kind, False]; print(f"{kind:30s} n {n:3d}  hop-2 top-1 {c[kind, True] / max(n, 1):.3f}")
print("no keys", c["no keys"])
