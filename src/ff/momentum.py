"""Momentum rebuilt from the NSE archive, the IIMA way where the archive allows.

IIMA (working paper 2013-09-05, section 3.2): at the end of month t, momentum is the return from
the end of t-12 to the end of t-1; winners are the top 30%, losers the bottom 30%; big companies
are the top 10% by market value; WML = ((big winners - big losers) + (small winners - small
losers)) / 2, value-weighted, held over month t+1. The archive has no shares outstanding, so here
size is the median daily turnover over the past 12 months and portfolios are equal-weighted
(or turnover-weighted as a stand-in for value weights).
"""

import numpy as np
import pandas as pd

from ff.lake import lake_dir


def monthly_panel() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Month-end split-adjusted prices (last trade in the month, so a stock that stops trading
    keeps its last price for the month it stops) and the past 12 months' median daily turnover,
    symbol columns."""
    p = pd.read_parquet(lake_dir() / "panel.parquet",
                        columns=["date", "symbol", "adj_close", "turnover"])
    px = p.pivot_table(index="date", columns="symbol", values="adj_close")
    tv = p.pivot_table(index="date", columns="symbol", values="turnover")
    m_px = px.resample("ME").last()
    alive = px.notna().resample("ME").max()  # traded at least once in the month
    m_px = m_px.where(alive)
    m_tv = tv.rolling(250, min_periods=120).median().resample("ME").last()
    if (m_px.index[-1] - px.index[-1]).days > 3:  # the archive stops partway through its last month
        m_px, m_tv = m_px.iloc[:-1], m_tv.iloc[:-1]
    return m_px, m_tv


def wml(m_px: pd.DataFrame, m_tv: pd.DataFrame, skip: int = 1, weight: str = "equal",
        sized: bool = True, big_share: float = 0.10, tail: float = 0.30,
        min_names: int = 5, uni: pd.DataFrame | None = None) -> pd.DataFrame:
    """Monthly winners-minus-losers returns, formed at each month-end t and held over t+1.
    skip=1 measures momentum from t-12 to t-1 (IIMA, Carhart); skip=0 from t-12 to t. Returns a
    frame with WML, the four corner portfolios (when sized) and the number of stocks. With `uni`
    (month-end booleans, e.g. monthly_universe), only stocks in it at t are eligible."""
    nxt = m_px.shift(-1) / m_px - 1  # return over month t+1
    mom = m_px.shift(skip) / m_px.shift(12) - 1
    rows = {}
    for t in m_px.index[12:-1]:
        ok = mom.loc[t].notna() & m_px.loc[t].notna() & m_tv.loc[t].notna()
        if uni is not None:
            ok &= uni.reindex(index=[t], columns=m_px.columns, fill_value=False).iloc[0]
        r = nxt.loc[t][ok]
        if not np.isfinite(r).all():  # a stock with no price next month: last price, return 0
            r = r.fillna(0.0)
        mo, tv = mom.loc[t][ok], m_tv.loc[t][ok]
        if len(mo) < 50:
            continue
        win = mo >= mo.quantile(1 - tail)
        lose = mo <= mo.quantile(tail)
        big = tv >= tv.quantile(1 - big_share) if sized else pd.Series(True, index=tv.index)

        def port(mask, r=r, tv=tv):
            if mask.sum() < min_names:
                return np.nan
            w = tv[mask] if weight == "turnover" else pd.Series(1.0, index=r[mask].index)
            return float((r[mask] * w).sum() / w.sum())

        if sized:
            c = {"WB": port(win & big), "WS": port(win & ~big), "LB": port(lose & big),
                 "LS": port(lose & ~big)}
            legs = [c["WB"] - c["LB"], c["WS"] - c["LS"]]
            val = float(np.nanmean(legs)) if np.isfinite(legs).any() else np.nan
        else:
            c = {}
            val = port(win) - port(lose)
        rows[t + pd.offsets.MonthEnd(1)] = {"WML": val, **c, "n": int(ok.sum())}
    return pd.DataFrame(rows).T.astype(float)


def monthly_universe() -> pd.DataFrame:
    """The reference model's point-in-time universe at each month-end (in_uni on the month's last trading
    day: the top 200 by median turnover, priced at ₹50 or more, with a year of history)."""
    p = pd.read_parquet(lake_dir() / "panel.parquet", columns=["date", "symbol", "in_uni"])
    u = p.pivot_table(index="date", columns="symbol", values="in_uni", aggfunc="last")
    return u.resample("ME").last().fillna(False).astype(bool)
