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
    they move together. The market factor is the market's return minus the risk-free rate; the
    other three are long-short. Newey-West t (3 lags). Also IIMA's market return against NIFTY
    from the NSE bhavcopy archive where both exist."""
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
    res["market return (MF) and risk-free (RF), compounded"] = (
        f"MF {stats.summary(f['MF'])['cagr']:+.1%} a year, "
        f"RF {stats.summary(f['RF'])['cagr']:+.1%}")
    try:
        from ff.lake import nifty_monthly

        n = nifty_monthly()
        j = pd.concat([f["MF"], n], axis=1, join="inner").dropna()
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
    fig.suptitle("Momentum and value paid in India; size and the market's premium over cash didn't",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    plots.save(fig, out_dir, "factors")
    plt.close(fig)
    return res


REPORTS: dict[str, Callable[[Path], dict]] = {
    "factors": report_factors,
}
