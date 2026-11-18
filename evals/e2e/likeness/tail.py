import json, statistics as st
sets = {"cards": ("q-cards", "s50-cards", "trace-cards"), "prs": ("q-prs-test", "s50-prs", "trace-pr"), "mq": ("q-musique-questions", "s50-mq", "trace-mq")}
B = [(0, 5, "1-5"), (5, 10, "6-10"), (10, 20, "11-20"), (20, 50, "21-50")]
for name, (qf, sf, tf) in sets.items():
    qs = {q["qid"]: q for q in map(json.loads, open(f"{qf}.jsonl"))}
    s = {r["qid"]: r["docs"] for r in map(json.loads, open(f"{sf}.jsonl"))}
    tr = {r["qid"]: r["trace"] for r in map(json.loads, open(f"{tf}.jsonl"))}
    ids = [q for q in qs if q in s and q in tr]
    gp = {lab: [] for *_, lab in B}; share = {lab: 0 for *_, lab in B}; tot = 0
    for q in ids:
        g = set(qs[q]["gold"]); tot += len(g)
        for a, b, lab in B:
            h = len(g & set(s[q][a:b])); gp[lab].append(h / (b - a)); share[lab] += h
    print(f"\n{name}: n={len(ids)}, gold {tot}; beyond top 50: {1 - sum(share.values())/tot:.2f}")
    print("  gold per read: " + "  ".join(f"{l} {sum(v)/len(v):.3f}" for l, v in gp.items()))
    print("  share of gold: " + "  ".join(f"{l} {share[l]/tot:.2f}" for l in share))
    # good seeds -> tail?
    for cond, f in (("seeds 0 gold", lambda h: h == 0), ("seeds 1 gold", lambda h: h == 1), ("seeds 2+ gold", lambda h: h >= 2)):
        sel = [q for q in ids if f(len(set(qs[q]["gold"]) & set(s[q][:5])))]
        if sel:
            m = lambda a, b: sum(len(set(qs[q]["gold"]) & set(s[q][a:b])) / (b - a) for q in sel) / len(sel)
            dr = [r for q in sel for r in tr[q]["reads"] if r["wave"] == 1]
            dg = sum(r["doc"] in set(qs[r_q]["gold"]) for r_q in sel for r in tr[r_q]["reads"] if r["wave"] == 1)
            print(f"  {cond:14s} n={len(sel):3d}  6-10 {m(5,10):.3f}  11-20 {m(10,20):.3f}  21-50 {m(20,50):.3f}  | first door {dg/max(1,len(dr)):.3f} per read ({len(dr)} reads)")
    # door vs tail, and door gold that search's top 50 lacks
    dr = dg = orth = 0
    for q in ids:
        g = set(qs[q]["gold"])
        for r in tr[q]["reads"]:
            if r["wave"] == 1:
                dr += 1; dg += r["doc"] in g; orth += r["doc"] in g and r["doc"] not in s[q]
    print(f"  first door (Jev's): {dg/dr:.3f} gold per read; {orth}/{dg} of its gold is outside search's top 50")
