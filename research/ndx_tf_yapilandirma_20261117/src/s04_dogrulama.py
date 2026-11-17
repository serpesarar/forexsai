"""Adım 4 — bağımsız doğrulama. tf_motor'un gruplama kodunu KULLANMAZ.

İşlem günü sınırları burada ayrı yoldan kurulur: her takvim günü için 17:00 America/New_York
zoneinfo ile UTC'ye çevrilir (D dizisi); bir barın günü = searchsorted(D, t). Pencere
toplamları np.maximum/minimum.reduceat ile (pandas groupby değil).

V1 biçim     : OHLC tutarlılığı, sıra/duplike, ızgara (gün içi dakika % N), güne taşma yok
V2 kaynak    : her mum kaynak barlarından birebir yeniden hesaplanır (open/high/low/close/n);
               her kaynak barı tam bir muma düşer (bölüntü)
V3 hiyerarşi : 2m→6m = 3m→6m; 2m,3m→90m/210m = dosya; 90m→630 = 210m→630 (+180 kuyruk);
               1m/2m/3m/90m/210m → günlük OHLC hepsi aynı
V4 MT5 yerli : MT5'in kendi M5/M15/M30/H1 barları ile M1'den/birbirinden kurulan karşılıkları;
               90/210'un M1/M5/M15/M30'dan ayrı ayrı kurulmuş sürümleri birbirine eşit mi
V5 besleme   : DUKA ↔ MT5 90 dk getiri korelasyonu en iyi gecikme 0 mı (saat ekseni)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import kaynak as K  # noqa: E402
import s03_uret as U  # noqa: E402  (yalnız kaynak yükleyici/bölüntü — gruplama değil)

BASE = Path(__file__).resolve().parents[1]
NYZ = ZoneInfo("America/New_York")
TOL = 1e-9
REP: dict = {}
FAIL: list[str] = []


# ── bağımsız gün takvimi ───────────────────────────────────────────────────────
def day_starts(t_min: int, t_max: int) -> np.ndarray:
    d0 = datetime.fromtimestamp(t_min, timezone.utc).date() - timedelta(days=2)
    d1 = datetime.fromtimestamp(t_max, timezone.utc).date() + timedelta(days=2)
    out, d = [], d0
    while d <= d1:
        out.append(int(datetime(d.year, d.month, d.day, 17, 0, tzinfo=NYZ).timestamp()))
        d += timedelta(days=1)
    return np.array(out, dtype=np.int64)


class Cal:
    def __init__(self, t: np.ndarray):
        self.D = day_starts(int(t.min()), int(t.max()))

    def day_min(self, t: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        i = np.searchsorted(self.D, t, side="right") - 1
        return i, (t - self.D[i]) // 60

    def block(self, t: np.ndarray, b: int) -> np.ndarray:
        """b dk blok başlangıcı (gün başına sıfırlanan). 1440 % b ≠ 0 ise son blok kısadır."""
        i, m = self.day_min(t)
        return self.D[i] + (m // b) * b * 60


def regroup(df: pd.DataFrame, key: np.ndarray, trim: bool = True) -> pd.DataFrame:
    """Zaman sıralı barları ardışık anahtar bloklarına reduceat ile topla.

    trim: serinin ilk ve son bloğu atılır — verinin başı/sonu blok ortasına düşebilir (yarım blok),
    farklı zaman dilimleri farklı uç kırpar; uç dışındaki her blok tam karşılaştırılır.
    """
    if np.any(np.diff(key) < 0):
        raise AssertionError("anahtar sırası bozuk")
    starts = np.r_[0, np.flatnonzero(np.diff(key)) + 1]
    o, h, l, c = (df[k].to_numpy() for k in ("open", "high", "low", "close"))
    ends = np.r_[starts[1:], len(df)] - 1
    out = pd.DataFrame({"t": key[starts], "open": o[starts], "high": np.maximum.reduceat(h, starts),
                        "low": np.minimum.reduceat(l, starts), "close": c[ends],
                        "n": np.diff(np.r_[starts, len(df)])})
    if "vol" in df and df["vol"].notna().all():
        out["vol"] = np.add.reduceat(df["vol"].to_numpy(), starts)
    return out.iloc[1:-1].reset_index(drop=True) if trim else out


def compare(a: pd.DataFrame, b: pd.DataFrame, name: str, must: bool = True, vol: bool = False) -> dict:
    m = a.merge(b, on="t", suffixes=("_a", "_b"))
    cols = ["open", "high", "low", "close"] + (["vol"] if vol and "vol_a" in m and "vol_b" in m else [])
    if m.empty:
        r = {"ortak": 0}
    else:
        d = np.abs(np.column_stack([m[f"{c}_a"] - m[f"{c}_b"] for c in cols]))
        ok = d.max(axis=1) <= TOL
        r = {"ortak": int(len(m)), "birebir": int(ok.sum()), "birebir_%": round(100 * float(ok.mean()), 4),
             "max_fark": round(float(d.max()), 4)}
        if not ok.all():
            bad = m.loc[~ok, ["t"] + [f"{c}_{s}" for c in cols for s in "ab"]].head(5).copy()
            bad["t"] = pd.to_datetime(bad["t"], unit="s")
            r["ornek"] = bad.astype(str).to_dict("records")
    REP[name] = r
    if must and (r.get("ortak", 0) == 0 or r.get("birebir_%", 0) < 100):
        FAIL.append(name)
    print(f"{name:70s} {r.get('ortak'):>9} ortak  birebir %{r.get('birebir_%')}  max_fark {r.get('max_fark')}")
    return r


# ── V1 ─────────────────────────────────────────────────────────────────────────
def v1_format(df: pd.DataFrame, tf: int, cal: Cal, name: str) -> None:
    t = df["t"].to_numpy()
    o, h, l, c = (df[k].to_numpy() for k in ("open", "high", "low", "close"))
    _, m = cal.day_min(t)
    tail = 1440 - (1440 // tf) * tf
    sure = df["sure_dk"].to_numpy()
    exp_sure = np.where(m + tf > 1440, 1440 - m, tf)
    r = {
        "n": int(len(df)),
        "sira_duplike": int((np.diff(t) <= 0).sum()),
        "ohlc_ihlal": int(((h < np.maximum(o, c)) | (l > np.minimum(o, c)) | (h < l)).sum()),
        "nan": int(np.isnan(np.c_[o, h, l, c]).any(axis=1).sum()),
        "izgara_disi": int((m % tf != 0).sum()),
        "gune_tasan": int((m + sure > 1440).sum()),
        "sure_hatali": int((sure != exp_sure).sum()),
        "kisa_kuyruk_bar": int((sure < tf).sum()), "kuyruk_dk": tail,
        "fazla_alt_bar": int((df["n_alt"] > df["n_nominal"]).sum()),
        "eksik_alt_bar_%": round(100 * float((df["n_alt"] < df["n_nominal"]).mean()), 3),
    }
    bad = sum(r[k] for k in ("sira_duplike", "ohlc_ihlal", "nan", "izgara_disi", "gune_tasan", "sure_hatali",
                             "fazla_alt_bar"))
    REP[f"V1 {name}"] = r
    if bad:
        FAIL.append(f"V1 {name}")
    print(f"V1 {name:30s} {r}")


# ── V2 ─────────────────────────────────────────────────────────────────────────
def v2_from_source(out: pd.DataFrame, src: pd.DataFrame, cal: Cal, name: str) -> None:
    """Her mum: kaynakta [t, t+sure) penceresi → OHLC + n. Bölüntü: pencereler kaynak barlarını tam bir kez kapsar."""
    st = src["t"].to_numpy()
    t0 = out["t"].to_numpy()
    t1 = t0 + out["sure_dk"].to_numpy() * 60
    i0 = np.searchsorted(st, t0, "left")
    i1 = np.searchsorted(st, t1, "left")
    if np.any(i1 <= i0):
        FAIL.append(f"V2 {name} boş pencere")
    if np.any(i0[1:] < i1[:-1]):
        FAIL.append(f"V2 {name} pencere çakışması")
    # [i0, i1) pencereleri: aralıklı indeks dizisiyle reduceat, çift konumlar pencereleri verir
    h = np.r_[src["high"].to_numpy(), -np.inf]
    l = np.r_[src["low"].to_numpy(), np.inf]
    idx = np.c_[i0, i1].ravel()
    rec = pd.DataFrame({"t": t0, "open": src["open"].to_numpy()[i0], "close": src["close"].to_numpy()[i1 - 1],
                        "high": np.maximum.reduceat(h, idx)[::2], "low": np.minimum.reduceat(l, idx)[::2]})
    n_ok = np.array_equal(i1 - i0, out["n_alt"].to_numpy())
    covered = int((i1 - i0).sum())
    in_range = int(((st >= t0.min()) & (st < t1.max())).sum())
    REP[f"V2 {name} bölüntü"] = {"kaynak_bar_aralikta": in_range, "mumlara_dusen": covered, "n_alt_esit": n_ok}
    if covered != in_range or not n_ok:
        FAIL.append(f"V2 {name} bölüntü")
    print(f"V2 {name} bölüntü: aralıkta {in_range} kaynak bar, mumlara düşen {covered}, n_alt eşit {n_ok}")
    compare(out[["t", "open", "high", "low", "close"]], rec, f"V2 {name} kaynaktan yeniden hesap")


# ── V3 ─────────────────────────────────────────────────────────────────────────
def v3_hierarchy(feed: str, f: dict[int, pd.DataFrame], base: pd.DataFrame, cal: Cal) -> None:
    def up(df: pd.DataFrame, b: int) -> pd.DataFrame:
        return regroup(df, cal.block(df["t"].to_numpy(), b))

    compare(up(f[2], 6), up(f[3], 6), f"V3 {feed} 2m→6m = 3m→6m")
    for tf in (90, 210):
        lo, hi = f[2]["t"].min(), f[2]["t"].max()
        tgt = f[tf][(f[tf]["t"] >= lo) & (f[tf]["t"] + f[tf]["sure_dk"] * 60 <= hi + 120)]
        compare(tgt, up(f[2], tf), f"V3 {feed} 2m→{tf}m = {tf}m dosyası")
        compare(tgt, up(f[3], tf), f"V3 {feed} 3m→{tf}m = {tf}m dosyası")
    full = f.get("tam_dosya", f)
    compare(up(full[90], 630), up(full[210], 630), f"V3 {feed} 90m×7 = 210m×3 (630 dk blok + 180 kuyruk)")
    day = up(base, 1440)
    for tf in (2, 3, 90, 210):
        compare(day, up(f[tf], 1440), f"V3 {feed} {tf}m→gün = kaynak→gün")


# ── V4 ─────────────────────────────────────────────────────────────────────────
def v4_mt5(srcs: dict[str, pd.DataFrame], f: dict[int, pd.DataFrame], cal: Cal) -> None:
    mins = {"M1": 1, "M5": 5, "M15": 15, "M30": 30}

    def up(df, b):
        return regroup(df, cal.block(df["t"].to_numpy(), b))

    # yerli barlar birbirleriyle (MT5 kendi içinde tutarlı mı?)
    h1 = U.union([K.load_mt5_native("H1", K.MT5_DIR_A), U._fresh("H1")], "MT5 H1")
    h1 = h1[h1["t"] >= srcs["M30"]["t"].min()]
    pairs = [("M1", "M5"), ("M1", "M15"), ("M1", "M30"), ("M5", "M15"), ("M5", "M30"), ("M15", "M30")]
    for a, b in pairs:
        lo = max(srcs[a]["t"].min(), srcs[b]["t"].min())
        compare(srcs[b][srcs[b]["t"] >= lo], up(srcs[a][srcs[a]["t"] >= lo], mins[b]),
                f"V4 MT5 yerli {b} = {a}→{b}", must=False, vol=True)
    compare(h1, up(srcs["M30"], 60), "V4 MT5 yerli H1 = M30→H1", must=False, vol=True)
    # 2/3 dk → yerli M5/M15/M30
    for tf, tgt in ((3, "M15"), (3, "M30"), (2, "M30")):
        lo = f[tf]["t"].min()
        compare(srcs[tgt][(srcs[tgt]["t"] >= lo) & (srcs[tgt]["t"] <= f[tf]["t"].max() - 1800)],
                up(f[tf], mins[tgt]), f"V4 MT5 {tf}m→{tgt} = yerli {tgt}", must=False, vol=True)
    # 90/210 → yerli H1 (180 ve 420 dk ortak bloklar)
    compare(up(h1, 180), up(f[90], 180), "V4 MT5 90m×2 = yerli H1×3", must=False)
    compare(up(h1, 420), up(f[210], 420), "V4 MT5 210m×2 = yerli H1×7 (+180 kuyruk)", must=False)
    # 90/210 dört kaynaktan ayrı ayrı → birbirine eşit mi
    for tf in (90, 210):
        built = {k: up(v, tf) for k, v in srcs.items()}
        for a, b in (("M1", "M5"), ("M5", "M15"), ("M15", "M30"), ("M1", "M30")):
            lo = max(srcs[a]["t"].min(), srcs[b]["t"].min()) + 86400
            hi = min(srcs[a]["t"].max(), srcs[b]["t"].max()) - 86400
            x = built[a][(built[a]["t"] >= lo) & (built[a]["t"] <= hi)]
            compare(x, built[b], f"V4 MT5 {tf}m: {a}'den = {b}'den", must=False, vol=True)


# ── V5 ─────────────────────────────────────────────────────────────────────────
def v5_feeds(d: pd.DataFrame, m: pd.DataFrame, tf: int, name: str) -> None:
    """İki besleme aynı saat ekseninde mi: getiri korelasyonu en iyi gecikme 0 olmalı."""
    rd = d.set_index("t")["close"].pct_change()
    res = {}
    for lag in range(-3, 4):
        rm = m.assign(t=m["t"] + lag * tf * 60).set_index("t")["close"].pct_change()
        j = pd.concat([rd, rm], axis=1, join="inner").dropna()
        res[lag] = round(float(j.corr().iloc[0, 1]), 4)
    best = max(res, key=res.get)
    j = d.merge(m, on="t", suffixes=("_d", "_m"))
    lvl = (j["close_d"] - j["close_m"])
    key = f"V5 {name} {tf}m"
    REP[key] = {"gecikme_bar→r": res, "en_iyi": best, "ortak": int(len(j)),
                "seviye_farki_medyan": round(float(lvl.median()), 2),
                "seviye_farki_IQR": round(float(lvl.quantile(.75) - lvl.quantile(.25)), 2)}
    if best != 0:
        FAIL.append(f"{key} gecikme {best}")
    print(f"{key}: {REP[key]}")


def v6_wick_flags(fd: dict[int, pd.DataFrame]) -> None:
    """DUKA fitil bayrakları tutarlı mı (tam ⇔ fitil_durumu=tam) ve dağılım."""
    for tf, d in fd.items():
        ok = bool(((d["fitil_durumu"] == "tam") == d["tam"]).all())
        r = {"tutarli": ok, **d["fitil_durumu"].value_counts().to_dict()}
        REP[f"V6 DUKA {tf}m fitil_durumu"] = r
        if not ok:
            FAIL.append(f"V6 DUKA {tf}m")
        print(f"V6 DUKA {tf}m fitil_durumu: {r}")


def load_out(feed: str) -> dict[int, pd.DataFrame]:
    return {tf: pd.read_parquet(BASE / f"out/{feed}/NDX_{feed}_{tf}m.parquet") for tf in (2, 3, 90, 210)}


def check_1m_feed(feed: str, src: pd.DataFrame, f: dict[int, pd.DataFrame]) -> Cal:
    cal = Cal(np.r_[src["t"].to_numpy(), np.concatenate([v["t"].to_numpy() for v in f.values()])])
    print(f"──── {feed}")
    for tf, df in f.items():
        v1_format(df, tf, cal, f"{feed} {tf}m")
        v2_from_source(df, src, cal, f"{feed} {tf}m←1m")
    v3_hierarchy(feed, f, src, cal)
    return cal


def main() -> None:
    duka = K.load_duka_1m()
    fd = load_out("DUKA")
    check_1m_feed("DUKA", duka, fd)
    v6_wick_flags(fd)

    us, _ = U.drop_closed_hour(U.ustec_1m())
    fu = load_out("USTEC")
    check_1m_feed("USTEC", us, fu)

    print("──── MT5")
    srcs = U.mt5_sources()
    for k in list(srcs):
        srcs[k], _ = U.drop_closed_hour(srcs[k])
    m1_all, _ = U.mt5_m1_with_copies(srcs["M1"])
    fm = load_out("MT5")
    calm = Cal(np.r_[srcs["M30"]["t"].to_numpy(), m1_all["t"].to_numpy(),
                     np.concatenate([v["t"].to_numpy() for v in fm.values()])])
    for tf, df in fm.items():
        v1_format(df, tf, calm, f"MT5 {tf}m")
        if tf in (2, 3):  # terminal + doğrulanmış kopya günleri birlikte tek kaynak
            v2_from_source(df, m1_all, calm, f"MT5 {tf}m←M1(+kopya)")
            continue
        for k in df["kaynak_tf"].unique():
            v2_from_source(df[df["kaynak_tf"] == k].reset_index(drop=True), srcs[k], calm, f"MT5 {tf}m←{k}")
    fm_m1 = {tf: (v[v["kaynak_tf"] == "M1"].reset_index(drop=True) if tf in (90, 210) else v) for tf, v in fm.items()}
    fm_m1["tam_dosya"] = fm
    v3_hierarchy("MT5", fm_m1, m1_all, calm)
    v4_mt5(srcs, fm, calm)

    print("──── V5")
    for tf in (90, 210):
        v5_feeds(fd[tf], fm[tf], tf, "DUKA↔MT5")
        v5_feeds(fd[tf], fu[tf], tf, "DUKA↔USTEC")
        v5_feeds(fu[tf], fm[tf], tf, "USTEC↔MT5")

    REP["SONUC"] = {"zorunlu_basarisiz": FAIL, "gecti": not FAIL}
    (BASE / "results/s04_dogrulama.json").write_text(json.dumps(REP, indent=1, ensure_ascii=False, default=str))
    print("\nZORUNLU KONTROLLER:", "HEPSİ GEÇTİ" if not FAIL else f"BAŞARISIZ → {FAIL}")


if __name__ == "__main__":
    main()
