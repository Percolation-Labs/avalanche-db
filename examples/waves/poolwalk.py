"""poolwalk.py -- no walk: the views the question bears on, pooled, then judged together.

viewwalk.py found Jev judges membership well and chooses the next view badly, and that judging
everything read so far together fixed card testing but broke busy afternoons: a mild answer sank
beside louder oddities the question does not ask about (README, "Judging everyone read so far").
The README's guess was that the pool should hold only keys from views the question bears on.

Here relevance is not a sequence of choices. One request asks Jev, for every view the grammar
produces at once (description, count, top keys with their most telling row), whether it bears on
the question: a Noul per view. The pool is the union of the members of the views it keeps, at the
views' starting tightness. A second request judges the whole pool side by side, with the same
Nouls viewwalk.py uses (jev_keep). Two requests per question; nothing is chosen in order.

    python3 poolwalk.py questions/<q>.json [--sample 3] [--cap 80]

--cap bounds the pool; over it, each relevant view gives its highest keys in turn until the cap.
"""
import json, os, sqlite3, sys
import viewwalk as vw


def relevant(question, grammar, rows, sample):
    menu, back = {}, {}
    for name, v in grammar.items():
        mem = vw.members(v, vw.KS[vw.K0])
        if not mem:
            continue
        top = sorted(mem, key=lambda k: (-mem[k], k))[:sample]
        eg = [f"{k}: " + (vw.evidence(rows, k, 1)[1] if len(vw.evidence(rows, k, 1)) > 1 else "") for k in top]
        s = vw.slug(name)
        menu[s] = {"view": v[0] + (f", k={vw.KS[vw.K0]}" if v[2] == "outlier" else ""), "customers": len(mem), "for_example": eg}
        back[s] = name
    qs = {s: {"type": "noul", "instructions": f"Would the customers in `views.{s}` help answer `question`: does what this view "
              "selects bear on the activity the question asks about?",
              "criteria": {"true": "it bears on the question", "false": "it selects something the question does not ask about"}}
          for s in menu}
    ans, _ = vw.jev({"question": question, "views": menu}, qs)
    return {back[s]: float(ans[s]["noul"]) for s in menu}


def run(qfile, sample=3, cap=80):
    plan = json.load(open(qfile))
    db = sqlite3.connect(os.path.join(vw.HERE, plan["set_data"]))
    fact, rows = vw.load(db, plan.get("key_table", "customers"))
    grammar = vw.views(rows, plan["question"])
    vw.GRAMMAR.clear()
    vw.GRAMMAR.update(grammar)
    gold = set(plan["gold"])
    print(f"question: {plan['question']}\n{len(grammar)} views from the schema of {fact}")
    rel = relevant(plan["question"], grammar, rows, sample)
    for name, p in sorted(rel.items(), key=lambda x: -x[1]):
        mem = vw.members(grammar[name], vw.KS[vw.K0])
        print(f"  {'*' if p >= 0.5 else ' '} {p:.2f}  {name}: {len(mem)} keys, gold {len(gold & set(mem))}")
    chosen = [n for n, p in sorted(rel.items(), key=lambda x: -x[1]) if p >= 0.5]
    lists = [sorted(vw.members(grammar[n], vw.KS[vw.K0]).items(), key=lambda x: (-x[1], x[0])) for n in chosen]
    pool, i = {}, 0
    while len(pool) < cap and any(i < len(l) for l in lists):  # round-robin: each relevant view's highest keys in turn
        for n, l in zip(chosen, lists):
            if i < len(l) and len(pool) < cap:
                pool.setdefault(l[i][0], n)
        i += 1
    print(f"pool: {len(pool)} keys from {len(chosen)} views; gold in pool {len(gold & set(pool))} of {len(gold)}")
    if not pool:
        print("result set: (empty)\nagainst the planted answer: recall 0.00")
        return
    kept = vw.jev_keep(plan["question"], "customers from the views that bear on the question", {k: 0 for k in pool}, rows)
    print("    p(keep): " + ", ".join(f"{k} {p:.2f}" for k, p in sorted(vw.jev_keep.last.items(), key=lambda x: -x[1])[:12]))
    ids = sorted(k for k, y in kept.items() if y)
    hit = len(gold & set(ids))
    print(f"result set: {', '.join(ids) or '(empty)'}")
    print(f"against the planted answer {sorted(gold)[:12]}{' ...' if len(gold) > 12 else ''}: recall {hit / len(gold):.2f}, "
          f"precision {hit / max(1, len(ids)):.2f}; pool {len(pool)}")
    if vw.JEV_SPENT["requests"]:
        print(f"Jev this run: {vw.JEV_SPENT}")


if __name__ == "__main__":
    a = sys.argv
    run(a[1], int(a[a.index("--sample") + 1]) if "--sample" in a else 3, int(a[a.index("--cap") + 1]) if "--cap" in a else 80)
