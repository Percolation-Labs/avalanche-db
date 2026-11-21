"""W1 pricing look 2 (before registering): a warp taught by the graph, not by Jev (dreaming, REM-1341).
Train (gold-free, Jev-free): MuSiQue answerable 2-hop questions 41–1252, minus SR-J-R's 40 (seeded permutation 20261121,
ids only). read = cosine's top passage in the pool (cosdoor's entry); options = the other 19; teacher = SR-K's key-door
strength k_str(read, v) = Σ 1/(df − 1) over shared door keys (2 ≤ df ≤ 100) not in the question, as a share over the 19.
Look (seen data, not the test): SR-J's 40 with read = gold hop 1 as in SR-J; compare against Jev's cached p and hop 2.
    uv run --with sentence-transformers --with scikit-learn --with scipy python w1_look2.py MUSIQUE_DEV GRAPH_MQ"""
import hashlib, json, re, sys, numpy as np
from collections import Counter
from scipy.stats import spearmanr
import vecops as V
src, gpath = sys.argv[1], sys.argv[2]
grows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in grows}
df = Counter(k for r in grows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
held = set(qs[i]["id"] for i in np.random.default_rng(20261121).permutation(np.arange(40, len(qs)))[:40])
train = [r for r in qs[40:] if r["id"] not in held]
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); PFX = "Represent this sentence for searching relevant passages: "
def doorkeys(p, qt): return {k for k in keys[hid(p)] if 2 <= df[k] <= 100 and not set(k.split()) <= qt}
Xq, Xr, Y, G = [], [], [], []
texts = [PFX + r["question"] for r in train] + [p["title"] + ". " + p["paragraph_text"] for r in train for p in sorted(r["paragraphs"], key=lambda p: p["idx"])]
E = m.encode(texts, normalize_embeddings=True, batch_size=64); nq = len(train); off = nq; used = 0
for gi, r in enumerate(train):
    P = sorted(r["paragraphs"], key=lambda p: p["idx"]); n = len(P); q = E[gi]; O = E[off:off + n]; off += n
    qt = set(re.findall(r"[a-z0-9]+", r["question"].lower())); D = [doorkeys(p, qt) for p in P]
    e = int(np.argmax(O @ q)); opts = [i for i in range(n) if i != e]
    k = np.array([sum(1 / (df[x] - 1) for x in D[e] & D[i]) for i in opts])
    if k.sum() <= 0: continue
    used += 1; Xq.append(q * O[opts]); Xr.append(O[e] * O[opts]); Y += list(k / k.sum()); G += [gi] * len(opts)
Xq, Xr, Y, G = np.vstack(Xq), np.vstack(Xr), np.array(Y), np.array(G)
print(f"train: {used} of {nq} questions have a door from the entry; {len(Y)} rows")
fits = {nm: V.fit_diag(X, Y, G) for nm, X in (("warp q", Xq), ("warp q+r", np.hstack([Xq, Xr])))}
for nm, (w, b, C, _) in fits.items(): print(f"  {nm}: C {C}")
srj = json.load(open("out/srj-n40.json"))["cases"]; rows = {r["id"]: r for r in qs}
S = {k: [] for k in ("cos_q", "cos_qr", "cos_r", "warp q", "warp q+r")}; JP, H2 = [], []
for c in srj:
    r = rows[c["id"]]; Pd = {p["idx"]: p["title"] + ". " + p["paragraph_text"] for p in r["paragraphs"]}
    Ec = m.encode([PFX + c["q"], c["read"]] + [Pd[i] for i in c["opts"]], normalize_embeddings=True); q, rd, O = Ec[0], Ec[1], Ec[2:]
    S["cos_q"].append(O @ q); S["cos_qr"].append(np.array(c["cos_qr"])); S["cos_r"].append(O @ rd)
    S["warp q"].append((q * O) @ fits["warp q"][0]); S["warp q+r"].append(np.hstack([q * O, rd * O]) @ fits["warp q+r"][0])
    JP.append(np.array(c["p"])); H2.append(c["h2"])
for k, ss in S.items():
    sp = np.mean([spearmanr(s, p)[0] for s, p in zip(ss, JP)]); top = np.mean([s.argmax() == p.argmax() for s, p in zip(ss, JP)])
    sh = np.mean([p.argmax() in np.argsort(-s)[:5] for s, p in zip(ss, JP)]); h2 = np.mean([s.argmax() == h for s, h in zip(ss, H2)])
    print(f"{k:9s}: spearman with Jev {sp:.3f}, top-1 = Jev's {top:.2f}, Jev's pick in top 5 {sh:.2f}, hop-2 top-1 {h2:.2f}")
