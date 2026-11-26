"""Factor crashes and volatility scaling.

Scaling (Barroso and Santa-Clara, 2015): at each month-end, a factor's position for the next
month is target / realised volatility, the realised volatility from the factor's daily returns
over the past `look` trading days (annualised with the window's own trading days a year), capped
at `cap`. The look-back and the target are chosen on the training years only.
"""

import numpy as np
import pandas as pd

from ff import stats


def realised_vol(daily: pd.Series, look: int) -> pd.Series:
    """Annualised volatility of the past `look` daily returns, at each month-end."""
    per_year = len(daily) / ((daily.index[-1] - daily.index[0]).days / 365.25)
    v = daily.rolling(look, min_periods=int(0.8 * look)).std() * np.sqrt(per_year)
    return v.resample("ME").last()


def scaled(monthly: pd.Series, daily: pd.Series, look: int, target: float,
           cap: float = 2.0) -> pd.DataFrame:
    """Next-month weight target / vol (set at the end of the month before) and the scaled return."""
    w = (target / realised_vol(daily, look)).clip(upper=cap).shift(1)
    out = pd.DataFrame({"w": w, "r": monthly}).dropna()
    out["scaled"] = out["w"] * out["r"]
    return out


def choose(monthly: pd.Series, daily: pd.Series, train_end: str,
           looks=(21, 63, 126, 252)) -> tuple[int, float, dict]:
    """Look-back with the best training Sharpe ratio; target = the factor's own training
    volatility (so scaling doesn't change the average position size much)."""
    tr = monthly.loc[:train_end]
    target = float(tr.std() * np.sqrt(12))
    sharpe = {}
    for lk in looks:
        s = scaled(monthly, daily, lk, target)["scaled"].loc[:train_end]
        sharpe[lk] = float(s.mean() / s.std() * np.sqrt(12))
    return max(sharpe, key=sharpe.get), target, sharpe


def skew(x: pd.Series) -> float:
    x = x.dropna()
    return float(((x - x.mean()) ** 3).mean() / x.std(ddof=0) ** 3)


def describe(r: pd.Series) -> dict:
    s = stats.summary(r)
    return s | {"skew": skew(r)}
