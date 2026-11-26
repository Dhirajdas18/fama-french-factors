import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ff import stats

JS = Path(__file__).parents[1] / "src" / "ff" / "ff.js"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def _node(expr: str, payload) -> dict:
    code = f"const FF = require({json.dumps(str(JS))}); const d = {json.dumps(payload)};" \
           f"console.log(JSON.stringify({expr}));"
    return json.loads(subprocess.run(["node", "-e", code], capture_output=True, text=True,
                                     check=True).stdout)


def test_js_ols_and_summary_match_python():
    rng = np.random.default_rng(5)
    X = rng.normal(0, 0.05, (120, 4))
    y = 0.002 + X @ [1.0, 0.3, -0.2, 0.1] + rng.normal(0, 0.02, 120)
    js = _node("FF.ols(d.y, d.X, 3)", {"y": y.tolist(), "X": X.tolist()})
    py = stats.ols(y, X, 3)
    assert np.allclose(js["b"], py["b"], atol=1e-10) and np.allclose(js["t"], py["t"], atol=1e-8)
    assert np.isclose(js["r2"], py["r2"])
    r = pd.Series(y)
    js = _node("FF.summary(d)", y.tolist())
    py = stats.summary(r)
    for k in ("mean", "vol", "cagr", "t", "dd"):
        assert np.isclose(js[k], py[k], atol=1e-9), k


def test_js_monthly_returns_from_nav_rows():
    rows = [{"date": "29-02-2024", "nav": "110"}, {"date": "15-02-2024", "nav": "105"},
            {"date": "31-01-2024", "nav": "100"}, {"date": "30-11-2023", "nav": "90"}]
    assert _node("FF.monthlyReturns(d)", rows) == {"2024-02": pytest.approx(0.1)}
