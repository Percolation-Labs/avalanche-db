"""SR-MO2 (REGISTERED-SRMO2.md), james. Kappa's mechanism: SR-MO found that any `found` raised every option's price by
about +.3 logit. Is that history (content) or format (the request carries extra context)? And does it flip choices?
Same task as SR-MO: MuSiQue dev 3hop1 answerable; Jev reads h2 and prices the other 18 pool passages (SR-J's task).
Histories, carried as kappa's `found` (K6: title + first sentence):
  none        {question, read: h2, task}
  true        + found: [K6(h1)]
  wrong       + found: [K6(lure)]; lure = the non-chain pool passage nearest the question by bge cos (SR-MO's rule)
  irrelevant  + found: [K6(h1 of the next question in the draw's order)]; a real hop-1 sentence about something else
Measures (logit p clipped to [1e-4, 1 - 1e-4]):
  shift(h)  per question, the mean dlogit (h - none) over "neither" options (no door key shared with h2, the lure, or the
            irrelevant passage; not h3, not the lure). The common mode.
  top-1 h3 per history; flips against none: h3 first under none and not under h (lost), and the reverse (gained).
SET: stage0 = perm 304-307; every question also gets a repeat of none (amendment 1), fresh = perm 104-303 of seed 1343 (SR-MO's 0-99 and 100-103 excluded).
    set -a; source ~/code/p8-subsystems/.env; set +a; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \\
    uv run --with sentence-transformers --with numpy --with 'percolate-core==0.2.15' python srmo2.py MUSIQUE_DEV GRAPH_MQ SET MAX_USD"""
import asyncio, hashlib, json, re, sys
from collections import Counter
from pathlib import Path
import numpy as np

PASS_TASK = ("Each option is a passage not yet read. Having read `read`, would reading this option next give information "
             "needed to answer `question`?")   # SR-J's, unchanged
CACHE = Path.home() / ".cache" / "walklab" / "srmo-jev-cache.jsonl"   # shared with SR-MO (same key format)
PRICE_IN = 0.042e-6
H = ("none", "true", "wrong", "irrelevant")
src, gpath, SET, MAX_USD = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
rows = [json.loads(l) for l in open(gpath)]; keys = {r["d"]: set(r["keys"]) for r in rows}
df = Counter(k for r in rows for k in r["keys"])
hid = lambda p: "mq:" + hashlib.sha256((p["title"] + "\n" + p["paragraph_text"]).encode()).hexdigest()[:16]
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("3hop1") and r["answerable"]]
perm = np.random.default_rng(1343).permutation(len(qs)).tolist()
pool = {"stage0": perm[304:308], "fresh": perm[104:304]}[SET]
nxt = {qi: perm[(perm.index(qi) + 1) % len(perm)] for qi in pool}   # the next question in the draw's order
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
    rn = qs[nxt[qi]]; pn = {p["idx"]: p for p in rn["paragraphs"]}[rn["question_decomposition"][0]["paragraph_support_idx"]]
    opts = sorted(i for i in P if i not in (h1, h2)); qt = wd(r["question"])
    door = lambda p: {k for k in keys.get(hid(p), ()) if 2 <= df[k] <= 100 and not set(k.split()) <= qt}
    near = door(P[h2]) | door(P[lure]) | door(pn)
    neither = [j for j, i in enumerate(opts) if i not in (h3, lure) and not door(P[i]) & near]
    base = {"question": r["question"], "read": T[h2], "task": PASS_TASK}
    cases.append(dict(qi=int(qi), texts=[T[i] for i in opts], h3=opts.index(h3), neither=neither,
                      ctx=dict(none=base, true=base | {"found": [first(P[h1])]}, wrong=base | {"found": [first(P[lure])]},
                               irrelevant=base | {"found": [first(pn)]})))
cache = {}
if CACHE.exists():
    for l in open(CACHE): x = json.loads(l); cache[x["k"]] = x["p"]
ck = lambda ctx, o, rep=0: hashlib.sha256(json.dumps([ctx, o, rep]).encode()).hexdigest()
reqs = [(c["ctx"][h], c["texts"], 0) for c in cases for h in H]
reqs += [(c["ctx"]["none"], c["texts"], 1) for c in cases]   # amendment 1: a repeat of none on every question (noise floor for flips)
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
shift = {h: [] for h in H[1:]}; top = {h: [] for h in H}; out = []; top["none2"] = []
for c in cases:
    L = {h: lg(np.array(cache[ck(c["ctx"][h], c["texts"])])) for h in H}
    for h in H: top[h].append(int(np.argmax(L[h]) == c["h3"]))
    top["none2"].append(int(np.argmax(lg(np.array(cache[ck(c["ctx"]["none"], c["texts"], 1)]))) == c["h3"]))
    if c["neither"]:
        for h in H[1:]: shift[h].append(float((L[h] - L["none"])[c["neither"]].mean()))
    out.append(dict(qi=c["qi"], top={h: top[h][-1] for h in H}, nneither=len(c["neither"])))
n = len(cases); print(f"SET={SET}: n {n}; questions with neither options {len(shift['true'])}, median count {np.median([o['nneither'] for o in out]):.0f}")
for h in H: print(f"top-1 h3 under {h:10s} {np.mean(top[h]):.3f}")
for h in H[1:] + ("none2",):
    lost = sum(a and not b for a, b in zip(top["none"], top[h])); gained = sum(b and not a for a, b in zip(top["none"], top[h]))
    print(f"flips {h:10s} vs none: lost {lost}, gained {gained}")
if SET == "stage0":
    sp = [np.abs(lg(np.array(cache[ck(c['ctx']['none'], c['texts'], 1)])) - lg(np.array(cache[ck(c['ctx']['none'], c['texts'])]))).mean() for c in cases]
    print(f"noise: mean |dlogit| between two identical none requests {np.mean(sp):.3f}")
    for h in H[1:]: print(f"shift {h:10s} per question {[round(x, 3) for x in shift[h]]}")
    sys.exit()
rng = np.random.default_rng(0)
def ci(v, lab):
    v = np.array(v, float); bt = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(4000)]
    print(f"{lab}: {v.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}] (n {len(v)})")
ci(shift["irrelevant"], "PRIMARY shift(irrelevant - none) over neither options")
for h in ("true", "wrong"): ci(shift[h], f"shift({h} - none)")
ci(np.array(shift["true"]) - np.array(shift["irrelevant"]), "shift(true) - shift(irrelevant)")
ci(np.array(shift["wrong"]) - np.array(shift["irrelevant"]), "shift(wrong) - shift(irrelevant)")
for h in H[1:] + ("none2",): ci(np.array(top[h]) - np.array(top["none"]), f"top-1 h3, {h} - none")
json.dump(dict(out=out, shift=shift, usd=usd), open(f"out/srmo2-{SET}.json", "w"))
