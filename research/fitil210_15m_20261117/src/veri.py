"""veri.py — yol barları (1m Dukascopy / 15m MT5), 15m ve 210m mum kurma, 210m olay tablosu (PROTOCOL §1).

Saat: tüm `t` UTC epoch (bar açılışı). İşlem günü NY 17:00 çapası; 210m dilimleri 17:00, 20:30, 00:00, 03:30, 07:00, 10:30, 14:00 ET.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
RESULTS = HERE / "results"
CACHE = HERE / "cache"
sys.path.insert(0, str(ROOT / "research/ndx_10y_1m_20261116/src"))
sys.path.insert(0, str(ROOT / "research/ndx_tf_yapilandirma_20261117/src"))
import lib  # noqa: E402  (M1 yükleyici, Trade, summarize, block_boot_p)

TFY = ROOT / "research/ndx_tf_yapilandirma_20261117"
DUKA_210 = TFY / "out/DUKA/NDX_DUKA_210m.parquet"
KUTU = TFY / "out/kutu_taze"
NY = "America/New_York"
ANCHOR_MIN = 17 * 60          # işlem günü başlangıcı NY 17:00
SLOT_MIN = 210
N_SLOTS = 7                   # 6 × 210 + 1 × 180 = 1440
M15_SEC = 900
MT5_POINT = 0.1


@dataclass
class PathBars:
    """TP/SL yolunun yürüdüğü barlar (1m ya da 15m). spr = ask − bid (fiyat birimi)."""
    t: np.ndarray
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    spr: np.ndarray
    step: int                 # bar süresi (sn)
    name: str

    def zero_spread(self) -> "PathBars":
        return PathBars(self.t, self.o, self.h, self.l, self.c, np.zeros_like(self.spr), self.step, self.name + "_iyimser")


def duka_path() -> PathBars:
    """ndx_tf_yapilandirma'nın birleşik Dukascopy 1m'i (ana + bi5 kuyruğu + M1 dışa aktarımı) — 210m dosyasıyla aynı kaynak.
    Dışa aktarım dakikalarında spread modeli yok → aynı NY saatinin medyan spread'i."""
    import kaynak
    d = kaynak.load_duka_1m().sort_values("t").reset_index(drop=True)
    hr = pd.to_datetime(d.t, unit="s", utc=True).dt.tz_convert(NY).dt.hour
    d["spr"] = d.spr.fillna(d.groupby(hr).spr.transform("median"))
    return PathBars(d.t.values.astype(np.int64), d.open.values, d.high.values, d.low.values, d.close.values,
                    d.spr.values.astype(float), 60, "DUKA_1m")


def mt5_frame(tf: str) -> pd.DataFrame:
    import kaynak  # research/ndx_tf_yapilandirma_20261117/src
    return kaynak.load_mt5_native(tf, folder=KUTU)


def mt5_path(tf: str = "M15") -> PathBars:
    d = mt5_frame(tf)
    step = {"M1": 60, "M15": 900}[tf]
    return PathBars(d.t.values.astype(np.int64), d.open.values, d.high.values, d.low.values, d.close.values,
                    np.nan_to_num(d.spr.values.astype(float), nan=1.0), step, f"MT5_{tf}")


def _ny_minute(t: np.ndarray) -> np.ndarray:
    ts = pd.to_datetime(t, unit="s", utc=True).tz_convert(NY)
    return (ts.hour * 60 + ts.minute).to_numpy().astype(np.int64)


def build_15m(p: PathBars) -> pd.DataFrame:
    """Yol barlarından 15m mum. NY ofseti tam saat olduğundan 15m kovası = UTC 900 sn tabanı.
    `tend` = kovadaki son yol barının kapanışı (karar anı)."""
    key = p.t - p.t % M15_SEC
    starts = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    ends = np.r_[starts[1:], len(key)] - 1
    df = pd.DataFrame({
        "t": key[starts], "open": p.o[starts], "high": np.maximum.reduceat(p.h, starts),
        "low": np.minimum.reduceat(p.l, starts), "close": p.c[ends], "tend": p.t[ends] + p.step,
        "n": ends - starts + 1,
    })
    return _add_slot(df)


def _add_slot(df: pd.DataFrame) -> pd.DataFrame:
    md = (_ny_minute(df.t.values) - ANCHOR_MIN) % 1440
    slot = np.minimum(md // SLOT_MIN, N_SLOTS - 1)
    df["slot"] = slot
    df["b210"] = df.t.values - (md - slot * SLOT_MIN) * 60          # ait olduğu 210m mumun açılışı (UTC)
    return df


def build_210m(q: pd.DataFrame) -> pd.DataFrame:
    """15m'den 210m (14 × 15m; son dilim 12 × 15m). Yalnız aynı 210m kovasındaki 15m'ler birleşir. q t'ye göre sıralı, RangeIndex."""
    key = q.b210.values
    st = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    en = np.r_[st[1:], len(key)] - 1
    df = pd.DataFrame({
        "t": key[st], "open": q.open.values[st], "high": np.maximum.reduceat(q.high.values, st),
        "low": np.minimum.reduceat(q.low.values, st), "close": q.close.values[en], "tend": q.tend.values[en],
        "slot": q.slot.values[st], "n15": en - st + 1, "i_first": st, "i_last": en,
    })
    add_wicks(df)
    df["t_end_nom"] = df.t.values + np.where(df.slot.values < N_SLOTS - 1, SLOT_MIN, 1440 - (N_SLOTS - 1) * SLOT_MIN) * 60
    df["rng_pct"] = (df.high.values - df.low.values) / df.close.values * 100
    ts = pd.to_datetime(df.t, unit="s", utc=True).dt.tz_convert(NY)
    df["zaman_ny"] = ts
    df["year"] = ts.dt.year.values
    return df


def add_wicks(df: pd.DataFrame) -> pd.DataFrame:
    """alt fitil / üst fitil / gövde — fiyatın yüzdesi (alt: min(O,C) tabanlı, üst: max(O,C) tabanlı)."""
    bb = np.minimum(df.open.values, df.close.values)
    tt = np.maximum(df.open.values, df.close.values)
    df["lw_pct"] = (bb - df.low.values) / bb * 100
    df["uw_pct"] = (df.high.values - tt) / tt * 100
    df["gv_pct"] = (tt - bb) / bb * 100
    return df


def mt5_210m() -> pd.DataFrame:
    """Kullanıcının broker mumu: MT5 NAS100 210m (ndx_tf_yapilandirma, 2018-05 →; aynı NY 17:00 ızgarası)."""
    m = pd.read_parquet(TFY / "out/MT5/NDX_MT5_210m.parquet")
    return add_wicks(m)


def mt5_h4() -> pd.DataFrame:
    """Kullanıcının MT5 grafiğindeki H4 mumları (sunucu saati NY+7, 4 saatlik ızgara), H1'den. t = UTC açılış."""
    h = mt5_frame("H1")
    ny = pd.to_datetime(h.t, unit="s", utc=True).dt.tz_convert(NY)
    h["k"] = (ny.dt.tz_localize(None) + pd.Timedelta(hours=7)).dt.floor("4h")
    g = h.groupby("k").agg(t=("t", "first"), open=("open", "first"), high=("high", "max"), low=("low", "min"),
                           close=("close", "last"), n1h=("t", "size"))
    return add_wicks(g)


def h4_key(t_utc: np.ndarray) -> pd.DatetimeIndex:
    """UTC anını içeren MT5 H4 mumunun anahtarı (sunucu saati)."""
    ny = pd.to_datetime(t_utc, unit="s", utc=True).tz_convert(NY)
    return (ny.tz_localize(None) + pd.Timedelta(hours=7)).floor("4h")


def check_vs_file(b210: pd.DataFrame) -> dict:
    """Kendi 210m'imiz ↔ ndx_tf_yapilandirma DUKA 210m (ortak mumlarda OHLC)."""
    f = pd.read_parquet(DUKA_210)
    m = b210.merge(f[["t", "open", "high", "low", "close", "fitil_durumu", "kaynak_tf"]], on="t", suffixes=("", "_f"))
    m = m[m.kaynak_tf == "1m"]
    diff = np.abs(m[["open", "high", "low", "close"]].to_numpy() - m[["open_f", "high_f", "low_f", "close_f"]].to_numpy())
    return {"ortak": int(len(m)), "max_fark": float(diff.max()), "fark_0_olmayan": int((diff.max(1) > 1e-6).sum()),
            "supheli_t": set(f.loc[f.fitil_durumu == "eksik_dakika_supheli", "t"].astype(np.int64))}
