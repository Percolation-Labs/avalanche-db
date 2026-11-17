"""The registered scores (REGISTERED.md): the Jev walk as Claude calls it (mcp_drive.py's rows) against search and the
controls the probe ran with the same settings (probe/, E2E_CONFIGS k5, k10, k20). Paired per question, bootstrap 95%
CI, 10,000 resamples, seed 1118.

    python3 score.py NAME QUESTIONS.jsonl WALK.jsonl CTL_PREFIX     (CTL_PREFIX.k10.jsonl, ...)
"""
import json
import random
import sys


def rec(d, g, k):
    return len(set(d[:k]) & set(g)) / len(g) if g else 0.0


def paired(a, b, n=10000, seed=1118):
    d = [x - y for x, y in zip(a, b)]
    r = random.Random(seed)
    means = sorted(sum(r.choice(d) for _ in d) / len(d) for _ in range(n))
    return sum(d) / len(d), means[int(.025 * n)], means[int(.975 * n) - 1]


def main(name, qpath, wpath, ctl):
    qs = {q["qid"]: q for q in map(json.loads, open(qpath))}
    walks = {}
    for l in open(wpath):
        r = json.loads(l)
        walks[(r["qid"], r["k"])] = r["docs"]
    print(f"\n== {name}")
    for k in (10, 5, 20):
        rows = {json.loads(l)["qid"]: json.loads(l) for l in open(f"{ctl}.k{k}.jsonl")}
        ids = [q for q in rows if (q, k) in walks]
        if not ids:
            continue
        gold = {q: rows[q]["gold"] for q in ids}
        arms = {"walk": {q: walks[(q, k)] for q in ids}, "search": {q: rows[q]["search"] for q in ids}}
        for a in ("oracle", "search-order", "coin", "width"):
            arms[a] = {q: rows[q]["walks"][a] for q in ids}
        r = {a: [rec(v[q], gold[q], k) for q in ids] for a, v in arms.items()}
        full = {a: sum(set(gold[q]) <= set(v[q][:k]) for q in ids) / len(ids) for a, v in arms.items()}
        print(f"k={k}  n={len(ids)}  recall: " + "  ".join(f"{a} {sum(x) / len(x):.3f}" for a, x in r.items()))
        print(f"        full support: " + "  ".join(f"{a} {v:.3f}" for a, v in full.items()))
        for a, b, tag in (("walk", "search", "W1"), ("walk", "width", "W2"), ("walk", "search-order", ""),
                          ("walk", "coin", ""), ("oracle", "search", "G1")):
            m, lo, hi = paired(r[a], r[b])
            verdict = f"  {tag} {'PASS' if (lo > 0 if tag != 'G1' else m >= .10) else 'FAIL'}" if tag and k == 10 else ""
            print(f"        {a} - {b:12s} {m:+.3f} [{lo:+.3f}, {hi:+.3f}]{verdict}")
        if isinstance(next(iter(qs.values()))["gold"], dict):
            last = {q: [d for d, h in qs[q]["gold"].items() if h == max(qs[q]["gold"].values())] for q in ids}
            lr = {a: sum(rec(v[q], last[q], k) for q in ids) / len(ids) for a, v in arms.items() if a in ("walk", "search", "oracle")}
            print("        last-hop gold recall: " + "  ".join(f"{a} {v:.3f}" for a, v in lr.items()))


if __name__ == "__main__":
    main(*sys.argv[1:5])
