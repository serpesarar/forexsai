"""
forensics.py — her karara ZENGİN FORENSİK SNAPSHOT (SL-otopsi altyapısı).
=============================================================================
Kullanıcının istediği "beynimdeki analiz" — her işlem/karar anında kaydedilir:
 - HACİM: son kapalı barın hacmi / 20-bar ortalaması (vol_ratio)
 - MAKRO: VIX + DXY
 - TREND-KANAL UZAKLIĞI: channel_z + vwap_z her TF'te (1m/5m/30m/1h/4h)
 - ADX + trend dizilimi her TF
 - S/R HER TF'TE: en yakın destek + direnç → fiyat, ATR-mesafe, KAÇ KEZ dokunulmuş
   (güç) ve SON TEPKİ (bounce mı kırılma mı) — "geçmişte oraya çarptı da döndü mü?"

Bu snapshot journal'a gömülür → post_mortem.py WIN'leri LOSS'lardan AYIRAN özelliği
bulur (placebo-kapılı) → yeni filtre adayı. Saf modül: MT5/HTTP yok, test edilebilir.
"""
from __future__ import annotations
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from channel_filter import channel_zscore, vwap_zscore  # noqa: E402
from evidence import _adx, _atr  # noqa: E402

TOL_ATR = 0.15        # S/R dokunuş toleransı (± ATR çarpanı)
CLUSTER_ATR = 0.35    # yakın pivotları tek seviyeye birleştirme eşiği
SR_LOOKBACK = 120     # S/R için taranan mum sayısı (TF başına)


def _ema(vals, period):
    if not vals:
        return None
    k = 2.0 / (period + 1); e = vals[0]
    for v in vals[1:]:
        e = v * k + e * (1 - k)
    return e


def _pivot_levels(bars, left=3, right=3):
    """Fraktal pivotlar → (destek_listesi, direnç_listesi) ham fiyatlar."""
    win = bars[-SR_LOOKBACK:]
    lows = [b["low"] for b in win]; highs = [b["high"] for b in win]
    sup, res = [], []
    for i in range(left, len(win) - right):
        if lows[i] == min(lows[i - left:i + right + 1]):
            sup.append(lows[i])
        if highs[i] == max(highs[i - left:i + right + 1]):
            res.append(highs[i])
    return sup, res


def _cluster(levels: list[float], atr: float) -> list[float]:
    """Birbirine ≤CLUSTER_ATR×ATR yakın pivotları tek seviyeye (ortalama) indir."""
    if not levels or not atr:
        return sorted(set(levels))
    out, grp = [], [sorted(levels)[0]]
    for p in sorted(levels)[1:]:
        if p - grp[-1] <= CLUSTER_ATR * atr:
            grp.append(p)
        else:
            out.append(sum(grp) / len(grp)); grp = [p]
    out.append(sum(grp) / len(grp))
    return out


def _touch_stats(bars, level: float, count_tol: float, react_tol: float, kind: str):
    """Seviyeye dokunuş sayısı + SON TEPKİ. kind='sup' → low'lar dokunur; 'res' → high'lar.
    count_tol = KÜME genişliği (CLUSTER_ATR) — seviye zaten ±bu banttaki pivotların ortalaması,
    dokunuşlar da aynı bantta sayılmalı (dar 0.15 tol kümenin kendi üyelerini SAYMIYORDU →
    'seviye gücü' sistematik düşüktü). react_tol = tepki için dar tolerans (0.15, hassas)."""
    win = bars[-SR_LOOKBACK:]
    touches, last_i = 0, None
    for i, b in enumerate(win):
        probe = b["low"] if kind == "sup" else b["high"]
        if abs(probe - level) <= count_tol:
            touches += 1; last_i = i
    reaction = None
    if last_i is not None and last_i + 1 < len(win):
        after = [b["close"] for b in win[last_i + 1:last_i + 5]]
        if after:
            if kind == "sup":
                reaction = "bounce" if min(after) > level - react_tol else "broke"
            else:
                reaction = "bounce" if max(after) < level + react_tol else "broke"
    return touches, reaction


def _sr_pack(bars, price: float, atr: float) -> dict:
    """En yakın destek+direnç: fiyat, ATR-mesafe, dokunuş gücü, son tepki."""
    if not bars or len(bars) < 40 or not atr:
        return {}
    sup_raw, res_raw = _pivot_levels(bars)
    sups = _cluster(sup_raw, atr); ress = _cluster(res_raw, atr)
    count_tol = CLUSTER_ATR * atr        # dokunuş = küme bandı (üyeler sayılsın)
    react_tol = TOL_ATR * atr            # tepki = dar bant (hassas bounce/broke)
    out = {}
    below = [s for s in sups if s < price]
    above = [r for r in ress if r > price]
    if below:
        lvl = max(below)
        t, rx = _touch_stats(bars, lvl, count_tol, react_tol, "sup")
        out["sup"] = {"level": round(lvl, 5), "dist_atr": round((price - lvl) / atr, 2),
                      "touches": t, "last_reaction": rx}
    if above:
        lvl = min(above)
        t, rx = _touch_stats(bars, lvl, count_tol, react_tol, "res")
        out["res"] = {"level": round(lvl, 5), "dist_atr": round((lvl - price) / atr, 2),
                      "touches": t, "last_reaction": rx}
    return out


def _tf_forensics(bars) -> dict | None:
    """Bir TF'in tam forensiği: kanal/vwap z, ADX, trend, HACİM oranı, S/R paketi."""
    if not bars or len(bars) < 55:
        return None
    closes = [b["close"] for b in bars]
    highs = [b["high"] for b in bars]; lows = [b["low"] for b in bars]
    price = closes[-1]
    atr = _atr(highs, lows, closes)
    ema20 = _ema(closes[-80:], 20); ema50 = _ema(closes[-120:], 50)
    vols = [float(b.get("volume", 0) or 0) for b in bars]
    # SON BAR FORMING (kısmi hacim) olabilir → hacim oranı SON KAPALI bar (-2) ile,
    # önceki 20 kapalı barın ortalamasına karşı. Aksi halde sistematik-düşük yanlış oran.
    vol_ratio = (round(vols[-2] / (sum(vols[-22:-2]) / 20), 2)
                 if len(vols) >= 22 and sum(vols[-22:-2]) else None)
    cz = channel_zscore(closes, 50); vz = vwap_zscore(bars, 50)
    adx = _adx(highs, lows, closes)
    trend = ("yukari" if (ema20 and ema50 and ema20 > ema50 and price > ema20)
             else "asagi" if (ema20 and ema50 and ema20 < ema50 and price < ema20) else "yatay")
    return {
        "channel_z": round(cz, 2) if cz is not None else None,
        "vwap_z": round(vz, 2) if vz is not None else None,
        "adx": round(adx, 1) if adx is not None else None,
        "trend": trend,
        "vol_ratio": vol_ratio,                     # >1.5 = hacim patlaması
        "atr": round(atr, 5) if atr else None,
        "sr": _sr_pack(bars, price, atr),           # en yakın destek/direnç + güç + son tepki
    }


def build_forensics(bars_by_tf: dict, vix=None, dxy=None) -> dict:
    """Tüm TF'lerin forensiği + makro. bars_by_tf: {'1m':[...],'5m':[...],...} (eski→yeni,
    her bar {high,low,close,volume})."""
    tfs = {}
    for tf in ("1m", "5m", "30m", "1h", "4h"):
        f = _tf_forensics(bars_by_tf.get(tf))
        if f:
            tfs[tf] = f
    return {"tfs": tfs, "macro": {"vix": vix, "dxy": dxy}}


if __name__ == "__main__":
    import math, json
    def mk(n, base, drift, vol_spike_last=False):
        out = [{"high": base + drift * i + math.sin(i / 6) + 0.6,
                "low": base + drift * i + math.sin(i / 6) - 0.6,
                "close": base + drift * i + math.sin(i / 6), "volume": 1000} for i in range(n)]
        if vol_spike_last:
            out[-1]["volume"] = 3500
        return out
    f = build_forensics({"5m": mk(150, 2000, 0.05, True), "1h": mk(150, 1990, 0.2),
                         "4h": mk(150, 1970, 0.5)}, vix=18.2, dxy=103.4)
    print(json.dumps(f, ensure_ascii=False, indent=1))
