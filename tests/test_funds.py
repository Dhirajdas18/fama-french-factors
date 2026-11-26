import numpy as np
import pandas as pd

from ff import funds


def test_monthly_returns_use_last_nav_and_need_the_previous_month():
    rows = [{"date": "29-02-2024", "nav": "110"}, {"date": "15-02-2024", "nav": "105"},
            {"date": "31-01-2024", "nav": "100"}, {"date": "30-11-2023", "nav": "90"}]
    r = funds.monthly(rows)
    assert list(r.index) == [pd.Timestamp("2024-02-29")] and np.isclose(r.iloc[0], 0.1)


def test_style_from_name_and_ranking_uses_only_the_past():
    assert funds.style("Baroda Mid-cap Fund- Plan B (Direct)") == "Mid Cap"
    assert funds.style("Kotak Large & Midcap Fund") == "Large & Mid Cap"
    idx = pd.date_range("2013-01-31", periods=72, freq="ME")
    rng = np.random.default_rng(3)
    f = pd.DataFrame(rng.normal(0, 0.04, (72, 4)), index=idx, columns=["MKT", "SMB", "HML", "WML"])
    f["RF"] = 0.005
    skill = np.r_[np.full(15, 0.004), np.zeros(15), np.full(15, -0.004)]  # constant alphas
    r = pd.DataFrame(f[["MKT"]].to_numpy() + 0.005 + skill + rng.normal(0, 0.005, (72, 45)),
                     index=idx)
    p = funds.persistence(r, f, ["MKT", "SMB", "HML", "WML"], start="2015-12-31")
    assert p["formed"].min() == pd.Timestamp("2015-12-31")
    assert p.index.min() == pd.Timestamp("2016-01-31")
    assert (p["top"] - p["bottom"]).mean() > 0.006  # skilled funds ranked top keep their edge
