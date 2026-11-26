"""Single NSE stocks on CAPM, three factors and four factors: fit, out-of-sample explanation and
stability of loadings. Stock returns are the archive's month-end split-adjusted prices (no
dividends) minus IIMA's risk-free rate."""

import numpy as np
import pandas as pd

from ff import data, stats

MODELS = {"CAPM": ["MKT"], "3-factor": ["MKT", "SMB", "HML"],
          "4-factor": ["MKT", "SMB", "HML", "WML"]}


def stock_excess(m_px: pd.DataFrame, f: pd.DataFrame) -> pd.DataFrame:
    """Monthly excess returns (stock minus risk-free), months the factors cover."""
    r = m_px.pct_change(fill_method=None)
    r = r.loc[r.index.intersection(f.index)]
    return r.sub(f.loc[r.index, "RF"], axis=0)


def fit(y: pd.Series, f: pd.DataFrame, cols: list[str]) -> dict:
    o = stats.ols(y.to_numpy(), f.loc[y.index, cols].to_numpy())
    n, k = o["n"], len(cols)
    return {"alpha": 12 * o["b"][0], **dict(zip(cols, o["b"][1:], strict=True)),
            **{f"t_{c}": t for c, t in zip(cols, o["t"][1:], strict=True)},
            "t_alpha": o["t"][0], "r2": o["r2"],
            "adj_r2": 1 - (1 - o["r2"]) * (n - 1) / (n - k - 1), "n": n}


def in_sample(ex: pd.DataFrame, f: pd.DataFrame, min_months: int = 60) -> pd.DataFrame:
    rows = []
    for s in ex:
        y = ex[s].dropna()
        if len(y) < min_months:
            continue
        for m, cols in MODELS.items():
            rows.append({"symbol": s, "model": m, **fit(y, f, cols)})
    return pd.DataFrame(rows)


def out_of_sample(ex: pd.DataFrame, f: pd.DataFrame, split: str = "2019-12-31",
                  min_months: int = 48) -> pd.DataFrame:
    """Loadings fitted on months up to `split`, then each later month's return predicted from
    those loadings and that month's factor returns (no alpha). Out-of-sample R² = 1 - squared
    prediction errors / squared deviations from the later months' own mean."""
    rows = []
    for s in ex:
        a, b = ex[s].loc[:split].dropna(), ex[s].loc[split:].iloc[1:].dropna()
        if len(a) < min_months or len(b) < min_months:
            continue
        for m, cols in MODELS.items():
            first, second = fit(a, f, cols), fit(b, f, cols)
            pred = f.loc[b.index, cols].to_numpy() @ np.array([first[c] for c in cols])
            oos = 1 - np.sum((b - pred) ** 2) / np.sum((b - b.mean()) ** 2)
            rows.append({"symbol": s, "model": m, "oos_r2": oos, "r2_second": second["r2"],
                         **{f"{c}_1": first[c] for c in cols},
                         **{f"{c}_2": second[c] for c in cols}})
    return pd.DataFrame(rows)


def factors() -> pd.DataFrame:
    return data.factors()
