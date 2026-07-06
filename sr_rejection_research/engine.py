"""
Faz 1 — S/R + trend-channel motoru (LOOKAHEAD'SİZ).
- Bar yükle (native: 1m/5m/30m/1h; türetilmiş: 15m=5m, 4h=1h).
- Fractal pivot S/R (pivot i+right'ta teyit → sinyal anında yalnız teyitliler aktif).
- Linreg trend channel (son n bar).
- Sinyal anında: en yakın destek/direnç mesafesi (%), 'recently touched' (rejection),
  kanal pozisyonu + sınıra mesafe.
"""
from __future__ import annotations
import json, bisect
from pathlib import Path
import numpy as np

DATA = Path("/Users/melihcanodacioglu/Desktop/panel/sr_rejection_research/data")


def _iso_ep(s: str) -> float:
    from datetime import datetime
    return datetime.fromisoformat(s).timestamp()


# Tüm TF'ler TEMİZ 5m tabanından türetilir (native 1h XAU'da snapshot-kirli;
# tutarlılık + temizlik için 5m→15m/30m/1h/4h). 1m ayrı native.
_DERIVE_SEC = {"5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400}


def load_bars(symbol: str, tf: str):
    """(epoch, o,h,l,c,v) listesi."""
    if tf == "1m":
        f = DATA / f"{symbol}_1m.json"
        if not f.exists():
            return []
        rows = json.loads(f.read_text())
        return [(_iso_ep(r["candle_time"]), r["open"], r["high"], r["low"],
                 r["close"], r.get("volume", 0)) for r in rows]
    f5 = DATA / f"{symbol}_5m.json"
    if not f5.exists():
        return []
    rows = json.loads(f5.read_text())
    base = [(_iso_ep(r["candle_time"]), r["open"], r["high"], r["low"],
             r["close"], r.get("volume", 0)) for r in rows]
    if tf == "5m":
        return base
    return _resample(base, _DERIVE_SEC[tf])


def _resample(bars, sec):
    buckets = {}
    for ep, o, h, l, c, v in bars:
        k = int(ep - (ep % sec))
        g = buckets.get(k)
        if g is None:
            buckets[k] = [o, h, l, c, v]
        else:
            g[1] = max(g[1], h); g[2] = min(g[2], l); g[3] = c; g[4] += v
    return [(k, g[0], g[1], g[2], g[3], g[4]) for k, g in sorted(buckets.items())]


def fractal_pivots(bars, left=3, right=3):
    """Swing H/L; her pivot i 'confirmed_at'=i+right (lookahead kontrolü için)."""
    n = len(bars)
    piv = []
    for i in range(left, n - right):
        hi = bars[i][2]; lo = bars[i][3]
        win = range(i - left, i + right + 1)
        if all(bars[i][2] >= bars[j][2] for j in win if j != i):
            piv.append({"i": i, "price": hi, "kind": "R", "conf": i + right})
        if all(bars[i][3] <= bars[j][3] for j in win if j != i):
            piv.append({"i": i, "price": lo, "kind": "S", "conf": i + right})
    return piv


_TF_SEC = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400}


def precompute(symbol, tf, left=3, right=3, lookback=120, chan_n=50):
    """Sembol/TF için motor durumu: barlar + pivotlar + bar epoch index."""
    bars = load_bars(symbol, tf)
    piv = fractal_pivots(bars, left, right)
    eps = [b[0] for b in bars]
    closes = np.array([b[4] for b in bars], dtype=float)
    piv_sorted = sorted(piv, key=lambda p: p["conf"])
    conf_idx = [p["conf"] for p in piv_sorted]
    # Günlük-anchored VWAP (broker-gün başında resetlenir) — bar başına
    daily_vwap = []
    cum_pv = cum_v = 0.0; last_day = None
    for (ep, o, h, l, c, v) in bars:
        day = int(ep // 86400)
        if day != last_day:
            cum_pv = cum_v = 0.0; last_day = day
        tp = (h + l + c) / 3.0
        cum_pv += tp * v; cum_v += v
        daily_vwap.append(cum_pv / cum_v if cum_v > 0 else c)
    return {"bars": bars, "eps": eps, "closes": closes, "piv": piv_sorted,
            "conf_idx": conf_idx, "lookback": lookback, "chan_n": chan_n,
            "left": left, "right": right, "tf_sec": _TF_SEC[tf],
            "daily_vwap": daily_vwap}


def bar_at(state, epoch):
    """Sinyalden ÖNCE TAM KAPANMIŞ son barın indexi (LOOKAHEAD YOK).
    candle_time=açılış; bar open+tf_sec ≤ epoch olmalı (forming bar elenir)."""
    i = bisect.bisect_right(state["eps"], epoch) - 1
    if i >= 0 and state["eps"][i] + state["tf_sec"] > epoch:
        i -= 1                       # forming bar → son KAPALI bara in
    return i


def features_at(state, epoch, price):
    """Sinyal anı özellikleri: en yakın S/R mesafe %, touched, kanal pozisyonu."""
    i = bar_at(state, epoch)
    if i < 35 or i >= len(state["bars"]):
        return None
    bars = state["bars"]
    # aktif pivotlar: conf <= i (teyitli) ve son lookback bar içinde
    hi = bisect.bisect_right(state["conf_idx"], i)
    active = [p for p in state["piv"][:hi] if p["i"] >= i - state["lookback"]]
    sup = [p["price"] for p in active if p["kind"] == "S" and p["price"] <= price]
    res = [p["price"] for p in active if p["kind"] == "R" and p["price"] >= price]
    nearest_sup = max(sup) if sup else None
    nearest_res = min(res) if res else None
    d_sup = (price - nearest_sup) / price * 100 if nearest_sup else None
    d_res = (nearest_res - price) / price * 100 if nearest_res else None

    # 'touched' (rejection): son K barda fiyat seviyeye değdi mi
    K = 4
    lo_recent = min(b[3] for b in bars[i - K:i + 1])
    hi_recent = max(b[2] for b in bars[i - K:i + 1])
    touched_sup = (nearest_sup is not None and lo_recent <= nearest_sup * (1 + 0.0005))
    touched_res = (nearest_res is not None and hi_recent >= nearest_res * (1 - 0.0005))

    # Liquidity sweep: son Ksw barda fiyat ÖNCEKİ swing low/high'ı süpürdü (wick aştı)
    # ama şimdi geri döndü (stop-hunt reversal). bull=alt süpürme, bear=üst süpürme.
    Ksw = 5
    sw_lo = min(b[3] for b in bars[i - Ksw + 1:i + 1])
    sw_hi = max(b[2] for b in bars[i - Ksw + 1:i + 1])
    old_sup = [p["price"] for p in active
               if p["kind"] == "S" and p["i"] < i - Ksw and p["price"] <= price]
    old_res = [p["price"] for p in active
               if p["kind"] == "R" and p["i"] < i - Ksw and p["price"] >= price]
    sweep_feat = {"bull": bool(any(sw_lo < L for L in old_sup)),
                  "bear": bool(any(sw_hi > H for H in old_res))}

    # linreg channel — n=30/50/80; pm=(price-mid)/price%, spp=sd/price% sakla.
    # d_chan_low(k)=pm+k*spp, d_chan_up(k)=-pm+k*spp → band-width k sweep ÜCRETSİZ.
    chan = {}
    for nn in (30, 50, 80):
        if i - nn + 1 < 0:
            continue
        y = state["closes"][i - nn + 1:i + 1]
        x = np.arange(nn)
        a, b = np.polyfit(x, y, 1)
        mid = a * (nn - 1) + b
        sd = float((y - (a * x + b)).std())
        chan[nn] = {"pm": (price - mid) / price * 100, "spp": sd / price * 100,
                    "slope_atr": float(a / (sd + 1e-9))}
    c50 = chan.get(50)
    d_chan_low = (c50["pm"] + 2 * c50["spp"]) if c50 else None     # geri uyumluluk (n=50,2σ)
    d_chan_up = (-c50["pm"] + 2 * c50["spp"]) if c50 else None

    adx = _adx14(bars, i, 14)

    # Volume Profile (son lookback bar, no-lookahead): POC + value area (VAH/VAL)
    vp = _volume_profile(bars, i, lookback=100, n_bins=30)
    vp_feat = None
    if vp and vp["va_width"] > 0:
        vp_feat = {
            "vp_pos": (price - vp["poc"]) / vp["va_width"],     # z-benzeri (>0 = POC üstü)
            "above_vah": bool(price > vp["vah"]),               # value area üstü = overbought
            "below_val": bool(price < vp["val"]),               # value area altı = oversold
            "dist_poc_pct": (price - vp["poc"]) / price * 100,
        }

    # VWAP — rolling z-skoru (son 50 bar, hacim-ağırlıklı) + günlük-anchored uzaklık
    n2 = 50
    win2 = bars[max(0, i - n2 + 1):i + 1]
    tps = np.array([(b[2] + b[3] + b[4]) / 3.0 for b in win2])
    vols = np.array([b[5] for b in win2])
    sv = float(vols.sum())
    vwap_roll = float((tps * vols).sum() / sv) if sv > 0 else price
    sd2 = float(tps.std())
    dvwap = state["daily_vwap"][i]
    vwap_feat = {
        "vwap_z": (price - vwap_roll) / sd2 if sd2 > 0 else 0.0,      # rolling VWAP z
        "vwap_daily_dist": (price - dvwap) / price * 100,            # günlük VWAP'tan %
    }

    return {"d_sup": d_sup, "d_res": d_res,
            "touched_sup": touched_sup, "touched_res": touched_res,
            "d_chan_low": d_chan_low, "d_chan_up": d_chan_up,
            "chan": chan, "adx": adx, "vp": vp_feat, "vwap": vwap_feat,
            "sweep": sweep_feat}


def _volume_profile(bars, i, lookback=100, n_bins=30):
    """Hacim profili: son lookback barda fiyat-seviyesine göre hacim histogramı.
    POC (en çok hacimli seviye) + value area (%70 hacmi kapsayan aralık)."""
    s = max(0, i - lookback + 1)
    win = bars[s:i + 1]
    if len(win) < 30:
        return None
    pmin = min(b[3] for b in win); pmax = max(b[2] for b in win)
    if pmax <= pmin:
        return None
    bw = (pmax - pmin) / n_bins
    hist = [0.0] * n_bins
    for b in win:
        tp = (b[2] + b[3] + b[4]) / 3.0                        # hlc3 tipik fiyat
        bi = min(n_bins - 1, max(0, int((tp - pmin) / bw)))
        hist[bi] += b[5]                                       # hacim
    total = sum(hist)
    if total <= 0:
        return None
    poc_bin = max(range(n_bins), key=lambda k: hist[k])
    acc = hist[poc_bin]; lo = hi = poc_bin
    while acc < 0.70 * total and (lo > 0 or hi < n_bins - 1):  # value area = %70 hacim
        left = hist[lo - 1] if lo > 0 else -1.0
        right = hist[hi + 1] if hi < n_bins - 1 else -1.0
        if right >= left:
            hi += 1; acc += hist[hi]
        else:
            lo -= 1; acc += hist[lo]
    return {"poc": pmin + (poc_bin + 0.5) * bw,
            "vah": pmin + (hi + 1) * bw, "val": pmin + lo * bw,
            "va_width": (hi + 1 - lo) * bw}


def _adx14(bars, i, p=14):
    """ADX(14) bar i'de (son ~3p bar, Wilder)."""
    s = max(0, i - 3 * p)
    h = np.array([b[2] for b in bars[s:i + 1]], float)
    l = np.array([b[3] for b in bars[s:i + 1]], float)
    c = np.array([b[4] for b in bars[s:i + 1]], float)
    if len(c) < p + 2:
        return None
    up = h[1:] - h[:-1]; dn = l[:-1] - l[1:]
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    pc = c[:-1]
    tr = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - pc), np.abs(l[1:] - pc)))

    def rma(x):
        r = np.empty_like(x); r[0] = x[0]
        for k in range(1, len(x)):
            r[k] = (r[k - 1] * (p - 1) + x[k]) / p
        return r
    atr = rma(tr); atr = np.where(atr == 0, np.nan, atr)
    pdi = 100 * rma(pdm) / atr; mdi = 100 * rma(mdm) / atr
    dx = 100 * np.abs(pdi - mdi) / np.where((pdi + mdi) == 0, np.nan, pdi + mdi)
    return float(np.nan_to_num(rma(np.nan_to_num(dx))[-1]))
