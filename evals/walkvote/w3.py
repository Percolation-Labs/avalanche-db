"""evals/walkvote/REGISTERED-W3.md: within-width vote; variant chosen per graph on dev, test scored once.
    python3 w3.py ROWS_DIR   (V1's full rows v-{dev,test}-{cards,prs,mq}.jsonl[.gz])"""
import gzip, json, math, os, sys
from collections import defaultdict

from w2 import SETS, fused, p_order, readout


def load(d, sp, k):
    p = f"{d}/v-{sp}-{k}.jsonl"
    f = open(p) if os.path.exists(p) else gzip.open(p + ".gz", "rt")
    rows = [json.loads(l) for l in f]
    u = [tuple(t) for t in rows[0]["thetas"]].index((-1.0, 0.0))
    B = defaultdict(list)
    for r in rows[1:]:
        B[(r["qid"], r["wave"])].append(r)
    return u, list(B.values())


def within(ds, v):
    cls = [int(math.log2(d["width"])) for d in ds]
    out = []
    for i in range(len(ds)):
        peers = [j for j in range(len(ds)) if j != i and cls[j] == cls[i]]
        out.append(.5 if not peers else sum(1.0 if v[i] > v[j] else .5 if v[i] == v[j] else 0.0 for j in peers) / len(peers))
    return out


def xs(ds, u, arm):
    s = [d[arm][u] for d in ds]
    return {"summed": s, "per target": [x / d["width"] for x, d in zip(s, ds)], "within width": within(ds, s)}


def score(B, u, variant, arm="real"):
    return readout(B, lambda ds: fused(ds, xs(ds, u, arm)[variant]))


def main(d):
    V = ["summed", "per target", "within width"]
    gains = {}; dropb = {}; ctl = {}
    for k, n in SETS:
        u, dev = load(d, "dev", k)
        P = readout(dev, p_order)
        D = {v: score(dev, u, v) for v in V}
        ok = [v for v in V if D[v][2] >= P[2] - .02]
        ch = max(ok, key=lambda v: D[v][0]) if ok else None
        print(f"{n}: dev P gold-first {P[0]:.3f} (b) {P[2]:.3f}; " + "; ".join(f"{v} {D[v][0]:.3f} (b) {D[v][2]:.3f}" for v in V) + f" -> chosen {ch}")
        u, test = load(d, "test", k)
        T = readout(test, p_order)
        rows = [("P", T)]
        if ch:
            C = score(test, u, ch); S = score(test, u, ch, "shuffled")
            rows += [(f"P ⊕ {ch} (chosen)", C), (f"P ⊕ {ch}, shuffled", S)]
            gains[k], dropb[k], ctl[k] = C[0] - T[0], C[2] - T[2], C[0] - S[0]
        else:
            gains[k], dropb[k], ctl[k] = 0.0, 0.0, 0.0
        rows += [("P ⊕ within width", score(test, u, "within width")),
                 ("within width alone", readout(test, lambda ds: sorted(range(len(ds)), key=lambda i: (-xs(ds, u, "real")["within width"][i], p_order(ds).index(i)))))]
        for a, (g, m, r) in rows:
            print(f"  test {a:<28} gold first {g:.3f}  MRR {m:.3f}  read-weighted (b) {r:.3f}   ({len(test)} waves)")
    up = [k for k in gains if gains[k] >= .03]
    ok = len(up) >= 2 and min(gains.values()) >= -.02 and min(dropb.values()) >= -.02 and all(ctl[k] >= .02 for k in up)
    print("\nchosen − P, gold first: " + ", ".join(f"{n} {gains[k]:+.3f}" for k, n in SETS))
    print("chosen − P, read-weighted (b): " + ", ".join(f"{n} {dropb[k]:+.3f}" for k, n in SETS))
    print("chosen − shuffled, gold first: " + ", ".join(f"{n} {ctl[k]:+.3f}" for k, n in SETS))
    print(f"W3: {'pass' if ok else 'fail'}")


if __name__ == "__main__":
    main(sys.argv[1])
