"""SR-JW2 (REGISTERED-SRJW2.md): SR-JW with bill's renderer fixes (render.render2, decoys at b, fresh seeds 51001–51004)
and string-reader control rows. SR-JW's docstring follows.
SR-JW (REGISTERED-SRJW.md), james: does the theory's conductance, priced by Jev's measured (β, γ), predict Jev's own
choices on worlds it has never seen? SR1c's worlds (seeds 41001–41004) are rendered as text (render.py, token-free).
At the chain's two hops, Jev reads the question and the passages already read, and scores each door's passage:
  hop 1: at s, read [s], options = s's neighbours (b among them)
  hop 2: at b, read [s, b], options = b's neighbours (a and the way back, s, among them)
One batched request per option set, all in flight together (bill's srj.py pattern, same TASK wording).
Jev's share of an option = its odds / Σ odds. The theory's share = exp(β·cos + γ·[door's relation is r1 or r2]) / Σ, with
cos = bge-small cos(question, passage) and MuSiQue's (β 1.0, γ 3.7) from RESULT-SRJ.
    source ~/code/p8-subsystems/.env; P8_CREDENTIAL_ORIGINS='{"JEV_API_KEY":["https://api.typesafe.ai"]}' \\
    uv run --with sentence-transformers --with scipy --with 'percolate-core==0.2.15' python srjw.py STAGE MAX_USD"""
import asyncio, json, sys, hashlib
from pathlib import Path
import numpy as np
import re
import gen, render
WORD = re.compile(r"[a-z0-9]+")
STOP = {"the", "a", "an", "of", "in", "is", "was", "by", "one", "that", "which", "place", "it", "its"}
def words(t): return set(WORD.findall(t.lower())) - STOP
from sr1b import ATYPE, NOISE

SEEDS = (51001, 51002, 51003, 51004)
BETA, GAMMA, ALPHA = 1.0, 3.7, .15
TASK = ("Each option is a passage not yet read. Having read `read`, would reading this option next give information "
        "needed to answer `question`?")
CACHE = Path.home() / ".cache" / "walklab" / "srjw2-jev-cache.jsonl"
PRICE_IN = 0.042e-6


def hops(stage):
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")
    out = []
    for sd in (SEEDS[:1] if stage == 0 else SEEDS):
        w = gen.world(sd, NOISE, ATYPE, decoys=True); nm, own, read_text, qs = render.render2(w, sd)
        E = np.array(w["edges"]); rel = np.array(w["rel"])
        for c, q in zip(w["cases"], qs):
            ta = w["topic"][c["a"]]; tw = set(render.TOPICS[ta][1].split())
            for hop, (u, read, gold) in enumerate(((c["s"], [c["s"]], c["b"]), (c["b"], [c["s"], c["b"]], c["a"]))):
                nb = sorted({int(v) for x, y in E for v in ((y,) if x == u else (x,) if y == u else ())})
                match = [int(any(rel[k] in (c["r1"], c["r2"]) for k in np.nonzero(((E[:, 0] == u) & (E[:, 1] == v)) | ((E[:, 1] == u) & (E[:, 0] == v)))[0])) for v in nb]
                rtext = " ".join(read_text(r) for r in read)
                emb = m.encode(["Represent this sentence for searching relevant passages: " + q] + [own[v] for v in nb], normalize_embeddings=True)
                cos = (emb[1:] @ emb[0]).tolist()
                need = [render.RELS[c["r1"]], render.RELS[c["r2"]]]
                # string readers (bill's review 2): what a cheap reader without a model would use
                tnoun = render.TOPICS[ta][0]
                type_lit = [int(tnoun in own[v].lower()) for v in nb]                     # the literal type word in the door
                phrase = [int(any(p in own[v] for p in need) or nm[c["s"]] in own[v]) for v in nb]  # relation phrases or the start's name in the door
                relsent = [int(any(f"{nm[u]} {p} {nm[v]}." in rtext or f"{nm[v]} {p} {nm[u]}." in rtext for p in need)) for v in nb]  # a read sentence links u to v by a needed relation
                dict_rt = [relsent[j] + int(bool(tw & words(own[v]))) for j, v in enumerate(nb)]  # + the generator's own type dictionary
                out.append(dict(seed=sd, case=c["name"], hop=hop + 1, q=q, read=rtext, opts=nb, texts=[own[v] for v in nb],
                                cos=cos, match=match, gold=nb.index(gold), back=(nb.index(c["s"]) if hop == 1 else None),
                                ov=[len(words(q + " " + rtext) & words(own[v])) / max(len(words(own[v])), 1) for v in nb],
                                type_lit=type_lit, phrase=phrase, relsent=relsent, dict_rt=dict_rt))
    return out


def main():
    stage, max_usd = int(sys.argv[1]), float(sys.argv[2])
    H = hops(stage)
    cache = {}
    if CACHE.exists():
        for l in open(CACHE): x = json.loads(l); cache[x["k"]] = x["p"]
    key = lambda h: hashlib.sha256(json.dumps([h["q"], h["read"], h["texts"], TASK]).encode()).hexdigest()
    miss = [h for h in H if key(h) not in cache]
    usd = 0.0
    if miss:
        est = sum(len(" ".join(h["texts"]) + h["read"]) / 4 + 200 for h in miss) * PRICE_IN
        print(f"live: {len(miss)} requests, estimated ${est:.5f} (cap ${max_usd})", flush=True)
        if est > max_usd: sys.exit("estimate over cap")
        from percolate_core.decide import Jev, Noul
        async def go():
            async with Jev() as jev:
                async def one(h):
                    return await jev.ask({"question": h["q"], "read": h["read"], "task": TASK}, {f"p{j}": Noul(t) for j, t in enumerate(h["texts"])})
                return await asyncio.gather(*(one(h) for h in miss))  # one wave, all in flight
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        f = open(CACHE, "a")
        for h, r in zip(miss, asyncio.run(go())):
            p = [r[f"p{j}"].p for j in range(len(h["texts"]))]; cache[key(h)] = p
            f.write(json.dumps({"k": key(h), "p": p}) + "\n"); usd += r.input_tokens * PRICE_IN
        f.close()
    print(f"spend this run ${usd:.5f}")
    lines, rows = [], []
    def say(x): print(x, flush=True); lines.append(x)
    for h in H:
        p = np.clip(np.array(cache[key(h)]), 1e-4, 1 - 1e-4); odds = p / (1 - p); sj = odds / odds.sum()
        th = np.exp(BETA * np.array(h["cos"]) + GAMMA * np.array(h["match"])); st = th / th.sum()
        cs = np.array(h["cos"]); g = h["gold"]
        rk = lambda s: 1 + int((np.asarray(s) > np.asarray(s)[g]).sum())
        r = dict(seed=h["seed"], case=h["case"], hop=h["hop"], n=len(p), jev_share=float(sj[g]), theory_share=float(st[g]),
                 jev_rank=rk(p), theory_rank=rk(st), cos_rank=rk(cs), overlap_rank=rk(h["ov"]),
                 **{f"{k}_uniq": int(rk(h[k]) == 1 and sum(np.asarray(h[k]) == np.asarray(h[k])[g]) == 1) for k in ("type_lit", "phrase", "relsent", "dict_rt")},
                 jev_uniq=int(rk(p) == 1), chance=(len(p) + 1) / 2,
                 jev_back=(float(sj[h["back"]]) if h["back"] is not None else None),
                 theory_back=(float(st[h["back"]]) if h["back"] is not None else None), n_match=int(sum(h["match"])))
        rows.append(r)
        say(f"{r['seed']} {r['case']:<15} hop {r['hop']}: {r['n']} doors ({r['n_match']} relational); chain door share Jev {r['jev_share']:.3f}, "
            f"theory {r['theory_share']:.3f}; rank Jev {r['jev_rank']}, theory {r['theory_rank']}, cos {r['cos_rank']}, overlap {r['overlap_rank']}"
            + (f"; back share Jev {r['jev_back']:.3f}, theory {r['theory_back']:.3f}" if r["jev_back"] is not None else ""))
    lr = np.log([r["jev_share"] / r["theory_share"] for r in rows])
    rng = np.random.default_rng(0); bs = [np.median(lr[rng.integers(0, len(lr), len(lr))]) for _ in range(2000)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    say(f"median log(Jev share / theory share) at the chain door {np.median(lr):+.3f} [{lo:+.3f}, {hi:+.3f}] (n {len(lr)})")
    say("chain door ranked first: Jev {}/{n}, theory {}/{n}, cos {}/{n}, word overlap {}/{n}".format(*(sum(r[k] == 1 for r in rows) for k in ("jev_rank", "theory_rank", "cos_rank", "overlap_rank")), n=len(rows)))
    for hp in (1, 2):
        rs = [r for r in rows if r["hop"] == hp]; l = np.log([r["jev_share"] / r["theory_share"] for r in rs])
        bs = [np.median(l[rng.integers(0, len(l), len(l))]) for _ in range(2000)]
        say(f"hop {hp}: median log(Jev/theory) {np.median(l):+.3f} [{np.percentile(bs, 2.5):+.3f}, {np.percentile(bs, 97.5):+.3f}]; chain door uniquely first: "
            + ", ".join(f"{k} {sum(r[k] for r in rs)}/{len(rs)}" for k in ("jev_uniq", "type_lit_uniq", "phrase_uniq", "relsent_uniq", "dict_rt_uniq"))
            + f"; theory first {sum(r['theory_rank'] == 1 for r in rs)}, cos first {sum(r['cos_rank'] == 1 for r in rs)}"
            + (f"; back share Jev {np.median([r['jev_back'] for r in rs]):.3f} vs theory {np.median([r['theory_back'] for r in rs]):.3f}" if hp == 2 else ""))
    for ct in "ABCD":
        rs = {(r["seed"], r["hop"]): r for r in rows if r["case"].startswith(ct)}
        for sd in sorted({k[0] for k in rs}):
            h1, h2 = rs[(sd, 1)], rs[(sd, 2)]
            k = (1 - ALPHA) ** 2
            fj = k * h1["jev_share"] * h2["jev_share"] / (1 - k * h1["jev_share"] * h2["jev_back"])
            ft = k * h1["theory_share"] * h2["theory_share"] / (1 - k * h1["theory_share"] * h2["theory_back"])
            say(f"  {ct} {sd}: chain reach h(a) from Jev's shares {fj:.3f}, from the theory's {ft:.3f}")
    open(f"out/srjw2-{stage}.txt", "w").write("\n".join(lines) + "\n"); json.dump(rows, open(f"out/srjw2-{stage}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
