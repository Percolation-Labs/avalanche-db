import json, collections, random, statistics as st
def golds(g): return set(g.keys()) if isinstance(g,dict) else set(g)
for c, g in [("cards","p8"),("prs","p8"),("mq","mq")]:
    gold = {r["qid"]: golds(r["gold"]) for r in map(json.loads, open(f"../dt-{c}.jsonl"))}
    C = [set(json.loads(l)["members"]) for l in open(f"cand-{g}.jsonl")]
    by = collections.defaultdict(list)
    for i, m in enumerate(C):
        for d in m: by[d].append(i)
    W = [json.loads(l) for l in open(f"b-{c}.jsonl")]
    hub_best, door_best, hub_any, n = [], [], 0, 0
    for w in W:
        G = gold[w["qid"]]; R = set(w["reads_before"])
        if not (G - R): continue
        n += 1
        raised = {i for d in R for i in by.get(d, [])}
        dens = [len((C[i]-R)&G)/max(len(C[i]-R),1) for i in raised]
        hb = max(dens, default=0.0)
        db = max((d["gold"]/d["width"] for d in w["doors"] if d["width"]), default=0.0)
        hub_best.append(hb); door_best.append(db); hub_any += hb > 0
    print(f"{c}: waves {n} | raised hubs per wave ~{st.mean(len({i for d in set(w['reads_before']) for i in by.get(d,[])}) for w in W):.0f} | some hub holds unread gold {hub_any/n:.2f} | best gold density: hub {st.mean(hub_best):.3f} vs existing door {st.mean(door_best):.3f} | hub>door {sum(h>d for h,d in zip(hub_best,door_best))/n:.2f}")
