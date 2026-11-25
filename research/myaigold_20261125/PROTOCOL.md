# My AI Gold (MQL5 Market EA, canlı sinyal 2389616) — davranıştan strateji çözümü (MG) — 2026-11-25
Kullanıcı sinyalin işlem geçmişini (history CSV, 128 işlem, 2026-05-19 → 11-23) elle indirdi; .ex5'e dokunulmadı (decompile yok).
Veri: XAU 1m Duka (≤ 11-13) + broker 1m (Supabase indicator_snapshots, 11-10 → 11-25; Duka'yla taban farkı 0,2 $); spread Duka yıl×saat.
Saat ekseni ny7 (IC Markets): giriş fiyatlarının %95,3'ü o dakikanın açılışına ±1 $.
**MG-1 profil (betimleyici, sonuç görüldü):** 64 AL / 64 SAT, net +5.637 $ (300 $ yatırım), isabet %78,9 (başabaş %68,2); girişler HH:00:01–05
(H1 kapanışı kararı); çıkış sabit $: TP +25 $ (≈ 1,37 ATR_H1), ilk SL −40 $, kâra geçince stop +16 $'a kilit (kazanan medyan çıkış +16,0 $);
lot bakiyeyle (ρ 0,96). Giriş imzası: yön = son 12–24 sa trendi (r12 × yön > 0 %88), fiyat EMA50'nin yöne göre +1,7 ATR ötesinde, son 4 sa
düz/geri çekilme (medyan −0,05 ATR), 20-bar kırılımı yalnız %2, 24 sa aralıkta yöne göre konum 0,78, RSI(yöne göre) 60; saat 08/20/12 UTC 2–2,7×.
## MG-2/3 — ÖN KAYIT (kopya ve bağımsız dönem sonuçları görülmeden)
**MG-2 kopya:** +1 dk giriş (gerçek spread), sağlayıcının çıkış anında çıkış; plasebo aynı ISO hafta × UTC saati × yön rastgele saat başı (×5).
**MG-3 kural:** karar = her saat başı (bilinen: kapanmış H1'ler). Yön d = işaret(r12_atr). Giriş: d·r12 ≥ a ∧ |r4| ≤ b·ATR ∧ d·(fiyat−EMA50)/ATR ≥ c
∧ yöne göre konum24 ∈ [0,55; 0,95]. (a, b, c) hesap döneminde girişleri en iyi ayıran ızgaradan seçilir (a {1; 1,5; 2}, b {0,5; 1}, c {0,5; 1})
— F1 (giriş eşleşmesi ±1 sa) en yüksek. Çıkış: hesabın $ geometrisi hesap dönemi medyan fiyatına (≈ 4.000) göre bp'ye çevrilir:
TP 62 bp, ilk SL 100 bp, kilit = MFE ≥ L bp olunca stop +40 bp (L hesap verisinden ölçülür), 4.000 dk emniyet. Tek pozisyon.
**Bağımsız dönem 2018-01 → 2026-05-18 (hesaptan önce), tek atış.** Geçme: n ≥ 150, ort R > 0, P(EV>0) ≥ 0,95, iki yarı > 0, spread ×1,5 > 0,
aynı yıl × saat × yön rastgele girişe fark > 0 ∧ P ≥ 0,95, 2022–2025 her yıl R > 0, en iyi 10 gün hariç > 0.
Not: 128 işlem küçük örneklem; MG-1 bulguları betimleyici.

### MG-2/3 sonucu (değiştirilmez) — `results/mg23.json`, `results/islemler_ozellik.parquet`
Kilit: kilitli kazananların MFE'si ≥ 16,1 $ (p5), tam kayıpların MFE'si ≤ 15,3 $ → stop ≈ +16 $'a fiyat +16 $'ı görünce çekiliyor (fiilen
"+16 $'da kâr al, +25 $'a şans tanı"); TP +25 $ yalnız 5 işlemde. Sabit 1 ons: +5,69 $/işlem, toplam +728 $, maks. düşüş 90 $, en uzun kayıp serisi 3.
**MG-2 kopya:** sağlayıcı +13,3 bp, +1 dk kopya +10,3 bp (P 0,987) ama aynı hafta × saat × yön rastgele +20,3 bp → zamanlama −9,9 bp (P 0,17).
**MG-3:** seçilen kural (r12 ≥ 2 ATR yönde, |r4| ≤ 0,5 ATR, EMA50'den ≥ 1 ATR, konum24 0,55–0,95) hesap girişlerinin yalnız %32'sini yakalıyor
(kesinlik %20, F1 0,25). **Bağımsız 2018-01 → 2026-05-18: n 1.492, +0,010 R, isabet %68,4, P 0,73, spread ×1,5 −0,003, en iyi 10 gün hariç ≈ 0,
plaseboya +0,052 R (P 0,998); yıllar 2018 −0,09 / 2019 −0,005 / 2020 +0,06 / 2021 +0,02 / 2022 +0,0002 / 2023 +0,04 / 2024 +0,004 / 2025 +0,02;
AL +0,063 / SAT −0,056 → X.** Hesap döneminde aynı kural −0,009 R (hesabın seçimini yakalamıyor).
**Hüküm: X** — canlı kâr = (1) lot bileşiklemesi (300 → 5.937 $), (2) "+16 $ kâr / −40 $ stop" yüksek isabet geometrisi, (3) 2026 Mayıs–Kasım
altın oynaklığında 12–24 sa trend yönü. Davranıştan çıkarılan giriş deseni bağımsız dönemde maliyet sonrası ≈ 0. İz: yalnız AL tarafı +0,06 R
(altın boğası sürüklenmesi olabilir, E13 — ön kayıtsız, kanıt değil).

## MG-4 — kuralı geliştir: daha çok para, daha iyi yön, daha çok işlem (ÖN KAYIT, 2026-11-25, hiçbir MG-4 hücresi koşulmadan)
Kullanıcı: "bu kuralı öğren ve geliştir; daha fazla para, daha iyi giriş yönü, daha çok işlem". Taban = MG-3 kuralı.
**Dönemler:** KEŞİF 2018-01 → 2021-12 (geliştirme yalnız burada); TEST 2022-01 → 2026-05-18 (aday başına TEK atış); KÖR kontrol 2026-05-18 →
2026-11-25 (robotun canlı dönemi; betimleyici). ⚠️ TEST döneminde TABAN kuralın yıllık sonuçları MG-3'te görüldü; varyantlarınki görülmedi.
**Defter:** E13/E73 (altın boğası → AL sürüklenmesi; plasebo aynı yıl × UTC saati × yön), MK-08 (en iyi günlere bağımlılık → en iyi 10 gün hariç
ölçütü), MK-03 (altında aşağı kırılım SAT da artı olabilir), R0B canlı (H1 20-bar tepe AL — korelasyon raporlanır).
**Aşama 1 — giriş/yön (çıkış = robotun bp geometrisi: TP 59,2 / SL 94,7 / kilit 38,2 → +37,9 bp, 4.000 dk):**
yön modu {T12 (taban: işaret r12), T12∧T24 (ikisi aynı), YALNIZ AL, D200 (T12 ∧ fiyat H1 EMA200'ün aynı tarafında)} × a (d·r12 ≥) {1,0; 1,5; 2,0}
× b (|r4| ≤) {0,5; 1,0} × uzama tavanı (d·(fiyat−EMA50)/ATR) {[1, ∞); [1, 2]} × konum24 üst sınırı {0,95; 0,80} × saat {tümü; robotun
yoğun saatleri 07, 08, 12, 15, 20, 22 UTC} = 192 hücre.
**Aşama 2 — çıkış (Aşama 1'in en iyi 3 girişi üstüne, ATR_H1 cinsinden):** TP {1,0; 1,5; 2,0} × SL {1,5; 2,2; 3,0} × kilit {yok; MFE ≥ 0,6·TP → stop
+0,5·TP} = 18 × 3 = 54 hücre.
**KEŞİF geçme:** n ≥ 150, ort R > 0, P(EV>0) ≥ 0,95, iki yarı > 0, spread ×1,5 > 0, plaseboya fark > 0 ∧ P ≥ 0,95, en iyi 10 gün hariç > 0.
Sıralama: **aylık R (ort R × aylık işlem)** — "daha çok para + daha çok işlem"; eşitlikte günlük Sharpe. Aşama 1'den Aşama 2'ye en çok 3 giriş;
TEST'e en çok 3 aday (Aşama 1 ∪ 2 geçenlerden aylık R sırasıyla).
**TEST geçme:** KEŞİF ölçütleri + 2022, 2023, 2024, 2025 her yıl R > 0 + kart 5. ölçüt (iyimser − gerçek ≤ ort/2). Geçen → kart (2. KURAL);
canlı kararı kullanıcıda. Hiçbiri geçmezse X.

### MG-4 sonucu (değiştirilmez) — `results/mg4_asama1.*`, `mg4_asama2.*`, `mg4_test.json`
Aşama 1: 192 hücreden 1'i geçti — **YALNIZ AL, a 1,0, b 0,5, uzama sınırsız, konum ≤ 0,95, yoğun saatler** (KEŞİF n 231, +0,081 R, P 0,985,
plaseboya +0,089 P 0,987); taban KEŞİF −0,005 R. Daha çok işlem açan hücreler anlamlılığı geçmedi; SAT tarafı zayıf (T12T24 SAT +0,02).
Aşama 2: 18 ATR çıkışından 1'i geçti (TP 2 / SL 3 ATR + kilit, aylık 0,364 < robot bp geometrisi 0,391).
**TEST 2022-01 → 2026-05-18 (tek atış): aday 1 → B** — n 308 (ayda 5,9), +0,096 R, isabet %76, P 0,999, yarılar +0,061 / +0,131, spread ×1,5
+0,081, plaseboya +0,062 R (P 0,951), en iyi 10 gün hariç +0,067, yıllar 2022 +0,036 / 2023 +0,089 / 2024 +0,047 / 2025 +0,196 / 2026 +0,076,
iyimser 0,120 (icra ✓). Aday 2 (ATR çıkış) → X (P 0,89, 2022 eksi).
**KÖR 2026-05-18 → 11-25 (robotun canlı dönemi, altın düşüşü): aday 1 n 26, −0,060 R** (betimleyici; küçük n).
Kart `backend/data/evolution/go_live_cards/xau_trend_duraklama_al.json` 6/6 — canlı kararı kullanıcıda. Uyarılar: AL sürüklenmesi (plasebo farkı
sınırda), düşen altında zayıf, ayda ~6 işlem (robottan az), R0B/E4X3 ile korelasyon.

## MG-5 — "canlıya alınabilir yapana kadar" farklı açılardan geliştirme (ÖN KAYIT, 2026-11-25, hiçbir MG-5 hücresi koşulmadan)
Gövde G0 = MG-4 adayı (YALNIZ AL, r12 ≥ 1 ATR, |r4| ≤ 0,5, EMA50 ≥ 1 ATR, konum ≤ 0,95, saat {07,08,12,15,20,22}, robot bp geometrisi).
Zayıflıklar: ayda ~6 işlem; plaseboya fark P 0,951 (sınırda); düşen altında zayıf (kör −0,06 R).
**Açılar (KEŞİF 2018–21'de, G0'ın üstüne tek değişiklik; her biri iki tarafıyla raporlanır):**
- A daha çok işlem: A1 saat seti = KEŞİF'te G0 girişi tüm saatlerde koşulup UTC saat başına ort R > 0 olan saatler (yalnız KEŞİF'ten) ;
  A2 tüm saatler; A3 kilitli/TP çıkışından sonra aynı koşulla yeniden giriş serbest (tek pozisyon korunur — zaten serbest; ölçüm: ayda işlem);
  A4 **dondurulmuş taşıma** NDX ve DAX (Duka 1m; geometri XAU KEŞİF medyan ATR_H1/fiyat oranıyla ATR katına çevrilir; saat {G0 saatleri; tümü}).
- B düşen piyasa: B1 D1 rejim süzgeci (önceki UTC günü D1 kapanışı > D1 EMA50); B2 B1 + ayna SAT (D1 kapanış < D1 EMA50 ∧ yön −1 koşulları).
- C giriş kalitesi: C1 ATR_H1 / önceki 480 H1 medyanı ∈ [0,8; 1,5]; C2 geri çekilme d·r4 ∈ [−0,5; 0] ; C3 d·r4 ∈ [0; 0,5].
- D çıkış (bp): D1 TP 80; D2 TP 120 (kilit aynı); D3 kilit tetiği 50 bp → stop +40; D4 SL 70.
**KEŞİF geçme:** MG-4 ölçütleri + G0'a göre aylık R ↑ (ya da Sharpe ↑ iken aylık R ≥ %90). En çok 3 aday + BİRLEŞİK (geçen açıların hepsi birlikte).
**TEST 2022-01 → 2026-05-18 (bu dönem G0 için bir kez kullanıldı → çoklu sınama düzeltmesi):** MG-4 TEST ölçütleri, plasebo farkı ve P(EV>0)
eşiği **0,99** (Bonferroni, ≤ 5 atış), G0'dan aylık R ↑ ∧ Sharpe ≥ 0,9×. KÖR 2026-05 → 11 betimleyici. A4 taşıma: KEŞİF + TEST birlikte raporlanır
(dondurulmuş, ayar yok) — 2022–25 her yıl > 0 ve plasebo P ≥ 0,95 ise portföye ek aday.
**Kesin doğrulama önerisi (kullanıcı kararı):** altın 2010–2017 KASA'sı (2013–15 ayı piyasası) hiç açılmadı → seçilen son aday için tek atış.

### MG-5 sonucu (değiştirilmez) — `results/mg5_kesif.*`, `mg5_tasima.json`, `mg5_test.json`
KEŞİF (G0: n 231, aylık 0,391 R, plasebo P 0,987): A1 KEŞİF-artı saatler ayda 8,2 / aylık 0,455 ama plasebo P 0,86 ✗; A2 tüm saatler 0,370, P 0,74 ✗;
B1 D1 rejimi 0,162 ✗; B2 ayna SAT 0,052 (SAT −0,050 R) ✗; C1 oynaklık 0,269 ✗; C2 geri çekilme 0,186 ✗; C3 ileri kayma 0,269 ✗; D1 TP 80 → 0,399 ✓
(tek geçen, marjinal); D2 TP 120 0,443 ama plasebo P 0,91 ✗; D3 kilit 50→40 0,290 ✗; D4 SL 70 0,325 ✗. BİRLEŞİK = D1.
**A4 taşıma (dondurulmuş, ATR geometrisi TP 2,77 / SL 4,43 / kilit 1,79 → 1,77 ATR):** NDX KEŞİF −0,018 / TEST +0,007 R; tüm saatler −0,013 / −0,009;
DAX −0,008 / +0,019; tüm saatler +0,013 / +0,040 (P 0,95, plasebo P 0,83, 2022 −0,078) → taşınmıyor, kural altına özgü.
**TEST D1 TP 80 (sıkı eşik 0,99): X** — +0,104 R, aylık 0,608 (G0 0,563), Sharpe 1,42, 2022–26 her yıl +, P(EV) 0,9997 ama plasebo farkı +0,065
P 0,957 < 0,99. KÖR −0,043. **Sonuç: G0 yerel en iyi; dört açıdan hiçbiri onu anlamlı biçimde iyileştirmedi.** Kalan tek açık soru düşen altın
(kör dönem −0,06 R): kesin cevap 2010–17 KASA'sında (2013–15 ayı) — kullanıcı kararı.
