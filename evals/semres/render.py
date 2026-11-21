"""Render a gen.world as text, token-free (templates and fixed word lists, no model). Each passage names its entity, its
topic and its links ("X <relation> Y."), so a reader can see what each door leads to. The question names the start, both
relations and the answer's type, never the answer. Every word list below is fixed, not tuned."""
import numpy as np

TOPICS = [
    ("river", "water delta flood bank current estuary"), ("composer", "symphony opera score orchestra sonata concert"),
    ("volcano", "lava eruption crater magma ash summit"), ("football club", "stadium league striker cup season goal"),
    ("monastery", "monk abbey prayer cloister relic pilgrimage"), ("railway", "station locomotive track signal freight timetable"),
    ("painter", "canvas fresco portrait gallery brush pigment"), ("island", "harbour reef lagoon ferry coast lighthouse"),
    ("university", "faculty lecture campus degree library professor"), ("newspaper", "editor headline column press reporter edition"),
    ("vineyard", "grape harvest cellar vintage barrel wine"), ("observatory", "telescope star orbit comet lens astronomer"),
]
RELS = ["was founded by", "is located in", "was named after", "is part of", "was designed by", "borders", "is owned by", "was built near"]
ISA = "is listed under"
SYL = ["ka", "lo", "mi", "ren", "tu", "va", "sor", "bel", "dan", "qui", "zor", "pel", "ost", "ima", "ur", "nev"]


def names(n, rng):
    out, seen = [], set()
    while len(out) < n:
        k = "".join(rng.choice(SYL, rng.integers(2, 4))).capitalize()
        if k not in seen: seen.add(k); out.append(k)
    return out


def render(w, seed):
    rng = np.random.default_rng(seed + 7)
    n = len(w["V"]); nm = names(n, rng)
    lures = {u for c in w["cases"] for u in c["lures"]}
    def kind(u):
        t = w["topic"][u]
        if u in w["hubs"]: return "a general category", ""
        if t >= 0: return f"a {TOPICS[t][0]}", "Known for its " + ", ".join(rng.choice(TOPICS[t][1].split(), 3, replace=False)) + "."
        return None, None
    rel = lambda r: ISA if r == w["isa"] else RELS[r]
    links = [[] for _ in range(n)]
    for (u, v), r in zip(w["edges"], w["rel"]):
        s = f"{nm[u]} {rel(r)} {nm[v]}."; links[u].append(s); links[v].append(s)
    text = []
    for u in range(n):
        k, d = kind(u)
        if u in lures:  # a lure is built to look like its case's question
            c = next(c for c in w["cases"] if u in c["lures"])
            k = f"a {TOPICS[w['topic'][c['s']]][0]}"; d = f"Often confused with {nm[c['s']]}; it {RELS[c['r1']]} and {RELS[c['r2']]} many places."
        text.append(f"{nm[u]} is {k}. {d} " + " ".join(links[u]))
    qs = []
    for c in w["cases"]:
        ta = w["topic"][c["a"]]
        qs.append(f"Which {TOPICS[ta][0]} is the one that the place {nm[c['s']]} {RELS[c['r1']]} {RELS[c['r2']]}?")
    return nm, text, qs
