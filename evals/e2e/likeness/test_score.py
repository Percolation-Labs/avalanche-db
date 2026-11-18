"""Held-out score for REGISTERED-likeness.md: L1 like-search >= -.01 each set; L2 like-walk >= -.02 cards, mq; L3 like-coin > 0."""
import json, sys, statistics as st
sys.path.insert(0, "/tmp/claude-501/adb-like/evals/e2e")
from score import rec, paired
sets = {"cards": ("leads_test_walk-p8", "leads_test_ctl-p8.k10", "test-cards", .51), "prs": ("prs_walk-test", "prs_ctl-test.k10", "test-prs", .30), "mq": ("leads_test_walk-mq", "leads_test_ctl-mq.k10", "test-mq", .36)}
ok = True
for name, (wf, cf, lf, orth) in sets.items():
    ctl = {r["qid"]: r for r in map(json.loads, open(f"{cf}.jsonl"))}
    walk = {r["qid"]: r for r in map(json.loads, open(f"{wf}.jsonl")) if r["k"] == 10 and r["kappa"]}
    try: like = {r["qid"]: r for r in map(json.loads, open(f"{lf}.jsonl"))}
    except FileNotFoundError: print(name, "not run"); continue
    ids = [q for q in ctl if q in walk and q in like]
    R = lambda d, q: rec(d, ctl[q]["gold"], 10)
    s = [R(ctl[q]["search"], q) for q in ids]; w = [R(walk[q]["docs"], q) for q in ids]; l = [R(like[q]["docs"], q) for q in ids]
    coin = [(a + b) / 2 for a, b in zip(w, s)]
    L1, L2, L3 = paired(l, s), paired(l, w), paired(l, coin)
    p1, p2, p3 = L1[0] >= -.01, (L2[0] >= -.02 if name != "prs" else None), L3[0] > 0
    ok &= p1 and p3 and (p2 is not False)
    l1 = [like[q]["like"][0] for q in ids if like[q]["like"] and like[q]["like"][0]["wave"] == 1]
    print(f"{name}: n={len(ids)}/{len(ctl)} (orthogonal share {orth})  search {sum(s)/len(s):.3f}  walk {sum(w)/len(w):.3f}  like {sum(l)/len(l):.3f}  oracle {sum(map(max, w, s))/len(s):.3f}")
    print("  L1 like-search %+.3f [%+.3f, %+.3f]" % L1, "PASS" if p1 else "FAIL")
    print("  L2 like-walk   %+.3f [%+.3f, %+.3f]" % L2, {True: "PASS", False: "FAIL", None: "(reported)"}[p2])
    print("  L3 like-coin   %+.3f [%+.3f, %+.3f]" % L3, "PASS" if p3 else "FAIL")
    print(f"  losses to search: walk {sum(a < b for a, b in zip(w, s))}  like {sum(a < b for a, b in zip(l, s))};  w1 open {sum(x['opened'] for x in l1)}/{len(l1)}  P med {st.median(x['p'] for x in l1):.2f} vs top {st.median(x['top'] for x in l1):.2f}  ${sum(like[q]['cost_usd'] for q in ids):.3f}")
print("PASS" if ok else "FAIL (on the sets run)")
