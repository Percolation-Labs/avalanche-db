"""SR-MO3 (REGISTERED-SRMO3.md), james. Kappa on BEAM, at one step: does question-related history narrow the gold's lead
more on BEAM than on MuSiQue (SR-MO, SR-MO2), the step-level mechanism for kappa's BEAM loss (kappa round 5: K7 −.022)?
BEAM 1M fixture (~/.cache/walklab/fixture-1M), all conversations (DEV and HELD-OUT), recorded search order.
Per question: read = the first gold message in search order; options = the next 19 messages in search order (gold and
not); questions need at least one unread gold and one non-gold option. Jev prices the options with SR-J's task.
Histories, as kappa's `found` (K6: the message's first sentence):
  none, none2 (identical repeat: noise floor)
  true        K6 of the second gold message in search order (a right but partial history; excluded as `self` if an option)
  related     K6 of search's top non-gold message other than the read (the question-nearest lure; SR-MO's rule in search's terms)
  irrelevant  K6 of the read message of the next usable question from a different conversation
Measures (logit p clipped to [1e-4, 1 - 1e-4]); `self` = the related and true messages themselves if they are options, excluded:
  lead(h)   mean dlogit (h − none) over unread gold options minus the same over non-gold options
  shift(h)  mean dlogit (h − none) over non-gold options
  rho(h)    Spearman over options between word overlap with found's sentence and dlogit (h − none) (round 5's statistic)
  top-1 gold under each history; flips against none, with none2 as the floor
    set -a; source ~/code/p8-subsystems/.env; set +a; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \\
    uv run --with numpy --with scipy --with 'percolate-core==0.2.15' python srmo3.py FIXTURE_DIR SET MAX_USD    (SET: stage0 | fresh)"""
import asyncio, hashlib, json, re, sys
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr

PASS_TASK = ("Each option is a passage not yet read. Having read `read`, would reading this option next give information "
             "needed to answer `question`?")   # SR-J's, unchanged
CACHE = Path.home() / ".cache" / "walklab" / "srmo3-jev-cache.jsonl"
PRICE_IN = 0.042e-6
H = ("none", "true", "related", "irrelevant")
fx, SET, MAX_USD = Path(sys.argv[1]), sys.argv[2], float(sys.argv[3])
items = [json.loads(l) for l in open(fx / "items.jsonl")]
order = {json.loads(l)["qid"]: json.loads(l)["order"] for l in open(fx / "search.jsonl")}
said = {d["uri"]: d["said"] for d in map(json.loads, open(fx / "docs.jsonl"))}
conv = lambda q: int(q.split(":")[1])
first = lambda u: re.split(r"(?<=[.!?])\s", said[u].strip(), maxsplit=1)[0]
wd = lambda s: set(re.findall(r"[a-z0-9]+", s.lower()))
U = []
for it in items:   # the usable DEV questions, in file order
    o, g = order[it["qid"]], set(it["gold"]); fg = [d for d in o if d in g]
    if not fg: continue
    if len(fg) < 2: continue
    rd, tru = fg[0], fg[1]; opts = [d for d in o if d != rd][:19]
    rel = next(d for d in o if d not in g and d != rd)
    if not any(d in g and d != tru for d in opts) or all(d in g for d in opts): continue
    U.append(dict(qid=it["qid"], q=it["question"], rd=rd, opts=opts, gold=[d in g for d in opts], rel=rel, tru=tru))
for j, u in enumerate(U):   # irrelevant: the next usable question's read, from a different conversation
    nx = next(v for v in U[j + 1:] + U[:j] if conv(v["qid"]) != conv(u["qid"])); u["irr"] = nx["rd"]
pool = {"stage0": U[:4], "fresh": U[4:]}[SET]
print(f"usable questions {len(U)}")
for u in pool:
    base = {"question": u["q"], "read": said[u["rd"]], "task": PASS_TASK}
    u["ctx"] = dict(none=base, true=base | {"found": [first(u["tru"])]}, related=base | {"found": [first(u["rel"])]}, irrelevant=base | {"found": [first(u["irr"])]})
    u["texts"] = [said[d] for d in u["opts"]]
cache = {}
if CACHE.exists():
    for l in open(CACHE): x = json.loads(l); cache[x["k"]] = x["p"]
ck = lambda ctx, o, rep=0: hashlib.sha256(json.dumps([ctx, o, rep]).encode()).hexdigest()
reqs = [(u["ctx"][h], u["texts"], 0) for u in pool for h in H] + [(u["ctx"]["none"], u["texts"], 1) for u in pool]
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
lead = {h: [] for h in H[1:]}; shift = {h: [] for h in H[1:]}; rho = {h: [] for h in H[1:]}; top = {h: [] for h in H + ("none2",)}
for u in pool:
    L = {h: lg(np.array(cache[ck(u["ctx"][h], u["texts"])])) for h in H}; L["none2"] = lg(np.array(cache[ck(u["ctx"]["none"], u["texts"], 1)]))
    g = np.array(u["gold"]); keep = np.array([d not in (u["rel"], u["tru"]) for d in u["opts"]])
    for h in top: top[h].append(int(g[int(np.argmax(L[h]))]))
    for h in H[1:]:
        dd = L[h] - L["none"]; fw = wd(u["ctx"][h]["found"][0])
        lead[h].append(float(dd[g & keep].mean() - dd[~g & keep].mean())); shift[h].append(float(dd[~g & keep].mean()))
        ov = np.array([len(fw & wd(t)) / max(1, len(wd(t))) for t in u["texts"]])
        r = spearmanr(ov[keep], dd[keep]).statistic
        if np.isfinite(r): rho[h].append(float(r))
n = len(pool); print(f"SET={SET}: n {n} (usable DEV questions {len(U)})")
for h in top:
    lost = sum(a and not b for a, b in zip(top["none"], top[h])); gained = sum(b and not a for a, b in zip(top["none"], top[h]))
    print(f"top-1 gold under {h:10s} {np.mean(top[h]):.3f}" + ("" if h == "none" else f"  (lost {lost}, gained {gained})"))
if SET == "stage0":
    for h in H[1:]: print(f"{h}: lead {[round(x, 3) for x in lead[h]]}, shift {[round(x, 3) for x in shift[h]]}, rho {[round(x, 3) for x in rho[h]]}")
    sys.exit()
rng = np.random.default_rng(0)
def ci(v, lab):
    v = np.array(v, float); bt = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(4000)]
    print(f"{lab}: {v.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}] (n {len(v)})")
ci(lead["related"], "PRIMARY lead(related): dlogit gold minus non-gold")
ci(lead["true"], "lead(true)"); ci(np.array(lead["related"]) - np.array(lead["true"]), "lead(related) − lead(true)"); ci(lead["irrelevant"], "lead(irrelevant)"); ci(shift["true"], "shift(true) over non-gold"); ci(shift["related"], "shift(related) over non-gold"); ci(shift["irrelevant"], "shift(irrelevant) over non-gold")
ci(rho["related"], "rho(related): Spearman(overlap with found, dlogit)"); ci(rho["true"], "rho(true)"); ci(rho["irrelevant"], "rho(irrelevant)")
for h in ("true", "related", "irrelevant", "none2"): ci(np.array(top[h]) - np.array(top["none"]), f"top-1 gold, {h} − none")
json.dump(dict(lead=lead, shift=shift, rho=rho, top=top, usd=usd), open(f"out/srmo3-{SET}.json", "w"))
