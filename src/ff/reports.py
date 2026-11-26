"""README findings, one function per topic: `ff report <topic>` writes charts to out/."""

from collections.abc import Callable
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ff import plots

HALVES = (("1993-2009", None, "2009"), ("2010-2025", "2010", None))


def _fmt(s: dict) -> str:
    return (f"{s['n']} months: mean {s['mean']:+.1%} a year (t {s['t']:.2f}), compounded "
            f"{s['cagr']:+.1%}, volatility {s['vol']:.1%}, positive {s['pos']:.0%}, worst month "
            f"{s['worst']:+.1%}, worst 12 months {s['worst12']:+.1%}, worst fall {s['dd']:.0%}")


def report_factors(out_dir: Path) -> dict:
    """What market, size, value and momentum earned in India: IIMA's monthly factors (the latest
    release, survivorship-bias adjusted), whole period and two halves, their worst falls and how
    they move together. The market factor is the market's return minus the risk-free rate (the
    file's MF); the other three are long-short. Newey-West t (3 lags). Also the market's own
    return (MF + RF) against NIFTY from the NSE bhavcopy archive where both exist."""
    from ff import data, stats

    f = data.factors()
    res = {"data": f"IIMA release {data.release()}, {f.index[0]:%b %Y}-{f.index[-1]:%b %Y}, "
                   f"{len(f)} months"}
    means = {}
    for c in data.FACTORS:
        s = stats.summary(f[c])
        res[f"{data.NAMES[c]} ({c}), all"] = _fmt(s)
        for lab, a, b in HALVES:
            h = stats.summary(f[c].loc[a:b])
            means[(c, lab)] = (h["mean"], h["t"])
            res[f"  {c} {lab}"] = _fmt(h)
        w = (1 + f[c]).cumprod()
        dd = w / w.cummax() - 1
        end = dd.idxmin()
        res[f"  {c} worst fall"] = f"{dd.min():.0%} from {w[:end].idxmax():%b %Y} to {end:%b %Y}"
        r5 = (1 + f[c]).rolling(60).apply(np.prod, raw=True) ** (1 / 5) - 1
        res[f"  {c} five-year windows"] = (f"compounded {r5.min():+.1%} to {r5.max():+.1%} a year; "
                                       f"below zero in {(r5 < 0).mean():.0%} of windows")
    c = f[data.FACTORS].corr()
    res["correlations"] = "; ".join(f"{a}-{b} {c.at[a, b]:+.2f}" for i, a in enumerate(data.FACTORS)
                                    for b in data.FACTORS[i + 1:])
    res["market's own return and risk-free, compounded"] = (
        f"market {stats.summary(f['MARKET'])['cagr']:+.1%} a year, "
        f"risk-free {stats.summary(f['RF'])['cagr']:+.1%}")
    try:
        from ff.lake import nifty_monthly

        n = nifty_monthly()
        j = pd.concat([f["MARKET"], n], axis=1, join="inner").dropna()
        g = (1 + j).prod() ** (12 / len(j)) - 1
        res["IIMA market against NIFTY (price index)"] = (
            f"{j.index[0]:%b %Y}-{j.index[-1]:%b %Y}, {len(j)} months: correlation "
            f"{j.corr().iloc[0, 1]:.2f}; compounded {g.iloc[0]:+.1%} against {g.iloc[1]:+.1%}")
    except FileNotFoundError:
        res["IIMA market against NIFTY"] = "skipped (no NSE bhavcopy archive)"

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.5, 1]})
    ax = axes[0]
    for k in data.FACTORS:
        w = (1 + f[k]).cumprod()
        ax.plot(w.index, w, color=plots.COLORS[k], lw=2)
        plots.label_line_end(ax, w.index[-1], float(w.iloc[-1]), data.NAMES[k], plots.COLORS[k])
    ax.set_yscale("log")
    ax.axhline(1, color=plots.TEXT_2, lw=0.8)
    ax.set_yticks([0.1, 0.3, 1, 3, 10, 30])
    ax.set_yticklabels(["₹0.1", "₹0.3", "₹1", "₹3", "₹10", "₹30"])
    ax.set_ylabel("₹1 in each factor, compounded monthly")
    ax.set_title("₹1 in each factor since 1993", fontsize=10.5, loc="left")
    ax = axes[1]
    x = np.arange(len(data.FACTORS))
    for i, (lab, *_) in enumerate(HALVES):
        v = [100 * means[(k, lab)][0] for k in data.FACTORS]
        bars = ax.bar(x + (i - 0.5) * 0.38, v, 0.36, color=plots.SERIES[0] if i else plots.MUTED,
                      label=lab)
        for b, k in zip(bars, data.FACTORS, strict=True):
            m, t = means[(k, lab)]
            top = (b.get_x() + b.get_width() / 2, b.get_height())
            ax.annotate(f"{100 * m:+.1f}\nt {t:.1f}", top,
                        xytext=(0, 3 if m >= 0 else -3), textcoords="offset points", ha="center",
                        va="bottom" if m >= 0 else "top", fontsize=8, color=plots.TEXT)
    ax.axhline(0, color=plots.TEXT_2, lw=0.8)
    ax.set_xticks(x, [data.NAMES[k] for k in data.FACTORS])
    ax.set_ylabel("average return, % a year")
    ax.set_title("Average a year, by half", fontsize=10.5, loc="left")
    ax.legend(frameon=False, fontsize=9)
    ax.margins(y=0.2)
    fig.suptitle("Momentum and value paid most in India; small companies didn't beat big ones",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    plots.save(fig, out_dir, "factors")
    plt.close(fig)
    return res


def report_momentum(out_dir: Path) -> dict:
    """Momentum rebuilt from the NSE archive (ff.momentum) against IIMA's WML over the months
    both cover: the IIMA-like build (12-1 momentum, top and bottom 30%, big = top 10% by past
    turnover, equal weights), and one change at a time: turnover weights, no size split, no
    skipped month, and today's survivors only. Correlation, average a year with Newey-West t,
    the regression of ours on IIMA's, tracking error, and how much of the winners changes each
    month. Needs the NSE bhavcopy archive."""
    from ff import data, momentum, stats

    f = data.factors()
    px, tv = momentum.monthly_panel()
    alive = px.columns[px.iloc[-1].notna()]
    variants = {
        "IIMA-like": ({}, px),
        "turnover weights": ({"weight": "turnover"}, px),
        "no size split": ({"sized": False}, px),
        "no skipped month": ({"skip": 0}, px),
        "survivors only": ({}, px[alive]),
    }
    res, out = {}, {}
    for name, (kw, p) in variants.items():
        w = momentum.wml(p, tv[p.columns], **kw)
        j = pd.concat([w["WML"], f["WML"].rename("IIMA")], axis=1, join="inner").dropna()
        o = stats.ols(j["WML"], j["IIMA"].to_numpy())
        s, si = stats.summary(j["WML"]), stats.summary(j["IIMA"])
        out[name] = (j, s)
        res[name] = (
            f"{len(j)} months ({j.index[0]:%b %Y}-{j.index[-1]:%b %Y}), median "
            f"{w['n'].median():.0f} stocks: mean {s['mean']:+.1%} a year (t {s['t']:.2f}) against "
            f"IIMA {si['mean']:+.1%} (t {si['t']:.2f}); correlation {j.corr().iloc[0, 1]:.2f}; "
            f"ours = {12 * o['b'][0]:+.1%}"
            f" a year + {o['b'][1]:.2f} x IIMA (R² {o['r2']:.2f}); tracking error "
            f"{(j['WML'] - j['IIMA']).std() * np.sqrt(12):.1%} a year; worst fall {s['dd']:.0%} "
            f"(IIMA {si['dd']:.0%})")
    res["  delisted or stopped trading in the archive"] = (
        f"{px.shape[1] - len(alive)} of {px.shape[1]} stocks")
    j = out["IIMA-like"][0]
    for lab, a, b in (("2014-2019", None, "2019"), ("2020-2025", "2020", None)):
        h = j.loc[a:b]
        res[f"  IIMA-like, {lab}"] = (
            f"correlation {h.corr().iloc[0, 1]:.2f}; mean {12 * h['WML'].mean():+.1%} against "
            f"{12 * h['IIMA'].mean():+.1%}")
    # winners' turnover: share of the winners list replaced from one month to the next
    mom = px.shift(1) / px.shift(12) - 1
    chg = []
    prev = None
    for t in px.index[12:-1]:
        m = mom.loc[t].dropna()
        if len(m) < 50:
            continue
        win = set(m[m >= m.quantile(0.7)].index)
        if prev:
            chg.append(1 - len(win & prev) / len(prev))
        prev = win
    res["  winners replaced each month"] = f"{np.mean(chg):.0%} on average"

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"width_ratios": [1.4, 1]})
    ax = axes[0]
    lines = (("IIMA (all listed, value-weighted)", j["IIMA"], plots.MUTED),
             ("rebuilt, IIMA-like (archive)", j["WML"], plots.COLORS["WML"]),
             ("rebuilt, no size split", out["no size split"][0]["WML"], plots.SERIES[0]))
    for lab, r, col in lines:
        w = (1 + r).cumprod()
        ax.plot(w.index, w, color=col, lw=2)
        plots.label_line_end(ax, w.index[-1], float(w.iloc[-1]), lab, col)
    ax.axhline(1, color=plots.TEXT_2, lw=0.8)
    ax.set_ylabel("₹1 in winners minus losers,\ncompounded monthly")
    ax.yaxis.set_major_formatter(lambda v, _: f"₹{v:g}")
    ax.set_title("Momentum rebuilt from the archive against IIMA's", fontsize=10.5, loc="left")
    ax = axes[1]
    names = list(variants)
    y = np.arange(len(names))[::-1]
    vals = [100 * out[n][1]["mean"] for n in names]
    ax.barh(y, vals, color=[plots.COLORS["WML"]] + [plots.SERIES[0]] * (len(names) - 1),
            height=0.6)
    iima = 100 * stats.summary(j["IIMA"])["mean"]
    ax.axvline(iima, color=plots.TEXT_2, lw=1, ls="--")
    ax.text(iima, y[-1] - 0.45, f" IIMA {iima:+.1f}", fontsize=8.5, color=plots.TEXT_2, va="top")
    right = max(vals) * 1.08
    for yy, n, v in zip(y, names, vals, strict=True):
        c = out[n][0].corr().iloc[0, 1]
        ax.text(right, yy, f"{v:+.1f}  (corr {c:.2f})", va="center", fontsize=8.5,
                color=plots.TEXT)
    ax.set_yticks(y, names)
    ax.set_xlim(0, max(vals) * 1.6)
    ax.set_xlabel("average a year, %")
    ax.set_title("One change at a time", fontsize=10.5, loc="left")
    fig.suptitle("Momentum rebuilt from about 460 liquid NSE stocks tracked IIMA's factor",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    plots.save(fig, out_dir, "momentum")
    plt.close(fig)
    return res


def report_stocks(out_dir: Path) -> dict:
    """Single NSE stocks from the archive on CAPM, three and four factors. In-sample: every
    stock with 60+ months, February 2013 to December 2025: R², adjusted R², loadings and how many
    are significant. Out of sample: loadings fitted on 2013-2019 explain 2020-2025 from that
    period's factor returns (stocks with 48+ months in each half), and how well each loading
    keeps its cross-stock ranking from one half to the next. Needs the NSE bhavcopy archive."""
    from ff import exposures as ex
    from ff import momentum

    f = ex.factors()
    px, _ = momentum.monthly_panel()
    e = ex.stock_excess(px, f)
    ins = ex.in_sample(e, f)
    oo = ex.out_of_sample(e, f)
    res = {"in-sample": f"{ins['symbol'].nunique()} stocks with 60+ months, "
                        f"{e.index[1]:%b %Y}-{e.index[-1]:%b %Y}"}
    for m in ex.MODELS:
        g = ins[ins["model"] == m]
        res[f"  {m}"] = (f"median R² {g['r2'].median():.1%}, adjusted {g['adj_r2'].median():.1%}; "
                         f"median alpha {g['alpha'].median():+.1%} a year, |t| > 2 for "
                         f"{(g['t_alpha'].abs() > 2).mean():.0%}")
    g = ins[ins["model"] == "4-factor"]
    for c in ["MKT", "SMB", "HML", "WML"]:
        res[f"  4-factor {c} loading"] = (
            f"median {g[c].median():+.2f}; t > 2 for {(g[f't_{c}'] > 2).mean():.0%}, "
            f"t < -2 for {(g[f't_{c}'] < -2).mean():.0%}")
    res["out of sample"] = (f"{oo['symbol'].nunique()} stocks with 48+ months in 2013-2019 and "
                            "in 2020-2025")
    w = oo.pivot(index="symbol", columns="model", values="oos_r2")
    for m in ex.MODELS:
        g = oo[oo["model"] == m]
        res[f"  {m} (out of sample)"] = (
            f"median R² of 2020-2025 from 2013-2019 loadings {g['oos_r2'].median():.1%}; "
            f"refitted on 2020-2025 itself {g['r2_second'].median():.1%}")
    res["  3-factor beats CAPM out of sample"] = (
        f"{(w['3-factor'] > w['CAPM']).mean():.0%} of stocks")
    res["  4-factor beats 3-factor out of sample"] = (
        f"{(w['4-factor'] > w['3-factor']).mean():.0%} of stocks")
    stab = {}
    capm = oo[oo["model"] == "CAPM"]
    stab["market (CAPM beta)"] = capm["MKT_1"].rank().corr(capm["MKT_2"].rank())
    q = oo[oo["model"] == "4-factor"]
    for c, lab in (("MKT", "market (4-factor)"), ("SMB", "size"), ("HML", "value"),
                   ("WML", "momentum")):
        stab[lab] = q[f"{c}_1"].rank().corr(q[f"{c}_2"].rank())
    res["rank correlation of loadings, 2013-2019 against 2020-2025"] = "; ".join(
        f"{k} {v:.2f}" for k, v in stab.items())
    first = px.apply(lambda s: s.first_valid_index())
    res["  archive stocks first priced after June 2013"] = (
        f"{(first > pd.Timestamp('2013-06-30')).sum()} of {px.shape[1]}")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    ax = axes[0]
    x = np.arange(len(ex.MODELS))
    groups = (("in-sample, 2013-2025", [ins[ins["model"] == m]["r2"].median() for m in ex.MODELS],
               plots.MUTED),
              ("2020-2025 from 2013-2019 loadings",
               [oo[oo["model"] == m]["oos_r2"].median() for m in ex.MODELS], plots.SERIES[0]))
    for i, (lab, v, col) in enumerate(groups):
        bars = ax.bar(x + (i - 0.5) * 0.38, [100 * a for a in v], 0.36, color=col, label=lab)
        for b, a in zip(bars, v, strict=True):
            ax.annotate(f"{100 * a:.0f}%", (b.get_x() + b.get_width() / 2, b.get_height()),
                        xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8.5,
                        color=plots.TEXT)
    ax.set_xticks(x, list(ex.MODELS))
    ax.set_ylabel("median share of a stock's monthly\nmoves explained (R², %)")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.margins(y=0.25)
    ax.set_title("Three factors beat the market alone, out of sample too", fontsize=10.5, loc="left")
    ax = axes[1]
    labs = list(stab)
    y = np.arange(len(labs))[::-1]
    cols = [plots.COLORS["MKT"], plots.COLORS["MKT"], plots.COLORS["SMB"], plots.COLORS["HML"],
            plots.COLORS["WML"]]
    ax.barh(y, [stab[k] for k in labs], color=cols, height=0.6)
    for yy, k in zip(y, labs, strict=True):
        ax.text(stab[k] + 0.01, yy, f"{stab[k]:.2f}", va="center", fontsize=8.5, color=plots.TEXT)
    ax.set_yticks(y, labs)
    ax.set_xlim(0, 1)
    ax.set_xlabel("rank correlation across stocks,\n2013-2019 loading against 2020-2025")
    ax.set_title("Size and value loadings carried over; momentum's didn't",
                 fontsize=10.5, loc="left")
    fig.suptitle("Size and value helped explain NSE stocks; momentum didn't",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    plots.save(fig, out_dir, "stocks")
    plt.close(fig)
    return res


REPORTS: dict[str, Callable[[Path], dict]] = {
    "factors": report_factors,
    "momentum": report_momentum,
    "stocks": report_stocks,
}
