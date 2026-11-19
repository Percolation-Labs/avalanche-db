"""J4 (REGISTERED-J4.md), $0: per-attribute AUC of the gold door among the doors of what has been read.
    uv run --with scipy --with numpy python j4.py SCRATCH PROBE STORE OUTDIR"""
import hashlib, json, os, re, subprocess, sys
from collections import defaultdict
import numpy as np, scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l1 import G, load  # noqa: E402

SRC = os.path.expanduser("~/.cache/walklab/musique-src/musique_ans_v1.0_dev.jsonl")
K1, B_, READ = 1.2, .75, 5
scr, probe, store, od = sys.argv[1:5]
os.makedirs(od, exist_ok=True)


def hid(p): return "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]


src, text = {}, {}
for l in open(SRC):
    r = json.loads(l); src[r["id"]] = r
    for p in r["paragraphs"]:
        text[hid(p)] = p["title"] + ". " + p["paragraph_text"]
rows = [json.loads(l) for l in open(f"{scr}/dream/d1/graph-mq.jsonl")]
g = G(rows)
_, test = load(scr, g, "mq"); order = [q for q, *_ in test]

# keys (df 2..100), next (Beside) and near, both directions
mem = defaultdict(list)
for i, r in enumerate(rows):
    for k in r["keys"]:
        mem[k].append(i)
mem = {k: v for k, v in mem.items() if 2 <= len(v) <= 100}
pkeys = defaultdict(list)
for k, v in mem.items():
    for i in v:
        pkeys[i].append(k)
nxt, nea = defaultdict(set), defaultdict(set)
for i, r in enumerate(rows):
    for kind, m in (("next", nxt), ("near", nea)):
        for x in r[kind]:
            j = g.ix.get(x)
            if j is not None and j != i:
                m[i].add(j); m[j].add(i)

tok = lambda s: re.findall(r"[a-z0-9]+", s.lower())
vocab, ri, ci, vals, dl = {}, [], [], [], np.zeros(g.n)
for i, d in enumerate(g.ids):
    ts = tok(text.get(d, "")); dl[i] = len(ts); c = {}
    for t in ts:
        v = vocab.setdefault(t, len(vocab)); c[v] = c.get(v, 0) + 1
    for t, f in c.items():
        ri.append(i); ci.append(t); vals.append(f)
TF = sp.coo_matrix((vals, (ri, ci)), shape=(g.n, len(vocab)), dtype=float)
df = np.bincount(ci, minlength=len(vocab)); idf = np.log(1 + (g.n - df + .5) / (df + .5))
norm = K1 * (1 - B_ + B_ * dl[TF.row] / dl.mean())
W = sp.csr_matrix((idf[TF.col] * TF.data * (K1 + 1) / (TF.data + norm), (TF.row, TF.col)), shape=TF.shape).tocsc()


def bm25_all(q):
    ts = sorted({vocab[t] for t in tok(q) if t in vocab})
    return np.asarray(W[:, ts].sum(1)).ravel() if ts else np.zeros(g.n)


def search(batch):
    tf, of = f"{od}/_q.jsonl", f"{od}/_s.jsonl"
    with open(tf, "w") as f:
        for k, q in batch.items():
            f.write(json.dumps({"qid": k, "walk": {"question": q}}) + "\n")
    subprocess.run([probe, store, "x", of], env=dict(os.environ, E2E_SEARCHDUMP=tf), check=True, capture_output=True)
    return {r["qid"]: [g.ix.get(d, -1) for d, _ in r["S"]] for r in map(json.loads, open(of))}


def doors(R):
    """{candidate: attrs} for neighbours of R (excluding R)."""
    Rs = set(R); A = defaultdict(lambda: {"narrow": -np.inf, "strength": 0.0, "reads": set(), "beside": 0, "near": 0, "keys": set()})
    for r in R:
        for k in pkeys.get(r, ()):
            w = len(mem[k])
            for c in mem[k]:
                if c in Rs:
                    continue
                a = A[c]; a["narrow"] = max(a["narrow"], -w); a["strength"] += 1 / (w - 1); a["reads"].add(r); a["keys"].add(k)
        for c in nxt.get(r, ()):
            if c not in Rs:
                a = A[c]; a["beside"] = 1; a["strength"] += 1; a["reads"].add(r)
        for c in nea.get(r, ()):
            if c not in Rs:
                a = A[c]; a["near"] = 1; a["reads"].add(r)
    return A


def auc(v, gi):
    o = np.delete(v, gi); x = v[gi]
    return ((o < x).sum() + .5 * (o == x).sum()) / len(o)


info = {}
for q in order:
    s = src[q.split(":", 1)[1]]; d = s["question_decomposition"]
    info[q] = {"q": s["question"], "subq": [x["question"] for x in d], "ans": [x["answer"] for x in d],
               "gold": [g.ix.get(hid(next(p for p in s["paragraphs"] if p["idx"] == x["paragraph_support_idx"])), -1) for x in d]}
h1 = search({q: " ".join(info[q]["subq"][0].split()) for q in order})

NAMES = ("narrow", "strength", "fan-in", "beside", "near", "passage", "door text", "question")
out = {"RO": defaultdict(list), "RD": defaultdict(list)}; diag = {"RO": [], "RD": []}; cover = {"RO": [0, 0], "RD": [0, 0]}
for q in order:
    s = info[q]; dhits = [h1[q][:READ]]
    qb = bm25_all(s["q"])
    for j in range(1, len(s["subq"])):
        gj = s["gold"][j]; blind = " ".join(re.sub(r"#\d+", " ", s["subq"][j]).split()); bt = set(tok(blind))
        pb = bm25_all(blind)
        RD = sorted({x for h in dhits for x in h if x >= 0})
        for name, R in (("RO", [x for x in s["gold"][:j] if x >= 0]), ("RD", RD)):
            A = doors(R); cand = list(A); cover[name][1] += 1
            if gj < 0 or gj not in A:
                continue
            cover[name][0] += 1; gi = cand.index(gj)
            cols = {"narrow": [A[c]["narrow"] for c in cand], "strength": [A[c]["strength"] for c in cand],
                    "fan-in": [len(A[c]["reads"]) for c in cand], "beside": [A[c]["beside"] for c in cand],
                    "near": [A[c]["near"] for c in cand], "passage": pb[cand], "question": qb[cand],
                    "door text": [sum(set(tok(k)) <= bt for k in A[c]["keys"]) for c in cand]}
            for k in NAMES:
                out[name][k].append(auc(np.asarray(cols[k], float), gi))
            pa = s["ans"][j - 1].lower().strip()
            hit = np.array([pa in A[c]["keys"] for c in cand])
            diag[name].append((hit[gi], np.delete(hit, gi).mean()))
        # D's own next reads (J3's D arm): BM25 of the unfilled text among the doors of RD
        A = doors(RD); cand = np.array(list(A), int)
        o = cand[np.argsort(-pb[cand], kind="stable")] if len(cand) else cand
        dhits.append([int(x) for x in o[:READ] if pb[x] > 0])

rng = np.random.default_rng(0)
with open(f"{od}/j4.json", "w") as f:
    json.dump({n: {k: v for k, v in out[n].items()} for n in out}, f)
for name in ("RO", "RD"):
    print(f"{name}: gold among the doors in {cover[name][0]}/{cover[name][1]} later sub-questions")
    for grp, ks in (("connection", NAMES[:4]), ("likeness", NAMES[4:])):
        print(f"  {grp}")
        for k in ks:
            v = np.array(out[name][k]); bs = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(2000)]
            lo, hi = np.percentile(bs, [2.5, 97.5])
            print(f"    {k:10s} AUC {v.mean():.3f} [{lo:.3f}, {hi:.3f}]{'' if lo > .5 else '  (does not separate)'}")
    dg = np.array(diag[name], float)
    print(f"  diagnostic: a shared key equals the previous answer for gold {dg[:, 0].mean():.3f}, for other doors {dg[:, 1].mean():.3f}")
