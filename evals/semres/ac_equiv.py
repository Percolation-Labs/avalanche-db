"""AC scoring fix, look (bill, 22 Nov). AC's string check (gold or alias contained in the chosen sentence, after norm())
misses answers stated in another form (SR-AC's hand reads: 'Thambidurai' for 'M. Thambidurai'; SR-BF: 'Salt Lake
City' for 'Salt Lake City metropolitan area'). Fix without a threshold: when the string check fails, Jev judges, by
argmax over two options, whether the chosen sentence states the gold answer. Run here on SR-AC's 600 cached decisions
(out/srac-fresh.json); only the string-check failures are sent. The 20 hand-read failures in RESULT-SRAC.md are the
check on the judge.
    set -a; source ~/code/p8-subsystems/.env; set +a; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \\
    uv run --with numpy --with 'percolate-core==0.2.15' python ac_equiv.py TRAIN_CORPUS MAX_USD [--dry]"""
import asyncio, hashlib, json, sys
from pathlib import Path
import numpy as np
EQ_TASK = "Does `sentence` state that the answer to `question` is `answer`, possibly in other words?"
EQ_OPTS = ["Yes: the sentence states this answer.", "No: the sentence does not state this answer."]
src, MAX_USD = sys.argv[1], float(sys.argv[2]); DRY = "--dry" in sys.argv
PRICE_IN = 0.042e-6; CACHE = Path.home() / ".cache" / "walklab" / "ac-equiv-cache.jsonl"
Q = {r["id"]: r for r in map(json.loads, open(src))}
d = json.load(open(sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "out/srac-fresh.json"))["out"]
fails = [(o["id"], a, o[a]["chosen"]) for o in d for a in ("G", "L", "LR", "R") if o[a]["ac"] == 0]
ctx = lambda i, sent: {"question": Q[i]["question"], "answer": Q[i]["answer"], "sentence": sent, "task": EQ_TASK}
ck = lambda c: hashlib.sha256(json.dumps([c, EQ_OPTS]).encode()).hexdigest()
cache = {}
if CACHE.exists():
    for l in open(CACHE): y = json.loads(l); cache[y["k"]] = y["p"]
reqs = list({ck(ctx(i, s)): ctx(i, s) for i, _, s in fails}.values()); miss = [c for c in reqs if ck(c) not in cache]
est = sum(len(json.dumps(c)) / 4 + 60 for c in miss) * PRICE_IN
print(f"{len(fails)} string-check failures; {len(reqs)} distinct requests, {len(miss)} uncached, estimated ${est:.4f}")
spent = 0.0
if DRY: sys.exit()
if miss:
    if est > MAX_USD: sys.exit("over cap")
    from percolate_core.decide import Jev, Noul
    async def go():
        async with Jev() as jev:
            return await jev.ask_many([(c, {f"p{j}": Noul(t) for j, t in enumerate(EQ_OPTS)}) for c in miss])
    with open(CACHE, "a") as f:
        for c, res in zip(miss, asyncio.run(go())):
            p = [res[f"p{j}"].p for j in range(2)]; cache[ck(c)] = p; spent += res.input_tokens * PRICE_IN
            f.write(json.dumps({"k": ck(c), "p": p}) + "\n")
print(f"spend ${spent:.5f}")
yes = {(i, a): int(np.argmax(cache[ck(ctx(i, s))]) == 0) for i, a, s in fails}
for a in ("G", "L", "LR", "R"):
    n = len(d); base = sum(o[a]["ac"] for o in d); add = sum(v for (i, aa), v in yes.items() if aa == a)
    print(f"{a}: AC string {base/n:.3f} -> with judge {(base+add)/n:.3f} (+{add})")
g = lambda arm: np.array([o[arm]["ac"] + yes.get((o["id"], arm), 0) for o in d])
rng = np.random.default_rng(0); dd = g("G") - g("L"); bt = [dd[rng.integers(0, len(dd), len(dd))].mean() for _ in range(4000)]
print(f"AC(G) − AC(L) with judge: {dd.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}]")
print("judge on the first 20 failures (the hand-read set, same order as RESULT-SRAC.md):")
k = 0
for o in d:
    for a in ("G", "L", "LR"):
        if o[a]["ac"] == 0 and k < 20:
            k += 1; print(f"  {k:2d} {a:2s} judge={'yes' if yes[(o['id'], a)] else 'no '} | {Q[o['id']]['answer'][:40]} | {o[a]['chosen'][:90]}")
