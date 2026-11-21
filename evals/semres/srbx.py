"""SR-BX (REGISTERED-SRBX.md), bill (walk, entry) with james (train graph, rescue rule). REM-1341.
The cheap walk with a chosen entry, on MuSiQue train answerable 2-hop, each question's own pool of 20.
Entry factor (each picks e from the 20):
  e_cos    argmax cos(question, ·), bge-small                                    (SR-BW's entry)
  e_title  Jev over the 20 TITLES only, ENTRY_TASK; e = argmax p                 (knob-free, about naming-request size)
  e_pass   Jev over the 20 full passages, ENTRY_TASK                             (reference)
Step factor from e (each picks one other passage s; the walk's pair is {e, s}). SR-BW/SR-BT rules, unchanged:
  cosdoor   argmax door strength S[e, ·], ties by cos(q, ·)
  name      Jev names K from e's door keys R (NAME_TASK); argmax 1/(df_K−1)·[v shares K], ties by S[e, ·] then cos(q + e, ·)
  nt        name; if the set sharing K has 2+ members, Jev's PASS_TASK over that set only (wave 3)
  nt_rescue nt, but when no other passage shares K (or R is empty), s = argmax of Jev's PASS_TASK p over all 19 (wave 2)
  pass      Jev's PASS_TASK over the 19 others                                    (reference)
Walks scored: {e_cos, e_title} × {cosdoor, name, nt, nt_rescue, pass}, and e_pass × pass.
Jev: three dependent ask_many waves — (1) entry requests, (2) name + pass from each distinct entry, (3) twin requests.
Draw: train answerable 2-hop, np.random.default_rng(SEED).permutation, first 300 = registered; stage0 = positions 300–303.
    set -a; source ~/code/p8-subsystems/.env; set +a; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \
    uv run --with numpy --with sentence-transformers --with 'percolate-core==0.2.15' \
      python srbx.py MUSIQUE_TRAIN GRAPH_TRAIN SET MAX_USD [--look]"""
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
CACHE = Path.home() / ".cache" / "walklab" / "srbx-jev-cache.jsonl"
PRICE_IN = 0.042e-6
src, gpath, SET, MAX_USD = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]); LOOK = "--look" in sys.argv
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("2hop") and r["answerable"]]
perm = np.random.default_rng(SEED).permutation(len(qs))
pool = {"stage0": perm[300:304], "fresh": perm[:300]}[SET].tolist()
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
# wave 1: entries
ctxE = lambda x, t: {"question": x["q"], "task": t}
get = wave([(ctxE(x, ENTRY_TASK_T), [p["title"] for p in x["P"]]) for x in Q] + [(ctxE(x, ENTRY_TASK), x["T"]) for x in Q], "1 entry")
for x in Q:
    x["e"] = dict(e_cos=int(np.argmax(x["cq"])), e_title=int(np.argmax(get(ctxE(x, ENTRY_TASK_T), [p["title"] for p in x["P"]]))),
                  e_pass=int(np.argmax(get(ctxE(x, ENTRY_TASK), x["T"]))))
# wave 2: name + pass from each distinct entry
others = lambda x, e: [v for v in range(x["n"]) if v != e]
ctxR = lambda x, e, t: {"question": x["q"], "read": x["T"][e], "task": t}
R2 = []
for x in Q:
    for en in ("e_cos", "e_title", "e_pass"):
        e = x["e"][en]; R2.append((ctxR(x, e, PASS_TASK), [x["T"][v] for v in others(x, e)]))
        if en != "e_pass" and x["D"][e]: R2.append((ctxR(x, e, NAME_TASK), sorted(x["D"][e])))
get = wave(R2, "2 name+pass")
def from_entry(x, e):
    """Steps from entry e that need no wave 3; returns (steps, twin request or None)."""
    n, D, cq = x["n"], x["D"], x["cq"]; ot = others(x, e)
    S = np.array([sum(W(k) for k in D[e] & D[v]) if v != e else -1.0 for v in range(n)])
    qr = x["E"][1:] @ m.encode([QP + x["q"] + " " + x["T"][e]], normalize_embeddings=True)[0]
    pj = get(ctxR(x, e, PASS_TASK), [x["T"][v] for v in ot]); st = {}
    st["cosdoor"] = int(max(np.nonzero(S == S.max())[0], key=lambda u: cq[u])) if S.max() > 0 else int([v for v in np.argsort(-cq) if v != e][0])
    st["pass"] = ot[int(np.argmax(pj))]
    R = sorted(D[e]); share, K = [], None
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
# wave 3: twins
pend = []
for x in Q:
    x["st"] = {}
    for en in ("e_cos", "e_title"):
        st, twin, share, K = from_entry(x, x["e"][en]); x["st"][en] = (st, share, K)
        if twin: pend.append(twin)
    x["st"]["e_pass"] = (from_entry(x, x["e"]["e_pass"])[0], [], None)
get3 = wave(pend, "3 twins")
for x in Q:
    for en in ("e_cos", "e_title"):
        st, share, K = x["st"][en]
        if len(share) > 1:
            p = get3(ctxR(x, x["e"][en], PASS_TASK), [x["T"][v] for v in share]); st["nt"] = st["nt_rescue"] = share[int(np.argmax(p))]
print(f"spend this run ${spent[0]:.5f}")
# ---- scoring
STEPS = ("cosdoor", "name", "nt", "nt_rescue", "pass")
WALKS = [(en, s) for en in ("e_cos", "e_title") for s in STEPS] + [("e_pass", "pass")]
out = []
for x in Q:
    h1, h2 = x["h1"], x["h2"]; rec = dict(qi=x["qi"], entry={en: ("h1" if x["e"][en] == h1 else "h2" if x["e"][en] == h2 else "-") for en in x["e"]})
    for en, s in WALKS:
        e, v = x["e"][en], x["st"][en][0][s]; rec[f"{en}×{s}"] = dict(both=int({e, v} == {h1, h2}), ordered=int(e == h1 and v == h2), hop2=int(h2 in (e, v)))
    rec["share"] = {en: len(x["st"][en][1]) for en in ("e_cos", "e_title")}; out.append(rec)
nq = len(out)
for en in ("e_cos", "e_title", "e_pass"):
    print(f"{en:8s} entry: hop 1 {np.mean([o['entry'][en] == 'h1' for o in out]):.3f}, hop 2 {np.mean([o['entry'][en] == 'h2' for o in out]):.3f}")
for w in WALKS:
    k = f"{w[0]}×{w[1]}"; print(f"{k:20s} both {np.mean([o[k]['both'] for o in out]):.3f}  ordered {np.mean([o[k]['ordered'] for o in out]):.3f}  hop2 {np.mean([o[k]['hop2'] for o in out]):.3f}")
if SET == "fresh":
    rng = np.random.default_rng(0)
    def diff(a, b, met="both"):
        dd = np.array([o[a][met] - o[b][met] for o in out], float); bt = [dd[rng.integers(0, nq, nq)].mean() for _ in range(4000)]
        print(f"{met} {a} − {b}: {dd.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]")
    diff("e_title×nt_rescue", "e_cos×name")                         # primary
    for a, b in (("e_title×name", "e_cos×name"), ("e_cos×nt_rescue", "e_cos×nt"), ("e_cos×nt", "e_cos×name"),
                 ("e_title×nt_rescue", "e_pass×pass"), ("e_cos×name", "e_cos×cosdoor")): diff(a, b)
    dd = np.array([(o["entry"]["e_title"] == "h1") - (o["entry"]["e_cos"] == "h1") for o in out], float)
    bt = [dd[rng.integers(0, nq, nq)].mean() for _ in range(4000)]
    print(f"entry hop 1, e_title − e_cos: {dd.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]")
json.dump(dict(usd=spent[0], out=out), open(f"out/srbx-{SET}.json", "w"))
