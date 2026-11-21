"""SR-BW (REGISTERED-SRBW.md), bill. REM-1341: the cheap pipeline in a full 2-hop walk, without gold hop 1.
Per question, over its pool of 20 (MuSiQue answerable 2-hop):
  entry e   argmax cos(q, ·), bge-small (SR-E2's cosdoor entry)
  arms for the step from e (each picks one other passage s; the walk's pair is {e, s}):
    cos      the second passage by cos(q, ·)                                              (SR-E's baseline)
    cosdoor  argmax door strength S[e, ·] = Σ 1/(df−1) over shared door keys, ties by cos(q, ·)  (SR-E2's winner)
    name     Jev names one key K from e's door keys R (SR-BN's naming wording, unchanged); s = argmax 1/(df_K−1)·[v shares K],
             ties by S[e, ·], then qr = cos(q + e's text, ·)                      (SR-BN's lexical step, james's rule)
             empty R: s = cosdoor's step
    pass     Jev picks s among the 19 others (SR-J's passage task, unchanged), read = e's text   (reference, ~12x the tokens)
Metrics: both = {e, s} == {h1, h2};  ordered = e == h1 and s == h2;  hop2 = h2 in {e, s}.
Jev: every request of a SET in one ask_many wave. Draw: SR-KB's permutation (seed 1341 over 41–1252 minus SR-J-R's 40).
  SET stage0 = perm 0–3 (seen, SR-KB's first four)    fresh = perm 904–1171 (registered; never scored)
  --look: gold-blind, no Jev, no scoring
    set -a; source ~/code/p8-subsystems/.env; set +a; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \
    uv run --with numpy --with sentence-transformers --with 'percolate-core==0.2.15' python srbw.py MUSIQUE_DEV GRAPH_MQ SET MAX_USD"""
import asyncio, hashlib, json, re, sys
from collections import Counter
from pathlib import Path
import numpy as np

NAME_TASK = ("Each option is a name or phrase that appears in `read`. Which option is the thing that `question` needs "
             "`read` to identify, so that the next passage to read is about it?")   # SR-BN, unchanged
PASS_TASK = ("Each option is a passage not yet read. Having read `read`, would reading this option next give information "
             "needed to answer `question`?")   # SR-J, unchanged
CACHE = Path.home() / ".cache" / "walklab" / "srbw-jev-cache.jsonl"
PRICE_IN = 0.042e-6
src, gpath, SET, MAX_USD = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]); LOOK = "--look" in sys.argv
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
held = set(np.random.default_rng(20261121).permutation(np.arange(40, len(qs)))[:40].tolist())
perm = [i for i in np.random.default_rng(1341).permutation(np.arange(40, len(qs))) if i not in held]
pool = {"stage0": perm[0:4], "fresh": perm[904:]}[SET]
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
W = lambda k: 1 / (df[k] - 1)
cases = []
for qi in pool:
    r = qs[qi]; P = sorted(r["paragraphs"], key=lambda p: p["idx"]); n = len(P)
    T = [p["title"] + ". " + p["paragraph_text"] for p in P]; qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    D = [{k for k in keys[hid(p)] if 2 <= df[k] <= 100 and not set(k.split()) <= qt} for p in P]
    E = m.encode([QP + r["question"]] + T, normalize_embeddings=True); cq = E[1:] @ E[0]; o = np.argsort(-cq); e = int(o[0])
    S = np.array([sum(W(k) for k in D[e] & D[v]) if v != e else -1.0 for v in range(n)])
    qr = E[1:] @ m.encode([QP + r["question"] + " " + T[e]], normalize_embeddings=True)[0]
    others = [v for v in range(n) if v != e]
    cosdoor = max(np.nonzero(S == S.max())[0], key=lambda u: cq[u]) if S.max() > 0 else int(o[1])
    d = r["question_decomposition"]; ix = {p["idx"]: i for i, p in enumerate(P)}
    cases.append(dict(qi=int(qi), q=r["question"], read=T[e], e=e, R=sorted(D[e]), others=others, texts=[T[v] for v in others],
                      S=S.tolist(), qr=qr.tolist(), sh=[sorted(keys[hid(P[v])] & D[e]) for v in range(n)],
                      step=dict(cos=int(o[1]), cosdoor=int(cosdoor)),
                      h1=ix[d[0]["paragraph_support_idx"]], h2=ix[d[1]["paragraph_support_idx"]]))
sz = np.array([len(c["R"]) for c in cases])
print(f"SET={SET}: {len(cases)} questions; entry's door keys: median {np.median(sz):.0f}, empty {int((sz == 0).sum())}")
if LOOK:
    c = cases[0]; print(f"-- {c['q']}\n   entry: {c['read'][:80]}\n   R[:10]: {c['R'][:10]}"); sys.exit()
# ---- Jev: one wave through ask_many
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
        async with Jev() as jev:
            return await jev.ask_many([({"question": c["q"], "read": c["read"], "task": NAME_TASK if kind == "name" else PASS_TASK},
                                        {f"p{j}": Noul(t) for j, t in enumerate(o)}) for c, kind, o in miss])
    with open(CACHE, "a") as f:
        for x, res in zip(miss, asyncio.run(go())):
            p = [res[f"p{j}"].p for j in range(len(x[2]))]; cache[key(*x)] = p
            f.write(json.dumps({"k": key(*x), "p": p}) + "\n"); usd += res.input_tokens * PRICE_IN
print(f"spend this run ${usd:.5f}")
# ---- steps and scoring
ARMS = ("cos", "cosdoor", "name", "pass"); out = []
for c in cases:
    S, qr = np.array(c["S"]), np.array(c["qr"])
    pj = cache[key(c, "pass", c["texts"])]; c["step"]["pass"] = c["others"][int(np.argmax(pj))]
    if c["R"]:
        K = c["R"][int(np.argmax(cache[key(c, "name", c["R"])]))]
        sc = np.array([W(K) * (K in c["sh"][v]) for v in range(len(S))]) + 1e-3 * np.maximum(S, 0) / (S.max() + 1e-9) + 1e-6 * qr
        sc[c["e"]] = -np.inf; c["step"]["name"] = int(np.argmax(sc)); c["K"] = K
    else:
        c["step"]["name"] = c["step"]["cosdoor"]; c["K"] = None
    e, h1, h2 = c["e"], c["h1"], c["h2"]
    out.append(dict(qi=c["qi"], K=c["K"], entry_h1=int(e == h1), entry_h2=int(e == h2),
                    **{a: dict(both=int({e, c["step"][a]} == {h1, h2}), ordered=int(e == h1 and c["step"][a] == h2),
                               hop2=int(h2 in (e, c["step"][a]))) for a in ARMS}))
nq = len(out); print(f"entry is hop 1 {np.mean([o['entry_h1'] for o in out]):.3f}, hop 2 {np.mean([o['entry_h2'] for o in out]):.3f}")
for met in ("both", "ordered", "hop2"): print(f"{met:7s}: " + ", ".join(f"{a} {np.mean([o[a][met] for o in out]):.3f}" for a in ARMS))
for lab, f in (("entry = hop 1", "entry_h1"), ("entry = hop 2", "entry_h2")):
    sub = [o for o in out if o[f]]; print(f"  given {lab} (n {len(sub)}): both " + ", ".join(f"{a} {np.mean([o[a]['both'] for o in sub]):.3f}" for a in ARMS))
if SET == "stage0":
    for c in cases: print(f"-- {c['q']}\n   entry {'h1' if c['e'] == c['h1'] else 'h2' if c['e'] == c['h2'] else 'neither'}; Jev names {c['K']!r}")
else:
    rng = np.random.default_rng(0)
    for met in ("both", "hop2"):
        for a, b in (("name", "cosdoor"), ("name", "pass"), ("pass", "cosdoor"), ("cosdoor", "cos")):
            dd = np.array([o[a][met] - o[b][met] for o in out], float); bt = [dd[rng.integers(0, nq, nq)].mean() for _ in range(4000)]
            print(f"{met} {a} − {b}: {dd.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]")
json.dump(dict(usd=usd, out=out), open(f"out/srbw-{SET}.json", "w"))
