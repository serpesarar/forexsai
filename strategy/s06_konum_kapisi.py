"""S06 — KONUM KAPISI (mevcut mekanizmanın parametreleri)

Bot'ta zaten var: SELL dalganın alt %40'ından açılmaz (4 saat, POS_SELL_MIN=0,40).
Soru: pencere ve eşik daha iyi seçilebilir mi?

NASDAQ backtest: 6 saat/0,60 → +8.401$ vs baz +4.290$ (20 hücrede yön tutarlı).
⚠️ AMA BOTUN KENDİ GÖLGE ÖLÇÜMÜ TERSİNİ SÖYLEDİ: bloklanacak NDX SELL'ler
%62,0 kazanıyor (başabaş %57,9) → bloklamak para kaybettirir.

📌 METODOLOJİK DERS (bu oturumun en önemlisi):
   Mevcut bir kapıdan (0,40) GEÇMİŞ işlemlere daha sıkı eşik uygulayan backtest,
   sıkı kapının canlıda BLOKLAYACAĞI popülasyonu ölçmez → YANLI.
   Gölge kaydı gerçek bloklanan kümeyi ölçer → gölge kanıtı backtest'i EZER.

Sembol bazlı gerçek karne (gölge, gerçek TP/SL geometrisiyle çözülmüş):
   GDAXI BUY : %28,6 vs başabaş %64,0 → BLOKLA (canlıya alındı)
   NDX  SELL : %62,0 vs %57,9         → BLOKLAMA
   USOIL BUY : %99,0 vs %58,9         → KESİNLİKLE BLOKLAMA
"""
from ortak import sim

ACIKLAMA = "SELL konum < eşik (veya BUY > 1-eşik) ise açma"
IZGARA = [{"saat": s, "esik": e} for s in (2, 4, 6, 8, 12)
          for e in (0.40, 0.50, 0.60, 0.70)]
VERDIKT_NDX = "NDX'te BLOKLAMA (gölge karnesi backtest'i çürüttü); GDAXI'de canlı"


def calistir(v, saat: float = 4, esik: float = 0.40) -> dict:
    out = {}
    for t in v.islemler:
        k = sim.konum(v, t["ts"], saat)
        if k is None:
            out[id(t)] = t["usd"]
            continue
        kotu = (t["yon"] == "SELL" and k < esik) or (t["yon"] == "BUY" and k > 1 - esik)
        out[id(t)] = 0.0 if kotu else t["usd"]
    return out
