"""Namer pricing look (unregistered, SR-KB's first 300, seen data, $0, no Jev). Given gold hop 1 as read, can something
cheap name the bridge (hop 1's answer) from the read passage's door keys R (SR-KB's bundle)?
  B = keys in R whose words are all in hop 1's answer (gold, as in K-MISS's ceiling).
  namer ceiling: share of questions with B non-empty. Namers pick one key in R:
    cosq   argmax bge cos(question, key)
    cbq    argmax a-ColBERT MaxSim(question query tokens, key doc tokens), mean over the key's tokens
    rare   argmax 1/(df-1) (the rarest key; no question)
  end to end (lexical): walk only through the named key (its 1/(df-1) if the option shares it), ties by qr -> hop-2 top-1.
  *_k: the same, with ties broken by k (SR-K's sum) and then qr: lexicographic, no weight.
    uv run --with pylate --with numpy python namer_look.py MUSIQUE_DEV GRAPH_MQ"""
import hashlib, json, re, sys, numpy as np
from collections import Counter
src, gpath = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
held = set(np.random.default_rng(20261121).permutation(np.arange(40, len(qs)))[:40].tolist())
perm = [i for i in np.random.default_rng(1341).permutation(np.arange(40, len(qs))) if i not in held]; pool = perm[:300]
from sentence_transformers import SentenceTransformer
from pylate import models
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
cb = models.ColBERT("answerdotai/answerai-colbert-small-v1", device="cpu")
wd = lambda s: set(re.findall(r"[a-z0-9]+", s.lower())); W = lambda k: 1 / (df[k] - 1)
NM = ("cosq", "cbq", "rare"); named = Counter(); hop = {a: [] for a in ("k", "ceiling", "ceiling_k") + NM + tuple(a + "_k" for a in NM)}; sizes = []; nB = 0
for qi in pool:
    r = qs[qi]; d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p for p in r["paragraphs"]}; T = {i: P[i]["title"] + ". " + P[i]["paragraph_text"] for i in P}
    opts = sorted(i for i in P if i != h1); qt = wd(r["question"])
    R = sorted(k for k in keys[hid(P[h1])] if 2 <= df[k] <= 100 and not set(k.split()) <= qt)
    B = {k for k in R if set(k.split()) <= wd(d[0]["answer"])}; nB += bool(B); sizes.append(len(R))
    O = m.encode([T[i] for i in opts], normalize_embeddings=True); eqr = m.encode([QP + r["question"] + " " + T[h1]], normalize_embeddings=True)[0]
    tb = 1e-6 * (O @ eqr); sh = [keys[hid(P[i])] & set(R) for i in opts]; h = opts.index(h2)
    rank = lambda s: int(1 + (s > s[h]).sum())
    hop["k"].append(rank(np.array([sum(map(W, x)) for x in sh]) + tb))
    ksum = np.array([sum(map(W, x)) for x in sh]); tk = 1e-3 * ksum / (ksum.max() + 1e-9) + tb   # tie-break by k, then qr
    hop["ceiling"].append(rank(np.array([sum(map(W, x & B)) for x in sh]) + tb))
    hop["ceiling_k"].append(rank(np.array([sum(map(W, x & B)) for x in sh]) + tk))
    if not R:
        for a in NM: hop[a].append(rank(tb)); hop[a + "_k"].append(rank(tk))
        continue
    eq = m.encode([QP + r["question"]], normalize_embeddings=True)[0]; EK = m.encode(R, normalize_embeddings=True)
    Q = np.asarray(cb.encode([r["question"]], is_query=True)[0]); KT = [np.asarray(x) for x in cb.encode(R, is_query=False)]
    pick = dict(cosq=R[int(np.argmax(EK @ eq))], cbq=R[int(np.argmax([(Q @ kt.T).max(0).mean() for kt in KT]))],
                rare=R[int(np.argmax([W(k) for k in R]))])
    for a, k in pick.items():
        named[a] += k in B
        hop[a].append(rank(np.array([W(k) if k in x else 0 for x in sh]) + tb))
        hop[a + "_k"].append(rank(np.array([W(k) if k in x else 0 for x in sh]) + tk))
n = len(pool); s = np.array(sizes)
print(f"n {n}; bundle size median {np.median(s):.0f}, mean {s.mean():.1f}, max {s.max()}, empty {np.sum(s == 0)}")
print(f"bridge among the door keys (namer ceiling): {nB / n:.3f}")
for a in NM: print(f"namer {a:5s} names a bridge key {named[a] / n:.3f}")
for a, v in hop.items(): v = np.array(v); print(f"hop-2 via {a:8s} top-1 {np.mean(v == 1):.3f}  top-3 {np.mean(v <= 3):.3f}")
