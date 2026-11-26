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
- [x] Momentum rebuilt from the NSE archive and checked against the library's factor
- [x] CAPM against three and four factors on single stocks: how much each explains, and stable loadings
- [x] Do the factors price the size-value portfolios? The GRS test for CAPM, three and four factors
- [x] Mutual funds: is their alpha just size, value and momentum? Out of sample
- [x] Factor crashes: momentum and value drawdowns, and a risk-scaling rule chosen on early years
- [x] Verdict: which factors to use for risk and attribution, and whether to tilt towards any

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

### 2. Momentum rebuilt from about 460 liquid NSE stocks tracked IIMA's factor

<a href="docs/img/momentum.png"><picture><source media="(prefers-reduced-motion: reduce)" srcset="docs/img/momentum.png"><img src="docs/img/momentum.gif" alt="Growth of one rupee in IIMA's momentum factor and in momentum rebuilt from the NSE archive, 2014-2025, and the average return of five rebuilt variants" width="720"></picture></a>

IIMA's momentum rule (working paper 2013-09-05, section 3.2): at each month-end, momentum is the
return from 12 months back to one month back; winners are the top 30%, losers the bottom 30%; big
companies are the top 10% by market value; the factor is the average of big winners minus big
losers and small winners minus small losers, value-weighted, held for the next month. The NSE
archive has split-adjusted prices for every stock that was among its most-traded from 2013,
including 69 that later stopped trading, but no shares outstanding, so the rebuild uses each
stock's median daily turnover over the past year for size and weights stocks equally; a stock
that stops trading keeps its last price. It is compared with IIMA's factor over the 143 months
both cover, February 2014 to December 2025, changing one choice at a time. Nothing is fitted.

- **It tracked IIMA's factor.** The IIMA-like rebuild made 11.9% a year (t 2.01) against IIMA's
  12.9% (t 2.92), with a monthly correlation of 0.76; regressed on IIMA's, its loading was 1.00 and
  its intercept −1.0% a year. Tracking error was 12.9% a year.
- **It was rougher.** Its worst fall was −43% against IIMA's −26% over the same months.
- **The details moved the average by several points.** Without the size split it made 16.1% a year;
  with turnover weights, 8.7%; without skipping the latest month, 11.3%; with today's survivors only,
  9.9%. Every variant kept a correlation of 0.73–0.76 with IIMA's.
- **Both halves agreed.** The correlation was 0.77 in 2014–2019 (17.1% a year against IIMA's 16.5%)
  and 0.74 in 2020–2025 (6.7% against 9.3%).
- **Winners change slowly.** On average 17% of the winners list was replaced each month.

### 3. Size and value helped explain NSE stocks; momentum didn't

<a href="docs/img/stocks.png"><picture><source media="(prefers-reduced-motion: reduce)" srcset="docs/img/stocks.png"><img src="docs/img/stocks.gif" alt="Median share of NSE stocks' monthly moves explained by CAPM, three and four factors, in-sample and out of sample, and how well each loading kept its ranking from 2013-2019 to 2020-2025" width="720"></picture></a>

Each stock's monthly return in the NSE archive (split-adjusted month-end prices, so dividends are
left out) minus IIMA's risk-free rate is regressed on the market alone (CAPM), on market, size and
value (three factors), and on those plus momentum (four factors), with Newey-West t (3 lags).
In-sample: the 494 stocks with at least 60 months between February 2013 and December 2025. Out of
sample: for the 389 stocks with at least 48 months in each half, loadings fitted on 2013–2019
predict each 2020–2025 month from that month's factor returns, with no alpha; the score is the
share of the stock's 2020–2025 variation that prediction explains. The archive holds stocks that
were among its most-traded at some point from 2013 (140 of its 556 stocks were first priced after
June 2013), so in-sample alphas are not evidence of skill.

- **The market alone explained about a quarter.** CAPM's median R² was 24.5% in-sample; three
  factors 30.3%, four 31.4%.
- **Three factors kept their edge out of sample.** Loadings from 2013–2019 explained a median 23.5%
  of 2020–2025 with CAPM, 26.5% with three factors and 25.2% with four; three factors beat CAPM for
  71% of stocks, and four beat three for only 42%.
- **Most stocks leaned small, and many cheap.** Measured against IIMA's factors, where big means the
  top 10% of all listed companies, the median size loading was +0.40 (significantly positive for
  44% of stocks) and value +0.19 (28%); momentum −0.16, significantly negative for 14%.
- **Size and value loadings carried over; momentum's didn't.** Ranked across stocks, 2013–2019
  loadings matched 2020–2025 with a correlation of 0.55 for size, 0.44 for value and 0.18 for
  momentum. CAPM beta kept 0.52, but the market loading inside the four-factor model only 0.11.

### 4. No model priced IIMA's own portfolios; four factors left the smallest alphas overall

<a href="docs/img/grs.png"><picture><source media="(prefers-reduced-motion: reduce)" srcset="docs/img/grs.png"><img src="docs/img/grs.gif" alt="Alpha of nine IIMA size-value and size-momentum portfolios under CAPM, three and four factors, and the GRS statistic for each model by period against its 5% line" width="720"></picture></a>

The test assets are IIMA's six size-value portfolios less big value (absent in 154 months, when it
held under five stocks) and its four size-momentum portfolios, in excess of the risk-free rate,
over the 377 months with all nine, November 1993 to December 2025. Each is regressed on CAPM, three
and four factors; the Gibbons-Ross-Shanken (GRS) test asks whether all nine alphas are zero at once,
assuming normal, independent errors. Big value is tested alone on its own 232 months. The factors
are built from these same portfolios: IIMA's published size, value and momentum factors match the
corresponding portfolio differences with monthly correlations of 0.995, 0.997 and 0.983 (they are
compounded from daily returns, so not exactly), so the test asks whether the factors' averages
line up with the portfolios' averages, not whether unrelated assets are priced.

- **Every model was rejected.** GRS was 3.07 for CAPM, 5.44 for three factors and 4.35 for four,
  against a 5% critical value of 1.91 (p 0.0015 and below 0.0001).
- **Four factors left the smallest alphas.** The average alpha, ignoring sign, was 4.0% a year
  for CAPM, 3.7% for three factors and 2.8% for four.
- **Three factors couldn't price momentum.** Their alphas were +7.3% and +6.4% a year for big and
  small winners and −6.7% and −6.5% for big and small losers; with momentum added they were +0.9%,
  +2.5%, +7.4% and +2.4%.
- **The rejection held in both halves.** In 1993–2009, GRS was 2.05 for CAPM (p 0.036), 3.32 and
  3.09; in 2010–2025, 5.63, 6.37 and 4.60.
- **Big value on its own was not rejected.** Its alpha was +9.4% a year under CAPM (t 1.55) and
  −3.3% under three factors (t −1.39).

### 5. Funds kept a small alpha after the four factors, mostly inside the index funds' range

<a href="docs/img/funds.png"><picture><source media="(prefers-reduced-motion: reduce)" srcset="docs/img/funds.png"><img src="docs/img/funds.gif" alt="Histogram of 297 Indian active equity funds' four-factor alpha against six index funds, and growth of one rupee in the top and bottom thirds of funds ranked on their past three years' alpha, 2017-2025" width="720"></picture></a>

Every Indian diversified equity fund that mfapi.in lists with a direct plan and growth option
(sector, thematic, overseas, index and closed-ended schemes left out), including 56 that have
since stopped reporting: monthly returns from each month's last net asset value, after fees, from
January 2013, when direct plans began, to December 2025; 297 funds with at least 36 months. Each
fund's return above the risk-free rate is regressed on CAPM, three and four factors (Newey-West t,
3 lags). Six index funds tracking NIFTY 50, NIFTY Next 50, Midcap 150 and Smallcap 250 go through
the same regression as a zero-skill baseline, since they only hold their index. Out of sample,
each December from 2016 the funds with a full 36 months (167–215) are ranked on that window's
four-factor alpha, and the top and bottom thirds are held equally weighted for the next 12 months;
nothing after the ranking date is used.

- **More factors raised funds' alpha.** The median alpha was +1.4% a year under CAPM, +1.5% under
  three factors and +2.6% under four; 24% of funds had t above 2 under four factors and none below
  −2. Most styles leaned slightly away from momentum (median loadings −0.01 to −0.09).
- **Index funds set the bar.** The six index funds' four-factor alphas ranged from −3.0% to +3.6% a
  year (all t below 1.4); 34% of active funds beat the best of them.
- **Funds that stopped did worse.** The 56 that stopped reporting had a median four-factor alpha of
  +0.6% a year against +3.1% for the rest.
- **Mid and small cap funds showed the most.** Median four-factor alpha +4.8% a year each, with size
  loadings of +0.25 and +0.41; large cap funds +1.1%.
- **Past alpha persisted a little.** From 2017 to 2025 the past top third returned 18.0% a year with
  a four-factor alpha of +3.7% (t 2.20), the bottom third 16.1% and +2.4% (t 1.60); top minus
  bottom +1.4% a year (t 2.10).

### 6. Momentum's crashes came in rebounds; scaling by volatility didn't help out of sample

<a href="docs/img/crashes.png"><picture><source media="(prefers-reduced-motion: reduce)" srcset="docs/img/crashes.png"><img src="docs/img/crashes.gif" alt="Monthly momentum returns against the market's, marking months after bear markets, and each factor's Sharpe ratio unscaled and volatility-scaled in 1994-2009 and 2010-2025" width="720"></picture></a>

IIMA's monthly and daily factors, November 1993 to December 2025. A month counts as after a bear
market when the market's return above cash over the previous 24 months was below zero (142 of 361
months). Volatility scaling, after Barroso and Santa-Clara (2015): each month a factor is held at
a weight of a target volatility over its realised volatility from the previous month-end's daily
returns, capped at 2. The look-back (21, 63, 126 or 252 trading days) is the one with the best
Sharpe ratio on 1994–2009, and the target is the factor's 1994–2009 volatility; both are then
fixed and scored on 2010–2025. Because 2010–2025 was calmer, scaled weights averaged 1.7–1.9, so
worst months and falls are compared after setting both versions to the same volatility.

- **Momentum crashed in rebounds after bear markets.** After a bear market its correlation with
  the market was −0.50 (otherwise +0.20), and in the 76 such months when the market rose it averaged
  −26.8% a year. Four of its six worst months came then: November 2001 (−27.6%, market +12.4%), May
  2009 (−25.0%, market +33.6%), December 2008 and March 1998.
- **Each factor's worst months.** Market −29.1% (October 2008); size −14.1% (March 2020); value
  −19.0% (January 2000); momentum −27.6% (November 2001).
- **Scaling looked good where it was chosen.** On 1994–2009, scaled momentum's Sharpe ratio was
  0.64 against 0.38 unscaled; the market, size and value gained 0.03–0.10.
- **Out of sample it didn't help.** On 2010–2025 the Sharpe ratios were 0.92 against 0.90 for
  momentum, 0.36 against 0.43 for the market, 0.37 against 0.42 for value and 0.06 against 0.07 for
  size; at the same volatility scaled momentum's worst month was −18.5% against −18.0% and its worst
  fall −35% against −33%.

### 7. Use value and momentum together; momentum survived costs as a long-only tilt

<a href="docs/img/verdict.png"><picture><source media="(prefers-reduced-motion: reduce)" srcset="docs/img/verdict.png"><img src="docs/img/verdict.gif" alt="Sharpe ratios of value, momentum, a 50/50 mix and fitted mixes in 1993-2009 and 2010-2025, and growth of one rupee in long-only liquid momentum winners after costs against the equal-weighted top 200 and NIFTY, 2014-2026" width="720"></picture></a>

The findings put together, in three checks. First, value and momentum combined: a 50/50 mix with
nothing fitted, and maximum-Sharpe weights fitted on 1994–2009 (value and momentum only, and all
four factors) and scored on 2010–2025. Second, what a long-only investor could capture: IIMA's
long-only winner and value portfolios against the market's own return. Third, a long-only momentum
tilt built from the archive: each month-end, the top 30% by 12-1 momentum within the reference model's
point-in-time universe (that day's 200 most-traded stocks priced at ₹50 or more, so no look-ahead
in which stocks are eligible), equally weighted, paying NSE delivery costs on every trade (STT,
stamp duty, exchange and SEBI charges with GST, and 5 bp of slippage each side, as checked in
momentum-after-costs), from February 2014 to November 2026, against the equally weighted top 200
and NIFTY's price index. Before tax and without dividends; the IIMA portfolios carry no costs.

- **A plain 50/50 mix did best out of sample.** Its Sharpe ratio was 0.69 in 1993–2009 and 1.27 in
  2010–2025, against 0.42 for value and 0.90 for momentum alone; its worst fall in 2010–2025 was −12%
  against −50% and −33%. Weights fitted on 1994–2009 scored 1.16 (value and momentum) and 0.93 (all
  four, which shorted size) out of sample.
- **Long-only winners beat the market.** IIMA's big winners beat the market's own return by 6.8% a
  year from 1993 (t 2.80), 3.6% since 2010 (t 1.52); small winners by 10.5% since 2010 (t 3.02).
  Long-only value was noisier: big value +9.6% a year (t 1.56) with a 28.9% tracking error.
- **The liquid momentum tilt survived costs.** Trading 24% of the book a month cost 0.93% a year. It
  compounded 19.8% a year after costs against 15.4% for the equally weighted top 200 and 11.9% for
  NIFTY's price index; it beat the top 200 by 3.9% a year after costs (t 1.98), 4.3% in 2014–2019
  and 3.6% in 2020–2026, and its worst fall was −30% against −43%.
- **The verdict.** For risk, use market, size and value (finding 3). For alpha, use all four factors
  and judge against same-style index funds (findings 4 and 5). Tilt towards momentum and value
  together rather than either alone, long-only, and expect momentum's crashes in rebounds after bear
  markets (finding 6); size earned nothing here (finding 1).

## Quick start

```bash
uv sync
uv run python scripts/fetch_data.py   # IIMA factor library -> data/iima/
uv run python scripts/fetch_funds.py  # fund NAVs from mfapi.in -> data/funds/ (for funds)
uv run ff report factors              # topics: factors, momentum, stocks, grs, funds,
                                      # crashes, verdict
uv run python scripts/build_site.py   # factor lab -> site/index.html
uv run pytest
```

The factor files are downloaded, not committed. The NIFTY comparison and later stock studies read a
local NSE bhavcopy archive (`FF_LAKE_DIR`, default `/path/to/lake`) and are skipped without
it.

## Design

- `src/ff/data.py`: finds the library's latest release, downloads its survivorship-bias adjusted
  factor and portfolio files with retries, and loads them as decimal returns by month-end.
- `src/ff/stats.py`: least squares with Newey-West t statistics, the return summary (average,
  volatility, compounded growth, t, worst month, worst 12 months, worst fall) and the
  Gibbons-Ross-Shanken test (F p-value from scipy).
- `src/ff/ff.js`: the lab's browser copy of the regression and summary, and monthly returns from
  mfapi.in net asset values, tested against Python through Node to 1e-8.
- `src/ff/site.py`: the factor lab, one static Plotly page that carries the monthly factors; fund
  prices are fetched live from mfapi.in.
- `src/ff/lake.py`: NIFTY's monthly return from the local NSE archive.
- `src/ff/momentum.py`: month-end prices and past-year turnover from the archive, and winners
  minus losers built the IIMA way (size by turnover, equal or turnover weights).
- `src/ff/exposures.py`: single stocks on CAPM, three and four factors: fits, out-of-sample
  explanation from earlier loadings, and loadings in each half.
- `src/ff/funds.py`: diversified equity funds' NAV histories from mfapi.in (cached, not committed),
  styles from fund names, index funds as the baseline, alphas and the ranking test.
- `src/ff/crashes.py`: volatility scaling from daily factor returns (look-back and target chosen on
  the training years), and skew.
- `src/ff/verdict.py`: maximum-Sharpe weights, NSE delivery costs, and the long-only momentum tilt
  within the reference model's point-in-time top 200.
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
