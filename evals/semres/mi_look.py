"""Mutual-inductance look (unregistered, $0, no Jev): MuSiQue dev 3hop2, two parallel branches A and B that join at J.
Does reading branch A's passage pull branch B's passage up (cross-branch, "mutual") as much as it pulls up J (the chain
neighbour)? Ranks among the pool's 19 passages other than the one read; lower is better.
  door  rank by door strength S[read, ·] = Σ 1/(df−1) over shared door keys (2 ≤ df ≤ 100, not in the question), ties by cos(q, ·)
  cosq  rank by cos(q, ·)                      cosqr  rank by cos(q + read, ·)     (bge-small)
Reports each target's median rank and top-1 share, reading A and reading B, plus a random non-gold passage as control.
    uv run --with sentence-transformers --with numpy python mi_look.py MUSIQUE_DEV GRAPH_MQ"""
import hashlib, json, re, sys
from collections import Counter
import numpy as np
src, gpath = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("3hop2") and r["answerable"]]
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
rng = np.random.default_rng(0); res = {}; miss = 0; anydoor = Counter()
for r in qs:
    P = sorted(r["paragraphs"], key=lambda p: p["idx"]); n = len(P); ix = {p["idx"]: i for i, p in enumerate(P)}
    d = r["question_decomposition"]; A, B, J = (ix[s["paragraph_support_idx"]] for s in d)
    miss += sum(hid(p) not in keys for p in P)
    qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    D = [{k for k in keys.get(hid(p), ()) if 2 <= df[k] <= 100 and not set(k.split()) <= qt} for p in P]
    T = [p["title"] + ". " + p["paragraph_text"] for p in P]
    E = m.encode([QP + r["question"]] + T, normalize_embeddings=True); cq = E[1:] @ E[0]
    ctrl = int(rng.choice([v for v in range(n) if v not in (A, B, J)]))
    for read, lab in ((A, "A"), (B, "B")):
        S = np.array([sum(1 / (df[k] - 1) for k in D[read] & D[v]) for v in range(n)])
        cqr = E[1:] @ m.encode([QP + r["question"] + " " + T[read]], normalize_embeddings=True)[0]
        other = B if read == A else A
        for tgt, tl in ((other, "other branch"), (J, "join J"), (ctrl, "random lure")):
            anydoor[lab, tl] += S[tgt] > 0
            for name, sc in (("door", S + 1e-6 * cq), ("cosq", cq), ("cosqr", cqr)):
                s = sc.copy(); s[read] = -np.inf; res.setdefault((lab, tl, name), []).append(int(1 + (s > s[tgt]).sum()))
nq = len(qs); print(f"3hop2 dev: {nq} questions; pool passages missing from the graph {miss}")
for lab in ("A", "B"):
    for tl in ("other branch", "join J", "random lure"):
        line = f"read {lab} -> {tl:12s} shares a door {anydoor[lab, tl] / nq:.2f} | "
        line += "  ".join(f"{name} med {np.median(res[lab, tl, name]):.0f} top1 {np.mean(np.array(res[lab, tl, name]) == 1):.2f}" for name in ("door", "cosq", "cosqr"))
        print(line)
