"""Where SR-K's lexical door misses (a pricing look, unregistered, on SR-KB's 300, seen). $0, no Jev.
For each question with gold hop 1 as read: is the hop-2 answer reachable by a door key at all (strength > 0)?
If it is and loses, what does the winning lure share with the read passage, and how rare is it?
    uv run --with sentence-transformers --with numpy python k_miss.py MUSIQUE_DEV GRAPH_MQ"""
import hashlib, json, re, sys, numpy as np
from collections import Counter
src, gpath = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
held = set(np.random.default_rng(20261121).permutation(np.arange(40, len(qs)))[:40].tolist())
pool = [i for i in np.random.default_rng(1341).permutation(np.arange(40, len(qs))) if i not in held][:300]
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
cat = Counter(); ex = []; qr_rank_nodoor = []; ans_in_text = Counter()
for qi in pool:
    r = qs[qi]; d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p for p in r["paragraphs"]}; T = {i: P[i]["title"] + ". " + P[i]["paragraph_text"] for i in P}
    opts = sorted(i for i in P if i != h1); qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    R = set(k for k in keys[hid(P[h1])] if 2 <= df[k] <= 100 and not set(k.split()) <= qt)
    sh = {i: keys[hid(P[i])] & R for i in opts}
    O = m.encode([T[i] for i in opts], normalize_embeddings=True); eqr = m.encode([QP + r["question"] + " " + T[h1]], normalize_embeddings=True)[0]
    ks = np.array([sum(1 / (df[k] - 1) for k in sh[i]) for i in opts]); sc = ks + 1e-6 * (O @ eqr)
    h = opts.index(h2); rank = int(1 + (sc > sc[h]).sum()); top = opts[int(sc.argmax())]
    a1 = d[0]["answer"].lower()  # hop-1 answer: the bridge entity
    bridge_in_h2 = a1 in T[h2].lower()
    if rank == 1: c = "hit"
    elif ks[h] == 0: c = "no door" + (" (bridge in text)" if bridge_in_h2 else " (bridge absent)")
    else: c = "door, lure stronger"
    cat[c] += 1
    if c == "no door (bridge in text)" or c == "no door (bridge absent)":
        qr_rank_nodoor.append(int(1 + ((O @ eqr) > (O @ eqr)[h]).sum()))
    if c == "door, lure stronger" and len(ex) < 12:
        ex.append((r["question"], d[0]["answer"], sorted(sh[h2], key=lambda k: df[k])[:4], round(ks[h], 3),
                   P[top]["title"], sorted(sh[top], key=lambda k: df[k])[:4], round(ks.max(), 3), a1 in T[top].lower()))
    # does the winning door key set contain the bridge?
    if c == "door, lure stronger": ans_in_text["lure names bridge" if a1 in T[top].lower() else "lure lacks bridge"] += 1
n = len(pool); print(f"n {n}")
for c, v in sorted(cat.items(), key=lambda x: -x[1]): print(f"  {c:28s} {v:4d}  {v/n:.3f}")
v = np.array(qr_rank_nodoor); print(f"no-door cases: qr top-1 {np.mean(v==1):.3f}, top-3 {np.mean(v<=3):.3f} (n {len(v)})")
print("door-lure cases:", dict(ans_in_text))
for e in ex: print("-", e)
