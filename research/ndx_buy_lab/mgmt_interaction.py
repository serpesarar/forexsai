"""mgmt_interaction.py — yeni geometri ile CANLIDA AÇIK olan işlem yönetimi çelişiyor mu?

Bot şu an NDX BUY'da: BE@30dk (SL→giriş) + TP kaldır + 0.6R iz süren stop
(TRADE_MGMT_ENABLED=1, research/trade_mgmt_ndx/REPORT.md).
Bu yönetim TP=80 puan geometrisi için ölçülmüştü. Hedefi 2×ATR'ye taşırsak
BE@30dk çoğu işlemi hedefe varmadan başabaşta kesebilir → kenar yok olabilir.

Bu dosya dört rejimi AYNI girişler üzerinde 1m çözünürlükte karşılaştırır:
  A) sabit TP/SL (yönetim yok)
  B) BE@30dk + sabit TP
  C) BE@30dk + TP YOK + 0.6R iz süren  (canlıdaki NDX BUY kurulumu)
  D) BE@30dk + TP 2×ATR + 0.6R iz süren (öneri)
Kurallar bar kapanışında; aynı barda TP+SL → SL önce; sürtünme her çıkışta.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA, add_indicators, asof_features, load_bars, resample_from

FRICTION = 1.0
MAX_HOLD = 2880
MODELS = ["pulse1", "pulse2", "pulse3"]


def simulate(bars, ts1m, i0, sl_dist, tp_dist, be_min, trail_r, direction="BUY"):
    """i0 = giriş barı indeksi. tp_dist None → TP yok."""
    sgn = 1.0 if direction == "BUY" else -1.0
    entry = bars[i0, 0] + sgn * FRICTION
    sl_px = entry - sgn * sl_dist
    tp_px = entry + sgn * tp_dist if tp_dist else None
    best = entry
    end = min(len(ts1m), i0 + MAX_HOLD + 2)
    for j in range(i0, end):
        hi, lo, cl = bars[j, 1], bars[j, 2], bars[j, 3]
        hit_sl = (lo <= sl_px) if direction == "BUY" else (hi >= sl_px)
        hit_tp = (tp_px is not None) and ((hi >= tp_px) if direction == "BUY" else (lo <= tp_px))
        if hit_sl:
            pnl = sgn * (sl_px - entry) - FRICTION
            return pnl / sl_dist, j - i0
        if hit_tp:
            pnl = sgn * (tp_px - entry) - FRICTION
            return pnl / sl_dist, j - i0
        # bar KAPANIŞINDA yönetim güncellemesi (sonraki bardan geçerli)
        best = max(best, cl) if direction == "BUY" else min(best, cl)
        held = j - i0
        if be_min and held >= be_min:
            be = entry
            sl_px = max(sl_px, be) if direction == "BUY" else min(sl_px, be)
        if trail_r:
            t = best - sgn * trail_r * sl_dist
            sl_px = max(sl_px, t) if direction == "BUY" else min(sl_px, t)
        if held >= MAX_HOLD:
            pnl = sgn * (cl - entry) - FRICTION
            return pnl / sl_dist, held
    return None, None


def main() -> None:
    b1 = load_bars("1m")
    ts1m = b1["ts"].values
    arr = b1[["open", "high", "low", "close"]].to_numpy()
    h1 = resample_from(b1, "1h")
    af = add_indicators(h1, "H1")[["known_at", "H1_atr", "H1_adx", "H1_di_diff"]]

    s = pd.read_csv(DATA / "signals.csv")
    s["ts"] = pd.to_datetime(s["created_at"], utc=True, format="mixed")
    s = s[s.model_type.isin(MODELS) & (s.ml_direction == "BUY")]
    s = s[(s.ts >= b1.ts.min()) & (s.ts <= b1.ts.max() - pd.Timedelta(days=3))]
    s = s[["id", "ts"]].sort_values("ts")
    s = asof_features(s, af.assign(ts=af["known_at"])).drop(columns=["known_at"])
    s = s[np.isfinite(s.H1_atr) & (s.H1_atr > 0)]

    CFG = [
        ("A0 bot bugün: TP80/SL110, yönetim YOK", 110.0, 80.0, 0, 0.0),
        ("A1 bot bugün + BE30 + 0.6R iz (CANLI)", 110.0, None, 30, 0.6),
        ("B0 SL=1ATR, TP=2ATR, yönetim yok", None, 2.0, 0, 0.0),
        ("B1 SL=1ATR, TP=2ATR + BE30 + 0.6R iz", None, 2.0, 30, 0.6),
        ("B2 SL=1ATR, TP YOK + BE30 + 0.6R iz", None, None, 30, 0.6),
        ("B3 SL=1ATR, TP=3ATR + BE60 + 0.6R iz", None, 3.0, 60, 0.6),
        ("B4 SL=1ATR, TP=2ATR + BE YOK + 0.6R iz", None, 2.0, 0, 0.6),
    ]
    print(f"{len(s)} NDX BUY sinyali (ham) — epizod kuralı her konfigde ayrı uygulanır\n")
    rows = []
    for label, sl_fix, tp_mult, be_min, trail in CFG:
        recs, open_until = [], None
        for r in s.itertuples(index=False):
            if open_until is not None and r.ts < open_until:
                continue
            i0 = int(np.searchsorted(ts1m, np.datetime64(r.ts), side="right"))
            if i0 >= len(ts1m):
                continue
            sl_d = sl_fix if sl_fix else 1.0 * r.H1_atr
            tp_d = (80.0 if sl_fix and tp_mult == 80.0 else
                    (tp_mult * r.H1_atr if (tp_mult and tp_mult < 10) else tp_mult))
            rr, held = simulate(arr, ts1m, i0, sl_d, tp_d, be_min, trail)
            if rr is None:
                continue
            open_until = b1["ts"].iloc[min(i0 + held, len(b1) - 1)]
            recs.append(dict(ts=r.ts, r=rr, held=held,
                             k1=not (r.H1_adx > 25 and r.H1_di_diff < 0)))
        d = pd.DataFrame(recs)
        k = d[d.k1]
        rows.append(dict(konfig=label, n=len(d), WR=round((d.r > 0).mean(), 3),
                         EV=round(d.r.mean(), 4), toplamR=round(d.r.sum(), 1),
                         medyan_dk=int(d.held.median()),
                         n_K1=len(k), EV_K1=round(k.r.mean(), 4),
                         toplamR_K1=round(k.r.sum(), 1)))
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nNot: 'K1' = H1 güçlü ayı trendi DEĞİL kapısı (H1_adx>25 & -DI>+DI olanlar elenir).")


if __name__ == "__main__":
    main()
