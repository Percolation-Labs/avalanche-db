"""SR-BN namer half (REGISTERED-SRBN.md), james. REM-1341: can a decision name the bridge (hop 1's answer) from the read
passage's door keys, so that the walk steps through one identity instead of a sum of rare keys?
Per question, with gold hop 1 as read and R = SR-KB's bundle (the read's door keys, 2 <= df <= 100, not inside the question):
  Jev namer   one request: options = the keys in R (each a short phrase from the read). It picks argmax p.
  Jev passage one request, SR-J's task over the 19 passages, as a same-draw reference for Jev's own hop-2 top-1.
  Both requests for every question go out in one wave through Jev.ask_many, all in flight together.
  $0 namer controls: cosq (bge cos(question, key)), cbq (a-ColBERT MaxSim(question, key)), rare (max 1/(df-1)).
Hop-2 arms (lexical, mine): via a named key K, score(v) = 1/(df_K - 1) if v shares K; ties by k (SR-K's sum), then qr.
B (gold, scoring only): keys in R whose words are all in hop 1's answer.
Writes out/srbn-names-SET.json: {qi: {"R": [...], "jev": key, "cosq": key, "cbq": key, "rare": key, "p": [...], "pj": [...]}}
SET: stage0 = perm 900-903 (outside the registered set), fresh = perm 600-899 (registered).
    source ~/code/p8-subsystems/.env; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \\
    uv run --with pylate --with numpy --with 'percolate-core==0.2.15' python srbn_name.py MUSIQUE_DEV GRAPH_MQ SET MAX_USD"""
import asyncio, hashlib, json, re, sys
from collections import Counter
from pathlib import Path
import numpy as np

NAME_TASK = ("Each option is a name or phrase that appears in `read`. Which option is the thing that `question` needs "
             "`read` to identify, so that the next passage to read is about it?")
PASS_TASK = ("Each option is a passage not yet read. Having read `read`, would reading this option next give information "
             "needed to answer `question`?")   # SR-J's task, unchanged
CACHE = Path.home() / ".cache" / "walklab" / "srbn-jev-cache.jsonl"
PRICE_IN = 0.042e-6
src, gpath, SET, MAX_USD = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
held = set(np.random.default_rng(20261121).permutation(np.arange(40, len(qs)))[:40].tolist())
perm = [i for i in np.random.default_rng(1341).permutation(np.arange(40, len(qs))) if i not in held]
pool = {"stage0": perm[900:904], "fresh": perm[600:900]}[SET]
from sentence_transformers import SentenceTransformer
from pylate import models
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
cb = models.ColBERT("answerdotai/answerai-colbert-small-v1", device="cpu")
wd = lambda s: set(re.findall(r"[a-z0-9]+", s.lower())); W = lambda k: 1 / (df[k] - 1)
cases = []
for qi in pool:
    r = qs[qi]; d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p for p in r["paragraphs"]}; T = {i: P[i]["title"] + ". " + P[i]["paragraph_text"] for i in P}
    opts = sorted(i for i in P if i != h1); qt = wd(r["question"])
    R = sorted(k for k in keys[hid(P[h1])] if 2 <= df[k] <= 100 and not set(k.split()) <= qt)
    O = m.encode([T[i] for i in opts], normalize_embeddings=True); eqr = m.encode([QP + r["question"] + " " + T[h1]], normalize_embeddings=True)[0]
    c = dict(qi=int(qi), q=r["question"], read=T[h1], R=R, texts=[T[i] for i in opts], h=opts.index(h2), qr=(O @ eqr).tolist(),
             sh=[sorted(keys[hid(P[i])] & set(R)) for i in opts], B=sorted(k for k in R if set(k.split()) <= wd(d[0]["answer"])))
    if R:
        eq = m.encode([QP + r["question"]], normalize_embeddings=True)[0]; EK = m.encode(R, normalize_embeddings=True)
        Q = np.asarray(cb.encode([r["question"]], is_query=True)[0]); KT = [np.asarray(x) for x in cb.encode(R, is_query=False)]
        c.update(cosq=R[int(np.argmax(EK @ eq))], cbq=R[int(np.argmax([(Q @ kt.T).max(0).mean() for kt in KT]))],
                 rare=R[int(np.argmax([W(k) for k in R]))])
    cases.append(c)
# ---- Jev: one wave, two requests per question
cache = {}
if CACHE.exists():
    for l in open(CACHE): x = json.loads(l); cache[x["k"]] = x["p"]
reqs = [(c, "name", c["R"]) for c in cases if c["R"]] + [(c, "pass", c["texts"]) for c in cases]
key = lambda c, kind, o: hashlib.sha256(json.dumps([c["q"], c["read"], o, NAME_TASK if kind == "name" else PASS_TASK]).encode()).hexdigest()
miss = [x for x in reqs if key(*x) not in cache]; usd = 0.0
if miss:
    est = sum(len(" ".join(o) + c["q"] + c["read"]) / 4 + 200 for c, _, o in miss) * PRICE_IN
    print(f"live: {len(miss)} requests, estimated ${est:.4f} (cap ${MAX_USD})", flush=True)
    if est > MAX_USD: sys.exit("estimate over cap")
    from percolate_core.decide import Jev, Noul
    async def go():
        async with Jev() as jev:   # the whole wave through ask_many, all in flight together
            return await jev.ask_many([({"question": c["q"], "read": c["read"], "task": NAME_TASK if kind == "name" else PASS_TASK},
                                        {f"p{j}": Noul(t) for j, t in enumerate(o)}) for c, kind, o in miss])
    with open(CACHE, "a") as f:
        for x, res in zip(miss, asyncio.run(go())):
            p = [res[f"p{j}"].p for j in range(len(x[2]))]; cache[key(*x)] = p
            f.write(json.dumps({"k": key(*x), "p": p}) + "\n"); usd += res.input_tokens * PRICE_IN
print(f"spend this run ${usd:.5f}")
names = {}
for c in cases:
    pj = cache[key(c, "pass", c["texts"])]; c["pj"] = pj
    if c["R"]: c["p"] = cache[key(c, "name", c["R"])]; c["jev"] = c["R"][int(np.argmax(c["p"]))]
    names[c["qi"]] = {k: c.get(k) for k in ("R", "jev", "cosq", "cbq", "rare", "p", "pj")}
json.dump(names, open(f"out/srbn-names-{SET}.json", "w"))
# ---- scoring
def rank(s, h): s = np.asarray(s); return int(1 + (s > s[h]).sum())
NM = ("jev", "cosq", "cbq", "rare"); res = {a: [] for a in ("k", "jev_pass", "ceiling_k") + NM}; acc = Counter()
for c in cases:
    h, qr = c["h"], np.array(c["qr"]); ksum = np.array([sum(map(W, x)) for x in c["sh"]])
    tk = 1e-3 * ksum / (ksum.max() + 1e-9) + 1e-6 * qr; B = set(c["B"])
    res["k"].append(rank(ksum + 1e-6 * qr, h)); res["jev_pass"].append(rank(c["pj"], h))
    res["ceiling_k"].append(rank(np.array([sum(W(k) for k in x if k in B) for x in c["sh"]]) + tk, h))
    for a in NM:
        K = c.get(a); acc[a] += K in B
        res[a].append(rank(np.array([W(K) if K in x else 0 for x in c["sh"]]) + tk, h) if K else rank(tk, h))
n = len(cases); print(f"SET={SET}: n {n}; bridge among door keys {np.mean([bool(c['B']) for c in cases]):.3f}")
for a in NM: print(f"namer {a:5s} names a bridge key {acc[a] / n:.3f}")
for a, v in res.items(): v = np.array(v); print(f"hop-2 {a:9s} top-1 {np.mean(v == 1):.3f}  top-3 {np.mean(v <= 3):.3f}  MRR {np.mean(1 / v):.3f}")
if SET == "stage0":
    for c in cases: print(f"-- {c['q']}\n   |R| {len(c['R'])}; Jev names {c.get('jev')!r}; gold bridge keys {c['B']}")
    sys.exit()
rng = np.random.default_rng(0)
for a, b in (("jev", "k"), ("jev", "cosq"), ("jev", "jev_pass"), ("ceiling_k", "jev")):
    dd = np.array([(x == 1) - (y == 1) for x, y in zip(res[a], res[b])], float)
    bt = [dd[rng.integers(0, n, n)].mean() for _ in range(4000)]
    print(f"top-1 {a} − {b}: {dd.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]")
dd = np.array([(c.get("jev") in set(c["B"])) - (c.get("cosq") in set(c["B"])) for c in cases], float)
bt = [dd[rng.integers(0, n, n)].mean() for _ in range(4000)]
print(f"naming jev − cosq: {dd.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]")
json.dump(dict(ranks=res, usd=usd), open(f"out/srbn-name-{SET}.json", "w"))
