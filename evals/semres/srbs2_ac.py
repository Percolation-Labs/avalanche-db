"""SR-BS2 addendum 1: AC (bill's reader check, string or judge) on SR-BS2's returned sets. The reader request is copied
verbatim from srac.py (#99) and the judge from ac_equiv.py (#102), with the same caches, so the scoring is bill's,
unchanged.
    uv run --with numpy --with 'percolate-core==0.2.15' python srbs2_ac.py MAX_USD [WALKS_JSON] [--dry]   (SR-BS3: WALKS_JSON = out/srbs3-fresh.json)"""
import asyncio, hashlib, json, re, sys
from pathlib import Path
import numpy as np
SENT_TASK = "Each option is a sentence from `reads`. Which sentence states the answer to `question`?"        # srac.py
EQ_TASK = "Does `sentence` state that the answer to `question` is `answer`, possibly in other words?"           # ac_equiv.py
EQ_OPTS = ["Yes: the sentence states this answer.", "No: the sentence does not state this answer."]
norm = lambda s: " ".join(re.findall(r"[a-z0-9]+", s.lower()))
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
sents = lambda p: [f"{p['title']}: {s}" for s in SPLIT.split(p["paragraph_text"].strip()) if s.strip()]
ctx = lambda q, ps: {"question": q, "reads": [f"{p['title']}. {p['paragraph_text']}" for p in ps], "task": SENT_TASK}
opts = lambda ps: [s for p in ps for s in sents(p)]
ectx = lambda q, a, s: {"question": q, "answer": a, "sentence": s, "task": EQ_TASK}
PRICE_IN = 0.042e-6; MAX_USD = float(sys.argv[1]); DRY = "--dry" in sys.argv
C1 = Path.home() / ".cache/walklab/srac-jev-cache.jsonl"; C2 = Path.home() / ".cache/walklab/ac-equiv-cache.jsonl"
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
SRC = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "out/srbs2-fresh.json"
X = [x for x in json.load(open(SRC)) if "id" in x]
RULES = tuple(r for r in ("H", "H+1", "S-check", "S-state") if r in ("H", "H+1") or r in X[0]["stop"])
def cut(x, rule):
    H = len(x["hops"]); k = {"H": H, "H+1": H + 1}.get(rule) or x["stop"][rule]; return x["walk"][:min(k, len(x["walk"]))]
items = []
for x in X:
    r = R[x["id"]]; P = sorted(r["paragraphs"], key=lambda p: p["idx"])
    for rule in RULES:
        ps = [P[v] for v in cut(x, rule)]
        items.append(dict(id=x["id"], rule=rule, q=r["question"], a=r["answer"], ps=ps, alast=int(x["hops"][-1] in cut(x, rule)),
                          golds={norm(g) for g in [r["answer"]] + r.get("answer_aliases", []) if norm(g)}))
ask([(ctx(it["q"], it["ps"]), opts(it["ps"])) for it in items], c1, C1, "reader")
for it in items:
    o = opts(it["ps"]); it["chosen"] = o[int(np.argmax(c1[ck(ctx(it["q"], it["ps"]), o)]))]
    it["str"] = int(any(g in norm(it["chosen"]) for g in it["golds"]))
ask([(ectx(it["q"], it["a"], it["chosen"]), EQ_OPTS) for it in items if not it["str"]], c2, C2, "judge")
for it in items:
    it["judge"] = 0 if it["str"] else int(np.argmax(c2[ck(ectx(it["q"], it["a"], it["chosen"]), EQ_OPTS)]) == 0)
    it["ac"] = it["str"] or it["judge"]
print(f"spend ${spent[0]:.5f}{' (DRY)' if DRY else ''}")
def boot(d, B=2000):
    d = np.asarray(d, float); rng = np.random.default_rng(0); i = rng.integers(0, len(d), (B, len(d))); m = d[i].mean(1)
    return f"{d.mean():+.3f} [{np.quantile(m, .025):+.3f}, {np.quantile(m, .975):+.3f}]"
by = {rule: {it["id"]: it for it in items if it["rule"] == rule} for rule in RULES}; ids = sorted(by["H"])
for rule in RULES:
    v = [by[rule][i] for i in ids]
    print(f"{rule:8s} AC {np.mean([i['ac'] for i in v]):.3f} (judge yes {sum(i['judge'] for i in v)})  A-last {np.mean([i['alast'] for i in v]):.3f}  "
          f"AC=1 & A-last=0 {sum(i['ac'] and not i['alast'] for i in v)}, AC=0 & A-last=1 {sum(i['alast'] and not i['ac'] for i in v)}  returned {np.mean([len(i['ps']) for i in v]):.2f}")
for rule in [r for r in RULES if r != "H"]:
    print(f"AC {rule} − H: {boot([by[rule][i]['ac'] - by['H'][i]['ac'] for i in ids])}   (A-last: {boot([by[rule][i]['alast'] - by['H'][i]['alast'] for i in ids])})")
json.dump([{k: v for k, v in it.items() if k not in ("ps", "golds")} for it in items], open(SRC.replace(".json", "-ac.json"), "w"))
