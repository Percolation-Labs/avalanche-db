"""SR-BS2 (REGISTERED-SRBS2.md, james; built from srbs.py): which check stops the full-step walk at the answer passage?
Measure: A-last (the gold last-hop passage is returned; NOTE-ANSWER-MEASURE.md). Pass walk only; S-in dropped.
Two checks after each read, each a two-option request over every read passage (full text):
  S-check  SR-BS's wording, unchanged
  S-state  "these passages state the answer to `question`" against "`question` needs a passage not yet read"
A trajectory ends once both checks have fired and H + 1 reads are in, or the pool is empty.
SR-BS's original description follows.

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
STATE_OPTS = ["these passages state the answer to `question`", "`question` needs a passage not yet read"]   # SR-BS2
SEED = 1347   # 1346 is SR-AC's seed (bill's review); a new seed, plus explicit exclusion below
PER = 60   # per type (SR-BS's final size)
TYPES = ("2hop", "3hop1", "4hop1")
CACHE = Path.home() / ".cache" / "walklab" / "srbs2-jev-cache.jsonl"
PRICE_IN = 0.042e-6
src, gpath, SET, MAX_USD = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]); DRY = "--dry" in sys.argv
DRAW_SRC = str(Path.home() / ".cache/walklab/mq-train/musique_ans_v1.0_train.jsonl")   # sha 83a75b1e…
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
allq = [r for r in map(json.loads, open(src)) if r["answerable"]]
bytype = {t: [r for r in allq if r["id"].split("__")[0] == t] for t in TYPES}
# questions any earlier Jev run used, rebuilt exactly as each run drew them from the corpus lists
used = {bytype["2hop"][i]["id"] for i in np.random.default_rng(1341).permutation(len(bytype["2hop"]))[:608]}   # SR-BX, SR-BE
for t in ("3hop1", "4hop1"):
    used |= {bytype[t][i]["id"] for i in np.random.default_rng(1344).permutation(len(bytype[t]))[:102]}        # SR-BH
_u = set(used)                                                                                                   # SR-BS's own exclusion set
for t in ("2hop", "3hop1", "4hop1"):
    fr = [r for r in bytype[t] if r["id"] not in _u]
    used |= {fr[i]["id"] for i in np.random.default_rng(1345).permutation(len(fr))[:82]}                         # SR-BS (60 + stage 0 at 80-81)
for f in ("used/srac-fresh.json", "used/srac-stage0.json"):                                                     # SR-AC, by id
    used |= {o["id"] for o in json.load(open(f))["out"]}
for f in ("used/srbf-fresh.json", "used/srbf-stage0.json"):                                                     # SR-BF, by id
    used |= set(json.load(open(f))["ids"])
# The draw comes from the FULL MuSiQue train file (the corpus has only 10 unused 4hop1 chains left). The pass walk and
# the checks use no graph keys, so passages outside the train graph don't matter.
full = [r for r in map(json.loads, open(DRAW_SRC)) if r["answerable"]]
draw = []
for t in TYPES:
    fresh = [r for r in full if r["id"].split("__")[0] == t and r["id"] not in used]
    perm = np.random.default_rng(SEED).permutation(len(fresh))
    draw += [fresh[k] for k in {"stage0": perm[80:82], "fresh": perm[:PER]}[SET]]
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
# ---- entry, then the pass walk with two checks after each read
ctxE = lambda x: {"question": x["q"], "task": ENTRY_TASK}
get = wave([(ctxE(x), x["T"]) for x in Q], "entry")
ctxR = lambda x, e, t: {"question": x["q"], "read": x["T"][e], "task": t}
ctxC = lambda x: {"question": x["q"], "reads": [x["T"][v] for v in x["walk"]], "task": CHECK_TASK}
unread = lambda x: [v for v in range(x["n"]) if v not in x["walk"]]
RULES_C = {"S-check": CHECK_OPTS, "S-state": STATE_OPTS}
for x in Q:
    x["walk"] = [int(np.argmax(get(ctxE(x), x["T"])))]; x["ch"] = [rc(ctxE(x), x["T"])]
    x["stop"] = {r: None for r in RULES_C}; x["cch"] = {r: [] for r in RULES_C}; x["checks"] = {r: [] for r in RULES_C}
needs = lambda x: len(x["walk"]) < x["n"] and (len(x["walk"]) < len(x["hops"]) + 1 or None in x["stop"].values())
while True:
    live = [x for x in Q if needs(x) or None in x["stop"].values()]
    if not live: break
    r = max(len(x["walk"]) for x in live); reqs = []
    for x in live:
        x["go"] = needs(x)
        for rule, o in RULES_C.items():
            if x["stop"][rule] is None: reqs.append((ctxC(x), o))
        if x["go"]: reqs.append((ctxR(x, x["walk"][-1], PASS_TASK), [x["T"][v] for v in unread(x)]))
    get = wave(reqs, f"after up to {r} reads")
    for x in live:
        k = len(x["walk"]); got = int(x["hops"][-1] in x["walk"])
        for rule, o in RULES_C.items():
            if x["stop"][rule] is None:
                p = get(ctxC(x), o); x["cch"][rule].append(rc(ctxC(x), o)); x["checks"][rule].append((k, int(p[0] > p[1]), got))
                if p[0] > p[1] or k >= x["n"]: x["stop"][rule] = k
        if x["go"]:
            e = x["walk"][-1]; ot = unread(x); o = [x["T"][v] for v in ot]
            x["walk"].append(ot[int(np.argmax(get(ctxR(x, e, PASS_TASK), o)))]); x["ch"].append(x["ch"][-1] + rc(ctxR(x, e, PASS_TASK), o))
print(f"spend this run ${spent[0]:.5f}{' (DRY: estimate only)' if DRY else ''}")
# ---- scoring: A-last (primary), returned-set size, input
def boot(d, B=2000):
    rng = np.random.default_rng(0); d = np.asarray(d, float); i = rng.integers(0, len(d), (B, len(d))); m = d[i].mean(1)
    return f"{d.mean():+.3f} [{np.quantile(m, .025):+.3f}, {np.quantile(m, .975):+.3f}] (n {len(d)})"
def cut(x, rule):
    H = len(x["hops"]); k = {"H": H, "H+1": H + 1}.get(rule) or x["stop"][rule]; k = min(k, len(x["walk"]))
    return k, float(x["hops"][-1] in x["walk"][:k]), x["ch"][k - 1] + (sum(x["cch"][rule][:k]) if rule in RULES_C else 0)
RULES = ("H", "H+1", "S-check", "S-state")
A = {s_: [cut(x, s_) for x in Q] for s_ in RULES}
for t in TYPES + ("all",):
    sel = [i for i, x in enumerate(Q) if t == "all" or x["t"] == t]; print(f"-- {t} (n {len(sel)})")
    for s_ in RULES:
        v = [A[s_][i] for i in sel]; H = [len(Q[i]["hops"]) for i in sel]
        el = Counter("early" if k < h else "exact" if k == h else "late" for (k, _, _), h in zip(v, H))
        print(f"   pass {s_:7s} A-last {np.mean([a for _, a, _ in v]):.3f}  returned {np.mean([k for k, _, _ in v]):.2f}  "
              f"input {np.mean([c for _, _, c in v]):,.0f}  early/exact/late {el['early']}/{el['exact']}/{el['late']}")
d = lambda s_: np.array([a for _, a, _ in A[s_]])
print("PRIMARY A-last, S-state − S-check: " + boot(d("S-state") - d("S-check")))
print("S-state − oracle(H): " + boot(d("S-state") - d("H")) + "; S-check − oracle(H): " + boot(d("S-check") - d("H")))
for rule in RULES_C:
    cm = Counter((st_, ok) for x in Q for (_, st_, ok) in x["checks"][rule])
    arr = Counter()
    for x in Q:
        L = x["hops"][-1]; f = x["walk"].index(L) + 1 if L in x["walk"] else None; s_ = x["stop"][rule]
        arr["never reached" if f is None else "before arrival" if s_ < f else "at arrival" if s_ == f else "after arrival"] += 1
    print(f"{rule}: decisions (stop/continue × answer passage read) stop&read {cm[(1, 1)]}, stop&not {cm[(1, 0)]}, continue&read {cm[(0, 1)]}, "
          f"continue&not {cm[(0, 0)]}; stop vs first arrival {dict(arr)}; stops after one read {sum(x['stop'][rule] == 1 for x in Q)}")
json.dump([dict(id=x["id"], t=x["t"], hops=x["hops"], walk=x["walk"], stop=x["stop"], checks=x["checks"], ch=x["ch"], cch=x["cch"]) for x in Q]
          + [{"usd": spent[0]}], open(f"out/srbs2-{SET}{'-dry' if DRY else ''}.json", "w"))
