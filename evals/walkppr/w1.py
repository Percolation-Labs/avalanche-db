"""W1 (REGISTERED.md): re-rank recorded test batches by fixed reciprocal rank fusion of P and read-set PageRank.
    python3 w1.py   (from the repo root)"""
import gzip, json, collections, random, statistics as st, subprocess
def rows(c):
    raw = subprocess.run(["git", "show", f"origin/main:evals/structural/out/ft-{c}.jsonl.gz"], capture_output=True).stdout
    return [json.loads(l) for l in gzip.decompress(raw).decode().splitlines() if l.strip()]
def ranks(ds, key):
    o = sorted(ds, key=lambda d: (-key(d), -d["p"], d["key"]))
    return {d["key"]: i + 1 for i, d in enumerate(o)}
def rrf(ds, key):
    rp = ranks(ds, lambda d: d["p"]); rk = ranks(ds, key)
    return lambda d: 1 / (60 + rp[d["key"]]) + 1 / (60 + rk[d["key"]])
for c in ("cards", "prs", "mq"):
    W = collections.defaultdict(list)
    for r in rows(c): W[(r["qid"], r["wave"])].append(r)
    W = [ds for ds in W.values() if any(d["gold"] for d in ds)]
    arms = {
        "P": lambda ds: (lambda d: d["p"]),
        "P+PPR": lambda ds: rrf(ds, lambda d: d["real"]["ppr"]),
        "P+shuffled PPR": lambda ds: rrf(ds, lambda d: d["shuffled"]["ppr"]),
        "P+width": lambda ds: rrf(ds, lambda d: d["width"]),
        "PPR alone": lambda ds: (lambda d: d["real"]["ppr"]),
        "search order": lambda ds: (lambda d: -(d["search_rank"] if d["search_rank"] is not None else 1e9)),
    }
    out = [f"{c}: waves with a gold door {len(W)}"]
    for name, mk in arms.items():
        first, mrr, eg = [], [], []
        for ds in W:
            f = mk(ds)
            o = sorted(ds, key=lambda d: (-f(d), -d["p"], d["key"]))
            first.append(int(o[0]["gold"] > 0))
            mrr.append(1 / next(i + 1 for i, d in enumerate(o) if d["gold"] > 0))
            best = max(d["gold"] / d["width"] for d in ds if d["width"])
            eg.append((o[0]["gold"] / o[0]["width"] if o[0]["width"] else 0) / best)
        out.append(f"  {name:15s} gold first {st.mean(first):.3f} | MRR {st.mean(mrr):.3f} | first door's gold rate / best gold door's {st.mean(eg):.3f}")
    print("\n".join(out))
