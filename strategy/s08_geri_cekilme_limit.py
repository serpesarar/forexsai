"""S08 — GERİ ÇEKİLMEDE DAHA İYİ FİYATTAN GİRİŞ ⭐ (oturumun en iyisi)

Hipotez (S07'nin TERSİ): sinyalde hemen girme; X puan DAHA İYİ fiyata limit koy
(SELL → yukarıdan sat, BUY → aşağıdan al). Süre içinde dolmazsa market'ten gir.

Neden S07'nin tersi çalışıyor: daha iyi fiyattan girmek SL'i fiyattan
UZAKLAŞTIRIR ve TP'yi YAKLAŞTIRIR — S07'de tam tersi oluyordu.

NASDAQ: X=20/30dk market-fallback → +19.606$ vs baz +5.023$.
  · 4/4 çeyrek pozitif (3. çeyrek −2.627 → +5.481)
  · 7/9 hafta · doluluk %74 (211/284)
  · DIŞ-ÖRNEKLEM (bu hafta): +105$ → +970$ ✅ oturumda bunu geçen tek strateji
  · risk-sabit kontrol (SL/TP mutlak seviyede sabit): +21.652$ — kazanç
    yalnız "daha fazla risk"ten değil, gerçekten giriş kalitesinden geliyor

⚠️ UYARI: X'e tepki MONOTON artıyor (X5=+11.288 … X40=+27.266), plato yok.
Model beklemenin maliyetini eksik sayıyor (sinyalin bayatlaması, doluluk
varsayımı). Sonuçlar ÜST SINIR olarak okunmalı → GÖLGE ile başla.

⚠️ Bot'ta altyapı hazır: open_trade_sr pending limit + PENDING_EXPIRY_MIN=30.
Fark: bot limiti S/R bölgesine koyuyor ve SR_FALLBACK_MARKET=False (dolmazsa
ATLA). Test "atla" varyantının çok daha zayıf olduğunu söylüyor (+6.163 vs +19.606).
"""
from bisect import bisect_right
from ortak import sim

ACIKLAMA = "X puan DAHA İYİ fiyata limit; dolmazsa market (veya atla)"
IZGARA = [{"X": x, "sure": s, "dolmazsa": d}
          for x in (5, 10, 15, 20, 30) for s in (10, 20, 30, 60)
          for d in ("market", "atla")]
VERDIKT_NDX = "EN İYİ ADAY — dış-örneklemi geçen tek strateji; X monoton → gölge"


def calistir(v, X: float = 20, sure: int = 30, dolmazsa: str = "market",
             sabit_seviye: bool = False) -> dict:
    """sabit_seviye=True → TP/SL MUTLAK seviyeleri korunur (risk-sabit kontrol)."""
    out = {}
    for t in v.islemler:
        sgn = 1 if t["yon"] == "BUY" else -1
        limit = t["o"] - sgn * X
        sl_sev = t["o"] - sgn * t["sl_d"]
        tp_sev = t["o"] + sgn * t["tp_d"]
        i = bisect_right(v.bar_ts, t["ts"])
        son = t["ts"] + sure * 60
        girdi = None
        for k in range(i, len(v.barlar)):
            tt, o, h, l, c = v.barlar[k]
            if tt > son:
                break
            if (l <= limit) if sgn > 0 else (h >= limit):
                girdi = (tt, limit)
                break
        if girdi is None:
            if dolmazsa == "market":
                pnl, _ = sim.yaris(v, t["ts"], t["o"], t["yon"], t["tp_d"], t["sl_d"])
                out[id(t)] = pnl * t["lot"]
            else:
                out[id(t)] = 0.0
            continue
        if sabit_seviye:
            tp_d, sl_d = abs(tp_sev - girdi[1]), abs(sl_sev - girdi[1])
        else:
            tp_d, sl_d = t["tp_d"], t["sl_d"]
        pnl, _ = sim.yaris(v, girdi[0], girdi[1], t["yon"], tp_d, sl_d)
        out[id(t)] = pnl * t["lot"]
    return out
