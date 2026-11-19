"""J3 (REGISTERED-J3.md), $0: later MuSiQue hops searched among the doors (graph neighbours) of what has been read.
    uv run --with scipy --with numpy python j3.py SCRATCH PROBE STORE J2DIR OUTDIR
Arms: D (doors of own reads), DO (doors of earlier gold), B (BM25, whole corpus), F (J2's recorded Jev-filled probe
search). Prints the later-hop top-5 rates, the gate, the bar, and total recall at 10 for D."""
import hashlib, json, os, re, subprocess, sys
import numpy as np, scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l1 import G, load, UNI  # noqa: E402
from p2 import adjacency  # noqa: E402

SRC = os.path.expanduser("~/.cache/walklab/musique-src/musique_ans_v1.0_dev.jsonl")
K1, B_, READ = 1.2, .75, 5  # textbook BM25; 5 reads per hop as in J1/J2/P2
scr, probe, store, j2d, od = sys.argv[1:6]
os.makedirs(od, exist_ok=True)


def hid(p): return "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]


src, text = {}, {}
for l in open(SRC):
    r = json.loads(l); src[r["id"]] = r
    for p in r["paragraphs"]:
        text[hid(p)] = p["title"] + ". " + p["paragraph_text"]

g = G([json.loads(l) for l in open(f"{scr}/dream/d1/graph-mq.jsonl")])
N = adjacency(g)
_, test = load(scr, g, "mq"); order = [q for q, *_ in test]; gold_all = {q: gi for q, _, gi, _, _ in test}

# BM25 matrix over the corpus (rows = g.ids)
tok = lambda s: re.findall(r"[a-z0-9]+", s.lower())
vocab, rows, cols, vals, dl = {}, [], [], [], np.zeros(g.n)
for i, d in enumerate(g.ids):
    ts = tok(text.get(d, "")); dl[i] = len(ts)
    c = {}
    for t in ts:
        v = vocab.setdefault(t, len(vocab)); c[v] = c.get(v, 0) + 1
    for t, f in c.items():
        rows.append(i); cols.append(t); vals.append(f)
TF = sp.csr_matrix((vals, (rows, cols)), shape=(g.n, len(vocab)), dtype=float)
df = np.bincount(cols, minlength=len(vocab)); idf = np.log(1 + (g.n - df + .5) / (df + .5))
TF = TF.tocoo(); norm = K1 * (1 - B_ + B_ * dl[TF.row] / dl.mean())
W = sp.csr_matrix((idf[TF.col] * TF.data * (K1 + 1) / (TF.data + norm), (TF.row, TF.col)), shape=TF.shape).tocsc()


def bm25(q, cand=None):
    """Ranked passage indices for query q, among cand (array) or the whole corpus."""
    ts = sorted({vocab[t] for t in tok(q) if t in vocab})
    if not ts:
        return []
    s = np.asarray(W[:, ts].sum(1)).ravel()
    idx = np.arange(g.n) if cand is None else np.asarray(cand)
    sc = s[idx]; o = np.argsort(-sc, kind="stable")
    return [int(idx[k]) for k in o if sc[k] > 0]


def doors(R):
    R = [x for x in R if x >= 0]
    if not R:
        return np.array([], int)
    nb = np.asarray(N[R].sum(0)).ravel() > 0; nb[R] = False
    return np.where(nb)[0]


def search(batch):
    tf, of = f"{od}/_q.jsonl", f"{od}/_s.jsonl"
    with open(tf, "w") as f:
        for k, q in batch.items():
            f.write(json.dumps({"qid": k, "walk": {"question": q}}) + "\n")
    subprocess.run([probe, store, "x", of], env=dict(os.environ, E2E_SEARCHDUMP=tf), check=True, capture_output=True)
    return {r["qid"]: [g.ix.get(d, -1) for d, _ in r["S"]] for r in map(json.loads, open(of))}


J2 = {r["qid"]: r for r in map(json.loads, open(f"{j2d}/j1-J.jsonl"))}
info = {}
for q in order:
    d = src[q.split(":", 1)[1]]["question_decomposition"]; ps = src[q.split(":", 1)[1]]["paragraphs"]
    info[q] = {"subq": [s["question"] for s in d],
               "gold": [g.ix.get(hid(next(p for p in ps if p["idx"] == s["paragraph_support_idx"])), -1) for s in d]}
# hop 1 (all arms) and F (J2's recorded queries, every hop) through the probe
batch = {f"{q}|{j}": x for q in order for j, x in enumerate(J2[q]["queries"])}
F = search(batch)
assert all(J2[q]["queries"][0] == " ".join(info[q]["subq"][0].split()) for q in order)


def rank(lst, x): return lst.index(x) + 1 if x >= 0 and x in lst else None


res = {a: [] for a in ("F", "B", "D", "DO")}; meta = []; dseeds = {}
for q in order:
    s = info[q]; h1 = F[f"{q}|0"]; dhits = [h1[:READ]]
    for j in range(1, len(s["subq"])):
        gj = s["gold"][j]; blind = " ".join(re.sub(r"#\d+", " ", s["subq"][j]).split())
        Rd = sorted({x for h in dhits for x in h})
        D = bm25(blind, doors(Rd)); dhits.append(D[:READ])
        DO = bm25(blind, doors(s["gold"][:j]))
        res["F"].append(rank(F.get(f"{q}|{j}", []), gj)); res["B"].append(rank(bm25(blind), gj))
        res["D"].append(rank(D, gj)); res["DO"].append(rank(DO, gj))
        meta.append({"qid": q, "hop": j + 1, "prev_gold_read": s["gold"][j - 1] in Rd, "n_doors": int(len(doors(Rd))),
                     "gold_in_doors": bool(gj in set(doors(Rd).tolist())), **{a: res[a][-1] for a in res}})
    seeds, k = [], 0
    while len(seeds) < 5 and any(k < len(h) for h in dhits):
        for h in dhits:
            if k < len(h) and h[k] not in seeds and h[k] >= 0 and len(seeds) < 5:
                seeds.append(h[k])
        k += 1
    dseeds[q] = seeds
with open(f"{od}/j3-hops.jsonl", "w") as f:
    for m in meta:
        f.write(json.dumps(m) + "\n")

top5 = {a: np.array([r is not None and r <= 5 for r in v], float) for a, v in res.items()}
n = len(meta); rng = np.random.default_rng(0)


def pdiff(a, b):
    d = top5[a] - top5[b]; bs = [d[rng.integers(0, n, n)].mean() for _ in range(2000)]
    lo, hi = np.percentile(bs, [2.5, 97.5]); return d.mean(), lo, hi


print(f"later sub-questions: {n}")
for a in ("F", "B", "D", "DO"):
    v = res[a]
    bins = [np.mean([r is not None and lo_ <= r <= hi_ for r in v]) for lo_, hi_ in ((1, 5), (6, 20), (21, 100))]
    print(f"  {a:2s} top5 {bins[0]:.3f}  6-20 {bins[1]:.3f}  21-100 {bins[2]:.3f}  beyond/absent {1 - sum(bins):.3f}")
pg = np.mean([m["prev_gold_read"] for m in meta]); gid = np.mean([m["gold_in_doors"] for m in meta])
print(f"  D: previous hop's gold among reads {pg:.3f}; this hop's gold among the doors {gid:.3f}; median doors "
      f"{int(np.median([m['n_doors'] for m in meta]))} of {g.n}")
for flag in (True, False):
    sub = [m for m in meta if m["prev_gold_read"] == flag]
    print(f"  D top5 where previous gold {'was' if flag else 'was not'} read (n {len(sub)}): "
          f"{np.mean([m['D'] is not None and m['D'] <= 5 for m in sub]):.3f}")
gd, glo, ghi = pdiff("DO", "F")
print(f"gate DO − F {gd:+.3f} [{glo:+.3f}, {ghi:+.3f}]: {'open' if gd >= .05 else 'CLOSED'}")
if gd < .05:
    sys.exit("J3: gate closed; D not scored")
d1, l1_, h1_ = pdiff("D", "F"); d2, l2, h2 = pdiff("D", "B")
print(f"bar D − F {d1:+.3f} [{l1_:+.3f}, {h1_:+.3f}];  D − B {d2:+.3f} [{l2:+.3f}, {h2:+.3f}]")
print("J3:", "pass" if gd >= .05 and d1 >= .05 and l1_ > 0 and l2 > 0 else "fail")

# secondary: total recall at 10 for D (5 seeds + uniform avalanche top 5 beyond)
seeds = [dseeds[q] for q in order]; P, _ = g.run(seeds, UNI); tot = []
for c, q in enumerate(order):
    p = P[:, c].copy(); p[seeds[c]] = -1; top = [int(t) for t in np.argsort(-p)[:5] if p[t] > 0]
    tot.append(len(gold_all[q] & (set(seeds[c]) | set(top))) / len(gold_all[q]))
print(f"total recall at 10, D: {np.mean(tot):.3f}  (J2 J .586, blind .504, single .475)")
with open(f"{od}/j3-D.jsonl", "w") as f:
    for q in order:
        f.write(json.dumps({"qid": q, "seeds": [g.ids[x] for x in dseeds[q]]}) + "\n")
