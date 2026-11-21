"""SR-J (REGISTERED-SRJ.md), bill: Jev's semantic conductance against the vectors'. Stage 0: 4 MuSiQue 2-hop dev questions.
Jev reads the question, with the hop-1 passage as already read, and scores each of the 19 other passages (one batched
request per question, all in flight together). Fit logit p_Jev = β_J·cos + γ·[hop 2] + c, where cos is bge-small's
cos(question, passage), and compare β_J with the vectors' Bayes slope β_B (srj_look.py: 8.7 on 200 dev questions).
Controls on the rank of hop 2 among the 19: chance, coin, word overlap (question + read), search cos, oracle.
    source ~/code/p8-subsystems/.env; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \\
    uv run --with sentence-transformers --with scikit-learn --with 'percolate-core==0.2.15' python srj.py MUSIQUE_DEV N MAX_USD"""
import asyncio, json, re, sys, hashlib
from pathlib import Path
import numpy as np

TASK = ("Each option is a passage not yet read. Having read `read`, would reading this option next give information "
        "needed to answer `question`?")
CACHE = Path.home() / ".cache" / "walklab" / "srj-jev-cache.jsonl"
PRICE_IN = 0.042e-6
WORD = re.compile(r"[a-z0-9]+")


def words(t): return set(WORD.findall(t.lower())) - {"the", "a", "an", "of", "in", "on", "and", "is", "was", "to", "for", "by", "at", "who", "what", "which", "where", "when"}


def main():
    src, N, max_usd = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
    rows = [json.loads(l) for l in open(src)]
    rows = [r for r in rows if r["id"].startswith("2hop") and r["answerable"]][:N]
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")
    cases = []
    for r in rows:
        d = r["question_decomposition"]; h1, h2 = d[0]["paragraph_support_idx"], d[1]["paragraph_support_idx"]
        P = {p["idx"]: p["title"] + ". " + p["paragraph_text"] for p in r["paragraphs"]}
        opts = sorted(i for i in P if i != h1)
        E = m.encode(["Represent this sentence for searching relevant passages: " + r["question"]] + [P[i] for i in opts], normalize_embeddings=True)
        cos = (E[1:] @ E[0]).tolist()
        Er = m.encode([P[h1]], normalize_embeddings=True)[0]; cos_r = (E[1:] @ Er).tolist()
        Eqr = m.encode(["Represent this sentence for searching relevant passages: " + r["question"] + " " + P[h1]], normalize_embeddings=True)[0]
        cos_qr = (E[1:] @ Eqr).tolist()
        qr = words(r["question"] + " " + P[h1])
        ov = [len(qr & words(P[i])) / max(len(words(P[i])), 1) for i in opts]
        cases.append(dict(id=r["id"], q=r["question"], read=P[h1], opts=opts, texts=[P[i] for i in opts], cos=cos, cos_r=cos_r, cos_qr=cos_qr, ov=ov, h2=opts.index(h2)))
    cache = {}
    if CACHE.exists():
        for l in open(CACHE): x = json.loads(l); cache[x["k"]] = x["p"]
    key = lambda c: hashlib.sha256(json.dumps([c["q"], c["read"], c["texts"], TASK]).encode()).hexdigest()
    miss = [c for c in cases if key(c) not in cache]
    usd = 0.0
    if miss:
        est = sum(len(" ".join(c["texts"])) / 4 + 200 for c in miss) * PRICE_IN
        print(f"live: {len(miss)} requests, estimated ${est:.4f} (cap ${max_usd})", flush=True)
        if est > max_usd: sys.exit("estimate over cap")
        from percolate_core.decide import Jev, Noul

        async def go():
            async with Jev() as jev:
                async def one(c):
                    return await jev.ask({"question": c["q"], "read": c["read"], "task": TASK}, {f"p{j}": Noul(t) for j, t in enumerate(c["texts"])})
                return await asyncio.gather(*(one(c) for c in miss))  # one wave, all in flight
        f = open(CACHE, "a")
        for c, r in zip(miss, asyncio.run(go())):
            p = [r[f"p{j}"].p for j in range(len(c["texts"]))]; cache[key(c)] = p
            f.write(json.dumps({"k": key(c), "p": p}) + "\n"); usd += r.input_tokens * PRICE_IN
        f.close()
    print(f"spend this run ${usd:.5f}")
    X, Y, G, XR, Q = [], [], [], [], []
    rng = np.random.default_rng(0)
    ranks = {k: [] for k in ("chance", "coin", "overlap", "search cos", "cos read", "cos q+read", "Jev", "oracle")}
    for c in cases:
        p = np.clip(np.array(cache[key(c)]), 1e-4, 1 - 1e-4); lp = np.log(p / (1 - p)); h = c["h2"]; n = len(p)
        for j in range(n): X.append(c["cos"][j]); XR.append(c["cos_r"][j]); G.append(int(j == h)); Y.append(lp[j]); Q.append(len(ranks["Jev"]))
        rk = lambda s: 1 + int((np.asarray(s) > np.asarray(s)[h]).sum())
        ranks["chance"].append((n + 1) / 2); ranks["coin"].append(rk(rng.random(n))); ranks["overlap"].append(rk(c["ov"]))
        ranks["search cos"].append(rk(c["cos"])); ranks["cos read"].append(rk(c["cos_r"])); ranks["cos q+read"].append(rk(c["cos_qr"]))
        ranks["Jev"].append(rk(p)); ranks["oracle"].append(1)
        if N <= 4: print(f"-- {c['id']}: hop-2 rank Jev {rk(p)}, cos {rk(c['cos'])}, overlap {rk(c['ov'])}; p_Jev(hop 2) {p[h]:.3f}, "
              f"max other {np.max(np.delete(p, h)):.3f}; cos(hop 2) {c['cos'][h]:.3f}, max other {max(np.delete(c['cos'], h)):.3f}")
    X, Y, G, XR, Q = map(np.array, (X, Y, G, XR, Q))
    def fit(ix, full):
        A = np.c_[X[ix], XR[ix], G[ix], np.ones(len(ix))] if full else np.c_[X[ix], G[ix], np.ones(len(ix))]
        return np.linalg.lstsq(A, Y[ix], rcond=None)[0]
    allix = np.arange(len(X)); nq = Q.max() + 1; byq = [np.nonzero(Q == i)[0] for i in range(nq)]
    f1, f2 = fit(allix, False), fit(allix, True)
    B1, B2 = [], []
    for _ in range(2000):
        ix = np.concatenate([byq[i] for i in rng.integers(0, nq, nq)]); B1.append(fit(ix, False)); B2.append(fit(ix, True))
    lo1, hi1 = np.percentile(B1, [2.5, 97.5], 0); lo2, hi2 = np.percentile(B2, [2.5, 97.5], 0)
    bJ, g, c0 = f1
    print(f"fit cos_q only, {len(X)} options: β_q {f1[0]:+.2f} [{lo1[0]:+.2f}, {hi1[0]:+.2f}], γ {f1[1]:+.2f} [{lo1[1]:+.2f}, {hi1[1]:+.2f}] (vectors' β_B 8.7)")
    print(f"fit cos_q + cos_r: β_q {f2[0]:+.2f} [{lo2[0]:+.2f}, {hi2[0]:+.2f}], β_r {f2[1]:+.2f} [{lo2[1]:+.2f}, {hi2[1]:+.2f}], γ {f2[2]:+.2f} [{lo2[2]:+.2f}, {hi2[2]:+.2f}]")
    for k, v in ranks.items(): print(f"  hop-2 rank, {k:11s}: mean {np.mean(v):.1f}, top-1 {np.mean(np.array(v) == 1):.2f}")
    Path("out").mkdir(exist_ok=True)
    json.dump(dict(fit_q=f1.tolist(), fit_qr=f2.tolist(), ci_q=[lo1.tolist(), hi1.tolist()], ci_qr=[lo2.tolist(), hi2.tolist()], ranks=ranks, usd=usd, cases=[{k: v for k, v in c.items() if k != "texts"} | {"p": cache[key(c)]} for c in cases]),
              open(f"out/srj-n{N}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
