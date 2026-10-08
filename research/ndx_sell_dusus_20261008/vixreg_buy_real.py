"""IO-15 doğrulaması: VIX≥18,4 günlerinde GERÇEK pulse1/pulse2 NDX BUY sinyalleri (VIXREG'in oy kaynağı)
broker 1m'de yeniden oynatılır. python3 research/ndx_sell_dusus_20261008/vixreg_buy_real.py

Çıkışlar: (a) bot 80/110 (b) TP×2 160/110 (c) zaman çıkışı ertesi gün 16:00 ET (SL 110 korunur).
Taban: aynı günlerde 14–19 UTC saat başı BUY (aynı üç çıkış). Bot kapıları vekil: 1h EMA50 üstü (trend),
4s aralık konumu ≤ 0,60 (POSITION_GATE BUY).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.islem_otopsi import data  # noqa: E402
from scripts.islem_otopsi.indicators import SymbolBars  # noqa: E402
from scripts.islem_otopsi.placebo import simulate  # noqa: E402
from scripts.islem_otopsi.stats import boot_mean_ci  # noqa: E402

VIX_T, SPREAD, TP, SL = 18.4, 1.5, 80.0, 110.0
POS_BUY_MAX = 0.60
NY = "America/New_York"


def signals() -> pd.DataFrame:
    rows = data.fetch_table(data.get_client(), "prediction_logs", "created_at,model_type,ml_direction,factors",
                            [("symbol", "eq", "NDX.INDX"), ("ml_direction", "eq", "BUY"),
                             ("created_at", "gte", "2026-06-17"), ("model_type", "in_", ["pulse1", "pulse2"])],
                            "created_at")
    d = pd.DataFrame(rows)
    d["ts"] = pd.to_datetime(d["created_at"], utc=True)
    d["vix"] = d["factors"].map(lambda f: (f or {}).get("macro_vix_price"))
    d["vix"] = pd.to_numeric(d["vix"], errors="coerce")
    return d[d["vix"] >= VIX_T].sort_values("ts").reset_index(drop=True)


def time_exit(sb: SymbolBars, j0: int, entry: float, t0: pd.Timestamp) -> float:
    ny = t0.tz_convert(NY)
    end = (ny.normalize() + pd.Timedelta(days=1, hours=16)).tz_convert("UTC")
    j1 = sb.pos_at(end)
    lo = sb.a["low"][j0:j1]
    if not lo.size:
        return np.nan
    hit = np.flatnonzero(lo <= entry - SL)
    if hit.size:
        return -1.0
    return float((sb.a["close"][min(j1, sb.a["close"].size - 1)] - entry) / SL)


def trade(sb: SymbolBars, t0: pd.Timestamp) -> dict | None:
    j = sb.pos_at(t0) + 1                       # sonraki dakika açılışı
    if j >= sb.a["close"].size - 10:
        return None
    entry = float(sb.a["open"][j]) + SPREAD
    r1, k1, _ = simulate(sb, 1, entry, j, SL, TP, SPREAD)
    r2, _, _ = simulate(sb, 1, entry, j, SL, 2 * TP, SPREAD)
    i = sb.last_closed(1, t0)
    e50 = sb.ta[60]["ema50"][sb.last_closed(60, t0)]
    w = slice(i - 239, i + 1)
    hi, lo = sb.a["high"][w].max(), sb.a["low"][w].min()
    pos = (sb.a["close"][i] - lo) / (hi - lo) if hi > lo else 0.5
    return {"ts": t0, "R_80_110": r1, "R_160_110": r2, "R_zaman": time_exit(sb, j, entry, t0),
            "trend_ok": sb.a["close"][i] > e50, "pos_ok": pos <= POS_BUY_MAX, "end_j": k1 if k1 >= 0 else j + 240}


def independent(sb: SymbolBars, ts: list) -> list[dict]:
    out, busy = [], -1
    for t0 in ts:
        if sb.pos_at(t0) <= busy:
            continue
        r = trade(sb, t0)
        if r:
            out.append(r)
            busy = r["end_j"]
    return out


def show(name: str, df: pd.DataFrame) -> None:
    print(f"\n--- {name}: n={len(df)}")
    for c in ("R_80_110", "R_160_110", "R_zaman"):
        x = df[c].dropna().to_numpy(float)
        if x.size < 3:
            print(f"  {c}: n={x.size}"); continue
        lo, hi, p = boot_mean_ci(x)
        print(f"  {c:10s} ort {x.mean():+.3f}R  WR %{100 * (x > 0).mean():.0f}  %95 [{lo:+.2f}…{hi:+.2f}]  P(>0) {p:.2f}  top {x.sum():+.1f}")


def main() -> None:
    now = data.utc_now()
    raw = data.load_bars_raw("NDX.INDX", pd.Timestamp("2026-06-01", tz="UTC"), now)
    sb = SymbolBars("NDX.INDX", data.normalize_snapshot_clock(raw))
    s = signals()
    print("VIX≥18,4 pulse1/pulse2 BUY kayıt:", len(s), "| günler:", sorted(s.ts.dt.strftime("%m-%d").unique()))
    sig = pd.DataFrame(independent(sb, list(s.ts)))
    show("sinyal (kapısız)", sig)
    show("sinyal + trend kapısı", sig[sig.trend_ok])
    show("sinyal + trend + konum kapısı (bot VIXREG vekili)", sig[sig.trend_ok & sig.pos_ok])
    days = sorted(s.ts.dt.normalize().unique())
    grid = [d + pd.Timedelta(hours=h) for d in days for h in range(14, 20)]
    base = pd.DataFrame(independent(sb, [g for g in grid if g < now - pd.Timedelta(days=1)]))
    show("TABAN: aynı günlerde saat başı BUY", base)
    print("\nişlemler:\n", sig.drop(columns=["end_j"]).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
