"""Putting the factors to use: a value-momentum mix, long-only versions, and what delivery costs
leave of a long-only momentum tilt built from the archive."""

import numpy as np
import pandas as pd

# NSE delivery costs per rupee traded, as checked in momentum-after-costs (Zerodha, Nov 2026):
# STT 0.1% each side, stamp duty 0.015% on buys, NSE 0.00322% and SEBI 0.0001% each side with 18%
# GST, plus 5 bp of slippage each side, and the ₹16 DP charge per stock sold on a ₹10 lakh book.
BUY = 0.001 + 0.00015 + (0.0000322 + 0.000001) * 1.18 + 0.0005
SELL = 0.001 + (0.0000322 + 0.000001) * 1.18 + 0.0005
DP_PER_SELL = 16.0
CAPITAL = 1_000_000.0


def tangency(train: pd.DataFrame) -> pd.Series:
    """Maximum-Sharpe weights (inverse covariance times means), scaled to sum to one."""
    w = np.linalg.solve(train.cov().to_numpy(), train.mean().to_numpy())
    return pd.Series(w / w.sum(), index=train.columns)


def winners_long_only(m_px: pd.DataFrame, uni: pd.DataFrame | None = None,
                      top: float = 0.30) -> pd.DataFrame:
    """Each month-end, buy the top `top` of eligible stocks by 12-1 momentum, equally weighted,
    and hold for the month; trades are the weight changes from the drifted holdings. Returns
    gross and net monthly returns, the cost, one-way turnover, and the equal-weighted return of
    every eligible stock (the benchmark, without costs). Eligible: priced, with 12-1 momentum, and
    in `uni` at the month-end when given. A stock without a next price returns 0."""
    nxt = m_px.shift(-1) / m_px - 1
    mom = m_px.shift(1) / m_px.shift(12) - 1
    held = pd.Series(dtype=float)
    rows = {}
    for t in m_px.index[12:-1]:
        ok = mom.loc[t].notna() & m_px.loc[t].notna()
        if uni is not None:
            ok &= uni.reindex(index=[t], columns=m_px.columns, fill_value=False).iloc[0]
        if ok.sum() < 50:
            continue
        mo = mom.loc[t][ok]
        win = mo[mo >= mo.quantile(1 - top)].index
        target = pd.Series(1 / len(win), index=win)
        allw = target.reindex(target.index.union(held.index), fill_value=0.0)
        cur = held.reindex(allw.index, fill_value=0.0)
        buys = (allw - cur).clip(lower=0).sum()
        sells = (cur - allw).clip(lower=0).sum()
        n_sold = int(((cur - allw) > 1e-12).sum())
        cost = buys * BUY + sells * SELL + n_sold * DP_PER_SELL / CAPITAL
        r = nxt.loc[t].reindex(win).fillna(0.0)
        gross = float((target * r).sum())
        grown = target * (1 + r)
        held = grown / grown.sum()
        bench = float(nxt.loc[t][ok].fillna(0.0).mean())
        rows[t + pd.offsets.MonthEnd(1)] = {"gross": gross, "cost": cost,
                                            "net": (1 - cost) * (1 + gross) - 1,
                                            "turnover": (buys + sells) / 2, "bench": bench}
    return pd.DataFrame(rows).T.astype(float)
