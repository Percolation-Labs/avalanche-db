"""SR-E (REGISTERED-SRE.md), $0: does an entry that names its link land better than cosine alone? MuSiQue 2-hop dev.
For each passage v in a question's pool of 20, its link u*(v) is the passage sharing the most door strength with v
(Σ 1/(df − 1) over shared door keys not in the question, as in SR-K). Each arm picks a pair and an entry:
  cos    pair = the top 2 by cos(q, ·); entry = the top 1            (baseline)
  door   pair = argmax_v cos(q, ê_v + ê_u*(v)) over pairs (v, u*(v)); entry = the pair member with the higher cos(q, ·)
  vec    as door with u*(v) replaced by v's nearest passage by cosine   (control: a vector link instead of a door)
    uv run --with sentence-transformers --with numpy python sre.py MUSIQUE_DEV GRAPH_MQ N [--score]"""
import hashlib, json, re, sys
from collections import Counter
import numpy as np
src, gpath, N = sys.argv[1], sys.argv[2], int(sys.argv[3]); SCORE = "--score" in sys.argv
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]][:N]
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")
ARMS = ("cos", "door", "vec"); out = []; nolink = 0
for qi, r in enumerate(qs):
    P = sorted(r["paragraphs"], key=lambda p: p["idx"]); n = len(P)
    qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    D = [{k for k in keys[hid(p)] if 2 <= df[k] <= 100 and not set(k.split()) <= qt} for p in P]
    S = np.array([[sum(1 / (df[k] - 1) for k in D[a] & D[b]) if a != b else -1 for b in range(n)] for a in range(n)])
    E = m.encode(["Represent this sentence for searching relevant passages: " + r["question"]] + [p["title"] + ". " + p["paragraph_text"] for p in P], normalize_embeddings=True)
    q, V = E[0], E[1:]; C = V @ V.T; np.fill_diagonal(C, -9)
    link = S.argmax(1); nolink += int((S.max(1) <= 0).sum()); near = C.argmax(1)
    joint = lambda j: np.array([(V[v] + V[j[v]]) @ q / np.linalg.norm(V[v] + V[j[v]]) for v in range(n)])
    cq = V @ q; o2 = np.argsort(-cq)
    def pick(j):
        J = np.array([(V[v] + V[j[v]]) @ q / np.linalg.norm(V[v] + V[j[v]]) for v in range(n)]); v = int(J.argmax()); u = int(j[v])
        return (v if cq[v] >= cq[u] else u), {v, u}
    pk = dict(cos=(int(o2[0]), {int(o2[0]), int(o2[1])}), door=pick(link), vec=pick(near))
    if qi == 0:
        e, pr = pk["door"]; print(f"-- {r['question']}\n   door pair: {[P[i]['title'] for i in pr]}, entry {P[e]['title']}\n   cos pair: {[P[i]['title'] for i in pk['cos'][1]]}")
    rec = dict(id=r["id"], nolink=int((S.max(1) <= 0).sum()), same_entry=int(pk["door"][0] == pk["cos"][0]))
    if SCORE:
        d = r["question_decomposition"]; ix = {p["idx"]: i for i, p in enumerate(P)}
        h1, h2 = ix[d[0]["paragraph_support_idx"]], ix[d[1]["paragraph_support_idx"]]
        for a in ARMS: rec[a] = dict(entry=int(pk[a][0] == h1), has1=int(h1 in pk[a][1]), both=int(pk[a][1] == {h1, h2}))
    out.append(rec)
print(f"\n{len(out)} questions; passages with no door link {nolink} of {sum(len(r['paragraphs']) for r in qs)}; door entry = cos entry in {np.mean([o['same_entry'] for o in out]):.2f}")
if SCORE:
    rng = np.random.default_rng(0); nq = len(out)
    for met in ("entry", "has1", "both"):
        t = {a: np.array([o[a][met] for o in out], float) for a in ARMS}
        line = ", ".join(f"{a} {t[a].mean():.3f}" for a in ARMS)
        for a, b in (("door", "cos"), ("door", "vec")):
            dd = t[a] - t[b]; bt = [dd[rng.integers(0, nq, nq)].mean() for _ in range(4000)]
            line += f";  {a}−{b} {dd.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]"
        print(f"{met:5s}: {line}")
    json.dump(out, open("out/sre.json", "w"), indent=0)
