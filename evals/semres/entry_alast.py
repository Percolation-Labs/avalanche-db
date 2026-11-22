"""Entry look on A-last ($0, post hoc, SR-BE's cached entry requests), bill. Sirsh 17:07Z: the target is the answer
passage in the returned set (A-last). SR-AC: a reader needs only that passage. So how good is Jev's 20-passage entry
request at finding the answer passage itself, and does returning its top k beat walking?
Rebuilds SR-BE's fresh draw (seed 1341, positions 304-603 of the 2-hop answerable permutation) and reads the cached
ENTRY_TASK requests; no Jev call is made (a cache miss exits).
    python3 entry_alast.py TRAIN_CORPUS"""
import hashlib, json, sys
from pathlib import Path
ENTRY_TASK = "Each option is a passage. Which passage should be read first to answer `question`?"
cache = {}
for l in open(Path.home() / ".cache" / "walklab" / "srbe-jev-cache.jsonl"):
    y = json.loads(l); cache[y["k"]] = y["p"]
ck = lambda c, o: hashlib.sha256(json.dumps([c, o]).encode()).hexdigest()
qs = [r for r in map(json.loads, open(sys.argv[1])) if r["id"].startswith("2hop") and r["answerable"]]
import random
# numpy-free permutation identical to np.random.default_rng(1341).permutation would need numpy; use it
import numpy as np
pool = np.random.default_rng(1341).permutation(len(qs))[304:604].tolist()
be = json.load(open("out/srbe-fresh.json"))
rows = []
for qi in pool:
    r = qs[qi]; P = sorted(r["paragraphs"], key=lambda p: p["idx"]); T = [p["title"] + ". " + p["paragraph_text"] for p in P]
    k = ck({"question": r["question"], "task": ENTRY_TASK}, T)
    if k not in cache: sys.exit(f"cache miss {r['id']}")
    p = np.array(cache[k]); order = list(np.argsort(-p, kind="stable"))
    ix = {q["idx"]: j for j, q in enumerate(P)}; d = r["question_decomposition"]
    h1, h2 = ix[d[0]["paragraph_support_idx"]], ix[d[1]["paragraph_support_idx"]]
    rows.append(dict(r1=order.index(h1) + 1, r2=order.index(h2) + 1, top=order, h1=h1, h2=h2))
n = len(rows)
print(f"{n} questions (SR-BE fresh). Entry request ranks: answer passage (hop 2) median {np.median([x['r2'] for x in rows]):.0f}, hop 1 median {np.median([x['r1'] for x in rows]):.0f}")
print(f"entry argmax is the answer passage {np.mean([x['r2'] == 1 for x in rows]):.3f}; hop 1 {np.mean([x['r1'] == 1 for x in rows]):.3f}")
for k in (1, 2, 3):
    print(f"return the entry request's top {k}: A-last {np.mean([x['r2'] <= k for x in rows]):.3f}  both hops {np.mean([x['r1'] <= k and x['r2'] <= k for x in rows]):.3f}")
# second entry: when the argmax misses both hops, is the runner-up on a hop? (a walk from a hop reaches the answer
# passage almost always on 2-hop, so a hop entry is the proxy for A-last)
hit = lambda x, j: x["top"][j] in (x["h1"], x["h2"])
miss = [x for x in rows if not hit(x, 0)]
print(f"entry argmax off both hops: {len(miss)} of {n}; runner-up on a hop in {sum(hit(x, 1) for x in miss)}, "
      f"third in {sum(hit(x, 2) for x in miss)} of those")
print(f"upper bound, two entries each walked one step (4 passages): entry on a hop {np.mean([hit(x, 0) or hit(x, 1) for x in rows]):.3f} vs one entry {np.mean([hit(x, 0) for x in rows]):.3f}")
