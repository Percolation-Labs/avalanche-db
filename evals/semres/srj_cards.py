"""SR-J amendment 3 (REGISTERED-SRJ.md): the same Jev fit on our cards. Read = the card's text, options = its gold commits
(up to 3) + the commits most like the question that aren't gold (to 19), cos by bge-small. $0 look with --look.
    srj_cards.py DT_CARDS FIXTURE_DOCS N MAX_USD [--look]"""
import asyncio, json, sys, hashlib
from pathlib import Path
import numpy as np

TASK = ("Each option is a passage not yet read. Having read `read`, would reading this option next give information "
        "needed to answer `question`?")
CACHE = Path.home() / ".cache" / "walklab" / "srj-jev-cache.jsonl"
PRICE_IN = 0.042e-6
QP = "Represent this sentence for searching relevant passages: "


def main():
    dt, fx, N, max_usd = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]); look = "--look" in sys.argv
    docs = {}
    for l in open(fx):
        r = json.loads(l); docs[r["uri"]] = (r["title"] + ". " + (r["said"] or ""))[:1500]
    commits = [u for u in docs if u.startswith("commit:")]
    full = {}
    for u in commits: full.setdefault("commit/" + u[7:17], u)
    rows = [json.loads(l) for l in open(dt)]
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")
    embp = Path.home() / ".cache" / "walklab" / "srj-commits-bge.npy"
    if embp.exists(): EC = np.load(embp)
    else: EC = m.encode([docs[u] for u in commits], normalize_embeddings=True, batch_size=64); np.save(embp, EC)
    cases = []
    for r in rows:
        card = "file:board/cards/" + r["qid"].split(":", 1)[1] + ".md"
        gold = [full[g] for g in r["gold"] if g in full][:3]
        if card not in docs or not gold: continue
        eq = m.encode([QP + r["question"]], normalize_embeddings=True)[0]; er = m.encode([docs[card]], normalize_embeddings=True)[0]
        cq = EC @ eq; order = np.argsort(-cq); gs = set(gold)
        dis = [commits[i] for i in order if commits[i] not in gs][:19 - len(gold)]
        opts = sorted(gold + dis); idx = {u: i for i, u in enumerate(commits)}
        cases.append(dict(id=r["qid"], q=r["question"], read=docs[card], opts=opts, texts=[docs[u] for u in opts],
                          cos=[float(cq[idx[u]]) for u in opts], cos_r=[float(EC[idx[u]] @ er) for u in opts], g=[int(u in gs) for u in opts]))
        if len(cases) == (200 if look else N): break
    X = np.array([x for c in cases for x in c["cos"]]); XR = np.array([x for c in cases for x in c["cos_r"]]); Gd = np.array([x for c in cases for x in c["g"]])
    from sklearn.linear_model import LogisticRegression
    bq = LogisticRegression(C=1e6).fit(X[:, None], Gd).coef_[0][0]; br = LogisticRegression(C=1e6).fit(XR[:, None], Gd).coef_[0][0]
    gm = lambda a: (np.mean(a[Gd == 1]), np.mean(a[Gd == 0]))
    print(f"{len(cases)} cards, {len(X)} options, {Gd.sum()} gold; vectors' Bayes slope on cos_q {bq:.2f}, on cos_r {br:.2f}; "
          f"cos_q gold/other {gm(X)[0]:.3f}/{gm(X)[1]:.3f}, cos_r {gm(XR)[0]:.3f}/{gm(XR)[1]:.3f}")
    if look: return
    cache = {}
    if CACHE.exists():
        for l in open(CACHE): x = json.loads(l); cache[x["k"]] = x["p"]
    key = lambda c: hashlib.sha256(json.dumps([c["q"], c["read"], c["texts"], TASK]).encode()).hexdigest()
    miss = [c for c in cases if key(c) not in cache]; usd = 0.0
    if miss:
        est = sum(len(" ".join(c["texts"])) / 4 + 400 for c in miss) * PRICE_IN
        print(f"live: {len(miss)} requests, estimated ${est:.4f} (cap ${max_usd})", flush=True)
        if est > max_usd: sys.exit("estimate over cap")
        from percolate_core.decide import Jev, Noul
        async def go():
            async with Jev() as jev:
                return await asyncio.gather(*(jev.ask({"question": c["q"], "read": c["read"], "task": TASK},
                                                      {f"p{j}": Noul(t) for j, t in enumerate(c["texts"])}) for c in miss))
        f = open(CACHE, "a")
        for c, r in zip(miss, asyncio.run(go())):
            p = [r[f"p{j}"].p for j in range(len(c["texts"]))]; cache[key(c)] = p
            f.write(json.dumps({"k": key(c), "p": p}) + "\n"); usd += r.input_tokens * PRICE_IN
        f.close()
    print(f"spend this run ${usd:.5f}")
    Y, Q = [], []; rng = np.random.default_rng(0); top = {k: [] for k in ("coin", "search cos", "cos read", "Jev")}
    for qi, c in enumerate(cases):
        p = np.clip(np.array(cache[key(c)]), 1e-4, 1 - 1e-4); Y += list(np.log(p / (1 - p))); Q += [qi] * len(p); g = np.array(c["g"])
        for k, s in (("coin", rng.random(len(p))), ("search cos", np.array(c["cos"])), ("cos read", np.array(c["cos_r"])), ("Jev", p)):
            top[k].append(int(g[np.argmax(s)] == 1))
        if N <= 4: print(f"-- {c['id']}: Jev p gold {np.round(p[g == 1], 2)}, max other {np.max(p[g == 0]):.2f}; cos gold {np.round(np.array(c['cos'])[g == 1], 3)}, max other {np.max(np.array(c['cos'])[g == 0]):.3f}")
    Y, Q = np.array(Y), np.array(Q); nq = len(cases); byq = [np.nonzero(Q == i)[0] for i in range(nq)]
    def fit(ix, cols): return np.linalg.lstsq(np.c_[tuple(v[ix] for v in cols) + (np.ones(len(ix)),)], Y[ix], rcond=None)[0]
    for name, cols in (("cos_q + gold", (X, Gd)), ("cos_q + cos_r + gold", (X, XR, Gd))):
        f = fit(np.arange(len(Y)), cols); B = [fit(np.concatenate([byq[i] for i in rng.integers(0, nq, nq)]), cols) for _ in range(2000)]
        lo, hi = np.percentile(B, [2.5, 97.5], 0)
        print(f"{name:22s} " + ", ".join(f"{k} {f[i]:+.2f} [{lo[i]:+.2f}, {hi[i]:+.2f}]" for i, k in enumerate(name.split(" + "))))
    print("top-1 is gold: " + ", ".join(f"{k} {np.mean(v):.2f}" for k, v in top.items()))
    json.dump(dict(usd=usd, cases=[{k: v for k, v in c.items() if k != "texts"} | {"p": cache[key(c)]} for c in cases]), open(f"out/srj-cards-n{N}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
