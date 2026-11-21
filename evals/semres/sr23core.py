"""SR (2), (3) and inductance readouts: pure functions over reach vectors h (n,) and arrival curves M (steps,).
(2) combined percolation of k probes at matched start mass; (3) collision (AND) vs coverage (OR), raw and over a
degree null; inductance as the arrival time constant. No constants beyond the definitions named."""
import numpy as np


def combined(H):
    """H: k × n reach probabilities of independent walkers. P(v reached by ≥1) = 1 − Π_k (1 − h_k(v))."""
    return 1.0 - np.prod(1.0 - H, axis=0)


def matched_mass(H, k_whole=1):
    """Equal budget: one whole-question walker vs k probes, each a walker with probability 1/k of being launched
    (so the expected number of walkers is 1 in both arms). P(v reached) = 1 − Π_k (1 − h_k(v)/k)."""
    k = H.shape[0]
    return 1.0 - np.prod(1.0 - H / k, axis=0)


def collision(H):
    """Mean over probe pairs of h_i(v)·h_j(v): two pulses meeting at v (AND)."""
    k = H.shape[0]
    if k < 2: return np.full(H.shape[1], np.nan)
    pr = [H[i] * H[j] for i in range(k) for j in range(i + 1, k)]
    return np.mean(pr, axis=0)


def collision_lift(H, Q):
    """log of collision over a degree null's collision (Q: k × n reach from degree-matched starts); nan where 0."""
    c, cq = collision(H), collision(Q)
    with np.errstate(all="ignore"):
        return np.where((c > 0) & (cq > 0), np.log(c / cq), np.nan)


def coverage(Hgold):
    """Hgold: k × g reach at the gold passages. P(every gold reached by some probe) = Π_g [1 − Π_k (1 − h)]."""
    return float(np.prod(1.0 - np.prod(1.0 - Hgold, axis=0)))


def time_constant(M):
    """steps until the arrival curve M(t) (non-decreasing) first reaches (1 − 1/e) of its last value; nan if none."""
    M = np.asarray(M, float)
    if M[-1] <= 0: return float("nan")
    hit = np.nonzero(M >= (1 - np.exp(-1)) * M[-1])[0]
    return float(hit[0] + 1) if len(hit) else float("nan")


def rank_of(score, idx, exclude=()):
    """1-based rank of each idx under score (descending), excluding given nodes; ties take the mean rank."""
    s = np.asarray(score, float).copy(); s[list(exclude)] = -np.inf; s = np.where(np.isnan(s), -np.inf, s)
    out = []
    for i in idx:
        out.append(float((s > s[i]).sum() + ((s == s[i]).sum() + 1) / 2))
    return out
