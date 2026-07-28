"""hiwr_lab.py — KULLANICININ TARİFİ: yüksek kazanma oranlı NDX BUY kurulumları.

İstenen (2026-07-28): "boğa mumu KAPANDIKTAN sonra gir; hacme bak; destek (sup)
bölgelerine bak; piyasa pozitife döndüğünde anla; TP kısa olabilir — önemli olan
kazanma oranı."

Bu laboratuvar TAM bunu ölçer. Rastgele/saatlik ızgara YOK — her kurulum olay
tetiklidir: karar yalnız 5m mum KAPANIŞINDA, koşullar sağlanıyorsa giriş bir
sonraki 1m mumun açılışından.

KURULUMLAR (kullanıcının aileleri):
  MUM   : yeşil 5m kapanış · 2 ardışık yeşil · boğa yutan (engulfing)
  HACİM : kapanan mumun hacmi son 20 mum ortalamasının 1.5×/2× üstü
  DESTEK: son 4 saatin dibine yakın dönüş · çok-dokunuşlu destek bölgesi tepkisi
  DÖNÜŞ : 5m kapanış EMA20 üstüne ÇIKTI (altında ≥6 bar kaldıktan sonra)
          · 15m trend pozitif (EMA20 üstü + eğim yukarı)
  KOMBO : destek + yeşil mum + hacim · dönüş + hacim · trend + yeşil + hacim

GEOMETRİLER (kısa TP — yüksek WR tasarımı; puan):
  TP 20/SL 60 · 30/60 · 30/90 · 40/90 · 40/110 · 60/110 · 80/110(bot)

DÜRÜSTLÜK:
  * Veri: ONARILMIŞ candle_cache (gerçek UTC, 2026-02-11 → 07-28).
  * Karar = kapanmış mum; giriş = sonraki 1m açılış + 1.3 puan sürtünme.
  * Aynı 1m barda TP+SL → SL önce (konservatif); belirsizlik oranı raporlanır.
  * Aynı anda 1 pozisyon (botun gerçeği) — sinyal yağmuru n şişirmez.
  * Kronolojik TRAIN/VAL/TEST + gün-bloklu bootstrap.
  * BAŞABAŞ ÇITASI her geometrinin yanında: WR çıtanın üstünde değilse KIRMIZI.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
FRIC = 1.3
RNG = np.random.default_rng(42)

T_TRAIN_END = pd.Timestamp("2026-05-05", tz="UTC")
T_VAL_END = pd.Timestamp("2026-06-12", tz="UTC")
PURGE = pd.Timedelta(days=1)

GEOMS = [(20, 60), (30, 60), (30, 90), (40, 90), (40, 110), (60, 110), (80, 110)]


# ── veri ─────────────────────────────────────────────────────────────────────
def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    b1 = pd.read_csv(DATA / "bars_1m_clean.csv", parse_dates=["ts"])
    b1["ts"] = pd.to_datetime(b1["ts"], utc=True)
    b1 = b1.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)

    def rs(rule):
        g = (b1.set_index("ts").resample(rule, label="left", closed="left")
             .agg({"open": "first", "high": "max", "low": "min",
                   "close": "last", "volume": "sum"}).dropna(subset=["open"]))
        return g.reset_index()

    return b1, rs("5min"), rs("15min")


def build_setups(b1: pd.DataFrame, b5: pd.DataFrame, b15: pd.DataFrame) -> pd.DataFrame:
    """Her 5m mum KAPANIŞI için kurulum bayrakları. Satır i = i. mumun kapanış anı."""
    d = b5.copy()
    o, h, l, c, v = d.open, d.high, d.low, d.close, d.volume

    # mum aileleri
    green = (c > o)
    body = (c - o).abs() / (h - l).replace(0, np.nan)
    d["green"] = green
    d["green_solid"] = green & (body > 0.5)                # gövdeli yeşil mum
    d["green2"] = green & green.shift(1).fillna(False)
    d["engulf"] = (green & (c.shift(1) < o.shift(1))
                   & (c > o.shift(1)) & (o < c.shift(1)))

    # hacim
    vma = v.rolling(20).mean()
    d["vol15"] = v / vma > 1.5
    d["vol20"] = v / vma > 2.0

    # destek aileleri (yalnız GEÇMİŞ barlardan)
    low240 = l.shift(1).rolling(48).min()                  # önceki 48×5m = 4 saat dibi
    atr1h = (h - l).rolling(12).mean() * 3.5               # kaba saatlik aralık ölçeği
    d["near_low"] = (l - low240) < 0.15 * atr1h            # dibe dokundu/yaklaştı
    d["sup_bounce"] = d["near_low"] & green & (c > low240) # dipten yeşil kapanışla döndü

    # çok-dokunuşlu bölge: son 4 saatte 10-puanlık kovaya ≥3 AYRI mum düşmüş dip
    bin_ = (l / 10).round() * 10
    touch = bin_.shift(1).rolling(48).apply(
        lambda x: pd.Series(x).value_counts().max() if len(x) else 0, raw=False)
    mode_bin = bin_.shift(1).rolling(48).apply(
        lambda x: pd.Series(x).mode().iloc[0] if len(x) else np.nan, raw=False)
    d["zone_touch"] = (touch >= 3) & ((l - mode_bin).abs() < 12) & green

    # dönüş aileleri
    ema20_5 = c.ewm(span=20, adjust=False).mean()
    below = (c < ema20_5)
    below_run = below.shift(1).rolling(6).sum()            # önceki 6 barın kaçı altında
    d["ema_crossup"] = (c > ema20_5) & (below_run >= 5)    # uzun süre altında kal + üstüne KAPAN
    # RSI(5m,14) 40 altından yukarı dönüş
    delta = c.diff()
    up = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    dn = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rsi = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    d["rsi_turn"] = (rsi > rsi.shift(1)) & (rsi.shift(1) < 40) & green

    # 15m trend pozitif (kapanmış 15m barlardan; asof ile bağlanır)
    e15 = b15.close.ewm(span=20, adjust=False).mean()
    t15 = pd.DataFrame({
        "known_at": b15.ts + pd.Timedelta(minutes=15),
        "trend15_up": (b15.close > e15) & (e15.diff(3) > 0),
    })
    d["known_at"] = d.ts + pd.Timedelta(minutes=5)
    d = pd.merge_asof(d.sort_values("known_at"), t15.sort_values("known_at"),
                      on="known_at", direction="backward")
    d["trend15_up"] = d["trend15_up"].fillna(False)

    # NY seansı (kullanıcı ekranda RTH izliyor)
    et = d.ts.dt.tz_convert("America/New_York")
    d["rth"] = (et.dt.hour * 60 + et.dt.minute).between(9 * 60 + 30, 15 * 60 + 55)
    return d


SETUPS = {
    # ── mum teyidi ──
    "yeşil 5m mum":                lambda d: d.green,
    "gövdeli yeşil 5m":            lambda d: d.green_solid,
    "2 ardışık yeşil":             lambda d: d.green2,
    "boğa yutan (engulf)":         lambda d: d.engulf,
    # ── hacim ──
    "yeşil + hacim 1.5×":          lambda d: d.green_solid & d.vol15,
    "yeşil + hacim 2×":            lambda d: d.green_solid & d.vol20,
    # ── destek ──
    "4s dibinden dönüş":           lambda d: d.sup_bounce,
    "çok-dokunuşlu destek tepki":  lambda d: d.zone_touch,
    "destek dönüş + hacim 1.5×":   lambda d: d.sup_bounce & d.vol15,
    # ── piyasa pozitife döndü ──
    "EMA20 üstüne kapanış (dönüş)":lambda d: d.ema_crossup,
    "RSI<40'tan dönüş + yeşil":    lambda d: d.rsi_turn,
    "dönüş + hacim 1.5×":          lambda d: d.ema_crossup & d.vol15,
    # ── trend + teyit ──
    "15m trend + gövdeli yeşil":   lambda d: d.trend15_up & d.green_solid,
    "15m trend + yeşil + hacim":   lambda d: d.trend15_up & d.green_solid & d.vol15,
    "15m trend + destek dönüşü":   lambda d: d.trend15_up & d.sup_bounce,
    # ── hepsi + RTH ──
    "destek dönüş + hacim (RTH)":  lambda d: d.sup_bounce & d.vol15 & d.rth,
    "dönüş + hacim (RTH)":         lambda d: d.ema_crossup & d.vol15 & d.rth,
    "trend + yeşil + hacim (RTH)": lambda d: d.trend15_up & d.green_solid & d.vol15 & d.rth,
}


def replay_episodes(b1, sig_ts, tp, sl):
    """Aynı anda 1 pozisyon; SL-önce konservatif; MFE kaydı yok (hız)."""
    ts1 = b1.ts.values
    arr = b1[["open", "high", "low", "close"]].to_numpy()
    out, open_until, amb = [], None, 0
    for t in sig_ts:
        t64 = np.datetime64(pd.Timestamp(t).tz_localize(None) if pd.Timestamp(t).tzinfo else pd.Timestamp(t))
        if open_until is not None and t64 < open_until:
            continue
        i = np.searchsorted(ts1, t64, side="right")
        if i >= len(ts1) - 1:
            continue
        entry = arr[i, 0] + FRIC
        tp_px, sl_px = entry + tp, entry - sl
        res = None
        for j in range(i, min(len(ts1), i + 1440)):
            hi, lo = arr[j, 1], arr[j, 2]
            if lo <= sl_px:
                if hi >= tp_px:
                    amb += 1
                res = (0, -(sl + FRIC) / sl, j); break
            if hi >= tp_px:
                res = (1, (tp - FRIC) / sl, j); break
        if res is None:
            continue
        open_until = ts1[res[2]]
        out.append(dict(ts=pd.Timestamp(t64, tz="UTC"), outcome=res[0], r=res[1]))
    df = pd.DataFrame(out)
    return df, amb


def split_of(ts):
    return np.where(ts < T_TRAIN_END - PURGE, "tr",
                    np.where(ts < T_TRAIN_END, "pg",
                             np.where(ts < T_VAL_END - PURGE, "va",
                                      np.where(ts < T_VAL_END, "pg", "te"))))


def day_boot_wr(df, B=2000):
    if len(df) == 0:
        return np.nan, np.nan
    day = df.ts.dt.date.values
    days = np.unique(day)
    by = {x: df.outcome.values[day == x] for x in days}
    o = np.empty(B)
    for i in range(B):
        pick = RNG.choice(days, size=len(days), replace=True)
        o[i] = np.concatenate([by[x] for x in pick]).mean()
    return float(np.quantile(o, .05)), float(np.quantile(o, .95))


def main():
    pd.set_option("display.width", 240)
    b1, b5, b15 = load()
    print(f"1m {len(b1)} · 5m {len(b5)}  {b1.ts.min().date()} → {b1.ts.max().date()}\n")
    d = build_setups(b1, b5, b15)

    rows = []
    for sname, fn in SETUPS.items():
        mask = fn(d).fillna(False)
        sig_ts = (d.ts[mask] + pd.Timedelta(minutes=5)).values   # kapanış anı
        n_sig = int(mask.sum())
        for tp, sl in GEOMS:
            be = (sl + FRIC) / (tp + sl)          # sürtünmeli başabaş WR
            ep, amb = replay_episodes(b1, sig_ts, float(tp), float(sl))
            if len(ep) < 40:
                continue
            ep["sp"] = split_of(ep.ts)
            wr = ep.outcome.mean()
            ev = ep.r.mean()
            lo, hi = day_boot_wr(ep)
            sub = {s: ep[ep.sp == s] for s in ("tr", "va", "te")}
            rows.append(dict(
                kurulum=sname, tp=tp, sl=sl, n=len(ep),
                gün=ep.ts.dt.date.nunique(),
                WR=round(wr * 100, 1), başabaş=round(be * 100, 1),
                marj=round((wr - be) * 100, 1),
                EV=round(ev, 4),
                WR_GA=f"[{lo*100:.0f},{hi*100:.0f}]",
                tr=round(sub["tr"].r.mean(), 3) if len(sub["tr"]) > 10 else np.nan,
                va=round(sub["va"].r.mean(), 3) if len(sub["va"]) > 10 else np.nan,
                te=round(sub["te"].r.mean(), 3) if len(sub["te"]) > 10 else np.nan,
                belirsiz=amb,
            ))
    res = pd.DataFrame(rows)
    res.to_csv(DATA / "hiwr_results.csv", index=False)

    print("═══ TÜM SONUÇLAR (marj = WR − başabaş; pozitifse çıtayı geçiyor) ═══")
    show = res.sort_values(["kurulum", "tp"])
    print(show.to_string(index=False))

    print("\n═══ ÇITAYI GEÇENLER (marj>0 VE üç dilimde EV≥0) ═══")
    ok = res[(res.marj > 0) & (res.tr.fillna(-1) >= 0)
             & (res.va.fillna(-1) >= 0) & (res.te.fillna(-1) >= 0)]
    print(ok.sort_values("EV", ascending=False).to_string(index=False) if len(ok) else "  YOK")


if __name__ == "__main__":
    main()
