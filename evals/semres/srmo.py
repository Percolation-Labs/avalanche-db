"""SR-MO (REGISTERED-SRMO.md), james. Semantic inductance (1), walk momentum: does Jev's price for the next step depend
on the path so far? MuSiQue dev 3hop1 (a chain h1 -> h2 -> h3), unused by semres before this. Jev reads h2 and prices the
other 18 passages (pool minus h1, h2) with SR-J's passage task, under three histories carried as `found`, the walker's
kappa (K6: one opening sentence per earlier document; title + its first sentence here):
  none   {question, read: h2, task}
  true   + found: [K6(h1)]
  wrong  + found: [K6(lure)]; lure = the pool passage outside the gold chain with the highest bge cos to the question
Measures per question (logit p clipped to [1e-4, 1 - 1e-4]):
  pull   mean dlogit(wrong - none) over options linked to the lure but not to h2, minus the same over options linked to
         neither (linked = shares a door key, 2 <= df <= 100, not inside the question, graph-mq)
  help   top-1 h3 under true minus under none; and dlogit(true - none) of h3
  noise  stage 0 sends the none request twice, in one wave, to measure Jev's repeat spread
SET: stage0 = perm 100-103, fresh = perm 0-99 of seed 1343 over dev 3hop1 answerable.
    set -a; source ~/code/p8-subsystems/.env; set +a; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \\
    uv run --with sentence-transformers --with numpy --with 'percolate-core==0.2.15' python srmo.py MUSIQUE_DEV GRAPH_MQ SET MAX_USD"""
import asyncio, hashlib, json, re, sys
from collections import Counter
from pathlib import Path
import numpy as np

PASS_TASK = ("Each option is a passage not yet read. Having read `read`, would reading this option next give information "
             "needed to answer `question`?")   # SR-J's, unchanged
CACHE = Path.home() / ".cache" / "walklab" / "srmo-jev-cache.jsonl"
PRICE_IN = 0.042e-6
src, gpath, SET, MAX_USD = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("3hop1") and r["answerable"]]
perm = np.random.default_rng(1343).permutation(len(qs)).tolist()
pool = {"stage0": perm[100:104], "fresh": perm[:100]}[SET]
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
first = lambda p: p["title"] + ". " + re.split(r"(?<=[.!?])\s", p["paragraph_text"].strip(), maxsplit=1)[0]
wd = lambda s: set(re.findall(r"[a-z0-9]+", s.lower()))
cases = []
for qi in pool:
    r = qs[qi]; d = r["question_decomposition"]; h1, h2, h3 = (x["paragraph_support_idx"] for x in d)
    P = {p["idx"]: p for p in r["paragraphs"]}; T = {i: P[i]["title"] + ". " + P[i]["paragraph_text"] for i in P}
    out = [i for i in sorted(P) if i not in (h1, h2, h3)]
    E = m.encode([QP + r["question"]] + [T[i] for i in out], normalize_embeddings=True); lure = out[int(np.argmax(E[1:] @ E[0]))]
    opts = sorted(i for i in P if i not in (h1, h2)); qt = wd(r["question"])
    door = lambda i: {k for k in keys[hid(P[i])] if 2 <= df[k] <= 100 and not set(k.split()) <= qt}
    Dl, D2 = door(lure), door(h2)
    link = ["self" if i == lure else "h3" if i == h3 else                       # amendment 1: own classes, out of pull
            "lure" if door(i) & Dl and not door(i) & D2 else "neither" if not door(i) & (Dl | D2) else "h2" for i in opts]
    base = {"question": r["question"], "read": T[h2], "task": PASS_TASK}
    cases.append(dict(qi=int(qi), q=r["question"], texts=[T[i] for i in opts], h3=opts.index(h3), lure=opts.index(lure), link=link,
                      ctx=dict(none=base, true=base | {"found": [first(P[h1])]}, wrong=base | {"found": [first(P[lure])]})))
cache = {}
if CACHE.exists():
    for l in open(CACHE): x = json.loads(l); cache[x["k"]] = x["p"]
ck = lambda ctx, o, rep=0: hashlib.sha256(json.dumps([ctx, o, rep]).encode()).hexdigest()
reqs = [(c["ctx"][h], c["texts"], 0) for c in cases for h in ("none", "true", "wrong")]
if SET == "stage0": reqs += [(c["ctx"]["none"], c["texts"], 1) for c in cases]   # repeat, for Jev's noise floor
miss = [x for x in reqs if ck(*x) not in cache]; usd = 0.0
if miss:
    est = sum(len(json.dumps(c)) / 4 + len(" ".join(o)) / 4 + 200 for c, o, _ in miss) * PRICE_IN
    print(f"live: {len(miss)} requests, estimated ${est:.4f} (cap ${MAX_USD})", flush=True)
    if est > MAX_USD: sys.exit("estimate over cap")
    from percolate_core.decide import Jev, Noul
    async def go():
        async with Jev() as jev:   # one wave through ask_many
            return await jev.ask_many([(c, {f"p{j}": Noul(t) for j, t in enumerate(o)}) for c, o, _ in miss])
    with open(CACHE, "a") as f:
        for x, res in zip(miss, asyncio.run(go())):
            p = [res[f"p{j}"].p for j in range(len(x[1]))]; cache[ck(*x)] = p
            f.write(json.dumps({"k": ck(*x), "p": p}) + "\n"); usd += res.input_tokens * PRICE_IN
print(f"spend this run ${usd:.5f}")
lg = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))
pull, help1, helpl, wrong1, nlinks, rows_out, selfd = [], [], [], [], Counter(), [], []
for c in cases:
    L = {h: lg(np.array(cache[ck(c["ctx"][h], c["texts"])])) for h in ("none", "true", "wrong")}
    lk = np.array(c["link"]); nlinks.update(c["link"])
    if (lk == "lure").any() and (lk == "neither").any():
        dd = L["wrong"] - L["none"]; pull.append(dd[lk == "lure"].mean() - dd[lk == "neither"].mean())
    top = {h: int(np.argmax(L[h])) for h in L}
    help1.append((top["true"] == c["h3"]) - (top["none"] == c["h3"])); wrong1.append((top["wrong"] == c["h3"]) - (top["none"] == c["h3"]))
    helpl.append(L["true"][c["h3"]] - L["none"][c["h3"]]); selfd.append(L["wrong"][c["lure"]] - L["none"][c["lure"]])
    rows_out.append(dict(qi=c["qi"], top=top, h3=c["h3"], lure=c["lure"], link=c["link"]))
n = len(cases); print(f"SET={SET}: n {n}; option links {dict(nlinks)}; questions with a pull contrast {len(pull)}")
for h in ("none", "true", "wrong"): print(f"top-1 h3 under {h:5s} {np.mean([o['top'][h] == o['h3'] for o in rows_out]):.3f}")
if SET == "stage0":
    sp = [np.abs(lg(np.array(cache[ck(c['ctx']['none'], c['texts'], 1)])) - lg(np.array(cache[ck(c['ctx']['none'], c['texts'])]))).mean() for c in cases]
    print(f"noise: mean |dlogit| between two identical none requests {np.mean(sp):.3f} (per question {[round(x, 3) for x in sp]})")
    same = sum(cache[ck(c['ctx']['none'], c['texts'], 1)] == cache[ck(c['ctx']['none'], c['texts'])] for c in cases)
    print(f"identical repeat answers {same}/{n} (all identical may mean server-side caching, not zero noise)")
    print(f"pull per question {[round(x, 3) for x in pull]}; lure self dlogit {[round(x, 3) for x in selfd]}"); sys.exit()
rng = np.random.default_rng(0)
def ci(v, lab):
    v = np.array(v, float); bt = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(4000)]
    print(f"{lab}: {v.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}] (n {len(v)})")
ci(pull, "PRIMARY pull, dlogit(wrong - none) lure-linked minus neither")
ci(selfd, "dlogit of the lure itself, wrong - none (found says it was read)"); ci(help1, "top-1 h3, true - none"); ci(wrong1, "top-1 h3, wrong - none"); ci(helpl, "dlogit h3, true - none")
json.dump(dict(rows=rows_out, pull=pull, usd=usd), open(f"out/srmo-{SET}.json", "w"))
# ---- POST-HOC (added after scoring, unregistered, $0 from the cache): the general shift by class and history
for h in ("true", "wrong"):
    for cl in ("neither", "lure", "h2"):
        v = [ (lg(np.array(cache[ck(c["ctx"][h], c["texts"])])) - lg(np.array(cache[ck(c["ctx"]["none"], c["texts"])])))[np.array(c["link"]) == cl].mean()
              for c in cases if (np.array(c["link"]) == cl).any()]
        ci(v, f"post-hoc: mean dlogit ({h} - none) over {cl} options")
