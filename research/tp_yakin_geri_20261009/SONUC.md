# Sonuç — "TP'nin %92'sine geldi, %50'ye döndü → kapat / koru" (2026-10-09)

`run.py` (ön-kayıt docstring'de) · `results/kurallar.csv`. 569 bağımsız bot kararı, broker 1m, yönetimsiz taban.
Kullanıcı tarifi "TP'yi %30'a çek" — fiyat %50'deyken TP %30'a çekilirse TP fiyatın arkasında kalır → fiilen %50'de
kapanış (V2). V1 = SL'yi +%30'a çek (tetikte SL=%30 ile özdeş).

Tetiklenen küme küçük: ≥%92'ye gelip SONRA SL olan **15** işlem; ≥%92'ye gelip TP olan **144**.

## Ana kural (%92 → %50'de kapat)
| kapsam | n | toplam fark R | işlem başı | P(>0) | kurtarılan SL | kesilen TP |
|---|---:|---:|---:|---:|---:|---:|
| TÜMÜ | 569 | **+9,6** | +0,017 | %94 | 15 | 35 |
| NDX | 312 | +2,9 | +0,009 | %72 | 9 | 24 |
| NDX BUY / SELL | 76 / 236 | +0,05 / +2,9 | | %47 / %74 | 2 / 7 | 7 / 17 |
| USOIL | 147 | +8,9 | +0,060 | %99 | 6 | 4 |
| DAX / XAU | 68 / 42 | −0,8 / −1,3 | | %0 / %0 | 0 | 3 / 4 |
| 1. yarı / **2. yarı** | 284 / 285 | +10,9 / **−1,3** | | %99 / %36 | | |
| 09-02 öncesi / **sonrası** | 464 / 105 | +11,3 / **−1,7** | | %97 / %16 | | |

V1 (SL +%30): TÜMÜ +8,8R, NDX +3,9R, 2. yarı −1,8R — aynı desen, daha az TP kesiyor (21).

Izgara (tetik %85–95 × dönüş %40–60): %90–95 tetiklerinde TÜMÜ +8…+11R, NDX +3…+6R — tutarlı; %85'te NDX ≈0.
2. yarıda 15 hücrenin 11'i hafif negatif (−0,2…−1,8R), 4'ü hafif pozitif (+0,1…+0,9R).

## Hüküm
- %80/%30 kilidinden (IO-10: −0,3R, 57 TP kesiyor) çok daha iyi: geç tetik kazanan öldürmeyi azaltıyor.
- Ama ön-kayıtlı ölçütü GEÇMEDİ: kazancın tamamı 1. yarı/09-02 öncesi ve ağırlıkla USOIL (M9'da USOIL kilidi bağımsız
  örneklemde −8,1R vermişti). Son dönemde hafif negatif; NDX'te anlamlı değil (P %72).
- Zarar tarafı küçük (2. yarı işlem başı −0,005R) → "pahalı değil ama kanıtlı da değil". GÖLGE ölçümüne uygun (C).
- Not: canlı NDX BUY'da BE30+koştur (M3) var — TP'ye gelince kapanmıyor, bu tablo yönetimsiz. Seviye dolumu kaymasız.
Defter: IO-16.

## Ek — dönüş seviyesi taraması (`geri_tarama.py`)
- 09-02 sonrası %92'ye gelen 33 işlemin **32'si TP**, 1'i SL (06.10 DAYCOMBO NDX BUY). 32 TP'nin 8'i tetikten sonra %50'nin
  altına inip yine TP oldu (medyan geri çekilme TP'nin %82'si) → %50 kuralı bunları erken kesti, P(>0) %16'nın sebebi.
- Tüm dönem ızgarası (tetik %90–95 × dönüş %0–85): en büyük toplam tetik %90 / dönüş %85 → +16,2R. Bu fiilen "TP'yi ~%85–90'a
  indirmek"tir (IO-13: TP küçültme dönemler arası taşınmıyor).
- Dürüst sınama (bir dönemde seç → diğerinde ölç): 09-02 öncesinde seç (%90/%85, +17,7R) → sonrasında **−1,5R** (P %19);
  1. yarıda seç → 2. yarıda **+0,5R** (P %55). Sonradan seçilenler öncesinde iyi (+9,6…+13,8R) çünkü öncesi (USOIL ağırlıklı)
  hemen her varyantı ödüllendiriyor. İleri yönde hiçbir hücre güvenilir değil; 09-02 sonrasında ulaşılabilecek en iyi değer
  +0,8R/105 işlem (%94/%80) — korunacak SL yok.
- NDX %92 tetik: dönüş %70 tüm dönem +4,1R / 09-02 sonrası +0,5R (en iyi NDX hücresi; kanıt değil).
