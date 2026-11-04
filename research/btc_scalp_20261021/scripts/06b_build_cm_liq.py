"""COIN-M BTCUSD_PERP liquidationSnapshot (2023-06-25 → 2024-10-14) → 1m ve 5m tasfiye serisi.

YALNIZ DOĞRULAMA AMAÇLI: USDT-M BTCUSDT için Binance arşivinde liquidationSnapshot YOK.
Kaynak, forceOrder akışının anlık görüntüsüdür (sembol başına 1000 ms'de yalnız SON tasfiye) →
ALT SINIR / örneklem, tam toplam değil. Ham dosyalarda satırların ~yarısı birebir kopya → atılır.
side=SELL: long pozisyon tasfiyesi (zorla satış); side=BUY: short tasfiyesi (zorla alış).
Notional USD = accumulated_fill_quantity × 100 (BTCUSD_PERP kontrat = 100 USD).
Kullanım: python -I 06b_build_cm_liq.py <raw_dir> <out_dir>
"""
from __future__ import annotations
import io, json, sys, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

CONTRACT_USD = 100.0


def main() -> None:
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    parts, empty = [], 0
    for f in sorted((raw / "cm_liq").glob("*.zip")):
        with zipfile.ZipFile(f) as z:
            b = z.read([n for n in z.namelist() if n.endswith(".csv")][0])
        if len(b.strip().split(b"\n")) < 2:
            empty += 1
            continue
        parts.append(pd.read_csv(io.BytesIO(b)))
    d = pd.concat(parts, ignore_index=True)
    rep = {"files_nonempty": len(parts), "files_empty": empty, "rows_raw": len(d), "exact_dup_rows": int(d.duplicated().sum())}
    d = d.drop_duplicates().copy()
    d["ts_event"] = pd.to_datetime(d["time"], unit="ms", utc=True)
    d["usd"] = d["accumulated_fill_quantity"].astype(float) * CONTRACT_USD
    d["long_liq_usd"] = np.where(d["side"] == "SELL", d["usd"], 0.0)
    d["short_liq_usd"] = np.where(d["side"] == "BUY", d["usd"], 0.0)
    rep.update({"rows": len(d), "first": str(d["ts_event"].min()), "last": str(d["ts_event"].max()),
                "side_counts": d["side"].value_counts().to_dict()})
    for rule, name in [("1min", "cm_liq_1m"), ("5min", "cm_liq_5m")]:
        g = d.groupby(d["ts_event"].dt.floor(rule))
        o = pd.DataFrame({"cm_long_liq_usd": g["long_liq_usd"].sum(), "cm_short_liq_usd": g["short_liq_usd"].sum(),
                          "cm_liq_n": g.size()}).reset_index().rename(columns={"ts_event": "ts"})
        o.to_parquet(out / f"{name}.parquet", index=False)
        rep[f"{name}_rows"] = len(o)
    (out / "cm_liq_quality_report.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps(rep, indent=1, default=str))


if __name__ == "__main__":
    main()
