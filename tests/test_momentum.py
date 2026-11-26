import numpy as np
import pandas as pd

from ff import momentum


def _toy(n_stocks=60, months=16):
    idx = pd.date_range("2020-01-31", periods=months, freq="ME")
    rng = np.random.default_rng(2)
    drift = np.linspace(-0.03, 0.03, n_stocks)  # steady winners and losers
    r = drift + rng.normal(0, 0.001, (months, n_stocks))
    px = pd.DataFrame(100 * np.cumprod(1 + r, axis=0), index=idx,
                      columns=[f"S{i}" for i in range(n_stocks)])
    size = rng.permutation(np.arange(1, n_stocks + 1, dtype=float))  # unrelated to momentum
    tv = pd.DataFrame(np.tile(size, (months, 1)), index=idx,
                      columns=px.columns)
    return px, tv


def test_persistent_winners_give_positive_wml_held_next_month():
    px, tv = _toy()
    w = momentum.wml(px, tv, sized=False)
    assert w.index[0] == pd.Timestamp("2021-02-28")  # formed Jan 2021 (needs 12 months), held Feb
    assert (w["WML"] > 0.03).all()  # top 30% drift about +2.1%, bottom 30% about -2.1% a month


def test_sized_wml_is_the_average_of_the_two_size_legs():
    px, tv = _toy()
    w = momentum.wml(px, tv, sized=True, big_share=0.5)
    legs = ((w["WB"] - w["LB"]) + (w["WS"] - w["LS"])) / 2
    assert np.allclose(w["WML"], legs)


def test_universe_mask_limits_the_eligible_stocks():
    px, tv = _toy()
    uni = pd.DataFrame(False, index=px.index, columns=px.columns)
    uni.iloc[:, :55] = True
    w_all = momentum.wml(px, tv, sized=False)
    w_uni = momentum.wml(px, tv, sized=False, uni=uni)
    assert (w_uni["n"] == 55).all() and (w_all["n"] == 60).all()
