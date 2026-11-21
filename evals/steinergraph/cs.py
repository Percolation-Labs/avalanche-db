"""Surprise coherence, CS (Sirsh 22:37Z brief; bill's review M-20261120-224120): convergence of walks from different
seeds, scored against a degree null. The walk is linear in its start mass, so a question's walk is the mean of one walk
per seed, p_i. The null q_i is the same walk (same θ, β, F) from a uniform mass on every other passage with seed i's
door count: the exact mean over degree-matched random seeds, no sampling. Per seed pair and passage v:
    s_ij(v) = log p_i(v) p_j(v) / q_i(v) q_j(v)            (x: discounts hubs and small-world reach)
            − log A_ij,  A_ij = Σ_u p_i p_j / Σ_u q_i q_j   (a: also discounts twins that agree everywhere)
CS(v) is the mean (geometric) or max over pairs. A walk's CS is the mean over its top 5 beyond the seeds."""
import itertools
import numpy as np


def link_degree(g):
    """g.nd: the door count, which includes Beside and Near and is what hdeg uses (bill's review 5)."""
    return np.asarray(g.nd).astype(int)


def degree_classes(deg):
    """passage -> the other passages of its degree; if none, the nearest degree that has one (a rule, not a number)."""
    by = {}
    for i, d in enumerate(deg): by.setdefault(int(d), []).append(i)
    ds = sorted(by)
    def cls(i):
        d = int(deg[i]); own = [j for j in by[d] if j != i]
        if own: return own
        for dd in sorted(ds, key=lambda x: (abs(x - d), x)):
            if dd != d: return by[dd]
    return cls


def per_seed(g, seeds, theta, F, cls):
    """for each question: (seed list, p: n x k, q: n x k). F is n x m (one column per question) or None.
    q_i is the exact mean over degree-matched random seeds; q_i·q_j is the pair's null only for independent draws
    (two draws from one class can coincide, which is negligible and ignored; bill's review 3)."""
    cols, fc = [], []
    for c, ss in enumerate(seeds):
        for x in ss: cols.append([x]); fc.append(c)
        for x in ss: cols.append(cls(x)); fc.append(c)
    Fx = None if F is None else F[:, fc]
    P, _ = g.run(cols, theta, F=Fx)
    out, at = [], 0
    for ss in seeds:
        k = len(ss); out.append((ss, P[:, at:at + k], P[:, at + k:at + 2 * k])); at += 2 * k
    return out


def scores(p, q, seeds):
    """per passage (n,): {'xm','xM','am','aM'} = (no A | with A) x (mean | max over seed pairs) of
    s_ij(v) = log p_i(v)p_j(v) / q_i(v)q_j(v)  [− log A_ij].
    Seeds are excluded from the scored v and from A's sums (bill's review 1). v is scored only if every seed's walk
    reaches it, p_i(v) > 0 for all i, no epsilon (review 2); others are nan. Mean over pairs is geometric, so one
    pair that never meets drags v down; max shows single-pair convergence (review 4)."""
    n, k = p.shape
    keep = np.ones(n, bool); keep[list(seeds)] = False
    reach = keep & (p > 0).all(1) & (q > 0).all(1)
    pairs = list(itertools.combinations(range(k), 2))
    Sx = np.full((len(pairs), n), np.nan); Sa = np.full((len(pairs), n), np.nan)
    for r, (i, j) in enumerate(pairs):
        pp, qq = p[:, i] * p[:, j], q[:, i] * q[:, j]
        A = pp[keep].sum() / qq[keep].sum()
        lx = np.log(pp[reach] / qq[reach])
        Sx[r, reach] = lx; Sa[r, reach] = lx - np.log(A)
    out = {}
    with np.errstate(all="ignore"):
        for nm, S in (("x", Sx), ("a", Sa)):
            out[nm + "m"] = np.where(reach, S.mean(0), np.nan) if pairs else np.full(n, np.nan)
            out[nm + "M"] = np.where(reach, S.max(0), np.nan) if pairs else np.full(n, np.nan)
    out["reach"] = reach
    return out


def walk_score(sc, top):
    """mean over the walk's top 5 that every seed reaches; also returns how many of the top 5 were dropped."""
    v = [sc[t] for t in top if np.isfinite(sc[t])]
    return (float(np.mean(v)) if v else float("nan")), len(top) - len(v)
