import numpy as np

from ff import stats


def test_grs_rejects_at_about_five_percent_under_the_null_and_detects_alpha():
    rng = np.random.default_rng(7)
    p = []
    for _ in range(300):
        F = rng.normal(0.005, 0.04, (240, 3))
        R = F @ rng.normal(1, 0.3, (3, 6)) + rng.normal(0, 0.02, (240, 6))
        p.append(stats.grs(R, F)["p"])
    assert 0.02 < np.mean(np.array(p) < 0.05) < 0.09
    F = rng.normal(0.005, 0.04, (240, 3))
    R = 0.005 + F @ rng.normal(1, 0.3, (3, 6)) + rng.normal(0, 0.02, (240, 6))
    g = stats.grs(R, F)
    assert g["p"] < 0.01 and np.allclose(g["alpha"], 0.005, atol=0.003)
