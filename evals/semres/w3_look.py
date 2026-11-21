"""W3 pricing look: the MuSiQue analogue of W2's x_out_s, on SR-J's 40 (seen block). Probes after reading hop 1:
q, qr (text), pivot_out(q, read), rocchio(q, read) (vector q + read), rocchio(pivot_out(q, read), read)."""
import json, sys, numpy as np, vecops as V
from scipy.stats import spearmanr
srj = json.load(open("out/srj-n40.json"))["cases"]; rows = {r["id"]: r for r in map(json.loads, open(sys.argv[1]))}
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); PFX = "Represent this sentence for searching relevant passages: "
res = {}
for c in srj:
    r = rows[c["id"]]; Pd = {p["idx"]: p["title"] + ". " + p["paragraph_text"] for p in r["paragraphs"]}
    E = m.encode([PFX + c["q"], c["read"]] + [Pd[i] for i in c["opts"]], normalize_embeddings=True); q, rd, O = E[0], E[1], E[2:]
    pr = dict(q=q, q_out_r=V.pivot_out(q, rd[None]), q_plus_r=V.rocchio(q, rd[None]), q_out_r_plus_r=V.rocchio(V.pivot_out(q, rd[None]), rd[None]))
    sc = {k: O @ v for k, v in pr.items()}; sc["qr(text)"] = np.array(c["cos_qr"]); p = np.array(c["p"])
    for k, s in sc.items():
        res.setdefault(k, []).append((s.argmax() == c["h2"], s.argmax() == p.argmax(), spearmanr(s, p)[0]))
for k, v in res.items():
    v = np.array(v, float); print(f"{k:16s} hop-2 top-1 {v[:,0].mean():.2f}, = Jev's pick {v[:,1].mean():.2f}, spearman {v[:,2].mean():.3f}")
