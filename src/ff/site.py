"""The factor lab: one static Plotly page with the monthly factors built in (ff.js does the maths
in the browser and fetches fund prices from mfapi.in)."""

import datetime
import json
import re
from pathlib import Path
from string import Template

import pandas as pd

from ff import data, plots

FONT = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
ICON = (
    "data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 16 16%22%3E"
    "%3Cpath d=%22M2 14V9M6 14V5M10 14V7M14 14V2%22 fill=%22none%22"
    " stroke=%22%232a78d6%22 stroke-width=%222%22 stroke-linecap=%22round%22/%3E"
    "%3C/svg%3E"
)
HERE = Path(__file__).parent
JS = (HERE / "ff.js").read_text(encoding="utf-8")
LAB = (HERE / "lab.html").read_text(encoding="utf-8")
PAGE = Template((HERE / "page.html").read_text(encoding="utf-8"))
REPO = "https://github.com/Dhirajdas18/fama-french-factors"
# Preset funds (AMFI scheme codes, direct plans, growth): an index fund first as a check.
FUNDS = [
    (120716, "UTI Nifty 50 Index Fund"),
    (119598, "SBI Large Cap Fund"),
    (118955, "HDFC Flexi Cap Fund"),
    (122639, "Parag Parikh Flexi Cap Fund"),
    (120323, "ICICI Prudential Value Fund"),
    (118778, "Nippon India Small Cap Fund"),
]


def lab_data(f: pd.DataFrame, release: str) -> dict:
    """Monthly factors as decimals rounded to 1e-6, months as 'YYYY-MM'."""
    out = {"months": list(f.index.strftime("%Y-%m")), "release": release,
           "first": f"{f.index[0]:%b %Y}", "last": f"{f.index[-1]:%b %Y}"}
    for c in data.FACTORS + ["RF"]:
        out[c] = [round(float(v), 6) for v in f[c].fillna(0.0)]
    return out


def lab_section(d: dict) -> str:
    colors = {k: plots.COLORS[k] for k in data.FACTORS}
    return (LAB.replace("$js", JS).replace("$data", json.dumps(d, separators=(",", ":")))
            .replace("$colors", json.dumps(colors)).replace("$funds", json.dumps(FUNDS)))


def method_section(d: dict) -> str:
    return f"""<ul class="plain">
<li>Factors: IIM Ahmedabad’s monthly market, size (SMB), value (HML) and momentum (WML) returns,
release {d["release"]}, {d["first"]} to {d["last"]}, survivorship-bias adjusted. Market is the
market return minus the risk-free rate; the others are long-short portfolios of listed companies
sorted on size, book-to-market and past 12-month return (skipping the latest month), with
micro-cap and penny stocks excluded. November 1994, which has no long-short returns in the source,
is left out. The market is IIMA’s broad market of listed companies, not NIFTY.</li>
<li>Growth of ₹1 compounds the monthly returns; averages are 12 times the monthly mean,
volatility √12 times the monthly standard deviation, compounded growth uses the number of months
divided by 12, and t is the mean over its Newey-West standard error with 3 lags.</li>
<li>Fund regression: each month’s last net asset value gives the fund’s monthly return, after
fees, minus the risk-free rate; it is regressed on the chosen factors by least squares with
Newey-West t statistics (3 lags). Alpha is 12 times the monthly intercept. Only months the fund
and the factor data share count, so the newest months, beyond the factor release, are left out.
Everything is fitted on the same months it describes.</li>
<li>Research only, not investment advice. A fund’s past alpha says little about its future
alpha.</li>
</ul>"""


SECTIONS = [
    ("Factor lab", "Pick the years and a fund. Research only, not investment advice.",
     lab_section),
    ("Method and caveats", "Where the numbers come from, and what they leave out.",
     method_section),
]


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def build_html(f: pd.DataFrame, release: str) -> str:
    d = lab_data(f, release)
    parts, nav = [], []
    for title, blurb, make in SECTIONS:
        sid = _slug(title)
        nav.append(f'<li><a href="#{sid}">{title}</a></li>')
        parts.append(f'<section id="{sid}">\n<h2>{title}</h2>\n<p>{blurb}</p>\n{make(d)}\n'
                     "</section>")
    dk, s = plots.DARK, plots.SERIES
    return PAGE.substitute(
        updated=datetime.date.today().strftime("%d %b %Y").lstrip("0"),
        release=release, first=d["first"], last=d["last"], citation=data.CITATION,
        icon=ICON, font=FONT, repo=REPO,
        surface=plots.SURFACE, text=plots.TEXT, text2=plots.TEXT_2, grid=plots.GRID,
        accent=s[0], accent2=s[1], green=s[2], violet=s[6], muted=plots.MUTED,
        d_surface=dk[plots.SURFACE], d_text=dk[plots.TEXT], d_text2=dk[plots.TEXT_2],
        d_grid=dk[plots.GRID], d_accent=dk[s[0]], d_accent2=dk[s[1]], d_green=dk[s[2]],
        d_violet=dk[s[6]], d_muted="#6b6a64",
        nav="\n".join(nav), sections="\n".join(parts),
    )
