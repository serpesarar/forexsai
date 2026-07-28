"""geometry_sweep.py — TP/SL geometrisi taraması (3.4 yıl, vektörize, sızıntısız).

Neden bu soru: botun NDX geometrisi TP=80 / SL=110 puan → RR 0.727 → BAŞABAŞ
kazanma oranı %58.4. 3.4 yıllık ölçüm: NDX long'un koşulsuz kazanma oranı %57.6.
Yani strateji yapısal olarak çizginin ~1 puan ALTINDA. Hiçbir filtre bulunamadıysa
sebep filtrelerin kötülüğü değil, HEDEFİN çok uzak / STOP'un çok yakın olması
olabilir. Bu dosya onu ölçer: hangi (TP, SL) bölgesinde NDX long +EV?

Yöntem: her karar noktası için gelecek 96 barın (24 saat) high/low yolu bir kez
çıkarılır; tüm geometriler AYNI yol üzerinde değerlendirilir (adil kıyas).
Aynı barda TP+SL → SL önce (konservatif, her geometride aynı).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA

HORIZON = 96          # 96 × 15m = 24 saat piyasa zamanı
FRIC = 1.0 / 29000    # bugünkü 1 puanlık sürtünmenin oransal karşılığı


def build_paths(d15: pd.DataFrame, horizon: int = HORIZON):
    """Her i için giriş = i. barın açılışı; yol = i..i+horizon-1 high/low."""
    o = d15["open"].to_numpy()
    h = d15["high"].to_numpy()
    l = d15["low"].to_numpy()
    c = d15["close"].to_numpy()
    n = len(d15) - horizon - 1
    idx = np.arange(n)[:, None] + np.arange(horizon)[None, :]
    fh = h[idx]
    fl = l[idx]
    entry = o[:n]
    up = fh / entry[:, None] - 1.0          # oransal lehte hareket (long)
    dn = fl / entry[:, None] - 1.0
    end_ret = c[idx[:, -1]] / entry - 1.0   # ufuk sonundaki GERÇEK kapanış getirisi
    return (entry, np.maximum.accumulate(up, axis=1),
            np.minimum.accumulate(dn, axis=1), end_ret)


def outcomes(cummax_up, cummin_dn, tp: np.ndarray, sl: np.ndarray, direction="BUY"):
    """tp/sl satır başına ORANSAL mesafe (pozitif sayı). SL-önce konservatif."""
    if direction == "BUY":
        hit_tp = cummax_up >= tp[:, None]
        hit_sl = cummin_dn <= -sl[:, None]
    else:
        hit_tp = cummin_dn <= -tp[:, None]
        hit_sl = cummax_up >= sl[:, None]
    any_tp, any_sl = hit_tp.any(1), hit_sl.any(1)
    t_tp = np.where(any_tp, hit_tp.argmax(1), 10**6)
    t_sl = np.where(any_sl, hit_sl.argmax(1), 10**6)
    win = any_tp & (t_tp < t_sl)            # eşitlikte SL kazanır (konservatif)
    loss = any_sl & (t_sl <= t_tp)
    open_end = ~win & ~loss
    return win, loss, open_end, np.minimum(t_tp, t_sl)


def sweep(direction: str = "BUY") -> pd.DataFrame:
    d15 = pd.read_csv(DATA / "long_15m.csv", parse_dates=["ts"])
    d15["ts"] = pd.to_datetime(d15["ts"], utc=True)
    d15 = d15.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)

    # H1 ATR (yüzde) — karar anında bilinen (kapanmış barlardan, shift'li)
    h1 = (d15.set_index("ts").resample("1h", label="left", closed="left")
          .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
          .dropna())
    pc = h1["close"].shift(1)
    tr = pd.concat([h1.high - h1.low, (h1.high - pc).abs(), (h1.low - pc).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    atr_pct = (atr / h1["close"]).rename("atr_pct").reset_index()
    atr_pct["known_at"] = atr_pct["ts"] + pd.Timedelta(hours=1)
    m = pd.merge_asof(d15[["ts"]].sort_values("ts"),
                      atr_pct[["known_at", "atr_pct"]].sort_values("known_at"),
                      left_on="ts", right_on="known_at", direction="backward")
    d15["atr_pct"] = m["atr_pct"].to_numpy()

    entry, cmax, cmin, end_ret = build_paths(d15)
    n = len(entry)
    a = d15["atr_pct"].to_numpy()[:n]
    ts = d15["ts"].to_numpy()[:n]
    ok = np.isfinite(a) & (a > 0)
    year = pd.DatetimeIndex(ts).year

    rows = []
    # (A) ATR-ölçekli geometriler
    for tp_a in (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0):
        for sl_a in (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0):
            tp = a * tp_a
            sl = a * sl_a
            win, loss, opn, _ = outcomes(cmax, cmin, tp, sl, direction)
            r = np.where(win, (tp - FRIC) / sl, np.where(loss, -(sl + FRIC) / sl, 0.0))
            # açık kalanlar 24 saat sonunda piyasadan kapatılır (GERÇEK kapanış)
            sgn = 1.0 if direction == "BUY" else -1.0
            r = np.where(opn, (sgn * end_ret - FRIC) / sl, r)
            sel = ok
            rows.append(dict(tip="ATR", tp=tp_a, sl=sl_a, rr=round(tp_a / sl_a, 2),
                             n=int(sel.sum()), wr=float(win[sel].mean()),
                             ev=float(r[sel].mean()), acik=float(opn[sel].mean()),
                             **{f"ev{y}": float(r[sel & (year == y)].mean())
                                for y in (2023, 2024, 2025, 2026)}))
    # (B) sabit yüzdeler (botun bugünkü geometrisi = tp %0.276 / sl %0.379)
    for tp_p in (0.15, 0.2, 0.276, 0.35, 0.45, 0.6, 0.8):
        for sl_p in (0.2, 0.276, 0.379, 0.5, 0.65, 0.85):
            tp = np.full(n, tp_p / 100)
            sl = np.full(n, sl_p / 100)
            win, loss, opn, _ = outcomes(cmax, cmin, tp, sl, direction)
            r = np.where(win, (tp - FRIC) / sl, np.where(loss, -(sl + FRIC) / sl, 0.0))
            sgn = 1.0 if direction == "BUY" else -1.0
            r = np.where(opn, (sgn * end_ret - FRIC) / sl, r)
            rows.append(dict(tip="PCT", tp=tp_p, sl=sl_p, rr=round(tp_p / sl_p, 2),
                             n=n, wr=float(win.mean()), ev=float(r.mean()),
                             acik=float(opn.mean()),
                             **{f"ev{y}": float(r[year == y].mean())
                                for y in (2023, 2024, 2025, 2026)}))
    return pd.DataFrame(rows)


def main() -> None:
    pd.set_option("display.width", 220)
    for direction in ("BUY", "SELL"):
        df = sweep(direction)
        df["tum_yillar_poz"] = (df[["ev2023", "ev2024", "ev2025", "ev2026"]] > 0).sum(1)
        df.to_csv(DATA / f"geometry_{direction}.csv", index=False)
        print(f"\n══════ {direction} — en iyi 18 geometri (EV'ye göre) ══════")
        print(df.sort_values("ev", ascending=False).head(18).round(4).to_string(index=False))
        print(f"\n── {direction}: 4 yılın 4'ünde de +EV olanlar ──")
        s = df[df.tum_yillar_poz == 4].sort_values("ev", ascending=False)
        print(s.round(4).to_string(index=False) if len(s) else "  YOK")
        cur = df[(df.tip == "PCT") & (df.tp == 0.276) & (df.sl == 0.379)]
        print(f"\n── {direction}: botun BUGÜNKÜ geometrisi (tp %0.276 / sl %0.379) ──")
        print(cur.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
