# Kırılım / zaman-serisi momentumu (TSMOM) NDX — ÖN KAYIT (2026-10-13, sonuçlara bakılmadan yazıldı)

## 0. Köken ve defter kontrolü (3. KURAL)
- Köken: MK-02 mekanizma testi (`pinbar_20261010/deep.py` T5): "yeni 20-mum tepesi → BUY, 20 mum tut", her 3. mumda
  rastgele BUY tabanına göre NDX 5m −0,020 · 15m +0,056 · **30m +0,167** · 1h(10y) +0,018 · DAX 15m +0,017 · 30m +0,026 ·
  1h +0,053 (7 setin 6'sı +). MK-03: XAU/USOIL'de genel olarak geçmedi; MK-04: XAU 1h stoplu kart icra ölçütünde ✗.
- **Görülmüşlük (E23) beyanı:** T5'in NDX 30m seti `bars_30m` 2023-10→**2026-10-02**'yi (yani bu protokolün kasasını
  da) ve DAX 15m/30m/1h **≥2019**'u kapsıyordu. Dolayısıyla tek hücre (F1, N=20, H=20, stopsuz) için kasa ve DAX
  **toplu olarak görülmüştür**. Bu çalışmada GERÇEKTEN yeni olanlar: (a) tüm ızgara (N, H, aile, TF, stop), (b) SELL aynası
  NDX'te, (c) yıl×saat eşli sürüklenme tabanı, (d) 2022 ayı piyasası (NDX 30m 2021-06→2023-09 T5'te yoktu), (e) 4h ve
  günlük TF, (f) koruyucu stop, (g) **DAX günlük 2008-2018** (T5'te yok — tek gerçek bağımsız örneklem), (h) kart.
- Defterle ilişki: OLD-20 (momentum filtresi gerçek ama yalnız uzak hedefle ödüyor → burada braket değil ZAMAN çıkışı,
  meta-ders 5 "braket ≠ zaman"); GF-12 (coşku aynası 1/5 — "korku döner coşku dönmez" → SELL aynası bu ilkeye göre
  BUY'dan zayıf olmalı; ama "yeni dip SELL" bir *momentum* kuralıdır, "aşırı düşmüşte SELL yok" ile karışmasın);
  MK-02/03/04; E13/E15 (taban), E7 (icra), E16 (çok-TF örnekleme sızıntısı: 4h/günlük mumlar yalnız TAMAMLANINCA karar).

## 1. Veri
| Set | Kaynak | Dönem |
|---|---|---|
| NDX 30m | `ndx_gate_forge` `load_long('30m')` (<2026-07-01) + `ndx_pattern_motifs/data/bars_30m.parquet` (≥2026-07-01); çakışan dönemde iki kaynak birebir aynı (kontrol edildi, fark 0) | 2021-06-29 → 2026-10-02 |
| NDX 1h | `load_long('1h')` (<2026-07-01) + bars_30m'den 1h'e (≥2026-07-01; 2026'da iki kaynak birebir aynı) | 2016-05-29 → 2026-10-02 |
| NDX 4h | 1h'ten; kova = NY saatine +7 sa kaydırılmış zamanın 4 saatlik tabanı (17:00 NY = gün başı) | aynı |
| NDX D | 1h'ten; gün = NY 17:00 sınırı (vadeli işlem günü) | aynı |
| DAX 30m / 1h / 4h | `ndx_gate_forge/data/dax_30m.parquet`, `dax_1h.parquet` (yoğun 1h yalnız ≥2019) | 30m 2021-03+, 1h/4h 2019+ |
| DAX D | `dax_1h.parquet` tümü, Berlin tarihine göre günlük OHLC | **2008 → 2026-10-02** |
Segment: ardışık mumlar arasında >4 gün boşluk → yeni segment; işlem segment sınırını aşamaz.

## 2. Kurallar (her biri yalnız i. mum ve öncesini kullanır; karar i. mum KAPANINCA)
Pencere N ∈ {10, 20, 40, 60} mum; tutma H ∈ {10, 20, 40} mum.
- **F1 yeni tepe:** high[i] ≥ max(high[i−N..i−1]) → BUY. Ayna F1s: low[i] ≤ min(low[i−N..i−1]) → SELL.
- **F2 kapanış kırılımı (Donchian kapanış):** close[i] > max(high[i−N..i−1]) → BUY. Ayna: close[i] < min(low[i−N..i−1]) → SELL.
- **F3 F2 + trend süzgeci:** F2 ve close[i] > EMA200(close, aynı TF) → BUY. Ayna: F2s ve close < EMA200 → SELL.
- **F4 TSMOM işareti:** close[i] > close[i−N] → BUY. Ayna: close[i] < close[i−N] → SELL.
Her olay ayrı işlem sayılır (çakışan sinyaller dahil, "tüm sinyaller"); ayrıca **tek pozisyon** sürümü (düzken gelen ilk sinyal).

## 3. İcra ve R birimi
- Giriş = **i+1 mumunun açılışı** + 1,5 puan spread (BUY ask; SELL'de açılış − 1,5 değil: spread bir kez maliyet olarak düşülür).
- Çıkış = i+H. mumun kapanışı (zaman çıkışı) veya stop.
- **Stop:** yok / 1,5×ATR / 2×ATR; giriş fiyatından. Mum low ≤ stop (SELL: high ≥ stop) ise stop; giriş mumundan sonraki
  mumda boşlukla açılırsa dolum = min(açılış, stop) (SELL: max). Aynı mum içi sıra bilinmez → stop önce varsayılır (muhafazakâr).
- ATR = önceki 14 mumun gerçek aralık ortalaması (i dahil DEĞİL).
- **Izgara birimi:** ATR. **Kart birimi:** stoplu sürümde R = stop mesafesi (k×ATR), stopsuzda ATR.
- Net R = yön × (çıkış − giriş)/ATR − 1,5/ATR.

## 4. Taban (kapısız) ve sürüklenme düzeltmesi
- Her geçerli mum için aynı TF/H/stop/yönle "rastgele işlem" sonucu R_all[i] hesaplanır.
- **Birincil taban:** olayın **(takvim yılı × sinyal mumunun UTC saati)** hücresindeki R_all ortalaması (4h: kova saati;
  günlük: yalnız yıl). Fazla getiri = R − taban. Bu, NDX'in yukarı sürüklenmesini (beta) yıl yıl ve saat saat çıkarır (E13, E15).
- İkincil (yalnız rapor): eşlemesiz tüm-mum ortalaması; ve **yıl-ay** eşli taban (ay içi sürüklenmeyi de çıkarır; ayın kendi
  yolunu içerdiği için ticari taban değil, yalnız "beta mı?" ayrıştırması).

## 5. Bölümleme
- **Keşif:** sinyal < 2026-07-01 **ve** çıkış mumu < 2026-07-01 (NDX). Tüm seçim burada.
- **Kasa (bir kez):** NDX sinyal 2026-07-01 → 2026-10-02 (özellikler önceki tarihten süreklidir). Kasa yalnız aşağıdaki
  önceden belirlenmiş varyantlar ve ızgara oranı için okunur; sonra hiçbir şey değiştirilmez.
- **DAX bağımsız piyasa:** aynı kurallar, YENİDEN AYAR YOK. Birincil DAX kanıtı = DAX günlük 2008–2018 (T5'te görülmedi)
  + DAX 30m/1h/4h (≥2019, F1-20-20 hücresi görülmüş).
- **2022 ayı:** NDX 1h ve 30m'de 2022 takvim yılı ayrıca (BUY ve SELL).

## 6. Izgara kararı (en iyi hücre DEĞİL)
Hücre = aile(4) × N(4) × H(3) × TF(4) × stop(3) × yön(2) = 1.152. Hücre başına keşifte: n, ortR, fazla getiri, iki yarı.
- **G1 (BUY yaygınlığı):** stop başına BUY hücrelerinin fazla getirisi > 0 oranı. Geçer: ≥ %75 **ve** plasebo %95'inin üstünde.
  Plasebo: olay maskesini dairesel kaydırma (50 tekrar; kümelenme korunur), aynı ızgara oranı.
- **G2 (düzgünlük):** her TF × aile'de 12 N×H hücresinin ≥ 9'u pozitif ise "düzgün"; TF başına raporlanır.
- **G3 (SELL aynası):** aynı oran SELL için. Hipotez (ön kayıt): SELL oranı BUY'dan belirgin düşük; ≤ %50 beklenir.
- **G4 (beta):** yıl×saat eşli fazla getiri ile eşlemesiz fazla getiri; yıl-ay eşli fazla getiri ayrıca. Kenar yıl-ay
  eşlemesinde de > 0 kalmıyorsa "büyük ölçüde rejim/beta".
- **G5 (stop):** aynı oranlar 1,5 ve 2 ATR stopla; stop kenarı öldürüyorsa (oran < %50) "kenar kuyrukta / sabır gerektiriyor".

## 7. Kart varyantları (önceden belirlenmiş)
- **H-A (ipucu hücresi, a priori):** F1, N=20, H=20, 30m, BUY; stop 2×ATR (birincil) ve stopsuz (rapor).
- **H-S (keşifte seçilen):** BUY yönünde, stop ∈ {1,5; 2}, F1/F2/F3 aileleri arasından **komşuluk-yumuşatılmış** fazla
  getirisi (hücre + aynı TF/aile/stop'ta N ve H'de ±1 adım komşularının ortalaması) en yüksek hücre; koşullar: keşifte tek
  pozisyon işlem sayısı ≥ 150 ve fazla getirinin iki kronolojik yarısı da > 0. Seçim YALNIZ NDX keşif verisiyle.
- Kontrol kartı: aynı TF/H/stop'la **rastgele BUY** (her mum) — NDX sürüklenmesi tek başına kartı geçiriyor mu?

### Kart ölçütleri (CLAUDE.md 2. KURAL) — NDX tüm dönem (keşif + kasa), tek-pozisyon işlem listesi
1. ≥ 150 işlem · 2. ortR > 0 ve gün-bloklu bootstrap P(EV>0) ≥ %90 · 3. iki kronolojik yarı ≥ 0 · 4. spread ×1,5'te > 0 ·
5. iyimser giriş (sinyal mumu kapanışı, spread'siz) ile gerçek giriş farkı < ortR/2 · 6. tek pozisyonla > 0 (liste zaten
tek-pozisyon; ayrıca tüm-sinyal sürümü raporlanır).
Ek (karar için zorunlu): **(7)** aynı stop/çıkışlı rastgele BUY'a göre fazla getiri > 0 ve gün-bloklu P ≥ %90; **(8)** kasada
fazla getiri > 0; **(9)** DAX'ta (aynı hücre, ayar yok) fazla getiri > 0. Ayrıca yıl yıl, en iyi 5/10 gün çıkınca toplam.
**Verdikt:** 1–9 hepsi → LIVE adayı (yine de önce gölge, E23); 1–6 geçer ama 7–9'dan biri düşer → SHADOW/RED ("kart
sürüklenmeyi ölçüyor"); 1–6 düşer → RED.

## 8. Yapılmayacaklar
Sonuçtan sonra N/H/eşik/aile eklemek; DAX'ta ayar; kasayı ikinci kez okumak; canlı bot/backend/DB'ye dokunmak.
