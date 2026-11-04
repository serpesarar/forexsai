"""Günlük 1s aggTrades parquet'lerini tek dosyada birleştir + 1m akış özellikleri + kalite.

Çıktılar:
  perp_aggtrades_1s.parquet  (tüm 1s barlar)
  perp_aggflow_1m.parquet    (1s'den 1m: max_agg_qty, large_buy/sell_qty, n_active_sec,
                              max_1s_buy_qty/max_1s_sell_qty, vwap)
  aggtrades_quality_report.json (1m kline ile hacim/taker uzlaşması dahil)
Kullanım: python -I 05_consolidate_aggtrades.py <days_dir> <out_dir>
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd


def main() -> None:
    days, out = Path(sys.argv[1]), Path(sys.argv[2])
    files = sorted(days.glob("*_1s.parquet"))
    s = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True).sort_values("ts").reset_index(drop=True)
    for c in ["open", "high", "low", "close", "vwap", "buy_qty", "sell_qty", "buy_quote", "sell_quote", "max_agg_qty",
              "large_buy_qty", "large_sell_qty"]:
        s[c] = s[c].astype("float32") if c not in ("open", "high", "low", "close", "vwap") else s[c].astype("float64")
    rep = {"day_files": len(files), "rows_1s": len(s), "first": str(s["ts"].iloc[0]), "last": str(s["ts"].iloc[-1]),
           "dup_ts": int(s["ts"].duplicated().sum())}
    gap = s["ts"].diff().dt.total_seconds()
    rep["max_gap_s"] = float(gap.max())
    rep["gaps_gt_60s"] = [{"after": str(s["ts"].iloc[i - 1]), "gap_s": float(gap.iloc[i])} for i in np.where(gap > 60)[0]][:50]
    tot_sec = int((s["ts"].iloc[-1] - s["ts"].iloc[0]).total_seconds()) + 1
    rep["share_seconds_with_trades"] = round(len(s) / tot_sec, 4)
    s.to_parquet(out / "perp_aggtrades_1s.parquet", index=False)
    # 1m
    s["m"] = s["ts"].dt.floor("1min")
    s["quote"] = s["buy_quote"].astype("float64") + s["sell_quote"].astype("float64")
    s["qty"] = s["buy_qty"].astype("float64") + s["sell_qty"].astype("float64")
    g = s.groupby("m")
    m = pd.DataFrame({
        "agg_buy_qty": g["buy_qty"].sum(), "agg_sell_qty": g["sell_qty"].sum(),
        "agg_n_agg": g["n_agg"].sum(), "agg_n_trades": g["n_trades"].sum(),
        "agg_max_agg_qty": g["max_agg_qty"].max(),
        "agg_large_buy_qty": g["large_buy_qty"].sum(), "agg_large_sell_qty": g["large_sell_qty"].sum(),
        "agg_max_1s_buy_qty": g["buy_qty"].max(), "agg_max_1s_sell_qty": g["sell_qty"].max(),
        "agg_n_active_sec": g["ts"].size().astype("int16"),
        "agg_vwap": g["quote"].sum() / g["qty"].sum(),
    }).reset_index().rename(columns={"m": "ts"})
    m.to_parquet(out / "perp_aggflow_1m.parquet", index=False)
    # uzlaşma: kline 1m
    k = pd.read_parquet(out / "perp_1m.parquet", columns=["ts", "volume", "taker_buy_base", "trades"])
    j = m.merge(k, on="ts", how="inner")
    vol = j["agg_buy_qty"] + j["agg_sell_qty"]
    rep["recon_1m_rows"] = len(j)
    rep["recon_volume_rel_err_p50_p99_max"] = [float(x) for x in (vol / j["volume"] - 1).abs().quantile([.5, .99, 1]).round(6)]
    rep["recon_taker_buy_rel_err_p50_p99"] = [float(x) for x in (j["agg_buy_qty"] / j["taker_buy_base"] - 1).abs().quantile([.5, .99]).round(6)]
    rep["recon_trades_equal_share"] = round(float((j["agg_n_trades"] == j["trades"]).mean()), 4)
    rep["rows_1m"] = len(m)
    (out / "aggtrades_quality_report.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps(rep, indent=1, default=str))


if __name__ == "__main__":
    main()
