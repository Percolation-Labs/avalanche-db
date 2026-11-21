"""SR-CB post-hoc control (not registered; labelled in RESULT-SRCB): a LEXICAL gold ceiling on the same questions.
lex_gb(v) = fraction of the hop-1 answer's words present in v's text, ties broken by bge qr. Uses gold, like a_gb.
Also: how often hop 2 contains the whole answer string, and how often some other option does too (twins).
    uv run --with sentence-transformers --with numpy python srcb_lexgb.py MUSIQUE_DEV SET"""
import json, re, sys
import numpy as np
src, SET = sys.argv[1], sys.argv[2]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
held = set(np.random.default_rng(20261121).permutation(np.arange(40, len(qs)))[:40].tolist())
perm = [i for i in np.random.default_rng(1341).permutation(np.arange(40, len(qs))) if i not in held]
pool = perm[:300] if SET == "kb" else perm[300:600]
from sentence_transformers import SentenceTransformer
bge = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
W = lambda s: set(re.findall(r"[a-z0-9]+", s.lower()))
rk, inh2, twin = [], 0, 0
for qi in pool:
    r = qs[qi]; d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p for p in r["paragraphs"]}; T = {i: P[i]["title"] + ". " + P[i]["paragraph_text"] for i in P}
    opts = sorted(i for i in P if i != h1); a = d[0]["answer"]; aw = W(a)
    E = bge.encode([QP + r["question"] + " " + T[h1]] + [T[i] for i in opts], normalize_embeddings=True); q = E[1:] @ E[0]
    s = np.array([len(aw & W(T[i])) / max(len(aw), 1) for i in opts]) + 1e-6 * q
    h = opts.index(h2); rk.append(int(1 + (s > s[h]).sum()))
    has = [a.lower() in T[i].lower() for i in opts]; inh2 += has[h]; twin += has[h] and sum(has) > 1
v = np.array(rk); n = len(v)
print(f"SET={SET}: lex_gb top-1 {np.mean(v == 1):.3f} top-3 {np.mean(v <= 3):.3f} MRR {np.mean(1 / v):.3f}; "
      f"hop 2 contains the answer string {inh2 / n:.3f}; and another option does too {twin / n:.3f}")
json.dump(rk, open(f"out/srcb-lexgb-{SET}.json", "w"))
