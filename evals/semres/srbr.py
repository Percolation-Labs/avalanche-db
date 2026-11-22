"""SR-BR (REGISTERED-SRBR.md), bill. Reward-driven bridge weighting: dreaming that learns from walk outcomes. $0, no Jev.
MuSiQue train 2-hop answerable (james's corpus and graph). Split by sha256(id) parity: half 0 learns, half 1 is tested
(SR-BX's scored 300 and its stage 0 excluded from the test half).
Walk: entry e = argmax cos(q, ·) (bge-small); step s = argmax weighted door strength from e, ties by cos(q, ·); if no
door, the second by cos. Weighted strength S_w[e, v] = Σ_{k in D[e] ∩ D[v]} (1 + r(e, k))(1 + r(v, k)) / (df_k − 1), with
D = door keys (2 <= df <= 100, not inside the question). r is keyed by (passage id, key), so it transfers across questions.
Update (one walk, one shared key k between e and s): r(e, k) += 1/|S_k| and r(s, k) += 1/|S_k|, where |S_k| is the number of
pool passages other than e sharing k (diminishing returns over parallel bridges).
Weight sets learned on half 0:
  R    rewarded walks only (reward = {e, s} is the gold pair: a feedback stand-in, gold on the learn half only)
  F    failed walks only (control)
  RND  count-matched: as many update events as R, drawn at random from all walks' events regardless of outcome (control)
  B    every learn question's gold bridge (h1, h2) shared keys, walked or not (supervised ceiling, labelled gold)
  R2, R3  R re-walked on its own weighted graph for 2 and 3 passes (cumulative), the convergence secondary
Test: both hops ({e, s} = {h1, h2}) on half 1 under each weight set, paired against unweighted. Strata: test questions
whose gold pair (h1, h2) equals some learn question's gold pair ("shared pair") against the rest.
    uv run --with numpy --with sentence-transformers python srbr.py TRAIN_CORPUS GRAPH_TRAIN [--look]"""
import hashlib, json, re, sys
from collections import Counter, defaultdict
import numpy as np
src, gpath = sys.argv[1], sys.argv[2]; LOOK = "--look" in sys.argv
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
half = lambda mid: int(hashlib.sha256(mid.encode()).hexdigest()[:8], 16) % 2
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
bx = set(np.random.default_rng(1341).permutation(len(qs))[:304].tolist())   # SR-BX's 300 + stage 0
learn = [i for i in range(len(qs)) if half(qs[i]["id"]) == 0]
test = [i for i in range(len(qs)) if half(qs[i]["id"]) == 1 and i not in bx]
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
C = {}
for i in learn + test:
    r = qs[i]; P = sorted(r["paragraphs"], key=lambda p: p["idx"]); ids = [hid(p) for p in P]
    qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    D = [{k for k in keys.get(x, ()) if 2 <= df[k] <= 100 and not set(k.split()) <= qt} for x in ids]
    E = m.encode([QP + r["question"]] + [p["title"] + ". " + p["paragraph_text"] for p in P], normalize_embeddings=True)
    d = r["question_decomposition"]; ix = {p["idx"]: j for j, p in enumerate(P)}
    C[i] = dict(ids=ids, D=D, cq=E[1:] @ E[0], h1=ix[d[0]["paragraph_support_idx"]], h2=ix[d[1]["paragraph_support_idx"]])
pair = lambda c: frozenset((c["ids"][c["h1"]], c["ids"][c["h2"]]))
lpairs = {pair(C[i]) for i in learn}
shared = {i for i in test if pair(C[i]) in lpairs}
print(f"2-hop questions {len(qs)}; learn {len(learn)}; test {len(test)} (SR-BX's 304 excluded); test questions sharing a learn gold pair {len(shared)}")
if LOOK: sys.exit()
def walk(c, r):
    n = len(c["ids"]); e = int(np.argmax(c["cq"])); ue = c["ids"][e]
    S = np.array([sum((1 + r.get((ue, k), 0)) * (1 + r.get((c["ids"][v], k), 0)) / (df[k] - 1) for k in c["D"][e] & c["D"][v]) if v != e else -1.0 for v in range(n)])
    s = max(np.nonzero(S == S.max())[0], key=lambda u: c["cq"][u]) if S.max() > 0 else [v for v in np.argsort(-c["cq"]) if v != e][0]
    return e, int(s)
def events(c, e, s):
    out = []
    for k in c["D"][e] & c["D"][s]:
        nS = sum(1 for v in range(len(c["ids"])) if v != e and k in c["D"][v])
        out += [((c["ids"][e], k), 1 / nS), ((c["ids"][s], k), 1 / nS)]
    return out
def apply(r, evs):
    r = dict(r)
    for key, w in evs: r[key] = r.get(key, 0) + w
    return r
ok = lambda c, e, s: {e, s} == {c["h1"], c["h2"]}
W = {"none": {}}
walks = {i: walk(C[i], {}) for i in learn}
evR = [ev for i in learn if ok(C[i], *walks[i]) for ev in events(C[i], *walks[i])]
evF = [ev for i in learn if not ok(C[i], *walks[i]) for ev in events(C[i], *walks[i])]
allw = [ev for i in learn for ev in events(C[i], *walks[i])]
rng = np.random.default_rng(0)
W["R"] = apply({}, evR); W["F"] = apply({}, evF)
W["RND"] = apply({}, [allw[j] for j in rng.choice(len(allw), len(evR), replace=False)]) if len(evR) <= len(allw) else apply({}, allw)
W["B"] = apply({}, [ev for i in learn for ev in events(C[i], C[i]["h1"], C[i]["h2"])])
rr = W["R"]; prev = rr
for p in (2, 3):
    ev = [x for i in learn for x in (events(C[i], *walk(C[i], rr)) if ok(C[i], *walk(C[i], rr)) else [])]
    rr = apply(rr, ev); W[f"R{p}"] = rr
    ch = sum(abs(rr.get(k, 0) - prev.get(k, 0)) for k in set(rr) | set(prev)) / max(sum(prev.values()), 1e-9)
    print(f"pass {p}: learn-half success {np.mean([ok(C[i], *walk(C[i], rr)) for i in learn]):.3f}; relative weight change {ch:.3f}"); prev = rr
print(f"learn half: pass-1 success {np.mean([ok(C[i], *walks[i]) for i in learn]):.3f}; events R {len(evR)}, F {len(evF)}, all {len(allw)}, B {sum(1 for i in learn for _ in events(C[i], C[i]['h1'], C[i]['h2']))}")
for name in ("R", "R3", "B"):
    top = sorted(W[name].items(), key=lambda x: -x[1])[:10]
    print(f"top-10 weights {name}: " + "; ".join(f"{k[1]!r}@{k[0][-6:]} {v:.2f}" for k, v in top))
res = {name: np.array([int(ok(C[i], *walk(C[i], W[name]))) for i in test]) for name in W}
sh = np.array([i in shared for i in test])
for name in W: print(f"test both hops {name:5s} {res[name].mean():.3f}  (shared pair {res[name][sh].mean():.3f}, n {sh.sum()}; no shared pair {res[name][~sh].mean():.3f}, n {(~sh).sum()})")
def ci(d, lab):
    bt = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]
    print(f"{lab}: {d.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}] (n {len(d)})")
ci(res["R"] - res["none"], "PRIMARY both hops, R − unweighted (all test)")
ci((res["R"] - res["none"])[~sh], "R − unweighted, no shared gold pair")
ci((res["R"] - res["none"])[sh], "R − unweighted, shared gold pair")
for a, b in (("R", "RND"), ("R", "F"), ("B", "R"), ("R3", "R")): ci(res[a] - res[b], f"{a} − {b}")
json.dump({k: v.tolist() for k, v in res.items()} | {"shared": sh.tolist(), "test": test}, open("out/srbr.json", "w"))
