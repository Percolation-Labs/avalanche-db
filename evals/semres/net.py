"""The walk as an electrical network (Doyle & Snell). A link u–v of type e has conductance
    c_uv = w_e · g(u) · g(v),
where w_e is structure (the edge type's weight) and g is semantics. The walk steps u → v with probability
c_uv / C_u, C_u = Σ_w c_uw, so g(u) cancels and the step is ∝ w_e · g(v). c is symmetric, so the walk is reversible
and this is a true resistor network: resistance 1/c, Rayleigh monotonicity holds.
Stopping (the walk's restart α) is a leak from every node to ground, with conductance α/(1−α) · C_u.
Reach probability h_v(a) = P(a walker landing on a hits v before it stops) is the voltage at a with v held at 1 V and
ground at 0 V. For all pairs at once: G = (I − (1−α) P)^-1 counts expected visits, and h_v(a) = G[a, v] / G[v, v]."""
import numpy as np


def transition(n, edges, c):
    """edges: list of (u, v) undirected; c: conductance per edge. Returns the dense row-stochastic P and C_u."""
    A = np.zeros((n, n))
    for (u, v), x in zip(edges, c):
        A[u, v] += x; A[v, u] += x
    C = A.sum(1)
    P = np.divide(A, C[:, None], out=np.zeros_like(A), where=C[:, None] > 0)
    return P, C


def reach(P, alpha):
    """h[a, v]: probability that a walker landing on a hits v before stopping. Exact (one dense inverse)."""
    n = P.shape[0]
    G = np.linalg.inv(np.eye(n) - (1 - alpha) * P)
    h = G / np.diag(G)[None, :]
    np.fill_diagonal(h, 1.0)
    return h


def monte_carlo(P, alpha, a, walkers, rng):
    """the check that can fail: fraction of walkers from a that hit each node before stopping."""
    n = P.shape[0]
    cum = np.cumsum(P, 1)
    hit = np.zeros(n)
    for _ in range(walkers):
        seen = {a}; u = a
        while rng.random() >= alpha and cum[u, -1] > 0:
            u = int(np.searchsorted(cum[u], rng.random() * cum[u, -1], side="right"))
            seen.add(u)
        hit[list(seen)] += 1
    return hit / walkers


def conductance(w, probe, semantic=True):
    """(P, C) for one probe vector. Structure: every edge type weighs 1 (the generator's ontology has no preferred type).
    Semantics, the Bayes decider for this generator (bill's review 1): on-topic and off-topic cos are equal-variance
    Gaussians with variance 1/DIM, so log LR = DIM · (μ1 − μ0) · cos + const.
      nodes: g(v) = exp(DIM·μ·cos(probe, v)), μ = mean cos(probe, passages of the landing passage's topic) − mean cos to the rest
      edges: exp(DIM·μ_r·cos(probe, r_e)), μ_r = cos(probe, its best relation) − mean cos to the other relations
    The landing passage is search's top 1 for the probe. Both μ are measured on the world, not chosen."""
    V, R, top = w["V"], w["R"], np.array(w["topic"])
    E = np.array(w["edges"]); rel = np.array(w["rel"])
    if not semantic: return transition(len(V), w["edges"], np.ones(len(E)))
    d = V.shape[1]
    cv = V @ probe; land = int(np.argmax(cv)); on = top == top[land]
    mu = cv[on].mean() - cv[~on].mean() if (~on).any() else 0.0
    cr = R @ probe; best = int(np.argmax(cr)); mur = cr[best] - np.delete(cr, best).mean()
    logg = d * mu * cv
    loge = d * mur * cr[rel] + logg[E[:, 0]] + logg[E[:, 1]]
    c = np.exp(loge - loge.max())  # a common factor cancels in P
    return transition(len(V), w["edges"], c)


def arrival(P, alpha, src, targets, steps):
    """M[t, j]: probability that a walker started from mass src (n,) has hit targets[j] by step t without stopping.
    One row of mass per target, each absorbed at its own target, so all targets run in one matrix product per step."""
    targets = np.asarray(targets); k = len(targets); r = np.arange(k)
    m = np.tile(np.asarray(src, float), (k, 1))
    got = m[r, targets].copy(); m[r, targets] = 0
    M = np.zeros((steps + 1, k)); M[0] = got
    for t in range(1, steps + 1):
        m = (1 - alpha) * (m @ P); got = got + m[r, targets]; m[r, targets] = 0; M[t] = got
    return M


def edge_walk(w, P, probe_turn=True):
    """Inductance: a second-order walk whose state is the directed link (u → v) just taken. The walker carries a
    semantic current, the displacement v − u. Continuing to w is weighted P[v, w] · exp(DIM·μ_nn·cos(v − u, w − v)):
    keeping the direction is cheap and reversing it (w = u, cos = −1) is dear, as an inductor resists a change of
    current. μ_nn = mean cos between passages of one topic − mean cos across topics, measured on the world, the same
    Bayes unit as conductance. (A first draft used cos(u, w), which rewards going straight back: caught before any run.) Returns (Q sparse over states, states, by_head) where
    by_head[v] lists the states that arrive at v."""
    import scipy.sparse as sp
    V, top = w["V"], np.array(w["topic"])
    n = len(V); d = V.shape[1]
    reg = top >= 0
    rng = np.random.default_rng(0)
    i, j = rng.integers(0, reg.sum(), (2, 20000)); Vi = V[reg]; tt = top[reg]
    cs = (Vi[i] * Vi[j]).sum(1); same = tt[i] == tt[j]
    mu = cs[same].mean() - cs[~same].mean()
    nb = [np.nonzero(P[v])[0] for v in range(n)]
    states = [(u, v) for u in range(n) for v in nb[u]]
    idx = {s: k for k, s in enumerate(states)}
    ri, ci, x = [], [], []
    for k, (u, v) in enumerate(states):
        ws = nb[v]
        if not len(ws): continue
        din = V[v] - V[u]; dout = V[ws] - V[v]
        cosd = (dout @ din) / np.maximum(np.linalg.norm(dout, axis=1) * np.linalg.norm(din), 1e-12)
        wt = P[v, ws] * np.exp(d * mu * cosd if probe_turn else 0)
        wt = wt / wt.sum()
        ri += [k] * len(ws); ci += [idx[(v, int(q))] for q in ws]; x += list(wt)
    Q = sp.csr_matrix((x, (ri, ci)), shape=(len(states), len(states)))
    by_head = [[] for _ in range(n)]
    for k, (u, v) in enumerate(states): by_head[v].append(k)
    return Q, states, by_head, float(mu)


def edge_start(P, states, a):
    """mass on states (a → w) after the first step, which is the node walk's step from a."""
    m = np.zeros(len(states))
    for k, (u, v) in enumerate(states):
        if u == a: m[k] = P[a, v]
    return m


def edge_arrival(Q, alpha, m0, landed, by_head, targets, steps):
    """M[t, j] for the edge walk: hit by step t without stopping. m0 is the state mass after step 1, before step 1's
    leak; the landing node counts as hit at t = 0. Batched like arrival: one row per target."""
    import scipy.sparse as sp
    targets = list(targets); k = len(targets)
    H = sp.csr_matrix((np.ones(sum(len(by_head[v]) for v in targets)),
                       ([j for j, v in enumerate(targets) for _ in by_head[v]], [q for v in targets for q in by_head[v]])),
                      shape=(k, Q.shape[0]))
    keep = 1 - H.toarray()
    m = (1 - alpha) * np.tile(m0, (k, 1))
    M = np.zeros((steps + 1, k))
    land = np.array([v == landed for v in targets], float)
    got = land + (1 - land) * (m * (1 - keep)).sum(1); m = m * keep
    M[0] = land; M[1:] = got
    for t in range(2, steps + 1):
        m = (1 - alpha) * np.asarray((sp.csr_matrix(m) @ Q).todense()); got = got + (1 - land) * (m * (1 - keep)).sum(1); m = m * keep; M[t] = got
    return M
