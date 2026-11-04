"""Binance BTCUSDT 1m zip'lerinden temiz parquet + resample (5m..1d).

- Zaman birimi DOSYA BAŞINA tespit edilir (2025-01'den itibaren mikrosaniye).
- Başlık satırı varsa atlanır. Zip içeriği yalnız CSV olarak okunur.
- 1m'de boşluk DOLDURULMAZ (eksik dakika = satır yok). Üst TF'lerde n_1m
  sütunu kovadaki gerçek dakika sayısını taşır (tam kova: 5m→5, 1d→1440).
- Resample: UTC, left-closed + left-label (kova başlangıcı), 1d 00:00 UTC.

Kullanım: python -I 02_build_binance.py <raw_dir> <out_dir>
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
        "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"]
START = pd.Timestamp("2021-06-01", tz="UTC")
TFS = {"5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h", "1d": "1D"}
FULL = {"5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}


def read_zip(path: Path) -> tuple[pd.DataFrame, str]:
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.endswith(".csv")]
        assert len(names) == 1, (path, z.namelist())
        raw = z.read(names[0])
    first = raw.split(b"\n", 1)[0].split(b",")[0]
    header = not first.strip().isdigit()
    df = pd.read_csv(io.BytesIO(raw), header=None, names=COLS, skiprows=1 if header else 0)
    ot = df["open_time"].astype("int64")
    unit = "us" if ot.iloc[0] > 1e15 else "ms"
    assert ((ot > 1e15) == (unit == "us")).all(), f"karışık birim {path}"
    df["ts"] = pd.to_datetime(ot, unit=unit, utc=True)
    df["close_ts"] = pd.to_datetime(df["close_time"].astype("int64"), unit=unit, utc=True)
    return df.drop(columns=["open_time", "close_time", "ignore"]), f"{unit}{' header' if header else ''}"


def resample(m1: pd.DataFrame, rule: str) -> pd.DataFrame:
    g = m1.set_index("ts").resample(rule, label="left", closed="left")
    out = pd.DataFrame({
        "open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
        "close": g["close"].last(), "volume": g["volume"].sum(),
        "quote_volume": g["quote_volume"].sum(), "trades": g["trades"].sum(),
        "taker_buy_base": g["taker_buy_base"].sum(), "n_1m": g["close"].count(),
    })
    out = out[out["n_1m"] > 0].reset_index()
    return out


def main() -> None:
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    files = sorted((raw / "monthly").glob("*.zip")) + sorted((raw / "daily").glob("*.zip"))
    parts, units = [], {}
    for f in files:
        df, u = read_zip(f)
        units[f.name] = u
        parts.append(df)
    m1 = pd.concat(parts, ignore_index=True)
    rep: dict = {"files": len(files), "unit_by_file": units, "rows_raw": len(m1)}
    dup = m1.duplicated("ts", keep=False)
    rep["dup_ts_rows"] = int(dup.sum())
    rep["dup_ts_identical"] = int(m1[dup].duplicated(keep=False).sum())
    m1 = m1.drop_duplicates("ts", keep="last").sort_values("ts").reset_index(drop=True)
    m1 = m1[m1["ts"] >= START].reset_index(drop=True)
    # sanity: close_ts == ts + 59.999s
    dct = (m1["close_ts"] - m1["ts"]).dt.total_seconds()
    rep["close_ts_offset_not_59.999"] = int((~np.isclose(dct, 59.999, atol=0.0015)).sum())
    m1 = m1.drop(columns=["close_ts"])
    for c in ["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_base", "taker_buy_quote"]:
        m1[c] = m1[c].astype("float64")
    m1["trades"] = m1["trades"].astype("int64")
    bad = (m1["high"] < m1[["open", "close"]].max(axis=1)) | (m1["low"] > m1[["open", "close"]].min(axis=1)) | (m1["low"] <= 0)
    rep["ohlc_inconsistent"] = int(bad.sum())
    rep["rows_clean"] = len(m1)
    rep["first_ts"], rep["last_ts"] = str(m1["ts"].iloc[0]), str(m1["ts"].iloc[-1])
    expected = int((m1["ts"].iloc[-1] - m1["ts"].iloc[0]).total_seconds() // 60) + 1
    rep["expected_minutes"] = expected
    rep["missing_minutes"] = expected - len(m1)
    d = m1["ts"].diff().dt.total_seconds().div(60)
    gi = np.where(d > 1)[0]
    gaps = [{"after": str(m1["ts"].iloc[i - 1]), "resume": str(m1["ts"].iloc[i]), "missing_min": int(d.iloc[i] - 1)}
            for i in gi]
    rep["n_gaps"] = len(gaps)
    rep["gaps_ge_5min"] = [g for g in gaps if g["missing_min"] >= 5]
    rep["gaps_lt_5min_count"] = sum(1 for g in gaps if g["missing_min"] < 5)
    rep["zero_volume_bars"] = int((m1["volume"] == 0).sum())
    rep["zero_trade_bars"] = int((m1["trades"] == 0).sum())
    zv = m1.loc[m1["volume"] == 0, "ts"]
    rep["zero_volume_by_year"] = zv.dt.year.value_counts().sort_index().astype(int).to_dict()
    r = np.log(m1["close"]).diff()
    rng = (m1["high"] / m1["low"] - 1) * 100
    rep["abs_ret_1m_gt_2pct"] = [{"ts": str(t), "ret_pct": round(float(x) * 100, 2)}
                                 for t, x in zip(m1["ts"][r.abs() > 0.02], r[r.abs() > 0.02])]
    rep["range_1m_gt_3pct"] = [{"ts": str(t), "range_pct": round(float(x), 2), "low": float(lo), "high": float(hi)}
                               for t, x, lo, hi in zip(m1["ts"][rng > 3], rng[rng > 3], m1["low"][rng > 3], m1["high"][rng > 3])]
    med = m1["close"].rolling(61, center=True, min_periods=10).median()
    wick = ((m1["low"] / med - 1).abs() > 0.05) | ((m1["high"] / med - 1).abs() > 0.05)
    rep["wick_gt5pct_from_rolling_median"] = [{"ts": str(t), "low": float(lo), "high": float(hi), "median": round(float(mm), 2)}
                                              for t, lo, hi, mm in zip(m1["ts"][wick], m1["low"][wick], m1["high"][wick], med[wick])]
    rep["ret_1m_std_pct"] = round(float(r.std() * 100), 4)
    out.mkdir(parents=True, exist_ok=True)
    m1.to_parquet(out / "btc_1m.parquet", index=False)
    rep["resampled"] = {}
    for k, rule in TFS.items():
        df = resample(m1, rule)
        df.to_parquet(out / f"btc_{k}.parquet", index=False)
        rep["resampled"][k] = {"rows": len(df), "first": str(df["ts"].iloc[0]), "last": str(df["ts"].iloc[-1]),
                               "incomplete_buckets": int((df["n_1m"] < FULL[k]).sum())}
    (out / "btc_quality_report.json").write_text(json.dumps(rep, indent=1, default=str))
    short = {k: v for k, v in rep.items() if k not in ("unit_by_file", "gaps_ge_5min", "abs_ret_1m_gt_2pct",
                                                       "range_1m_gt_3pct", "wick_gt5pct_from_rolling_median")}
    print(json.dumps(short, indent=1, default=str))
    print("units:", pd.Series(units).value_counts().to_dict())
    print("gaps>=5min:", len(rep["gaps_ge_5min"]))
    for g in rep["gaps_ge_5min"]:
        print("  ", g)
    print("abs_ret>2%:", rep["abs_ret_1m_gt_2pct"][:30])
    print("range>3%:", len(rep["range_1m_gt_3pct"]), rep["range_1m_gt_3pct"][:20])
    print("wick>5% vs median:", rep["wick_gt5pct_from_rolling_median"][:20])


if __name__ == "__main__":
    main()
