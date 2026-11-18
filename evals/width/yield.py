"""Wave-1 doors of the recorded dev walks: gold per read the door would give at k=10 (5 reads left), by width and P.
Expected, not shown-order exact: gold behind it x min(width,5)/width."""
import json, sys
from collections import defaultdict
for name, path in zip(sys.argv[1::2], sys.argv[2::2]):
    cell = defaultdict(lambda: [0, 0.0, 0.0])
    for l in open(path):
        r = json.loads(l); g = set(r["gold"]) if isinstance(r["gold"], list) else set(r["gold"])
        t = r["walk"]["trace"]; b = t["batches"][0]
        P = {x["key"]: x["score"] for x in b["ranking"] if x["score"] is not None}
        for d in b["doors"]:
            if d["key"] not in P: continue
            w = len(d["targets"]); gb = len(set(d["targets"]) & g); c = min(w, 5)
            wb = "1" if w == 1 else "2" if w == 2 else "3-5" if w <= 5 else "6-20" if w <= 20 else ">20"
            pb = "P<.5" if P[d["key"]] < .5 else "P.5-.7" if P[d["key"]] < .7 else "P>=.7"
            e = gb * c / w
            for key in ((wb, pb), (wb, "all")):
                cell[key][0] += 1; cell[key][1] += e; cell[key][2] += e / c
    print(f"== {name}: doors, expected gold per door read, per read")
    for wb in ("1", "2", "3-5", "6-20", ">20"):
        print("  w", wb.ljust(5), "  ".join(f"{pb}: n {cell[(wb,pb)][0]:>5} gold/door {cell[(wb,pb)][1]/max(1,cell[(wb,pb)][0]):.3f} /read {cell[(wb,pb)][2]/max(1,cell[(wb,pb)][0]):.3f}" for pb in ("all", "P<.5", "P.5-.7", "P>=.7")))
