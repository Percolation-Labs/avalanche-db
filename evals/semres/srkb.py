"""SR-KB (REGISTERED-SRKB.md), REM-1341, $0: a key-bundle probe for the next hop. Given the gold hop 1 as read (as in
SR-K), rank the 19 other passages of the pool for hop 2. The key bundle is the read passage's door keys (2 <= df <= 100)
not contained in the question, each embedded as its own phrase with bge-small; weights are vecops.idf over the 21,100-
passage graph. Probes use james's vecops (combine = Average PRF, rocchio = query + feedback at equal weight).
Arms (each: argmax over options of cos(probe, option); `k` is SR-K's lexical decider):
  q        the question                         qr      the question + read passage, as one text (SR-K's baseline)
  k        SR-K: argmax Σ 1/(df-1) over shared new keys, ties by qr
  kb       combine(key vectors, idf)            rq      rocchio(q, key vectors, idf)
  rq_out   pivot_out(rq, centre(pool))          drift control: remove the pool's mean direction
Draw: seeded permutation of answerable 2-hop questions 41-1252, excluding SR-J-R's 40 (james's warp test set).
    uv run --with sentence-transformers --with numpy python srkb.py MUSIQUE_DEV GRAPH_MQ N [--score]"""
import hashlib, json, re, sys
from collections import Counter
import numpy as np
import vecops as vo
src, gpath, N = sys.argv[1], sys.argv[2], int(sys.argv[3]); SCORE = "--score" in sys.argv
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}; NG = len(rows)
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
held = set(np.random.default_rng(20261121).permutation(np.arange(40, len(qs)))[:40].tolist())
pool = [i for i in np.random.default_rng(1341).permutation(np.arange(40, len(qs))) if i not in held][:N]
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
ARMS = ("q", "qr", "k", "kb", "rq", "rq_out"); out = []; nokeys = 0
for n_, qi in enumerate(pool):
    r = qs[qi]; d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p for p in r["paragraphs"]}; T = {i: P[i]["title"] + ". " + P[i]["paragraph_text"] for i in P}
    opts = sorted(i for i in P if i != h1); qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    R = sorted(k for k in keys[hid(P[h1])] if 2 <= df[k] <= 100 and not set(k.split()) <= qt)
    E = m.encode([QP + r["question"], QP + r["question"] + " " + T[h1]] + [T[i] for i in opts] + [T[h1]], normalize_embeddings=True)
    eq, eqr, O, er = E[0], E[1], E[2:-1], E[-1]
    ks = np.array([sum(1 / (df[k] - 1) for k in keys[hid(P[i])] & set(R)) for i in opts])
    sc = dict(q=O @ eq, qr=O @ eqr, k=ks + 1e-6 * (O @ eqr))
    if R:
        K = m.encode(R, normalize_embeddings=True); w = vo.idf([df[k] for k in R], NG)
        kb = vo.combine(K, w); rq = vo.rocchio(eq, K, w); cen = vo.centre(np.vstack([O, er[None]]))
        sc.update(kb=O @ kb, rq=O @ rq, rq_out=O @ vo.pivot_out(rq, cen))
    else:
        nokeys += 1; sc.update(kb=sc["q"], rq=sc["q"], rq_out=sc["q"])   # no bundle: fall back to the question
    if n_ == 0:
        print(f"-- {r['question']}\n   read: {P[h1]['title']}; bundle: {R[:8]}")
        for a in ("qr", "kb", "rq"): print(f"   {a:3s} top 3: {[P[opts[j]]['title'] for j in np.argsort(-sc[a])[:3]]}")
    rec = dict(qi=int(qi), nkeys=len(R))
    if SCORE:
        h = opts.index(h2)
        for a in ARMS: rec[a] = int(1 + (sc[a] > sc[a][h]).sum())
    out.append(rec)
print(f"\n{len(out)} questions; empty bundle (fallback to q) {nokeys}; bundle size median {int(np.median([o['nkeys'] for o in out]))}")
if SCORE:
    rng = np.random.default_rng(0); nq = len(out)
    for a in ARMS: print(f"{a:7s} top-1 {np.mean([o[a] == 1 for o in out]):.3f}  top-3 {np.mean([o[a] <= 3 for o in out]):.3f}  MRR {np.mean([1 / o[a] for o in out]):.3f}")
    for a, b in (("rq", "qr"), ("kb", "qr"), ("rq", "k"), ("rq_out", "rq")):
        dd = np.array([(o[a] == 1) - (o[b] == 1) for o in out], float); bt = [dd[rng.integers(0, nq, nq)].mean() for _ in range(4000)]
        print(f"top-1 {a} − {b}: {dd.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]")
    json.dump(out, open("out/srkb.json", "w"))
