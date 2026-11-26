"""Optional local data from the NSE bhavcopy archive (FF_LAKE_DIR, default /path/to/lake)."""

import os
from pathlib import Path

import pandas as pd


def lake_dir() -> Path:
    return Path(os.environ.get("FF_LAKE_DIR", Path.home() / "data" / "lake"))


def nifty_monthly() -> pd.Series:
    """NIFTY's month-end close-to-close return (a price index: no dividends)."""
    n = pd.read_parquet(lake_dir() / "market.parquet").set_index("date")["nifty"].dropna()
    return n.resample("ME").last().pct_change().dropna().rename("NIFTY")
