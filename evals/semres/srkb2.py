"""SR-KB2 (REGISTERED-SRKB2.md): SR-KB with james's holder-mean reading. Each key's vector is the mean of the stored
vectors of the graph passages that hold it, EXCLUDING the question's own 20-passage pool (hop 2 holds the shared key by
construction); a key with no outside holder is dropped. Graph vectors: ~/.cache/walklab/mq-graph-bge.npy (graph order).
Arms added: hm = combine(holder means, 1/(df-1)); rhm = rocchio(q, holder means, 1/(df-1)).

SR-KB (REGISTERED-SRKB.md), REM-1341, $0: a key-bundle probe for the next hop. Given the gold hop 1 as read (as in
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
import vecops as vo, os
src, gpath, N = sys.argv[1], sys.argv[2], int(sys.argv[3]); SCORE = "--score" in sys.argv
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}; NG = len(rows)
df = Counter(k for r in rows for k in r["keys"])
GV = np.load(os.path.expanduser("~/.cache/walklab/mq-graph-bge.npy")); gix = {r["d"]: i for i, r in enumerate(rows)}
holders = {}
for i, r in enumerate(rows):
    for k in r["keys"]:
        if 2 <= df[k] <= 100: holders.setdefault(k, []).append(i)
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
held = set(np.random.default_rng(20261121).permutation(np.arange(40, len(qs)))[:40].tolist())
pool = [i for i in np.random.default_rng(1341).permutation(np.arange(40, len(qs))) if i not in held][:N]
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
nh = []
ARMS = ("qr", "k", "rq_s", "hm", "rhm"); out = []; nokeys = 0
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
        ws = np.array([1 / (df[k] - 1) for k in R]); sc.update(kb_s=O @ vo.combine(K, ws), rq_s=O @ vo.rocchio(eq, K, ws))   # amendment 1
        poolg = {gix[hid(p)] for p in r["paragraphs"]}; HM, wh = [], []
        for k in R:
            hs = [i for i in holders[k] if i not in poolg]
            if hs: HM.append(vo.combine(GV[hs])); wh.append(1 / (df[k] - 1))
        nh.append(len(HM))
        if HM: sc.update(hm=O @ vo.combine(np.array(HM), wh), rhm=O @ vo.rocchio(eq, np.array(HM), wh))
        else: sc.update(hm=sc["q"], rhm=sc["q"])
    else:
        nokeys += 1; sc.update(kb=sc["q"], rq=sc["q"], rq_out=sc["q"], kb_s=sc["q"], rq_s=sc["q"])   # no bundle: fall back to the question
    if n_ == 0:
        print(f"-- {r['question']}\n   read: {P[h1]['title']}; bundle: {R[:8]}")
        for a in ("qr", "rq_s", "hm", "rhm"): print(f"   {a:3s} top 3: {[P[opts[j]]['title'] for j in np.argsort(-sc[a])[:3]]}")
    rec = dict(qi=int(qi), nkeys=len(R))
    if SCORE:
        h = opts.index(h2)
        for a in ARMS: rec[a] = int(1 + (sc[a] > sc[a][h]).sum())
    out.append(rec)
print(f"\nholder-mean keys per question median {int(np.median(nh))}, zero {sum(x == 0 for x in nh)}")
print(f"\n{len(out)} questions; empty bundle (fallback to q) {nokeys}; bundle size median {int(np.median([o['nkeys'] for o in out]))}")
if SCORE:
    rng = np.random.default_rng(0); nq = len(out)
    for a in ARMS: print(f"{a:7s} top-1 {np.mean([o[a] == 1 for o in out]):.3f}  top-3 {np.mean([o[a] <= 3 for o in out]):.3f}  MRR {np.mean([1 / o[a] for o in out]):.3f}")
    for a, b in (("rhm", "qr"), ("hm", "qr"), ("rhm", "rq_s"), ("rhm", "k")):
        dd = np.array([(o[a] == 1) - (o[b] == 1) for o in out], float); bt = [dd[rng.integers(0, nq, nq)].mean() for _ in range(4000)]
        print(f"top-1 {a} − {b}: {dd.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]")
    json.dump(out, open("out/srkb2.json", "w"))
