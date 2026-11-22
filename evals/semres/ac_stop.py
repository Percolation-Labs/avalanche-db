"""AC on SR-BS2's stopped sets (bill, for james's #101; its registered secondary). For each question, the returned set
under S-check, S-state and oracle H is walk[:stop]. AC = srac.py's reader request, unchanged, scored as string or
judge (NOTE-AC-JUDGE.md: when the string check fails, a two-option Jev judge). A-last = the set holds the last hop.
    set -a; source ~/code/p8-subsystems/.env; set +a; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \\
    uv run --with numpy --with 'percolate-core==0.2.15' python ac_stop.py MUSIQUE_TRAIN SRBS2_JSON MAX_USD [--dry]"""
import asyncio, hashlib, json, re, sys
from pathlib import Path
import numpy as np
SENT_TASK = "Each option is a sentence from `reads`. Which sentence states the answer to `question`?"
EQ_TASK = "Does `sentence` state that the answer to `question` is `answer`, possibly in other words?"
EQ_OPTS = ["Yes: the sentence states this answer.", "No: the sentence does not state this answer."]
src, sp, MAX_USD = sys.argv[1], sys.argv[2], float(sys.argv[3]); DRY = "--dry" in sys.argv
PRICE_IN = 0.042e-6; CACHE = Path.home() / ".cache" / "walklab" / "ac-stop-cache.jsonl"
norm = lambda s: " ".join(re.findall(r"[a-z0-9]+", s.lower()))
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
sents = lambda p: [f"{p['title']}: {s}" for s in SPLIT.split(p["paragraph_text"].strip()) if s.strip()]
rows = [r for r in json.load(open(sp)) if "id" in r]; ids = {r["id"] for r in rows}   # the last entry is the run's usd
Q = {}
for l in open(src):
    r = json.loads(l)
    if r["id"] in ids: Q[r["id"]] = r
assert len(Q) == len(ids), "missing questions"
P = {i: sorted(Q[i]["paragraphs"], key=lambda p: p["idx"]) for i in Q}
for r in rows:   # check the index convention: hops must be the decomposition's support passages
    dec = [d["paragraph_support_idx"] for d in Q[r["id"]]["question_decomposition"]]
    assert [P[r["id"]][h]["idx"] for h in r["hops"]] == dec, r["id"]
ARMS = ("S-check", "S-state", "oracle H")
sets = {(r["id"], a): r["walk"][: (r["stop"][a] if a != "oracle H" else len(r["hops"]))] for r in rows for a in ARMS}
ctxA = lambda i, vs: {"question": Q[i]["question"], "reads": [f"{P[i][v]['title']}. {P[i][v]['paragraph_text']}" for v in vs], "task": SENT_TASK}
optA = lambda i, vs: [t for v in vs for t in sents(P[i][v])]
ck = lambda c, o: hashlib.sha256(json.dumps([c, o]).encode()).hexdigest()
cache = {}
if CACHE.exists():
    for l in open(CACHE): y = json.loads(l); cache[y["k"]] = y["p"]
spent = [0.0]
def wave(reqs, label):
    reqs = list({ck(c, o): (c, o) for c, o in reqs}.values()); miss = [(c, o) for c, o in reqs if ck(c, o) not in cache]
    est = sum(len(json.dumps(c)) / 4 + len(" ".join(o)) / 4 + 200 for c, o in miss) * PRICE_IN
    print(f"wave {label}: {len(reqs)} requests, {len(miss)} uncached, estimated ${est:.4f}")
    if DRY or not miss: return
    if spent[0] + est > MAX_USD: sys.exit("over cap")
    from percolate_core.decide import Jev, Noul
    async def go():
        async with Jev() as jev:
            return await jev.ask_many([(c, {f"p{j}": Noul(t) for j, t in enumerate(o)}) for c, o in miss])
    with open(CACHE, "a") as f:
        for (c, o), res in zip(miss, asyncio.run(go())):
            p = [res[f"p{j}"].p for j in range(len(o))]; cache[ck(c, o)] = p; spent[0] += res.input_tokens * PRICE_IN
            f.write(json.dumps({"k": ck(c, o), "p": p}) + "\n")
wave([(ctxA(i, vs), optA(i, vs)) for (i, a), vs in sets.items() if vs], "reader")
if DRY: sys.exit()
golds = {i: {norm(a) for a in [Q[i]["answer"]] + Q[i].get("answer_aliases", []) if norm(a)} for i in Q}
chosen = {}; strk = {}
for (i, a), vs in sets.items():
    o = optA(i, vs); j = int(np.argmax(cache[ck(ctxA(i, vs), o)])); chosen[i, a] = o[j]
    strk[i, a] = int(any(g in norm(o[j]) for g in golds[i]))
ctxE = lambda i, s: {"question": Q[i]["question"], "answer": Q[i]["answer"], "sentence": s, "task": EQ_TASK}
fails = [(i, a) for (i, a) in sets if not strk[i, a]]
wave([(ctxE(i, chosen[i, a]), EQ_OPTS) for i, a in fails], "judge")
ac = {k: strk[k] or int(np.argmax(cache[ck(ctxE(*k[:1], chosen[k]), EQ_OPTS)]) == 0) for k in sets}
alast = {(r["id"], a): int(r["hops"][-1] in sets[r["id"], a]) for r in rows for a in ARMS}
print(f"spend ${spent[0]:.5f}")
rng = np.random.default_rng(0)
def ci(d):
    d = np.asarray(d, float); bt = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]
    return f"{d.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]"
for a in ARMS:
    print(f"{a:8s} A-last {np.mean([alast[r['id'], a] for r in rows]):.3f}  AC {np.mean([ac[r['id'], a] for r in rows]):.3f}  "
          f"(string only {np.mean([strk[r['id'], a] for r in rows]):.3f})  returned {np.mean([len(sets[r['id'], a]) for r in rows]):.2f}")
v = lambda a, m: np.array([m[r["id"], a] for r in rows])
for a in ("S-check", "S-state"):
    print(f"AC {a} − oracle H: {ci(v(a, ac) - v('oracle H', ac))};  A-last {a} − oracle H: {ci(v(a, alast) - v('oracle H', alast))}")
    ks = [r["id"] for r in rows if not alast[r["id"], a]]
    print(f"   {a}: sets without the answer passage {len(ks)}; reader still picks the answer in {sum(ac[i, a] for i in ks)}")
print(f"AC S-state − S-check: {ci(v('S-state', ac) - v('S-check', ac))}")
json.dump({f"{i}|{a}": dict(ac=int(ac[i, a]), alast=alast[i, a], chosen=chosen[i, a]) for (i, a) in sets}, open("out/ac-stop.json", "w"))
