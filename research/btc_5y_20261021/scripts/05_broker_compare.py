"""Kutudan gelen BTCUSD M1 dökümlerini çöz + Binance BTCUSDT 1m ile kıyasla.

1. data/broker/box_dump_*.txt → broker_btcusd_m1.parquet (ts_server, ts_utc,
   bid OHLC, spread_pts, spread_usd, tick_volume). MT5 barları BID fiyatıdır.
2. Sunucu saati ofseti: aday ofsetler (−6..+6 saat, 1 dk adım çevresi) için
   1m log getiri korelasyonu; en yüksek korelasyon = ofset.
3. Baz farkı (broker mid − Binance close), getiri korelasyonu, eksik dakika
   deseni (sunucu saatine göre), hafta sonu kapsaması, open−önceki close.

Kullanım: python -I 05_broker_compare.py <data_dir>
"""
from __future__ import annotations

import base64
import json
import lzma
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

POINT = 0.01


def decode(path: Path) -> pd.DataFrame | None:
    txt = path.read_text(errors="replace")
    if "DUMP_BEGIN" not in txt:
        return None
    body = txt.split("DUMP_BEGIN", 1)[1].split("DUMP_END", 1)[0]
    b64 = "".join(re.findall(r"[A-Za-z0-9+/=]+", body))
    a = np.frombuffer(lzma.decompress(base64.b64decode(b64)), dtype=np.int64)
    a = a.reshape(7, -1)
    t = np.cumsum(a[0])
    o, h, l, c = (np.cumsum(a[i]) / 100.0 for i in range(1, 5))
    return pd.DataFrame({"ts_server": pd.to_datetime(t, unit="s", utc=True), "open": o, "high": h,
                         "low": l, "close": c, "spread_pts": a[5], "tick_volume": a[6]})


def main() -> None:
    d = Path(sys.argv[1])
    parts = [x for x in (decode(p) for p in sorted((d / "broker").glob("box_dump_*.txt"))) if x is not None]
    b = pd.concat(parts).drop_duplicates("ts_server").sort_values("ts_server").reset_index(drop=True)
    b["spread_usd"] = b["spread_pts"] * POINT
    rep: dict = {"broker_rows": len(b), "server_first": str(b.ts_server.iloc[0]), "server_last": str(b.ts_server.iloc[-1])}

    m1 = pd.read_parquet(d / "btc_1m.parquet", columns=["ts", "open", "close", "volume"])
    m1 = m1[m1.ts >= b.ts_server.min() - pd.Timedelta(days=1)].set_index("ts")
    br = b.set_index("ts_server")
    lr_b = np.log(br["close"]).diff()
    lr_n = np.log(m1["close"]).diff()
    scores = {}
    for off_min in range(-6 * 60, 6 * 60 + 1, 30):
        s = lr_b.copy(); s.index = s.index - pd.Timedelta(minutes=off_min)
        j = pd.concat([s.rename("b"), lr_n.rename("n")], axis=1, join="inner").dropna()
        scores[off_min] = float(j["b"].corr(j["n"]))
    best = max(scores, key=scores.get)
    fine = {}
    for off_min in range(best - 5, best + 6):
        s = lr_b.copy(); s.index = s.index - pd.Timedelta(minutes=off_min)
        j = pd.concat([s.rename("b"), lr_n.rename("n")], axis=1, join="inner").dropna()
        fine[off_min] = float(j["b"].corr(j["n"]))
    best = max(fine, key=fine.get)
    rep["offset_corr_by_hour"] = {f"{k/60:+.1f}h": round(v, 3) for k, v in scores.items() if k % 60 == 0}
    rep["offset_fine_min"] = {k: round(v, 4) for k, v in fine.items()}
    rep["server_offset_minutes"] = best
    b["ts_utc"] = b["ts_server"] - pd.Timedelta(minutes=best)

    j = b.set_index("ts_utc").join(m1, rsuffix="_bn", how="inner")
    j["mid_close"] = j["close"] + j["spread_usd"] / 2
    basis = j["mid_close"] - j["close_bn"]
    rep["overlap_rows"] = len(j)
    rep["basis_usd"] = {"median": round(float(basis.median()), 2), "mean": round(float(basis.mean()), 2),
                        "p05": round(float(basis.quantile(.05)), 2), "p95": round(float(basis.quantile(.95)), 2),
                        "median_pct": round(float((basis / j["close_bn"]).median() * 100), 4)}
    rep["basis_daily_median_usd"] = {str(k.date()): round(float(v), 2)
                                     for k, v in basis.groupby(basis.index.floor("D")).median().items()}
    rb = np.log(j["close"]).diff(); rn = np.log(j["close_bn"]).diff()
    ok = (j.index.to_series().diff() == pd.Timedelta(minutes=1))
    rep["ret_corr_1m"] = round(float(rb[ok].corr(rn[ok])), 4)
    for k in (5, 15, 60):
        jb = j["close"].resample(f"{k}min").last(); jn = j["close_bn"].resample(f"{k}min").last()
        rep[f"ret_corr_{k}m"] = round(float(np.log(jb).diff().corr(np.log(jn).diff())), 4)
    rep["ret_std_ratio_broker_over_binance_1m"] = round(float(rb[ok].std() / rn[ok].std()), 3)
    # eksik dakika deseni
    full = pd.date_range(b.ts_server.iloc[0], b.ts_server.iloc[-1], freq="1min")
    miss = full.difference(pd.DatetimeIndex(b.ts_server))
    rep["broker_missing_minutes"] = len(miss)
    rep["missing_by_server_hhmm_top"] = pd.Series(miss.strftime("%a %H:%M")).value_counts().head(25).to_dict()
    rep["missing_by_server_hhmm_nodow_top"] = pd.Series(miss.strftime("%H:%M")).value_counts().head(15).to_dict()
    bn_full = m1.loc[b.ts_utc.min():b.ts_utc.max()]
    rep["binance_minutes_in_window"] = len(bn_full)
    wk = b.ts_utc.dt.dayofweek >= 5
    rep["broker_weekend_bars"] = int(wk.sum())
    rep["broker_bars_per_utc_day"] = {str(k): int(v) for k, v in b.groupby(b.ts_utc.dt.date).size().items()}
    gapo = (b["open"] - b["close"].shift()).where(b.ts_server.diff() == pd.Timedelta(minutes=1))
    rep["open_minus_prevclose_usd"] = {"median_abs": round(float(gapo.abs().median()), 2),
                                       "p90_abs": round(float(gapo.abs().quantile(.9)), 2),
                                       "p99_abs": round(float(gapo.abs().quantile(.99)), 2)}
    rep["spread_usd_overlap"] = {"median": float(b.spread_usd.median()), "p90": float(b.spread_usd.quantile(.9)),
                                 "p99": float(b.spread_usd.quantile(.99)), "max": float(b.spread_usd.max())}
    hr = b.groupby(b.ts_utc.dt.hour)["spread_usd"]
    rep["spread_usd_by_utc_hour_mean_p90"] = {int(h): [round(float(g.mean()), 2), round(float(g.quantile(.9)), 2),
                                                        round(float(g.quantile(.99)), 2)] for h, g in hr}
    # broker hacmi vs binance hacmi korelasyonu (saatlik)
    hv = pd.concat([j["tick_volume"].resample("1h").sum(), j["volume"].resample("1h").sum()], axis=1).dropna()
    rep["hourly_tickvol_vs_binance_vol_corr"] = round(float(hv.iloc[:, 0].corr(hv.iloc[:, 1])), 3)
    out = b[["ts_utc", "ts_server", "open", "high", "low", "close", "spread_pts", "spread_usd", "tick_volume"]]
    out.to_parquet(d / "broker_btcusd_m1.parquet", index=False)
    (d / "broker_compare_report.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps(rep, indent=1, default=str))


if __name__ == "__main__":
    main()
