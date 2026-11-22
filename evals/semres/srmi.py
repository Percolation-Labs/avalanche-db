"""SR-MI (REGISTERED-SRMI.md), bill. Semantic inductance (2), mutual inductance: does reading one parallel branch raise
Jev's price for the other branch? MuSiQue train 3hop2 (branches A, B independent; J joins them), james's train corpus
and graph. Per question, Jev reads one passage and prices every other pool passage (SR-J's passage task, unchanged):
  read A   read B   read L (control: the pool passage outside {A, B, J} nearest the question by bge cos)
Measures (logit p clipped to [1e-4, 1 - 1e-4]):
  mutual  [logit p(B | read A) − logit p(B | read L)] and [logit p(A | read B) − logit p(A | read L)], averaged per question
  series  the same for J: [logit p(J | read A) − p(J | read L)] and from B, averaged
  rank    where B (resp. A) and J sit in Jev's order after reading A (resp. B)
  vector  the same contrasts with cos(q + read, ·), bge-small, for comparison with mi_look's anti-induction
All requests in one ask_many wave. Draw: seed 1344 permutation of the corpus's answerable 3hop2; fresh = all except
stage0 = the first 4 (outside the scored set).
    set -a; source ~/code/p8-subsystems/.env; set +a; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \
    uv run --with numpy --with sentence-transformers --with 'percolate-core==0.2.15' python srmi.py TRAIN_CORPUS SET MAX_USD [--look]"""
import asyncio, hashlib, json, sys
from pathlib import Path
import numpy as np

PASS_TASK = ("Each option is a passage not yet read. Having read `read`, would reading this option next give information "
             "needed to answer `question`?")   # SR-J's, unchanged
CACHE = Path.home() / ".cache" / "walklab" / "srmi-jev-cache.jsonl"
PRICE_IN = 0.042e-6
src, SET, MAX_USD = sys.argv[1], sys.argv[2], float(sys.argv[3]); LOOK = "--look" in sys.argv
qs = [r for r in map(json.loads, open(src)) if r["id"].startswith("3hop2") and r["answerable"]]
perm = np.random.default_rng(1344).permutation(len(qs)).tolist()
pool = {"stage0": perm[:4], "fresh": perm[4:]}[SET]
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu"); QP = "Represent this sentence for searching relevant passages: "
cases = []
for qi in pool:
    r = qs[qi]; P = sorted(r["paragraphs"], key=lambda p: p["idx"]); n = len(P); ix = {p["idx"]: i for i, p in enumerate(P)}
    A, B, J = (ix[s["paragraph_support_idx"]] for s in r["question_decomposition"])
    T = [p["title"] + ". " + p["paragraph_text"] for p in P]
    E = m.encode([QP + r["question"]] + T, normalize_embeddings=True); cq = E[1:] @ E[0]
    L = max((v for v in range(n) if v not in (A, B, J)), key=lambda v: cq[v])
    vec = {rd: E[1:] @ m.encode([QP + r["question"] + " " + T[rd]], normalize_embeddings=True)[0] for rd in (A, B, L)}
    cases.append(dict(qi=int(qi), q=r["question"], T=T, n=n, A=A, B=B, J=J, L=L, vec=vec))
print(f"SET={SET}: {len(cases)} questions (3hop2)")
if LOOK:
    c = cases[0]; print(f"-- {c['q']}\n   A {c['T'][c['A']][:60]} | B {c['T'][c['B']][:60]} | L {c['T'][c['L']][:60]}"); sys.exit()
others = lambda c, rd: [v for v in range(c["n"]) if v != rd]
ctx = lambda c, rd: {"question": c["q"], "read": c["T"][rd], "task": PASS_TASK}
ck = lambda cx, o: hashlib.sha256(json.dumps([cx, o]).encode()).hexdigest()
reqs = [(ctx(c, rd), [c["T"][v] for v in others(c, rd)]) for c in cases for rd in (c["A"], c["B"], c["L"])]
cache = {}
if CACHE.exists():
    for l in open(CACHE): x = json.loads(l); cache[x["k"]] = x["p"]
miss = [x for x in reqs if ck(*x) not in cache]; usd = 0.0
if miss:
    est = sum(len(json.dumps(cx)) / 4 + len(" ".join(o)) / 4 + 200 for cx, o in miss) * PRICE_IN
    print(f"live: {len(miss)} requests, estimated ${est:.4f} (cap ${MAX_USD})", flush=True)
    if est > MAX_USD: sys.exit("estimate over cap")
    from percolate_core.decide import Jev, Noul
    async def go():
        async with Jev() as jev:
            return await jev.ask_many([(cx, {f"p{j}": Noul(t) for j, t in enumerate(o)}) for cx, o in miss])
    with open(CACHE, "a") as f:
        for (cx, o), res in zip(miss, asyncio.run(go())):
            p = [res[f"p{j}"].p for j in range(len(o))]; cache[ck(cx, o)] = p
            f.write(json.dumps({"k": ck(cx, o), "p": p}) + "\n"); usd += res.input_tokens * PRICE_IN
print(f"spend this run ${usd:.5f}")
lg = lambda p: float(np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4))))
def jev(c, rd, tgt):
    o = others(c, rd); return cache[ck(ctx(c, rd), [c["T"][v] for v in o])][o.index(tgt)]
def jrank(c, rd, tgt):
    o = others(c, rd); p = np.array(cache[ck(ctx(c, rd), [c["T"][v] for v in o])]); return int(1 + (p > p[o.index(tgt)]).sum())
def vrank(c, rd, tgt):
    s = c["vec"][rd].copy(); s[rd] = -np.inf; return int(1 + (s > s[tgt]).sum())
mutual, series, vmut, vser, rows = [], [], [], [], []
for c in cases:
    A, B, J, L = c["A"], c["B"], c["J"], c["L"]
    mutual.append(np.mean([lg(jev(c, A, B)) - lg(jev(c, L, B)), lg(jev(c, B, A)) - lg(jev(c, L, A))]))
    series.append(np.mean([lg(jev(c, A, J)) - lg(jev(c, L, J)), lg(jev(c, B, J)) - lg(jev(c, L, J))]))
    vmut.append(np.mean([c["vec"][A][B] - c["vec"][L][B], c["vec"][B][A] - c["vec"][L][A]]))
    vser.append(np.mean([c["vec"][A][J] - c["vec"][L][J], c["vec"][B][J] - c["vec"][L][J]]))
    rows.append(dict(qi=c["qi"], jr_other=[jrank(c, A, B), jrank(c, B, A)], jr_join=[jrank(c, A, J), jrank(c, B, J)],
                     jr_other_ctrl=[jrank(c, L, B), jrank(c, L, A)], jr_join_ctrl=[jrank(c, L, J)] * 2,
                     vr_other=[vrank(c, A, B), vrank(c, B, A)], vr_join=[vrank(c, A, J), vrank(c, B, J)]))
n = len(cases)
for k, lab in (("jr_other", "Jev, other branch after reading a branch"), ("jr_other_ctrl", "Jev, that branch after reading L"),
               ("jr_join", "Jev, join after reading a branch"), ("jr_join_ctrl", "Jev, join after reading L"),
               ("vr_other", "cos(q+read), other branch"), ("vr_join", "cos(q+read), join")):
    v = np.array([x for o in rows for x in o[k]]); print(f"{lab:42s} median rank {np.median(v):.0f}, top-1 {np.mean(v == 1):.3f}")
if SET == "fresh":
    rng = np.random.default_rng(0)
    def ci(v, lab):
        v = np.array(v, float); bt = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(4000)]
        print(f"{lab}: {v.mean():+.3f} [{np.percentile(bt, 2.5):+.3f}, {np.percentile(bt, 97.5):+.3f}] (n {len(v)})")
    ci(mutual, "PRIMARY mutual, dlogit p(other branch): read branch − read L")
    ci(series, "series, dlogit p(J): read branch − read L")
    ci(np.array(series) - np.array(mutual), "series − mutual")
    ci(vmut, "vector mutual, dcos(other branch): read branch − read L")
    ci(vser, "vector series, dcos(J): read branch − read L")
json.dump(dict(usd=usd, mutual=list(map(float, mutual)), series=list(map(float, series)), rows=rows), open(f"out/srmi-{SET}.json", "w"))
