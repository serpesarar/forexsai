"""S02 — CUMA ÖĞLEDEN SONRA BLOĞU

Hipotez (dış AI + panel doğrulaması): Cuma ≥12:00 UTC girişleri zararlı.

NASDAQ: Cuma ≥12 n=24 −4.050$, Cuma <12 n=16 +48$. Plasebo p=0,015.
Eşik platosu 10-15 UTC'nin hepsinde iyi. Hafta-çıkarma 9/9.
⚠️ Kutuda `NDX_FRIDAY_BLOCK` ZATEN tüm Cuma'yı bloklıyordu (~2026-08-07'den).
→ Kanıt mevcut kanonik bayrağa bağlandı, repo varsayılanı True yapıldı.
⚠️ GER40'ta Cuma ≥12 POZİTİF (+1.047$, n=7) → genellenmez, sembol bazlı bak.
"""
import datetime as dt

ACIKLAMA = "Cuma saat >= X UTC ise giriş yapma"
IZGARA = [{"saat": s} for s in (10, 11, 12, 13, 14, 15)]
VERDIKT_NDX = "DOĞRU ama YENİ DEĞİL — NDX_FRIDAY_BLOCK zaten canlıydı"


def calistir(v, saat: int = 12) -> dict:
    out = {}
    for t in v.islemler:
        d = dt.datetime.fromtimestamp(t["ts"], tz=dt.timezone.utc)
        out[id(t)] = 0.0 if (d.weekday() == 4 and d.hour >= saat) else t["usd"]
    return out
