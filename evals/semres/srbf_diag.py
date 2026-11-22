"""SR-BF (REGISTERED-SRBF.md), bill. One entry or two, judged on the answer (Sirsh 17:07Z): A-last (the returned set
holds the gold last-hop passage) and AC (Jev, reading the set, chooses a sentence holding the gold answer; srac.py's
request). Walk: Jev's 20-passage entry request, then the cheap step (nt_rescue), as SR-BE. ONE returns {e1, s1};
TWO also walks the entry request's runner-up e2 one step and returns {e1, s1, e2, s2} (deduplicated, in that order).
Draw: 2-hop answerable, seed 1341 permutation positions 608 onward, minus the 2-hop questions SR-BS and SR-AC used;
fresh = the first 150, stage0 = the next 4. Built from srbe.py (SR-BX's walk code, unchanged).
    set -a; source ~/code/p8-subsystems/.env; set +a; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \
    uv run --with numpy --with sentence-transformers --with 'percolate-core==0.2.15' python srbf.py TRAIN_CORPUS GRAPH_TRAIN SET MAX_USD [--dry]"""
import asyncio, hashlib, json, re, sys
from collections import Counter
from pathlib import Path
import numpy as np

ENTRY_TASK = "Each option is a passage. Which passage should be read first to answer `question`?"
ENTRY_TASK_T = "Each option is the title of a passage. Which passage should be read first to answer `question`?"
NAME_TASK = ("Each option is a name or phrase that appears in `read`. Which option is the thing that `question` needs "
             "`read` to identify, so that the next passage to read is about it?")   # SR-BN, unchanged
PASS_TASK = ("Each option is a passage not yet read. Having read `read`, would reading this option next give information "
             "needed to answer `question`?")   # SR-J, unchanged
SEED = 1341
CACHE = Path.home() / ".cache" / "walklab" / "srbf-jev-cache.jsonl"
PRICE_IN = 0.042e-6
src, gpath, SET, MAX_USD = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]); LOOK = "--look" in sys.argv; DRY = "--dry" in sys.argv
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
perm = np.random.default_rng(SEED).permutation(len(qs))
allq = [r for r in map(json.loads, open(src)) if r["answerable"]]
by = {t: [r for r in allq if r["id"].split("__")[0] == t] for t in ("2hop", "3hop1", "4hop1")}
used = {by["2hop"][i]["id"] for i in perm[:608]}
for t in ("3hop1", "4hop1"):
    used |= {by[t][i]["id"] for i in np.random.default_rng(1344).permutation(len(by[t]))[:102]}
for sd, k in ((1345, 82), (1346, 52)):   # SR-BS, then SR-AC, each drawn from what was unused before it
    for t in ("2hop", "3hop1", "4hop1"):
        fr = [r for r in by[t] if r["id"] not in used]; used |= {fr[i]["id"] for i in np.random.default_rng(sd).permutation(len(fr))[:k]}
rest = [int(i) for i in perm[608:] if qs[i]["id"] not in used]
pool = {"stage0": rest[150:154], "fresh": rest[:150]}[SET]
assert not {qs[i]["id"] for i in pool} & used
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
W = lambda k: 1 / (df[k] - 1)
Q = []
for qi in pool:
    r = qs[qi]; P = sorted(r["paragraphs"], key=lambda p: p["idx"]); n = len(P)
    T = [p["title"] + ". " + p["paragraph_text"] for p in P]; qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    missing = sum(hid(p) not in keys for p in P)
    D = [{k for k in keys.get(hid(p), ()) if 2 <= df[k] <= 100 and not set(k.split()) <= qt} for p in P]
    E = m.encode([QP + r["question"]] + T, normalize_embeddings=True); cq = E[1:] @ E[0]
    d = r["question_decomposition"]; ix = {p["idx"]: i for i, p in enumerate(P)}
    Q.append(dict(qi=int(qi), q=r["question"], P=P, T=T, D=D, E=E, cq=cq, n=n, missing=missing,
                  h1=ix[d[0]["paragraph_support_idx"]], h2=ix[d[1]["paragraph_support_idx"]]))
print(f"SET={SET}: {len(Q)} questions; passages missing from the graph {sum(x['missing'] for x in Q)}; "
      f"cos entry's door keys median {np.median([len(x['D'][int(np.argmax(x['cq']))]) for x in Q]):.0f}")
dup = sum(len({p["title"] for p in x["P"]}) < x["n"] for x in Q)
print(f"pools with a repeated title: {dup} of {len(Q)} (e_title: Jev picks a title; among passages with that title, the one nearest the question by cos)")
if LOOK:
    x = Q[0]; print(f"-- {x['q']}\n   titles: {[p['title'] for p in x['P']][:8]}"); sys.exit()
# ---- Jev plumbing: cached, one ask_many per wave
cache = {}
if CACHE.exists():
    for l in open(CACHE): y = json.loads(l); cache[y["k"]] = y["p"]
ck = lambda ctx, opts: hashlib.sha256(json.dumps([ctx, opts]).encode()).hexdigest()
spent = [0.0]
def wave(reqs, label):
    reqs = list({ck(c, o): (c, o) for c, o in reqs}.values()); miss = [(c, o) for c, o in reqs if ck(c, o) not in cache]
    if miss:
        est = sum(len(json.dumps(c)) / 4 + len(" ".join(o)) / 4 + 200 for c, o in miss) * PRICE_IN
        print(f"wave {label}: {len(miss)} requests, estimated ${est:.4f} (spent so far ${spent[0]:.4f}, cap ${MAX_USD})", flush=True)
        if spent[0] + est > MAX_USD: sys.exit("estimate over cap")
        from percolate_core.decide import Jev, Noul
        async def go():
            async with Jev() as jev:
                return await jev.ask_many([(c, {f"p{j}": Noul(t) for j, t in enumerate(o)}) for c, o in miss])
        with open(CACHE, "a") as f:
            for (c, o), res in zip(miss, asyncio.run(go())):
                p = [res[f"p{j}"].p for j in range(len(o))]; cache[ck(c, o)] = p
                f.write(json.dumps({"k": ck(c, o), "p": p}) + "\n"); spent[0] += res.input_tokens * PRICE_IN
    return lambda c, o: cache[ck(c, o)]

if DRY:   # price with random scores: fill misses before any call
    _wave = wave
    def wave(reqs, label):
        rng = np.random.default_rng(0)
        for c, o in reqs:
            if ck(c, o) not in cache:
                est = (len(json.dumps(c)) / 4 + len(" ".join(o)) / 4 + 200) * PRICE_IN; spent[0] += est; cache[ck(c, o)] = rng.random(len(o)).tolist()
        print(f"DRY wave {label}: {len(reqs)} requests; cumulative estimate ${spent[0]:.4f}")
        return lambda c, o: cache[ck(c, o)]
ctxE = lambda x, t: {"question": x["q"], "task": t}
get = wave([(ctxE(x, ENTRY_TASK), x["T"]) for x in Q], "1 entry")
for x in Q:
    order = list(np.argsort(-np.array(get(ctxE(x, ENTRY_TASK), x["T"])), kind="stable"))
    x["e"] = dict(e1=int(order[0]), e2=int(order[1]))
others = lambda x, e: [v for v in range(x["n"]) if v != e]
ctxR = lambda x, e, t: {"question": x["q"], "read": x["T"][e], "task": t}
R2 = []
for x in Q:
    for en in ("e1", "e2"):
        e = x["e"][en]; R2.append((ctxR(x, e, PASS_TASK), [x["T"][v] for v in others(x, e)]))
        if x["D"][e]: R2.append((ctxR(x, e, NAME_TASK), sorted(x["D"][e])))
get = wave(R2, "2 name+pass")
def from_entry(x, e, names=True):
    """Steps from entry e that need no wave 3; returns (steps, twin request or None). names=False: pass only (e_pass)."""
    n, D, cq = x["n"], x["D"], x["cq"]; ot = others(x, e)
    S = np.array([sum(W(k) for k in D[e] & D[v]) if v != e else -1.0 for v in range(n)])
    qr = x["E"][1:] @ m.encode([QP + x["q"] + " " + x["T"][e]], normalize_embeddings=True)[0]
    pj = get(ctxR(x, e, PASS_TASK), [x["T"][v] for v in ot]); st = {}
    st["cosdoor"] = int(max(np.nonzero(S == S.max())[0], key=lambda u: cq[u])) if S.max() > 0 else int([v for v in np.argsort(-cq) if v != e][0])
    st["pass"] = ot[int(np.argmax(pj))]
    R = sorted(D[e]) if names else []; share, K = [], None
    if R:
        K = R[int(np.argmax(get(ctxR(x, e, NAME_TASK), R)))]
        sh = [keys.get(hid(x["P"][v]), set()) for v in range(n)]
        sc = np.array([W(K) * (K in sh[v]) for v in range(n)]) + 1e-3 * np.maximum(S, 0) / (S.max() + 1e-9) + 1e-6 * qr
        sc[e] = -np.inf; st["name"] = int(np.argmax(sc)); share = [v for v in ot if K in sh[v]]
    else:
        st["name"] = st["cosdoor"]
    st["nt"] = st["name"] if len(share) != 1 else share[0]
    st["nt_rescue"] = st["nt"] if share else st["pass"]
    twin = (ctxR(x, e, PASS_TASK), [x["T"][v] for v in share]) if len(share) > 1 else None
    return st, twin, share, K
pend = []
for x in Q:
    x["st"] = {}
    for en in ("e1", "e2"):
        st, twin, share, K = from_entry(x, x["e"][en]); x["st"][en] = (st, share, K)
        if twin: pend.append(twin)
get3 = wave(pend, "3 twins")
for x in Q:
    for en in ("e1", "e2"):
        st, share, K = x["st"][en]
        if len(share) > 1:
            p = get3(ctxR(x, x["e"][en], PASS_TASK), [x["T"][v] for v in share]); st["nt"] = st["nt_rescue"] = share[int(np.argmax(p))]
# returned sets
for x in Q:
    s1 = x["st"]["e1"][0]["nt_rescue"]; s2 = x["st"]["e2"][0]["nt_rescue"]
    two = []
    for v in (x["e"]["e1"], s1, x["e"]["e2"], s2):
        if v not in two: two.append(v)
    x["sets"] = {"ONE": [x["e"]["e1"], s1], "TWO": two}
# AC: srac.py's request, unchanged
SENT_TASK = "Each option is a sentence from `reads`. Which sentence states the answer to `question`?"
norm = lambda s: " ".join(re.findall(r"[a-z0-9]+", s.lower()))
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
sents = lambda p: [f"{p['title']}: {s}" for s in SPLIT.split(p["paragraph_text"].strip()) if s.strip()]
ctxA = lambda x, vs: {"question": x["q"], "reads": [f"{x['P'][v]['title']}. {x['P'][v]['paragraph_text']}" for v in vs], "task": SENT_TASK}
optA = lambda x, vs: [t for v in vs for t in sents(x["P"][v])]
get4 = wave([(ctxA(x, x["sets"][a]), optA(x, x["sets"][a])) for x in Q for a in ("ONE", "TWO")], "4 reader")
print(f"spend this run ${spent[0]:.5f}" + (" (DRY estimate)" if DRY else ""))
golds = {x["qi"]: {norm(a) for a in [qs[x["qi"]]["answer"]] + qs[x["qi"]].get("answer_aliases", []) if norm(a)} for x in Q}
res = {a: dict(alast=[], ac=[], size=[]) for a in ("ONE", "TWO")}
for x in Q:
    for a in ("ONE", "TWO"):
        vs = x["sets"][a]; o = optA(x, vs); j = int(np.argmax(get4(ctxA(x, vs), o)))
        res[a]["alast"].append(int(x["h2"] in vs)); res[a]["ac"].append(int(any(g in norm(o[j]) for g in golds[x["qi"]])))
        res[a]["size"].append(len(vs))
rng = np.random.default_rng(0)
def ci(d):
    d = np.asarray(d, float); bt = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]
    return f"{d.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]"
for a in ("ONE", "TWO"):
    print(f"{a}: A-last {np.mean(res[a]['alast']):.3f}  AC {np.mean(res[a]['ac']):.3f}  returned passages {np.mean(res[a]['size']):.2f}")
d = lambda m: np.array(res["TWO"][m]) - np.array(res["ONE"][m])
print(f"PRIMARY H-F: AC(TWO) − AC(ONE): {ci(d('ac'))}")
print(f"A-last(TWO) − A-last(ONE): {ci(d('alast'))}")
print(f"e1 on a hop {np.mean([x['e']['e1'] in (x['h1'], x['h2']) for x in Q]):.3f}; e2 on a hop when e1 is off both {sum(x['e']['e2'] in (x['h1'], x['h2']) for x in Q if x['e']['e1'] not in (x['h1'], x['h2']))} of {sum(x['e']['e1'] not in (x['h1'], x['h2']) for x in Q)}")
ga = [(a, b) for a, b in zip(res["TWO"]["ac"], res["ONE"]["ac"])]
print(f"AC flips TWO vs ONE: gained {sum(1 for a, b in ga if a > b)}, lost {sum(1 for a, b in ga if a < b)}")
if not DRY: json.dump({a: res[a] for a in res} | {"usd": spent[0], "ids": [qs[x["qi"]]["id"] for x in Q]}, open(f"out/srbf-{SET}.json", "w"))
# ---- diagnostic ($0, from cache): AC by what the ONE set contains
from collections import defaultdict
cat = defaultdict(list); ex = []
for x, ac in zip(Q, res["ONE"]["ac"]):
    vs = set(x["sets"]["ONE"]); h = {x["h1"], x["h2"]}
    k = "both hops" if vs == h else "answer passage + other" if x["h2"] in vs else "hop 1 + other" if x["h1"] in vs else "neither"
    cat[k].append(ac)
    if k == "both hops" and not ac and len(ex) < 6:
        o = optA(x, x["sets"]["ONE"]); j = int(np.argmax(get4(ctxA(x, x["sets"]["ONE"]), o)))
        ex.append((qs[x["qi"]]["question"][:100], qs[x["qi"]]["answer"], o[j][:160]))
for k, v in cat.items(): print(f"ONE set = {k:24s} n {len(v):3d}  AC {np.mean(v):.3f}")
for e in ex: print("  ", e)
