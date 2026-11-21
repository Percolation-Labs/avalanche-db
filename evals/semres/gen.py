"""Token-free world for semantic resistance (Sirsh 21 Nov 13:15Z). Every number below describes the world. None is a
setting of the measure, and none is tuned against a result. Four seeds, fixed before any run.
World:
  - TOPICS unit topic vectors in DIM dimensions. NODES passages, each with a topic and a vector = topic + noise
    (cos to its topic ≈ .7).
  - RELS relation types, each a unit vector (the edge's semantics; the engineered ontology's edge types).
  - Links: each passage gets HOMO links to passages of its own topic (homogeneous clusters) and one link to a random
    other passage, each with a random relation.
  - HUBS generic passages (vector = mean of all topics + noise, so mildly like everything), each joined by the 'is_a'
    relation to HUB_DEG random passages.
Four planted chains s –r1→ b –r2→ a. The question x = s + r1 + r2 names the start and both relations, never the answer,
as multi-hop questions do. The probes, for an intelligent questioner, are x, s + r1 (find the bridge) and r2 (the
second hop, without knowing the bridge). Gold = {s, b, a}, and the Steiner tree is the chain itself.
  A semantic:  a shares s's topic, so the answer looks like the question.
  B bridge:    a is in a topic far from s, and b in a third, so the answer looks nothing like the question.
  C hub lure:  as B, and s is also joined to 3 hubs, so most structural mass leaves through hubs.
  D cluster lure: as B, and s is joined to a tight 8-passage cluster built to look like x (off the chain)."""
import numpy as np

DIM, TOPICS, NODES, RELS, HOMO, HUBS, HUB_DEG = 64, 12, 1200, 8, 3, 10, 60
SEEDS = (20261121, 20261122, 20261123, 20261124)  # four worlds, each with all four case types (bill's review 3)


def unit(v): return v / np.linalg.norm(v, axis=-1, keepdims=True)


def world(seed=SEEDS[0], noise=1.0, atype=0.0):
    """noise scales the passage noise around its topic (1.0 = SR1's world, cos to topic ≈ .7).
    atype is how much of the answer's topic (its type) the question carries: x = s + r1 + r2 + atype·T[t_a].
    SR1 used 0; SR1b calibrates it to MuSiQue's measured cos gap between hop 1 and hop 2."""
    rng = np.random.default_rng(seed)
    T = unit(rng.normal(size=(TOPICS, DIM)))
    R = unit(rng.normal(size=(RELS + 1, DIM)))  # last one is 'is_a'
    ISA = RELS
    topic = list(rng.integers(0, TOPICS, NODES))
    V = [unit(T[t] + noise * rng.normal(size=DIM) / np.sqrt(DIM)) for t in topic]
    edges, rel = [], []
    def link(u, v, r): edges.append((u, v)); rel.append(r)
    by = {t: [i for i in range(NODES) if topic[i] == t] for t in range(TOPICS)}
    for i in range(NODES):
        for j in rng.choice([x for x in by[topic[i]] if x != i], HOMO, replace=False): link(i, int(j), int(rng.integers(RELS)))
        link(i, int(rng.integers(NODES)), int(rng.integers(RELS)))
    hubs = []
    for _ in range(HUBS):
        h = len(V); V.append(unit(T.mean(0) + rng.normal(size=DIM) / np.sqrt(DIM))); topic.append(-1); hubs.append(h)
        for j in rng.choice(NODES, HUB_DEG, replace=False): link(h, int(j), ISA)
    def new(t, vec=None):
        V.append(unit(T[t] + noise * rng.normal(size=DIM) / np.sqrt(DIM)) if vec is None else vec); topic.append(t)
        u = len(V) - 1
        for j in rng.choice(by[t], HOMO, replace=False): link(u, int(j), int(rng.integers(RELS)))  # it lives in its topic
        return u
    cases = []
    tp = rng.permutation(TOPICS)
    for k, name in enumerate(("A semantic", "B bridge", "C hub lure", "D cluster lure")):
        t_s, t_b, t_a = int(tp[3 * k % TOPICS]), int(tp[(3 * k + 1) % TOPICS]), int(tp[(3 * k + 2) % TOPICS])
        if name.startswith("A"): t_a = t_s
        r1, r2 = (int(x) for x in rng.choice(RELS, 2, replace=False))
        s = new(t_s); b = new(t_b); a = new(t_a)
        link(s, b, r1); link(b, a, r2)
        x = unit(V[s] + R[r1] + R[r2] + atype * T[t_a])
        lures = []
        if name.startswith("C"):
            for h in rng.choice(hubs, 3, replace=False): link(s, int(h), ISA)
        if name.startswith("D"):
            for _ in range(8):
                u = len(V); V.append(unit(x + rng.normal(size=DIM) / (2 * np.sqrt(DIM)))); topic.append(-2); lures.append(u)
            for i, u in enumerate(lures):
                for w in lures[i + 1:]: link(u, w, int(rng.integers(RELS)))
            link(s, lures[0], r1)
        probes = {"x": x, "s+r1": unit(V[s] + R[r1]), "r2": R[r2]}
        cases.append(dict(name=name, s=s, b=b, a=a, r1=r1, r2=r2, lures=lures, probes=probes))
    # each link's own semantics: its relation plus the same noise passages carry (SR1b; SR1 used the bare relation)
    ev = unit(R[np.array(rel)] + noise * np.random.default_rng(seed + 1).normal(size=(len(rel), DIM)) / np.sqrt(DIM))
    return dict(V=np.array(V), topic=topic, R=R, edges=edges, rel=rel, EV=ev, hubs=hubs, cases=cases, isa=ISA)


if __name__ == "__main__":
  for sd in SEEDS:
    w = world(sd)
    print(f"seed {sd}: {len(w['V'])} passages, {len(w['edges'])} links, {len(w['hubs'])} hubs")
    for c in w["cases"]:
        x = c["probes"]["x"]
        print("  ", c["name"], {k: round(float(w["V"][c[k]] @ x), 3) for k in ("s", "b", "a")})
