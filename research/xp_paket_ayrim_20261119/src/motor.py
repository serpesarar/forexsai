"""motor.py — paket (K1 + OPEX + XP) işlemleri ve ETF çağı (V1 vekili) için çok TF kanal + tam `ta` bataryası.

python motor.py test   # birim + sızıntı testleri (tam veri = girişte kesilmiş veri)
python motor.py kos    # results/paket_ozellik.parquet, results/cag_ozellik.parquet
Tüm gün içi TF'ler giriş anına çapalıdır: son blok tam 16:00 NY'de biter (E81).
"""
from __future__ import annotations

import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
RES = HERE / "results"
for p in ("research/xp_kaybeden_20261119/src", "research/k1_ayi_cagi_20261118/src"):
    sys.path.insert(0, str(ROOT / p))

NY = "America/New_York"
CUT = pd.Timestamp("2026-11-05")          # ileri gölge dönemi 2026-11-06'dan başlar; dokunma
KESIF_SON = pd.Timestamp("2021-10-31")
WIN = 400                                  # blok penceresi (durumlu göstergeler için sabit ısınma)
INTRA = {"m30": 1, "h1": 2, "h2": 4, "h4": 8}
LENS = (20, 50, 100, 200)
PRICE_LEVEL = ["volume_vwap", "volatility_bbm", "volatility_bbh", "volatility_bbl", "volatility_kcc", "volatility_kch", "volatility_kcl",
               "volatility_dcl", "volatility_dch", "volatility_dcm", "trend_sma_fast", "trend_sma_slow", "trend_ema_fast", "trend_ema_slow",
               "trend_ichimoku_conv", "trend_ichimoku_base", "trend_ichimoku_a", "trend_ichimoku_b", "trend_visual_ichimoku_a",
               "trend_visual_ichimoku_b", "trend_psar_up", "trend_psar_down", "momentum_kama"]
PRICE_UNIT = ["volatility_atr", "trend_macd", "trend_macd_signal", "trend_macd_diff", "momentum_ao", "trend_dpo"]
DROP = ["volume_adi", "volume_obv", "volume_vpt", "volume_nvi", "others_cr", "volume_fi", "volume_em", "volume_sma_em"]
VOLUME_COLS = ["volume_cmf", "volume_mfi", "volume_vwap", "momentum_pvo", "momentum_pvo_signal", "momentum_pvo_hist"]


# ---------------- çekirdek özellikler ----------------
def linreg(y: np.ndarray) -> tuple[float, float, float, float]:
    """z (son nokta kalıntısı / σ), eğim (bp/blok, son değere göre), R², σ/fiyat (bp)."""
    y = np.asarray(y, float)
    if len(y) < 5 or not np.all(np.isfinite(y)):
        return (np.nan,) * 4
    x = np.arange(len(y), dtype=float)
    b, a = np.polyfit(x, y, 1)
    res = y - (a + b * x)
    sd = res.std(ddof=2)
    ss = ((y - y.mean()) ** 2).sum()
    r2 = 1 - (res ** 2).sum() / ss if ss > 0 else np.nan
    return (res[-1] / sd if sd > 0 else np.nan, b / y[-1] * 1e4, r2, sd / y[-1] * 1e4)


def chan_feats(df: pd.DataFrame, pre: str) -> dict:
    c, h, l = df.c.values, df.h.values, df.l.values
    out = {}
    for n in LENS:
        if len(c) >= n:
            z, s, r2, w = linreg(c[-n:])
        else:
            z = s = r2 = w = np.nan
        out.update({f"{pre}_k{n}_z": z, f"{pre}_k{n}_egim": s, f"{pre}_k{n}_r2": r2, f"{pre}_k{n}_gen": w})
    for n in (50, 100):
        if len(c) >= n:
            hi, lo = h[-n:].max(), l[-n:].min()
            out[f"{pre}_dc{n}_kon"] = (c[-1] - lo) / (hi - lo) if hi > lo else np.nan
        else:
            out[f"{pre}_dc{n}_kon"] = np.nan
    return out


def ta_feats(df: pd.DataFrame, pre: str, has_vol: bool) -> dict:
    import ta
    if len(df) < 60:
        return {}
    x = pd.DataFrame({"open": df.o.values, "high": df.h.values, "low": df.l.values, "close": df.c.values,
                      "volume": df.v.values if has_vol else np.ones(len(df))})
    t = ta.add_all_ta_features(x, "open", "high", "low", "close", "volume", fillna=False).iloc[-1]
    c = float(df.c.values[-1])
    out = {}
    for k, v in t.items():
        if k in ("open", "high", "low", "close", "volume") or k in DROP:
            continue
        if not has_vol and k in VOLUME_COLS:
            continue
        v = float(v) if v is not None else np.nan
        if k in PRICE_LEVEL:
            v = (v / c - 1) * 1e4 if np.isfinite(v) and v != 0 else np.nan
        elif k in PRICE_UNIT:
            v = v / c * 1e4
        out[f"{pre}_{k}"] = v
    # PSAR yönü tek sütun: fiyat PSAR'ın üstünde mi
    up, dn = out.pop(f"{pre}_trend_psar_up", np.nan), out.pop(f"{pre}_trend_psar_down", np.nan)
    out[f"{pre}_psar_uz"] = up if np.isfinite(up) else dn
    return out


def blocks(b: pd.DataFrame, m: int) -> pd.DataFrame:
    """Son mumdan geriye m'li bloklar (son blok son mumla biter)."""
    n = (len(b) // m) * m
    z = b.iloc[len(b) - n:]
    g = np.arange(n) // m
    agg = {"o": "first", "h": "max", "l": "min", "c": "last"}
    if "v" in z.columns:
        agg["v"] = "sum"
    return z.groupby(g).agg(agg).reset_index(drop=True)


def tf_feats(df: pd.DataFrame, pre: str, has_vol: bool) -> dict:
    out = chan_feats(df, pre)
    out.update(ta_feats(df, pre, has_vol))
    return out


def align(r: dict) -> dict:
    tfs = [t for t in list(INTRA) + ["D", "W"] if f"{t}_k50_egim" in r]
    def cnt(f):
        return float(sum(1 for t in tfs if np.isfinite(r.get(f"{t}_k50_egim", np.nan)) and f(t)))
    return {"H_egim_eksi_tf": cnt(lambda t: r[f"{t}_k50_egim"] < 0),
            "H_z_dip_tf": cnt(lambda t: r.get(f"{t}_k50_z", np.nan) < -1),
            "H_rsi_dip_tf": cnt(lambda t: r.get(f"{t}_momentum_rsi", np.nan) < 30),
            "H_tf_say": float(len(tfs))}


# ---------------- barlar ----------------
def rth_daily(b: pd.DataFrame) -> pd.DataFrame:
    """30 dk mumlardan 09:30–16:00 NY nakit seansı günlük mumları (ETF günlük mumuyla aynı tanım)."""
    import ozellik as O
    x = O.G._local(b, NY)
    z = b.assign(day=pd.to_datetime(x.day.values), mn=x.mn.values)
    z = z[(z.mn >= 570) & (z.mn < 960)]
    agg = {"o": ("o", "first"), "h": ("h", "max"), "l": ("l", "min"), "c": ("c", "last")}
    if "v" in z.columns:
        agg["v"] = ("v", "sum")
    d = z.groupby("day").agg(**agg)
    n = z.groupby("day").size()
    return d[n >= 10]                       # yarım/eksik seans dışı


def entry_ts(d: pd.Timestamp) -> int:
    return int(pd.Timestamp(datetime(d.year, d.month, d.day, 16, 0), tz=NY).timestamp())


def feed_trade_feats(b30: pd.DataFrame, daily: pd.DataFrame, d: pd.Timestamp, has_vol: bool, intraday: bool = True) -> dict:
    r = {}
    if intraday:
        e = entry_ts(d)
        i = int(np.searchsorted(b30.t.values, e - 1800, side="right"))   # başlangıcı ≤ 15:30 olan mumlar (16:00'da kapanmış)
        if i == 0 or b30.t.values[i - 1] != e - 1800:
            return {}                                                      # 15:30 mumu yok → işlem dışı
        hist = b30.iloc[max(0, i - WIN * 8):i]
        for tf, m in INTRA.items():
            blk = blocks(hist, m).iloc[-WIN:]
            r.update(tf_feats(blk, tf, has_vol))
    dd = daily[daily.index <= d].iloc[-WIN * 5:]
    if len(dd) and dd.index[-1] == d:
        r.update(tf_feats(dd.iloc[-WIN:], "D", has_vol))
        r.update(tf_feats(blocks(dd, 5).iloc[-WIN:], "W", has_vol))
    r.update(align(r))
    return r


# ---------------- popülasyonlar ----------------
def paket_trades() -> pd.DataFrame:
    I = pd.read_parquet(ROOT / "research/xp_gelistir_20261119/results/islemler.parquet")
    P = I[~I.opex_k.isin([0, 1, 2]) & (I.d <= CUT)].copy()
    return P[["besleme", "d", "net", "donem", "cikis", "tutus_gun"]].reset_index(drop=True)


def load_feed(name: str) -> tuple[pd.DataFrame, bool]:
    import ozellik as O
    if name == "DUKA_NDX":
        b = O.duka_30m()
        has_vol = False
    else:
        b = O.load_market(name.replace("MT5_", ""))
        has_vol = True
    b = b.copy()
    b["t"] = (b.t // 1800) * 1800
    b = b.drop_duplicates("t").sort_values("t").reset_index(drop=True)
    b = b[b.t < entry_ts(CUT + pd.Timedelta(days=1))].reset_index(drop=True)
    return b, has_vol


def _feed_job(name: str) -> pd.DataFrame:
    P = paket_trades()
    P = P[P.besleme == name]
    b, hv = load_feed(name)
    daily = rth_daily(b)
    rows = []
    for _, t in P.iterrows():
        r = feed_trade_feats(b, daily, pd.Timestamp(t.d), hv)
        rows.append({"besleme": name, "d": t.d, **r})
    return pd.DataFrame(rows)


def cag_trades(sym: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """ETF V1 vekili + OPEX vetosu + XP, 1993–2017."""
    import ka
    sys.path.insert(0, str(ROOT / "research/son_rapor_20261118/src"))
    import rapor as R
    import lib
    d = pd.read_parquet(ka.D / f"{sym}.parquet")
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    x = pd.DataFrame({"o": d.Open, "h": d.High, "l": d.Low, "c": d.Close, "v": d.Volume.astype(float)}).dropna()
    x = x[x.index <= CUT]
    v1 = (x.c <= (x.h + x.l) / 2 * 0.995) & (x.c < x.o)
    k, _ = R.cycle(R.trading_calendar())
    kk = k.reindex(x.index).values
    c, idx = x.c.values, x.index
    rows = []
    for i in np.flatnonzero(v1.values):
        if idx[i] > pd.Timestamp("2017-12-31") or kk[i] in (0, 1, 2) or i + 1 >= len(c):
            continue
        prev, j = c[i], None
        for jj in range(i + 1, min(i + 6, len(c))):
            if c[jj] > prev or jj == min(i + 5, len(c) - 1):
                j = jj
                break
            prev = c[jj]
        net = (c[j] / c[i] - 1) * 1e4 - 2 - lib.FIN_BP_PER_DAY * (idx[j] - idx[i]).days
        rows.append({"besleme": f"ETF_{sym}", "d": idx[i], "net": net, "tutus_gun": j - i})
    return pd.DataFrame(rows), x


def _cag_job(sym: str) -> pd.DataFrame:
    T, x = cag_trades(sym)
    rows = []
    for _, t in T.iterrows():
        r = feed_trade_feats(None, x, pd.Timestamp(t.d), True, intraday=False)
        rows.append({**t.to_dict(), **r})
    return pd.DataFrame(rows)


# ---------------- testler ----------------
def unit_tests() -> None:
    z, s, r2, w = linreg(np.arange(1, 21, dtype=float))
    assert abs(r2 - 1) < 1e-12 and abs(s - 1 / 20 * 1e4) < 1e-9
    b = pd.DataFrame({"o": np.arange(10.0), "h": np.arange(10.0) + 1, "l": np.arange(10.0) - 1, "c": np.arange(10.0) + 0.5, "v": np.ones(10)})
    k = blocks(b, 4)
    assert len(k) == 2 and k.c.iloc[-1] == 9.5 and k.o.iloc[0] == 2.0 and k.v.iloc[-1] == 4
    # sızıntı: girişten sonraki veriyi silince aynı özellikler çıkmalı
    b30, hv = load_feed("MT5_NAS100")
    daily = rth_daily(b30)
    P = paket_trades()
    for d in P[P.besleme == "MT5_NAS100"].d.sample(3, random_state=1):
        d = pd.Timestamp(d)
        full = feed_trade_feats(b30, daily, d, hv)
        cut = b30[b30.t < entry_ts(d)]
        part = feed_trade_feats(cut, rth_daily(cut), d, hv)
        diff = [kk for kk in full if not (np.isclose(full[kk], part.get(kk, np.nan), equal_nan=True))]
        assert not diff, f"sızıntı {d.date()}: {diff[:5]}"
        assert len(full) > 500, len(full)
    print("birim + sızıntı testleri geçti; özellik sayısı", len(full))


def main() -> None:
    RES.mkdir(exist_ok=True)
    feeds = ["MT5_NAS100", "MT5_US500", "MT5_US30", "MT5_US2000", "DUKA_NDX"]
    syms = ["QQQ", "SPY", "DIA", "IWM"]
    with ProcessPoolExecutor(max_workers=6) as ex:
        fp = list(ex.map(_feed_job, feeds))
        cp = list(ex.map(_cag_job, syms))
    P = paket_trades().merge(pd.concat(fp, ignore_index=True), on=["besleme", "d"], how="left")
    P.to_parquet(RES / "paket_ozellik.parquet")
    C = pd.concat(cp, ignore_index=True)
    C.to_parquet(RES / "cag_ozellik.parquet")
    print("paket", P.shape, "ÇAĞ", C.shape, "ÇAĞ kaybeden %", round(float((C.net < 0).mean() * 100), 1))


if __name__ == "__main__":
    unit_tests() if sys.argv[1] == "test" else main()
