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
rk, rt, inh2, twin, tit, tw_tit = [], [], 0, 0, 0, 0
N = lambda s: " ".join(re.findall(r"[a-z0-9]+", s.lower()))   # normalised text
CB = {o["qi"]: o for o in json.load(open(f"out/srcb-{SET}.json"))}; tw = []
for qi in pool:
    r = qs[qi]; d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p for p in r["paragraphs"]}; T = {i: P[i]["title"] + ". " + P[i]["paragraph_text"] for i in P}
    opts = sorted(i for i in P if i != h1); a = d[0]["answer"]; aw = W(a)
    E = bge.encode([QP + r["question"] + " " + T[h1]] + [T[i] for i in opts], normalize_embeddings=True); q = E[1:] @ E[0]
    s = np.array([len(aw & W(T[i])) / max(len(aw), 1) for i in opts]) + 1e-6 * q
    h = opts.index(h2); rk.append(int(1 + (s > s[h]).sum()))
    ti = np.array([float(N(P[i]["title"]) == N(a)) for i in opts]) + s * 1e-3   # title IS the bridge, then answer words, then qr
    rt.append(int(1 + (ti > ti[h]).sum())); tit += ti[h] >= 1
    has = [a.lower() in T[i].lower() for i in opts]; inh2 += has[h]; t2 = has[h] and sum(has) > 1; twin += t2
    if t2: tw.append((CB[int(qi)]["a_gb"] == 1, rk[-1] == 1, rt[-1] == 1, ti[h] >= 1))
v = np.array(rk); n = len(v)
print(f"SET={SET}: lex_gb top-1 {np.mean(v == 1):.3f} top-3 {np.mean(v <= 3):.3f} MRR {np.mean(1 / v):.3f}; "
      f"hop 2 contains the answer string {inh2 / n:.3f}; and another option does too {twin / n:.3f}")
vt = np.array(rt); print(f"lex_title (title == bridge, then answer words, then qr) top-1 {np.mean(vt == 1):.3f}; hop 2's title is the bridge {tit / n:.3f}")
T_ = np.array(tw, bool); print(f"twins n={len(T_)}: a_gb top-1 {T_[:,0].mean():.3f}, lex_gb {T_[:,1].mean():.3f}, lex_title {T_[:,2].mean():.3f}; hop 2 titled by the bridge {T_[:,3].mean():.3f}")
A = np.array([CB[int(q)]["a_gb"] == 1 for q in pool]); rng = np.random.default_rng(0); d = A.astype(float) - (vt == 1)
bt = [d[rng.integers(0, n, n)].mean() for _ in range(4000)]; print(f"a_gb − lex_title {d.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]")
json.dump(rk, open(f"out/srcb-lexgb-{SET}.json", "w"))
