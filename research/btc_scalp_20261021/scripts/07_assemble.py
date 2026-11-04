"""btc_scalp_1m.parquet: UTC dakika başına tek satır (2021-06-01 00:00 → 2026-10-20 23:59).

NEDENSELLİK SÖZLEŞMESİ (tüm sütunlar): satır `ts` = 1m bar AÇILIŞI; satırdaki HER değer
bar KAPANIŞINDA (ts+60 s) bilinir. Bu satıra dayalı karar en erken ts+1m açılışında icra edilir
(CLAUDE.md 2. Kural ölçüt 5: sonraki M1 açılışı). Dış seriler (metrics, funding, bookDepth)
yalnız yayın/ölçüm anı ≤ ts+60 s ise satıra girer.

Kullanım: python -I 07_assemble.py <scalp_data_dir> <spot_1m_parquet>
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

START = pd.Timestamp("2021-06-01", tz="UTC")
END = pd.Timestamp("2026-10-20 23:59", tz="UTC")
METRICS_STAMP_SWITCH = pd.Timestamp("2024-03-04 00:00", tz="UTC")  # öncesi damga=pencere SONU, sonrası=pencere BAŞI
METRICS_SAFETY = pd.Timedelta(minutes=1)    # pencere sonu + 1 dk yayın payı
FUNDING_H = 8
INTEREST = 0.0001                            # 8 saatlik faiz bileşeni (%0.01)
CLAMP = 0.0005
ROLL_5M = 8640                               # 30 gün (5 dk)
ROLL_1M = 43200                              # 30 gün (1 dk)
# Ön-kayıtlı tasfiye vekili eşikleri (doğrulamadan ÖNCE sabitlendi)
P5 = {"z_oi": -2.5, "z_ret": 2.5, "z_lvol": 2.0, "sell_share": 0.55}
P1 = {"z_ret": 4.0, "z_lvol": 3.0, "sell_share": 0.65}


def rz(x: pd.Series, n: int, minp: int, center: bool = True) -> pd.Series:
    """Geçmişe dayalı z-skoru: istatistikler bir önceki noktaya kadar (shift(1))."""
    m = x.rolling(n, min_periods=minp).mean().shift(1)
    s = x.rolling(n, min_periods=minp).std().shift(1)
    return (x - m) / s if center else x / s


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


def funding(g: pd.DataFrame, d: Path, rep: dict) -> pd.DataFrame:
    f = pd.read_parquet(d / "funding.parquet")
    f["estimated"] = 0
    # Ekim 2026 aylık dosyası yok, REST bölgesel engelli → premium endeksinden Binance formülüyle tahmin
    pm = ((g["prem_open"] + g["prem_close"]) / 2).to_numpy()
    w = np.arange(1, FUNDING_H * 60 + 1, dtype=float)
    est = []
    for H in pd.date_range(f["funding_time_nominal"].max() + pd.Timedelta(hours=FUNDING_H), END + pd.Timedelta(minutes=1) - pd.Timedelta(seconds=1), freq=f"{FUNDING_H}h"):
        i = int((H - START).total_seconds() // 60)
        seg = pm[i - len(w): i]
        ok = ~np.isnan(seg)
        P = (seg[ok] * w[ok]).sum() / w[ok].sum()
        est.append({"funding_time": H + pd.Timedelta(milliseconds=50), "funding_time_nominal": H, "interval_h": FUNDING_H,
                    "rate": P + np.clip(INTEREST - P, -CLAMP, CLAMP), "estimated": 1})
    f = pd.concat([f, pd.DataFrame(est)], ignore_index=True).sort_values("funding_time")
    rep["funding_estimated_settlements"] = len(est)
    f[["funding_time", "funding_time_nominal", "interval_h", "rate", "estimated"]].to_parquet(d / "funding_with_oct_estimates.parquet", index=False)
    g["_close"] = g["ts"] + pd.Timedelta(minutes=1)
    j = pd.merge_asof(g[["_close"]], f.rename(columns={"funding_time": "_ft"})[["_ft", "funding_time_nominal", "rate", "estimated"]],
                      left_on="_close", right_on="_ft", direction="backward")
    g["funding_rate_last"] = j["rate"].to_numpy()
    g["funding_last_time"] = j["funding_time_nominal"].to_numpy()
    g["funding_last_estimated"] = j["estimated"].to_numpy().astype("float32")
    cs = g["_close"].astype("int64") // 10**9
    per = FUNDING_H * 3600
    nxt = (cs // per) * per + per
    g["min_to_next_funding"] = ((nxt - cs) / 60).astype("int32")
    # kendi canlı tahminimiz: mevcut 8 sa penceresinde bu bar DAHİL artan ağırlıklı premium ort.
    win = (g["ts"].astype("int64") // 10**9) // per
    pos = (((g["ts"].astype("int64") // 10**9) % per) // 60 + 1).astype(float)
    xm = pd.Series(pm)
    wx = (xm * pos).where(xm.notna(), 0.0)
    ww = pos.where(xm.notna(), 0.0)
    P = wx.groupby(win).cumsum() / ww.groupby(win).cumsum()
    g["funding_pred_running"] = P + np.clip(INTEREST - P, -CLAMP, CLAMP)
    return g.drop(columns="_close")


def metrics(g: pd.DataFrame, d: Path, rep: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    m = pd.read_parquet(d / "metrics_5m.parquet")
    # OI=0 satırları (471) ölçüm hatası → NaN (aksi hâlde d_oi = ±inf olur)
    zero = m["sum_open_interest"] <= 0
    rep["metrics_zero_oi_rows_nulled"] = int(zero.sum())
    m.loc[zero, ["sum_open_interest", "sum_open_interest_value"]] = np.nan
    m["eff_ts"] = np.where(m["ts"] < METRICS_STAMP_SWITCH, m["ts"], m["ts"] + pd.Timedelta(minutes=5))
    m["eff_ts"] = pd.to_datetime(m["eff_ts"], utc=True)
    m["avail_ts"] = m["eff_ts"] + METRICS_SAFETY
    m = m.sort_values("eff_ts").drop_duplicates("eff_ts", keep="last").reset_index(drop=True)
    # 5 dk pencere [eff-5, eff) için perp akışı
    k = g.set_index("ts")[["perp_close", "perp_volume", "perp_taker_buy_base"]]
    c_end = k["perp_close"].reindex(m["eff_ts"] - pd.Timedelta(minutes=1)).to_numpy()
    c_start = k["perp_close"].reindex(m["eff_ts"] - pd.Timedelta(minutes=6)).to_numpy()
    vol5 = k["perp_volume"].rolling(5).sum().reindex(m["eff_ts"] - pd.Timedelta(minutes=1)).to_numpy()
    buy5 = k["perp_taker_buy_base"].rolling(5).sum().reindex(m["eff_ts"] - pd.Timedelta(minutes=1)).to_numpy()
    m["w_ret"] = c_end / c_start - 1
    m["w_lvol"] = np.log(vol5)
    m["w_sell_share"] = 1 - buy5 / vol5
    contiguous = m["eff_ts"].diff() == pd.Timedelta(minutes=5)
    m["d_oi"] = (m["sum_open_interest"] / m["sum_open_interest"].shift(1) - 1).where(contiguous)
    m["d_oi"] = m["d_oi"].replace([np.inf, -np.inf], np.nan)
    m["z_oi"] = rz(m["d_oi"], ROLL_5M, 2000)
    m["z_ret5"] = rz(m["w_ret"], ROLL_5M, 2000, center=False)
    m["z_lvol5"] = rz(m["w_lvol"].replace(-np.inf, np.nan), ROLL_5M, 2000)
    base = (m["z_oi"] <= P5["z_oi"]) & (m["z_lvol5"] >= P5["z_lvol"])
    m["liq_proxy_long_5m"] = (base & (m["z_ret5"] <= -P5["z_ret"]) & (m["w_sell_share"] >= P5["sell_share"])).astype("int8")
    m["liq_proxy_short_5m"] = (base & (m["z_ret5"] >= P5["z_ret"]) & (m["w_sell_share"] <= 1 - P5["sell_share"])).astype("int8")
    m["liq_proxy_score_5m"] = (-m["z_oi"]).clip(lower=0) * m["z_ret5"]
    rep["liq_proxy_5m_counts"] = {"long": int(m["liq_proxy_long_5m"].sum()), "short": int(m["liq_proxy_short_5m"].sum()),
                                  "windows": len(m)}
    m.to_parquet(d / "metrics_5m_effective.parquet", index=False)
    keep = {"eff_ts": "metrics_eff_ts", "sum_open_interest": "oi_btc", "sum_open_interest_value": "oi_usd",
            "count_toptrader_long_short_ratio": "top_ls_count", "sum_toptrader_long_short_ratio": "top_ls_pos",
            "count_long_short_ratio": "global_ls_count", "sum_taker_long_short_vol_ratio": "taker_ls_vol_ratio_5m",
            "d_oi": "oi_chg_5m", "z_oi": "oi_chg_5m_z", "liq_proxy_long_5m": "liq_proxy_long_5m",
            "liq_proxy_short_5m": "liq_proxy_short_5m", "liq_proxy_score_5m": "liq_proxy_score_5m"}
    mm = m[["avail_ts"] + list(keep)].rename(columns=keep)
    g["_close"] = g["ts"] + pd.Timedelta(minutes=1)
    j = pd.merge_asof(g[["_close"]], mm, left_on="_close", right_on="avail_ts", direction="backward")
    for c in keep.values():
        g[c] = j[c].to_numpy()
    g["metrics_age_min"] = ((g["_close"] - g["metrics_eff_ts"]).dt.total_seconds() / 60).astype("float32")
    # yalnız taze (≤ 15 dk) metrics'e güven; daha eski satırlarda değerler NaN
    stale = g["metrics_age_min"] > 15
    rep["metrics_stale_rows_nulled"] = int(stale.sum())
    for c in keep.values():
        if c != "metrics_eff_ts":
            g.loc[stale, c] = np.nan
    return g.drop(columns="_close"), m


def flow_proxy_1m(g: pd.DataFrame, rep: dict) -> pd.DataFrame:
    r = np.log(g["perp_close"] / g["perp_open"])
    lv = np.log(g["perp_volume"].where(g["perp_volume"] > 0))
    zr = rz(r, ROLL_1M, 10000, center=False)
    zv = rz(lv, ROLL_1M, 10000)
    ss = g["perp_taker_sell_base"] / g["perp_volume"]
    g["perp_ret_1m_z"] = zr.astype("float32")
    g["perp_lvol_1m_z"] = zv.astype("float32")
    g["liq_flow_long_1m"] = ((zr <= -P1["z_ret"]) & (zv >= P1["z_lvol"]) & (ss >= P1["sell_share"])).astype("int8")
    g["liq_flow_short_1m"] = ((zr >= P1["z_ret"]) & (zv >= P1["z_lvol"]) & (ss <= 1 - P1["sell_share"])).astype("int8")
    rep["liq_flow_1m_counts"] = {"long": int(g["liq_flow_long_1m"].sum()), "short": int(g["liq_flow_short_1m"].sum())}
    return g


def bookdepth(g: pd.DataFrame, d: Path) -> pd.DataFrame:
    b = pd.read_parquet(d / "bookdepth_1m.parquet")
    keep = ["imb_0p2", "imb_1", "imb_2", "imb_5", "bid_n_1", "ask_n_1", "bid_n_5", "ask_n_5", "bd_suspect"]
    b = b[["ts", "snap_age_s"] + keep].rename(columns={"ts": "_bts"})
    j = pd.merge_asof(g[["ts"]], b, left_on="ts", right_on="_bts", direction="backward", tolerance=pd.Timedelta(minutes=5))
    for c in keep:
        g[f"bd_{c}" if not c.startswith("bd_") else c] = j[c].to_numpy()
    g["bd_snap_age_s"] = (j["snap_age_s"] + (g["ts"] - j["_bts"]).dt.total_seconds()).astype("float32")
    return g


def main() -> None:
    d, spot = Path(sys.argv[1]), Path(sys.argv[2])
    rep: dict = {}
    g = load_grid(d, spot)
    g = funding(g, d, rep)
    g, m = metrics(g, d, rep)
    g = flow_proxy_1m(g, rep)
    g = bookdepth(g, d)
    a = pd.read_parquet(d / "perp_aggflow_1m.parquet")
    g = g.merge(a, on="ts", how="left")
    for c in g.columns:
        if g[c].dtype == "float64" and not any(c.endswith(s) for s in ("open", "high", "low", "close", "vwap")) \
                and not c.startswith("funding") and c not in ("oi_usd",):
            g[c] = g[c].astype("float32")
    g.to_parquet(d / "btc_scalp_1m.parquet", index=False)
    rep["rows"] = len(g)
    rep["columns"] = list(g.columns)
    rep["non_null_share"] = g.notna().mean().round(4).to_dict()
    rep["first_non_null"] = {c: str(g.loc[g[c].notna(), "ts"].iloc[0]) if g[c].notna().any() else None for c in g.columns}
    (d / "btc_scalp_1m_report.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps({k: v for k, v in rep.items() if k not in ("columns",)}, indent=1, default=str))


if __name__ == "__main__":
    main()
