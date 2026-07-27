"""
free_context.py — XAU "serbest zekâ" modu: çok-TF ham bağlam (kanıt-tablosu YOK).
=============================================================================
FELSEFE: XAUUSD intraday'de doğrulanmış edge YOK (kanıtlandı: çöp). O yüzden Opus'a
kanıt-tablosu (evidence_tables) dayatmak yerine, ÇIPLAK TEMEL BAĞLAM veriyoruz ve kendi
zekâsıyla karar veriyor — bir insan trader'ın grafiğe bakıp yorumlaması gibi.

Kanıt-temelli akıştan (gates+evidence) AYRI. Yalnız XAUUSD için. Riskli deneysel mod →
ayrı journal etiketi (mode:"free"), küçük boyut, ayrı ölçüm. Kaybedecek edge yok; kazanç
Opus'un ham piyasa okuması iyiyse gelir.

Verilen bağlam (kanıt DEĞİL, ham gözlem):
 - Çok-TF trend: 1m/5m/30m/1h EMA20/50 dizilimi + son 100 mum özeti (yön, momentum)
 - Trend-channel: linreg z (fiyat kanalın neresinde) her TF
 - S/R: son 100 mumdan pivot destek/direnç + mevcut fiyata mesafe
 - Makro: VIX + DXY ham değer (yön kanıtı DEĞİL — makro→XAU bağı bizim veride çöktü)
 - ATR (stop boyutu için)
"""
from __future__ import annotations
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from channel_filter import channel_zscore, vwap_zscore  # noqa: E402
from evidence import _adx, _atr, _session  # noqa: E402
from datetime import datetime, timezone  # noqa: E402


def _ema(vals, period):
    if not vals:
        return None
    k = 2.0 / (period + 1); e = vals[0]
    for v in vals[1:]:
        e = v * k + e * (1 - k)
    return e


def _pivots(bars, lookback=100, left=3, right=3):
    """Fraktal pivot S/R (son lookback mum). Dönüş: (destekler, dirençler) fiyat listesi."""
    win = bars[-lookback:]
    highs = [b["high"] for b in win]; lows = [b["low"] for b in win]
    sup, res = [], []
    for i in range(left, len(win) - right):
        if lows[i] == min(lows[i - left:i + right + 1]):
            sup.append(lows[i])
        if highs[i] == max(highs[i - left:i + right + 1]):
            res.append(highs[i])
    return sorted(set(sup)), sorted(set(res))


def _tf_summary(bars):
    """Bir TF için ham özet: trend (EMA dizilimi), channel z, momentum, son 100 mum yönü."""
    if not bars or len(bars) < 55:
        return None
    closes = [b["close"] for b in bars]
    ema20 = _ema(closes[-80:], 20); ema50 = _ema(closes[-120:], 50) if len(closes) >= 50 else None
    price = closes[-1]
    cz = channel_zscore(closes, 50)
    vz = vwap_zscore(bars, 50)
    adx = _adx([b["high"] for b in bars], [b["low"] for b in bars], closes)
    # son 100 mum net yön (ilk-son % değişim)
    w = closes[-100:] if len(closes) >= 100 else closes
    chg = (w[-1] - w[0]) / w[0] * 100 if w[0] else 0
    trend = "yukarı" if (ema50 and ema20 and ema20 > ema50 and price > ema20) else \
            "aşağı" if (ema50 and ema20 and ema20 < ema50 and price < ema20) else "yatay/karışık"
    return {
        "trend": trend,
        "price_vs_ema20": round((price - ema20) / ema20 * 100, 2) if ema20 else None,
        "channel_z": round(cz, 2) if cz is not None else None,   # + üstte, − altta, |z|≈2 sınır
        "vwap_z": round(vz, 2) if vz is not None else None,
        "adx": round(adx, 1) if adx is not None else None,
        "chg_100bar_pct": round(chg, 2),
    }


def build_free_context(bars_by_tf: dict, vix=None, dxy=None) -> dict | None:
    """XAU için çok-TF ham bağlam. bars_by_tf: {'1m':[...],'5m':[...],'30m':[...],'1h':[...]}.
    Her biri {high,low,close,volume,time}, eski→yeni. En az 5m gerekli."""
    base = bars_by_tf.get("5m")
    if not base or len(base) < 55:
        return None
    price = base[-1]["close"]
    atr5 = _atr([b["high"] for b in base], [b["low"] for b in base], [b["close"] for b in base])

    tfs = {}
    for tf in ("1m", "5m", "30m", "1h"):
        s = _tf_summary(bars_by_tf.get(tf))
        if s:
            tfs[tf] = s

    # S/R en yakın (30m tercih — swing yapısı; yoksa 5m)
    sr_bars = bars_by_tf.get("30m") or base
    sup, res = _pivots(sr_bars)
    near_sup = max([s for s in sup if s < price], default=None)
    near_res = min([r for r in res if r > price], default=None)
    now = datetime.now(timezone.utc)
    return {
        "symbol": "XAUUSD", "price": round(price, 3), "atr_5m": round(atr5, 3) if atr5 else None,
        "bar_time_5m": base[-1].get("time"),   # MT5-frame (outcomes broker-saat tutarlı grade)
        "session": _session(now.hour), "now_utc": now.isoformat(timespec="minutes"),
        "multi_tf": tfs,
        "support": round(near_sup, 3) if near_sup else None,
        "resistance": round(near_res, 3) if near_res else None,
        "dist_to_support_atr": round((price - near_sup) / atr5, 2) if (near_sup and atr5) else None,
        "dist_to_resistance_atr": round((near_res - price) / atr5, 2) if (near_res and atr5) else None,
        # 2026-07-27: vix_regime etiketi + "yüksek DXY → altına baskı" notu KALDIRILDI —
        # makro→XAU yön bağı bizim veride çöktü (xauusd-macro-direction: 2024-26 işaret
        # değişimi; VIX rejimi yalnız NDX'te doğrulandı). Ham sayı kalır, anlatı kalmaz.
        "macro": {"vix": vix, "dxy": dxy,
                  "note": "ham bağlam — makro→XAU yön bağı bizim veride ÇÖKTÜ; yön kanıtı sayma"},
    }


if __name__ == "__main__":
    import math
    def mk(n, base=2000, drift=0.0):
        return [{"high": base + drift * i + math.sin(i / 6) + 0.5, "low": base + drift * i + math.sin(i / 6) - 0.5,
                 "close": base + drift * i + math.sin(i / 6), "volume": 1000, "time": 1782640800 + i * 60}
                for i in range(n)]
    ctx = build_free_context({"1m": mk(120, drift=-0.05), "5m": mk(120, drift=-0.1),
                              "30m": mk(120, drift=0.2), "1h": mk(120, drift=0.3)}, vix=17.5, dxy=103.2)
    import json
    print(json.dumps(ctx, ensure_ascii=False, indent=2))
