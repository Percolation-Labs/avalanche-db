"""Per-wave rows of (b) for dreaming (james): one row per recorded wave of the dev walks.
    python3 rows.py TRACES.jsonl STEINER.jsonl OUT.jsonl"""
import json, sys
T = [json.loads(l) for l in open(sys.argv[1])]
St = {json.loads(l)["qid"]: json.loads(l) for l in open(sys.argv[2])}
with open(sys.argv[3], "w") as f:
    for r in T:
        s = St.get(r["qid"])
        if not s or not s["gold"]: continue
        g = set(s["gold"]); arr = s["real"]["arrival"]
        share = sum(1 for x in arr if x is not None and x <= 5) / len(arr)
        t = r["walk"]["trace"]
        for b in t["batches"]:
            before = [x["doc"] for x in t["reads"] if x["wave"] < b["wave"]]
            bs = set(before)
            P = {x["key"]: (i + 1, x["score"]) for i, x in enumerate(b["ranking"])}
            doors = []
            for d in b["doors"]:
                tg = [x for x in d["targets"] if x not in bs]
                doors.append({"key": d["key"], "kind": d["kind"], "width": len(tg), "gold": len(set(tg) & g),
                              "p": P.get(d["key"], (None, None))[1], "rank": P.get(d["key"], (None, None))[0],
                              "search_rank": s["search_order"].get(d["key"])})
            f.write(json.dumps({"qid": r["qid"], "question": r["walk"]["question"], "wave": b["wave"], "reads_before": before,
                                "opened": b["opened"], "steiner_share5": share, "doors": doors}) + "\n")
