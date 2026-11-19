# NA-01…04 — NASDAQ'ta zorunlu / mekanik akış ve dış bilgi: oynaklık hedefli fonlar, varyans primi, Hazine ihaleleri, BTC hafta sonu öncülüğü

Ön kayıt: 2026-11-18, sonuçlara bakılmadan yazıldı. Yalnız NASDAQ (^NDX / Dukascopy NDX 1m / MT5 NAS100).

## Gerekçe (defter kontrolü)
Defterde yok: varyans primi (VXN − gerçekleşen), oynaklık hedefli fonların kaldıraç azaltma/artırma akışı, Hazine
ihaleleri, BTC hafta sonu → NDX Pazar açılışı. Yakın sınamalar: DB-03 (VXN − VIX, C3b içinde), NK-01 (ΔlnVXN artığı,
düşüş günü sonrası), korku ailesi (§2.71…2.82, fiyat düşüşüne dayalı), BTC-X04 (QQQ → BTC, ters yön).
Kullanıcı tezi (§2.84): son 5 yılda algoritmik / mekanik akış piyasayı değiştirdi. Burada mekanik akışın
**zorunlu ve önceden hesaplanabilir** olanları sınanır. §3-41'e göre beklenti: hesaplanabilen akış fiyatlanmış olur.

## Dönemler
- Günlük aileler (NA-01, NA-02): KEŞİF = verinin başı → 2021-10-31; TEST = 2021-11-01 → 2026-11 (son 5 yıl).
  NA-01 için ayrıca mekanizma çağı: 1990–2011 (oynaklık hedefli fon varlığı küçük) vs 2012+.
- Gün içi aileler (NA-03, NA-04): ESKİ 2018-04 → 2021-10 · KEŞİF 2021-11 → 2024-06 · TEST 2024-07 → 2026-11.
  NA-03 günlük ekinde (^NDX) KEŞİF 1990 → 2021-10, TEST 2021-11 →.

## Maliyet
Günlük: işlem başına 2 bp + uzunda takvim günü başına `lib.FIN_BP_PER_DAY`; kısada finansman alınmaz (muhafazakâr değil
ama simetrik değil — raporlanır). Gün içi: Duka 1m gerçek spread (giriş ask/çıkış bid), ×1,5 stres.

## NA-01 — Oynaklık hedefli fon akışı (^NDX günlük 1985+)
RV20 = son 20 günlük log getirinin std × √252. Vekil pozisyon E = min(1,5; 0,15 / RV20). ΔE5 = E_t − E_{t−5}.
- **OH1 SAT:** ΔE5 ≤ −0,30 → t kapanışı → t+5 kapanışı SAT.
- **OH2 AL:** ΔE5 ≥ +0,30 → t kapanışı → t+5 kapanışı AL.
- **OH1b / OH2b:** aynı, yalnız son 5 gün getirisi |r5| < %2 olan günlerde (fiyattan bağımsız oynaklık değişimi).
Ölçü: tetik ort − tüm günler ortalaması (taban), blok bootstrap (blok 5). Geçme: KEŞİF 2012→2021-10 fark yönü doğru
(OH1 < 0, OH2 > 0) ve P ≥ 0,90; TEST'te aynı yön, P ≥ 0,90; 1990–2011'de etkinin daha küçük olması mekanizmayı destekler
ama ölçüt değil. Korku ailesiyle örtüşme (V1 K1 günleri) raporlanır.

## NA-02 — Varyans primi (VXN 2001+)
VRP = VXN − 100·RV20(NDX). Nedensel yüzdelik: son 504 günde t'nin sırası (min 252).
- **VP1 AL:** yüzdelik ≥ 0,80 → h ∈ {5, 20} gün AL.
- **VP2 SAT:** yüzdelik ≤ 0,20 → h ∈ {5, 20} gün SAT.
- **VP3:** VRP < 0 (ima edilen < gerçekleşen) → h ∈ {5, 20} AL (yön ön-kayıtlı: stres sonrası dönüş).
Geçme: KEŞİF'te fark (tetik − taban) ön-kayıtlı yönde, P ≥ 0,90; TEST aynı yönde, P ≥ 1 − 0,10/6. Bağımsız: QQQ ile
aynı kurallar (VXN aynı); 2001–2010 ve 2011–2021 yarıları ikisi de aynı yönde.

## NA-03 — Hazine 10 ve 30 yıl ihaleleri (TreasuryDirect, 13:00 ET kapanış)
İhale günü D (10-Year Note ve 30-Year Bond, yeni ve yeniden açılış). 20 yıl ve kısa vade dışarıda.
- **HI1:** D günü 13:00 → 16:00 NDX getirisi, taban = ihale olmayan günlerin aynı penceresi. Yön ön-kayıtsız: KEŞİF'te
  işaret seçilir, TEST'te doğrulanır.
- **HI2 (bilgi):** ihale sonucu 13:00'te açıklanır. Zayıf ihale = bid-to-cover aynı vadenin son 6 ihalesinin medyanının
  altında. Zayıf → 13:02 SAT, güçlü → 13:02 AL, çıkış 16:00. Ölçü: zayıf−güçlü fark ve iki bacak ayrı.
- **HI3 (günlük, ^NDX 1985+ / QQQ):** ihaleden önceki gün kapanış → ihale günü kapanış (öncesi taviz) ve ihale günü
  kapanış → ertesi gün kapanış (rahatlama), taban tüm günler.
Geçme: KEŞİF yönünde TEST P ≥ 0,95 ve tetik net > 0; bağımsız MT5 NAS100 (TEST) aynı yön.

## NA-04 — BTC hafta sonu öncülüğü (Binance BTC 5m, Duka NDX 1m)
NDX Cuma 16:00 ET fiyatı P_F, Pazar 18:00 sonrası ilk 1m açılışı P_S. BTC aynı iki anda B_F, B_S.
bw = B_S/B_F − 1, σ = son 26 hafta sonu bw std (nedensel). g = P_S/P_F − 1 (NDX açılış boşluğu).
- **BH0 (ölçüm):** g ~ bw eğimi ve korelasyonu dönem dönem (fiyatlama ne kadar?).
- **BH1:** |bw| ≥ k·σ (k 1,0 / 1,5) → Pazar 18:05'te BTC yönünde NDX, çıkış Pazartesi 09:30 / Pazartesi 16:00.
- **BH2 (eksik tepki):** artık = g − β·bw (β son 52 haftadan, nedensel); |artık| ≥ 1σ_artık → artığın tersi yönde
  (eksik tepki tamamlanır), aynı çıkışlar.
Geçme: KEŞİF (2021-11 → 2024-06) seçilen ≤ 2 hücre, TEST'te tetik net > 0 ve P ≥ 1 − 0,10/2; bağımsız MT5 NAS100
(TEST) aynı yön. ESKİ 2018–21 bilgi amaçlı.

## Hüküm
A/B/C/X defter §5 ölçeği. B için 2. KURAL kartı (6 ölçüt), canlıya bağlama YOK.

## EK-1 (2026-11-18, NA-02 sonucu görüldükten sonra, VP1'in kopya olup olmadığı)
VP1 KEŞİF'te geçti, TEST'te aynı yönde ama P < 0,983. Kopya kontrolü: (a) yalnız VXN düzey yüzdeliği ≥ 0,80 (aynı
504 gün), (b) VP1 ∧ VXN düzey yüzdeliği < 0,80 (prim yüksek ama korku düzeyi değil), (c) VP1 ∧ son 20 gün getirisi ≥ 0
(düşüş sonrası değil). (b) ve (c) KEŞİF + TEST aynı yönde artıysa VP1 bağımsız sayılır; değilse korku ailesinin kopyası.

## EK-2 (2026-11-18, NA-03 sonucu görüldükten sonra — yön TEST'te döndü)
HI1/HI2 SAT ESKİ+KEŞİF'te artı, TEST'te ters. Hipotez: etki faiz rejimine bağlı (ihale arzı faiz yükselirken hisseyi
baskılar). Rejim = ^TNX (10 yıl getirisi) D−1 kapanışı − 60 işlem günü önceki kapanış > 0 ("faiz yükseliyor").
Geçme: yükselen rejimde HI1_SAT ve HI2_zayif_SAT üç dönemin üçünde (ESKİ/KEŞİF/TEST) ve iki beslemede (Duka/MT5) artı,
düşen rejimde fark yok ya da ters. Yeni tanım olduğu için en fazla C+ verilir (kör dönem yok; ileri gölge gerekir).
