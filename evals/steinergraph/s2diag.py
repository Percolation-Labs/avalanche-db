import json,sys,collections
import numpy as np
import l1, s2
scr=sys.argv[1]
for gn,sets in (("mq",("mq",)),("p8",("cards","prs"))):
    rows=[json.loads(l) for l in open(f"{scr}/dream/d1/graph-{gn}.jsonl")]
    g=l1.G(rows); L=s2.links(g)
    for c in sets:
        _,test=l1.load(scr,g,c); C=collections.Counter(); adj=0; tot=0
        for qid,seeds,gi,_,_ in test:
            gl={x for x in gi if x>=0}-set(seeds)
            if not gl: continue
            cost,_=s2.tstar(L,seeds,gl); C[min(cost,3)]+=1
            for x in gl:
                tot+=1; adj+= L[x][:,seeds].nnz>0
        print(c,"T* cost (0/1/2/3+):",dict(sorted(C.items())),f"gold-beyond-seeds adjacent to a seed: {adj}/{tot}",flush=True)
