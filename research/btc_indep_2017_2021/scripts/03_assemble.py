"""btc_scalp_1m.parquet (bağımsız dönem): UTC dakika başına tek satır 2017-08-17 00:00 → 2021-05-31 23:59.

btc_scalp_20261021/scripts/07_assemble.py::load_grid + son float32 dönüşüm kuralı BİREBİR (yalnız START/END değişti).
funding/metrics/bookdepth/aggflow birleştirmeleri ATLANIR: yedi dondurulmuş kolun hiçbiri bu sütunları okumaz (prereg §1).
Perp verisi 2020-01-01'de başlar → öncesi perp_* NaN (perp_zero_vol=0; NaN akış z-skorlarını NaN yapar → olay yok).
Kullanım: python -I -B 03_assemble.py <data_dir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

START = pd.Timestamp("2017-08-17", tz="UTC")
END = pd.Timestamp("2021-05-31 23:59", tz="UTC")


def load_grid(d: Path, spot_path: Path) -> pd.DataFrame:
    g = pd.DataFrame({"ts": pd.date_range(START, END, freq="1min")})
    sp = pd.read_parquet(spot_path)
    sp["taker_sell_base"] = sp["volume"] - sp["taker_buy_base"]
    sp = sp.rename(columns={c: f"spot_{c}" for c in sp.columns if c != "ts"})
    pp = pd.read_parquet(d / "perp_1m.parquet")
    pp["taker_sell_base"] = pp["volume"] - pp["taker_buy_base"]
    pp = pp.rename(columns={c: f"perp_{c}" for c in pp.columns if c != "ts"})
    g = g.merge(sp, on="ts", how="left").merge(pp, on="ts", how="left")
    g["spot_missing"] = g["spot_close"].isna().astype("int8")
    g["spot_zero_vol"] = (g["spot_volume"] == 0).astype("int8")
    g["perp_zero_vol"] = (g["perp_volume"] == 0).astype("int8")
    for name, pre in [("premium_1m", "prem"), ("mark_1m", "mark"), ("index_1m", "index")]:
        x = pd.read_parquet(d / f"{name}.parquet").drop(columns="n_samples")
        x = x.rename(columns={c: f"{pre}_{c}" for c in x.columns if c != "ts"})
        if pre != "prem":
            x = x[["ts", f"{pre}_close"]]
        g = g.merge(x, on="ts", how="left")
    g["basis_perp_spot_bp"] = (g["perp_close"] / g["spot_close"] - 1) * 1e4
    g["basis_perp_index_bp"] = (g["perp_close"] / g["index_close"] - 1) * 1e4
    g["basis_mark_index_bp"] = (g["mark_close"] / g["index_close"] - 1) * 1e4
    g["prem_close_bp"] = g["prem_close"] * 1e4
    return g


def main() -> None:
    d = Path(sys.argv[1])
    g = load_grid(d, d / "btc_1m.parquet")
    for c in g.columns:
        if g[c].dtype == "float64" and not any(c.endswith(s) for s in ("open", "high", "low", "close", "vwap")) \
                and not c.startswith("funding") and c not in ("oi_usd",):
            g[c] = g[c].astype("float32")
    g.to_parquet(d / "btc_scalp_1m.parquet", index=False)
    rep = {"rows": len(g), "columns": list(g.columns),
           "first_non_null": {c: str(g.loc[g[c].notna(), "ts"].iloc[0]) if g[c].notna().any() else None for c in g.columns}}
    pm = g["ts"] >= pd.Timestamp("2020-01-01", tz="UTC")
    b = g.loc[pm, ["basis_perp_spot_bp", "basis_perp_index_bp", "prem_close_bp"]].astype(float)
    rep["perp_window"] = {"spot_missing": int(g.loc[pm, "spot_missing"].sum()), "perp_missing": int(g.loc[pm, "perp_close"].isna().sum()),
                          "perp_zero_vol": int(g.loc[pm, "perp_zero_vol"].sum()),
                          "basis_perp_spot_bp_quantiles": b["basis_perp_spot_bp"].quantile([0.001, 0.01, 0.5, 0.99, 0.999]).round(2).to_dict(),
                          "corr_basis_spot_vs_prem": round(float(b.corr().iloc[0, 2]), 4),
                          "corr_basis_spot_vs_index": round(float(b.corr().iloc[0, 1]), 4)}
    (d / "btc_scalp_1m_report.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps({k: v for k, v in rep.items() if k != "columns"}, indent=1, default=str))


if __name__ == "__main__":
    main()
