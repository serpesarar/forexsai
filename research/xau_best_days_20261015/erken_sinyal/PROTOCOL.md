# XAU R0B_G1 sağ kuyruğu — EX-ANTE erken sinyal testi — ÖN KAYIT

**Yazıldı: 2026-10-16 04:20 UTC (00:20 EDT).** Bu dosya yazılırken bu çalışmada HİÇBİR sonuç (R, kazanç, en iyi gün
listesi) hesaplanmadı. Yalnız girdi verisi hazırlandı (`data/macro_yf.csv`: yfinance ^VIX ve DX-Y.NYB günlük kapanış,
2007-06→2026-10-15). Bu dosya sonuçtan sonra DEĞİŞTİRİLMEZ; sapma olursa §10'a tarihli ek yazılır.

## 0. Önceden bilinenler (dürüstlük beyanı)
- Kural (MK-04 = R0B_G1, `decider_xau_tpsl_20261015/mekanik/`): H1 high ≥ önceki 20 H1 barın en yükseği → sonraki H1
  açılışında BUY (+$0,12), SL 1,5×ATR14(H1), TP yok, 20 H1 bar sonra çıkış, tek pozisyon. Dukascopy 2008-01→2026-06-16:
  ham 12.403 olay +0,102R; tek pozisyon n=3.664, WR %35,6, +0,079R, toplam +290,5R, maks. düşüş −59,1R, pozitif hafta
  %46. Yıllık toplamları gördüm (2009 +56, 2025 +60, 2012–15 ve 2018 negatif). En iyi 20 gün toplam R'nin %72'si,
  çıkarılınca +0,029R. P1 rastgele BUY (aynı yıl+UTC saat) ≈ +0,03–0,05R.
- MK-07: R4 (BB sıkışma kırılımı + D1 trend) bağımsız KURAL olarak sınandı → C (en iyi 20 gün hariç −0,030). R1/R5'te
  D1 EMA200 trend filtresinin "sürüklenmeyi seçtiği, tetiğin katkı vermediği" görüldü. R2 (Londra Asya kırılımı) ve
  R3 (NY sabah gücü) zayıf/negatif. Bu çalışma bunları KURAL olarak tekrar etmez; aynı tanımların bir kısmını (sıkışma,
  D1 trend, seans) R0B_G1'in KENDİ olaylarını işaretleyen bayrak olarak kullanır → yeni soru (kuyruk seçimi), aynı veri.
  Bu durum sonuçta açıkça belirtilecek.
- OLD-07/OLD-10: XAU'da makro YÖN tahmini yok (DXY/reel faiz bağları 2024-26'da işaret çevirdi). Bu yüzden DXY bayrağı
  ALINMADI; yalnız VIX (kriz/kaçış mekanizması, yön tahmini değil kuyruk koşulu) alındı.
- Bir başka ajan aynı klasörün `makro/` alt klasöründe çalışıyor; onun `out/` dosyalarına (en iyi gün listeleri) BAKMADIM
  ve bakmayacağım.

## 1. Veri ve dönemler (önceden sabit)
- Ana: `mekanik/data/duka_h1.parquet` (Dukascopy XAU H1 BID; `v` hacim). `mekanik/run_main.load_main()` aynen kullanılır
  (2026-06-17 öncesi; MK-06 ile birebir aynı olaylar). Kod `mekanik/`'i SALT-OKUNUR import eder.
- **Keşif:** sinyal barı 2008-01-01 → 2016-12-31. **Doğrulama:** 2017-01-01 → 2026-06-16.
  (Görev "2017→2026-09" diyor; Duka 06-17 sonrası broker kasasıyla çakıştığı için doğrulama 06-16'da kesilir — MK-06
  ile aynı kesim; kasa bağımsız kalır.)
- **Kasa:** broker (Pepperstone) 1m `decider_xau_tpsl_20261015/data/xau_1m_utc.csv.gz` 2026-06-17 → 10-14;
  `mekanik/holdout.py` yöntemi (Duka geçmişi + broker H1 ek, yol 1m). n küçük → yalnız işaret.
- Tek pozisyon her dönem içinde ayrı hesaplanır (`mech.one_position`).

## 2. Özellikler (10; hepsi sinyal barı `s` KAPANIŞINDA bilinen veriden; D1 = NY 17:00 sınırlı, yalnız kapanmış gün)
Yön ön-kayıtlıdır: bayrak = "iyi" beklenen durum.
| # | Ad | Tanım (bayrak DOĞRU ise) | Mekanizma |
|---|---|---|---|
| F1 | H1_SIKISMA | `s−1` barında BB(20,2) genişliği/orta ≤ önceki 120 barın (s−1 dahil değil… aynı R4 tanımı: `bw.shift(1)` vs `bw.shift(1).rolling(120).quantile(0.2)`) %20'liği | sıkışma→genişleme: enerji birikimi, kırılım trend başlatır |
| F2 | D1_SIKISMA | son kapanmış D1 barı NR4 (son 4 kapanmış günün en dar aralığı) VEYA inside day (h ≤ önceki h ve l ≥ önceki l) | Crabel NR4/inside: günlük sıkışma sonrası genişleme günü |
| F3 | KAPANIS_TEYIDI | `s` kapanışı > önceki 20 H1 high VE kapanış konumu (c−l)/(h−l) ≥ 0,6 | fitil kırılımı ≠ kabul; kapanışla kabul gerçek talep (sahte kırılım ayıklama) |
| F4 | HACIM | `s` hacmi / aynı UTC saatinin önceki 20 işlem günündeki medyan hacmi ≥ 1,5 (en az 10 gün; yoksa YANLIŞ) | katılım: hacimli kırılım kurumsal akış |
| F5 | D1_TREND | son kapanmış D1 kapanışı > D1 EMA200 (`trend_up`) | altında "güçlüyü al"; trend devamı |
| F6 | D1_DONCHIAN20 | `s` high ≥ son 20 kapanmış D1 barının en yüksek high'ı | çok-zaman-dilimi kırılımı: günlük ölçek de yeni tepe |
| F7 | ZIRVE_250 | `s` high ≥ son 250 kapanmış D1 barının en yüksek high'ı (≈52 hafta) | 52-hafta tepesi çapası (George–Hwang): tepe kırılımı sürer |
| F8 | SEANS | `s` UTC saati 07–15 (bar başlangıcı; giriş 08–16 UTC) | Londra+NY likit seans kırılımı gerçek akış; Asya kırılımı ince |
| F9 | MOMENTUM6 | (c[s] − c[s−6]) / ATR[s] ≥ keşif dönemi OLAYLARININ bu değişkeninin %66,7'liği (yalnız özellik dağılımından; sonuç kullanılmaz) | kırılıma ivmeyle gelmek; "coşku dönmez" |
| F10 | VIX20 | sinyal anının NY takvim gününden ÖNCEKİ son VIX kapanışı ≥ 20 | stres/kaçış rejiminde altın kuyruğu |
Hepsi aynı segmentte (hafta sonu boşluğu yok) hesaplanır; hesaplanamayan (NaN) değer bayrak = YANLIŞ.

## 3. Kullanımlar (2 × 10 = 20 test)
- **FİLTRE:** yalnız bayraklı ham olaylar → tek pozisyon yeniden yürütülür (boşalan kapasiteye başka bayraklı olay girer, E19).
  İstatistik d = ortR(filtreli tek-poz) − ortR(taban tek-poz).
- **BOYUT2:** taban tek-poz işlemleri aynen; bayraklıya 2× risk. İstatistik d = ortR(bayraklı) − ortR(bayraksız)
  (taban tek-poz kümesi içinde). Risk-başı getiri = Σ w·R / Σ w.

## 4. Çıkarım
- **Boş dağılım (rastgele alt küme, E24):** sonuç ikilisi (R, süre) olay sırasında **yıl içinde dairesel kaydırılır**
  (her yıl için rastgele ofset; özellikler sabit) → aynı yıl karışımı, korunmuş kümelenme, kuralın kendi olayları.
  1.000 tekrar; aynı kaydırma 20 testin hepsine uygulanır (ortak boş). Ham p = P(boş ≥ gerçek).
  **max-T:** z_j = (d_j − ort_boş_j)/sd_boş_j; düzeltilmiş p_j = P(max_k z_boş_k ≥ z_j). Ayrıca **Holm** (m=20).
- **Gün-blok bootstrap** (`mech.day_boot_p`, 4.000): strateji ortR'si için P(EV>0) ve %95 GA.
- **Sürüklenme kontrolü (M2, E29/E30):** her ham olay için W_i = aynı ISO haftasındaki TÜM geçerli H1 barlarında aynı
  geometriyle BUY'ın ortalama R'si (haftalık sürüklenme; aynı dönemden kontrol). Fazla_i = R_i − W_i.
  DiD = ort(Fazla | F) − ort(Fazla | ¬F); gün-blok bootstrap P(DiD>0). İkincil (bilgi): P1-F = aynı yıl + UTC saati +
  aynı bayrak durumu rastgele bar (20 çekim) — F3/F6/F7 bayrağı kırılımı içerdiğinden bu kontrol onlar için kendine-
  benzer (totolojik) olur; not edilecek.
- **Kuyruk:** P(R≥3) içeride/dışarıda; bayraklı işlemlerin toplam R payı vs işlem payı; dönem içi en iyi 20/50 gün
  (taban tek-poz, giriş UTC günü, günlük ΣR) içindeki işlemlerin bayrak oranı / tüm işlemlerin bayrak oranı (lift).
- **Strateji ölçüleri:** n, işlem/hafta, R/hafta, haftalık Sharpe (tüm takvim haftaları, sıfırlar dahil, ort/sd),
  pozitif hafta oranı (işlemli haftalar), maks. düşüş (R), en iyi 20 gün hariç risk-başı ortR.

## 5. Geçme ölçütleri (DOĞRULAMA döneminde; her özellik × kullanım)
- c1: d > 0 ve max-T düzeltilmiş p ≤ 0,10
- c2: keşif döneminde d > 0
- c3: strateji gün-blok P(EV>0) ≥ 0,90 VE en iyi 20 gün hariç risk-başı ortR > tabanın aynı ölçüsü
- c4: haftalık Sharpe ≥ taban; FİLTRE için ayrıca ≥ 1,0 işlem/hafta
- c5: M2 DiD > 0 doğrulamada P ≥ 0,90 ve keşifte DiD > 0
- c6: kasada d > 0 (işaret)
**Verdikt:** A = c1–c6 · B = c1–c4 geçer, c5 veya c6 düşer (c5 düşerse "B-sürüklenme": rejim seçici, kurala özgü değil)
· C = c1–c4'ten biri düşer ama d > 0 ve ham p ≤ 0,10 · RED = diğer her durum (d ≤ 0 veya ham p > 0,10).

## 6. Sızıntı denetimi (sonuçtan önce koşulur)
Önek testi: veri rastgele 3 noktada kesilip özellikler yeniden hesaplanır; kesimden önceki barların 10 özelliği tam
veriyle birebir aynı olmalı. D1/H4 eşlemesi `mech.prep_h1` mantığıyla (gün kapanışı ≤ karar anı). Biri tutmazsa dur, düzelt, §10'a yaz.

## 7. Raporlanacak
Her özellik: bayrak oranı (keşif/doğrulama), 20 test tablosu (d, ham p, Holm, max-T, bootstrap, M2), kuyruk tablosu,
strateji ölçüleri, kasa, verdikt, gerçek zamanlı entegrasyon tarifi (bot/decider bayrağı nasıl hesaplar).

## 8. Kapsam dışı
Eşik taraması (her özelliğin tek ön-kayıtlı eşiği var), özellik kombinasyonları (yalnız sonradan, POST-HOC etiketiyle),
DXY, haber, SELL, geometri değişikliği, Pazartesi boşluğu, kırılım öncesi aralık uzunluğu.

## 9. Çıktılar
`research/xau_best_days_20261015/erken_sinyal/` (kod + `results/`); not:
`research_notes/XAU kırılım kuralının en iyi günleri/erken_sinyal_testi.md`.

## 10. Sapmalar (tarihli)
- 2026-10-16 ~04:40 UTC (sonuçlar GÖRÜLDÜKTEN SONRA): §4 M2'nin "aynı ISO haftası tüm-bar BUY" kontrolü **E15 tuzağının
  hafta ölçeği** çıktı: kırılım olan haftalar, kırılım hareketini içeren haftalardır; haftanın kırılım ÖNCESİ barlarının
  20-bar ileri getirisi o hareketi içerir → W kırılım olayları için yukarı yanlı (doğrulamada kural +0,111 vs W +0,279).
  c5 bu yüzden GEÇERSİZ sayılır. Nedensel yedek (`05_did_causal.py`): P1-F (aynı yıl + UTC saati + aynı bayrak durumu,
  40 çekim) ile DiD + gün-blok bootstrap. c1'de tüm 20 test zaten düştüğü için hiçbir verdikt değişmez.
- `04_posthoc.py`, `05_did_causal.py` sonradan eklendi; `04` POST-HOC KEŞİF (verdikte girmez).
