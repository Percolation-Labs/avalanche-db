"""Vector operations for probes (REM-1341, Sirsh 21 Nov 16:37Z): a small library, one contract per operation, tested
across the semres scenarios (synthetic worlds, SR-J/SR-K option sets, SR-E pools). No operation has a free constant:
anything a caller would tune is either an input measured elsewhere (and named at the call) or fitted by `fit_*`
with grouped cross-validated selection, which is a rule, not a knob.

Conventions: vectors are rows of float arrays; every returned probe is unit length; `w` arguments are non-negative
weights that the caller derives (e.g. idf), never hand-set.

  unit(V)                     rows scaled to length 1
  combine(V, w=None)          weighted mean of rows, unit: Average PRF when w is None (Li et al., TOIS 2023)
  rocchio(q, V, w=None)       unit(q + combine(V, w)): the query kept at equal weight with its feedback, no α
  idf(df, n)                  log(n / df): the rarity weight for a key held by df of n passages
  pivot_onto(x, D)            x's component in span(D), unit: keep only the named directions (e.g. relations)
  pivot_out(x, D)             x minus its component in span(D), unit: remove directions (e.g. the corpus centre)
  centre(V)                   the corpus mean direction, for pivot_out against drift
  warp(x, W)                  unit(x @ W): a learned linear map of probe space; W = I is no warp
  diag_scores(Q, V, w)        Σ_d w_d q_d v_d per row pair: a dimension-reweighted cosine (a diagonal warp)
  fit_diag(X, y, groups)      w for diag_scores by L2 logistic regression on q⊙v features; the L2 strength is chosen
                              by grouped 5-fold log-loss over a decade grid (folds by question; the choice is the
                              data's, the grid spans it)
"""
import numpy as np


def unit(V):
    V = np.asarray(V, float)
    n = np.linalg.norm(V, axis=-1, keepdims=True)
    return np.divide(V, n, out=np.zeros_like(V), where=n > 0)


def combine(V, w=None):
    V = unit(V); w = np.ones(len(V)) if w is None else np.asarray(w, float)
    return unit((w[:, None] * V).sum(0) / max(w.sum(), 1e-300))


def rocchio(q, V, w=None):
    return unit(unit(q) + combine(V, w))


def idf(df, n):
    return np.log(n / np.asarray(df, float))


def _basis(D):
    D = np.atleast_2d(np.asarray(D, float))
    Qb, _ = np.linalg.qr(D.T)
    return Qb  # columns span D's rows


def pivot_onto(x, D):
    B = _basis(D); return unit((x @ B) @ B.T)


def pivot_out(x, D):
    B = _basis(D); return unit(x - (x @ B) @ B.T)


def centre(V):
    return combine(V)


def warp(x, W):
    return unit(np.asarray(x, float) @ W)


def diag_scores(Q, V, w):
    return (unit(Q) * unit(V)) @ np.asarray(w, float)


def fit_diag(X, y, groups):
    """X: rows q⊙v (n × d); y: targets in [0, 1] (a probability or a 0/1 label); groups: question id per row.
    Returns (w, b, C, cv_logloss). Soft targets are fitted by duplicating each row as a weighted 1 and 0."""
    from sklearn.linear_model import LogisticRegression
    X = np.asarray(X, float); y = np.asarray(y, float); g = np.asarray(groups)
    XX = np.vstack([X, X]); yy = np.r_[np.ones(len(y)), np.zeros(len(y))]; sw = np.r_[y, 1 - y]
    from sklearn.model_selection import GroupKFold
    folds = list(GroupKFold(n_splits=min(5, len(np.unique(g)))).split(X, y, g))
    best = None
    for C in 10.0 ** np.arange(-3, 4):
        ll = 0.0
        for tr0, te0 in folds:
            tr, te = np.r_[tr0, tr0 + len(y)], np.r_[te0, te0 + len(y)]
            m = LogisticRegression(C=C, max_iter=2000).fit(XX[tr], yy[tr], sample_weight=sw[tr])
            p = np.clip(m.predict_proba(XX[te])[:, 1], 1e-9, 1 - 1e-9)
            ll -= (sw[te] * (yy[te] * np.log(p) + (1 - yy[te]) * np.log(1 - p))).sum()
        if best is None or ll < best[1]: best = (C, ll)
    m = LogisticRegression(C=best[0], max_iter=2000).fit(XX, yy, sample_weight=sw)
    return m.coef_[0], float(m.intercept_[0]), best[0], best[1]


if __name__ == "__main__":  # contract checks, no data
    rng = np.random.default_rng(0); d = 16
    q = unit(rng.normal(size=d)); V = unit(rng.normal(size=(5, d))); D = unit(rng.normal(size=(2, d)))
    assert abs(np.linalg.norm(combine(V)) - 1) < 1e-9 and abs(np.linalg.norm(rocchio(q, V)) - 1) < 1e-9
    assert np.allclose(combine(V, np.r_[1, 0, 0, 0, 0]), V[0])
    po, pt = pivot_onto(q, D), pivot_out(q, D)
    assert np.allclose(pt @ _basis(D), 0, atol=1e-9) and np.allclose(po, unit(po @ _basis(D) @ _basis(D).T))
    assert np.allclose(warp(q, np.eye(d)), q)
    assert np.allclose(diag_scores(q[None], V, np.ones(d)), V @ q)
    print("vecops contracts hold")
