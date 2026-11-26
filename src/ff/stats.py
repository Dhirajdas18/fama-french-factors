"""Return statistics and regressions shared by the reports and mirrored in ff.js."""

import numpy as np
import pandas as pd


def nw_se(X: np.ndarray, e: np.ndarray, lags: int) -> np.ndarray:
    """Newey-West (Bartlett) standard errors of OLS coefficients."""
    n = len(e)
    xe = X * e[:, None]
    S = xe.T @ xe
    for k in range(1, lags + 1):
        g = xe[k:].T @ xe[:-k]
        S += (1 - k / (lags + 1)) * (g + g.T)
    XtXi = np.linalg.inv(X.T @ X)
    V = XtXi @ S @ XtXi
    return np.sqrt(np.diag(V) * n / (n - X.shape[1]))


def ols(y, X, lags: int = 3) -> dict:
    """OLS of y on [1, X] with Newey-West t-statistics: coefficients (alpha first), t, R²."""
    y = np.asarray(y, float)
    X = np.column_stack([np.ones(len(y)), np.asarray(X, float).reshape(len(y), -1)])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    se = nw_se(X, e, lags)
    r2 = 1 - (e @ e) / np.sum((y - y.mean()) ** 2)
    return {"b": b, "t": b / se, "r2": float(r2), "n": len(y)}


def summary(r: pd.Series) -> dict:
    """Monthly decimal returns: mean and volatility a year (×12, ×√12), compound growth a year
    over the calendar span, Newey-West t of the mean (3 lags), share of positive months, worst
    month, worst fall of the compounded value and worst 12 months."""
    r = r.dropna()
    n = len(r)
    years = n / 12  # one row per calendar month, so n / 12 is calendar time
    wealth = (1 + r).cumprod()
    dd = float((wealth / wealth.cummax() - 1).min())
    y12 = (1 + r).rolling(12).apply(np.prod, raw=True) - 1
    return {"n": n, "mean": float(r.mean() * 12), "vol": float(r.std() * np.sqrt(12)),
            "cagr": float(wealth.iloc[-1] ** (1 / years) - 1),
            "t": float(ols(r.to_numpy(), np.empty((n, 0)))["t"][0]),
            "pos": float((r > 0).mean()), "worst": float(r.min()), "dd": dd,
            "worst12": float(y12.min()), "sharpe": float(r.mean() / r.std() * np.sqrt(12))}


def grs(excess: np.ndarray, factors: np.ndarray) -> dict:
    """Gibbons-Ross-Shanken test that all N intercepts are zero when T x N excess returns are
    regressed on T x L factor returns: (T - N - L) / N x a' S^-1 a / (1 + m' W^-1 m), with S the
    residual and W the factor covariance (both divided by T) and m the factor means; F(N, T-N-L)
    under normal, independent errors. Also the intercepts and their mean absolute value."""
    from scipy.stats import f as fdist

    R = np.asarray(excess, float)
    F = np.asarray(factors, float).reshape(len(R), -1)
    T, N = R.shape
    L = F.shape[1]
    X = np.column_stack([np.ones(T), F])
    B, *_ = np.linalg.lstsq(X, R, rcond=None)
    a = B[0]
    E = R - X @ B
    S = E.T @ E / T
    m = F.mean(axis=0)
    W = np.atleast_2d(np.cov(F.T, bias=True))
    stat = (T - N - L) / N * (a @ np.linalg.solve(S, a)) / (1 + m @ np.linalg.solve(W, m))
    return {"grs": float(stat), "p": float(fdist.sf(stat, N, T - N - L)), "alpha": a,
            "mean_abs_alpha": float(np.mean(np.abs(a))), "T": T, "N": N,
            "sharpe_alpha": float(np.sqrt(a @ np.linalg.solve(S, a)))}
