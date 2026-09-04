"""S03 — TP BÜYÜTME (sabit hedef yerine k×ATR)

Hipotez: sabit 80 puan yerine volatiliteye ölçekli hedef.

⚠️ DİKKAT — İKİ KEZ ELENDİ:
  * TP_MODE="atr" 2026-08-15'te dış-örneklemde elendi ("kozmetik WR": kazanma
    oranı yükseliyor, para yükselmiyor).
  * Dış AI'ın 2×ATR önerisi de aynı tuzak: WR +14/21pp, para DIŞ +1.448→−2.458$.
BÜYÜTME yönü (3-5×) tarihsel olarak pozitif ama slot-farkındalı testte yalnız
5×'te fayda çıkıyor ve iki simülatör (panel/dış AI) 4,8× farklı sonuç üretti.
→ AÇIK SORU, canlıya alınmadı.
"""
from ortak import sim

ACIKLAMA = "TP = k × ATR(period) — sabit hedefin yerine"
IZGARA = [{"k": k} for k in (1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0)]
VERDIKT_NDX = "AÇIK SORU — 2× kesin zararlı, 5× umutlu ama simülatöre duyarlı"


def calistir(v, k: float = 3.0, atr_bar: int = 15) -> dict:
    out = {}
    for t in v.islemler:
        a = sim.atr(v.barlar, t["ts"], atr_bar)
        if not a:
            out[id(t)] = t["usd"]
            continue
        pnl, _ = sim.yaris(v, t["ts"], t["o"], t["yon"], k * a, t["sl_d"])
        out[id(t)] = pnl * t["lot"]
    return out
