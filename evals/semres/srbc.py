"""SR-BC (REGISTERED-SRBC.md), bill. Reward-driven bridge weighting with an update that can reach a fixed point. $0.
Everything but the update is SR-BR's (srbr.py): data, split, walk, events, gold-pair reward stand-in on the learn half.
  T  r_{p+1} = sum of events of learn walks that succeed under r_p (replace, not accumulate); run until a success set
     repeats; a repeat of the previous set is a fixed point, an earlier one a cycle (test arm = mean of cycle states).
  U  Q_{p+1} = Q_p + learn questions succeeding under r(Q_p), each rewarded once with its first successful walk's events.
Embeddings are cached at $SRBC_CACHE (default ./srbc-emb.npz, not committed).
    uv run --with numpy --with sentence-transformers python srbc.py TRAIN_CORPUS GRAPH_TRAIN"""
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
import os
cache = os.environ.get("SRBC_CACHE", "srbc-emb.npz"); Ec = dict(np.load(cache)) if os.path.exists(cache) else {}
C = {}; m = None; QP = "Represent this sentence for searching relevant passages: "
for i in learn + test:
    r = qs[i]; P = sorted(r["paragraphs"], key=lambda p: p["idx"]); ids = [hid(p) for p in P]
    qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    D = [{k for k in keys.get(x, ()) if 2 <= df[k] <= 100 and not set(k.split()) <= qt} for x in ids]
    if r["id"] not in Ec:
        if m is None:
            from sentence_transformers import SentenceTransformer
            m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")
        E = m.encode([QP + r["question"]] + [p["title"] + ". " + p["paragraph_text"] for p in P], normalize_embeddings=True)
        Ec[r["id"]] = E[1:] @ E[0]
    d = r["question_decomposition"]; ix = {p["idx"]: j for j, p in enumerate(P)}
    C[i] = dict(ids=ids, D=D, cq=Ec[r["id"]], h1=ix[d[0]["paragraph_support_idx"]], h2=ix[d[1]["paragraph_support_idx"]])
if m is not None: np.savez(cache, **Ec)
pair = lambda c: frozenset((c["ids"][c["h1"]], c["ids"][c["h2"]]))
lpairs = {pair(C[i]) for i in learn}
shared = {i for i in test if pair(C[i]) in lpairs}
print(f"2-hop questions {len(qs)}; learn {len(learn)}; test {len(test)} (SR-BX's 304 excluded); test questions sharing a learn gold pair {len(shared)}")
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

def succ(r): return frozenset(i for i in learn if ok(C[i], *walk(C[i], r)))
# T: the state is the success set; weights from a set are the events of those questions' current walks
r = {}; seq = []; seen = {}
S = succ(r); p = 0
print(f"T pass 0 (unweighted): learn success {len(S)/len(learn):.3f} ({len(S)})")
while True:
    p += 1
    r_new = apply({}, [ev for i in sorted(S) for ev in events(C[i], *walk(C[i], r))])
    S_new = succ(r_new)
    ch = sum(abs(r_new.get(k, 0) - r.get(k, 0)) for k in set(r_new) | set(r)) / max(sum(r_new.values()), 1e-9)
    print(f"T pass {p}: weights from {len(S)} successes; learn success now {len(S_new)/len(learn):.3f} ({len(S_new)}); "
          f"in +{len(S_new - S)}, out -{len(S - S_new)}; relative weight change {ch:.3f}")
    seq.append((S, r_new))
    if S in seen:
        start = seen[S]; cyc = seq[start:-1]
        period = len(cyc)
        break
    seen[S] = len(seq) - 1
    r, S = r_new, S_new
if period == 1:
    print(f"H-C1: T reached a FIXED POINT after {p - 1} pass(es) (success set repeats with period 1)")
    Tstar = cyc[0][1]
else:
    print(f"H-C1: T entered a CYCLE of period {period}; test arm = mean of the cycle's weight states")
    ks = set().union(*[set(w) for _, w in cyc]); Tstar = {k: sum(w.get(k, 0) for _, w in cyc) / period for k in ks}
# U: monotone, each question rewarded once with its first successful walk
Q = {}; rU = {}; p = 0
while True:
    p += 1
    new = {i: walk(C[i], rU) for i in learn if i not in Q and ok(C[i], *walk(C[i], rU))}
    print(f"U pass {p}: +{len(new)} questions (rewarded total {len(Q) + len(new)}); learn success under current weights "
          f"{len(succ(rU))/len(learn):.3f}")
    if not new: break
    Q.update(new); rU = apply({}, [ev for i in sorted(Q) for ev in events(C[i], *Q[i])])
W = {"none": {}, "R": apply({}, [ev for i in learn if ok(C[i], *walk(C[i], {})) for ev in events(C[i], *walk(C[i], {}))]),
     "Tstar": Tstar, "Ustar": rU}
rr = W["R"]
for _ in (2, 3):
    rr = apply(rr, [x for i in learn for x in (events(C[i], *walk(C[i], rr)) if ok(C[i], *walk(C[i], rr)) else [])])
W["R3"] = rr
print(f"total weight: R {sum(W['R'].values()):.1f}, T* {sum(Tstar.values()):.1f}, U* {sum(rU.values()):.1f}, R3 {sum(rr.values()):.1f}")
res = {name: np.array([int(ok(C[i], *walk(C[i], W[name]))) for i in test]) for name in W}
for name in W: print(f"test both hops {name:5s} {res[name].mean():.3f}")
rng = np.random.default_rng(0)
def ci(d, lab):
    bt = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]
    print(f"{lab}: {d.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}] (n {len(d)})")
ci(res["Tstar"] - res["none"], "PRIMARY H-C2 both hops, T* − unweighted")
for a, b in (("Tstar", "R"), ("Ustar", "R"), ("Ustar", "none"), ("Tstar", "R3")): ci(res[a] - res[b], f"{a} − {b}")
for name in ("R", "Tstar", "Ustar", "R3"):
    d = res[name] - res["none"]; print(f"flips vs unweighted {name}: gained {(d > 0).sum()}, lost {(d < 0).sum()}")
assert abs(res["R"].mean() - 0.418) < 0.0015, "R must reproduce SR-BR's .418"
json.dump({k: v.tolist() for k, v in res.items()} | {"test": test}, open("out/srbc.json", "w"))
