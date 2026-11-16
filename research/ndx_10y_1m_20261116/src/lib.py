"""lib.py — NDX 9y 1m araştırma katmanı: veri, saat, maliyet, istatistik (PROTOCOL.md §0–§1).

Tek kaynak: research/nom_20261113/data/ndx_1m_v3_duka.parquet (Dukascopy BID 1m, 2018-01 → 2026-11, spr = ask − bid modeli).
Tüm karar saatleri America/New_York; NYSE takvimi backend/services/nom/nyse_calendar.py.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
CACHE = HERE / "cache"
RESULTS = HERE / "results"
SRC_1M = ROOT / "research/nom_20261113/data/ndx_1m_v3_duka.parquet"
MACRO = ROOT / "research/nom_20261113/data/macro/macro_daily.parquet"
CAL = ROOT / "research/nom_20261113/data/macro/calendar.parquet"
QS_DATA = ROOT / "research/qs03_akis_takvim_20261111/data"
sys.path.insert(0, str(ROOT / "backend"))
from services.nom import nyse_calendar as nyse  # noqa: E402

NY = ZoneInfo("America/New_York")
ESKI_END = date(2021, 10, 31)          # ESKİ = 2018-01-01 → 2021-10-31 (yeni 1m dilim)
FIN_BP_PER_DAY = 6.41 / 365 * 100      # ≈ 1,756 bp/takvim günü uzun finansman (FR-18 NAS100 swap)
MIN = 60


def era(d: date) -> str:
    return "ESKI" if d <= ESKI_END else "YENI"


# ═══════════════════════════ 1m veri ═══════════════════════════

@dataclass
class M1:
    t: np.ndarray        # UTC epoch, bar açılışı
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    spr: np.ndarray
    d: np.ndarray        # NY tarihi (datetime64[D])
    m: np.ndarray        # NY gün dakikası (0..1439)
    _ix: dict = field(default_factory=dict, repr=False)

    def idx_at(self, t_utc: int) -> int | None:
        """t_utc'de AÇILAN 1m barın indeksi; yoksa None."""
        i = int(np.searchsorted(self.t, t_utc))
        return i if i < len(self.t) and self.t[i] == t_utc else None

    def idx_from(self, t_utc: int, tol_s: int = 300) -> int | None:
        """t_utc'de veya sonraki tol_s içinde açılan ilk bar (eksik dakikaya tolerans)."""
        i = int(np.searchsorted(self.t, t_utc))
        return i if i < len(self.t) and self.t[i] - t_utc <= tol_s else None

    def last_before(self, t_utc: int, tol_s: int = 300) -> int | None:
        """Açılışı < t_utc olan son bar (kapanışı t_utc'den önce/anında), en çok tol_s eski."""
        i = int(np.searchsorted(self.t, t_utc)) - 1
        return i if i >= 0 and t_utc - (self.t[i] + MIN) <= tol_s else None


def load_m1() -> M1:
    CACHE.mkdir(exist_ok=True)
    cp = CACHE / "m1_ny.parquet"
    if cp.exists():
        df = pd.read_parquet(cp)
    else:
        df = pd.read_parquet(SRC_1M, columns=["t", "open", "high", "low", "close", "spr"]).sort_values("t")
        df = df.drop_duplicates("t").reset_index(drop=True)
        ts = pd.to_datetime(df.t, unit="s", utc=True).dt.tz_convert(NY)
        df["d"] = ts.dt.tz_localize(None).dt.normalize().values.astype("datetime64[D]")
        df["m"] = (ts.dt.hour * 60 + ts.dt.minute).astype(np.int16)
        df.to_parquet(cp)
    return M1(df.t.values.astype(np.int64), df.open.values, df.high.values, df.low.values, df.close.values,
              df.spr.values, df.d.values.astype("datetime64[D]"), df.m.values.astype(np.int16))


def utc(d: date, minute: int) -> int:
    """NY yerel (tarih, gün dakikası) → UTC epoch."""
    extra, minute = divmod(minute, 24 * 60)
    d = d + timedelta(days=extra)
    dt = datetime(d.year, d.month, d.day, minute // 60, minute % 60, tzinfo=NY)
    return int(dt.timestamp())


def trading_days(m1: M1) -> list[date]:
    """Verinin kapsadığı NYSE işlem günleri (hafta içi, tatil değil)."""
    d0 = pd.Timestamp(m1.d[0]).date()
    d1 = pd.Timestamp(m1.d[-1]).date()
    out, d = [], d0
    while d <= d1:
        if d.weekday() < 5 and not nyse.is_holiday(d):
            out.append(d)
        d += timedelta(days=1)
    return out


# ═══════════════════════════ günlük tablo ═══════════════════════════

def daily_table(m1: M1) -> pd.DataFrame:
    """İşlem günü başına RTH ölçüleri (yalnız karar için gereken saat damgaları; hepsi o günün içinden)."""
    cp = CACHE / "daily.parquet"
    if cp.exists():
        return pd.read_parquet(cp)
    rows = []
    for d in trading_days(m1):
        close_m = nyse.cash_close_minutes(d)
        a, b = int(np.searchsorted(m1.t, utc(d, 0))), int(np.searchsorted(m1.t, utc(d, 24 * 60)))
        if b - a < 100:
            continue
        mm, o, h, l, c, sp = m1.m[a:b], m1.o[a:b], m1.h[a:b], m1.l[a:b], m1.c[a:b], m1.spr[a:b]

        def at(minute: int, arr: np.ndarray) -> float:
            k = np.searchsorted(mm, minute)
            return float(arr[k]) if k < len(mm) and mm[k] - minute <= 5 else np.nan

        def before(minute: int) -> float:      # bitişi ≤ minute olan son barın kapanışı (≤5 dk eski)
            k = np.searchsorted(mm, minute) - 1
            return float(c[k]) if k >= 0 and minute - (mm[k] + 1) <= 5 else np.nan

        r930 = (mm >= 570) & (mm < close_m)
        r900 = (mm >= 540) & (mm < close_m)
        rows.append({
            "d": d, "early": nyse.is_early_close(d), "n_rth": int(r930.sum()),
            "open930": at(570, o), "close": before(close_m),
            "low900": float(l[r900].min()) if r900.any() else np.nan,
            "high930": float(h[r930].max()) if r930.any() else np.nan,
            "low930": float(l[r930].min()) if r930.any() else np.nan,
            "S": before(930), "E": at(930, o), "O15": at(900, o), "O1430": at(870, o), "O1530": at(930, o),
            "O16": at(960, o), "c1600": before(960), "O1630": at(990, o), "O1000": at(600, o),
            "spr930": at(930, sp), "spr960": at(960, sp), "spr570": at(570, sp), "spr990": at(990, sp),
        })
    df = pd.DataFrame(rows)
    df["full"] = (~df.early) & (df.n_rth >= 0.9 * 390)
    df.to_parquet(cp)
    return df


def vix_prev_map(days: list[date]) -> dict[date, float]:
    """Her gün için o günden ÖNCEKİ son VIX kapanışı (kart: 'dünkü VIX')."""
    mac = pd.read_parquet(MACRO)[["date", "VIX_close"]].dropna()
    mac["date"] = pd.to_datetime(mac.date).dt.date
    vd, vv = mac.date.values, mac.VIX_close.values
    out = {}
    for d in days:
        k = np.searchsorted(vd, d) - 1
        if k >= 0:
            out[d] = float(vv[k])
    return out


def fomc_days() -> set[date]:
    c = pd.read_parquet(CAL)
    return set(pd.to_datetime(c.loc[c.event == "FOMC", "date"]).dt.date)


def etf(name: str) -> pd.Series:
    s = pd.read_parquet(QS_DATA / f"{name}.parquet")["Adj Close"]
    s.index = pd.to_datetime(s.index).date
    return s


# ═══════════════════════════ işlem ve istatistik ═══════════════════════════

@dataclass
class Trade:
    rule: str
    d: date                  # karar/giriş günü (NY)
    t_in: int
    t_out: int
    side: int                # +1 uzun, −1 kısa
    px_in: float             # icra fiyatı (spread dahil)
    px_out: float
    risk: float = np.nan     # fiyat birimi (R ölçüsü için); nan → bp kuralı
    lot: float = 1.0
    spr_in: float = 0.0
    spr_out: float = 0.0
    mae: float = 0.0         # en kötü seyir, giriş fiyatına oranla (negatif)
    why: str = ""
    tags: dict = field(default_factory=dict)

    def nights(self) -> int:
        return max(0, (pd.Timestamp(self.t_out, unit="s").date() - pd.Timestamp(self.t_in, unit="s").date()).days)

    def gross_bp(self) -> float:
        return self.side * (self.px_out / self.px_in - 1) * 1e4

    def fin_bp(self) -> float:
        return FIN_BP_PER_DAY * self.nights() if self.side > 0 else 0.0

    def net_bp(self, spr_mult: float = 1.0) -> float:
        extra = (spr_mult - 1.0) * (self.spr_in + self.spr_out) / self.px_in * 1e4
        return self.gross_bp() - self.fin_bp() - extra

    def R(self, spr_mult: float = 1.0) -> float:
        if not np.isfinite(self.risk) or self.risk <= 0:
            return np.nan
        return self.net_bp(spr_mult) / 1e4 * self.px_in / self.risk


def walk(m1: M1, i0: int, t_end: int, side: int, stop: float | None, tp: float | None) -> tuple[int, float, str, float]:
    """i0 barından (dahil) itibaren t_end'e kadar yürü. BID fiyatlarla: uzunda low ≤ stop → stop, high ≥ tp → tp,
    aynı barda ikisi → stop. Döner (çıkış bar indeksi, çıkış BID fiyatı, neden, MAE oranı). Zaman çıkışında
    t_end'de açılan barın açılışı (yoksa son barın kapanışı)."""
    j_end = int(np.searchsorted(m1.t, t_end))
    entry_ref = m1.o[i0]
    mae = 0.0
    for j in range(i0, min(j_end, len(m1.t))):
        lo, hi = m1.l[j], m1.h[j]
        if side > 0:
            mae = min(mae, lo / entry_ref - 1)
            hit_s = stop is not None and lo <= stop
            hit_t = tp is not None and hi >= tp
            if hit_s:
                return j, min(stop, m1.o[j]), "stop", mae
            if hit_t:
                return j, max(tp, m1.o[j]) if m1.o[j] > tp else tp, "tp", mae
        else:
            a_hi, a_lo = hi + m1.spr[j], lo + m1.spr[j]
            mae = min(mae, -(a_hi / entry_ref - 1))
            hit_s = stop is not None and a_hi >= stop
            hit_t = tp is not None and a_lo <= tp
            if hit_s:
                return j, max(stop, m1.o[j] + m1.spr[j]), "stop", mae
            if hit_t:
                return j, tp, "tp", mae
    k, px = exit_px(m1, t_end, side)
    return k, px, "time", mae


def exit_px(m1: M1, t: int, side: int, tol_s: int = 300) -> tuple[int, float]:
    """t anındaki çıkış fiyatı: t'de (≤ tol_s sonra) açılan barın açılışı; yoksa t'den önceki son barın kapanışı
    (Dukascopy 16:15–18:00 ET boşluğu, eksik dakika). Uzunda BID, kısada ask."""
    k = m1.idx_from(t, tol_s)
    if k is not None:
        return k, (m1.o[k] if side > 0 else m1.o[k] + m1.spr[k])
    k = int(np.searchsorted(m1.t, t)) - 1
    return k, (m1.c[k] if side > 0 else m1.c[k] + m1.spr[k])


def entry_ix(m1: M1, t: int, tol_s: int = 300) -> tuple[int | None, float]:
    """t anındaki giriş: t'de açılan barın açılışı, yoksa önceki son barın kapanışı (≤ 15 dk eski). (indeks, BID fiyat)."""
    k = m1.idx_from(t, tol_s)
    if k is not None:
        return k, m1.o[k]
    k = int(np.searchsorted(m1.t, t)) - 1
    if k >= 0 and t - (m1.t[k] + MIN) <= 900:
        return k + 1, m1.c[k]          # yol k+1'den başlar (giriş barın kapanışında)
    return None, np.nan


def time_trade(m1: M1, rule: str, d: date, t_in: int, t_out: int, side: int, tol_s: int = 300, **tags) -> Trade | None:
    """Zaman girişli/çıkışlı (stopsuz) işlem: t_in'de açılan barın açılışı + spread, t_out'ta açılan barın açılışı."""
    i, bid_in = entry_ix(m1, t_in, tol_s)
    if i is None or i >= len(m1.t):
        return None
    k, pout = exit_px(m1, t_out, side, tol_s)
    if k <= i:
        return None
    spi, spo = m1.spr[min(i, len(m1.t) - 1)], m1.spr[k]
    pin = bid_in + spi if side > 0 else bid_in
    seg_l, seg_h = m1.l[i:k].min(), m1.h[i:k].max()
    mae = (seg_l / pin - 1) if side > 0 else -((seg_h + spo) / pin - 1)
    return Trade(rule, d, int(m1.t[i]), int(m1.t[k]), side, pin, pout, spr_in=spi, spr_out=spo, mae=mae, tags=tags)


def to_frame(trades: list[Trade]) -> pd.DataFrame:
    rows = []
    for x in trades:
        rows.append({"rule": x.rule, "d": x.d, "era": era(x.d), "year": x.d.year, "side": x.side, "t_in": x.t_in,
                     "t_out": x.t_out, "px_in": x.px_in, "px_out": x.px_out, "risk": x.risk, "lot": x.lot,
                     "gross_bp": x.gross_bp(), "net_bp": x.net_bp(), "net_bp_s15": x.net_bp(1.5),
                     "R": x.R(), "R_s15": x.R(1.5), "mae": x.mae, "why": x.why, **x.tags})
    return pd.DataFrame(rows)


def block_boot_p(vals: np.ndarray, months: np.ndarray, n_boot: int = 4000, seed: int = 7) -> float:
    """Ay-blok bootstrap P(ortalama > 0)."""
    vals = np.asarray(vals, float)
    ok = np.isfinite(vals)
    vals, months = vals[ok], np.asarray(months)[ok]
    if len(vals) < 3:
        return np.nan
    um = np.unique(months)
    groups = [vals[months == u] for u in um]
    rng = np.random.default_rng(seed)
    sums = np.array([g.sum() for g in groups])
    cnts = np.array([len(g) for g in groups])
    pick = rng.integers(0, len(um), size=(n_boot, len(um)))
    means = sums[pick].sum(1) / cnts[pick].sum(1)
    return float((means > 0).mean())


def summarize(df: pd.DataFrame, col: str) -> dict:
    """n, ort, medyan, isabet, P, yarılar, s×1,5, en iyi 5 hariç, en kötü — tek sütun üzerinden."""
    if df.empty:
        return {"n": 0}
    v = df[col].values.astype(float)
    mo = pd.to_datetime(df.d).dt.to_period("M").astype(str).values
    s15 = df[col + "_s15"].values if col + "_s15" in df else v
    order = np.argsort(df.t_in.values)
    h = len(v) // 2
    top5 = np.sort(v)[-5:].sum() if len(v) > 5 else np.nan
    return {"n": int(len(v)), "mean": float(np.nanmean(v)), "median": float(np.nanmedian(v)),
            "hit": float(np.nanmean(v > 0)), "P": block_boot_p(v, mo), "sum": float(np.nansum(v)),
            "h1": float(np.nanmean(v[order[:h]])) if h else np.nan, "h2": float(np.nanmean(v[order[h:]])) if h else np.nan,
            "mean_s15": float(np.nanmean(s15)), "ex_top5": float((np.nansum(v) - top5) / max(1, len(v) - 5)),
            "worst": float(np.nanmin(v)), "mae_p05": float(np.nanpercentile(df.mae.values, 5)) if "mae" in df else np.nan,
            "mae_min": float(np.nanmin(df.mae.values)) if "mae" in df else np.nan}


def by_era_year(df: pd.DataFrame, col: str) -> dict:
    out = {"TUM": summarize(df, col)}
    for e in ("ESKI", "YENI"):
        out[e] = summarize(df[df.era == e], col)
    out["yil"] = {int(y): {"n": int(len(g)), "mean": float(g[col].mean()), "sum": float(g[col].sum())}
                  for y, g in df.groupby("year")}
    return out
