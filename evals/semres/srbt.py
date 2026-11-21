"""SR-BT (REGISTERED-SRBT.md), james: beyond the name. Given gold hop 1 as read, after Jev names the bridge K from the
read's door keys (SR-BN's request, unchanged), does a second short Jev request over only the options sharing K (the
named set S, when |S| > 1) recover what Jev's full passage choice gets from the question's second relation?
  wave 1 (one ask_many): SR-BN's naming request and SR-J's passage request (jev_pass, the reference), per question.
  wave 2 (one ask_many): SR-J's passage task over S's passages only, for questions with |S| > 1.
Arms (top-1 hop 2):
  k        SR-K's sum, ties by qr                       jev      SR-BN's step: the named key, ties by k then qr
  nt       |S| = 0 -> k;  |S| = 1 -> that option;  |S| > 1 -> argmax of wave 2's p over S
  nt_cut   as nt, but with wave 1's pj restricted to S (the $0 approximation used in pricing)
  jev_pass argmax of wave 1's pj over all 19          ceiling_k  gold bridge keys, ties by k then qr (gold, labelled)
SET: stage0 = perm 600-603 (SR-BN's set, seen; a smoke test), bw = perm 904-1171 (shared with SR-BW, registered).
    source ~/code/p8-subsystems/.env; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \\
    uv run --with sentence-transformers --with numpy --with 'percolate-core==0.2.15' python srbt.py MUSIQUE_DEV GRAPH_MQ SET MAX_USD"""
import asyncio, hashlib, json, re, sys
from collections import Counter
from pathlib import Path
import numpy as np

NAME_TASK = ("Each option is a name or phrase that appears in `read`. Which option is the thing that `question` needs "
             "`read` to identify, so that the next passage to read is about it?")   # SR-BN's, unchanged
PASS_TASK = ("Each option is a passage not yet read. Having read `read`, would reading this option next give information "
             "needed to answer `question`?")   # SR-J's, unchanged
CACHE = Path.home() / ".cache" / "walklab" / "srbn-jev-cache.jsonl"   # shared with SR-BN: same key, same request
PRICE_IN = 0.042e-6
src, gpath, SET, MAX_USD = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
held = set(np.random.default_rng(20261121).permutation(np.arange(40, len(qs)))[:40].tolist())
perm = [i for i in np.random.default_rng(1341).permutation(np.arange(40, len(qs))) if i not in held]
pool = {"stage0": perm[600:604], "stage0t": perm[604:900], "bw": perm[904:]}[SET]   # stage0t: amendment 2, see below
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
wd = lambda s: set(re.findall(r"[a-z0-9]+", s.lower())); W = lambda k: 1 / (df[k] - 1)
cases = []
for qi in pool:
    r = qs[qi]; d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
    P = {p["idx"]: p for p in r["paragraphs"]}; T = {i: P[i]["title"] + ". " + P[i]["paragraph_text"] for i in P}
    opts = sorted(i for i in P if i != h1); qt = wd(r["question"])
    R = sorted(k for k in keys[hid(P[h1])] if 2 <= df[k] <= 100 and not set(k.split()) <= qt)
    O = m.encode([T[i] for i in opts], normalize_embeddings=True); eqr = m.encode([QP + r["question"] + " " + T[h1]], normalize_embeddings=True)[0]
    cases.append(dict(qi=int(qi), q=r["question"], read=T[h1], R=R, texts=[T[i] for i in opts], h=opts.index(h2), qr=(O @ eqr).tolist(),
                      sh=[sorted(keys[hid(P[i])] & set(R)) for i in opts], B=sorted(k for k in R if set(k.split()) <= wd(d[0]["answer"]))))
cache = {}
if CACHE.exists():
    for l in open(CACHE): x = json.loads(l); cache[x["k"]] = x["p"]
key = lambda c, kind, o: hashlib.sha256(json.dumps([c["q"], c["read"], o, NAME_TASK if kind == "name" else PASS_TASK]).encode()).hexdigest()
usd = 0.0

def wave(reqs, label):
    global usd
    miss = [x for x in reqs if key(*x) not in cache]
    if not miss: print(f"{label}: all {len(reqs)} cached"); return
    est = sum(len(" ".join(o) + c["q"] + c["read"]) / 4 + 200 for c, _, o in miss) * PRICE_IN
    print(f"{label}: {len(miss)} live requests, estimated ${est:.4f} (spent so far ${usd:.4f}, cap ${MAX_USD})", flush=True)
    if usd + est > MAX_USD: sys.exit("estimate over cap")
    from percolate_core.decide import Jev, Noul
    async def go():
        async with Jev() as jev:   # the whole wave through ask_many, all in flight together
            return await jev.ask_many([({"question": c["q"], "read": c["read"], "task": NAME_TASK if kind == "name" else PASS_TASK},
                                        {f"p{j}": Noul(t) for j, t in enumerate(o)}) for c, kind, o in miss])
    with open(CACHE, "a") as f:
        for x, res in zip(miss, asyncio.run(go())):
            p = [res[f"p{j}"].p for j in range(len(x[2]))]; cache[key(*x)] = p
            f.write(json.dumps({"k": key(*x), "p": p}) + "\n"); usd += res.input_tokens * PRICE_IN

if SET == "stage0t":   # amendment 2: the first 4 SR-BN questions (seen, all wave-1 requests cached) whose named set has 2+ members
    for c in cases:
        if not c["R"] or key(c, "name", c["R"]) not in cache: continue
        K = c["R"][int(np.argmax(cache[key(c, "name", c["R"])]))]; c["n_S"] = sum(K in x for x in c["sh"])
    cases = [c for c in cases if c.get("n_S", 0) > 1][:4]
wave([(c, "name", c["R"]) for c in cases if c["R"]] + [(c, "pass", c["texts"]) for c in cases], "wave 1")
for c in cases:
    c["pj"] = cache[key(c, "pass", c["texts"])]
    c["K"] = c["R"][int(np.argmax(cache[key(c, "name", c["R"])]))] if c["R"] else None
    c["S"] = [i for i, x in enumerate(c["sh"]) if c["K"] in x]
    c["St"] = [c["texts"][i] for i in c["S"]]
wave([(c, "pass", c["St"]) for c in cases if len(c["S"]) > 1], "wave 2")
print(f"spend this run ${usd:.5f}")

def rank(s, h): s = np.asarray(s, float); return int(1 + (s > s[h]).sum())
def pick_rank(i, h, fallback): return (1 if i == h else 2) if i is not None else fallback   # a single pick: hit or miss
A = ("k", "jev", "nt", "nt_cut", "jev_pass", "ceiling_k"); res = {a: [] for a in A}; read2 = 0; out = []
for c in cases:
    h, qr = c["h"], np.array(c["qr"]); ksum = np.array([sum(map(W, x)) for x in c["sh"]])
    tk = 1e-3 * ksum / (ksum.max() + 1e-9) + 1e-6 * qr; B = set(c["B"]); K, S = c["K"], c["S"]
    rk = rank(ksum + 1e-6 * qr, h)
    res["k"].append(rk); res["jev_pass"].append(rank(c["pj"], h))
    res["jev"].append(rank(np.array([W(K) if K in x else 0 for x in c["sh"]]) + tk, h) if K else rank(tk, h))
    res["ceiling_k"].append(rank(np.array([sum(W(k) for k in x if k in B) for x in c["sh"]]) + tk, h))
    if len(S) == 0: res["nt"].append(rk); res["nt_cut"].append(rk)
    elif len(S) == 1: res["nt"].append(pick_rank(S[0], h, rk)); res["nt_cut"].append(pick_rank(S[0], h, rk))
    else:
        p2 = cache[key(c, "pass", c["St"])]; read2 += len(S)
        res["nt"].append(pick_rank(S[int(np.argmax(p2))], h, rk)); res["nt_cut"].append(pick_rank(max(S, key=lambda i: c["pj"][i]), h, rk))
    out.append(dict(qi=c["qi"], K=K, S=len(S), named_bridge=K in B, **{a: res[a][-1] for a in A}))
n = len(cases); print(f"SET={SET}: n {n}; Jev names a bridge key {np.mean([o['named_bridge'] for o in out]):.3f}; "
                      f"|S| = 0 / 1 / >1: {sum(o['S'] == 0 for o in out)} / {sum(o['S'] == 1 for o in out)} / {sum(o['S'] > 1 for o in out)}")
print(f"wave-2 passages per question {read2 / n:.2f} (against 19 in jev_pass)")
for a in A: v = np.array(res[a]); print(f"{a:9s} top-1 {np.mean(v == 1):.3f}")
if SET.startswith("stage0"):
    for c, o in zip(cases, out): print(f"-- {c['q']}\n   K {o['K']!r}; |S| {o['S']}; nt {o['nt']}, jev_pass {o['jev_pass']}")
    sys.exit()
rng = np.random.default_rng(0)
for a, b in (("nt", "jev"), ("nt", "jev_pass"), ("nt", "k"), ("nt", "nt_cut")):
    dd = np.array([(x == 1) - (y == 1) for x, y in zip(res[a], res[b])], float)
    bt = [dd[rng.integers(0, n, n)].mean() for _ in range(4000)]
    print(f"top-1 {a} − {b}: {dd.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]")
tw = [i for i, o in enumerate(out) if o["S"] > 1]   # amendment 1: nt and jev differ only where |S| > 1
for a, b in (("nt", "jev"), ("nt", "jev_pass")):
    dd = np.array([(res[a][i] == 1) - (res[b][i] == 1) for i in tw], float)
    bt = [dd[rng.integers(0, len(tw), len(tw))].mean() for _ in range(4000)]
    print(f"within |S| > 1 (n {len(tw)}): {a} − {b}: {dd.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]; "
          f"{a} {np.mean([res[a][i] == 1 for i in tw]):.3f}, {b} {np.mean([res[b][i] == 1 for i in tw]):.3f}")
json.dump(dict(out=out, usd=usd), open(f"out/srbt-{SET}.json", "w"))
