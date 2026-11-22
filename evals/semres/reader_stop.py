"""Reader-stop look (REGISTERED-RSTOP.md, james; bill's suggestion 17:43Z). Replays a stop rule on SR-BS3's cached
pass-walk trajectories (out/srbs3-fresh.json), no walk rerun. After each read prefix, bill's reader request (srac.py,
verbatim) with one extra option, NONE: "No sentence in `reads` states the answer to `question`." Stop at the first
prefix where a real sentence wins the argmax. Scored on the stopped set by AC (string or judge, #102) using the chosen
sentence, plus A-last and the returned size, against oracle H (the same trajectories cut at the hop count, AC from
srbs2_ac.py's cache). A walk the reader never stops runs to the end of its cached trajectory (reported).
    uv run --with numpy --with 'percolate-core==0.2.15' python reader_stop.py MAX_USD [--dry]"""
import asyncio, hashlib, json, re, sys
from pathlib import Path
import numpy as np
SENT_TASK = "Each option is a sentence from `reads`. Which sentence states the answer to `question`?"        # srac.py
NONE = "No sentence in `reads` states the answer to `question`."
EQ_TASK = "Does `sentence` state that the answer to `question` is `answer`, possibly in other words?"           # ac_equiv.py
EQ_OPTS = ["Yes: the sentence states this answer.", "No: the sentence does not state this answer."]
norm = lambda s: " ".join(re.findall(r"[a-z0-9]+", s.lower()))
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
sents = lambda p: [f"{p['title']}: {s}" for s in SPLIT.split(p["paragraph_text"].strip()) if s.strip()]
ctx = lambda q, ps: {"question": q, "reads": [f"{p['title']}. {p['paragraph_text']}" for p in ps], "task": SENT_TASK}
opts = lambda ps: [s for p in ps for s in sents(p)]
ectx = lambda q, a, s: {"question": q, "answer": a, "sentence": s, "task": EQ_TASK}
PRICE_IN = 0.042e-6; MAX_USD = float(sys.argv[1]); DRY = "--dry" in sys.argv
C1 = Path.home() / ".cache/walklab/rstop-jev-cache.jsonl"; C2 = Path.home() / ".cache/walklab/ac-equiv-cache.jsonl"
ck = lambda c, o: hashlib.sha256(json.dumps([c, o]).encode()).hexdigest()
def load(p):
    d = {}
    if p.exists():
        for l in open(p): y = json.loads(l); d[y["k"]] = y["p"]
    return d
c1, c2 = load(C1), load(C2); spent = [0.0]
def ask(reqs, cache, path, label):
    reqs = list({ck(c, o): (c, o) for c, o in reqs}.values()); miss = [(c, o) for c, o in reqs if ck(c, o) not in cache]
    est = sum(len(json.dumps(c)) / 4 + len(" ".join(o)) / 4 + 200 for c, o in miss) * PRICE_IN
    print(f"{label}: {len(reqs)} requests, {len(miss)} uncached, estimated ${est:.4f} (spent ${spent[0]:.4f}, cap ${MAX_USD})", flush=True)
    if DRY:
        for c, o in miss: cache[ck(c, o)] = list(np.random.default_rng(int(ck(c, o)[:8], 16)).random(len(o)))
        return
    if spent[0] + est > MAX_USD: sys.exit("over cap")
    if not miss: return
    from percolate_core.decide import Jev, Noul
    async def go():
        async with Jev() as jev:
            return await jev.ask_many([(c, {f"p{j}": Noul(t) for j, t in enumerate(o)}) for c, o in miss])
    with open(path, "a") as f:
        for (c, o), res in zip(miss, asyncio.run(go())):
            p = [res[f"p{j}"].p for j in range(len(o))]; cache[ck(c, o)] = p; spent[0] += res.input_tokens * PRICE_IN
            f.write(json.dumps({"k": ck(c, o), "p": p}) + "\n")
R = {}
for l in open(Path.home() / ".cache/walklab/mq-train/musique_ans_v1.0_train.jsonl"):
    r = json.loads(l); R[r["id"]] = r
X = [x for x in json.load(open("out/srbs3-fresh.json")) if "id" in x]
AC0 = {(it["id"], it["rule"]): it for it in json.load(open("out/srbs3-fresh-ac.json"))}
# every prefix of every cached trajectory: one wave (all prefixes are known in advance, so no dependency)
Q = []
for x in X:
    r = R[x["id"]]; P = sorted(r["paragraphs"], key=lambda p: p["idx"])
    Q.append(dict(id=x["id"], t=x["t"], q=r["question"], a=r["answer"], hops=x["hops"], walk=x["walk"], P=P, ch=x["ch"],
                  golds={norm(g) for g in [r["answer"]] + r.get("answer_aliases", []) if norm(g)}))
for x in Q: x["stop"], x["chosen"] = None, None
kmax = max(len(x["walk"]) for x in Q)
for k in range(1, kmax + 1):   # one wave per prefix length, only for walks the reader hasn't stopped (least spend)
    live = [x for x in Q if x["stop"] is None and len(x["walk"]) >= k]
    if not live: break
    pre = lambda x: [x["P"][v] for v in x["walk"][:k]]
    ask([(ctx(x["q"], pre(x)), opts(pre(x)) + [NONE]) for x in live], c1, C1, f"reader with NONE, prefix {k}")
    for x in live:
        ps = pre(x); o = opts(ps) + [NONE]; pr = c1[ck(ctx(x["q"], ps), o)]; j = int(np.argmax(pr))
        if j < len(o) - 1: x["stop"], x["chosen"] = k, o[j]
        elif k == len(x["walk"]): x["stop"], x["chosen"], x["never"] = k, o[int(np.argmax(pr[:-1]))], True   # never stopped
for x in Q:
    x["str"] = int(any(g in norm(x["chosen"]) for g in x["golds"]))
ask([(ectx(x["q"], x["a"], x["chosen"]), EQ_OPTS) for x in Q if not x["str"]], c2, C2, "judge")
for x in Q:
    x["ac"] = x["str"] or int(np.argmax(c2[ck(ectx(x["q"], x["a"], x["chosen"]), EQ_OPTS)]) == 0)
    x["alast"] = int(x["hops"][-1] in x["walk"][:x["stop"]])
print(f"spend ${spent[0]:.5f}{' (DRY)' if DRY else ''}")
def boot(d, B=2000):
    d = np.asarray(d, float); rng = np.random.default_rng(0); i = rng.integers(0, len(d), (B, len(d))); m = d[i].mean(1)
    return f"{d.mean():+.3f} [{np.quantile(m, .025):+.3f}, {np.quantile(m, .975):+.3f}]"
for t in ("2hop", "3hop1", "4hop1", "all"):
    s = [x for x in Q if t == "all" or x["t"] == t]
    print(f"{t:6s} R-stop AC {np.mean([x['ac'] for x in s]):.3f}  A-last {np.mean([x['alast'] for x in s]):.3f}  returned {np.mean([x['stop'] for x in s]):.2f}  "
          f"never stopped {sum(x.get('never', False) for x in s)}  | oracle H AC {np.mean([AC0[(x['id'], 'H')]['ac'] for x in s]):.3f}, S-check AC {np.mean([AC0[(x['id'], 'S-check')]['ac'] for x in s]):.3f}")
print("AC, R-stop − oracle H: " + boot([x["ac"] - AC0[(x["id"], "H")]["ac"] for x in Q]))
print("AC, R-stop − S-check: " + boot([x["ac"] - AC0[(x["id"], "S-check")]["ac"] for x in Q]))
print(f"stops after one read {sum(x['stop'] == 1 for x in Q)}; input to the stop (walk + reader requests) is reported in the result from the json")
json.dump([{k: v for k, v in x.items() if k not in ("P", "golds")} for x in Q], open("out/rstop.json", "w"))
