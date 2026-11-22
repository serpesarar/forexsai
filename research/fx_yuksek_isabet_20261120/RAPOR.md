# Forex'te %80 isabetli strateji arayışı (2026-11-20)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md) (+ EK-1…EK-6). Defter §2.108 (YI-01…07).

## 1. Bot neden döviz işlemlerinin hepsinde zararda?
17 Kasım 16:30 ET'de `yeni deneme/fx_vixreg_live.py` (VIXREG-FX, FX-01 H12) **16 çiftte aynı anda "risk para birimi uzun"** açtı
(AUDJPY, NZDJPY, CADJPY, AUDUSD, NZDUSD, USDJPY, GBPJPY, EURJPY uzun; USDMXN, USDZAR, USDNOK, USDSEK, USDCAD, EURAUD, EURCAD, GBPAUD kısa;
0,01 lot). Kural: önceki gün VIX ≥ 18,4 ise risk para birimini tut. VIX 22,9 → 25,5 → 24,6 → 28,4'e çıktı: korku arttıkça risk para birimleri
düştü. 16 işlem tek bahis olduğundan hepsi birlikte zararda; "tersini açsaydık hepsi kârdaydı" da aynı yoğunlaşmanın sonucu.
Kuralın araştırma beklentisi küçük (≈ +3,75 bp/gün, Sharpe 0,29) ve korkunun ilk günlerinde kaybedip sakinleşince kazanmayı varsayar.
Not: 19 Kasım penceresinde uzlaştırma kaydı yok (`done` = 18 Kasım); hedef değişmeyeceği için pozisyonlara etkisi yok, nedeni ayrıca bakılmalı.

## 2. %80 araştırması — sonuç: bulunamadı
| Tur | Fikir | Veri | Sonuç |
|---|---|---|---|
| F1 | Gece (18–21 ET) M15 bant dönüşü, 25 çift, 162 hücre | Pepperstone M15 2022–26 | Brüt +1 bp gerçek ama maliyet 1,7 bp → X |
| F2/F3 | Gün içi aşırı uzama sönmesi; Asya aralığı taşması dönüşü | aynı | Brüt ≈ 0 → X |
| EK-1 | Günlük RSI2/büyük gün/seri/trend geri çekilme/Donchian/VIX × 12 geometri, iki yön | D1 1993–2026 | Hiçbir hücre üç dönemde brüt > 2 bp değil → X |
| EK-2 | ABD olay günü ertesi gün devamı × yüksek isabet | D1 1994–2026 | %87,8 isabetli hücre brüt 2,4 < maliyet 2,7 → X |
| EK-3 | F1 gece, düşük maliyetli 4 çift (sonradan seçim) | M15 | KEŞİF %84,5 +0,8 → KÖR %77,4 −1,0 → X |
| EK-4 | NY 10:00 opsiyon vadesi sabitlemesi | M15 | Gerçek = hayalet seviye → X |
| EK-5 | Resmî bant kurları USDHKD / EURDKK | H1 (kutudan yeni) | Spread/swap kazancı aşıyor → X |
| EK-6 | ABD veri anı 3 dk sıçrama devamı, TP ¼, SL 2× | Dukascopy 1m BID+ASK 2012–26 | 2012–18 %82,4 +3,1 bp → 2019–22 %81,1 +1,5 → **2023–26 %74,3 −1,2** → X (kenar söndü) |

| EK-7 | ABD dışı planlı açıklama anı (:00/:30) sıçraması | Dukascopy 1m 2018–26, 4 majör | Brüt +0,1…0,9 < maliyet 2,4 → X |
| **EK-8** | **USDHKD 7,75 taahhüt ucunda al, SL 7,7470, TP +20 pip, süre sınırı yok** | MT5 H1 2010–26 | **İki yarıda %89,4 / %95,8, +1,7 / +2,8 bp; hayalet seviyeler %53–62 eksi → mekanizma gerçek (B). AMA Pepperstone'da USDHKD işleme kapalı (`trade_mode=0`)** |
| ek | EURCHF/EURCZK eski tabanları, USDAED | MT5 | n çok küçük / spread ≈ 40 bp / işleme kapalı |
| EK-11 | Zorunlu akış takvimi (gotobi, ay sonu fiksi, FOMC öncesi) × yüksek isabet geometrisi | MT5 H1 2010–26 | Ay sonu fiksi KEŞİF %80,7 +3,2 bp → TEST %69,6 −0,9, KÖR %72,4 +0,1 → X (2018'den beri söndü) |
| EK-12 | Makine öğrenmesi filtresi (LightGBM meta-etiketleme) gece/gündüz bant dönüşünde | MT5 M15 2022–26 | İsabeti %84'e çıkarıyor ama brüt +0,1, net −1,1 bp → X |
| EK-13 | VIXREG-FX yönünde gün içi geri çekilmeden giriş | MT5 H1 2010–26 | İsabet %73–87, net −3,3…−5,0 bp → X |
| ek | HK3 için ikinci terminal (DBG Markets) | kutu, salt-okuma | HKD sembolü yok → icra yeri yok |
| EK-14 | **Hedef %70 + ayda ≥ 3 sinyal**: tüm eski işlem tabloları yeniden seçildi (≈ 10.700 hücre) | hepsi | Keşifte 4 aday, kör dönemde %55–77 isabet, net ≤ +0,2 (P ≤ 0,54) → X |
| EK-15 | NDX korku gecesi → risk para birimi gecesi | MT5 H1 2010–26 + QQQ | İsabet %45–55, kontrolle aynı → X |
| EK-16 | Saatlik para birimi gücü (en güçlü/en zayıf) dönüş/devam | MT5 H1 2010–26 | İlk koşu ileriye bakıyordu (%75, t 15); düzeltilince %51–56, brüt ≈ 0 → X |
| EK-17 | Kural madencisi: 15.000 basit kural (saat/seans × önceki hareket × yön × tutuş × çift), üç aşamalı süzgeç | MT5 H1 2010–26 | Keşifte geçen yok; yazı-tura yönlü plasebo madenci aynı sayıda "iyi" kural üretiyor → X |
| EK-18 | **Yeni veri: CFTC COT** (spekülatif fon pozisyonu/akışı aşırıysa ters) | CFTC TFF 2010–26 + D1 | Ön kayıtlı seçim boş; iz: %80/%85/%80 ve %67/%65/%69 isabet, üç dönemde artı |
| EK-18b | COT izinin bağımsız sınavı | + CFTC eski rapor 1993–2009 | Yalnız fiyatla aynı sonuç; bakılmamış çiftler ve 1993–2009 eksi → X (iz C) |
| EK-19 | Emtia para birimi adil değeri (CAD/NOK–petrol, AUD–bakır/altın, ZAR–altın) | yfinance 2000–26 + D1 | Hepsi eksi, ilgisiz emtia (mısır) plaseboyla aynı → X |
| EK-20 | Hisse göreli getirisi → para birimi (Hau–Rey) | endeksler 1985→ + D1 | 2010 öncesi işaret doğru, sonrası eksi → X |
| EK-21 | Faiz farkı adil değeri + Fed net likiditesi → USD | ECB/FRED + D1 | Faiz eksi; likidite %77–84 isabet ama t < 1, ayda 1,3 → X |
| EK-22 | **USDHKD vekili**: 13 işlem görebilir enstrüman (HK50, Çin endeksleri/ETF, USDX, USDCNH, USDSGD, altın…) | MT5 D1/H1 | Aynı yönde giden yok (\|ρ\| ≤ 0,31); HK3 sinyali vekilde %8–56 isabet → X |
| EK-23 | COT-TERS geliştirme: kesitsel kalabalık (en kalabalık uzunu sat / kısayı al) | CFTC TFF 2006–26 | 2010–26 %83–86 isabet +6/+11 bp, ayda 3,2–3,5; **2007–10 −40 bp (2008 çöküşü)** → C, canlıya uygun değil |

**Neden?** İsabet oranı strateji kalitesi değil, TP/SL oranının sonucudur: TP 1 / SL 4 ile rastgele giriş bile %75–80 isabet verir
(plasebolar %72–79). İsabeti yükseltmek için TP küçüldükçe işlem başına brüt kenar da küçülüyor; spread + komisyon (majörde 0,7–1,5 bp)
sabit kalıyor. FX'te maliyetin birkaç katı brüt kenar yalnız haber anı gibi büyük hareketlerde vardı, o da 2023'ten beri yok.

## 3. Ne yapılabilir (karar kullanıcıda)
- VIXREG-FX'in 16 korelasyonlu pozisyonu tek risktir; ya demo/0,01 lotta gölge gibi sürsün ya da çift sayısı/lot küçültülsün.
- "%80 isabet" hedefi yerine "maliyet sonrası artı beklenti + kör dönem" hedefi: FX'te ayakta kalanlar H8c gotobi, H9 ay sonu (GÖLGE) ve VIXREG-FX.
- Yeniden açma ancak yeni veriyle: FX opsiyon kullanım fiyatı/vade hacmi (DTCC), emir akışı (CLS), ima oynaklık — elimizde yok.
