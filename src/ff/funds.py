"""Indian diversified equity mutual funds (direct plans, growth option) from mfapi.in (AMFI net
asset values), cached in data/funds/ (not committed), including schemes that have since closed or
merged, as far as mfapi.in lists them."""

import json
import re
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from ff import data, stats

API = "https://api.mfapi.in/mf"
_KEEP = re.compile(r"flexi|large|mid|small|multi ?cap|value|contra|focus|elss|tax|bluechip|"
                   r"equity|opportunit|dividend yield", re.I)
_DROP = re.compile(r"idcw|dividend payout|reinvest|index|etf|fund of fund|fof|hybrid|debt|"
                   r"arbitrage|balanced|savings|liquid|overnight|gilt|bond|income|duration|credit|"
                   r"money market|nifty|sensex|retirement|children|solution|overseas|global|"
                   r"international|nasdaq|gold|silver|fixed|fmp|interval|series|days\)|"
                   r"capital protection|asset allocation|multi asset|off-?shore|china|asean|"
                   r"thematic|psu|entertainment|cash|close ended|maturity|\d+D |saving", re.I)
# AMFI's category labels are inconsistent (several spellings; some old equity schemes are filed
# as "Income" or "Growth"), so they are used only to drop sector, thematic and overseas funds, and
# the fund's style comes from its name, first match wins.
DROP_CATEGORY = re.compile(r"sectoral|thematic|overseas|fund of funds|fof|index|etf|hybrid|debt",
                           re.I)
STYLES = [("Small Cap", r"small[- ]?cap|emerging"), ("Large & Mid Cap", r"large (&|and) mid"),
          ("Mid Cap", r"mid[- ]?cap"), ("Large Cap", r"large[- ]?cap|bluechip|top 100"),
          ("ELSS", r"elss|tax"), ("Flexi Cap", r"flexi"), ("Multi Cap", r"multi[- ]?cap"),
          ("Focused", r"focus"), ("Value", r"value|contra|dividend yield"),
          ("Other diversified", r".")]


def style(name: str) -> str:
    return next(lab for lab, pat in STYLES if re.search(pat, name, re.I))


# Index funds (direct, growth) as the zero-skill baseline: they hold their index, so any alpha
# they show is the factor model's error for that kind of portfolio, plus fees.
INDEX_FUNDS = {120716: "UTI Nifty 50", 118347: "IDBI Nifty 50", 118348: "IDBI Nifty Next 50",
               143341: "UTI Nifty Next 50", 147622: "Motilal Oswal Nifty Midcap 150",
               147623: "Motilal Oswal Nifty Smallcap 250"}


def fund_dir() -> Path:
    return data.data_dir().parent / "funds"


def _get(url: str) -> bytes:
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except OSError:
            if i == 3:
                raise
            time.sleep(3 * (i + 1))
    raise RuntimeError("unreachable")


def candidates(schemes: list[dict]) -> list[dict]:
    """Direct-plan growth schemes whose names look like diversified equity funds."""
    return [s for s in schemes if re.search(r"direct", s["schemeName"], re.I)
            and re.search(r"growth", s["schemeName"], re.I)
            and _KEEP.search(s["schemeName"]) and not _DROP.search(s["schemeName"])]


def fetch() -> int:
    """Download every candidate's NAV history once (cached); returns how many are cached."""
    out = fund_dir()
    out.mkdir(parents=True, exist_ok=True)
    codes = [s["schemeCode"] for s in candidates(json.loads(_get(API)))] + list(INDEX_FUNDS)
    for code in codes:
        p = out / f"{code}.json"
        if not p.exists():
            p.write_bytes(_get(f"{API}/{code}"))
            time.sleep(0.1)
    return len(list(out.glob("*.json")))


def monthly(rows: list[dict]) -> pd.Series:
    """Month-end returns from NAV rows (last NAV each month; a month counts only if the month
    before has a NAV too), as ff.js does."""
    nav = pd.Series({pd.to_datetime(r["date"], format="%d-%m-%Y"): float(r["nav"])
                     for r in rows if float(r["nav"]) > 0}).sort_index()
    m = nav.resample("ME").last()
    r = m / m.shift(1) - 1
    return r.dropna()


def load(min_months: int = 36) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Monthly returns (fund columns) and a table of scheme code, name, style and last NAV date,
    for cached diversified equity funds with at least `min_months` returns."""
    rets, info = {}, []
    for p in sorted(fund_dir().glob("*.json")):
        j = json.loads(p.read_text())
        meta = j.get("meta") or {}
        name = meta.get("scheme_name") or ""
        if (DROP_CATEGORY.search(meta.get("scheme_category") or "") or _DROP.search(name)
                or not j.get("data")):
            continue
        r = monthly(j["data"])
        if len(r) < min_months:
            continue
        code = int(p.stem)
        rets[code] = r
        info.append({"code": code, "name": name, "category": style(name),
                     "last": pd.to_datetime(j["data"][0]["date"], format="%d-%m-%Y")})
    return pd.DataFrame(rets).sort_index(), pd.DataFrame(info).set_index("code")


def index_returns() -> pd.DataFrame:
    """Monthly returns of the baseline index funds, columns named as in INDEX_FUNDS."""
    out = {}
    for code, name in INDEX_FUNDS.items():
        p = fund_dir() / f"{code}.json"
        if p.exists():
            out[name] = monthly(json.loads(p.read_text())["data"])
    return pd.DataFrame(out).sort_index()


def alpha_table(r: pd.DataFrame, f: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = {}
    for c in r:
        y = r[c].dropna()
        y = y.loc[y.index.intersection(f.index)]
        if len(y) < 36:
            continue
        o = stats.ols((y - f.loc[y.index, "RF"]).to_numpy(), f.loc[y.index, cols].to_numpy())
        rows[c] = {"alpha": 12 * o["b"][0], "t": o["t"][0], "r2": o["r2"], "n": o["n"],
                   **dict(zip(cols, o["b"][1:], strict=True))}
    return pd.DataFrame(rows).T


def persistence(r: pd.DataFrame, f: pd.DataFrame, cols: list[str], look: int = 36,
                hold: int = 12, start: str = "2015-12-31") -> pd.DataFrame:
    """Each December from `start`: rank funds with a full `look` months by their alpha over those
    months; hold the top and bottom thirds, equally weighted, for the next `hold` months (a fund
    that stops reporting drops out of the average). Returns the monthly returns of the top and
    bottom thirds and all ranked funds."""
    r = r.loc[r.index.intersection(f.index)]
    out = []
    for t in [d for d in r.index if d.month == 12 and d >= pd.Timestamp(start)]:
        past = r.loc[:t].iloc[-look:]
        if len(past) < look:
            continue
        ok = past.columns[past.notna().all()]
        if len(ok) < 30:
            continue
        a = {}
        for c in ok:
            o = stats.ols((past[c] - f.loc[past.index, "RF"]).to_numpy(),
                          f.loc[past.index, cols].to_numpy())
            a[c] = o["b"][0]
        a = pd.Series(a)
        top, bot = a[a >= a.quantile(2 / 3)].index, a[a <= a.quantile(1 / 3)].index
        nxt = r.loc[t:].iloc[1:hold + 1]
        for d, row in nxt.iterrows():
            out.append({"date": d, "formed": t, "top": row[top].mean(), "bottom": row[bot].mean(),
                        "all": row[ok].mean(), "n": len(ok)})
    return pd.DataFrame(out).set_index("date")


def nan_safe(x) -> float:
    return float(x) if np.isfinite(x) else float("nan")
