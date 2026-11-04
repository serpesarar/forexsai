"""USDT-M perp BTCUSDT: 1m klines + premium/mark/index 1m + funding → temiz parquet.

Zaman birimi DOSYA BAŞINA tespit (ms/µs), başlık satırı varsa atlanır. 1m'de
boşluk doldurulmaz. ts = bar AÇILIŞI (UTC), bar [ts, ts+60s).
Kullanım: python -I 02_build_futures.py <raw_dir> <out_dir>
"""
from __future__ import annotations
import io, json, sys, zipfile
from pathlib import Path

import numpy as np
import pandas as pd

KCOLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "trades",
         "taker_buy_base", "taker_buy_quote", "ignore"]
START = pd.Timestamp("2021-06-01", tz="UTC")
END = pd.Timestamp("2026-10-21", tz="UTC")


def read_csv_zip(path: Path, names: list[str]) -> tuple[pd.DataFrame, bool]:
    with zipfile.ZipFile(path) as z:
        n = [x for x in z.namelist() if x.endswith(".csv")]
        assert len(n) == 1, (path, z.namelist())
        b = z.read(n[0])
    header = not b[:1].isdigit()
    return pd.read_csv(io.BytesIO(b), header=None, names=names, skiprows=1 if header else 0), header


def to_ts(s: pd.Series, path: Path) -> tuple[pd.Series, str]:
    s = s.astype("int64")
    unit = "us" if s.iloc[0] > 1e15 else "ms"
    assert ((s > 1e15) == (unit == "us")).all(), f"karışık birim {path}"
    return pd.to_datetime(s, unit=unit, utc=True), unit


def build_klines(d: Path) -> tuple[pd.DataFrame, dict]:
    files = sorted(d.glob("*-1m-????-??.zip")) + sorted(d.glob("*-1m-????-??-??.zip"))
    parts, units = [], {}
    for f in files:
        df, hdr = read_csv_zip(f, KCOLS)
        df["ts"], u = to_ts(df["open_time"], f)
        ct, _ = to_ts(df["close_time"], f)
        df["_dct"] = (ct - df["ts"]).dt.total_seconds()
        units[f.name] = u + (" header" if hdr else "")
        parts.append(df.drop(columns=["open_time", "close_time", "ignore"]))
    m = pd.concat(parts, ignore_index=True)
    rep = {"files": len(files), "units": pd.Series(units).value_counts().to_dict(), "rows_raw": len(m)}
    dup = m.duplicated("ts", keep=False)
    rep["dup_ts_rows"] = int(dup.sum())
    rep["dup_ts_nonidentical"] = int(dup.sum() - m[dup].drop(columns="_dct").duplicated(keep=False).sum())
    m = m.drop_duplicates("ts", keep="last").sort_values("ts")
    m = m[(m["ts"] >= START) & (m["ts"] < END)].reset_index(drop=True)
    rep["close_ts_offset_not_59.999"] = int((~np.isclose(m["_dct"], 59.999, atol=0.0015)).sum())
    m = m.drop(columns="_dct")
    for c in m.columns:
        if c not in ("ts", "trades"):
            m[c] = m[c].astype("float64")
    m["trades"] = m["trades"].astype("int64")
    rep["rows"] = len(m)
    rep["first"], rep["last"] = str(m["ts"].iloc[0]), str(m["ts"].iloc[-1])
    exp = int((m["ts"].iloc[-1] - m["ts"].iloc[0]).total_seconds() // 60) + 1
    rep["missing_minutes"] = exp - len(m)
    dd = m["ts"].diff().dt.total_seconds().div(60)
    gi = np.where(dd > 1)[0]
    rep["gaps"] = [{"after": str(m["ts"].iloc[i - 1]), "resume": str(m["ts"].iloc[i]), "missing_min": int(dd.iloc[i] - 1)} for i in gi]
    return m, rep


def main() -> None:
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    rep: dict = {}
    k, r = build_klines(raw / "um_klines")
    bad = (k["high"] < k[["open", "close"]].max(axis=1)) | (k["low"] > k[["open", "close"]].min(axis=1)) | (k["low"] <= 0)
    r["ohlc_inconsistent"] = int(bad.sum())
    r["zero_volume_bars"] = int((k["volume"] == 0).sum())
    r["taker_buy_gt_volume"] = int((k["taker_buy_base"] > k["volume"] + 1e-9).sum())
    k.to_parquet(out / "perp_1m.parquet", index=False)
    rep["perp_1m"] = r
    for name, fn in [("um_premium", "premium_1m"), ("um_mark", "mark_1m"), ("um_index", "index_1m")]:
        df, r = build_klines(raw / name)
        r["count_values"] = df["trades"].value_counts().head(5).to_dict()
        r["volume_nonzero"] = int((df["volume"] != 0).sum())
        df = df[["ts", "open", "high", "low", "close", "trades"]].rename(columns={"trades": "n_samples"})
        df.to_parquet(out / f"{fn}.parquet", index=False)
        rep[fn] = r
    # funding
    parts = []
    for f in sorted((raw / "um_funding").glob("*.zip")):
        df, hdr = read_csv_zip(f, ["calc_time", "funding_interval_hours", "last_funding_rate"])
        df["funding_time"], u = to_ts(df["calc_time"], f)
        parts.append(df)
    fu = pd.concat(parts, ignore_index=True).drop_duplicates("calc_time").sort_values("funding_time")
    fu = fu[fu["funding_time"] >= START].reset_index(drop=True)
    fu["funding_time_nominal"] = fu["funding_time"].dt.round("h")
    fu = fu.rename(columns={"last_funding_rate": "rate", "funding_interval_hours": "interval_h"})[
        ["funding_time", "funding_time_nominal", "interval_h", "rate"]]
    fu["rate"] = fu["rate"].astype("float64")
    fu.to_parquet(out / "funding.parquet", index=False)
    step = fu["funding_time_nominal"].diff().dt.total_seconds().div(3600)
    rep["funding"] = {"rows": len(fu), "first": str(fu["funding_time"].iloc[0]), "last": str(fu["funding_time"].iloc[-1]),
                      "interval_h_values": fu["interval_h"].value_counts().to_dict(),
                      "step_h_values": step.value_counts().to_dict(),
                      "calc_offset_ms_max": float((fu["funding_time"] - fu["funding_time_nominal"]).dt.total_seconds().abs().max() * 1000),
                      "rate_stats": fu["rate"].describe().to_dict(),
                      "nominal_hours": fu["funding_time_nominal"].dt.hour.value_counts().to_dict()}
    (out / "futures_quality_report.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "gaps"} | {"n_gaps": len(v.get("gaps", []))} for k, v in rep.items()}, indent=1, default=str))
    for k_, v in rep.items():
        for g in v.get("gaps", [])[:15]:
            print(k_, g)


if __name__ == "__main__":
    main()
