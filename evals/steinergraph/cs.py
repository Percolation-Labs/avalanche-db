"""Coherence as surprising convergence (CS): Sirsh's 20 Nov definition, the measure james (Q1, Q3) and bill (Q2) share.

Coherence is things that had no reason to agree converging anyway. Here:
  p_i   L1's walk from seed i alone (same θ, F and ITERS as the question's walk; the walk is linear in its start mass).
  q_i   the same walk from a uniform mass on every passage with seed i's link degree: the EXACT mean of p_i over
        degree-matched random seeds. No sampling. A degree with no other passage uses the nearest degree that has one.
  lift_ij(v) = log p_i(v)p_j(v) − log q_i(v)q_j(v)   (E over independent matched draws of p_i'p_j' is q_i q_j)
  A_ij       = Σ_u p_i p_j / Σ_u q_i q_j over the scored set: how much the pair agrees everywhere (twin seeds)
  cs_ij(v)   = lift_ij(v) − log A_ij
Scored set: non-seed passages every seed's walk reaches (p_i > 0 ∀i): no epsilon. Seeds are outside A's sums too.
Mean over pairs and max over pairs are both returned. NB: within one question, −log A_ij is a constant per pair, so
cs_mean ranks passages exactly as lift_mean does; A only changes the max arm and comparisons across θ or graphs."""
import numpy as np

import s2


def link_degree(g):
    """Passages joined to each passage by a walkable link: keys of width 2–100, Beside and Near (s2.links)."""
    return np.asarray(s2.links(g).sum(1)).ravel().astype(int)


def degree_classes(deg):
    """degree -> passages with it; a degree held by one passage only borrows the nearest degree that has ≥2."""
    by = {}
    for i, d in enumerate(deg): by.setdefault(int(d), []).append(i)
    multi = np.array(sorted(d for d, v in by.items() if len(v) >= 2))

    def cls(d):
        d = int(d)
        if len(by.get(d, [])) >= 2: return by[d]
        nd = multi[np.argmin(np.abs(multi - d))]  # ties to the lower degree (argmin order)
        return sorted(by.get(d, []) + by[int(nd)])
    return cls


def per_seed(g, seeds, theta, F=None, deg=None, cls=None):
    """(p, q): n × k per-seed walks and their degree-null walks. F: n × 1 search prior column or None."""
    if deg is None: deg = link_degree(g)
    if cls is None: cls = degree_classes(deg)
    starts = [[s] for s in seeds] + [cls(deg[s]) for s in seeds]
    P, _ = g.run(starts, theta, F=F)
    k = len(seeds)
    return P[:, :k], P[:, k:]


def score(p, q, seeds):
    """Per-passage arrays over all n (nan outside the scored set): lift_mean, lift_max, cs_mean, cs_max; ok mask; A."""
    n, k = p.shape
    ok = (p > 0).all(1); ok[list(seeds)] = False
    lp, lq = np.full((n, k), np.nan), np.full((n, k), np.nan)
    lp[ok] = np.log(p[ok]); lq[ok] = np.log(q[ok])
    L, C, A = [], [], {}
    for i in range(k):
        for j in range(i + 1, k):
            lift = lp[:, i] + lp[:, j] - lq[:, i] - lq[:, j]
            a = (p[ok, i] * p[ok, j]).sum() / (q[ok, i] * q[ok, j]).sum()
            A[(i, j)] = float(a); L.append(lift); C.append(lift - np.log(a))
    L, C = np.array(L), np.array(C)
    return dict(lift_mean=L.mean(0), lift_max=L.max(0), cs_mean=C.mean(0), cs_max=C.max(0), ok=ok, A=A)
