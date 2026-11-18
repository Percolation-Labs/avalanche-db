import json,sys
# Dev traces and test questions are in the session scratchpad; run from there (paths below are relative to it).
def L(p): return [json.loads(l) for l in open(p)]
def golds(g): return set(g.keys()) if isinstance(g,dict) else set(g)
for name,dev,test in [("cards","dream/dt-cards.jsonl","floor/q-cards.jsonl"),("prs","dream/dt-prs.jsonl","floor/q-prs-test.jsonl"),("mq","dream/dt-mq.jsonl","floor/q-musique-questions.jsonl")]:
    D=L(dev); T=L(test)
    dg=set().union(*[golds(r["gold"]) for r in D])
    dr=set().union(*[set(r.get("docs",[])) for r in D])
    tg=[golds(r["gold"]) for r in T]
    allg=set().union(*tg)
    q_any=sum(1 for g in tg if g&dg)/len(tg)
    print(name,"test gold docs",len(allg),"| in dev gold",len(allg&dg),"| read in dev walks",len(allg&dr),"| test qs with any gold that was dev gold %.2f"%q_any)
