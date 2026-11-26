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
