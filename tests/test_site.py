import numpy as np
import pandas as pd

from ff import site


def test_page_builds_with_data_and_format_parts():
    idx = pd.date_range("2020-01-31", periods=30, freq="ME")
    rng = np.random.default_rng(1)
    f = pd.DataFrame(rng.normal(0, 0.03, (30, 5)), index=idx,
                     columns=["MKT", "SMB", "HML", "WML", "RF"])
    html = site.build_html(f, "2025-12")
    assert "$" + "data" not in html and "$" + "js" not in html
    assert "Updated " in html and "Data: IIM Ahmedabad" in html and "Research only" in html
    assert '"months":["2020-01"' in html and "How to read it:" in html
