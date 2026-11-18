"""Stage 0 of REGISTERED.md: the replayed-P walks under rank, per_read and per_target against search's top 10.
Paired bootstrap 95% CI, 10,000 resamples, seed 1118.   python3 score.py NAME SIM.jsonl [NAME SIM.jsonl ...]"""
import json, random, sys
from collections import Counter


def rec(d, g):
    return len(set(d[:10]) & set(g)) / len(g) if g else 0.0


def paired(a, b, n=10000, seed=1118):
    d = [x - y for x, y in zip(a, b)]
    r = random.Random(seed)
    m = sorted(sum(r.choice(d) for _ in d) / len(d) for _ in range(n))
    return sum(d) / len(d), m[int(.025 * n)], m[int(.975 * n) - 1]


def one(name, path):
    rows = [json.loads(l) for l in open(path)]
    gold = [list(r["gold"]) if isinstance(r["gold"], list) else list(r["gold"].keys()) for r in rows]
    ok = sum(r["recorded"] == [x[0] for x in r["arms"]["rank"]["reads"]] for r in rows)
    arms = {"search": [r["search"] for r in rows]}
    for a in ("rank", "per_read", "per_target"):
        arms[a] = [[x[0] for x in r["arms"][a]["reads"]] for r in rows]
    R = {a: [rec(d, g) for d, g in zip(v, gold)] for a, v in arms.items()}
    print(f"\n== {name}: {len(rows)} questions; rank reproduces the recorded walk on {ok}")
    for a in R:
        below = sum(x < s - 1e-9 for x, s in zip(R[a], R["search"]))
        unk = sum(r["arms"][a]["unknown"] for r in rows) if a != "search" else 0
        opened = Counter(len(r["arms"][a]["opened"]) for r in rows) if a != "search" else {}
        print(f"  {a:<10} recall@10 {sum(R[a])/len(rows):.3f}  below search {below:>3}  unscored doors met {unk:>4}  doors opened {dict(sorted(opened.items()))}")
    for a, b in (("per_read", "rank"), ("per_read", "search"), ("rank", "search"), ("per_target", "rank")):
        m, lo, hi = paired(R[a], R[b])
        print(f"  {a} - {b}: {m:+.3f} [{lo:+.3f}, {hi:+.3f}]")
    # where per_read changed the walk: did it open narrower doors, and what did the reads through them return
    ch = [i for i, r in enumerate(rows) if arms["per_read"][i] != arms["rank"][i]]
    w = Counter()
    for i in ch:
        for o in rows[i]["arms"]["per_read"]["opened"]:
            w["<=2" if (o["width"] or 0) <= 2 else "3-5" if o["width"] <= 5 else ">5"] += 1
    up = sum(R["per_read"][i] > R["rank"][i] for i in ch); dn = sum(R["per_read"][i] < R["rank"][i] for i in ch)
    print(f"  per_read changed {len(ch)} walks: better {up}, worse {dn}; its doors there by width {dict(w)}")


if __name__ == "__main__":
    a = sys.argv[1:]
    for i in range(0, len(a), 2):
        one(a[i], a[i + 1])
