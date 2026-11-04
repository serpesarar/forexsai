"""dv_core.py — (f) "kapanış baskısı dönüşü" doğrulaması için ortak çekirdek (PROTOCOL.md §1–§6).

Tanımlar `capali/capali_ek.py` (tf = "1h", "(f) tanımsal") ile birebir:
  son saat  rl = 100·(px(D 16:00)/px(D 15:00) − 1)        (NY)
  gece      on = px(D+1 09:00) − px(D 16:00)  [puan], on% = 100·on/px(D 16:00)
  dahil     ¬early[i] ∧ ¬early[i−1], rl ≠ 0, on ≠ 0
  bootstrap 5 ardışık işlem günlük bloklar (⌊i/5⌋), iadeli, oran-of-toplamlar.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RES = HERE / "results"
NY = ZoneInfo("America/New_York")
BER = ZoneInfo("Europe/Berlin")
HOLD = pd.Timestamp("2025-12-01", tz="UTC")
L1H = ROOT / "research/ndx_gate_forge/data/long_1h_utc.parquet"
B15 = ROOT / "research/ndx_pattern_motifs/data/bars_15m.parquet"
B1M = ROOT / "research/ndx_pattern_motifs/data/bars_1m.parquet"
DAX30 = ROOT / "research/ndx_gate_forge/data/dax_30m.parquet"
DAX1H = ROOT / "research/ndx_gate_forge/data/dax_1h.parquet"
DAILY = ROOT / "research/ndx_gate_forge/data/macro_daily_patched.csv"
NS_MIN = 60_000_000_000
Z_ALPHA, Z_POWER = 1.6449, 0.8416          # tek yönlü α = 0,05, güç 0,80
SEED = 20261013
B_BOOT = 10_000


# ───────────────────────── takvimler ─────────────────────────
def ny_calendar() -> pd.DataFrame:
    """NDXCASH O/H/L/C dolu günler + `early` (capali_veri.load_daily ile aynı kural) + QQQ sütunları."""
    d = pd.read_csv(DAILY, parse_dates=["date"])
    # §8 değişiklik 1 (sınama öncesi): takvim = NDXCASH_close dolu günler (O/H/L 2026-07-28'de bitiyor, kapanış 09-30'a
    # kadar var; 07-28'e kadar iki tanım birebir aynı gün kümesini veriyor — dv_0 denetler). (f) yalnız gün listesini kullanır.
    d["ohlc_ok"] = d[["NDXCASH_open", "NDXCASH_high", "NDXCASH_low", "NDXCASH_close"]].notna().all(axis=1)
    d = d.dropna(subset=["NDXCASH_close"])
    d = d.sort_values("date").reset_index(drop=True)
    dn = d.date.values.astype("datetime64[D]").astype(np.int64)
    s = set(dn.tolist())
    md, wd, dd = d.date.dt.month, d.date.dt.weekday, d.date.dt.day
    bf = (md == 11) & (wd == 4) & dd.between(23, 29) & ~pd.Series(dn - 1).isin(s)
    d["early"] = (bf | ((md == 12) & (dd == 24)) | ((md == 7) & (dd == 3))).to_numpy(bool)
    d["d"] = d.date.dt.date
    return d


def easter(y: int) -> date:
    """Anonim Gregoryen algoritma (Meeus/Jones/Butcher)."""
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    L = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * L) // 451
    mo = (h + L - 7 * m + 114) // 31
    da = (h + L - 7 * m + 114) % 31 + 1
    return date(y, mo, da)


def xetra_days(first: date, last: date) -> list[date]:
    """Berlin Pzt–Cum, Xetra tatilleri hariç (1 Oca, Kutsal Cuma, Paskalya Pzt, 1 May, 24/25/26/31 Ara)."""
    out, cur = [], first
    while cur <= last:
        if cur.weekday() < 5:
            e = easter(cur.year)
            hol = {date(cur.year, 1, 1), e - timedelta(days=2), e + timedelta(days=1), date(cur.year, 5, 1),
                   date(cur.year, 12, 24), date(cur.year, 12, 25), date(cur.year, 12, 26), date(cur.year, 12, 31)}
            if cur not in hol:
                out.append(cur)
        cur += timedelta(days=1)
    return out


def t_ns(d: date, hh: int, mm: int, tz: ZoneInfo) -> int:
    return int(pd.Timestamp(datetime(d.year, d.month, d.day, hh, mm, tzinfo=tz)).value)


# ───────────────────────── bar kaynakları ─────────────────────────
class Px:
    """px(t) = bitişi TAM t olan barın kapanışı (yoksa NaN)."""

    def __init__(self, ts: pd.Series, close: np.ndarray, minutes: int, valid: np.ndarray | None = None):
        st = ts.values.astype("datetime64[ns]").astype(np.int64)
        c = np.asarray(close, float)
        if valid is not None:
            st, c = st[valid], c[valid]
        o = np.argsort(st)
        self.en = st[o] + minutes * NS_MIN
        self.c = c[o]

    def __call__(self, t: int) -> float:
        i = int(np.searchsorted(self.en, t))
        if i < len(self.en) and self.en[i] == t:
            return float(self.c[i])
        return float("nan")


def load_long1h(before: pd.Timestamp | None = None) -> pd.DataFrame:
    d = pd.read_parquet(L1H)
    if before is not None:
        d = d[d.ts < before]
    return d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def agg_15m_to_1h(d15: pd.DataFrame) -> pd.DataFrame:
    """Saat başı UTC kovası; geçerli ⇔ kovanın :45 barı mevcut (kapanış = saat sonundaki gerçek fiyat)."""
    d = d15.sort_values("ts").drop_duplicates("ts").copy()
    d["h"] = d.ts.dt.floor("h")
    d["m45"] = d.ts.dt.minute == 45
    g = d.groupby("h")
    a = g.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"),
              n=("ts", "size"), last45=("m45", "max")).reset_index().rename(columns={"h": "ts"})
    # 'last' kapanış :45 barınınki olmalı: sıralı olduğu için :45 varsa sondadır
    return a


def fix_dax_axis(d: pd.DataFrame) -> pd.DataFrame:
    """NY standart saatindeyken etiket 60 dk erken → +60 dk (caprev_dax_recheck/fix_data.py ile aynı kural)."""
    d = d.copy()
    cand = d.ts + pd.Timedelta(minutes=60)
    loc = cand.dt.tz_convert("America/New_York").dt.tz_localize(None)
    off_h = (loc - cand.dt.tz_localize(None)) / pd.Timedelta(hours=1)
    std = (off_h == -5).to_numpy()
    d["ts"] = np.where(std, cand, d.ts)
    d["ts"] = pd.to_datetime(d.ts, utc=True)
    return d.sort_values("ts").drop_duplicates("ts", keep="last").reset_index(drop=True)


# ───────────────────────── gece tabloları ─────────────────────────
def ndx_nights(cal: pd.DataFrame, px: Px, d_from: date, d_to: date) -> pd.DataFrame:
    """§1 tanımı; plasebo saati (11:00→12:00 NY) de eklenir. Dönen tablo yalnız geçerli geceler (rl≠0, on≠0)."""
    days, early = cal.d.tolist(), cal.early.to_numpy(bool)
    rows = []
    for i in range(1, len(days) - 1):
        D = days[i]
        if D < d_from or D > d_to or early[i] or early[i - 1]:
            continue
        Dn = days[i + 1]
        rows.append((i, D, Dn, px(t_ns(D, 15, 0, NY)), px(t_ns(D, 16, 0, NY)), px(t_ns(Dn, 9, 0, NY)),
                     px(t_ns(D, 11, 0, NY)), px(t_ns(D, 12, 0, NY))))
    return _finish(pd.DataFrame(rows, columns=["i", "D", "Dn", "pa", "pc", "pn", "q0", "q1"]))


def dax_nights(xdays: list[date], px: Px, d_from: date, d_to: date, a: tuple[int, int], c: tuple[int, int]) -> pd.DataFrame:
    """a = son-saat başlangıç sınırı, c = kapanış sınırı (Berlin). Gece c → sonraki Xetra günü 09:00."""
    rows = []
    for i in range(len(xdays) - 1):
        D = xdays[i]
        if D < d_from or D > d_to:
            continue
        Dn = xdays[i + 1]
        rows.append((i, D, Dn, px(t_ns(D, *a, BER)), px(t_ns(D, *c, BER)), px(t_ns(Dn, 9, 0, BER)),
                     px(t_ns(D, 11, 0, BER)), px(t_ns(D, 12, 0, BER))))
    return _finish(pd.DataFrame(rows, columns=["i", "D", "Dn", "pa", "pc", "pn", "q0", "q1"]))


def _finish(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df["rl"] = 100 * (df.pc / df.pa - 1)
    df["on"] = df.pn - df.pc
    df["onp"] = 100 * df.on / df.pc
    df["rp"] = 100 * (df.q1 / df.q0 - 1)
    ok = np.isfinite(df.rl) & np.isfinite(df.on) & (df.rl != 0) & (df.on != 0)
    df.attrs["n_aday"] = int(len(df))
    out = df[ok].reset_index(drop=True)
    out.attrs["n_aday"] = int(len(df))
    return out


def qqq_nights(cal: pd.DataFrame, d_from: date, d_to: date) -> pd.DataFrame:
    q = cal.dropna(subset=["QQQ_open", "QQQ_high", "QQQ_low", "QQQ_close"]).reset_index(drop=True)
    early = q.early.to_numpy(bool)
    rows = []
    for i in range(1, len(q) - 1):
        D = q.d[i]
        if D < d_from or D > d_to or early[i] or early[i - 1]:
            continue
        H, L, C, On = q.QQQ_high[i], q.QQQ_low[i], q.QQQ_close[i], q.QQQ_open[i + 1]
        if not H > L:
            continue
        rows.append((i, D, q.d[i + 1], (C - L) / (H - L) - 0.5, On - C, 100 * (On / C - 1)))
    df = pd.DataFrame(rows, columns=["i", "D", "Dn", "rl", "on", "onp"])
    df = df[(df.rl != 0) & (df.on != 0)].reset_index(drop=True)
    df["rp"] = np.nan
    return df


# ───────────────────────── istatistik ─────────────────────────
def _block_sums(blk: np.ndarray, mask: np.ndarray, v: np.ndarray, nb: int) -> tuple[np.ndarray, np.ndarray]:
    return (np.bincount(blk, weights=np.where(mask, v, 0.0), minlength=nb),
            np.bincount(blk, weights=mask.astype(float), minlength=nb))


def boot_specs(i_day: np.ndarray, specs: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]],
               B: int = B_BOOT, seed: int = SEED) -> dict[str, np.ndarray]:
    """specs[ad] = (maske_A, maske_B, değer). Tüm spec'ler AYNI blok çekilişini kullanır (eşli kıyas için).
    Dönen: ad → B uzunlukta (ort_A − ort_B) dağılımı."""
    _, blk = np.unique(i_day // 5, return_inverse=True)
    nb = int(blk.max()) + 1
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, nb, (B, nb))
    out = {}
    for k, (ma, mb, v) in specs.items():
        sa, na = _block_sums(blk, ma, v, nb)
        sb, nbb = _block_sums(blk, mb, v, nb)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[k] = sa[pick].sum(1) / na[pick].sum(1) - sb[pick].sum(1) / nbb[pick].sum(1)
    return out


def describe(df: pd.DataFrame, cond: str = "rl") -> dict:
    """Koşul işaretine göre (aşağı < 0 / yukarı > 0) gece istatistikleri, noktasal."""
    dn = (df[cond] < 0).to_numpy()
    up = (df[cond] > 0).to_numpy()
    on, onp = df.on.to_numpy(), df.onp.to_numpy()
    r = dict(n=int(dn.sum() + up.sum()), n_asagi=int(dn.sum()), n_yukari=int(up.sum()),
             gun_ilk=str(df.D.min()) if len(df) else None, gun_son=str(df.D.max()) if len(df) else None)
    for nm, v in (("pts", on), ("pct", onp), ("up", (on > 0).astype(float) * 100)):
        a, b = float(v[dn].mean()) if dn.any() else np.nan, float(v[up].mean()) if up.any() else np.nan
        r[f"{nm}_asagi"], r[f"{nm}_yukari"], r[f"{nm}_fark"] = a, b, a - b
        r[f"{nm}_kosulsuz"] = float(v[dn | up].mean())
    r["sd_pct_tum"] = float(onp[dn | up].std(ddof=1))
    return r


def boot_summary(x: np.ndarray, thr: float | None = None) -> dict:
    x = x[np.isfinite(x)]
    sd = float(x.std(ddof=1))
    r = dict(P=float(np.mean(x > 0)), sd_boot=sd, q05=float(np.quantile(x, 0.05)), q95=float(np.quantile(x, 0.95)),
             MDE80=(Z_ALPHA + Z_POWER) * sd)
    if thr is not None:
        r["esik"] = thr
    return r


def verdict(point: float, bs: dict, thr: float) -> str:
    if bs["P"] >= 0.95 and point >= thr:
        return "GEÇER"
    if bs["q95"] < thr:
        return "ÇÜRÜTÜLDÜ"
    return "SONUÇSUZ"
