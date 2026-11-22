"""SR-AC (REGISTERED-SRAC.md), bill. Validates AC, the reader's-choice measure of 'the answer is in what the walk returns'
(Sirsh 17:07Z). AC request: context = question + the full text of every returned passage (title-prefixed, in set
order); options = every sentence of those passages, each prefixed with its passage title, in passage then sentence
order; task SENT_TASK; argmax (ties to the earlier option) is the reader's choice. AC = 1 if the chosen option contains
the gold answer or an alias after norm(). A-last = the set contains the gold last-hop passage.
Fixed sets per question: G (every hop passage), L (the last-hop passage alone), LR (L + random non-hop pool passages up
to the chain's size), R (random non-hop pool passages, the chain's size). Random picks are seeded by sha256(id + arm).
Draw: MuSiQue train answerable 2hop, 3hop1, 4hop1, PER each, SEED 1346, excluding every question SR-BX, SR-BE, SR-BH
and SR-BS used.
    set -a; source ~/code/p8-subsystems/.env; set +a; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \\
    uv run --with numpy --with 'percolate-core==0.2.15' python srac.py TRAIN_CORPUS SET MAX_USD [--dry]"""
import asyncio, hashlib, json, re, sys
from pathlib import Path
import numpy as np

SENT_TASK = "Each option is a sentence from `reads`. Which sentence states the answer to `question`?"
SEED, PER, TYPES = 1346, 50, ("2hop", "3hop1", "4hop1")
CACHE = Path.home() / ".cache" / "walklab" / "srac-jev-cache.jsonl"
PRICE_IN = 0.042e-6
src, SET, MAX_USD = sys.argv[1], sys.argv[2], float(sys.argv[3]); DRY = "--dry" in sys.argv
norm = lambda s: " ".join(re.findall(r"[a-z0-9]+", s.lower()))
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")   # sentence boundary: end punctuation, space, capital/digit/quote/paren
PYSBD = "--pysbd" in sys.argv   # AC splitter fix (NOTE-AC-SPLIT.md): a standard segmenter instead of the regex
if PYSBD:
    import pysbd
    _seg = pysbd.Segmenter(language="en", clean=False)
    _split = lambda t: [x.strip() for x in _seg.segment(t)]
else:
    _split = lambda t: SPLIT.split(t)
sents = lambda p: [f"{p['title']}: {s}" for s in _split(p["paragraph_text"].strip()) if s.strip()]
allq = [r for r in map(json.loads, open(src)) if r["answerable"]]
bytype = {t: [r for r in allq if r["id"].split("__")[0] == t] for t in TYPES}
used = {bytype["2hop"][i]["id"] for i in np.random.default_rng(1341).permutation(len(bytype["2hop"]))[:608]}
for t in ("3hop1", "4hop1"):
    used |= {bytype[t][i]["id"] for i in np.random.default_rng(1344).permutation(len(bytype[t]))[:102]}
for t in TYPES:   # SR-BS: seed 1345 over the questions not used before it, positions 0-81
    fr = [r for r in bytype[t] if r["id"] not in used]
    used |= {fr[i]["id"] for i in np.random.default_rng(1345).permutation(len(fr))[:82]}
draw = []
for t in TYPES:
    fresh = [r for r in bytype[t] if r["id"] not in used]
    perm = np.random.default_rng(SEED).permutation(len(fresh))
    draw += [fresh[i] for i in {"stage0": perm[PER:PER + 2], "fresh": perm[:PER]}[SET]]
assert not {r["id"] for r in draw} & used
def pick(r, arm, pool, k):
    rng = np.random.default_rng(int(hashlib.sha256((r["id"] + arm).encode()).hexdigest()[:8], 16))
    return [pool[i] for i in rng.permutation(len(pool))[:k]]
SETS = ("G", "L", "LR", "R")
Q = []
for r in draw:
    P = {p["idx"]: p for p in r["paragraphs"]}; hops = [P[d["paragraph_support_idx"]] for d in r["question_decomposition"]]
    hop_idx = {p["idx"] for p in hops}; non = [p for p in sorted(r["paragraphs"], key=lambda p: p["idx"]) if p["idx"] not in hop_idx]
    last = hops[-1]; H = len(hops)
    S = {"G": hops, "L": [last], "LR": [last] + pick(r, "LR", non, H - 1), "R": pick(r, "R", non, H)}
    golds = {norm(a) for a in [r["answer"]] + r.get("answer_aliases", []) if norm(a)}
    Q.append(dict(id=r["id"], t=r["id"].split("__")[0], q=r["question"], golds=golds, S=S, last=last["idx"]))
ctx = lambda x, ps: {"question": x["q"], "reads": [f"{p['title']}. {p['paragraph_text']}" for p in ps], "task": SENT_TASK}
opts = lambda ps: [s for p in ps for s in sents(p)]
cache = {}
if CACHE.exists():
    for l in open(CACHE): y = json.loads(l); cache[y["k"]] = y["p"]
ck = lambda c, o: hashlib.sha256(json.dumps([c, o]).encode()).hexdigest()
spent = [0.0]
reqs = list({ck(c, o): (c, o) for c, o in ((ctx(x, x["S"][a]), opts(x["S"][a])) for x in Q for a in SETS)}.values())
miss = [(c, o) for c, o in reqs if ck(c, o) not in cache]
est = sum(len(json.dumps(c)) / 4 + len(" ".join(o)) / 4 + 200 for c, o in miss) * PRICE_IN
print(f"SET={SET}: {len(Q)} questions; {len(reqs)} requests, {len(miss)} uncached, estimated ${est:.4f} (cap ${MAX_USD}); "
      f"options per request median {np.median([len(o) for _, o in reqs]):.0f}")
if DRY:
    rng = np.random.default_rng(0)
    for c, o in miss: cache[ck(c, o)] = rng.random(len(o)).tolist()
elif miss:
    if est > MAX_USD: sys.exit("estimate over cap")
    from percolate_core.decide import Jev, Noul
    async def go():
        async with Jev() as jev:
            return await jev.ask_many([(c, {f"p{j}": Noul(t) for j, t in enumerate(o)}) for c, o in miss])
    with open(CACHE, "a") as f:
        for (c, o), res in zip(miss, asyncio.run(go())):
            p = [res[f"p{j}"].p for j in range(len(o))]; cache[ck(c, o)] = p
            f.write(json.dumps({"k": ck(c, o), "p": p}) + "\n"); spent[0] += res.input_tokens * PRICE_IN
print(f"spend this run ${spent[0]:.5f}")
out = []
for x in Q:
    rec = dict(id=x["id"], t=x["t"])
    for a in SETS:
        ps = x["S"][a]; o = opts(ps); p = cache[ck(ctx(x, ps), o)]; j = int(np.argmax(p))   # argmax: ties to the earlier option
        rec[a] = dict(ac=int(any(g in norm(o[j]) for g in x["golds"])), alast=int(any(q["idx"] == x["last"] for q in ps)),
                      str=int(any(g in norm(" ".join(f"{q['title']} {q['paragraph_text']}" for q in ps)) for g in x["golds"])),
                      chosen=o[j])
    out.append(rec)
rng = np.random.default_rng(0)
def ci(d):
    d = np.asarray(d, float); bt = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]
    return f"{d.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]"
for t in TYPES + ("all",):
    sub = [o for o in out if t in ("all", o["t"])]
    print(f"{t:6s} n {len(sub):3d}  AC " + "  ".join(f"{a} {np.mean([o[a]['ac'] for o in sub]):.3f}" for a in SETS)
          + "   string " + "  ".join(f"{a} {np.mean([o[a]['str'] for o in sub]):.3f}" for a in SETS))
print(f"PRIMARY: AC(G) − AC(L), the bridge's worth to a reader: {ci([o['G']['ac'] - o['L']['ac'] for o in out])}")
for t in TYPES:
    sub = [o for o in out if o["t"] == t]; print(f"   {t}: {ci([o['G']['ac'] - o['L']['ac'] for o in sub])}")
print(f"AC(LR) − AC(L), noise without the bridge: {ci([o['LR']['ac'] - o['L']['ac'] for o in out])}")
print(f"AC(G) − AC(R), the measure's range: {ci([o['G']['ac'] - o['R']['ac'] for o in out])}")
ag = [(o[a]["alast"], o[a]["ac"]) for o in out for a in SETS]
print("A-last × AC over all sets: " + ", ".join(f"A-last {i} AC {j}: {sum(1 for x in ag if x == (i, j))}" for i in (1, 0) for j in (1, 0)))
json.dump(dict(usd=spent[0], out=out), open(f"out/srac-{SET}{'-pysbd' if PYSBD else ''}.json", "w"))
