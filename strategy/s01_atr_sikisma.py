"""S01 — ATR SIKIŞMA FİLTRESİ

Hipotez (dış AI, 2026-08-28): ATR14(1m)/ATR100(1m) < 1,00 ise piyasa sakin;
kırılım sinyali "likidite fitili"dir, giriş elenmeli.

NASDAQ verdikti: DIŞ-örneklemde elenen küme n=122 ortR −0,070 (−4.399$),
kalan +0,111. Permütasyon p=0,043 (yalnız 1,00'da; komşular geçmiyor).
→ GÖLGE (canlıda SQZ_FILTER_BLOCK=False).
"""
from ortak import sim

ACIKLAMA = "ATR14/ATR100 (1m) < eşik ise giriş yapma"
IZGARA = [{"esik": e} for e in (0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.20)]
VERDIKT_NDX = "GÖLGE — permütasyon yalnız 1,00'da geçti, 3. çeyrek negatif kaldı"


def calistir(v, esik: float = 1.00) -> dict:
    out = {}
    for t in v.islemler:
        s = sim.sikisma(v.barlar, t["ts"])
        out[id(t)] = 0.0 if (s is not None and s < esik) else t["usd"]
    return out
