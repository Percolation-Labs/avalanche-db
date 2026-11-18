"""Dev score for REGISTERED-likeness.md: per set and arm, recall@10, arm - search and arm - none (paired bootstrap),
losses to search, the coin, and the likeness door's wave-1 open rate and P against the top door's."""
import json, sys, statistics as st
sys.path.insert(0, "/tmp/claude-501/adb-like/evals/e2e")
from score import rec, paired
D = "/tmp/claude-501/adb-like/evals/e2e/dev"
sets = {"cards": ("cards-dev", "dev-cards", "s-cards"), "prs": ("prs-dev", "dev-prs", "s-prs"), "mq": ("musique-dev", "dev-mq", "s-mq")}
worst = {}
for name, (qf, wf, sf) in sets.items():
    try:
        qs = {q["qid"]: q for q in map(json.loads, open(f"{D}/{qf}.jsonl"))}
        rows = [json.loads(l) for l in open(f"{wf}.jsonl")]
        srch = {r["qid"]: r["docs"] for r in map(json.loads, open(f"{sf}.jsonl"))}
    except FileNotFoundError as e:
        print(name, "missing", e.filename); continue
    arms = {}
    for r in rows: arms.setdefault(r["arm"], {})[r["qid"]] = r
    ids = [q for q in qs if q in srch and all(q in a for a in arms.values())]
    R = lambda docs, q: rec(docs, qs[q]["gold"], 10)
    s = [R(srch[q], q) for q in ids]
    none = [R(arms["none"][q]["docs"], q) for q in ids] if "none" in arms else None
    print(f"\n{name}: n={len(ids)}  search {sum(s)/len(s):.3f}" + (f"  none {sum(none)/len(none):.3f}  coin {(sum(none)+sum(s))/2/len(s):.3f}  oracle {sum(map(max, none, s))/len(s):.3f}  losses(none) {sum(a < b for a, b in zip(none, s))}" if none else ""))
    for arm, a in arms.items():
        if arm == "none": continue
        x = [R(a[q]["docs"], q) for q in ids]
        l1 = [a[q]["like"][0] for q in ids if a[q]["like"] and a[q]["like"][0]["wave"] == 1]
        opened = sum(l["opened"] for l in l1)
        print(f"  {arm:6s} {sum(x)/len(x):.3f}  -search %+.3f [%+.3f, %+.3f]" % paired(x, s) + "  -none %+.3f [%+.3f, %+.3f]" % paired(x, none)
              + "  -coin %+.3f" % paired(x, [(p + q) / 2 for p, q in zip(none, s)])[0]
              + f"  losses {sum(p < q for p, q in zip(x, s))}  w1 open {opened}/{len(l1)}  P med {st.median(l['p'] for l in l1):.2f} vs top {st.median(l['top'] for l in l1):.2f}  rank med {st.median(l['pos'] for l in l1)}/{st.median(l['of'] for l in l1)}"
              + f"  ${sum(a[q]['cost_usd'] for q in ids):.3f}")
        worst.setdefault(arm, []).append(paired(x, s)[0])
print("\nworst-set (arm - search):", {a: round(min(v), 3) for a, v in worst.items() if len(v) == 3})
