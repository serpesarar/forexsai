# Korku gecesi küresel mi? K1/K3'ün ABD dışı endekslere taşınması (2026-11-18)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md). Kod: `src/kk.py`, veri çekimi `src/duka_pull.py` (UK100, JPN225).

## Sonuç: K1 küresel değil (0/5) → X; K3 yalnız UK100'de taşındı → C
Kurallar değiştirilmeden yerel nakit kapanışında: kapanışta AL, ertesi gün aynı saatte çık.

| endeks | K1 tetik vs taban (n) | ESKİ | YENİ | K3 tetik vs taban (n) | YENİ K3 |
|---|---|---|---|---|---|
| DAX (17:30 Berlin) | −1,1 vs −0,2 (202), P 0,48 | +15,7 | **−14,0** | +5,7 vs −1,1 (258) | −3,7 |
| CAC (17:30 Paris) | −8,0 vs −1,0 (198), P 0,28 | +3,0 | **−15,8** | +0,1 vs −1,9 (226) | −12,3 |
| EuroStoxx 50 | −19,8 vs −3,5 (211), P 0,07 | −8,0 | **−28,6** | −6,3 vs −4,8 (265) | −9,2 |
| *NDX referans (aynı kod)* | *+54,7 vs −2,0 (252), P 1,00* | *+69,7* | *+44,1* | *+38,7 vs −1,3 (321)* | *+29,2* |

- Aynı kod NDX'te bilinen sonucu yeniden üretiyor (§2.71 K1 +53,2). Avrupa sonucu kod hatası değil.
- Avrupa'da kapanış korkusu ertesi gün dönmüyor. YENİ'de hafif devam ediyor (Stoxx −28,6). ESKİ'deki küçük artılar 2020'den.
- Havuz: K1 −9,8 vs −1,6 (P 0,21); K3 −0,2 vs −2,6 (P 0,59).
- **Ne anlama geliyor:** korku gecesi ABD hisse endekslerine özgü. ABD'nin dört endeksinde var (GI-02), altında ve Avrupa'da yok. Mekanizma
  ABD'ye özgü bir akış. Kapanış müzayedesi penceresi değil (GN-02); korkunun genişliği (GN-03) ve kaynağı (GN-08) da değil.
- **UK100 ve JPN225 (tamamlandı):**
  - UK100 K1 +2,6 vs −2,6 (YENİ −2,3), taşınmadı. UK100 K3 +18,1 vs −4,0 (ESKİ +24,5, YENİ +11,9, P 0,988), taşındı.
    Londra kapanışı 16:30 = ABD sabahı 11:30; ABD seansı içinde kalıyor, bu yüzden ABD akışının bir yansıması olabilir.
  - JPN225 K1 −2,7 vs +0,5 (ESKİ +24,7, YENİ −24,8), K3 −1,2: taşınmadı.
  - Havuz: K1 −6,6 vs −1,3 (P 0,29) → **X**; K3 +2,6 vs −2,2 (P 0,71), 1/5 → **C**.
