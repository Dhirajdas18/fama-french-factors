// Factor lab maths, mirrored from ff/stats.py (tested against it through Node).
const FF = (() => {
  // Solve A x = b for a small symmetric positive-definite A (Gauss-Jordan with pivoting).
  function solve(A, b) {
    const n = b.length, M = A.map((r, i) => [...r, b[i]]);
    for (let c = 0; c < n; c++) {
      let p = c;
      for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
      [M[c], M[p]] = [M[p], M[c]];
      for (let r = 0; r < n; r++) {
        if (r === c) continue;
        const f = M[r][c] / M[c][c];
        for (let k = c; k <= n; k++) M[r][k] -= f * M[c][k];
      }
    }
    return M.map((r, i) => r[n] / r[i]);
  }
  function inverse(A) {
    const n = A.length;
    const cols = A.map((_, j) => solve(A, A.map((_, i) => (i === j ? 1 : 0))));
    return A.map((_, i) => cols.map((c) => c[i]));
  }
  const mm = (A, B) => A.map((r) => B[0].map((_, j) => r.reduce((s, v, k) => s + v * B[k][j], 0)));
  // OLS of y on [1, X] with Newey-West (Bartlett) t-statistics, as stats.ols.
  function ols(y, X, lags = 3) {
    const n = y.length, Z = y.map((_, i) => [1, ...(X[i] || [])]), p = Z[0].length;
    const ZtZ = Array.from({ length: p }, (_, a) => Array.from({ length: p }, (_, b) =>
      Z.reduce((s, z) => s + z[a] * z[b], 0)));
    const Zty = Array.from({ length: p }, (_, a) => Z.reduce((s, z, i) => s + z[a] * y[i], 0));
    const b = solve(ZtZ, Zty);
    const e = y.map((v, i) => v - Z[i].reduce((s, z, k) => s + z * b[k], 0));
    const xe = Z.map((z, i) => z.map((v) => v * e[i]));
    const S = Array.from({ length: p }, (_, a) => Array.from({ length: p }, (_, c) =>
      xe.reduce((s, r) => s + r[a] * r[c], 0)));
    for (let k = 1; k <= lags; k++) {
      const w = 1 - k / (lags + 1);
      for (let a = 0; a < p; a++) for (let c = 0; c < p; c++) {
        let g = 0;
        for (let i = k; i < n; i++) g += xe[i][a] * xe[i - k][c] + xe[i][c] * xe[i - k][a];
        S[a][c] += w * g;
      }
    }
    const inv = inverse(ZtZ), V = mm(mm(inv, S), inv);
    const t = b.map((v, i) => v / Math.sqrt(V[i][i] * n / (n - p)));
    const ym = y.reduce((s, v) => s + v, 0) / n;
    const r2 = 1 - e.reduce((s, v) => s + v * v, 0) / y.reduce((s, v) => s + (v - ym) ** 2, 0);
    return { b, t, r2, n, resid: e };
  }
  // Monthly decimal returns -> the statistics of stats.summary (annual mean, vol, compound
  // growth over n/12 years, Newey-West t of the mean, worst fall of the compounded value).
  function summary(r) {
    const n = r.length, m = r.reduce((s, v) => s + v, 0) / n;
    const sd = Math.sqrt(r.reduce((s, v) => s + (v - m) ** 2, 0) / (n - 1));
    let w = 1, peak = 1, dd = 0;
    for (const v of r) { w *= 1 + v; peak = Math.max(peak, w); dd = Math.min(dd, w / peak - 1); }
    return { n, mean: m * 12, vol: sd * Math.sqrt(12), cagr: w ** (12 / n) - 1,
             t: ols(r, []).t[0], dd };
  }
  // mfapi.in NAV rows [{date: "dd-mm-yyyy", nav: "123.4"}] -> {"YYYY-MM": return} using each
  // month's last NAV; a month counts only if the month before it has a NAV too.
  function monthlyReturns(rows) {
    const last = {};
    for (const { date, nav } of rows) {
      const [d, m, y] = date.split("-"), key = `${y}-${m}`, v = parseFloat(nav);
      if (!(v > 0)) continue;
      if (!last[key] || +d > last[key].d) last[key] = { d: +d, v };
    }
    const out = {};
    for (const key of Object.keys(last).sort()) {
      const [y, m] = key.split("-").map(Number);
      const prev = m === 1 ? `${y - 1}-12` : `${y}-${String(m - 1).padStart(2, "0")}`;
      if (last[prev]) out[key] = last[key].v / last[prev].v - 1;
    }
    return out;
  }
  return { ols, summary, monthlyReturns };
})();
if (typeof module !== "undefined") module.exports = FF;
