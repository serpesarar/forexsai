# DAX profesörü — piyasa yapısı, mevcut işlemlerin otopsisi, yeni kapılar

2026-11-12 · ön kayıt `PROTOCOL.md` (+EK-1) · kod bu klasörde · otopsi `otopsi/rapor.md` · sonuçlar `results/`

## 1. DAX nasıl bir piyasa (bizim işimize yarayan kısmı)

| özellik | ne demek | bizim için sonucu |
|---|---|---|
| **Performans endeksi** (temettüler yeniden yatırılır) | Temettü düşüşü yok; uzun vadede yukarı sürüklenme fiyat endekslerinden güçlü | Uzun yön tabanı artı, "uzun kalma primi"ni kenar sanma (E13) |
| **Xetra 09:00–17:30 Berlin**, açılış müzayedesi 08:50–09:00, kapanış müzayedesi 17:30–17:35, **gün-içi müzayede 13:00** | Hacmin tepesi 09:00 ve 15:30 (ABD açılışı) | GER40 CFD 01:15–22:00 işlem görür; nakit saatleri dışında fiyatı vadeli/ABD belirler |
| **Eurex FDAX/ODAX**: her ayın 3. Cuması 13:00 uzlaşma, Mart/Haziran/Eylül/Aralık çeyrek vadesi | Opsiyon yapıcılarının hedge akışı | D2'de sınandı: vade haftası DAX'ta ayırt edici değil (X) |
| **40 hisse, ihracatçı ağırlıklı** (SAP, Siemens, Allianz, otomotiv, kimya) | Küresel büyüme, Çin talebi, EUR/USD, ABD teknoloji duyarlılığı | Gün-içi yönü kendi mumundan çıkarmak defalarca X; DAX'ı ABD ve küresel risk iştahı sürüklüyor |
| **Makro takvim**: ECB (Perşembe 14:15 karar, 14:45 basın), Ifo (10:00), ZEW (11:00), PMI (09:30–10:00), ABD NFP/CPI 14:30, **FOMC 20:00 Berlin — Xetra kapandıktan sonra** | Haber oynaklık taşır, yön taşımaz (HB-01…03) | FOMC'nin Xetra kapanışından SONRA gelmesi DAX'a "saf duyuru öncesi" günü veriyor → D3 |
| **Korku ölçüsü VDAX-NEW** | DAX'ın kendi oynaklık endeksi | yfinance'te yok; CAPREV/C3b VIX ile çalışıyor (DAX'ta da tuttu) |

Defterin DAX'ta dayanan bütün bulguları aynı durumda: **endeks + uzun + korku/stres + zaman çıkışı** (CAPREV DAX, C3b GER40,
teyitli çekiç GER40, K1 geri çekilme). Kendi OHLC'sinden gün-içi yön (açılış aralığı, FVG, SMC, kanal, çizgi, yapı, gösterge
kombinasyonu) DAX'ta da her seferinde X çıktı.

## 2. Mevcut DAX işlemleri — 111 işlem, 2026-06-30 → 11-12 (`otopsi/rapor.md`)

Saat ekseni hizalı (%95,5), yol yeniden oynatması gerçek TP/SL'yi %100 tutuyor → sayılar güvenilir.

| aile | n | isabet | başabaş | ort R | net $ | lot / risk medyanı |
|---|---|---|---|---|---|---|
| MOM/SR (BUY) | 41 | %53,7 | %55,2 | +0,04 | −415 | 5,0 lot · ≈260 $ |
| CHREV (BUY 23 / SELL 14) | 37 | %67,6 | %64,2 | +0,05 | **+2.847** | 5,0 lot · ≈670 $ (SL 119 / TP 67) |
| DECIDER (BUY) | 30 | %53,3 | %60,2 | −0,11 | −10 | 0,1 lot · ≈4 $ |
| ÇEKİÇ | 2 | %0 | %17 | −1,00 | −92 | 0,5 lot |
| **toplam** | **111** | **%57,7** | **%58,9** | **−0,02** [−0,18…+0,16] | **+2.537** | |

Okuma:
1. **Para var ama kenar yok.** Ortalama R −0,02, P(EV>0) %44. +2.537 $'ın kaynağı lot farkı: CHREV işlem başına ≈670 $ riskle
   +0,05R yapıyor, decider 4 $ riskle −0,11R. Dolar eğrisini sinyal değil lot çiziyor (§3-21).
2. **Botun giriş anı rastgeleden iyi değil:** aynı saat, aynı yön, aynı SL/TP ile ±10 gün içinden rastgele giriş −0,06R daha iyi
   (P(bot iyi) %27). CHREV SELL'de rastgele giriş +0,14R, botunki 0,00.
3. **SL'lerin %36'sı hiç çalışmamış** (MFE < 0,15R) ve %23'ü "yön doğru, stop erken". Ama geometri karşı-olgusunda stop genişletmek
   işlem başına en fazla +0,04R getiriyor (SL ×2) → sorun stop değil giriş.
4. Hacim (tick hacmi) SL ile TP'yi giriş anında ayırmıyor (AUC 0,45–0,53). 65 özelliğin hiçbiri keşif + odakta tutarlı değil;
   otopsinin aday önlem bölümü veri azlığından boş. **Mevcut işlemlerden kanıtlı kapı çıkmıyor.**
5. Görünen ama kanıt sayılmayacaklar (E12, küçük n): Pazartesi 14 işlem +0,47R; gece/ön-seans (09:00 öncesi) 27 işlem +0,14R.
   Bunları kapı yapmak 111 işlemlik tek dönemde seçim yapmak olur.

## 3. Yeni kapı araması — üç ön-kayıtlı hipotez + bir ek

| ID | hipotez | sonuç | hüküm |
|---|---|---|---|
| **DP-01 (D1)** | DAX-KSG: 16:30→17:30 Berlin düştüyse 17:30 AL → ertesi 09:00 SAT (NAS100 KSG'nin kör taşınması), broker GER40 M30 2019-10→2026-11 | n 842, net **+1,0 bp**, P %64; karşı kol +0,3 → fark +0,7 (P %58); yarılar −0,2 / +2,2; yıl 5/8; spread ×3 ≈ 0. Brüt gece primi +3,8 bp ama kapanış saati yönü bilgi taşımıyor | **X** |
| **DP-02 (D2)** | Eurex vade haftası (aylık / çeyrek "Hexensabbat" / vade sonrası hafta), ^GDAXI 1990-2026 + broker | Aylık fark KEŞİF −19, TEST −5, broker −37 bp; çeyrek −46 / 0 / −61; vade sonrası KEŞİF −22, TEST +12. Sahte vade haftaları ±50–60 bp sallanıyor → takvim gürültüsü | **X** |
| **DP-03 (D3)** | **FOMC öncesi DAX:** FOMC'dan önceki işlem günü kapanışı → FOMC günü kapanışı (duyuru 20:00, Xetra 17:30'da kapanmış) | ^GDAXI 2008-26 n 144: **+28,1 bp** vs diğer günler +2,7 → fark **+25,4, P %98,3**; yarılar +27 / +24; broker GER40 +29,7 (P %95,6). Bkz. §4 | **B** |
| DP-04 (EK-1, sonradan) | FOMC'nin ertesi günü DAX uzun açma (veto) | ^GDAXI **−26,8 bp** (yarılar −19 / −35, en kötü 5 hariç −12,5, yıl 12/19 eksi); Euro Stoxx −28, CAC −27, FTSE −23; broker 19:30 → ertesi 17:30 **−40 bp**. **Ama taze 3 olayın 3'ü de ters (+30 / +77 / +130 bp)** | **C−** (sonradan + taze veride ters; yalnız gölge etiketi) |

## 4. DP-03 — FOMC öncesi DAX: kanıt dosyası

**Kural:** FOMC gününden önceki işlem günü 17:30 Berlin'de GER40 AL → FOMC günü 19:30'da SAT (duyuru 20:00'den önce, stop yok).
Yılda 8 olay. Kazanç gece ve gün boyu birikiyor; duyuru riski taşınmıyor.

Broker gün-içi yolu (önceki gün 17:30'dan, ort. bp, n 52): 20:00 −1,6 · 08:00 +17,0 · 11:00 +22,8 · 13:00 +26,0 · 15:30 +27,6 ·
17:30 +33,7 · 19:30 **+34,1**.

**Canlıya alma kartı** (`backend/data/evolution/go_live_cards/dax_fomc_oncesi.json`), broker GER40 2019-10 → 2026-06, gerçek
spread × 1,5 + gece swap'ı:

| # | ölçüt | değer | geçti |
|---|---|---|---|
| 1 | hacim ≥ 150 | 52 (günlük 144) | ✗ |
| 2 | beklenti | net **+31,9 bp**, P(EV>0) %99,8 | ✓ |
| 3 | kararlılık | yarılar +51,8 / +12,0 | ✓ |
| 4 | sürtünme | spread × 1,5 sonrası +30,7 | ✓ |
| 5 | icra | iyimser (bar kapanışı, spread'siz) +34,1 vs gerçek +31,9 → fark 2,3 | ✓ |
| 6 | sıra-bağımlı | olay başına tek pozisyon | ✓ |

**5/6 → SHADOW.** Hacim ölçütü seyrek günlük kenarları yapısal olarak reddediyor (§3-21). Bunun yerine geçen kontroller:
- **Sahte tarih plasebosu:** FOMC tarihleri ±5…15 işlem günü kaydırılınca ortalama +3,7 bp, gerçek +28,1 → p = 0,009.
- **Gün eşli kontrol:** FOMC olmayan Çarşambalar +5,6, Salılar +9,8 → hafta günü etkisi değil.
- **En iyi 5 gün hariç** +16,7 bp; medyan +16,0 (diğer günler +6,8).
- **Yan piyasalar (sonradan, seçimsiz, dördü birden raporlandı):** Euro Stoxx 50 +29,6, CAC +30,2, FTSE +21,8, Nikkei +18,9
  (diğer günler +1…+4) → mekanizma küresel: Lucca & Moench (2015) "FOMC öncesi sürüklenme"nin Avrupa'daki karşılığı.
- **VIX (sonradan):** önceki gün VIX ≥ 18,4 → +38,1 bp (n 64); altı +20,1 (n 80). Korku büyütüyor, sakin piyasada da artı.

**Zayıf yanlar (dürüst liste):**
1. **Son iki yıl eksi:** 2025 −12,0, 2026 −35,5 bp (≈12 olay; olay başına σ ≈ 100 bp → standart hata ≈ 30 bp, gürültüyle uyumlu
   ama literatürdeki "yayın sonrası sönme" riskiyle de uyumlu). Yıl tablosu 12/19 artı. Broker ikinci yarısı +12 (ilki +52).
2. Tek dönem: FOMC takvimi 2008'den başlıyor; 1994-2007 bağımsız eski dönem sınanmadı (backlog).
3. Bu oturumda 5 sınama yapıldı; D3'ün tek başına p'si 0,017, beşli Holm ile 0,085. Sahte tarih plasebosu (p 0,009) ve dört yan
   piyasa bu yükü kısmen karşılıyor ama tamamen değil.
4. NDX'te yakın tanımlar daha önce X (GF-07 SELL vetosu; HB-03 S7 NDX 2024-25 uzun, P ≤ %93). NDX nakit kapanışı duyurudan sonra
   olduğu için orada "saf öncesi" gün yok — DAX'ın avantajı tam burada.

**Taze veri (takvim dosyasında olmayan 2026-07-29, 09-16, 10-28 toplantıları; kural bunları görmeden donduruldu):**
DP-03 −4,4 / +41,3 / +37,6 bp (ort. +24,8, 2/3 artı) → tutarlı. **DP-04 ise üçünde de ters:** ertesi gün +29,6 / +77,2 / +130,2 bp.

**Portföy notu:** 2008-26'da DAX duyurudan önce yükselip ertesi gün geri veriyordu (+28 → −27 bp), ama ertesi gün vetosu (DP-04)
en yeni üç olayda üçte üç yanlış çıktı. Bu yüzden DP-04 kapı DEĞİL, yalnız gölge etiketi. O günlerde açılan bot DAX uzunları:
2026-07-30 CHREV BUY ×2 (+0,56R, +0,56R), 2026-10-29 MOM/SR BUY (−1R) — veto net olarak para kaybettirirdi.
DP-03'ün kendisi (duyurudan ÖNCE çık) duyuru sonrası yönden bağımsızdır.

## 5. Öneri

| aday | sınıf | öneri |
|---|---|---|
| DP-03 FOMC öncesi DAX uzun | B (kart 5/6) | **GÖLGE**; ileri 8 olay/yıl. Canlı kararı sizde. Önerilen lot küçük (0,5), acil SL %3 |
| DP-04 FOMC ertesi DAX uzun vetosu | C− | Canlı vetoya BAĞLAMA (taze 3/3 ters). En fazla gölge etiketi `shadow:fomc_ertesi`, ≥30 olayda oku |
| DP-01, DP-02 | X | Deftere işlendi, tekrar edilmeyecek |
| Mevcut DAX aileleri | — | Kapı çıkmadı. MOM/SR ve decider DAX'ta başabaş; CHREV'in $ katkısı lot büyüklüğünden. Lot = kanıt sınıfı ilkesine göre DAX MOM/SR ve CHREV lotlarının gözden geçirilmesi önerilir (karar sizde) |

Sıradaki araştırma: FOMC 1994-2007 bağımsız dönem; ECB toplantı günü öncesi (14:15 karar Xetra açıkken — farklı yapı) için takvim
verisi; VDAX verisi bulunursa CAPREV/C3b'nin DAX'ta VDAX'la sınaması.
