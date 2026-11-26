# Fama-French Factors

[![CI](https://github.com/Dhirajdas18/fama-french-factors/actions/workflows/ci.yml/badge.svg)](https://github.com/Dhirajdas18/fama-french-factors/actions/workflows/ci.yml)
[![Factor lab](https://github.com/Dhirajdas18/fama-french-factors/actions/workflows/pages.yml/badge.svg)](https://dhirajdas18.github.io/fama-french-factors/)

The market, size, value and momentum factors in Indian equities from 1993 to 2025, using IIM
Ahmedabad's survivorship-bias adjusted factor library: what each earned, how well they explain
stocks, portfolios and mutual funds, and how they crash. Fund prices are AMFI net asset values;
stock prices come from a local NSE archive, and only derived results are committed.

**Live factor lab: [dhirajdas18.github.io/fama-french-factors](https://dhirajdas18.github.io/fama-french-factors/)**,
pick any years to see what each factor earned, and split any Indian mutual fund's return into its
market, size, value and momentum exposures and what is left over, computed in your browser.

## Features

- [x] What market, size, value and momentum earned in India, 1993–2025, by half, with their worst falls
- [ ] Momentum rebuilt from the NSE archive and checked against the library's factor
- [ ] CAPM against three and four factors on single stocks: how much each explains, and stable loadings
- [ ] Do the factors price the size-value portfolios? The GRS test for CAPM, three and four factors
- [ ] Mutual funds: is their alpha just size, value and momentum? Out of sample
- [ ] Factor crashes: momentum and value drawdowns, and a risk-scaling rule chosen on early years
- [ ] Verdict: which factors to use for risk and attribution, and whether to tilt towards any

## Findings

### 1. Momentum and value paid most in India; small companies didn't beat big ones

<a href="docs/img/factors.png"><picture><source media="(prefers-reduced-motion: reduce)" srcset="docs/img/factors.png"><img src="docs/img/factors.gif" alt="Growth of one rupee in the Indian market, size, value and momentum factors from 1993 to 2025, and each factor's average return a year in 1993-2009 and 2010-2025" width="720"></picture></a>

IIM Ahmedabad's monthly factors (release 2025-12, November 1993 to December 2025, 385 months;
November 1994 has no long-short returns and is left out), survivorship-bias adjusted. Market is
the market's return minus the risk-free rate (the library's MF column, which matches its own
published market premium of 4.93% a year since 1994); size (small minus big), value (cheap minus
expensive on book-to-market) and momentum (winners minus losers on past returns) are long-short
portfolios of listed companies, micro-caps and penny stocks excluded. Each factor's average a year
is 12 times its monthly mean, with a Newey-West t (3 lags); compounded growth uses calendar years;
the halves are 1993–2009 and 2010–2025. Nothing is fitted. The market's own return is checked
against NIFTY from the local archive where both exist.

- **Momentum paid most.** Winners beat losers by 13.3% a year on average (t 2.84), 10.9% a year
  compounded; 14.8% (t 3.70) in 2010–2025. Over five-year windows it compounded between −2.3% and
  +29.7% a year and was below zero in 1% of them.
- **Value paid in both halves.** Cheap beat expensive by 8.5% a year (t 2.34): 10.1% in 1993–2009
  and 6.9% in 2010–2025 (t 1.7 each). Its worst fall was −59%, from October 1994 to February 2000.
- **Size didn't pay.** Small minus big averaged −2.9% a year (t −0.88): −6.8% in 1993–2009 and
  +1.0% since, and it fell 86% from January 1995 to March 2009.
- **The market beat cash, with deep falls.** The market premium averaged 8.6% a year (t 1.78) and
  compounded 5.7%; the market itself compounded 13.0% a year against 6.9% for cash. It fell 75%
  from August 1994 to September 2001. From March 2013 it compounded 15.9% a year against 12.6% for
  NIFTY's price index, which leaves out dividends (monthly correlation 0.92).
- **Momentum and value offset each other.** Their monthly correlation was −0.37; market and size
  +0.25, market and value +0.22.

## Quick start

```bash
uv sync
uv run python scripts/fetch_data.py   # IIMA factor library -> data/iima/
uv run ff report factors              # topics: factors
uv run python scripts/build_site.py   # factor lab -> site/index.html
uv run pytest
```

The factor files are downloaded, not committed. The NIFTY comparison and later stock studies read a
local NSE bhavcopy archive (`FF_LAKE_DIR`, default `/path/to/lake`) and are skipped without
it.

## Design

- `src/ff/data.py`: finds the library's latest release, downloads its survivorship-bias adjusted
  factor and portfolio files with retries, and loads them as decimal returns by month-end.
- `src/ff/stats.py`: least squares with Newey-West t statistics, and the return summary (average,
  volatility, compounded growth, t, worst month, worst 12 months, worst fall).
- `src/ff/ff.js`: the lab's browser copy of the regression and summary, and monthly returns from
  mfapi.in net asset values, tested against Python through Node to 1e-8.
- `src/ff/site.py`: the factor lab, one static Plotly page that carries the monthly factors; fund
  prices are fetched live from mfapi.in.
- `src/ff/lake.py`: NIFTY's monthly return from the local NSE archive.
- `src/ff/reports.py`: README findings, reproducible with `ff report <topic>`.
- Conventions: returns are monthly and simple, in decimals; averages are 12 × the monthly mean,
  volatility √12 × the monthly standard deviation, compounded growth over months ÷ 12 years; t
  statistics are Newey-West with 3 lags.
- Data: IIM Ahmedabad's Indian Fama-French-momentum data library (Agarwalla, Jacob and Varma,
  2013, Four factor model in Indian equities market, IIMA Working Paper 2013-09-05), the
  survivorship-bias adjusted series; AMFI net asset values through mfapi.in; NIFTY from a local NSE archive.
- Charts: one validated palette; README charts are animated GIFs with a static fallback for
  reduced-motion users.

Research only, not investment advice. MIT licence.
