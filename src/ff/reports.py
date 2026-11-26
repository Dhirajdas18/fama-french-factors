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
    ax.set_title("Three factors beat the market alone, out of sample too", fontsize=10.5,
                 loc="left")
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


def report_grs(out_dir: Path) -> dict:
    """Do CAPM, three and four factors price IIMA's own portfolios? Test assets: the six
    size-value portfolios less big value (missing in 154 months, when it held under five stocks)
    and the four size-momentum portfolios, in excess of the risk-free rate; the GRS test that all
    nine alphas are zero, whole period and halves; big value tested alone on its own months. Also
    how closely the published factors rebuild from these portfolios."""
    from scipy.stats import f as fdist

    from ff import data, stats

    f = data.factors()
    sv, sm = data.portfolios("size_value"), data.portfolios("size_momentum")
    P = pd.concat([sv.drop(columns="BV"), sm], axis=1)
    j = P.join(f, how="inner").dropna()
    ex = j[P.columns].sub(j["RF"], axis=0)
    models = {"CAPM": ["MKT"], "3-factor": ["MKT", "SMB", "HML"],
              "4-factor": ["MKT", "SMB", "HML", "WML"]}
    res = {"test assets": f"{', '.join(P.columns)}; {len(j)} months, "
                          f"{j.index[0]:%b %Y}-{j.index[-1]:%b %Y}"}
    out = {}
    for per, a, b in (("all", None, None), *HALVES):
        e, g_ = ex.loc[a:b], j.loc[a:b]
        for m, c in models.items():
            g = stats.grs(e.to_numpy(), g_[c].to_numpy())
            crit = fdist.isf(0.05, g["N"], g["T"] - g["N"] - len(c))
            out[(per, m)] = (g, crit)
            txt = (f"GRS {g['grs']:.2f} (5% critical {crit:.2f}), p {g['p']:.4f}; mean |alpha| "
                   f"{12 * g['mean_abs_alpha']:.1%} a year")
            if per == "all":
                txt += "; alphas % a year: " + ", ".join(
                    f"{k} {1200 * v:+.1f}" for k, v in zip(P.columns, g["alpha"], strict=True))
            res[f"{per}, {m} ({g['T']} months)"] = txt
    k = sv[["BV"]].join(f, how="inner").dropna()
    for m, c in models.items():
        o = stats.ols((k["BV"] - k["RF"]).to_numpy(), k[c].to_numpy())
        res[f"  big value alone, {m} ({len(k)} months)"] = (
            f"alpha {12 * o['b'][0]:+.1%} a year (t {o['t'][0]:.2f})")
    b = sv.join(sm).join(f[["SMB", "HML", "WML"]], how="inner")
    full = b.dropna()
    smb = full[["SV", "SN", "SG"]].mean(axis=1) - full[["BV", "BN", "BG"]].mean(axis=1)
    hml = (full["SV"] + full["BV"]) / 2 - (full["SG"] + full["BG"]) / 2
    q = b.dropna(subset=["WB", "WS", "LB", "LS", "WML"])
    wml = ((q["WB"] - q["LB"]) + (q["WS"] - q["LS"])) / 2
    res["published factors against the same differences of the portfolios"] = "; ".join(
        f"{n} correlation {x.corr(y):.3f}" for n, x, y in
        (("SMB", smb, full["SMB"]), ("HML", hml, full["HML"]), ("WML", wml, q["WML"])))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.5, 1]})
    ax = axes[0]
    x = np.arange(len(P.columns))
    for i, (m, col) in enumerate(zip(models, (plots.MUTED, plots.SERIES[2], plots.COLORS["WML"]),
                                     strict=True)):
        g = out[("all", m)][0]
        ax.bar(x + (i - 1) * 0.27, 1200 * g["alpha"], 0.25, color=col, label=m)
    ax.axhline(0, color=plots.TEXT_2, lw=0.8)
    names = {"BN": "big\nneutral", "BG": "big\ngrowth", "SV": "small\nvalue",
             "SN": "small\nneutral", "SG": "small\ngrowth", "WB": "big\nwinners",
             "WS": "small\nwinners", "LB": "big\nlosers", "LS": "small\nlosers"}
    ax.set_xticks(x, [names[c] for c in P.columns], fontsize=8.5)
    ax.set_ylabel("alpha, % a year")
    ax.legend(frameon=False, fontsize=9, ncols=3, loc="upper left")
    ax.margins(y=0.2)
    ax.set_title("Each portfolio's alpha, 1993-2025", fontsize=10.5, loc="left")
    ax = axes[1]
    pers = ["all", "1993-2009", "2010-2025"]
    y = np.arange(len(pers))[::-1]
    for i, (m, col) in enumerate(zip(models, (plots.MUTED, plots.SERIES[2], plots.COLORS["WML"]),
                                     strict=True)):
        v = [out[(p, m)][0]["grs"] for p in pers]
        ax.barh(y + (1 - i) * 0.27, v, 0.25, color=col)
    crit = out[("all", "CAPM")][1]
    ax.axvline(crit, color=plots.TEXT_2, lw=1, ls="--")
    ax.text(crit, y[-1] - 0.5, " 5% line", fontsize=8.5, color=plots.TEXT_2, va="top")
    ax.set_yticks(y, ["1993-2025", "1993-2009", "2010-2025"])
    ax.set_xlabel("GRS statistic (past the line: alphas not all zero)")
    ax.set_title("All three models rejected", fontsize=10.5, loc="left")
    fig.suptitle("No model priced IIMA's own portfolios; four factors left the smallest alphas "
                 "overall",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    plots.save(fig, out_dir, "grs")
    plt.close(fig)
    return res


def report_funds(out_dir: Path) -> dict:
    """Indian diversified equity funds (direct plans, growth, from mfapi.in; closed and merged
    schemes included where listed): CAPM, three- and four-factor alphas after fees from January
    2013 (direct plans start then), funds with 36+ months; index funds as the zero-skill
    baseline; alphas of funds that stopped reporting; loadings by style; and persistence out of
    sample: each December from 2015, rank funds on their past 36 months' four-factor alpha, hold
    the top and bottom thirds equally weighted for the next 12 months. Needs scripts/fetch_funds."""
    from ff import data, funds, stats

    f = data.factors()
    r, info = funds.load()
    r = r.loc["2013-01-31":]
    C4 = ["MKT", "SMB", "HML", "WML"]
    models = {"CAPM": ["MKT"], "3-factor": C4[:3], "4-factor": C4}
    res, tabs = {}, {}
    for m, c in models.items():
        a = funds.alpha_table(r, f, c)
        tabs[m] = a
        res[f"{m}, {len(a)} funds"] = (
            f"median alpha {a['alpha'].median():+.1%} a year (mean {a['alpha'].mean():+.1%}); "
            f"t > 2 for {(a['t'] > 2).mean():.0%}, t < -2 for {(a['t'] < -2).mean():.0%}; "
            f"median R² {a['r2'].median():.0%}")
    a4 = tabs["4-factor"].join(info)
    res["  fund months"] = (f"{a4['n'].min():.0f}-{a4['n'].max():.0f} per fund, "
                            f"{r.index[0]:%b %Y}-{f.index[-1]:%b %Y}")
    ix = funds.alpha_table(funds.index_returns().loc["2013-01-31":], f, C4)
    capm_ix = funds.alpha_table(funds.index_returns().loc["2013-01-31":], f, ["MKT"])
    res["index funds (baseline), 4-factor alpha"] = "; ".join(
        f"{n} {v:+.1%} (t {t:.2f})" for n, v, t in zip(ix.index, ix["alpha"], ix["t"],
                                                     strict=True))
    res["  index funds, CAPM alpha"] = (f"{capm_ix['alpha'].min():+.1%} to "
                                        f"{capm_ix['alpha'].max():+.1%}")
    res["  active funds above the best index fund's 4-factor alpha"] = (
        f"{(a4['alpha'] > ix['alpha'].max()).mean():.0%}")
    stopped = a4["last"] < pd.Timestamp("2026-10-01")
    res["funds that stopped reporting"] = (
        f"{stopped.sum()} of {len(a4)}: median 4-factor alpha "
        f"{a4.loc[stopped, 'alpha'].median():+.1%} against "
        f"{a4.loc[~stopped, 'alpha'].median():+.1%} for the rest")
    g = a4.groupby("category")[["alpha", "MKT", "SMB", "HML", "WML"]].median()
    for k, row in g.iterrows():
        res[f"  {k} ({(a4['category'] == k).sum()})"] = (
            f"alpha {row['alpha']:+.1%}, market {row['MKT']:.2f}, size {row['SMB']:+.2f}, "
            f"value {row['HML']:+.2f}, momentum {row['WML']:+.2f}")
    p = funds.persistence(r, f, C4)
    res["persistence"] = (f"{p['formed'].nunique()} formations, {len(p)} holding months "
                          f"({p.index[0]:%b %Y}-{p.index[-1]:%b %Y}), "
                          f"{p['n'].min()}-{p['n'].max()} funds ranked")
    for c, lab in (("top", "top third"), ("bottom", "bottom third"), ("all", "all ranked")):
        y = p[c]
        o = stats.ols((y - f.loc[y.index, "RF"]).to_numpy(), f.loc[y.index, C4].to_numpy())
        res[f"  {lab}"] = (f"return {12 * y.mean():+.1%} a year; 4-factor alpha "
                           f"{12 * o['b'][0]:+.1%} (t {o['t'][0]:.2f})")
    d = p["top"] - p["bottom"]
    o = stats.ols(d.to_numpy(), f.loc[d.index, C4].to_numpy())
    res["  top minus bottom"] = (f"{12 * d.mean():+.1%} a year; 4-factor alpha "
                                 f"{12 * o['b'][0]:+.1%} (t {o['t'][0]:.2f})")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    ax = axes[0]
    bins = np.arange(-0.10, 0.125, 0.01)
    ax.hist(a4["alpha"].clip(-0.099, 0.119), bins=bins, color=plots.SERIES[0], rwidth=0.9)
    for v in ix["alpha"]:
        ax.axvline(v, color=plots.TEXT_2, lw=1, ls="--")
    ax.text(ix["alpha"].max(), ax.get_ylim()[1] * 0.95, " index funds (dashed)",
            fontsize=8.5, color=plots.TEXT_2, va="top")
    ax.xaxis.set_major_formatter(lambda v, _: f"{100 * v:+.0f}%")
    ax.set_xlabel("four-factor alpha a year, after fees")
    ax.set_ylabel("number of funds")
    ax.set_title(f"{len(a4)} active funds against six index funds", fontsize=10.5, loc="left")
    ax = axes[1]
    for c, lab, col in (("top", "past alpha: top third", plots.SERIES[2]),
                        ("all", "all ranked funds", plots.MUTED),
                        ("bottom", "past alpha: bottom third", plots.SERIES[1])):
        w = (1 + p[c]).cumprod()
        ax.plot(w.index, w, color=col, lw=2)
        plots.label_line_end(ax, w.index[-1], float(w.iloc[-1]), lab, col)
    ax.yaxis.set_major_formatter(lambda v, _: f"₹{v:g}")
    ax.set_ylabel("₹1 invested each January, rebalanced yearly")
    ax.set_title("Ranked on the past 3 years, held the next year", fontsize=10.5, loc="left")
    fig.suptitle("Funds kept a small alpha after the four factors, mostly inside the index funds' "
                 "range",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    plots.save(fig, out_dir, "funds")
    plt.close(fig)
    return res


REPORTS: dict[str, Callable[[Path], dict]] = {
    "factors": report_factors,
    "momentum": report_momentum,
    "stocks": report_stocks,
    "grs": report_grs,
    "funds": report_funds,
}
