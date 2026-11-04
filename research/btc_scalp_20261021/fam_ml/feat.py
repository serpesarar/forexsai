"""fam_ml ortak: 1m ızgara yükleme, BAD maskesi, nedensel özellikler, broker rollover takvimi.

Kural: satır m'deki her özellik yalnız 0..m satırlarından (bar kapanışı ts[m]+1m'de bilinir) hesaplanır.
Pandas rolling pencereleri m'de biter (m dahil); z-skorlarının istatistikleri de m'de biten pencereden.
"""
from __future__ import annotations

from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

DATA = "/Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/data/btc_scalp_1m.parquet"
T0 = pd.Timestamp("2021-06-01", tz="UTC")
DAY = 1440
M30D = 30 * DAY

PRICE_COLS = ["spot_open", "spot_high", "spot_low", "spot_close", "spot_volume", "spot_quote_volume",
              "spot_taker_buy_base", "spot_missing", "spot_zero_vol"]
PERP_COLS = ["perp_close", "perp_volume", "perp_trades", "perp_taker_buy_base", "perp_zero_vol"]
DERIV_COLS = ["prem_close_bp", "basis_perp_spot_bp", "basis_mark_index_bp", "funding_rate_last", "funding_pred_running",
              "min_to_next_funding", "oi_btc", "top_ls_count", "top_ls_pos", "global_ls_count", "taker_ls_vol_ratio_5m",
              "oi_chg_5m_z", "liq_proxy_long_5m", "liq_proxy_short_5m", "liq_proxy_score_5m", "metrics_age_min",
              "perp_ret_1m_z", "perp_lvol_1m_z", "liq_flow_long_1m", "liq_flow_short_1m"]
DEPTH_COLS = ["bd_imb_1", "bd_imb_2", "bd_imb_5", "bd_bid_n_1", "bd_ask_n_1", "bd_suspect"]
CHECK_COLS = ["metrics_eff_ts", "funding_last_time", "bd_snap_age_s"]
ALL_COLS = ["ts"] + PRICE_COLS + PERP_COLS + DERIV_COLS + DEPTH_COLS


def load(cols=None, n_rows: int | None = None) -> pd.DataFrame:
    df = pd.read_parquet(DATA, columns=cols or ALL_COLS)
    if n_rows is not None:
        df = df.iloc[:n_rows].copy()
    m = ((df["ts"] - T0) / pd.Timedelta(minutes=1)).to_numpy()
    assert np.array_equal(m, np.arange(len(df))), "ızgara tam değil"
    return df.reset_index(drop=True)


def _runs(mask: np.ndarray, minlen: int) -> np.ndarray:
    out = np.zeros(len(mask), dtype=bool)
    d = np.diff(np.concatenate([[0], mask.astype(np.int8), [0]]))
    st, en = np.where(d == 1)[0], np.where(d == -1)[0]
    for a, b in zip(st, en):
        if b - a >= minlen:
            out[a:b] = True
    return out


def bad_mask(df: pd.DataFrame) -> np.ndarray:
    n = len(df)
    bad = np.zeros(n, dtype=bool)
    a = int((pd.Timestamp("2023-03-24 11:28", tz="UTC") - T0) / pd.Timedelta(minutes=1))
    b = int((pd.Timestamp("2023-03-24 14:00", tz="UTC") - T0) / pd.Timedelta(minutes=1))
    if a < n:
        bad[a:min(b, n)] = True
    bad |= _runs(df["spot_close"].isna().to_numpy(), 5)
    bad |= _runs(df["perp_zero_vol"].to_numpy() == 1, 5)
    return bad


def _z(x: pd.Series, w: int, minp: int) -> pd.Series:
    r = x.rolling(w, min_periods=minp)
    return (x - r.mean()) / r.std()


def _rsum(x: pd.Series, k: int) -> pd.Series:
    return x.rolling(k, min_periods=max(1, int(k * 0.8))).sum()


def atr5_price(h: np.ndarray, l: np.ndarray, c: np.ndarray) -> np.ndarray:
    """ATR14 of 5m buckets (m//5); value at row m uses buckets ≤ bucket(m). Meaningful at decision rows (m%5==4)."""
    n = len(c)
    b5 = np.arange(n) // 5
    g = pd.DataFrame({"b": b5, "h": h, "l": l, "c": c}).groupby("b")
    agg = pd.DataFrame({"h": g["h"].max(), "l": g["l"].min(), "c": g["c"].last()})
    pc = agg["c"].shift(1)
    tr = pd.concat([agg["h"] - agg["l"], (agg["h"] - pc).abs(), (agg["l"] - pc).abs()], axis=1).max(axis=1)
    a = tr.rolling(14, min_periods=10).mean().to_numpy()
    out = a[b5]
    # satır m, kovası henüz tamamlanmamışsa (m%5 != 4) önceki kovayı kullan → her satırda nedensel
    done = (np.arange(n) % 5) == 4
    prev = np.concatenate([[np.nan] * 5, a])[b5 + 4]  # a[b5-1]
    return np.where(done, out, prev)


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Tüm 1m satırlar için nedensel özellikler. Döner: (özellik DF, grup sözlüğü)."""
    n = len(df)
    bad = bad_mask(df)
    o = df["spot_open"].to_numpy().copy()
    h = df["spot_high"].to_numpy().copy()
    l = df["spot_low"].to_numpy().copy()
    c = df["spot_close"].to_numpy().copy()
    for arr in (o, h, l, c):
        arr[bad] = np.nan
    cs = pd.Series(c).ffill()
    cff = cs.to_numpy()
    lr = pd.Series(np.log(cff)).diff() * 1e4  # bp
    F: dict[str, np.ndarray] = {}
    G: dict[str, list] = {"PRICE": [], "FLOW": [], "DERIV": [], "DEPTH": [], "CAL": []}

    def put(name: str, val, grp: str) -> None:
        F[name] = np.asarray(val, dtype=np.float32)
        G[grp].append(name)

    # ---------------- PRICE ----------------
    vol = {}
    for k in (15, 60, 240, 1440):
        vol[k] = lr.rolling(k, min_periods=int(k * 0.8)).std()
        put(f"vol_{k}", vol[k], "PRICE")
    for k in (1, 5, 15, 30, 60, 240, 1440):
        r = pd.Series(np.log(cff)).diff(k) * 1e4
        put(f"ret_{k}", r, "PRICE")
        put(f"retz_{k}", r / (vol[1440] * np.sqrt(k)), "PRICE")
    for k in (15, 60, 240):
        put(f"volratio_{k}", vol[k] / vol[1440], "PRICE")
    pc = np.concatenate([[np.nan], c[:-1]])
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    atr1 = pd.Series(tr).rolling(14, min_periods=10).mean().to_numpy()
    atr5 = atr5_price(h, l, c)
    put("atr1_bp", atr1 / cff * 1e4, "PRICE")
    atr5_bp = atr5 / cff * 1e4
    put("atr5_bp", atr5_bp, "PRICE")
    s_bp = np.maximum(19.0, 1.1 * atr5_bp)
    put("s_bp", s_bp, "PRICE")
    put("s_over_atr5", s_bp / atr5_bp, "PRICE")
    hs, ls = pd.Series(h), pd.Series(l)
    for k in (60, 240, 1440):
        hi = hs.rolling(k, min_periods=int(k * 0.8)).max()
        lo = ls.rolling(k, min_periods=int(k * 0.8)).min()
        put(f"rangepos_{k}", (cs - lo) / (hi - lo), "PRICE")
        put(f"range_{k}_atr", (hi - lo) / pd.Series(atr5), "PRICE")
    sv = df["spot_volume"].astype("float64").fillna(0.0)
    tp = pd.Series((h + l + c) / 3.0).fillna(cs)
    day = np.arange(n) // DAY
    pv = (tp * sv)
    cum_pv = pv.groupby(day).cumsum()
    cum_v = sv.groupby(day).cumsum()
    vwap_d = cum_pv / cum_v.replace(0, np.nan)
    put("vwapd_dist_atr", (cs - vwap_d) / pd.Series(atr5), "PRICE")
    put("min_of_day", np.arange(n) % DAY, "CAL")
    vwap240 = pv.rolling(240, min_periods=200).sum() / sv.rolling(240, min_periods=200).sum().replace(0, np.nan)
    put("vwap240_dist_atr", (cs - vwap240) / pd.Series(atr5), "PRICE")
    bbw60 = cs.rolling(60, min_periods=50).std() / cs * 1e4
    put("bbw60_bp", bbw60, "PRICE")
    put("sqz60", bbw60 / bbw60.rolling(DAY, min_periods=1000).mean(), "PRICE")
    o5 = pd.Series(o).shift(4).to_numpy()
    h5 = hs.rolling(5, min_periods=4).max().to_numpy()
    l5 = ls.rolling(5, min_periods=4).min().to_numpy()
    rng5 = h5 - l5
    with np.errstate(invalid="ignore", divide="ignore"):
        put("bar5_body", np.where(rng5 > 0, (c - o5) / rng5, 0.0), "PRICE")
        put("bar5_upwick", np.where(rng5 > 0, (h5 - np.maximum(o5, c)) / rng5, 0.0), "PRICE")
        put("bar5_lowwick", np.where(rng5 > 0, (np.minimum(o5, c) - l5) / rng5, 0.0), "PRICE")
        put("bar5_range_atr", rng5 / atr5, "PRICE")
    rv24 = vol[1440] * np.sqrt(525600) / 1e4  # yıllık oran
    put("rv24", rv24, "PRICE")
    put("rv24_rel30d", rv24 / rv24.rolling(M30D, min_periods=10 * DAY).mean(), "PRICE")

    # ---------------- FLOW ----------------
    pvol = df["perp_volume"].astype("float64")
    ptb = df["perp_taker_buy_base"].astype("float64")
    svol = df["spot_volume"].astype("float64")
    stb = df["spot_taker_buy_base"].astype("float64")
    ptr = df["perp_trades"].astype("float64")
    imb_p, imb_s = {}, {}
    for k in (1, 5, 15, 60):
        imb_p[k] = 2 * _rsum(ptb, k) / _rsum(pvol, k).replace(0, np.nan) - 1
        imb_s[k] = 2 * _rsum(stb, k) / _rsum(svol, k).replace(0, np.nan) - 1
        put(f"pimb_{k}", imb_p[k], "FLOW")
        put(f"simb_{k}", imb_s[k], "FLOW")
    for k in (5, 60):
        put(f"imbdiff_{k}", imb_s[k] - imb_p[k], "FLOW")
    pflow = 2 * ptb - pvol
    v60m = _rsum(pvol, 60).rolling(M30D, min_periods=10 * DAY).mean()
    for k in (60, 240):
        put(f"pcvd_{k}", _rsum(pflow, k) / (v60m * k / 60), "FLOW")
    sflow = 2 * stb - svol
    put("scvd_60", _rsum(sflow, 60) / _rsum(svol, 60).rolling(M30D, min_periods=10 * DAY).mean(), "FLOW")
    for k in (5, 60):
        lv = np.log1p(_rsum(pvol, k))
        put(f"pvolz_{k}", _z(lv, M30D, 10 * DAY), "FLOW")
        lt = np.log1p(_rsum(ptr, k))
        put(f"ptradez_{k}", _z(lt, M30D, 10 * DAY), "FLOW")
        lsv = np.log1p(_rsum(svol, k))
        put(f"svolz_{k}", _z(lsv, M30D, 10 * DAY), "FLOW")
    ats = np.log(_rsum(pvol, 60) / _rsum(ptr, 60).replace(0, np.nan))
    put("ptsize_z", _z(ats, M30D, 10 * DAY), "FLOW")
    sp = np.log(_rsum(svol, 60) / _rsum(pvol, 60).replace(0, np.nan))
    put("spot_perp_vol_log", sp, "FLOW")
    put("spot_perp_vol_z", _z(sp, M30D, 10 * DAY), "FLOW")

    # ---------------- DERIV ----------------
    oi = df["oi_btc"].astype("float64")
    oich = {}
    for k in (5, 15, 60, 240):
        oich[k] = oi / oi.shift(k) - 1
        put(f"oichg_{k}", oich[k] * 1e4, "DERIV")
    put("oi_chg_5m_z", df["oi_chg_5m_z"], "DERIV")
    put("oichg60_z", _z(oich[60], M30D, 10 * DAY), "DERIV")
    r60 = pd.Series(np.log(cff)).diff(60)
    quad = np.where(oich[60].isna() | r60.isna(), np.nan, 2.0 * (r60 > 0) + (oich[60] > 0))
    put("oi_price_quad", quad, "DERIV")
    put("oi_price_prod", np.sign(r60) * oich[60] * 1e4, "DERIV")
    fr = df["funding_rate_last"].astype("float64") * 1e4
    put("funding_bp", fr, "DERIV")
    put("funding_z30", _z(fr, M30D, 10 * DAY), "DERIV")
    fp = df["funding_pred_running"].astype("float64") * 1e4
    put("funding_pred_bp", fp, "DERIV")
    put("funding_pred_minus_last", fp - fr, "DERIV")
    put("min_to_funding", df["min_to_next_funding"], "DERIV")
    prem = df["prem_close_bp"].astype("float64")
    put("prem_bp", prem, "DERIV")
    put("prem_z24", _z(prem, DAY, 1000), "DERIV")
    put("prem_chg60", prem - prem.rolling(60, min_periods=40).mean(), "DERIV")
    bas = df["basis_perp_spot_bp"].astype("float64")
    put("basis_bp", bas, "DERIV")
    put("basis_z24", _z(bas, DAY, 1000), "DERIV")
    put("basis_chg60", bas - bas.shift(60), "DERIV")
    put("basis_mark_index_bp", df["basis_mark_index_bp"], "DERIV")
    for col, nm in [("top_ls_count", "ls_top_acc"), ("top_ls_pos", "ls_top_pos"), ("global_ls_count", "ls_global"),
                    ("taker_ls_vol_ratio_5m", "ls_taker5")]:
        x = np.log(df[col].astype("float64").where(df[col] > 0))
        put(nm, x, "DERIV")
        put(f"{nm}_chg24", x - x.shift(DAY), "DERIV")
        put(f"{nm}_miss", x.isna().astype(float), "DERIV")
    put("ls_top_minus_global", np.log(df["top_ls_pos"].where(df["top_ls_pos"] > 0)) -
        np.log(df["global_ls_count"].where(df["global_ls_count"] > 0)), "DERIV")
    for col in ("liq_proxy_long_5m", "liq_proxy_short_5m", "liq_proxy_score_5m", "perp_ret_1m_z", "perp_lvol_1m_z",
                "metrics_age_min"):
        put(col, df[col], "DERIV")
    for col in ("liq_flow_long_1m", "liq_flow_short_1m"):
        put(col + "_sum60", df[col].astype("float64").rolling(60, min_periods=1).sum(), "DERIV")
    put("liq_proxy_long_sum60", df["liq_proxy_long_5m"].astype("float64").rolling(60, min_periods=1).max(), "DERIV")
    put("liq_proxy_short_sum60", df["liq_proxy_short_5m"].astype("float64").rolling(60, min_periods=1).max(), "DERIV")
    put("perp_ret_1m_z_absmax15", df["perp_ret_1m_z"].abs().rolling(15, min_periods=1).max(), "DERIV")

    # ---------------- DEPTH ----------------
    sus = df["bd_suspect"].to_numpy() == 1
    for col in ("bd_imb_1", "bd_imb_2", "bd_imb_5"):
        x = df[col].astype("float64").where(~sus)
        put(col, x, "DEPTH")
    i1 = df["bd_imb_1"].astype("float64").where(~sus)
    put("bd_imb_1_mean5", i1.rolling(5, min_periods=1).mean(), "DEPTH")
    put("bd_imb_1_chg15", i1 - i1.shift(15), "DEPTH")
    dep = np.log((df["bd_bid_n_1"] + df["bd_ask_n_1"]).astype("float64").where(~sus))
    put("bd_depth1_log", dep, "DEPTH")
    put("bd_depth1_z", _z(dep, M30D, 5 * DAY), "DEPTH")
    put("bd_miss", i1.isna().astype(float), "DEPTH")

    # ---------------- CAL (karar anı T = ts[m] + 1 dk) ----------------
    T = df["ts"] + pd.Timedelta(minutes=1)
    put("hour", T.dt.hour, "CAL")
    put("dow", T.dt.dayofweek, "CAL")
    put("weekend", (T.dt.dayofweek >= 5).astype(float), "CAL")
    put("min_of_hour", T.dt.minute, "CAL")
    G["CAL"].remove("min_of_day")
    del F["min_of_day"]
    out = pd.DataFrame(F)
    out["min_to_close"] = forced_close_minutes(len(df)) - (np.arange(n) + 1)
    G["CAL"].append("min_to_close")
    out["min_to_close"] = out["min_to_close"].astype(np.float32)
    return out, G


def rollover_minutes(n: int) -> np.ndarray:
    """Her UTC günü için broker rollover dakikası (NY 17:00) — günün başından dakika."""
    nd = n // DAY + 3
    ny = ZoneInfo("America/New_York")
    res = np.empty(nd, dtype=np.int64)
    for i in range(nd):
        d = (T0 + pd.Timedelta(days=i)).date()
        loc = pd.Timestamp(year=d.year, month=d.month, day=d.day, hour=17, tz=ny)
        u = loc.tz_convert("UTC")
        res[i] = i * DAY + u.hour * 60 + u.minute
    return res


def forced_close_minutes(n: int) -> np.ndarray:
    """Giriş dakikası e = m+1 için bir sonraki zorunlu kapanış dakikası (R−2); molada ise −1."""
    R = rollover_minutes(n)
    e = np.arange(n) + 1
    d = e // DAY
    r_today = R[d]
    fc = np.where(e < r_today - 2, r_today - 2, np.where(e < r_today + 1, -1, R[d + 1] - 2))
    return fc
