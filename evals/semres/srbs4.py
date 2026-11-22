"""SR-BS4 (REGISTERED-SRBS4.md, james): the reader-tied stop (R-stop, #105) as a live walk on a fresh draw.
Jev's entry, then the pass step. After each read, bill's reader request (srac.py, verbatim) plus NONE; the walk stops at
the first read where a real sentence wins, or when the pool (20) is empty. The walk continues at least to H reads so
oracle H is scored on the same trajectory. AC (string or judge) of each returned set with the standard reader request.
srbs3.py's description follows.


SR-BS2 (REGISTERED-SRBS2.md, james; built from srbs.py): which check stops the full-step walk at the answer passage?
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
SEED = 1349   # SR-BS4
PER = 100   # per type
TYPES = ("2hop", "3hop1", "4hop1")
CACHE = Path.home() / ".cache" / "walklab" / "srbs4-jev-cache.jsonl"
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
# SR-BS2's draw (seed 1347, positions 0-81 per type over the same fresh lists), rebuilt before adding it to `used`
_u2 = set(used)
for t in TYPES:
    fr = [r for r in full if r["id"].split("__")[0] == t and r["id"] not in _u2]
    used |= {fr[k]["id"] for k in np.random.default_rng(1347).permutation(len(fr))[:82]}
for f in ("out/srbs3-fresh.json", "out/srbs3-stage0.json"):   # SR-BS3 and R-stop's questions, by id
    used |= {x["id"] for x in json.load(open(f)) if "id" in x}
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
# ---- reader-tied stop, live
SENT_TASK = "Each option is a sentence from `reads`. Which sentence states the answer to `question`?"        # srac.py
NONE = "No sentence in `reads` states the answer to `question`."                                             # R-stop
EQ_TASK = "Does `sentence` state that the answer to `question` is `answer`, possibly in other words?"           # ac_equiv.py
EQ_OPTS = ["Yes: the sentence states this answer.", "No: the sentence does not state this answer."]
norm = lambda s: " ".join(re.findall(r"[a-z0-9]+", s.lower()))
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
sents = lambda p: [f"{p['title']}: {s}" for s in SPLIT.split(p["paragraph_text"].strip()) if s.strip()]
rctx = lambda x, k: {"question": x["q"], "reads": [f"{x['P'][v]['title']}. {x['P'][v]['paragraph_text']}" for v in x["walk"][:k]], "task": SENT_TASK}
ropts = lambda x, k: [s for v in x["walk"][:k] for s in sents(x["P"][v])]
ectx = lambda x, s: {"question": x["q"], "answer": x["ans"], "sentence": s, "task": EQ_TASK}
for x, r in zip(Q, draw):
    x["ans"] = r["answer"]; x["golds"] = {norm(g) for g in [r["answer"]] + r.get("answer_aliases", []) if norm(g)}
ctxE = lambda x: {"question": x["q"], "task": ENTRY_TASK}
get = wave([(ctxE(x), x["T"]) for x in Q], "entry")
ctxR = lambda x, e, t: {"question": x["q"], "read": x["T"][e], "task": t}
unread = lambda x: [v for v in range(x["n"]) if v not in x["walk"]]
for x in Q:
    x["walk"] = [int(np.argmax(get(ctxE(x), x["T"])))]; x["ch"] = [rc(ctxE(x), x["T"])]; x["rch"] = []; x["stop"] = None
needs = lambda x: len(x["walk"]) < x["n"] and (len(x["walk"]) < len(x["hops"]) or x["stop"] is None)
while True:
    live = [x for x in Q if needs(x) or x["stop"] is None]
    if not live: break
    r = max(len(x["walk"]) for x in live); reqs = []
    for x in live:
        x["go"] = needs(x); k = len(x["walk"])
        if x["stop"] is None: reqs.append((rctx(x, k), ropts(x, k) + [NONE]))
        if x["go"]: reqs.append((ctxR(x, x["walk"][-1], PASS_TASK), [x["T"][v] for v in unread(x)]))
    get = wave(reqs, f"after up to {r} reads")
    for x in live:
        k = len(x["walk"])
        if x["stop"] is None:
            o = ropts(x, k) + [NONE]; p = get(rctx(x, k), o); x["rch"].append(rc(rctx(x, k), o))
            if int(np.argmax(p)) < len(o) - 1 and not ("--dry-never" in sys.argv): x["stop"] = k   # --dry-never: price the tail
            elif k >= x["n"]: x["stop"], x["never"] = k, True
        if x["go"]:
            e = x["walk"][-1]; ot = unread(x); o = [x["T"][v] for v in ot]
            x["walk"].append(ot[int(np.argmax(get(ctxR(x, e, PASS_TASK), o)))]); x["ch"].append(x["ch"][-1] + rc(ctxR(x, e, PASS_TASK), o))
# ---- AC like for like: the standard reader request (no NONE) on each returned set, then the judge on string misses
sets = {(x["id"], a): (x, {"H": len(x["hops"]), "R": x["stop"]}[a]) for x in Q for a in ("H", "R")}
get = wave([(rctx(x, k), ropts(x, k)) for x, k in sets.values()], "standard reader on returned sets")
for key, (x, k) in sets.items():
    o = ropts(x, k); ch = o[int(np.argmax(get(rctx(x, k), o)))]; x.setdefault("chosen", {})[key[1]] = ch
    x.setdefault("str", {})[key[1]] = int(any(g in norm(ch) for g in x["golds"]))
get = wave([(ectx(x, x["chosen"][a]), EQ_OPTS) for x in Q for a in ("H", "R") if not x["str"][a]], "judge")
for x in Q:
    x["ac"] = {a: x["str"][a] or int(np.argmax(get(ectx(x, x["chosen"][a]), EQ_OPTS)) == 0) for a in ("H", "R")}
    x["judged"] = {a: int(x["ac"][a] and not x["str"][a]) for a in ("H", "R")}
print(f"spend this run ${spent[0]:.5f}{' (DRY: estimate only)' if DRY else ''}")
def boot(d, B=2000):
    rng = np.random.default_rng(0); d = np.asarray(d, float); i = rng.integers(0, len(d), (B, len(d))); m = d[i].mean(1)
    return f"{d.mean():+.3f} [{np.quantile(m, .025):+.3f}, {np.quantile(m, .975):+.3f}] (n {len(d)})"
K = lambda x, a: {"H": len(x["hops"]), "R": x["stop"]}[a]
for t in TYPES + ("all",):
    s_ = [x for x in Q if t == "all" or x["t"] == t]
    for a in ("H", "R"):
        print(f"{t:6s} {a}: AC {np.mean([x['ac'][a] for x in s_]):.3f} (judge yes {sum(x['judged'][a] for x in s_)})  A-last "
              f"{np.mean([x['hops'][-1] in x['walk'][:K(x, a)] for x in s_]):.3f}  returned {np.mean([K(x, a) for x in s_]):.2f}  "
              f"input {np.mean([x['ch'][K(x, a) - 1] + (sum(x['rch'][:K(x, a)]) if a == 'R' else 0) for x in s_]):,.0f}")
print("PRIMARY AC, R-stop − oracle H: " + boot([x["ac"]["R"] - x["ac"]["H"] for x in Q]))
nv = [x for x in Q if x.get("never")]
print(f"never fired: {len(nv)} of {len(Q)}; their AC {np.mean([x['ac']['R'] for x in nv]) if nv else 0:.3f}, returned {np.mean([x['stop'] for x in nv]) if nv else 0:.1f}; "
      f"excluding them: " + boot([x["ac"]["R"] - x["ac"]["H"] for x in Q if not x.get("never")]))
from collections import Counter as _C
print("reads at stop:", dict(sorted(_C(x["stop"] for x in Q).items())))
json.dump([dict(id=x["id"], t=x["t"], hops=x["hops"], walk=x["walk"], stop=x["stop"], never=x.get("never", False), ac=x["ac"], judged=x["judged"],
                chosen=x["chosen"], ch=x["ch"], rch=x["rch"]) for x in Q] + [{"usd": spent[0]}], open(f"out/srbs4-{SET}{'-dry' if DRY else ''}.json", "w"))
