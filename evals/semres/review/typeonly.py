import numpy as np, gen, render
from sr1b import ATYPE, NOISE
out = []
for sd in (41001, 41002, 41003, 41004):
    w = gen.world(sd, NOISE, ATYPE); nm, text, qs = render.render(w, sd); E = np.array(w["edges"])
    for c in w["cases"]:
        ta = render.TOPICS[w["topic"][c["a"]]][0]; u = c["b"]
        nb = sorted({int(v) for x, y in E for v in ((y,) if x == u else (x,) if y == u else ())}); nb = [v for v in nb if v != c["s"]]
        t = [v for v in nb if f"is a {ta}." in text[v]]
        out.append((len(t), c["a"] in t, len(nb)))
print("hop 2, unread doors whose passage says 'is a <answer type>': counts", [o[0] for o in out], "; chain door among them", sum(o[1] for o in out), "/", len(out))
print("type-only decider picks the chain door uniquely in", sum(o[0] == 1 and o[1] for o in out), "/ 16")
