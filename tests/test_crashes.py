import numpy as np
import pandas as pd

from ff import crashes


def test_weight_uses_only_the_previous_month_end_volatility():
    days = pd.bdate_range("2020-01-01", "2021-12-31")
    rng = np.random.default_rng(0)
    vol = np.where(days < pd.Timestamp("2021-01-01"), 0.01, 0.02)  # daily vol doubles in 2021
    d = pd.Series(rng.normal(0, 1, len(days)) * vol, index=days)
    m = (1 + d).resample("ME").prod() - 1
    s = crashes.scaled(m, d, look=21, target=0.2, cap=10)
    rv = crashes.realised_vol(d, 21)
    t = pd.Timestamp("2021-03-31")
    assert np.isclose(s.at[t, "w"], 0.2 / rv.at[pd.Timestamp("2021-02-28")])
    assert s.loc["2021-03":, "w"].mean() < 0.6 * s.loc["2020-03":"2020-12", "w"].mean()
    assert np.allclose(s["scaled"], s["w"] * s["r"])


def test_skew_is_negative_for_a_left_tail():
    x = pd.Series([0.0] * 50 + [-1.0])
    assert crashes.skew(x) < 0
