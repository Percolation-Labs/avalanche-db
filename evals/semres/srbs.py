"""SR-BS (bill's DESIGN-STOP-RULE.md, #96; loop by james): when should a chain walk stop, with the hop count hidden?
MuSiQue train answerable chains (2hop, 3hop1, 4hop1), PER of each (registered 80), each question's own pool of 20. srbh.py's walks,
tasks and key filter, unchanged, except that the step request carries one extra option, STOP_OPT (S-in).

ONE TRAJECTORY PER STEP RULE. Each walk (cheap, pass) is walked once. The passage it steps to is the argmax over the
real options only, so STOP_OPT never changes a step. The stop rules only decide where that trajectory is cut:
  S-in     the first step whose request ranks STOP_OPT first (cheap: the name request, or the rescue request when the
           read has no keys; pass: its pass request). Context: the last read only. No extra request.
  S-check  after each read, one request with every read passage (full text) in context and the two CHECK_OPTS; stop
           when the 'answered' option wins. One extra request per read, growing with the reads.
  H, H+1   oracles (SR-BH, SR-BH2).
A walk continues while any rule still needs it: until H + 1 reads and both rules have fired, or the pool is empty
(20 reads, the physical bound). Batching: per read count, one wave of [checks + step requests] over the still-live
questions, then one wave of twins and rescues.
    set -a; source ~/code/p8-subsystems/.env; set +a; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \
    uv run --with numpy --with 'percolate-core==0.2.15' python srbs.py MUSIQUE_TRAIN GRAPH_TRAIN SET MAX_USD [--dry]"""
import asyncio, hashlib, json, re, sys
from collections import Counter
from pathlib import Path
import numpy as np

ENTRY_TASK = "Each option is a passage. Which passage should be read first to answer `question`?"
NAME_TASK = ("Each option is a name or phrase that appears in `read`. Which option is the thing that `question` needs "
             "`read` to identify, so that the next passage to read is about it?")   # SR-BN, unchanged
PASS_TASK = ("Each option is a passage not yet read. Having read `read`, would reading this option next give information "
             "needed to answer `question`?")   # SR-J, unchanged
STOP_OPT = "Nothing more: what has been read already answers `question`."            # bill's design, S-in
CHECK_TASK = "Which statement is true of the passages in `reads`?"   # the registration gives only the options; task line flagged to bill
CHECK_OPTS = ["`question` can be answered from these passages", "`question` needs a passage not yet read"]   # REGISTERED-SRBS.md
SEED = 1345
PER = 70   # per type: the registered 80 shrunk evenly, since the random-score dry run priced 80 at $0.56 > the $0.50 cap
TYPES = ("2hop", "3hop1", "4hop1")
CACHE = Path.home() / ".cache" / "walklab" / "srbs-jev-cache.jsonl"
PRICE_IN = 0.042e-6
src, gpath, SET, MAX_USD = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]); DRY = "--dry" in sys.argv
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
allq = [r for r in map(json.loads, open(src)) if r["answerable"]]
bytype = {t: [r for r in allq if r["id"].split("__")[0] == t] for t in TYPES}
# questions any earlier Jev run used (SR-BX/SR-BE: 2hop, seed 1341, positions 0-607; SR-BH: seed 1344, 0-101 per type)
used = {bytype["2hop"][i]["id"] for i in np.random.default_rng(1341).permutation(len(bytype["2hop"]))[:608]}
for t in ("3hop1", "4hop1"):
    used |= {bytype[t][i]["id"] for i in np.random.default_rng(1344).permutation(len(bytype[t]))[:102]}
draw = []
for t in TYPES:
    fresh = [r for r in bytype[t] if r["id"] not in used]
    perm = np.random.default_rng(SEED).permutation(len(fresh))
    draw += [fresh[i] for i in {"stage0": perm[80:82], "fresh": perm[:PER]}[SET]]
assert not {r["id"] for r in draw} & used
Q = []
for r in draw:
    P = sorted(r["paragraphs"], key=lambda p: p["idx"]); n = len(P)
    T = [p["title"] + ". " + p["paragraph_text"] for p in P]; qt = set(re.findall(r"[a-z0-9]+", r["question"].lower()))
    D = [{k for k in keys.get(hid(p), ()) if 2 <= df[k] <= 100 and not set(k.split()) <= qt} for p in P]
    ix = {p["idx"]: i for i, p in enumerate(P)}
    Q.append(dict(id=r["id"], t=r["id"].split("__")[0], q=r["question"], P=P, T=T, D=D, n=n,
                  hops=[ix[s["paragraph_support_idx"]] for s in r["question_decomposition"]]))
print(f"SET={SET}: {len(Q)} questions ({dict(Counter(x['t'] for x in Q))}); none used by an earlier Jev run")
# ---- Jev plumbing (srbh.py's)
cache = {}
if CACHE.exists():
    for l in open(CACHE): y = json.loads(l); cache[y["k"]] = y["p"]
ck = lambda ctx, opts: hashlib.sha256(json.dumps([ctx, opts]).encode()).hexdigest()
spent = [0.0]
rc = lambda c, o: len(json.dumps(c)) + len(" ".join(o))
def wave(reqs, label):
    reqs = list({ck(c, o): (c, o) for c, o in reqs}.values()); miss = [(c, o) for c, o in reqs if ck(c, o) not in cache]
    if miss:
        est = sum(len(json.dumps(c)) / 4 + len(" ".join(o)) / 4 + 200 for c, o in miss) * PRICE_IN
        print(f"wave {label}: {len(miss)} requests, estimated ${est:.4f} (spent so far ${spent[0]:.4f}, cap ${MAX_USD})", flush=True)
        if DRY:
            spent[0] += est
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
# ---- entry (shared by both walks)
ctxE = lambda x: {"question": x["q"], "task": ENTRY_TASK}
get = wave([(ctxE(x), x["T"]) for x in Q], "entry")
WALKS = ("cheap", "pass")
for x in Q:
    e = int(np.argmax(get(ctxE(x), x["T"])))
    x["walk"] = {w: [e] for w in WALKS}
    x["step_ch"] = {w: [rc(ctxE(x), x["T"])] for w in WALKS}   # cumulative input after each read count (index r-1)
    x["check_ch"] = {w: [] for w in WALKS}                      # S-check request size after r reads
    x["sin"] = {w: None for w in WALKS}; x["scheck"] = {w: None for w in WALKS}   # reads at which each rule stopped
    x["checks"] = {w: [] for w in WALKS}; x["log"] = {w: [] for w in WALKS}; x["sin_step1"] = {}
ctxR = lambda x, e, t: {"question": x["q"], "read": x["T"][e], "task": t}
ctxC = lambda x, w: {"question": x["q"], "reads": [x["T"][v] for v in x["walk"][w]], "task": CHECK_TASK}
unread = lambda x, w: [v for v in range(x["n"]) if v not in x["walk"][w]]
def needs(x, w):
    r = len(x["walk"][w])
    return r < x["n"] and (r < len(x["hops"]) + 1 or x["sin"][w] is None or x["scheck"][w] is None)
while True:
    live = [(x, w) for x in Q for w in WALKS if needs(x, w) or (x["scheck"][w] is None and len(x["walk"][w]) >= x["n"])]
    if not live: break
    r = max(len(x["walk"][w]) for x, w in live)
    # wave a: the S-check after the reads so far, and each walk's first step request (STOP_OPT appended)
    reqs = []
    for x, w in live:
        x.setdefault("go", {})[w] = needs(x, w)   # decided before this wave's answers, so a step asked for is a step taken
        if x["scheck"][w] is None: reqs.append((ctxC(x, w), CHECK_OPTS))
        if not x["go"][w]: continue
        e = x["walk"][w][-1]; R = sorted(x["D"][e])
        if w == "cheap" and R: reqs.append((ctxR(x, e, NAME_TASK), R + [STOP_OPT]))
        else: reqs.append((ctxR(x, e, PASS_TASK), [x["T"][v] for v in unread(x, w)] + [STOP_OPT]))
    get = wave(reqs, f"after up to {r} reads, a")
    pend = []
    for x, w in live:
        k = len(x["walk"][w])
        if x["scheck"][w] is None:
            p = get(ctxC(x, w), CHECK_OPTS); x["check_ch"][w].append(rc(ctxC(x, w), CHECK_OPTS))
            x["checks"][w].append((k, int(p[0] > p[1]), int(set(x["hops"]) <= set(x["walk"][w]))))
            if p[0] > p[1] or k >= x["n"]: x["scheck"][w] = k
        if not x["go"][w]: continue
        e = x["walk"][w][-1]; ot = unread(x, w); R = sorted(x["D"][e]); c = 0
        if w == "cheap" and R:
            o = R + [STOP_OPT]; p = get(ctxR(x, e, NAME_TASK), o); c += rc(ctxR(x, e, NAME_TASK), o)
            stop = int(np.argmax(p)) == len(R); K = R[int(np.argmax(p[:-1]))]
            S = [v for v in ot if K in keys.get(hid(x["P"][v]), set())]
            kind = "one" if len(S) == 1 else "twin" if S else "rescue"
        else:
            o = [x["T"][v] for v in ot] + [STOP_OPT]; p = get(ctxR(x, e, PASS_TASK), o); c += rc(ctxR(x, e, PASS_TASK), o)
            stop = int(np.argmax(p)) == len(ot); S = None; kind = "pass" if w == "pass" else "rescue, no keys"
            x.setdefault("nxt", {})[w] = ot[int(np.argmax(p[:-1]))]
        if stop and x["sin"][w] is None: x["sin"][w] = k
        if k == 1: x["sin_step1"][w] = stop
        x["log"][w].append(kind)
        x.setdefault("st", {})[w] = (S, kind, c)
        if w == "cheap" and kind in ("twin", "rescue"):
            opts = S if kind == "twin" else ot
            pend.append((ctxR(x, e, PASS_TASK), [x["T"][v] for v in opts]))
    get = wave(pend, f"after up to {r} reads, b")
    for x, w in live:
        if not x["go"][w]: continue
        S, kind, c = x["st"][w]; e = x["walk"][w][-1]; ot = unread(x, w)
        if kind == "one": nxt = S[0]
        elif kind in ("twin", "rescue"):
            opts = S if kind == "twin" else ot; o = [x["T"][v] for v in opts]
            nxt = opts[int(np.argmax(get(ctxR(x, e, PASS_TASK), o)))]; c += rc(ctxR(x, e, PASS_TASK), o)
        else: nxt = x["nxt"][w]
        x["walk"][w].append(nxt); x["step_ch"][w].append(x["step_ch"][w][-1] + c)
print(f"spend this run ${spent[0]:.5f}{' (DRY: estimate only)' if DRY else ''}")
# ---- scoring
def boot(d, B=2000):
    rng = np.random.default_rng(0); d = np.asarray(d, float); i = rng.integers(0, len(d), (B, len(d)))
    return f"{d.mean():+.3f} [{np.quantile(d[i].mean(1), .025):+.3f}, {np.quantile(d[i].mean(1), .975):+.3f}] (n {len(d)})"
def cut(x, w, rule):
    """reads used, all-hops, input chars under a stop rule (S-in never fired: the walk ran to the pool's end)."""
    H = len(x["hops"]); k = {"H": H, "H+1": H + 1, "S-in": x["sin"][w] or len(x["walk"][w]), "S-check": x["scheck"][w]}[rule]
    k = min(k, len(x["walk"][w])); ch = x["step_ch"][w][k - 1] + (sum(x["check_ch"][w][:k]) if rule == "S-check" else 0)
    return k, float(set(x["hops"]) <= set(x["walk"][w][:k])), ch
RULES = ("H", "H+1", "S-in", "S-check")
A = {(w, s): [cut(x, w, s) for x in Q] for w in WALKS for s in RULES}
for t in TYPES + ("all",):
    sel = [i for i, x in enumerate(Q) if t == "all" or x["t"] == t]
    print(f"-- {t} (n {len(sel)})")
    for w in WALKS:
        for s in RULES:
            v = [A[(w, s)][i] for i in sel]; H = [len(Q[i]["hops"]) for i in sel]
            ac, ch = np.mean([a for _, a, _ in v]), np.mean([c for _, _, c in v])
            el = Counter("early" if k < h else "exact" if k == h else "late" for (k, _, _), h in zip(v, H))
            print(f"   {w:5s} {s:7s} all hops {ac:.3f}  reads {np.mean([k for k, _, _ in v]):.2f}  input {ch:,.0f}  "
                  f"per 10k {ac / ch * 1e4:.4f}  early/exact/late {el['early']}/{el['exact']}/{el['late']}")
d = lambda w, s: np.array([a for _, a, _ in A[(w, s)]])
print("PRIMARY all hops, cheap × S-check − cheap × oracle(H): " + boot(d("cheap", "S-check") - d("cheap", "H")))
for w, s in (("cheap", "S-in"), ("pass", "S-check"), ("pass", "S-in")):
    print(f"{w} × {s} − {w} × oracle(H): " + boot(d(w, s) - d(w, "H")))
print("cheap × S-check − pass × S-check: " + boot(d("cheap", "S-check") - d("pass", "S-check")))
for w in WALKS:
    cm = Counter((st, ok) for x in Q for (_, st, ok) in x["checks"][w])
    print(f"S-check decisions on the {w} walk (decision × all hops read): stop&complete {cm[(1, 1)]}, stop&incomplete {cm[(1, 0)]}, "
          f"continue&complete {cm[(0, 1)]}, continue&incomplete {cm[(0, 0)]}; stops after one read "
          f"{sum(x['scheck'][w] == 1 for x in Q)}; S-in wins at step 1 {sum(bool(x['sin_step1'].get(w)) for x in Q)}")
json.dump([dict(id=x["id"], t=x["t"], hops=x["hops"], walk=x["walk"], sin=x["sin"], scheck=x["scheck"], checks=x["checks"],
                log=x["log"], step_ch=x["step_ch"], check_ch=x["check_ch"]) for x in Q] + [{"usd": spent[0]}],
          open(f"out/srbs-{SET}{'-dry' if DRY else ''}.json", "w"))
