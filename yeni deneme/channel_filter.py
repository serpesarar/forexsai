"""
channel_filter.py — Linreg TREND-CHANNEL rejection filtresi (MEAN-REVERSION edge).
====================================================================================
Araştırma (sr_rejection_research, 2026-06-25, 97k sinyal, OOS+placebo doğrulandı):
sinyal fiyat linreg-channel sınırında iken (z ≤ -zt BUY / z ≥ zt SELL) → model WR
%44-50 → %72-84. En güçlü: 15m-30m, z≈2σ; BUY (alt-band oversold bounce) en iyi.

⚠️ Bu MEAN-REVERSION fırsatı — botun momentum scope'larının ZITTI. Ayrı/opt-in
kullan: momentum scope'larına dokunma; bunu yeni bir 'channel_reversion' yolu veya
düşük-ADX ortamda yüksek-öncelik sinyali olarak değerlendir. Önce gözlemde ölç.
"""
from __future__ import annotations
import numpy as np

# Araştırmadan doğrulanmış varsayılanlar. 2026-06-30: re-damıtma (claude_decider, 21.5k
# deduped sinyal, nested-CV+placebo) z≥2.0/vwap≥1.5'i doğruladı — eski 2.5/2.0 GEREKSİZ
# sıkıydı (özellikle NASDAQ CHREV hiç tetiklenmiyordu, z genelde 0.5-1.2). 2.0/1.5 hâlâ
# OOS-doğrulanmış (pulse3 rev>1.1'de bile ~%77) ama çok daha fazla geçerli sinyal verir.
CHAN_N = 50            # linreg penceresi (bar) — n=30/50/80 hepsi çalışıyor
Z_THRESH = 2.0         # trend çizgisinden ≥2.0σ aşırılık (re-damıtma doğruladı; eski 2.5)
ADX_MAX = 25.0         # düşük-ADX'te edge daha da güçlü (opsiyonel kapı)
# Doğrulanmış en iyi TF: 5m-30m (1m gürültülü/zayıf, 4h az sinyal).


def channel_zscore(closes, n: int = CHAN_N) -> float | None:
    """Fiyatın linreg trend çizgisinden standart-sapma cinsinden uzaklığı.
    z>0: çizginin üstünde, z<0: altında. |z|≈2 = kanal sınırı."""
    if closes is None or len(closes) < n:
        return None
    y = np.asarray(closes[-n:], dtype=float)
    x = np.arange(n)
    a, b = np.polyfit(x, y, 1)
    mid = a * (n - 1) + b
    sd = float((y - (a * x + b)).std())
    if sd <= 1e-9:
        return None
    return (y[-1] - mid) / sd


def is_channel_rejection(closes, direction: str, n: int = CHAN_N,
                         z_thresh: float = Z_THRESH) -> tuple[bool, float | None]:
    """Sinyal kanal sınırı rejection'ında mı? (BUY→alt band z≤-zt / SELL→üst band z≥zt).
    Dönüş: (uygun_mu, z). closes: kapalı barların kapanış listesi (eski→yeni)."""
    z = channel_zscore(closes, n)
    if z is None:
        return False, None
    ok = (z <= -z_thresh) if direction.upper() == "BUY" else (z >= z_thresh)
    return ok, z


def channel_slope_atr(bars, n: int = CHAN_N) -> float | None:
    """Linreg kanal eğimi, ATR14 birimiyle (bar başına). Negatif = düşen kanal.

    2026-07-23 rejim taraması (30g, z-epizodları 1m replay): GDAXI BUY chrev
    düşen kanalda WR %28.6 (−7.8R), yatay/yükselen kanalda %73.7 (+2.9R) —
    'düşen bıçağı satın alma' kapısının sayısal hali."""
    if not bars or len(bars) < max(n, 15):
        return None
    closes = np.asarray([b["close"] for b in bars[-n:]], dtype=float)
    a, _b = np.polyfit(np.arange(len(closes)), closes, 1)
    trs = [max(bars[j]["high"] - bars[j]["low"],
               abs(bars[j]["high"] - bars[j - 1]["close"]),
               abs(bars[j]["low"] - bars[j - 1]["close"]))
           for j in range(len(bars) - 14, len(bars))]
    atr = sum(trs) / len(trs)
    if atr <= 0:
        return None
    return float(a / atr)


VWAP_Z_THRESH = 1.5       # rolling VWAP'tan ≥1.5σ (re-damıtma doğruladı; eski 2.0). Kanala
                          # EK değer (kanalın kaçırdığı kurulumlar; VP redundant, VWAP additive)


def vwap_zscore(bars, n: int = CHAN_N) -> float | None:
    """Rolling VWAP z = (son tipik fiyat − VWAP) / σ(tipik fiyat). Hacim-ağırlıklı.
    bars: dict listesi high/low/close/volume (eski→yeni)."""
    if not bars or len(bars) < n:
        return None
    win = bars[-n:]
    tp = np.array([(b["high"] + b["low"] + b["close"]) / 3.0 for b in win], dtype=float)
    vol = np.array([float(b.get("volume", 0) or 0) for b in win], dtype=float)
    sv = vol.sum()
    if sv <= 0:
        return None
    vwap = float((tp * vol).sum() / sv)
    sd = float(tp.std())
    if sd <= 1e-9:
        return None
    return (tp[-1] - vwap) / sd


def adx_from_bars(bars, p: int = 14) -> float | None:
    """Wilder ADX(p) — bars: dict listesi high/low/close (eski→yeni).

    2026-08-05 GDAXI CHREV olayı: kanal z=-2.89 (BUY tetik) VE kanal eğimi
    hâlâ pozitif (+0.165 ATR/bar, 50-bar/25 saatlik regresyon önceki 1.5 günlük
    ralliyi taşıyordu) iken açılan BUY, güçlü bir gün-içi trend kırılımında SL
    yedi (−687$). ADX o anda 30.1 idi (kırılımdan ÖNCE de 33-37 — piyasa zaten
    trend rejimindeydi, 'range' değil). ADX_MAX=25.0 sabiti tanımlıydı ama hiçbir
    yerde KULLANILMIYORDU — bu fonksiyon onu gerçek bir hesaplamaya bağlar."""
    if not bars or len(bars) < p + 2:
        return None
    h = np.asarray([b["high"] for b in bars], dtype=float)
    l = np.asarray([b["low"] for b in bars], dtype=float)
    c = np.asarray([b["close"] for b in bars], dtype=float)

    def _rma(x: np.ndarray, period: int) -> np.ndarray:
        r = np.empty_like(x, dtype=float)
        r[0] = x[0]
        a = 1.0 / period
        for i in range(1, len(x)):
            r[i] = x[i] * a + r[i - 1] * (1 - a)
        return r

    up = h[1:] - h[:-1]
    dn = l[:-1] - l[1:]
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    pc = np.roll(c, 1); pc[0] = c[0]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))[1:]
    atr = _rma(tr, p)
    atr_safe = np.where(atr == 0, np.nan, atr)
    plus_di = 100 * _rma(plus_dm, p) / atr_safe
    minus_di = 100 * _rma(minus_dm, p) / atr_safe
    denom = np.where((plus_di + minus_di) == 0, np.nan, plus_di + minus_di)
    dx = np.nan_to_num(100 * np.abs(plus_di - minus_di) / denom)
    adx = _rma(dx, p)
    return float(adx[-1])


def is_mean_reversion(bars, direction: str, n: int = CHAN_N,
                      chan_z: float = Z_THRESH, vwap_z: float = VWAP_Z_THRESH):
    """KANAL z≥2.5 VEYA VWAP z≥2.0 ekstremi → mean-reversion fırsatı.
    Dönüş: (uygun_mu, kaynak['channel'/'vwap'/None], z). BUY: oversold / SELL: overbought."""
    d = direction.upper()
    closes = [b["close"] for b in bars]
    cz = channel_zscore(closes, n)
    if cz is not None and ((cz <= -chan_z) if d == "BUY" else (cz >= chan_z)):
        return True, "channel", round(cz, 2)
    vz = vwap_zscore(bars, n)
    if vz is not None and ((vz <= -vwap_z) if d == "BUY" else (vz >= vwap_z)):
        return True, "vwap", round(vz, 2)
    return False, None, round(cz if cz is not None else (vz or 0.0), 2)


# ── Bota entegrasyon reçetesi (yorum) ────────────────────────────────────────
# 1) Bot 1m/5m/15m/30m bar çeker (candles_tf zaten var). 30m veya 15m kapanışlarını al.
# 2) z = channel_zscore(closes_30m). is_channel_rejection(closes, dir) True ise:
#       → bu sinyal MEAN-REVERSION kanal-rejection fırsatı (WR ~%72-80 beklenir).
# 3) Kullanım seçenekleri (opt-in, momentum scope'larından ayrı):
#    a) Ayrı 'channel_reversion' scope: yalnız rejection True iken aç (S/R-pullback gibi).
#    b) Düşük-ADX kapısı: ADX(30m)<25 + rejection → en yüksek WR (%80).
#    c) Önce LIVE_TRADING=False gözlemde fill+WR ölç, sonra canlı.
