import numpy as np
import pandas as pd

from ff import exposures as ex


def test_out_of_sample_r2_is_near_in_sample_when_loadings_are_constant():
    idx = pd.date_range("2014-01-31", periods=144, freq="ME")
    rng = np.random.default_rng(4)
    f = pd.DataFrame(rng.normal(0, 0.05, (144, 4)), index=idx, columns=["MKT", "SMB", "HML", "WML"])
    f["RF"] = 0.005
    y = f[["MKT", "SMB", "HML", "WML"]].to_numpy() @ [1.0, 0.5, 0.3, 0.0] + rng.normal(0, 0.03, 144)
    e = pd.DataFrame({"A": y}, index=idx)
    oo = ex.out_of_sample(e, f).set_index("model")
    assert oo.loc["3-factor", "oos_r2"] > oo.loc["CAPM", "oos_r2"] + 0.05
    for half in ("SMB_1", "SMB_2"):
        assert abs(oo.loc["3-factor", half] - 0.5) < 0.15
    ins = ex.in_sample(e, f).set_index("model")
    assert ins.loc["4-factor", "r2"] >= ins.loc["3-factor", "r2"] >= ins.loc["CAPM", "r2"]
