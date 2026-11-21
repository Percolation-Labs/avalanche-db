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
        qr = words(r["question"] + " " + P[h1])
        ov = [len(qr & words(P[i])) / max(len(words(P[i])), 1) for i in opts]
        cases.append(dict(id=r["id"], q=r["question"], read=P[h1], opts=opts, texts=[P[i] for i in opts], cos=cos, ov=ov, h2=opts.index(h2)))
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
    X, Y, G = [], [], []
    rng = np.random.default_rng(0)
    ranks = {k: [] for k in ("chance", "coin", "overlap", "search cos", "Jev", "oracle")}
    for c in cases:
        p = np.clip(np.array(cache[key(c)]), 1e-4, 1 - 1e-4); lp = np.log(p / (1 - p)); h = c["h2"]; n = len(p)
        for j in range(n): X.append(c["cos"][j]); G.append(int(j == h)); Y.append(lp[j])
        rk = lambda s: 1 + int((np.asarray(s) > np.asarray(s)[h]).sum())
        ranks["chance"].append((n + 1) / 2); ranks["coin"].append(rk(rng.random(n))); ranks["overlap"].append(rk(c["ov"]))
        ranks["search cos"].append(rk(c["cos"])); ranks["Jev"].append(rk(p)); ranks["oracle"].append(1)
        print(f"-- {c['id']}: hop-2 rank Jev {rk(p)}, cos {rk(c['cos'])}, overlap {rk(c['ov'])}; p_Jev(hop 2) {p[h]:.3f}, "
              f"max other {np.max(np.delete(p, h)):.3f}; cos(hop 2) {c['cos'][h]:.3f}, max other {max(np.delete(c['cos'], h)):.3f}")
    X, Y, G = np.array(X), np.array(Y), np.array(G)
    A = np.c_[X, G, np.ones_like(X)]; (bJ, g, c0), *_ = np.linalg.lstsq(A, Y, rcond=None)
    print(f"fit over {len(X)} options: β_J {bJ:.2f} nats per cos unit (vectors' Bayes β_B 8.7), γ (hop 2 beyond cos) {g:+.2f} nats, c {c0:+.2f}")
    print("hop-2 rank among 19, mean: " + ", ".join(f"{k} {np.mean(v):.1f}" for k, v in ranks.items()))
    Path("out").mkdir(exist_ok=True)
    json.dump(dict(bJ=bJ, gamma=g, c=c0, ranks=ranks, usd=usd, cases=[{k: v for k, v in c.items() if k != "texts"} | {"p": cache[key(c)]} for c in cases]),
              open(f"out/srj-n{N}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
