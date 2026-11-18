"""REGISTERED-prs2.md's Jev dev step: recall@10 and the pick rate per candidate on the 65 dev PR questions."""
import json, sys
qs = {q["qid"]: q for q in map(json.loads, open(sys.argv[1]))}
for n in ("B", "N", "M", "NM", "H1"):
    try:
        rows = [json.loads(l) for l in open(f"{sys.argv[2]}/jev-dev-{n}.jsonl")]
    except FileNotFoundError:
        continue
    rec = sum(len(set(r["docs"][:10]) & set(qs[r["qid"]]["gold"])) / len(qs[r["qid"]]["gold"]) for r in rows) / len(rows)
    nxt = sum(any(v.startswith("next:") for v in r["via"]) for r in rows)
    mrg = sum(any(v.startswith("merge:") for v in r["via"]) for r in rows)
    cost = sum(r["cost_usd"] for r in rows)
    print(f"{n:3s} n={len(rows)} recall@10 {rec:.3f}  opened next {nxt}  merge {mrg}  ${cost:.3f}")
