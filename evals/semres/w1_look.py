"""W1 pricing look (before registering): on SR-J's 40 (the training block only), how much of Jev's price can a
diagonal warp of cos recover, held out by question? Features q⊙v and r⊙v (bge-small, as SR-J). $0, cached Jev p.
    uv run --with sentence-transformers --with scikit-learn python w1_look.py MUSIQUE_DEV"""
import json, sys, numpy as np
from scipy.stats import spearmanr
from sklearn.model_selection import GroupKFold
import vecops as V
src = sys.argv[1]; srj = json.load(open("out/srj-n40.json"))["cases"]
rows = {r["id"]: r for r in map(json.loads, open(src))}
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); PFX = "Represent this sentence for searching relevant passages: "
Xq, Xr, Y, G, H2, C0, CQR = [], [], [], [], [], [], []
for gi, c in enumerate(srj):
    r = rows[c["id"]]; P = {p["idx"]: p["title"] + ". " + p["paragraph_text"] for p in r["paragraphs"]}
    E = m.encode([PFX + c["q"], c["read"]] + [P[i] for i in c["opts"]], normalize_embeddings=True)
    q, rd, O = E[0], E[1], E[2:]
    assert np.allclose(O @ q, c["cos"], atol=1e-3), "re-embedding differs from SR-J's cos"
    Xq.append(q * O); Xr.append(rd * O); Y += list(c["p"]); G += [gi] * len(O); H2.append(c["h2"]); C0.append(np.array(c["cos"])); CQR.append(np.array(c["cos_qr"]))
Xq, Xr, Y, G = np.vstack(Xq), np.vstack(Xr), np.array(Y), np.array(G)
def per_q(score):
    sp, top, sh5, h2 = [], [], [], []
    for gi in range(len(srj)):
        s = score[G == gi]; p = Y[G == gi]; o = np.argsort(-s)
        sp.append(spearmanr(s, p)[0]); top.append(int(o[0] == p.argmax())); sh5.append(int(p.argmax() in o[:5])); h2.append(int(o[0] == H2[gi]))
    return f"spearman {np.mean(sp):.3f}, top-1 = Jev's {np.mean(top):.2f}, Jev's pick in top 5 {np.mean(sh5):.2f}, hop-2 top-1 {np.mean(h2):.2f}"
print("cos_q   :", per_q(np.concatenate(C0)))
print("cos_qr  :", per_q(np.concatenate(CQR)))
print("cos_r   :", per_q(Xr.sum(1)))
for nm, X in (("warp q", Xq), ("warp q+r", np.hstack([Xq, Xr]))):
    out = np.zeros(len(Y))
    for tr, te in GroupKFold(8).split(X, Y, G):
        w, b, C, _ = V.fit_diag(X[tr], Y[tr], G[tr]); out[te] = X[te] @ w
    print(f"{nm:8s}:", per_q(out))
print("Jev     :", per_q(Y))
