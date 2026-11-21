"""$0 review check for SR-JW: an exact-phrase decider on the same rendered option sets. Score of a door = how many of the
question's phrases its passage contains: each relation phrase, the start's name, and 'is a <answer type>'."""
import numpy as np, gen, render
from sr1b import ATYPE, NOISE
first = {1: [0, 0], 2: [0, 0]}; ties = {1: 0, 2: 0}
for sd in (41001, 41002, 41003, 41004):
    w = gen.world(sd, NOISE, ATYPE); nm, text, qs = render.render(w, sd); E = np.array(w["edges"])
    for c, q in zip(w["cases"], qs):
        ta = render.TOPICS[w["topic"][c["a"]]][0]
        phr = [render.RELS[c["r1"]], render.RELS[c["r2"]], nm[c["s"]], f"is a {ta}."]
        for hop, (u, gold, read) in ((1, (c["s"], c["b"], {c["s"]})), (2, (c["b"], c["a"], {c["s"], c["b"]}))):
            nb = sorted({int(v) for x, y in E for v in ((y,) if x == u else (x,) if y == u else ())})
            sc = np.array([sum(p in text[v] for p in phr) - (100 if v in read else 0) for v in nb], float)  # unread only, like Jev's read mask
            g = nb.index(gold); best = sc.max()
            first[hop][0] += int(sc[g] == best); first[hop][1] += 1; ties[hop] += int(sc[g] == best and (sc == best).sum() > 1)
for h in (1, 2): print(f"hop {h}: phrase decider ranks the chain door first (ties included) {first[h][0]}/{first[h][1]}, of which tied {ties[h]}")
