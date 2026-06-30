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
