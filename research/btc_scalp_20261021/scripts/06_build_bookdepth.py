"""USDT-M BTCUSDT bookDepth (günlük, ~30 sn anlık görüntü) → geniş anlık tablo + 1m dengesizlik serisi.

Ham satır: timestamp ('YYYY-mm-dd HH:MM:SS', UTC varsayımı), percentage (−5..+5; 2023 başında
±1..±5, sonra ±0.2 de eklendi), depth (BTC, KÜMÜLATİF: mid'den o yüzdeye kadar), notional (USDT).
Negatif yüzde = alış (bid) tarafı, pozitif = satış (ask) tarafı.

Çıktılar:
  bookdepth_snap.parquet: ts (anlık görüntü zamanı), bid_n_{p}/ask_n_{p} (USDT notional, kümülatif)
  bookdepth_1m.parquet: ts (1m bar açılışı) için bar KAPANIŞINDAN önceki son anlık görüntü
    (snap_ts ∈ [ts, ts+60s)); imb_{p} = (bid−ask)/(bid+ask); n_snaps; snap_age_s (bar kapanışına göre).
Kullanım: python -I 06_build_bookdepth.py <raw_dir> <out_dir>
"""
from __future__ import annotations
import io, json, sys, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

LEVELS = {0.2: "0p2", 1.0: "1", 2.0: "2", 3.0: "3", 4.0: "4", 5.0: "5"}


def main() -> None:
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    snaps, rep = [], {"files": 0, "levels_first_seen": {}, "noncumulative_snaps": 0, "odd_level_rows": 0}
    for f in sorted((raw / "um_bookdepth").glob("*.zip")):
        with zipfile.ZipFile(f) as z:
            n = [x for x in z.namelist() if x.endswith(".csv")]
            b = z.read(n[0])
        df = pd.read_csv(io.BytesIO(b))
        rep["files"] += 1
        df["percentage"] = df["percentage"].astype(float)
        odd = ~df["percentage"].abs().round(2).isin(list(LEVELS))
        rep["odd_level_rows"] += int(odd.sum())
        df = df[~odd]
        for p in df["percentage"].abs().unique():
            rep["levels_first_seen"].setdefault(str(p), f.name[-14:-4])
        df["side"] = np.where(df["percentage"] < 0, "bid_n_", "ask_n_")
        df["col"] = df["side"] + df["percentage"].abs().round(2).map(LEVELS)
        w = df.pivot_table(index="timestamp", columns="col", values="notional", aggfunc="last")
        snaps.append(w)
    s = pd.concat(snaps)
    s.index = pd.to_datetime(s.index, utc=True)
    s = s[~s.index.duplicated(keep="last")].sort_index()
    s.index.name = "ts"
    cols = [f"{sd}{v}" for sd in ("bid_n_", "ask_n_") for v in LEVELS.values()]
    s = s.reindex(columns=cols).astype("float64")
    # kümülatiflik kontrolü (1..5)
    for sd in ("bid_n_", "ask_n_"):
        a = s[[f"{sd}{v}" for v in ["1", "2", "3", "4", "5"]]].to_numpy()
        rep["noncumulative_snaps"] += int((np.diff(a, axis=1) < -1e-6).any(axis=1).sum())
    dt = s.index.to_series().diff().dt.total_seconds()
    rep.update({"snap_rows": len(s), "first": str(s.index[0]), "last": str(s.index[-1]),
                "snap_interval_s_p50_p90_p99": [float(x) for x in dt.quantile([.5, .9, .99])],
                "gaps_gt_10min": [{"after": str(s.index[i - 1]), "resume": str(s.index[i]), "gap_min": round(float(dt.iloc[i]) / 60, 1)}
                                  for i in np.where(dt > 600)[0]],
                "nan_share_by_col": s.isna().mean().round(4).to_dict()})
    s.reset_index().to_parquet(out / "bookdepth_snap.parquet", index=False)
    # 1m: bar içindeki son anlık görüntü
    t = s.copy()
    t["snap_ts"] = t.index
    t["m"] = t.index.floor("1min")
    g = t.groupby("m")
    last = g.last()
    last["n_snaps"] = g.size()
    last["snap_age_s"] = ((last.index + pd.Timedelta(minutes=1)) - last["snap_ts"]).dt.total_seconds()
    for v in LEVELS.values():
        b_, a_ = last[f"bid_n_{v}"], last[f"ask_n_{v}"]
        last[f"imb_{v}"] = (b_ - a_) / (b_ + a_)
    # Şüpheli anlık görüntü: bir tarafta %1→%2 arasında HİÇ likidite yok (kümülatif düz) ya da
    # |imb_1|>0.95. BTC perp'te gerçekçi değil; referans fiyatın bayat/kaymış olduğuna işaret
    # (2025-10-11..14 ve 2026-09-04..06 gün boyu sürüyor). Kullanıcı bu satırları dışlamalı.
    flat = (last["bid_n_1"] >= last["bid_n_2"] - 1e-6) | (last["ask_n_1"] >= last["ask_n_2"] - 1e-6)
    last["bd_suspect"] = (flat | (last["imb_1"].abs() > 0.95)).astype("int8")
    last = last.drop(columns=["snap_ts"]).reset_index().rename(columns={"m": "ts"})
    last.to_parquet(out / "bookdepth_1m.parquet", index=False)
    rep["rows_1m"] = len(last)
    rep["minutes_without_snap_in_range"] = int(((last["ts"].iloc[-1] - last["ts"].iloc[0]).total_seconds() // 60 + 1) - len(last))
    rep["bd_suspect_minutes"] = int(last["bd_suspect"].sum())
    sus = last.groupby(last["ts"].dt.date)["bd_suspect"].mean()
    rep["bd_suspect_days_gt20pct"] = {str(k): round(float(v), 3) for k, v in sus[sus > 0.2].items()}
    rep["imb_1_stats"] = last["imb_1"].describe().round(4).to_dict()
    (out / "bookdepth_quality_report.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps({k: v for k, v in rep.items() if k != "gaps_gt_10min"}, indent=1, default=str))
    print("gaps>10min:", len(rep["gaps_gt_10min"]), rep["gaps_gt_10min"][:30])


if __name__ == "__main__":
    main()
