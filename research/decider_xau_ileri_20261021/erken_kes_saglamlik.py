"""B1 erken kesme — sağlamlık (ön-kayıt eki 2026-10-21, sonuçlara bakmadan sabit liste):
  (a) plato: dakika {3,5,7,10,15} × eşik {−0,3,−0,4,−0,5,−0,6,−0,7}
  (b) icra: çıkış = kesme barının KAPANIŞI yerine bir sonraki barın AÇILIŞI (+ yarım spread kayma)
  (c) spread ×1,5
  (d) bağımsız popülasyon: decider SELL kararları (ayna)
  (e) plasebo: aynı dakika ±10 gün rastgele gün, aynı ATR/spread ile 200 set → kuralın kazancı decider'a mı ait, braket mi
  (f) canlıya alma kartı 6 ölçütü (2. KURAL) kural = 5 dk / −0,5R için
python3 research/decider_xau_ileri_20261021/erken_kes_saglamlik.py"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import yol_adaylari as Y

HERE = Path(__file__).resolve().parent
MINS, THS = (3, 5, 7, 10, 15), (-0.3, -0.4, -0.5, -0.6, -0.7)
N_PLAC = 200


def sim2(hi, lo, cl, op, idx, ts, atr, spread, s=1, cut_min=None, cut_r=-0.5, next_open=False, horizon=Y.HORIZON_MIN):
    j = idx.searchsorted(ts, side="right")
    if j >= idx.size - 2 or not np.isfinite(atr) or atr <= 0 or (idx[j] - ts) > pd.Timedelta(minutes=5):
        return np.nan
    e = float(op[j]) + (spread if s > 0 else 0.0)
    risk = Y.SL_X * atr
    sl, tp = e - s * risk, e + s * Y.TP_X * atr
    adj = 0.0 if s > 0 else spread                       # SELL: çıkış ASK = BID + spread
    end = min(idx.size, j + horizon)
    for k in range(j, end):
        if (lo[k] if s > 0 else hi[k] + adj) * s <= sl * s:
            return -1.0
        if (hi[k] if s > 0 else lo[k] + adj) * s >= tp * s:
            return Y.TP_X / Y.SL_X
        if cut_min is not None and k == j + cut_min - 1:
            r = s * (cl[k] + adj - e) / risk
            if r <= cut_r:
                if next_open and k + 1 < idx.size:
                    px = op[k + 1] + adj - (spread / 2 if s > 0 else -spread / 2)
                    return float(s * (px - e) / risk)
                return float(r)
    return float(s * (cl[end - 1] + adj - e) / risk)


def run_set(D, arr, sp_mult=1.0, **kw):
    hi, lo, cl, op, idx = arr
    return np.array([sim2(hi, lo, cl, op, idx, t, a, s * sp_mult, sg, **kw)
                     for t, a, s, sg in zip(D.ts, D.atr, D.sp, D.sgn)])


def main() -> None:
    S = pd.read_pickle(HERE / "kurallar" / "sim_decider.pkl")
    S = S[S.in_analysis_set.astype(bool) & S.direction.isin(["BUY", "SELL"])].copy()
    S["ts"] = pd.to_datetime(S.ts, utc=True)
    S = S.sort_values("ts").reset_index(drop=True)
    S["atr"], S["sp"] = S.atr5_closed.astype(float), S.spread_used.fillna(0.14).astype(float)
    S["sgn"] = np.where(S.direction == "BUY", 1, -1)
    b = Y.load_bars()
    arr = (b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy(), b.open.to_numpy(), b.index)
    L = ["# B1 erken kesme — sağlamlık (erken_kes_saglamlik.py; ön-kayıt eki dosya başında)"]
    for side in ("BUY", "SELL"):
        D = S[S.direction == side].reset_index(drop=True)
        days = D.day.astype(str).to_numpy()
        base = run_set(D, arr)
        ok = np.isfinite(base)
        L.append(f"\n## {side} n={int(ok.sum())} taban ortR {np.nanmean(base):+.3f}")
        rows = []
        for mn in MINS:
            row = {"dk": mn}
            for th in THS:
                x = run_set(D, arr, cut_min=mn, cut_r=th)
                m = ok & np.isfinite(x)
                row[f"{th:+.1f}"] = (x[m] - base[m]).mean()
            rows.append(row)
        L.append("### (a) plato — fark (aday − taban), R/işlem")
        L.append(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:+.4f}"))
        for lab, kw, mult in (("(b) sonraki açılışta çık", dict(next_open=True), 1.0), ("(c) spread ×1,5", {}, 1.5),
                              ("(b+c) ikisi birden", dict(next_open=True), 1.5)):
            b0 = run_set(D, arr, sp_mult=mult)
            x = run_set(D, arr, sp_mult=mult, cut_min=5, cut_r=-0.5, **kw)
            m = np.isfinite(b0) & np.isfinite(x)
            st = Y.stats(x[m], b0[m], days[m])
            L.append(f"- {lab}: fark {st['fark']:+.4f} P {st['P(fark>0)']:.3f} yarılar {st['yarılar']} (ortR {st['ortR aday']:+.3f} vs {st['ortR taban']:+.3f})")
        if side == "BUY":
            # (e) plasebo: rastgele gün, aynı UTC dakikası
            x0 = run_set(D, arr, cut_min=5, cut_r=-0.5)
            real = np.nanmean(x0 - base)
            idx = b.index
            gains = []
            rng = np.random.default_rng(7)
            for _ in range(N_PLAC):
                sh = rng.integers(-10, 11, len(D))
                sh[sh == 0] = 1
                ts2 = D.ts + pd.to_timedelta(sh, unit="D")
                P = D.assign(ts=ts2)
                bb = run_set(P, arr)
                xx = run_set(P, arr, cut_min=5, cut_r=-0.5)
                g = xx - bb
                gains.append(np.nanmean(g))
            gains = np.array(gains)
            L.append(f"\n### (e) plasebo (rastgele gün, aynı dakika, ×{N_PLAC}): gerçek fark {real:+.4f} · plasebo medyan "
                     f"{np.median(gains):+.4f} · %90 {np.quantile(gains, .9):+.4f} · gerçek > plasebo oranı %{100 * np.mean(gains < real):.0f}")
            # (f) kart
            x = run_set(D, arr, cut_min=5, cut_r=-0.5)
            xn = run_set(D, arr, cut_min=5, cut_r=-0.5, next_open=True)
            m = np.isfinite(x) & np.isfinite(xn)
            h = np.arange(m.sum()) < m.sum() // 2
            xs = x[m]
            ud = np.unique(days[m])
            ix = {u: np.flatnonzero(days[m] == u) for u in ud}
            pe = np.mean([xs[np.concatenate([ix[u] for u in rng.choice(ud, ud.size)])].mean() > 0 for _ in range(2000)])
            L.append("\n### (f) canlıya alma kartı (kural uygulanmış decider XAU BUY, G1)")
            L.append(f"1 hacim n={m.sum()} (≥150) · 2 beklenti ortR {xs.mean():+.3f} P(EV>0) %{100 * pe:.0f} (≥%90) · "
                     f"3 yarılar {xs[h].mean():+.3f}/{xs[~h].mean():+.3f} · 4 spread×1,5 bkz. (c) · 5 icra (sonraki açılış) "
                     f"ortR {xn[m].mean():+.3f} · 6 tek-poz: decider XAU zaten tek pozisyon")
    txt = "\n".join(L)
    (HERE / "results" / "erken_kes_saglamlik.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
