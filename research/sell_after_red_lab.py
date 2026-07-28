#!/usr/bin/env python3
"""sell_after_red_lab.py — "BÜYÜK KIRMIZI MUM + ALTINDA DESTEK YOK → SELL" laboratuvarı.

Kullanıcı hipotezi (2026-07-28):
  5 dakikalık grafikte büyük bir KIRMIZI mum kapandığında, kapanış tam bir güçlü
  desteğe denk gelmiyorsa altı boştur → seviye kırılır → o kapanıştan açılan SELL
  kâr eder. Kapanış desteğin üstünde oturuyorsa açma.

Bu dosya o hipotezi SIZINTISIZ ölçer ve üç bölüm üretir:

  BÖLÜM A — Betimsel: NAS100 5m'de büyük kırmızı mumdan SONRA gerçekte ne oluyor?
            (sonraki bar getirisi, ufuk MFE/MAE, aynanın kontrolü: büyük yeşil + BUY)
  BÖLÜM B — Kullanıcı kurgusu: destek sınıfına göre SELL sonuçları, 5 geometri,
            kırılma olasılığı tablosu, çeyreklik istikrar, OOS bölme, bootstrap,
            plasebo/taban karşılaştırması (rastgele anda SELL).
  BÖLÜM C — Bot teşhisi: canlı VIXREG SELL'lerinin girdiği KONUM bandının
            (4 saatlik dalgada 0.40 kapısı) tarihsel karnesi — kapı eşiği bir
            "çekim noktası" yarattı mı?

SIZINTI GARANTİLERİ
  * Tüm göstergeler yalnız KAPANMIŞ barlardan (ATR, pivotlar, seviyeler, konum).
  * Fraktal pivot ancak sağındaki `right` bar kapandıktan sonra "onaylı" sayılır.
  * Giriş = sinyal barının KAPANIŞI; sonuç yalnız SONRAKİ barların high/low'u ile.
  * Aynı barda hem TP hem SL → KAYIP (konservatif), oran ayrıca raporlanır.
  * Spread trigger koşullarına gömülü (SELL: ask ile tetiklenir, emir fiyatından dolar).

Kullanım (MT5 kutusunda):
    python research/sell_after_red_lab.py --symbol NAS100 --bars 99000
    python research/sell_after_red_lab.py --dump research/nas100_m5.csv     # veriyi kaydet
    python research/sell_after_red_lab.py --csv research/nas100_m5.csv      # MT5'siz tekrar koş
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from bisect import bisect_left
from datetime import datetime, timezone

import numpy as np

# ─── Sabitler (magic number yasak) ──────────────────────────────────────────
ATR_PERIOD = 14
PIVOT_LEFT = 2
PIVOT_RIGHT = 2
LEVEL_WINDOW = 400          # kullanıcı tarifi: "son 400 mum"
LEVEL_TOL_ATR = 0.35        # bu kadar yakın pivotlar tek seviyeye kümelenir
LEVEL_MIN_TOUCH = 2         # "güçlü destek" = en az 2 dokunuş
AT_SUPPORT_ATR = 0.25       # kapanış seviyeye bu kadar yakınsa "DESTEKTE"
FREE_ROOM_ATR = 0.75        # altındaki en yakın destek bu kadar uzaksa "BOŞLUKTA"
BREAK_MARGIN_ATR = 0.25     # kırılma sayılması için seviyenin bu kadar altına inme
BREAK_HORIZON = 24          # kırılma penceresi (bar) = 2 saat
POS_LOOKBACK_M5 = 48        # botun konum kapısıyla AYNI pencere (4 saat)
VOL_MEAN_WINDOW = 20
DEFAULT_SPREAD = 1.5        # NAS100 canlı ölçüm (ask-bid), fiyat birimi
BOT_TP_POINTS = 80.0        # canlı VIXREG geometrisi
BOT_SL_POINTS = 110.0
POINT_VALUE_PER_LOT = 1.0   # NAS100: 1 puan = 1$ / lot
LIVE_LOT = 5.0              # kutudaki canlı lot
BOOTSTRAP_N = 2000
RNG_SEED = 7

SESSIONS = (                # sunucu saati (UTC+3) — MT5 barlarının etiketi
    ("ASYA", 1, 9),
    ("AVRUPA", 9, 16.5),
    ("ABD", 16.5, 23),
    ("KAPANIS", 23, 25),
)


# ═══ Veri ═══════════════════════════════════════════════════════════════════

def load_mt5(symbol: str, count: int, tf: str = "M5"):
    """MT5'ten bar çek (kutuda çalışır). Dönen: dict of np arrays."""
    import MetaTrader5 as mt5

    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize başarısız: {mt5.last_error()}")
    tf_map = {"M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5,
              "M15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1}
    rates = mt5.copy_rates_from_pos(symbol, tf_map[tf], 0, count)
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"{symbol} {tf} bar gelmedi: {mt5.last_error()}")
    return {
        "time": np.asarray([int(r["time"]) for r in rates], dtype=np.int64),
        "open": np.asarray([float(r["open"]) for r in rates]),
        "high": np.asarray([float(r["high"]) for r in rates]),
        "low": np.asarray([float(r["low"]) for r in rates]),
        "close": np.asarray([float(r["close"]) for r in rates]),
        "vol": np.asarray([float(r["tick_volume"]) for r in rates]),
    }


def dump_csv(bars: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["time", "open", "high", "low", "close", "vol"])
        for i in range(len(bars["time"])):
            w.writerow([bars["time"][i], bars["open"][i], bars["high"][i],
                        bars["low"][i], bars["close"][i], bars["vol"][i]])


def load_csv(path: str) -> dict:
    t, o, h, l, c, v = [], [], [], [], [], []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t.append(int(row["time"])); o.append(float(row["open"]))
            h.append(float(row["high"])); l.append(float(row["low"]))
            c.append(float(row["close"])); v.append(float(row["vol"]))
    return {"time": np.asarray(t, dtype=np.int64), "open": np.asarray(o),
            "high": np.asarray(h), "low": np.asarray(l),
            "close": np.asarray(c), "vol": np.asarray(v)}


# ═══ Göstergeler (hepsi causal) ═════════════════════════════════════════════

def wilder_atr(high, low, close, period: int = ATR_PERIOD):
    n = len(close)
    tr = np.empty(n)
    tr[0] = high[0] - low[0]
    prev = close[:-1]
    tr[1:] = np.maximum(high[1:] - low[1:],
                        np.maximum(np.abs(high[1:] - prev), np.abs(low[1:] - prev)))
    atr = np.full(n, np.nan)
    if n <= period:
        return atr
    atr[period] = tr[1:period + 1].mean()
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def confirmed_pivot_lows(low, left=PIVOT_LEFT, right=PIVOT_RIGHT):
    """(onay_bar_indeksi, pivot_indeksi, fiyat) — onay = pivot + right."""
    out = []
    n = len(low)
    for i in range(left, n - right):
        window_l = low[i - left:i]
        window_r = low[i + 1:i + right + 1]
        if low[i] <= window_l.min() and low[i] <= window_r.min():
            out.append((i + right, i, float(low[i])))
    return out


def confirmed_pivot_highs(high, left=PIVOT_LEFT, right=PIVOT_RIGHT):
    out = []
    n = len(high)
    for i in range(left, n - right):
        if high[i] >= high[i - left:i].max() and high[i] >= high[i + 1:i + right + 1].max():
            out.append((i + right, i, float(high[i])))
    return out


def cluster_levels(values, tol, min_touch=LEVEL_MIN_TOUCH):
    """Yakın pivotları tek seviyeye kümele → [(seviye, dokunuş)]."""
    if not values:
        return []
    vals = sorted(values)
    levels, cur = [], [vals[0]]
    for v in vals[1:]:
        if v - cur[-1] <= tol:
            cur.append(v)
        else:
            levels.append(cur); cur = [v]
    levels.append(cur)
    return [(float(np.mean(g)), len(g)) for g in levels if len(g) >= min_touch]


def rolling_pos(close, high, low, window=POS_LOOKBACK_M5):
    """Botun konum kapısıyla AYNI hesap: son `window` barın (bugünkü bar dahil)
    dip-tepe aralığında kapanışın yeri. 0=dip, 1=tepe."""
    n = len(close)
    pos = np.full(n, np.nan)
    lo = np.full(n, np.nan)
    hi = np.full(n, np.nan)
    for i in range(window - 1, n):
        w_lo = low[i - window + 1:i + 1].min()
        w_hi = high[i - window + 1:i + 1].max()
        lo[i], hi[i] = w_lo, w_hi
        if w_hi > w_lo:
            pos[i] = (close[i] - w_lo) / (w_hi - w_lo)
    return pos, lo, hi


def bot_ema50_h1(h1_close):
    """Botun trend_alignment()'ındaki AYNI tarif: son 50 kapanış, seed=closes[-50]."""
    n = len(h1_close)
    ema = np.full(n, np.nan)
    k = 2.0 / 51.0
    for j in range(49, n):
        e = float(h1_close[j - 49])
        for v in h1_close[j - 48:j + 1]:
            e = float(v) * k + e * (1 - k)
        ema[j] = e
    return ema


def session_of(ts: int) -> str:
    hour = datetime.fromtimestamp(int(ts), tz=timezone.utc).hour + \
        datetime.fromtimestamp(int(ts), tz=timezone.utc).minute / 60.0
    for name, a, b in SESSIONS:
        if a <= hour < b:
            return name
    return "KAPANIS"


# ═══ İşlem simülasyonu ══════════════════════════════════════════════════════

def simulate(idx, entry, tp, sl, high, low, close, horizon, spread, side="SELL"):
    """Giriş barının KAPANIŞINDAN sonraki barlarla çöz. Dönen dict."""
    n = len(close)
    end = min(idx + horizon, n - 1)
    mfe = mae = 0.0
    for j in range(idx + 1, end + 1):
        if side == "SELL":
            fav = entry - low[j]
            adv = high[j] - entry
            hit_tp = low[j] <= tp - spread
            hit_sl = high[j] >= sl - spread
        else:
            fav = high[j] - entry
            adv = entry - low[j]
            hit_tp = high[j] >= tp + spread
            hit_sl = low[j] <= sl + spread
        mfe = max(mfe, fav); mae = max(mae, adv)
        if hit_tp and hit_sl:
            net = (entry - sl) if side == "SELL" else (sl - entry)
            return {"outcome": "LOSS", "ambiguous": True, "net": net,
                    "bars": j - idx, "mfe": mfe, "mae": mae}
        if hit_sl:
            net = (entry - sl) if side == "SELL" else (sl - entry)
            return {"outcome": "LOSS", "ambiguous": False, "net": net,
                    "bars": j - idx, "mfe": mfe, "mae": mae}
        if hit_tp:
            net = (entry - tp) if side == "SELL" else (tp - entry)
            return {"outcome": "WIN", "ambiguous": False, "net": net,
                    "bars": j - idx, "mfe": mfe, "mae": mae}
    px = close[end]
    net = (entry - px - spread) if side == "SELL" else (px - entry - spread)
    return {"outcome": "TIME", "ambiguous": False, "net": net,
            "bars": end - idx, "mfe": mfe, "mae": mae}


def stats(nets, risks, label="", extra=None):
    if not nets:
        return {"label": label, "n": 0}
    nets = np.asarray(nets, dtype=float)
    r = np.asarray(risks, dtype=float)
    rr = nets / r
    wins = int((nets > 0).sum())
    out = {"label": label, "n": len(nets), "wr": 100.0 * wins / len(nets),
           "ev_pts": float(nets.mean()), "ev_r": float(rr.mean()),
           "total_r": float(rr.sum()),
           "usd_total": float(nets.sum() * POINT_VALUE_PER_LOT * LIVE_LOT),
           "median_pts": float(np.median(nets))}
    if extra:
        out.update(extra)
    return out


def bootstrap_p_positive(nets, risks, n_boot=BOOTSTRAP_N, seed=RNG_SEED):
    if len(nets) < 10:
        return None
    rng = np.random.default_rng(seed)
    rr = np.asarray(nets, dtype=float) / np.asarray(risks, dtype=float)
    idx = rng.integers(0, len(rr), size=(n_boot, len(rr)))
    means = rr[idx].mean(axis=1)
    return float((means > 0).mean())


def fmt(s):
    if not s or s.get("n", 0) == 0:
        return f"  {s.get('label', '?'):<34} n=0"
    return (f"  {s['label']:<34} n={s['n']:>5}  WR={s['wr']:>5.1f}%  "
            f"EV={s['ev_pts']:>7.2f}p ({s['ev_r']:>+6.3f}R)  toplam={s['total_r']:>+8.1f}R  "
            f"{s['usd_total']:>+11,.0f}$")


# ═══ Ana akış ═══════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="NAS100")
    ap.add_argument("--bars", type=int, default=99000)
    ap.add_argument("--csv", default=None, help="MT5 yerine CSV'den oku")
    ap.add_argument("--dump", default=None, help="çekilen barları CSV'ye yaz")
    ap.add_argument("--spread", type=float, default=DEFAULT_SPREAD)
    ap.add_argument("--body-atr", type=float, default=1.0, help="büyük mum eşiği (×ATR)")
    ap.add_argument("--body-ratio", type=float, default=0.55, help="gövde/menzil min")
    ap.add_argument("--horizon", type=int, default=72, help="zaman stopu (bar)")
    ap.add_argument("--level-window", type=int, default=LEVEL_WINDOW)
    ap.add_argument("--min-touch", type=int, default=LEVEL_MIN_TOUCH)
    ap.add_argument("--free-room", type=float, default=FREE_ROOM_ATR)
    ap.add_argument("--at-support", type=float, default=AT_SUPPORT_ATR)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()
    lvl_window, min_touch = args.level_window, args.min_touch
    free_room, at_support = args.free_room, args.at_support

    if args.csv:
        bars = load_csv(args.csv)
        h1 = None
    else:
        bars = load_mt5(args.symbol, args.bars, "M5")
        try:
            h1 = load_mt5(args.symbol, min(args.bars, 20000), "H1")
        except Exception as exc:                       # H1 yoksa BÖLÜM C atlanır
            print(f"[uyari] H1 alinamadi: {exc}")
            h1 = None
        if args.dump:
            dump_csv(bars, args.dump)
            print(f"[bilgi] barlar kaydedildi → {args.dump}")

    t, o, h, l, c, v = (bars["time"], bars["open"], bars["high"],
                        bars["low"], bars["close"], bars["vol"])
    n = len(c)
    atr = wilder_atr(h, l, c)
    pos, wave_lo, wave_hi = rolling_pos(c, h, l)
    vol_mean = np.full(n, np.nan)
    for i in range(VOL_MEAN_WINDOW, n):
        vol_mean[i] = v[i - VOL_MEAN_WINDOW:i].mean()

    piv_lows = confirmed_pivot_lows(l)
    piv_confirm_idx = [p[0] for p in piv_lows]          # onay barı (sıralı)
    piv_bar_idx = [p[1] for p in piv_lows]              # pivotun kendi barı (sıralı)
    # ── H1 EMA50 trend hizası (botun trend_alignment'ıyla aynı tarif) ────────
    # SIZINTI ÖNLEMİ: 5m barı içinde bulunduğu H1 barının KAPANIŞI henüz
    # bilinmiyor → yalnız KAPANMIŞ H1 barından (h1t + 3600 ≤ t[i]) EMA al.
    trend_down = np.zeros(n, dtype=bool)
    trend_known = np.zeros(n, dtype=bool)
    if h1 is not None:
        ema_h1 = bot_ema50_h1(h1["close"])
        h1t = h1["time"]
        for i in range(n):
            j = int(np.searchsorted(h1t, t[i] - 3600, side="right")) - 1
            if j >= 0 and np.isfinite(ema_h1[j]):
                trend_known[i] = True
                trend_down[i] = c[i] < ema_h1[j]

    d0 = datetime.fromtimestamp(int(t[0]), tz=timezone.utc)
    d1 = datetime.fromtimestamp(int(t[-1]), tz=timezone.utc)
    print("=" * 96)
    print(f"SELL-AFTER-RED LAB — {args.symbol} 5m | {n:,} bar | "
          f"{d0:%Y-%m-%d} → {d1:%Y-%m-%d} | spread={args.spread}p | "
          f"lot={LIVE_LOT} (1p={POINT_VALUE_PER_LOT}$/lot)")
    print(f"büyük mum: gövde ≥ {args.body_atr}×ATR14 ve gövde/menzil ≥ {args.body_ratio} | "
          f"seviye penceresi {lvl_window} bar, ≥{min_touch} dokunuş, "
          f"küme toleransı {LEVEL_TOL_ATR}×ATR")
    print("=" * 96)

    # ── Olay taraması ───────────────────────────────────────────────────────
    warmup = max(lvl_window, POS_LOOKBACK_M5, ATR_PERIOD + 2, VOL_MEAN_WINDOW) + 5
    events = []
    for i in range(warmup, n - 2):
        a = atr[i]
        if not np.isfinite(a) or a <= 0:
            continue
        body = o[i] - c[i]
        rng_ = h[i] - l[i]
        if rng_ <= 0:
            continue
        is_red = body > 0
        big = abs(body) >= args.body_atr * a and abs(body) / rng_ >= args.body_ratio
        if not big:
            continue

        # causal seviye seti: onayı ≤ i olan ve pencere içindeki pivotlar
        hi_idx = bisect_left(piv_confirm_idx, i + 1)      # onay ≤ i
        lo_idx = bisect_left(piv_bar_idx, i - lvl_window)
        vals = [p[2] for p in piv_lows[lo_idx:hi_idx]]
        levels = cluster_levels(vals, LEVEL_TOL_ATR * a, min_touch)
        px = c[i]
        below = [lv for lv, _tc in levels if lv <= px]
        near_below = max(below) if below else None
        d_below = (px - near_below) / a if near_below is not None else float("inf")
        d_near = min((abs(px - lv) / a for lv, _ in levels), default=float("inf"))

        if d_near <= at_support:
            klass = "DESTEKTE"
        elif d_below >= free_room:
            klass = "BOSLUKTA"
        else:
            klass = "ARADA"
        # "KIRDI": mum bir önceki kapanışın ALTINDAKİ bir seviyeyi kapanışla deldi
        broke_level = any(c[i] < lv < c[i - 1] for lv, _tc in levels)

        # kırılma olayı (yalnız altında seviye varsa anlamlı)
        broke = None
        if near_below is not None:
            end = min(i + BREAK_HORIZON, n - 1)
            broke = bool(l[i + 1:end + 1].min() < near_below - BREAK_MARGIN_ATR * a)

        events.append({
            "i": i, "ts": int(t[i]), "red": bool(is_red), "px": float(px),
            "atr": float(a), "body_atr": float(abs(body) / a),
            "body_ratio": float(abs(body) / rng_),
            "vol_ratio": float(v[i] / vol_mean[i]) if np.isfinite(vol_mean[i]) and vol_mean[i] > 0 else np.nan,
            "d_below": float(d_below), "d_near": float(d_near),
            "n_levels": len(levels), "klass": klass, "broke": broke,
            "near_below": near_below, "pos": float(pos[i]) if np.isfinite(pos[i]) else np.nan,
            "session": session_of(int(t[i])),
            "trend_down": bool(trend_down[i]), "trend_known": bool(trend_known[i]),
            "broke_level": bool(broke_level),
            "prev_red": bool(o[i - 1] > c[i - 1]),
            "atr_pctile": float((atr[max(0, i - 500):i + 1] <= a).mean()),
        })

    reds = [e for e in events if e["red"]]
    greens = [e for e in events if not e["red"]]
    print(f"\nolaylar: buyuk KIRMIZI={len(reds):,}  buyuk YESIL={len(greens):,}  "
          f"(tum barlarin %{100.0 * len(events) / n:.1f}'i)")

    # ── BÖLÜM A — betimsel ──────────────────────────────────────────────────
    print("\n" + "─" * 96)
    print("BÖLÜM A — BÜYÜK MUMDAN SONRA GERÇEKTE NE OLUYOR? (geometriden bağımsız)")
    print("─" * 96)

    def fwd_stats(evs, k):
        """k bar sonraki net yön hareketi (puan) ve ATR-normalize."""
        out = []
        for e in evs:
            j = min(e["i"] + k, n - 1)
            out.append((c[j] - e["px"]) / e["atr"])
        return np.asarray(out) if out else np.asarray([0.0])

    for label, evs in (("büyük KIRMIZI mum", reds), ("büyük YEŞİL mum", greens)):
        row = [f"  {label:<20}"]
        for k in (1, 6, 12, 24, 72):
            f_ = fwd_stats(evs, k)
            row.append(f"+{k:>2}bar: {f_.mean():+.3f}ATR (yukarı %{100.0 * (f_ > 0).mean():.0f})")
        print("  ".join(row))
    allbar = np.asarray([(c[min(i + 24, n - 1)] - c[i]) / atr[i]
                         for i in range(warmup, n - 25, 7) if np.isfinite(atr[i]) and atr[i] > 0])
    print(f"  {'TABAN (rastgele bar)':<20}  +24bar: {allbar.mean():+.3f}ATR "
          f"(yukarı %{100.0 * (allbar > 0).mean():.0f})  ← karşılaştırma çıtası")

    # ── Geometriler ─────────────────────────────────────────────────────────
    def geometries(e, side="SELL"):
        a, px = e["atr"], e["px"]
        g = {}
        if side == "SELL":
            g["BOT 80/110 (canlı VIXREG)"] = (px - BOT_TP_POINTS, px + BOT_SL_POINTS)
            g["ATR 1.0 : 1.0"] = (px - a, px + a)
            g["ATR 1.5 : 1.0"] = (px - 1.5 * a, px + a)
            g["ATR 0.75 : 1.0 (yüksek WR)"] = (px - 0.75 * a, px + a)
            if e["near_below"] is not None and (px - e["near_below"]) >= 0.5 * a:
                g["DESTEĞE KADAR / SL 1ATR"] = (e["near_below"], px + a)
        else:
            g["BOT 80/110 (ayna)"] = (px + BOT_TP_POINTS, px - BOT_SL_POINTS)
            g["ATR 1.0 : 1.0"] = (px + a, px - a)
            g["ATR 1.5 : 1.0"] = (px + 1.5 * a, px - a)
            g["ATR 0.75 : 1.0 (yüksek WR)"] = (px + 0.75 * a, px - a)
        return g

    def run(evs, side="SELL", horizon=None):
        horizon = horizon or args.horizon
        res = {}
        for e in evs:
            for gname, (tp, sl) in geometries(e, side).items():
                r = simulate(e["i"], e["px"], tp, sl, h, l, c, horizon, args.spread, side)
                risk = abs(sl - e["px"])
                res.setdefault(gname, []).append((r, risk, e))
        return res

    # ── BÖLÜM B — kullanıcı kurgusu ─────────────────────────────────────────
    print("\n" + "─" * 96)
    print("BÖLÜM B — KULLANICI KURGUSU: büyük kırmızı mum kapanışında SELL")
    print("─" * 96)

    res_all = run(reds, "SELL")
    print("\n[B1] TÜM büyük kırmızı mumlar (destek filtresi YOK — 'her SELL mumunun ardından aç')")
    for gname, rows in res_all.items():
        nets = [r["net"] for r, _k, _e in rows]
        risks = [k for _r, k, _e in rows]
        amb = sum(1 for r, _k, _e in rows if r["ambiguous"])
        s = stats(nets, risks, gname)
        p = bootstrap_p_positive(nets, risks)
        print(fmt(s) + f"  P(EV>0)={'-' if p is None else f'%{100 * p:.0f}'}"
              f"  belirsiz={100.0 * amb / max(1, len(rows)):.1f}%")

    print("\n[B2] DESTEK SINIFINA GÖRE (kullanıcı kuralı: kapanış desteğe değmiyorsa SAT)")
    for klass in ("BOSLUKTA", "ARADA", "DESTEKTE"):
        sub = [e for e in reds if e["klass"] == klass]
        if not sub:
            continue
        res = run(sub, "SELL")
        print(f"\n  ▸ {klass}  (n={len(sub)})")
        for gname, rows in res.items():
            nets = [r["net"] for r, _k, _e in rows]
            risks = [k for _r, k, _e in rows]
            s = stats(nets, risks, gname)
            p = bootstrap_p_positive(nets, risks)
            print("  " + fmt(s) + f"  P(EV>0)={'-' if p is None else f'%{100 * p:.0f}'}")

    print("\n[B3] KIRILMA OLASILIĞI — altındaki en yakın desteğin "
          f"{BREAK_HORIZON} bar içinde {BREAK_MARGIN_ATR}×ATR aşılarak kırılma oranı")
    buckets = [(0.0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.25), (1.25, 2.0), (2.0, 99.0)]
    print(f"  {'destek mesafesi (ATR)':<26}{'n':>7}{'kırıldı':>10}{'| hacim>1.3x':>16}{'| ABD seansı':>16}")
    for lo_b, hi_b in buckets:
        sub = [e for e in reds if e["broke"] is not None and lo_b <= e["d_below"] < hi_b]
        if len(sub) < 15:
            continue
        br = 100.0 * sum(1 for e in sub if e["broke"]) / len(sub)
        volsub = [e for e in sub if np.isfinite(e["vol_ratio"]) and e["vol_ratio"] >= 1.3]
        vb = (100.0 * sum(1 for e in volsub if e["broke"]) / len(volsub)) if len(volsub) >= 10 else float("nan")
        us = [e for e in sub if e["session"] == "ABD"]
        ub = (100.0 * sum(1 for e in us if e["broke"]) / len(us)) if len(us) >= 10 else float("nan")
        print(f"  {lo_b:.2f}–{hi_b:.2f} ATR{'':<12}{len(sub):>7}{br:>9.1f}%{vb:>15.1f}%{ub:>15.1f}%")
    allbreak = [e for e in reds if e["broke"] is not None]
    if allbreak:
        print(f"  {'TÜMÜ':<26}{len(allbreak):>7}"
              f"{100.0 * sum(1 for e in allbreak if e['broke']) / len(allbreak):>9.1f}%")

    print("\n[B4] SEANS KIRILIMI (BOSLUKTA sınıfı, ATR 1.0:1.0)")
    for sname, _a, _b in SESSIONS:
        sub = [e for e in reds if e["klass"] == "BOSLUKTA" and e["session"] == sname]
        if len(sub) < 20:
            continue
        rows = run(sub, "SELL")["ATR 1.0 : 1.0"]
        nets = [r["net"] for r, _k, _e in rows]; risks = [k for _r, k, _e in rows]
        print(fmt(stats(nets, risks, sname)))

    print("\n[B5] ÇEYREKLİK İSTİKRAR (BOSLUKTA + ATR 1.0:1.0) — bir kenar her çeyrekte durmalı")
    rows = run([e for e in reds if e["klass"] == "BOSLUKTA"], "SELL")["ATR 1.0 : 1.0"]
    by_q = {}
    for r, k, e in rows:
        q = datetime.fromtimestamp(e["ts"], tz=timezone.utc)
        key = f"{q.year}Ç{(q.month - 1) // 3 + 1}"
        by_q.setdefault(key, []).append((r["net"], k))
    for key in sorted(by_q):
        nets = [x[0] for x in by_q[key]]; risks = [x[1] for x in by_q[key]]
        print(fmt(stats(nets, risks, key)))

    print("\n[B6] KRONOLOJİK BÖLME — ilk %70 (eğitim) vs son %30 (KÖR TEST)")
    cut = t[int(n * 0.7)]
    for gname in ("BOT 80/110 (canlı VIXREG)", "ATR 1.0 : 1.0", "ATR 0.75 : 1.0 (yüksek WR)"):
        for label, keep in (("EĞİTİM", lambda e: e["ts"] < cut), ("TEST ", lambda e: e["ts"] >= cut)):
            sub = [e for e in reds if e["klass"] == "BOSLUKTA" and keep(e)]
            if len(sub) < 20:
                continue
            rr = run(sub, "SELL").get(gname)
            if not rr:
                continue
            nets = [r["net"] for r, _k, _e in rr]; risks = [k for _r, k, _e in rr]
            print(fmt(stats(nets, risks, f"{label} | {gname}")))

    print("\n[B7] PLASEBO / TABAN — koşulsuz SELL (her 6. bar) aynı geometrilerle")
    base_evs = [{"i": i, "px": float(c[i]), "atr": float(atr[i]), "ts": int(t[i]),
                 "near_below": None}
                for i in range(warmup, n - args.horizon - 1, 6)
                if np.isfinite(atr[i]) and atr[i] > 0]
    res_base = run(base_evs, "SELL")
    for gname, rowsb in res_base.items():
        nets = [r["net"] for r, _k, _e in rowsb]; risks = [k for _r, k, _e in rowsb]
        print(fmt(stats(nets, risks, "TABAN " + gname)))

    print("\n[B1b] SONUÇ DAĞILIMI (TP / SL / zaman-stopu) — 'WR' kâr eden işlem oranıdır")
    for gname in ("BOT 80/110 (canlı VIXREG)", "ATR 1.0 : 1.0"):
        rowsx = res_all[gname]
        mix = {}
        for r, _k, _e in rowsx:
            mix[r["outcome"]] = mix.get(r["outcome"], 0) + 1
        tot = len(rowsx)
        bars_ = np.mean([r["bars"] for r, _k, _e in rowsx])
        print(f"  {gname:<34} TP=%{100 * mix.get('WIN', 0) / tot:.1f}  "
              f"SL=%{100 * mix.get('LOSS', 0) / tot:.1f}  "
              f"ZAMAN=%{100 * mix.get('TIME', 0) / tot:.1f}  ort.süre={bars_:.0f} bar")

    print("\n[B8] AYNA KONTROLÜ — büyük YEŞİL mum sonrası BUY (aynı kurallar)")
    res_g = run(greens, "BUY")
    for gname, rowsg in res_g.items():
        nets = [r["net"] for r, _k, _e in rowsg]; risks = [k for _r, k, _e in rowsg]
        print(fmt(stats(nets, risks, gname)))

    # ── BÖLÜM D — KURTARMA DENEMESİ: filtre taraması + KÖR TEST ─────────────
    print("\n" + "─" * 96)
    print("BÖLÜM D — BU FİKİR KURTARILABİLİR Mİ? filtre taraması (eğitim) → KÖR TEST")
    print("─" * 96)
    print("  protokol: aday filtreler YALNIZ ilk %70'te sıralanır; kazananın son %30'daki")
    print("  (hiç bakılmamış) sonucu yazılır. Eğitimde iyi + testte çöken = gürültü.")

    FILTERS = {
        "trend AŞAĞI (H1 EMA50 altı)": lambda e: e["trend_known"] and e["trend_down"],
        "trend YUKARI (H1 EMA50 üstü)": lambda e: e["trend_known"] and not e["trend_down"],
        "konum ≤0.35 (dalga dibi)": lambda e: np.isfinite(e["pos"]) and e["pos"] <= 0.35,
        "konum ≥0.65 (dalga tepesi)": lambda e: np.isfinite(e["pos"]) and e["pos"] >= 0.65,
        "hacim ≥1.3×": lambda e: np.isfinite(e["vol_ratio"]) and e["vol_ratio"] >= 1.3,
        "hacim <1.0× (sakin)": lambda e: np.isfinite(e["vol_ratio"]) and e["vol_ratio"] < 1.0,
        "gövde ≥1.5×ATR": lambda e: e["body_atr"] >= 1.5,
        "ABD seansı": lambda e: e["session"] == "ABD",
        "AVRUPA seansı": lambda e: e["session"] == "AVRUPA",
        "destek BOŞLUKTA": lambda e: e["klass"] == "BOSLUKTA",
        "destek DESTEKTE": lambda e: e["klass"] == "DESTEKTE",
        "seviye KIRDI (kapanışla)": lambda e: e["broke_level"],
        "önceki mum da kırmızı": lambda e: e["prev_red"],
        "yüksek volatilite (ATR %70+)": lambda e: e["atr_pctile"] >= 0.70,
        "düşük volatilite (ATR %30-)": lambda e: e["atr_pctile"] <= 0.30,
    }
    geo_for_sweep = ("BOT 80/110 (canlı VIXREG)", "ATR 1.0 : 1.0", "ATR 0.75 : 1.0 (yüksek WR)")
    cache = {}
    for gname in geo_for_sweep:
        for r, k, e in res_all[gname]:
            cache.setdefault(gname, {})[e["i"]] = (r["net"], k, e)

    names = list(FILTERS)
    combos = [(a,) for a in names] + [(a, b) for ia, a in enumerate(names)
                                      for b in names[ia + 1:]]
    ranked = []
    for gname in geo_for_sweep:
        rows_g = list(cache[gname].values())
        for combo in combos:
            fns = [FILTERS[x] for x in combo]
            tr = [(net, k) for net, k, e in rows_g
                  if e["ts"] < cut and all(f(e) for f in fns)]
            if len(tr) < 100:
                continue
            ev_tr = float(np.mean([x[0] / x[1] for x in tr]))
            ranked.append((ev_tr, gname, combo, len(tr)))
    ranked.sort(reverse=True)
    print(f"\n  {'#':>2} {'geometri + filtre':<62}{'EĞİTİM':>18}{'KÖR TEST':>26}")
    for rank, (ev_tr, gname, combo, n_tr) in enumerate(ranked[:12], 1):
        fns = [FILTERS[x] for x in combo]
        te = [(net, k) for net, k, e in cache[gname].values()
              if e["ts"] >= cut and all(f(e) for f in fns)]
        label = f"{gname.split(' (')[0]} + " + " + ".join(combo)
        if len(te) < 25:
            print(f"  {rank:>2} {label[:60]:<62}{ev_tr:>+9.3f}R n={n_tr:<6}  TEST n<25 (atlandı)")
            continue
        rr = np.asarray([x[0] / x[1] for x in te])
        wr = 100.0 * float((rr > 0).mean())
        print(f"  {rank:>2} {label[:60]:<62}{ev_tr:>+9.3f}R n={n_tr:<6}"
              f"{float(rr.mean()):>+10.3f}R n={len(te):<5} WR=%{wr:.0f}")
    surv = 0
    for ev_tr, gname, combo, _n in ranked[:12]:
        fns = [FILTERS[x] for x in combo]
        te = [(net, k) for net, k, e in cache[gname].values()
              if e["ts"] >= cut and all(f(e) for f in fns)]
        if len(te) >= 25 and float(np.mean([x[0] / x[1] for x in te])) > 0:
            surv += 1
    print(f"\n  → eğitimin en iyi 12 adayından KÖR TESTTE de +EV kalan: {surv}/12 "
          f"(şans beklentisi ≈6/12 — bu sayı 6'nın belirgin üstünde değilse kenar YOK)")

    # ── BÖLÜM C — bot teşhisi: konum kapısı ─────────────────────────────────
    print("\n" + "─" * 96)
    print("BÖLÜM C — BOT TEŞHİSİ: VIXREG SELL'in girdiği KONUM bandı (4s dalga, kapı=0.40)")
    print("─" * 96)
    if h1 is None:
        print("  H1 verisi yok → atlandı (MT5'siz koşuluyor).")
    else:
        aligned = trend_down & trend_known              # SELL hizası (sızıntısız)
        print("  (örtüşen işlemler var: min 24 bar arayla örneklendi, ufuk 72 bar "
              "→ n şişkin, güven aralığı dar okunmalı)")
        band_defs = [("0.40–0.50 (kapının hemen üstü)", 0.40, 0.50),
                     ("0.50–0.65", 0.50, 0.65),
                     ("0.65–0.80", 0.65, 0.80),
                     ("0.80–1.00 (dalga tepesi)", 0.80, 1.01),
                     ("0.00–0.40 (kapının blokladığı)", 0.0, 0.40)]
        min_gap = 24                                    # örtüşmeyi azalt (yine de tam bağımsız değil)
        for label, lo_b, hi_b in band_defs:
            nets, risks, last = [], [], -10 ** 9
            for i in range(warmup, n - args.horizon - 1):
                if not aligned[i] or not np.isfinite(pos[i]) or not np.isfinite(atr[i]):
                    continue
                if not (lo_b <= pos[i] < hi_b) or i - last < min_gap:
                    continue
                last = i
                r = simulate(i, c[i], c[i] - BOT_TP_POINTS, c[i] + BOT_SL_POINTS,
                             h, l, c, args.horizon, args.spread, "SELL")
                nets.append(r["net"]); risks.append(BOT_SL_POINTS)
            s = stats(nets, risks, label)
            p = bootstrap_p_positive(nets, risks)
            print(fmt(s) + f"  P(EV>0)={'-' if p is None else f'%{100 * p:.0f}'}")
        print("\n  [C2] KAPI GEÇİŞ ANI — konum 0.40'ı aşağıdan yukarı kestiği ilk bar "
              "(botun bugün yaptığı giriş biçimi)")
        for thr in (0.40, 0.50, 0.60, 0.70):
            nets, risks, last_cross = [], [], -10 ** 9
            for i in range(warmup, n - args.horizon - 1):
                if not aligned[i] or not np.isfinite(pos[i]) or not np.isfinite(pos[i - 1]):
                    continue
                if pos[i] >= thr > pos[i - 1] and i - last_cross >= 12:
                    last_cross = i
                    r = simulate(i, c[i], c[i] - BOT_TP_POINTS, c[i] + BOT_SL_POINTS,
                                 h, l, c, args.horizon, args.spread, "SELL")
                    nets.append(r["net"]); risks.append(BOT_SL_POINTS)
            s = stats(nets, risks, f"konum {thr:.2f} geçişinde SELL")
            p = bootstrap_p_positive(nets, risks)
            print(fmt(s) + f"  P(EV>0)={'-' if p is None else f'%{100 * p:.0f}'}")

    # ── BÖLÜM E — kullanıcının gözlemi: SELL yükselen mumların içine açılıyor ─
    print("\n" + "─" * 96)
    print("BÖLÜM E — KULLANICI GÖZLEMİ: bot SELL'i YÜKSELEN mumların içine açınca ne oluyor?")
    print("─" * 96)
    if h1 is None:
        print("  H1 verisi yok → atlandı.")
    else:
        aligned = trend_down & trend_known
        gate_pos = 0.40                                # botun mevcut konum kapısı
        pool = []                                      # (i, mom2, mom1)
        last = -10 ** 9
        for i in range(warmup, n - args.horizon - 1):
            if not aligned[i] or not np.isfinite(pos[i]) or not np.isfinite(atr[i]):
                continue
            if pos[i] < gate_pos or i - last < 24:
                continue
            last = i
            pool.append((i, (c[i] - c[i - 2]) / atr[i], (c[i] - c[i - 1]) / atr[i]))
        print(f"  popülasyon: botun BUGÜNKÜ kapılarını geçen anlar "
              f"(H1 EMA50 altı + konum ≥{gate_pos:.2f}), n={len(pool)}, geometri 80/110")

        def run_pool(sel, label):
            nets, risks = [], []
            for i, m2, m1 in pool:
                if not sel(m2, m1):
                    continue
                r = simulate(i, c[i], c[i] - BOT_TP_POINTS, c[i] + BOT_SL_POINTS,
                             h, l, c, args.horizon, args.spread, "SELL")
                nets.append(r["net"]); risks.append(BOT_SL_POINTS)
            s = stats(nets, risks, label)
            p = bootstrap_p_positive(nets, risks)
            print(fmt(s) + f"  P(EV>0)={'-' if p is None else f'%{100 * p:.0f}'}")
            return nets, risks

        print("\n  [E1] SON 2 MUMUN NET HAREKETİ (giriş anında, ATR birimi)")
        for label, lo_b, hi_b in (("son 2 mum GÜÇLÜ YUKARI (≥+1.0 ATR)", 1.0, 99.0),
                                  ("son 2 mum yukarı (0 … +1.0)", 0.0, 1.0),
                                  ("son 2 mum aşağı (−1.0 … 0)", -1.0, 0.0),
                                  ("son 2 mum GÜÇLÜ AŞAĞI (≤−1.0 ATR)", -99.0, -1.0)):
            run_pool(lambda m2, m1, a=lo_b, b=hi_b: a <= m2 < b, label)
        print("\n  [E2] SON MUM yeşil mi kırmızı mı")
        run_pool(lambda m2, m1: m1 > 0, "son mum YEŞİL")
        run_pool(lambda m2, m1: m1 <= 0, "son mum kırmızı")
        print("\n  [E3] ÖNERİLEN EK KAPI — 'yukarı momentumun içine SELL açma'")
        for thr in (0.5, 0.75, 1.0):
            run_pool(lambda m2, m1, x=thr: m2 < x, f"mom2 < +{thr:.2f} ATR ise aç (kapılı)")
        run_pool(lambda m2, m1: True, "KAPISIZ (bugünkü davranış)")
        print("\n  [E4] AYNI KURAL — kronolojik KÖR TEST (ilk %70 / son %30)")
        for label, keep in (("EĞİTİM", lambda ts: ts < cut), ("TEST  ", lambda ts: ts >= cut)):
            for tag, sel in (("kapısız", lambda m2: True),
                             ("mom2<+0.75 kapılı", lambda m2: m2 < 0.75)):
                nets, risks = [], []
                for i, m2, m1 in pool:
                    if not keep(t[i]) or not sel(m2):
                        continue
                    r = simulate(i, c[i], c[i] - BOT_TP_POINTS, c[i] + BOT_SL_POINTS,
                                 h, l, c, args.horizon, args.spread, "SELL")
                    nets.append(r["net"]); risks.append(BOT_SL_POINTS)
                print(fmt(stats(nets, risks, f"{label} | {tag}")))

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump({"symbol": args.symbol, "bars": int(n),
                       "from": int(t[0]), "to": int(t[-1]),
                       "n_red": len(reds), "n_green": len(greens),
                       "events": [{k: (None if isinstance(x, float) and not np.isfinite(x) else x)
                                   for k, x in e.items()} for e in reds]},
                      f, ensure_ascii=False)
        print(f"\n[bilgi] olaylar kaydedildi → {args.json_out}")
    print("\nBİTTİ.")


if __name__ == "__main__":
    main()
