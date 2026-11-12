# DAX 11–12 Kasım 2026 — işlem otopsisi

Kaynak: kutudaki Pepperstone MT5 geçmişi (hesap 61628380, `pull.py`, salt-okuma) + `bot_trades` otopsisi
(`output/islem_otopsi/2026-11-12_2138_dax`, saat ekseni ALIGNED %96,2) + 400 günlük tüm-sembol tabanı
(`output/islem_otopsi/2026-11-12_2142_all`, 1.080 işlem). Ön kayıt `PROTOCOL.md`. Kutuda bu yedi işlemden başka GER40 işlemi yok
(21:40 UTC, açık GER40 pozisyonu yok).

## Yedi işlem (UTC)
| # | aile | lot | giriş → çıkış | giriş | SL / TP | sonuç | $ |
|---|---|---|---|---|---|---|---|
| 421440870 | CEKIC | 0,5 | 11-11 09:00 → 09:18 | 26.648,5 | 26.538,1 / 27.200,5 | SL | −61,5 |
| 421446095 | MOMSR | 10 | 11-11 09:15 → 09:18 | 26.593,9 | 26.540,8 / 26.629,2 | SL | −591,6 |
| 421458031 | DECIDER | 0,1 | 11-11 09:27 → 09:36 | 26.556,1 | 26.513,2 / 26.584,5 | SL | −4,8 |
| 421467972 | DECIDER | 0,1 | 11-11 09:47 → 10:31 | 26.549,1 | 26.506,2 / 26.577,7 | TP | +3,2 |
| 422342928 | DECIDER | 0,1 | 11-12 11:00 → 11:08 | 26.886,2 | 26.851,0 / 26.909,6 | TP | +2,6 |
| 422352199 | DECIDER | 0,1 | 11-12 11:21 → 12:29 | 26.886,8 | 26.852,0 / 26.910,0 | SL | −3,9 |
| 422374628 | CHREV | 10 | 11-12 12:00 → 13:09 | 26.883,1 | 26.764,0 / 26.950,0 | SL | −1.319,8 |

İki gün: 7 işlem, 2 TP / 5 SL, −1.976 $, ort −0,52R. Zararın %97'si iki 10 lotluk işlemde (MOMSR −592, CHREV −1.320).

## Ne oldu
**11-11:** DAX 08:30'da 26.682'ye çıktı, 09:00–09:30 arasında 26.513'e indi. Üç motor bu düşüşe 27 dakika içinde ardı ardına AL açtı.
- **CEKIC:** çekiç teyidi 09:00'da tamamlandı. SL'i 07:00 dibine (26.538,1) koydu; fiyat 09:18'de 26.538,0'a inip stopu 0,1 puanla aldı, 09:30'da 26.513'e kadar indi.
- **MOMSR:** 10 lot girdi; giriş anında son 15 dakikanın düşüşü 1,6 ATR5 kadardı. 3 dakikada SL oldu, en iyi anı +0,00R.
- **DECIDER:** önceki iki işlem stoplandıktan 9 dakika sonra girdi, o da SL oldu. Sonraki girişi TP'ye ulaştı.
- **Gün sonu:** fiyat 26.780'e döndü. MOMSR'nin TP'si (26.629) ancak ~6 saat sonra geldi.

**11-12:** DAX 09:30'da 27.022 zirvesini gördü, 11:00'de 26.870'e indi.
- **DECIDER:** iki kez AL girdi (11:00 TP, 11:21 SL).
- **CHREV:** 12:00'de 10 lot AL girdi. Bu anda DECIDER'ın 11:21 işlemi hâlâ açık ve zarardaydı.
- **13:07–13:11 çöküşü:** 4 dakikada 26.900'den 26.727'ye indi. CHREV'in stopu (26.764) 13:09'da gitti, gün dibi 15:00'te 26.688 oldu.
- **Çöküşün nedeni belirsiz.** Haber akışında aynı dakikalarda "Trump: Iran deal not needed" başlığı var (13:09:10). Fiyat bir dakika önce düşmeye başlamıştı, bu yüzden neden olduğu kanıtlanmadı.
- **Arka plan:** sıcak Ekim TÜFE'si (11-10) sonrası Fed artırım beklentisi ve Nvidia açılış öncesi −%7 haberi.
- **CHREV TP'si:** 26.950'ye dönülmedi; akşam fiyat 26.834'te durdu.

## Teşhis
1. **"Düşen bıçağı yakalamak" sezgisi botun geçmişinde doğrulanmıyor.**
   - DAX+NDX AL işlemlerinde (n 206) son 60 dakikası en çok düşmüş üçte bir +0,094R, en çok yükselmiş üçte bir +0,042R.
   - DAX'ta en kötü dilim düşüşü almak değil, yükselişi kovalamak: DAX AL işlemlerinin son 60 dakikası en çok yükselmiş üçte biri −0,142R (n 33).
   - Defterde aynı fikir iki kez elendi: bıçak yakalama kapısı (IO-25 H1, X) ve kayıp sonrası tekrar giriş / kovalama (IO-04, X).
   - Bu iki gün kötü bir rastlantı, tekrar eden bir örüntü değil.
2. **Asıl sorun aynı düşüşe birden fazla motorun girmesi (Y1/Y2).**
   - Motorlar birbirinden habersiz. 11-11'de tek bir yön bahsi üç ayrı işleme dönüştü. 11-12'de CHREV, DECIDER'ın zarardaki pozisyonunun üstüne 10 lot ekledi.
   - **Y1** (aynı sembol ve yönde açık bot pozisyonu varken giriş): Δ −0,03R, P 0,59 → X.
   - **Y2** (o açık pozisyon zarardayken giriş): n 44; −0,157R vs +0,003R, Δ −0,16R; P(Δ<0) 0,87, %95 aralığı [−0,43; +0,14].
   - Y2 iki yarıda da eksi (−0,16 / −0,25) ve aileye göre tabakalı fark da eksi (−0,17). 400 günde toplam −8.311 $; DAX'ta n 15, −0,10R.
   - **Hüküm:** ön kayıttaki P ≥ 0,95 ölçütü tutmadı → **C**, yalnız gölge etiketi olarak izlenebilir.
3. **CHREV'in DAX riski iki katına çıkmış (Y3, ölçüm).**
   - DAX CHREV SL'i her işlemde sabit ~119 puan, TP ~67 puan: RR 0,56, başabaş isabet %64.
   - Lot 2026-09-14'te 5'ten 10'a çıktı. Bir SL artık ≈1.320 $, yani yaklaşık iki TP'yi siliyor.
   - Önceki 9 CHREV DAX işleminin 9'u da TP'ydi. Bu SL, kuralın %31'lik beklenen kaybı; kuralın bozulduğunu göstermiyor.
   - Lot zamanlaması kanıt taşımıyor (MA-05): lot büyütme kararı ayrıca sorgulanmalı.
4. **Giriş anı rastgeleden iyi değil.** Aynı geometriyle rastgele girişe göre eşli fark −0,05R/işlem (P(fark>0) %29,5, n 104, 120 gün).
   - Odak penceresinde SL'lerin 3'ü "hiç çalışmadı" (MFE < 0,15R).
   - Stopu genişletmek tüm dönemde aynı riskte en fazla +0,05R getiriyor ve IO-13 / OLD-20 ile zaten X.
5. **CEKIC stopu bariz dibe kondu, 0,1 puanla alındı.** Bu kuralın tasarımı (FR-15: SL = çekiç dibi). Fiyat sonra 25 puan daha indiği için daha geniş bir stop da kurtarmazdı. Değişiklik önerilmiyor.

## Öneriler
- (a) **Kanıtlı ve uygulanabilir:** yok.
- (b) **Gölge adayı (C):**
  - Y2 "zarardaki aynı yön pozisyonuna başka aileden ekleme" bot logunda etiketlensin; emir akışı değişmesin. ≥100 etiketli işlemde yeniden ölçülsün:
    `python3 research/dax_gun_otopsi_20261112/yigilma.py` (taban CSV'yi `islem_otopsi --symbol all --base-days 400` ile yenile).
  - Aynı mekanizmanın alternatif biçimi: sembol başına toplam açık risk tavanı (ör. DAX'ta aynı yönde en fazla 1,5× tek işlem riski). Bu ayrı ön kayıt gerektirir.
- (c) **Yapma:** bıçak yakalama kapısı (IO-25), kayıp sonrası bekleme / kovalama (IO-04), stop genişletme (IO-13), BE/kilit (M9), zaman stopu (M7).

## EK — gölgeye bağlandı (2026-11-12, commit b3c16222)
`yeni deneme/yigilma_shadow.py`: emir göndermez, giriş engellemez. Her 30 sn hesabın son 8 günlük deal geçmişini okur (decider dahil), her yeni pozisyonu Y1/Y2 ile `yigilma_shadow.jsonl`'e yazar, kapanınca $ ve R ekler; Y2'de logda `YIĞILMA-GÖLGE Y2` uyarısı. Gerçek deal verisiyle parite: 11-10 MOMSR (+752 $, CEKIC −5,9 p), 11-11 MOMSR, 11-12 CHREV Y2. Kutuda ilk çalışma 163 geçmiş girişi `retro` etiketledi (karne dışı). Karne: `python yigilma_shadow.py --karne`. Kapatma: `config.YIGILMA_SHADOW_ENABLED = False`.
