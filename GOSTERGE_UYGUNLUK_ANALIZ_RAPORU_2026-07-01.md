# ForexSAI — Gösterge Uygunluk Analiz Raporu

**Tarih:** 2026-07-01
**Kapsam:** 6 sinyal modelinin (ML, PULSE 1/2/3, EMEL, SMC) 4 sembol için kullandığı teknik/analitik göstergelerin uygunluk denetimi
**Odak:** XAUUSD ve GDAXI.INDX (yanlış yön + SL problemi)
**Metodoloji:** Kod denetimi (tüm model servisleri satır satır kataloglandı) + Supabase `prediction_logs` son 60 gün canlı sonuç verisi (resolved sinyaller) ile çapraz doğrulama

---

## 1. Yönetici Özeti — 5 Ana Bulgu

**Bulgu 1 — XAUUSD'de sorun gösterge eksikliği değil, YÖN ASİMETRİSİ.**
Son 60 günde tüm modellerde BUY win rate %64-85 bandında, SELL win rate %19-32 bandında. Altın ATH/güçlü trend ortamındayken modellerin mean-reversion mantığı (RSI aşırı alım, üst banda dokunma, momentum tükenmesi) sürekli SELL üretiyor ve bunlar SL oluyor. Yanlış olan gösterge seti değil, göstergelerin **trend ortamında ters yorumlanması**.

**Bulgu 2 — Kanıt sistemin içinde: EMEL XAUUSD %84.8 WR.**
EMEL'in ATH-zone SELL bloğu fiilen tüm SELL'leri kesmiş (60 günde EMEL XAUUSD'de yalnızca BUY üretmiş: 234W/42L). Aynı korumaya sahip olmayan PULSE 1/2/3 %38-41'de. Yani çözüm zaten kodda var, sadece tek modele uygulanmış.

**Bulgu 3 — DAX'ta sorun gösterge değil, GEOMETRİ + SEANS.**
GDAXI'de PULSE 1 hem düz (%25 WR) hem ters çevrilince (%38 WR) kaybediyor — sinyal tersine çevrilebilir bilgi bile taşımıyor. Stopped sinyallerin ortalama MFE'si 7 pip iken SL 65-68 pip: girişler anında ters gidiyor. Sabit TP 20 / SL 12 point geometrisi DAX'ın 5m gürültüsünün içinde kalıyor. NDX'te aynı PULSE 1 ters çevrilince %61 kazanıyor — yani PULSE mantığı NDX'te "ters bilgi", DAX'ta "gürültü".

**Bulgu 4 — "SL oluyor" şikayetinin yarısı exit yönetimi.**
XAUUSD'de stopped sinyallerin %46-58'i (pulse1: 1430/2472, pulse2: 981/1766, pulse3: 1070/2327) **önce TP1'e ulaşmış, sonra SL'ye dönmüş**. TP1 sonrası SL'yi girişe çeken (breakeven) bir kural yok. Tek başına bu kural, kayıt edilen kayıpların büyük bölümünü nötr/kazanca çevirir.

**Bulgu 5 — Saat etkisi ölçülebilir ve kullanılmıyor.**
XAUUSD: en kötü saat 20:00 UTC (%37.9 WR) ve Asya gecesi 01-03 UTC (~%42); en iyi 12-13 UTC Londra-NY overlap (%50.8-52.8). GDAXI: 07-12 UTC Avrupa sabahı %39.9-42.8, 13:00 UTC %52.4. Modellerde session feature yalnızca ML-XAUUSD'de var; PULSE/EMEL/SMC'de saat filtresi yok.

---

## 2. Canlı Performans Verisi (Son 60 Gün, prediction_logs)

### 2.1 Model × Sembol Win Rate (resolved = completed+stopped)

| Model | XAUUSD | GDAXI | NDX | USOIL |
|---|---|---|---|---|
| **emel** | **84.8** (234W/42L) | 50.0 | 44.3 | **8.5** ⚠️ |
| **ml:balanced** | 60.7 | **71.3** | 57.1 | 58.2 |
| **ai_panel** | 71.0 | 67.3 | 69.2 | 52.3 |
| **meta** | 60.2 | 50.2 | 43.4 | 48.9 |
| **smc** | 55.6 | 44.1 | 42.4 | 58.6 |
| **pulse2** | 40.7 | 51.6 | 42.4 | 44.4 |
| **pulse3** | 39.4 | 39.4 | 38.5 | 46.4 |
| **pulse1** | 37.7 | **25.0** | 28.8 | 42.8 |

### 2.2 Yön Kırılımı — Asıl Hikaye Burada

**XAUUSD (BUY / SELL win rate):**

| Model | BUY WR | SELL WR | SELL hacmi |
|---|---|---|---|
| pulse1 | 69.4 | **19.1** | 478W / **2024L** |
| pulse2 | 64.5 | **20.3** | 326W / 1279L |
| pulse3 | 70.9 | **19.7** | 466W / 1899L |
| smc | 80.1 | 31.8 | 113W / 242L |
| ml:main | 79.7 | 31.8 | 61W / 131L |
| meta | 77.7 | 41.6 | 77W / 108L |
| emel | 84.8 | — (ATH bloğu SELL üretmemiş) | 0 |

→ XAUUSD'deki toplam PULSE kaybının ~%75'i SELL sinyallerinden. **Tek kural (trend/ATH ortamında SELL bloğu) PULSE'ların WR'ını ~%65+ seviyesine taşır** (BUY-only senaryo).

**GDAXI (BUY / SELL win rate):**

| Model | BUY WR | SELL WR |
|---|---|---|
| pulse1 | 28.5 | 19.4 |
| pulse3 | 42.0 | 33.5 |
| pulse2 | 54.0 | 38.3 |
| ml:main | 61.8 | **81.4** |
| meta | 47.2 | 58.3 |
| ai_panel | 62.2 | 81.4 |

→ DAX'ta ML ve AI Panel'in SELL'i mükemmel, PULSE'ların her iki yönü de kötü. Sorun yön değil, PULSE'ların DAX mikro-yapısıyla uyumsuzluğu.

### 2.3 SL Anatomisi (stopped sinyaller)

| Sembol/Model | Ort. MFE (pip) | Ort. SL (pip) | MFE ≥ SL/2 oranı | Önce TP1 vurup sonra SL olan |
|---|---|---|---|---|
| XAUUSD pulse1 | 2.0 | 14.9 | %4.0 | **1430/2472 (%58)** |
| XAUUSD pulse2 | 1.8 | 14.9 | %5.5 | 981/1766 (%56) |
| XAUUSD pulse3 | 1.9 | 14.9 | %4.3 | 1070/2327 (%46) |
| XAUUSD ml:main | 2.9 | 14.8 | %9.8 | 57/194 (%29) |
| GDAXI pulse1 | 7.2 | 68.4 | %2.7 | 528/1339 (%39) |
| GDAXI pulse3 | 6.7 | 64.9 | %0.6 | 360/1000 (%36) |
| GDAXI ml:main | 5.2 | 53.6 | %2.6 | 25/114 (%22) |

İki kritik çıkarım:
1. **SL'yi genişletmek çözüm değil** — MFE ortalaması SL mesafesinin %10-13'ü. Kaybeden sinyaller girer girmez ters gidiyor (yön/zamanlama hatası), SL darlığından ölmüyor.
2. **Dağılım bimodal** — kaybedenlerin önemli bir alt kümesi önce TP1'i görmüş. Bunlar "yanlış sinyal" değil, "yanlış exit yönetimi". TP1 → breakeven kuralı şart.

---

## 3. XAUUSD — Model Bazlı Gösterge Denetimi

### 3.1 PULSE 1 (5m algo: son 10 mum, EMA 5/10/20, RSI-14, MACD hist, hacim oranı, Stoch-14)

| Değerlendirme | Detay |
|---|---|
| ✅ Doğru | EMA 5/10/20 stack (25p) — 5m trend okuması altında geçerli. Mum sayımı (20p) basit ama işlevsel. AI-Ops XAU guard'ları (SAR+transition, DXY, SAR+downtrend) doğru yönde — ancak yalnızca BUY tarafını koruyorlar. |
| ❌ Zararlı | **RSI >75 → 0 puan cezası:** Altın momentum varlığıdır; ATH trendinde RSI haftalarca 70+ kalır. Bu ceza trend BUY'larını kırpıyor ve skoru dolaylı SELL'e itiyor. SELL WR %19.1 bunun doğrudan sonucu. |
| ⚠️ Gereksiz | **Stochastic K (10p):** 5m'de RSI ile ~%90 korele — aynı mean-reversion bilgisini iki kez sayıyor, aşırı-alım cezasını katmerliyor. Kaldırılıp puanı EMA stack'e verilebilir. **MACD hist (15p) 5m'de** gecikmeli; whipsaw kaynağı, 10p'ye düşürülmeli. |
| ➕ Eklenecek | (1) **H4 trend kapısı:** fiyat H4 EMA50 üzerindeyken SELL → HOLD (EMEL'in ATH bloğunun genellemesi). (2) **DXY simetrik guard:** DXY günlük -%0.2 altındayken SELL blok (mevcut #XAU-PULSE1-002'nin aynası). (3) **Saat filtresi:** 20:00-21:00 UTC ve 01:00-03:00 UTC sinyal üretme veya eşik +10. |

### 3.2 PULSE 2 (15m: ML 40p, EMA 20/50 25p, MACD 15p, RSI 10p, hacim 10p, harmonik bonus)

| Değerlendirme | Detay |
|---|---|
| ✅ Doğru | ML bileşeninin en yüksek ağırlıkta olması doğru (ML XAU BUY %78.7). EMA 20/50 pullback mantığı ("STRONG_TREND_UP'ta derin pullback = fırsat") altın için isabetli tasarım. |
| ❌ Zararlı | ML=HOLD iken **TA fallback modu** (2 TA oyu ile sinyal): SELL kayıplarının önemli kaynağı — ML'in onaylamadığı yönde TA konsensüsü trend ortamında mean-reversion SELL'i demektir. Fallback yalnızca trend YÖNÜNDE çalışmalı. |
| ⚠️ Gereksiz | Hacim (tick volume, 10p) 15m altında bilgi düşük; 5p'ye indirilip RSI regime-aware yorumuna aktarılabilir. |
| ➕ Eklenecek | H4 trend kapısı (3.1 ile aynı) + TP1 breakeven. |

### 3.3 PULSE 3 (MTF: 5m %50, 1H %30, 4H %20)

| Değerlendirme | Detay |
|---|---|
| ✅ Doğru | MTF fikri doğru; 4H OB bonusu (ICT) doğru. |
| ❌ Zararlı | **Ağırlık dağılımı ters:** 5m %50 ağırlık taşıyor; altında 5m gürültüsü karar veriyor, 4H yalnızca %20. SELL WR %19.7 = 5m karşı-trend okumaları 4H trendini eziyor. Trend rejiminde ağırlıklar 4H %40 / 1H %35 / 5m %25 olmalı (rejime göre dinamik). |
| ⚠️ Gereksiz | "1H MACD >0 veya <0 her iki durumda +10p" — yönsüz puan, skor enflasyonu yaratıyor; yön eşleşmesine bağlanmalı. 4H "10-bar %değişim" ham momentum — ATR-normalize edilmeli (agent kataloğunda mutlak % eşikleri: altın volatilitesinde yanıltıcı). |
| ➕ Eklenecek | Veri kalitesi notu: XAUUSD 1h/4h mumları 5m→30m→1h **çift resample** ile türetiliyor; ara swing'ler siliniyor. PULSE 3'ün 1H/4H bileşeni ve SMC'nin 4H OB tespiti sentetik barlar üzerinde çalışıyor. MT5 Bridge'den doğrudan `mt5:bar:1h` stream'i XAUUSD için de beslenmeli. |

### 3.4 EMEL (9-check; XAU ağırlıkları: trend 15, mtf 20, regime 15, momentum 25, volume 10, sr 20, pattern 15)

| Değerlendirme | Detay |
|---|---|
| ✅ Doğru | **Sistemin en iyi kalibre edilmiş modeli (%84.8).** Momentum 25 + SR 20 + volume 10 dağılımı altına uygun. ATH SELL bloğu kanıtlanmış en değerli kural. |
| ⚠️ İzle | emel_inv XAUUSD %18.8 → ana EMEL'in doğruluğunun teyidi; inverse log doğru çalışıyor. |
| ➕ Eklenecek | Yalnızca iki şey: (1) DXY/US10Y makro check'i 10. kontrol olarak (yfinance verisi zaten saatlik geliyor, EMEL'de kullanılmıyor). (2) Ekonomik takvim kontrolü: FOMC/NFP/CPI ±30dk yeni sinyal blok — `economic_calendar_service` mevcut ama EMEL'e bağlı değil. |

### 3.5 ML (XAU v2/v3: 133 feature, ATR-normalize, DXY/US10Y/VIX korelasyon, session, anti-chase)

| Değerlendirme | Detay |
|---|---|
| ✅ Doğru | Feature seti modern ve altına uygun: ATR-normalize getiriler, swing mesafesi (anti-chase), session flag'leri, makro korelasyonlar. BUY %79.7 bunu doğruluyor. |
| ❌ Sorun | SELL %31.8 — model 12 saatlik ufukta eğitilmiş; ATH trendinde SELL head'in isabeti düşük. SELL sinyalleri için ek kapı: `p_sell` eşiğini 0.60→0.65'e çek veya H4 trend up iken SELL çıktısını HOLD'a indir. |
| 🗑️ Kapat | **ml_cross_xau_nasdaq deneyi: SELL %6.9 (12W/162L).** NASDAQ modelini altına uygulama deneyi açıkça başarısız — kapatılmalı, log kirliliği yaratıyor. |

### 3.6 SMC (OB/FVG/CHoCH/BOS)

| Değerlendirme | Detay |
|---|---|
| ✅ Doğru | BUY %80.1 — OB retest + displacement altında iyi çalışıyor. min_score 50 ve displacement 1.2 ATR sıkılaştırması (2026-04 audit) doğruymuş. |
| ❌ Sorun | SELL %31.8 — bearish OB'ler ATH trendinde "mitigation"a uğrayıp geçiliyor. Bearish OB sinyali için ek koşul: yalnızca CHoCH (yapı kırılımı) teyidi VARSA SELL üret; BOS devam ederken bearish OB retest'i sinyal olmamalı. |
| ➕ Not | 4H OB'ler çift-resample sentetik barlarda tespit ediliyor (3.3'teki veri sorunu SMC'yi de vuruyor). |

---

## 4. GDAXI (DAX) — Model Bazlı Gösterge Denetimi

### 4.1 Teşhis: Gösterge sorunundan önce üç yapısal sorun

1. **TP/SL geometrisi:** Sabit TP 20 / SL 12 point. DAX'ta 5m ATR tipik 8-20 point, spread 1-2 point. TP hedefi gürültü bandının içinde, SL tek mumla süpürülüyor. PULSE 1'in hem düz (%25) hem inverse (%38) kaybetmesi bunun kanıtı: geometri bozuksa yön bilgisi olsa da para kaybedilir.
2. **Seans yapısı:** Xetra açılışı (07:00 UTC) sonrası 07-12 UTC tüm modellerde %39.9-42.8 WR. Gap + düşük likidite + fixing dönemleri. 13:00 UTC'de (ABD verisi/NY açılış öncesi) %52.4'e sıçrıyor.
3. **Model routing:** DAX, NASDAQ modeli + NASDAQ'a göre tasarlanmış PULSE mantığıyla işlem görüyor. DAX'a özgü tek şey EMEL ağırlık tablosu. Buna rağmen ML DAX'ta %71.3 çalışıyor (özellikle SELL %84.7) — ML'e dokunma, PULSE katmanını düzelt.

### 4.2 PULSE 1 → DAX için askıya al veya yeniden tasarla

Mevcut 5m mean-reversion seti (mum sayımı, EMA 5/10/20, RSI, MACD, hacim, Stoch) DAX'ta hiçbir yönde bilgi üretmiyor. Seçenekler: (a) GDAXI'de pulse1'i devre dışı bırak (regime mapping'de zaten trend'de OFF; kalıcı OFF), (b) 15m'ye taşı + ATR-bazlı TP/SL + seans filtresi ile yeniden test. Mevcut haliyle 60 günde 446W/1339L üretmiş — sistemin en büyük tekil kayıp kaynağı.

### 4.3 PULSE 2/3

| Değerlendirme | Detay |
|---|---|
| ⚠️ PULSE 2 | %51.6 ile sınırda. ML bileşeni taşıyor (ML DAX iyi), TA bileşenleri frenliyor. SELL %38.3: DAX'ta ML SELL %84.7 iken pulse2 SELL'in kaybetmesi = TA fallback ve düşük-conf ML sinyallerinin karışması. `confirm_floor` DAX için 50→55'e çekilmeli. |
| ❌ PULSE 3 | %39.4. XAUUSD ile aynı sorun: 5m %50 ağırlık. DAX'ta ayrıca 4H "mutlak %değişim" eşikleri (%1, %2) endeks volatilitesine göre yanlış ölçekli. ATR-normalize + ağırlıkları 4H lehine çevir. |
| ➕ Ekle | Her ikisine: **NDX momentum bileşeni.** DAX öğleden sonra ABD endekslerini takip eder; DataHub'da NDX verisi zaten var. "NDX son 1h getiri yönü ile uyum" 10-15 puanlık bileşen olarak eklenirse 13-15 UTC penceresindeki isabet artar. |

### 4.4 EMEL (DAX ağırlıkları: trend 20, mtf 25, regime 15, momentum 20, volume 15, sr 15, pattern 10)

| Değerlendirme | Detay |
|---|---|
| ⚠️ Sorunlu | %50.0 (43W/43L) — yazı tura. MTF=25 fikri doğru ama 1h/4h okumaları sabah seansında gap'lerle bozuluyor. |
| ❌ Gereksiz | **Volume 15p:** DAX CFD hacmi MT5 tick volume — Xetra gerçek hacminden kopuk, bilgi değeri düşük. 15→8'e düşür. **SR pivot (20 bar) 15p:** klasik pivot DAX'ta zayıf; önceki gün H/L + Xetra açılış fiyatı + gap seviyesi daha anlamlı referanslar. |
| ➕ Ekle | Boşalan ~14 puan: (1) **Gap check (yeni):** açılış gap'i >%0.3 ise gap yönü/kapanma durumu skorlansın; ilk 60dk counter-gap sinyal blok. (2) Trend ağırlığı 20→25. (3) Takvim: ECB + Ifo/ZEW/PMI ±30dk blok. |

### 4.5 SMC

%44.1 — DAX'ın gap'li yapısında OB/FVG zone'ları sabah invalidate oluyor. Displacement eşiği (1.2 ATR) DAX için 1.5'e çekilmeli ve 07:00-08:00 UTC oluşan zone'lar (gap gürültüsü) skorlanmamalı.

### 4.6 ML

%71.3 — dokunma. Tek ekleme: EURUSD zaten makro serviste çekiliyor, DAX feature setine `eurusd_ret` + `ndx_corr` eklenmesi v2 iterasyonunda değerlendirilebilir (NASDAQ modeliyle paylaşıldığı için ayrı DAX head'i gerektirir; öncelik düşük).

---

## 5. Özet Matris — Tut / Düzelt / At / Ekle

| Gösterge/Bileşen | XAUUSD | GDAXI |
|---|---|---|
| EMA stack (5/10/20, 20/50/200) | ✅ Tut | ✅ Tut |
| RSI aşırı alım/satım cezası (>75/<25) | ❌ Kaldır — trend'de ters çalışıyor | ⚠️ Regime-aware yap |
| Stochastic (pulse1) | 🗑️ At — RSI ile mükerrer | 🗑️ At |
| MACD 5m | ⚠️ Ağırlık düşür (15→10) | ⚠️ Ağırlık düşür |
| Tick volume bileşenleri | ⚠️ Düşük ağırlıkta tut | ❌ 15→8'e düşür (sentetik veri) |
| SR pivot (20-bar) | ✅ Tut (EMEL sr=20 çalışıyor) | ❌ Önceki gün H/L + gap seviyesiyle değiştir |
| Harmonik pattern (4H) | ✅ Tut | ✅ Düşük ağırlıkta doğru (10p) |
| ADX rejim (1h, eşik 25/18) | ⚠️ H4 teyidi ekle — ATH trendi TRANSITION okunuyor, pulse1 açık kalıyor | ⚠️ Aynı |
| ATH/H4-trend SELL bloğu | ➕ **PULSE 1/2/3 + SMC + meta'ya yay (en yüksek etkili değişiklik)** | — (DAX'ta yön sorunu yok) |
| DXY/US10Y guard | ➕ SELL simetriği ekle | — |
| NDX korelasyon bileşeni | — | ➕ Ekle (pulse2/3, meta overlay) |
| EURUSD makro | — | ➕ ML v2'de değerlendir |
| Açılış gap analizi | — | ➕ Ekle (EMEL yeni check + sabah bloğu) |
| Saat/seans filtresi | ➕ 20-21 UTC + 01-03 UTC blok/eşik artışı | ➕ 07:00-08:00 UTC blok, 13-15 UTC pencere |
| Ekonomik takvim gating | ➕ FOMC/NFP/CPI ±30dk | ➕ ECB/Ifo/ZEW ±30dk |
| TP1 → breakeven kuralı | ➕ **Lifecycle'a ekle (kayıpların ~%50'si TP1 görmüş)** | ➕ Aynı |
| Sabit TP/SL geometrisi | ⚠️ Gözden geçir | ❌ **ATR-bazlı dinamik mesafeye geç (TP≥1.5×ATR15m, SL≥1.0×ATR15m)** |
| XAUUSD 1h/4h çift-resample | ➕ MT5'ten doğrudan 1h stream besle | — |

---

## 6. Öncelikli Aksiyon Listesi (etki sırasıyla)

1. **TP1 → breakeven** (`signal_lifecycle.py`): TP1 hit olduğunda SL'yi entry'e çek. Etki: her iki sembolde stopped'ların %36-58'i nötr/kazanca döner. En düşük risk, en yüksek getiri.
2. **XAUUSD trend-yönü SELL kapısı**: EMEL'deki ATH bloğunu genelle — H4 EMA50 üstü + rejim ∈ {STRONG_TREND_UP, TRANSITION-up} iken pulse1/2/3 + SMC SELL → HOLD. Etki: ~5.200 SL'lik SELL havuzunun büyük bölümü kesilir; PULSE WR'ları ~%65 bandına çıkar.
3. **GDAXI pulse1'i askıya al**, PULSE'lara ATR-bazlı TP/SL getir. Etki: sistemin en büyük tekil kayıp kaynağı (1339 SL/60gün) kapanır.
4. **PULSE 3 ağırlık reformu**: trend rejiminde 4H %40 / 1H %35 / 5m %25; mutlak % eşiklerini ATR-normalize et.
5. **Seans filtreleri**: XAUUSD 20-21 & 01-03 UTC; GDAXI 07:00-08:00 UTC blok. Confidence'a saat çarpanı (veri bölüm 2'de).
6. **pulse1 RSI>75 cezasını kaldır, Stochastic'i çıkar** — puanları EMA stack + H4 uyum bileşenine dağıt.
7. **ml_cross_xau_nasdaq deneyini kapat** (SELL %6.9 — kanıtlanmış başarısız).
8. **XAUUSD 1h/4h veri hattı**: MT5 `mt5:bar:1h` stream'ini XAUUSD için aktive et; çift-resample yerine gerçek bar (PULSE 3 + SMC kalitesini doğrudan etkiler).
9. **Ekonomik takvim gating**: mevcut `economic_calendar_service`'i PULSE/EMEL sinyal üretimine bağla.
10. **EMEL'e makro check**: DXY/US10Y 10. kontrol olarak (veri zaten saatlik geliyor).

---

## 7. Yan Bulgular (odak dışı ama acil)

- **USOIL EMEL %8.5 WR (17W/182L)** — bariz bir şey kırık; EMEL'in USOIL parametreleri veya veri beslemesi acil incelenmeli. Bu oran rastgeleden bile kötü → sistematik ters çalışan bir bileşen var (inverse'ü %91 demek).
- **NDX PULSE inversion deneyi anlamlı**: pulse1_inv NDX %61.1 vs pulse1 %28.8. NDX'te pulse sinyalleri tutarlı biçimde ters — shadow deneyi ana sisteme terfi ettirilebilir. **GDAXI'de ise inversion çalışmıyor** (%38) — DAX shadow listeden çıkarılabilir (bilgi yok, gürültü var).
- **NDX emel_inverse %76.9 vs emel %44.3** — EMEL'in NDX yorumu da sistematik ters; EMEL NDX ağırlıkları ayrıca incelenmeli.
- **ml:aggressive her endekste kötü** (GDAXI %29.4, NDX %27.0): 0.50 eşiği endekslerde gürültü topluyor; bu scope endekslerde kapatılabilir.

---

## 8. Metodoloji Notu

Kod katalogları `ml_prediction_service.py`, `emel_pulse.py` (+ pulse servisleri), `order_block_detector_v2.py`, `market_regime_service.py`, `meta_analysis_engine.py`, `ml_scope_policy.py`, `data_hub.py` üzerinden çıkarıldı. Performans verileri Supabase `prediction_logs` tablosundan, `created_at > now()-60 gün`, `status IN (completed, stopped)` filtresiyle sorgulandı; ≥5 resolved sinyali olan model×sembol kombinasyonları raporlandı. `market_closed_invalid` kayıtları hariçtir. MFE = `highest_profit_pips`; "önce TP1 sonra SL" = stopped kayıtta `targets_hit` dolu olması.
