"""USDT-M BTCUSDT günlük metrics (5 dk) → metrics_5m.parquet + kalite + zaman-damgası hizalama testi.

create_time: 'YYYY-mm-dd HH:MM:SS' (UTC varsayımı, ızgarayla doğrulanır). Satırlar dosya
içinde SIRASIZ olabilir → sıralanır. Hizalama testi: sum_taker_long_short_vol_ratio
(taker alış/satış hacim oranı) ile perp 1m klines'tan hesaplanan oran, T damgalı satır
için [T-5dk, T) ve [T, T+5dk) pencerelerinde karşılaştırılır; hangisi eşleşirse
damga o pencerenin SONU/BAŞI'dır.
Kullanım: python -I 04_build_metrics.py <raw_dir> <out_dir>
"""
from __future__ import annotations
import io, json, sys, zipfile
from pathlib import Path

import numpy as np
import pandas as pd

COLS = ["create_time", "symbol", "sum_open_interest", "sum_open_interest_value", "count_toptrader_long_short_ratio",
        "sum_toptrader_long_short_ratio", "count_long_short_ratio", "sum_taker_long_short_vol_ratio"]


def main() -> None:
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    parts, hdr_files, bad = [], 0, []
    for f in sorted((raw / "um_metrics").glob("*.zip")):
        with zipfile.ZipFile(f) as z:
            n = [x for x in z.namelist() if x.endswith(".csv")]
            b = z.read(n[0])
        h = not b[:2].isdigit()
        hdr_files += h
        df = pd.read_csv(io.BytesIO(b), header=None, names=COLS, skiprows=1 if h else 0)
        if len(df) == 0:
            bad.append(f.name)
        df["_file"] = f.name[-14:-4]
        parts.append(df)
    m = pd.concat(parts, ignore_index=True)
    rep: dict = {"files": len(parts), "header_files": hdr_files, "empty_files": bad, "rows_raw": len(m)}
    m["ts"] = pd.to_datetime(m["create_time"], utc=True)
    rep["symbol_values"] = m["symbol"].value_counts().to_dict()
    rep["rows_not_in_file_date"] = int((m["ts"].dt.strftime("%Y-%m-%d") != m["_file"]).sum())
    rep["off_5m_grid"] = int((m["ts"] != m["ts"].dt.floor("5min")).sum())
    dup = m.duplicated("ts", keep=False)
    rep["dup_ts_rows"] = int(dup.sum())
    m = m.drop_duplicates("ts", keep="last").sort_values("ts").reset_index(drop=True)
    for c in COLS[2:]:
        m[c] = pd.to_numeric(m[c], errors="coerce").astype("float64")
    rep["nan_by_col"] = m[COLS[2:]].isna().sum().to_dict()
    rep["zero_by_col"] = (m[COLS[2:]] == 0).sum().to_dict()
    grid = pd.date_range(m["ts"].iloc[0], m["ts"].iloc[-1], freq="5min")
    rep["rows"], rep["first"], rep["last"], rep["expected_5m"] = len(m), str(m["ts"].iloc[0]), str(m["ts"].iloc[-1]), len(grid)
    miss = grid.difference(m["ts"])
    rep["missing_5m"] = len(miss)
    per_day = pd.Series(1, index=miss).resample("D").sum()
    rep["missing_by_year"] = pd.Series(1, index=miss).groupby(miss.year).sum().to_dict()
    rep["days_missing_ge_12"] = {str(k.date()): int(v) for k, v in per_day[per_day >= 12].items()}
    d = m["ts"].diff().dt.total_seconds().div(60)
    rep["gaps_ge_60min"] = [{"after": str(m["ts"].iloc[i - 1]), "resume": str(m["ts"].iloc[i])}
                            for i in np.where(d >= 60)[0]]
    # --- hizalama testi ---
    k = pd.read_parquet(out / "perp_1m.parquet", columns=["ts", "volume", "taker_buy_base"]).set_index("ts")
    k["sell"] = k["volume"] - k["taker_buy_base"]
    r5 = k.resample("5min", label="left", closed="left")[["taker_buy_base", "sell"]].sum()
    ratio_start = (r5["taker_buy_base"] / r5["sell"])  # index = pencere başı
    t = m.set_index("ts")["sum_taker_long_short_vol_ratio"]
    res = {}
    for lag in [-15, -10, -5, 0, 5, 10]:
        # lag=-5: T damgası [T-5, T) penceresi (damga = pencere SONU)
        cand = ratio_start.reindex(t.index + pd.Timedelta(minutes=lag))
        x = pd.DataFrame({"m": t.values, "k": cand.values}).replace([np.inf, -np.inf], np.nan).dropna()
        lr = np.log(x[(x > 0).all(axis=1)])
        res[f"window_start=T{lag:+d}m"] = {"n": len(lr), "corr_log": round(float(lr["m"].corr(lr["k"])), 4),
                                         "median_abs_rel_err": round(float((x["m"] / x["k"] - 1).abs().median()), 5)}
    rep["timestamp_alignment_test_taker_ratio"] = res
    # OI hizalama: OI değişimi ile perp fiyat değişimi yerine – yalnız taker oranı yeterli
    m = m.drop(columns=["create_time", "symbol", "_file"])
    m.to_parquet(out / "metrics_5m.parquet", index=False)
    (out / "metrics_quality_report.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps({kk: v for kk, v in rep.items() if kk not in ("gaps_ge_60min",)}, indent=1, default=str))
    print("gaps>=60m:", len(rep["gaps_ge_60min"]), rep["gaps_ge_60min"][:40])


if __name__ == "__main__":
    main()
