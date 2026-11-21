"""'Beyond the name' pricing look (unregistered, $0, no Jev calls): SR-BN's fresh 300, now seen, with Jev's cached
passage p's (pj). What does Jev's passage choice use that the gold-named lexical step doesn't?
  Cells by (ceiling_k hit, jev_pass hit). Twins: options other than hop 2 that share a gold bridge key.
  Within the named set (options sharing the name), which second stage orders hop 2 first?
    qr (bge cos of question + read), cq (bge cos of question), rel (count of question words not in the read and not in the
    name that appear in v), jev (Jev's own pj restricted to the set).
    uv run --with sentence-transformers --with numpy python beyond_look.py MUSIQUE_DEV GRAPH_MQ"""
import hashlib, json, re, sys, numpy as np
from collections import Counter
src, gpath = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
N = json.load(open("out/srbn-names-fresh.json")); RK = json.load(open("out/srbn-name-fresh.json"))["ranks"]
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
STOP = {"the", "a", "an", "of", "in", "on", "and", "is", "was", "to", "for", "by", "at", "who", "what", "which", "where",
        "when", "how", "did", "does", "do", "that", "with", "from", "as", "it", "its", "his", "her", "their", "be", "are", "were"}
wd = lambda s: set(re.findall(r"[a-z0-9]+", s.lower())); W = lambda k: 1 / (df[k] - 1)
cell = Counter(); twin = Counter(); within = {a: Counter() for a in ("qr", "cq", "rel", "jev")}; ex = []
for j, (qi, v) in enumerate(N.items()):
    r = qs[int(qi)]; d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p for p in r["paragraphs"]}; T = {i: P[i]["title"] + ". " + P[i]["paragraph_text"] for i in P}
    opts = sorted(i for i in P if i != h1); h = opts.index(h2); R = set(v["R"])
    B = {k for k in R if set(k.split()) <= wd(d[0]["answer"])}
    sh = [keys[hid(P[i])] & R for i in opts]
    c = (RK["ceiling_k"][j] == 1, RK["jev_pass"][j] == 1); cell[c] += 1
    S = [i for i, x in enumerate(sh) if x & B]          # the gold-named set
    if not B or h not in S: twin["hop 2 not in named set"] += 1; continue
    tw = len(S) > 1; twin["twin" if tw else "alone"] += 1
    if not tw: continue
    O = m.encode([T[i] for i in opts], normalize_embeddings=True)
    eqr = m.encode([QP + r["question"] + " " + T[h1]], normalize_embeddings=True)[0]; eq = m.encode([QP + r["question"]], normalize_embeddings=True)[0]
    relw = wd(r["question"]) - wd(T[h1]) - wd(d[0]["answer"]) - STOP
    sc = dict(qr=O @ eqr, cq=O @ eq, rel=np.array([len(relw & wd(T[i])) + 1e-6 * (O @ eqr)[n] for n, i in enumerate(opts)]), jev=np.array(v["pj"]))
    for a in within:
        best = max(S, key=lambda n: sc[a][n]); within[a][best == h] += 1
    if len(ex) < 8 and c == (False, True):
        ex.append((r["question"], d[0]["answer"], sorted(relw), [P[opts[n]]["title"] for n in S], P[h2]["title"]))
print("cells (gold-named lexical step hit, jev_pass hit):", {f"{a:d}{b:d}": n for (a, b), n in sorted(cell.items())})
print("named-set structure:", dict(twin))
nt = twin["twin"]
for a, c in within.items(): print(f"within twins (n {nt}): {a:4s} picks hop 2 {c[True] / nt:.3f}")
for e in ex: print("-", e)
