import numpy as np
import pandas as pd

from ff import verdict


def test_tangency_weights_sum_to_one_and_favour_the_better_asset():
    rng = np.random.default_rng(1)
    d = pd.DataFrame({"a": rng.normal(0.01, 0.05, 600), "b": rng.normal(0.002, 0.05, 600)})
    w = verdict.tangency(d)
    assert np.isclose(w.sum(), 1) and w["a"] > w["b"]


def test_long_only_winners_pay_costs_on_trades_only():
    idx = pd.date_range("2020-01-31", periods=16, freq="ME")
    drift = np.linspace(-0.02, 0.02, 60)  # fixed ranking: the same winners every month
    px = pd.DataFrame(100 * np.cumprod(1 + np.tile(drift, (16, 1)), axis=0), index=idx)
    w = verdict.winners_long_only(px)
    first = w.iloc[0]
    assert np.isclose(first["cost"], verdict.BUY)  # buys the whole book once, sells nothing
    assert (w["turnover"].iloc[1:] < 0.02).all()  # later months only rebalance the drift
    assert (w["gross"] > w["bench"]).all()
    assert np.allclose(w["net"], (1 - w["cost"]) * (1 + w["gross"]) - 1)


def test_each_stock_sold_pays_the_dp_charge():
    idx = pd.date_range("2020-01-31", periods=16, freq="ME")
    rng = np.random.default_rng(5)
    px = pd.DataFrame(100 * np.cumprod(1 + rng.normal(0, 0.08, (16, 60)), axis=0), index=idx)
    w = verdict.winners_long_only(px)
    floor = verdict.DP_PER_SELL / verdict.CAPITAL
    later = w.iloc[1:]
    # a month that replaces names pays at least one DP charge on top of the percentage costs
    assert (later.loc[later["turnover"] > 0.05, "cost"] > floor).all()
