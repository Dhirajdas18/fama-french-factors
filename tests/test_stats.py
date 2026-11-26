import numpy as np
import pandas as pd

from ff import data, stats


def test_ols_recovers_coefficients_and_nw_reduces_to_white_at_zero_lags():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(400, 2))
    y = 0.01 + X @ [0.8, -0.3] + rng.normal(0, 0.1, 400)
    o = stats.ols(y, X, lags=0)
    assert np.allclose(o["b"], [0.01, 0.8, -0.3], atol=0.02)
    Xc = np.column_stack([np.ones(400), X])
    e = y - Xc @ o["b"]
    inv = np.linalg.inv(Xc.T @ Xc)
    white = np.sqrt(np.diag(inv @ (Xc.T * e**2) @ Xc @ inv) * 400 / 397)
    assert np.allclose(o["b"] / o["t"], white)


def test_summary_growth_drawdown_and_t():
    idx = pd.date_range("2020-01-31", periods=12, freq="ME")
    r = pd.Series([0.1, -0.5, 0.2, 0.1] + [0.0] * 8, index=idx)
    s = stats.summary(r)
    w = np.prod(1 + r.to_numpy())
    assert np.isclose(s["cagr"], w - 1)  # exactly one year
    assert np.isclose(s["dd"], -0.5)  # 1.1 -> 0.55
    assert np.isclose(s["mean"], r.mean() * 12) and s["n"] == 12


def test_latest_release_and_factor_parsing(tmp_path, monkeypatch):
    tail = "_FourFactors_and_Market_Returns_Monthly_SurvivorshipBiasAdjusted.csv"
    html = f'<a href="DATA/2025-03{tail}"> <a href="DATA/2025-12{tail}">'
    assert data.latest_release(html) == "2025-12"
    d = tmp_path / "iima"
    d.mkdir()
    (d / "factors_monthly.csv").write_text(
        "Date,SMB,HML,WML,MF,RF\n1993-10,1,2,3,NA,NA\n1993-11,-1,0.5,2,4,0.5\n")
    monkeypatch.setenv("FF_DATA_DIR", str(tmp_path))
    f = data.factors()
    assert list(f.index) == [pd.Timestamp("1993-11-30")]
    assert np.isclose(f["MKT"].iloc[0], 0.04) and np.isclose(f["MARKET"].iloc[0], 0.045)
    assert np.isclose(f["SMB"].iloc[0], -0.01)
