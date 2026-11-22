"""SR-BH (REGISTERED-SRBH.md), james: the cheap walk past 2 hops, on MuSiQue train answerable CHAINS (3hop1, 4hop1),
each question's own pool of 20. Follows NOTE-HOPS-LOOK.md and SR-BE (bill's entry, srbe.py's rules and tasks unchanged).
Entry: e_pass, Jev's 20-passage entry request (ENTRY_TASK), argmax. Both walks start there.
Then H - 1 steps, H = the question's hop count (an ORACLE a real walk doesn't have; bill's note 1). At each step the
`read` is the LAST passage read (chains depend only on it; the look), and the options are the passages not yet read.
  cheap  nt_rescue: Jev names K from the last read's door keys (NAME_TASK); the unread passages sharing K form S.
         |S| = 1: step to it. |S| >= 2: Jev's PASS_TASK over S. |S| = 0 or no keys: PASS_TASK over all unread (rescue).
  pass   Jev's PASS_TASK over all unread, argmax.
Door keys: the train graph, 2 <= df <= 100, not contained in the question (SR-BX's filter).
Jev: one ask_many per wave; per step, wave a = name (cheap) + pass (pass walk), wave b = twins and rescues (cheap).
Draw: SEED 1344, a permutation of each type's answerable questions; 'fresh' = the first 100 3hop1 and first 100
4hop1; 'stage0' = positions 100-101 of each.
    set -a; source ~/code/p8-subsystems/.env; set +a; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \
    uv run --with numpy --with 'percolate-core==0.2.15' python srbh.py MUSIQUE_TRAIN GRAPH_TRAIN SET MAX_USD [--dry] [--spare] [--nocap]"""
import asyncio, hashlib, json, re, sys
from collections import Counter
from pathlib import Path
import numpy as np

ENTRY_TASK = "Each option is a passage. Which passage should be read first to answer `question`?"
NAME_TASK = ("Each option is a name or phrase that appears in `read`. Which option is the thing that `question` needs "
             "`read` to identify, so that the next passage to read is about it?")   # SR-BN, unchanged
PASS_TASK = ("Each option is a passage not yet read. Having read `read`, would reading this option next give information "
             "needed to answer `question`?")   # SR-J, unchanged
SEED = 1344
CACHE = Path.home() / ".cache" / "walklab" / "srbh-jev-cache.jsonl"
PRICE_IN = 0.042e-6
src, gpath, SET, MAX_USD = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]); DRY = "--dry" in sys.argv; SPARE = int("--spare" in sys.argv)   # SR-BH2: H + 1 reads for both walks
NOCAP = "--nocap" in sys.argv   # SR-BU: keep every key with df >= 2 (no upper bound); pass GRAPH = graph-train-pc-nocap.jsonl
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
allq = [r for r in map(json.loads, open(src)) if r["answerable"]]
draw = []
for t in ("3hop1", "4hop1"):
    qs = [r for r in allq if r["id"].split("__")[0] == t]
    perm = np.random.default_rng(SEED).permutation(len(qs))
    draw += [qs[i] for i in {"stage0": perm[100:102], "fresh": perm[:100]}[SET]]
Q = []
for r in draw:
    P = sorted(r["paragraphs"], key=lambda p: p["idx"]); n = len(P)
    T = [p["title"] + ". " + p["paragraph_text"] for p in P]; qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    D = [{k for k in keys.get(hid(p), ()) if 2 <= df[k] and (NOCAP or df[k] <= 100) and not set(k.split()) <= qt} for p in P]
    ix = {p["idx"]: i for i, p in enumerate(P)}
    Q.append(dict(id=r["id"], t=r["id"].split("__")[0], q=r["question"], P=P, T=T, D=D, n=n,
                  hops=[ix[s["paragraph_support_idx"]] for s in r["question_decomposition"]],
                  missing=sum(hid(p) not in keys for p in P)))
print(f"SET={SET}: {len(Q)} questions ({Counter(x['t'] for x in Q)}); passages missing from the graph {sum(x['missing'] for x in Q)}")
# ---- Jev plumbing: cached, one ask_many per wave (srbe.py's)
cache = {}
if CACHE.exists():
    for l in open(CACHE): y = json.loads(l); cache[y["k"]] = y["p"]
ck = lambda ctx, opts: hashlib.sha256(json.dumps([ctx, opts]).encode()).hexdigest()
spent = [0.0]; chars = Counter()
rc = lambda c, o: len(json.dumps(c)) + len(" ".join(o))
def wave(reqs, label):
    reqs = list({ck(c, o): (c, o) for c, o in reqs}.values()); miss = [(c, o) for c, o in reqs if ck(c, o) not in cache]
    if miss:
        est = sum(len(json.dumps(c)) / 4 + len(" ".join(o)) / 4 + 200 for c, o in miss) * PRICE_IN
        print(f"wave {label}: {len(miss)} requests, estimated ${est:.4f} (spent so far ${spent[0]:.4f}, cap ${MAX_USD})", flush=True)
        if DRY:
            for c, o in miss: cache[ck(c, o)] = list(np.random.default_rng(int(ck(c, o)[:8], 16)).random(len(o)))
            return lambda c, o: cache[ck(c, o)]
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
# ---- entry
ctxE = lambda x: {"question": x["q"], "task": ENTRY_TASK}
get = wave([(ctxE(x), x["T"]) for x in Q], "entry")
for x in Q:
    e = int(np.argmax(get(ctxE(x), x["T"]))); x["walk"] = {"cheap": [e], "pass": [e]}; x["log"] = []
    x["ch"] = {"cheap": rc(ctxE(x), x["T"]), "pass": rc(ctxE(x), x["T"])}
ctxR = lambda x, e, t: {"question": x["q"], "read": x["T"][e], "task": t}
unread = lambda x, w: [v for v in range(x["n"]) if v not in x["walk"][w]]
for step in range(1, 5):
    live = [x for x in Q if len(x["hops"]) + SPARE > step]
    if not live: break
    # wave a: the cheap walk's name request, the pass walk's pass request
    reqs = []
    for x in live:
        e = x["walk"]["cheap"][-1]
        if x["D"][e]: reqs.append((ctxR(x, e, NAME_TASK), sorted(x["D"][e])))
        e = x["walk"]["pass"][-1]; reqs.append((ctxR(x, e, PASS_TASK), [x["T"][v] for v in unread(x, "pass")]))
    get = wave(reqs, f"step {step} a")
    pend = []
    for x in live:
        e = x["walk"]["pass"][-1]; ot = unread(x, "pass"); o = [x["T"][v] for v in ot]
        x["walk"]["pass"].append(ot[int(np.argmax(get(ctxR(x, e, PASS_TASK), o)))]); x["ch"]["pass"] += rc(ctxR(x, e, PASS_TASK), o)
        e = x["walk"]["cheap"][-1]; ot = unread(x, "cheap"); R = sorted(x["D"][e]); S = []
        if R:
            K = R[int(np.argmax(get(ctxR(x, e, NAME_TASK), R)))]; x["ch"]["cheap"] += rc(ctxR(x, e, NAME_TASK), R)
            S = [v for v in ot if K in keys.get(hid(x["P"][v]), set())]
        x["S"] = S if len(S) > 1 else (ot if not S else None)   # None: one passage shares K, no request
        x["kind"] = "one" if len(S) == 1 else "twin" if S else ("rescue" if R else "rescue, no keys")
        if len(S) == 1: x["walk"]["cheap"].append(S[0])
        else: pend.append((ctxR(x, e, PASS_TASK), [x["T"][v] for v in x["S"]]))
    get = wave(pend, f"step {step} b")
    for x in live:
        e = x["walk"]["cheap"][-1]
        if x["S"] is not None:
            o = [x["T"][v] for v in x["S"]]; x["ch"]["cheap"] += rc(ctxR(x, e, PASS_TASK), o)
            x["walk"]["cheap"].append(x["S"][int(np.argmax(get(ctxR(x, e, PASS_TASK), o)))])
        x["log"].append(x["kind"])
print(f"spend this run ${spent[0]:.5f}")
# ---- scoring
def boot(d, B=2000):
    rng = np.random.default_rng(0); d = np.asarray(d, float); i = rng.integers(0, len(d), (B, len(d)))
    return f"{d.mean():+.3f} [{np.quantile(d[i].mean(1), .025):+.3f}, {np.quantile(d[i].mean(1), .975):+.3f}] (n {len(d)})"
res = {w: {"all": [], "hop": []} for w in ("cheap", "pass")}
for x in Q:
    for w in res:
        got = set(x["walk"][w]); res[w]["all"].append(float(set(x["hops"]) <= got))
        res[w]["hop"].append(np.mean([h in got for h in x["hops"]]))
for t in ("3hop1", "4hop1", "all"):
    sel = [i for i, x in enumerate(Q) if t == "all" or x["t"] == t]
    for w in res:
        print(f"{t:6s} {w:6s} all hops {np.mean([res[w]['all'][i] for i in sel]):.3f}  per-hop recall {np.mean([res[w]['hop'][i] for i in sel]):.3f}"
              f"  input chars/question {np.mean([Q[i]['ch'][w] for i in sel]):,.0f}")
    print(f"{t:6s} cheap − pass: all hops {boot([res['cheap']['all'][i] - res['pass']['all'][i] for i in sel])}; "
          f"per-hop {boot([res['cheap']['hop'][i] - res['pass']['hop'][i] for i in sel])}")
print("PRIMARY all hops, cheap − pass (both types): " + boot(np.array(res["cheap"]["all"]) - np.array(res["pass"]["all"])))
pos = lambda x: f"hop {x['hops'].index(x['walk']['cheap'][0]) + 1}" if x["walk"]["cheap"][0] in x["hops"] else "off-chain"
for k in sorted({pos(x) for x in Q}):   # bill's note 2: a mid-chain entry can't reach earlier hops walking forward
    sel = [i for i, x in enumerate(Q) if pos(x) == k]
    print(f"entry {k:9s} n {len(sel):3d}: all hops cheap {np.mean([res['cheap']['all'][i] for i in sel]):.3f}, pass {np.mean([res['pass']['all'][i] for i in sel]):.3f}")
r = np.mean([x["ch"]["cheap"] for x in Q]) / np.mean([x["ch"]["pass"] for x in Q])
print(f"input chars, cheap / pass: {r:.3f}")
for step in range(1, 5):
    ks = Counter(x["log"][step - 1] for x in Q if len(x["log"]) >= step)
    if ks: print(f"step {step}: {dict(ks)}; rescue rate {(ks['rescue'] + ks['rescue, no keys']) / sum(ks.values()):.3f}")
json.dump([dict(id=x["id"], hops=x["hops"], walk=x["walk"], log=x["log"], ch=x["ch"]) for x in Q] + [{"usd": spent[0]}],
          open(f"out/srbh-{SET}{'-spare' if SPARE else ''}{'-nocap' if NOCAP else ''}{'-dry' if DRY else ''}.json", "w"))
