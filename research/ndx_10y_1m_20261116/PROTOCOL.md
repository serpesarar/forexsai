# NDX 9 yıllık 1m yeniden sınama + genişletme + yeni kapılar — ÖN KAYIT (2026-11-16)

Kullanıcı isteği: "Nasdaq üzerindeki tüm kapıları/stratejileri yeni indirilen ~10 yıllık 1 dakikalık veride tekrar test et,
mevcutları genişlet/geliştir, yeni kapılar ve stratejiler ara; daha zengin veriyle daha ne yapabiliriz?"

Bu dosya sonuçlara bakılmadan yazıldı. Sonradan eklenen her şey `EK-n` başlığıyla ve tarihle eklenir.

## 0. Veri ve neyin gerçekten yeni olduğu

- Kaynak: `research/nom_20261113/data/ndx_1m_v3_duka.parquet` — Dukascopy USATECHIDXUSD BID 1m, **2018-01-02 → 2026-11-13**,
  2.963.071 bar, `spr` = NY saatine göre spread modeli (bp × fiyat; 2025 gözlenen). Tek besleme (FAZ_0 EK-6: 2018-01→2021-10
  tamamı 2026-11-16'da indi; MT5 altın standartla gecikme 0, r 0,978–0,996).
- **Yeni olan:** 2018-01 → 2021-10 dilimi ilk kez aynı beslemede 1m. Önceki sınamalar bu dönemi broker M30/H1 (C3b, KSG, FOMC,
  çekiç), 1h (CAPREV, ORB×VIX 2016-21 "1h geometrisi") veya hiç (CK2 portföy/acil stop: 2021-11→2026-10) ile görmüştü.
  2021-11 → 2026-11 dilimi 1m'de zaten incelenmişti (KT-01, CK2) → orada bu çalışma yalnız **tekrar üretim** sayılır.
- Dönemler: **ESKİ = 2018-01-01 → 2021-10-31** (yeni 1m), **YENİ = 2021-11-01 → 2026-11-13**. İkisi kronolojik ayrık.
- Saat: tüm hesaplar `America/New_York` (DST doğru); NYSE tatil/yarım gün `backend/services/nom/nyse_calendar.py`.
- VIX: `research/nom_20261113/data/macro/macro_daily.parquet` (yfinance kapanış). Kural "dünkü VIX" = karar gününden önceki son
  VIX kapanışı. FOMC: `calendar.parquet` (event == FOMC, karar günü). SPY/TLT: `research/qs03_akis_takvim_20261111/data/`.

## 1. Maliyet / icra modeli (tüm kurallar aynı)
- Fiyatlar BID. Alış = bar açılışı/seçilen fiyat + `spr` (ask), satış = BID. Kısa işlemde tersi. Ek kayma yok (CAPREV kartındaki
  0,2 puan kayma CAPREV'de korunur).
- Gecelik finansman: uzun pozisyonda takvim günü başına %6,41/365 (NAS100 güncel swap, FR-18) → ≈ 1,76 bp/gün.
- Stop/TP çözümü 1m BID high/low ile; aynı 1m barda stop ve TP ikisi birden → **stop** (muhafazakâr, E58).
- Stres: `spr × 1,5`.

## 2. A — Dondurulmuş kuralların yeniden sınaması (parametre değişmez)
Tanımlar canlı koddan birebir (`yeni deneme/*_live.py`, `*_shadow.py`):
| Kod | Kural | Ölçü |
|---|---|---|
| A1 C3b | S = 15:30 ET barından önceki 30 dk barın kapanışı (15:29 1m kapanışı), E = 15:30 açılışı; RSI2-Wilder(S) < 10 → E'de AL; çıkış ilk S_t > S_{t−1} günü E'de, en geç 5 işlem günü; tek pozisyon; çıkış günü sinyal varsa yeniden gir | net bp |
| A1b C3 | aynı giriş, ertesi işlem günü E'de çık | net bp |
| A2 CAPREV | stres (r1 ≤ −%1,5 ∨ r5 ≤ −%4; RTH 09:00–16:00 kapanışları) ∧ dünkü VIX ≥ 18,4, Pzt–Per; tetik: 03:00 ≤ bar başı, bitiş ≤ 15:00 ET ilk kapanmış 1h bar kapanışı < önceki RTH (09:00–16:00) dibi → bar bitişinde AL (+0,2 kayma); stop giriş×(1−dvol20); çıkış 16:00 | R (risk = giriş×dvol) |
| A3 ORB×VIX | OR = 09:30–09:45 ET; ilk 5m kapanış > OR tepesi (bar bitişi ≤ 15:30) → sonraki 5m açılışında AL; SL OR ortası; TP 2R; 15:55 çıkış; risk < giriş×%0,05 → yok; dünkü VIX ≥ 18,4 | R |
| A4 FR-15 çekiç | UTC saat başı 1h bar i: alt fitil/aralık ≥ 0,70 ∧ alt fitil ≥ 0,20×ATR14 ∧ alt ≥ üst fitil; i+1 low > i low ∧ close > i high → i+2 açılışında AL; SL i low; TP 5R; 24 sa; Cuma 16:45 NY çıkış; risk < 2×spr → yok; tek pozisyon | R |
| A5 KSG | O16/O15 − 1 < 0 (15:00 ve 16:00 ET bar açılışları) → 16:00 AL, ertesi işlem günü 09:30 SAT; kısa gün yok | net bp |
| A6 AYSONU son seans | D = ayın son NYSE günü; Δ = SPY − TLT ay içi getirisi (önceki ay son kapanış → D−3 kapanışı); Δ ≥ +%2 SAT, ≤ −%2 AL; D 09:30→16:00 | net bp |
| A7 AY BAŞI uzun (E2) | Δ_D (D kapanışında) ≥ +%2 → D 16:30 AL → D+3 işlem günü 16:30 | net bp |
| A8 FOMC gecesi | planlı FOMC karar gününden önceki işlem günü 16:00 AL → FOMC günü 09:30 | net bp |

Raporlanan: n, ort, medyan, isabet, blok-bootstrap (ay bloğu) P(ort>0), ESKİ/YENİ ayrı, yıl tablosu, spr×1,5, en iyi 5 işlem hariç,
en kötü işlem, MAE (1m) dağılımı.
**Hüküm ölçütü (ESKİ dilim, kural başına):** "DAYANIYOR" = ESKİ ort > 0 ∧ ESKİ P ≥ 0,80 ∧ tüm dönem P ≥ 0,95; "ZAYIF" = ESKİ ort > 0
ama P < 0,80; "ÇÖKTÜ" = ESKİ ort ≤ 0. (ESKİ'de olay sayısı küçük kurallar için P eşiği bilgi amaçlıdır.)

## 3. B — Genişletme: komşuluk haritası (seçim değil, kırılganlık ölçümü)
Her parametre ızgarası iki dönemde AYRI koşulur. Canlı parametre bir "plato"da mı (komşuların ≥ %70'i aynı işarette, iki dönemde),
yoksa tepede mi? Bir komşu **iki dönemde de** canlı parametreden iyi ve fark P ≥ 0,90 ise "geliştirme adayı (C+, gölge)" — canlıya
doğrudan değil.
- B1 ORB×VIX: OR ∈ {5, 15, 30} dk × TP ∈ {1,5; 2; 3}R × VIX eşiği ∈ {16; 18,4; 22; 25} × tetik TF ∈ {1m, 5m}.
- B2 CAPREV: tetik TF ∈ {1h, 30m, 15m, 5m}; çıkış ∈ {aynı gün 16:00, ertesi gün 16:00}; VIX eşiği ∈ {18,4; 22; 25}.
- B3 C3b: RSI eşiği ∈ {5, 10, 15}; azami tutuş ∈ {3, 5, 8}; giriş ∈ {15:30, 16:00} (KT-01 A2 16:00 C).
- B4 KSG: sinyal penceresi ∈ {14:30→16:00, 15:00→16:00, 15:30→16:00}; çıkış ∈ {09:30, 10:00}.
- B5 Çekiç: fitil oranı ∈ {0,6; 0,7; 0,8}; TP ∈ {3; 5}R; tutuş ∈ {16; 24} sa.

## 4. C — Önceden kayıtlı kapı/strateji hipotezleri
- **H1 ORB OR-genişliği dozu.** g = OR genişliği / önceki 20 günün RTH aralığı ortalaması. ORB×VIX olaylarında g tertilleri.
  Öngörü (§3-20 "sıkışma sonrası kırılım başarısız"): dar tertil < geniş tertil. Geçer: fark aynı işaret iki dönemde ∧ havuz P ≥ 0,95.
- **H2 Oynaklık-yönetimli kitap (Moreira–Muir 2017 uyarlaması).** Canlı kuralların tümü (A1–A8 canlı lotlarla) aylık P&L'i, her işlemin
  boyutu × (hedef / RV20), RV20 = önceki 20 günün 1m getirilerinden gerçekleşen oynaklık, sınır [0,5; 2], ortalama boy 1'e normalize.
  Öngörü yok (C3b kenarı stresle büyür → ters yön olası; ikisi de raporlanır). Geçer: aylık Sharpe farkı iki dönemde aynı işaret ∧ P ≥ 0,90.
- **H3 Panik freni.** Dünkü VIX ≥ 35 → yeni uzun giriş yok (tüm kurallar). Öngörü: o günlerde açılan işlemler eksi. Geçer: atlanan
  işlemler ort < 0 ∧ kitabın max düşüşü azalır ∧ toplam P&L kaybı < düşüş kazancı. (Olay sayısı küçük; en fazla C+.)
- **H4 KSG yoğunluk dozu.** z = r(15:00→16:00) / σ(önceki 20 günün aynı saat getirisi). KSG gecelerinde z tertilleri. Öngörü:
  derin düşüş (en eksi tertil) en iyi gece. Geçer: monoton iki dönemde ∧ uç fark P ≥ 0,95.
- **H5 Önceki C+ etiketlerinin ESKİ 1m dilimde ölçümü** (tanımlar defterdeki gibi, ayarsız): NK-04 (ORB × dün NDX düştü),
  CK2-03 (CAPREV × dün son saat aşağı ∧ giriş 09:30 öncesi), DB-02 (KSG × dünkü VIX ≥ 25), TS-01 O4 (C3b vade haftası kötü),
  KT-01 A4 (C3b ekleme birimi > 0), KT-01 A2 (C3b 16:00 girişi > 15:30). Geçer: ESKİ dilimde aynı işaret.
  Not: bu etiketlerin çoğu broker 2018-05+ verisini de görmüştü → ESKİ dilim zaman olarak bağımsız değil, **besleme/çözünürlük**
  olarak bağımsız. Hüküm buna göre yazılır.
- **H6 Kitap stres sınaması (CK2-07'nin 2018-21'e uzatılması).** Canlı lotlarla (C3b 2,0 · CAPREV 1,0 · ORB 0,75 · çekiç 0,5 · KSG 0,5 ·
  AYSONU 1,0 · E2 0,75; FOMC gölge 0,5 varsayımsal) 1m yol üstünde birleşik kitap: en kötü gün, en kötü gece, max düşüş, acil stop
  (C3b %10, KSG %7, AYSONU %4/%8) kaç kez değerdi, 4,5 lot tavanı kaç kez bağladı. Bilgi (A/olgu), geçme ölçütü yok.

## 5. Yöntem tuzakları kontrolü (defter §1)
E1/E15/E16 sızıntı: her karar yalnız karar anından önce kapanmış barları kullanır (otomatik test: geleceği bozunca geçmiş karar değişmez).
E58 1m ilk dokunuş: aynı bar stop+TP → stop. E104 karışık besleme: tek besleme. E110: doz/filtre iddiası aylık Sharpe ile.
E23 çoklu bakış: B'de yalnız "iki dönemde de" kuralı; C'de hipotez sayısı 6, sonuçlar ham ve Holm ile birlikte.

## EK-1 (2026-11-16, A/B/C sonuçları görüldükten SONRA, aşağıdakiler koşulmadan önce yazıldı)
Gerekçe: B1'de ORB×VIX TP 3R iki dönemde 2R'yi geçti (plato: OR15/5m'de dört VIX eşiğinin dördü); H5'te üç C+ etiketi ESKİ 1m'de
aynı işareti verdi; H1 ters çıktı ama R birimi risk genişliğiyle karışık olabilir. Bunlar **sonradan** gelen sorular; sınıf en fazla B−.
- **EK1-a ORB çıkış eğrisi:** TP ∈ {2, 3, 4, 5, yok (yalnız 15:55)} × OR15/5m/VIX 18,4. "Braket ≠ zaman" (§3-5) öngörüsü: TP uzadıkça
  iyileşir. Ölçü ay başına R ve bp. Ayrıca TP 3R için 2. KURAL kartının 6 ölçütü (≥150 olay; ort > 0 ∧ P ≥ 0,90; iki yarı ≥ 0;
  spr×1,5 > 0; icra: giriş zaten sonraki 5m açılışı + spread — iyimser 'tetik barı kapanışı' girişiyle fark ≤ ort/2; tek pozisyon).
- **EK1-b H1'in bp ile tekrarı:** dar/geniş OR tertilinde net bp (R birimi değil). Bp'de de dar > geniş ise "dar açılış kırılımı" doz adayı (C).
- **EK1-c Doz etiketlerinin kitap düzeyi sınaması (E110):** canlı lotlarla kitap, ortalama lot sabit tutularak
  (i) ORB lotu dün düşüşte ×1,5, aksi ×0,5; (ii) KSG lotu dünkü VIX ≥ 25'te ×2, aksi ×(1 − p·1)/(1 − p) normalize; (iii) C3b lotu vade haftasında
  ×0,5, aksi normalize. Geçer: aylık kitap Sharpe'ı iki dönemde de artar ∧ birleşik P ≥ 0,90.
- **EK1-d FOMC öncesi sürüklenme uzatması (Lucca–Moench 2015):** FOMC gecesi çıkışı 09:30 yerine karar günü 13:55 ET (14:00 açıklamasından
  önce); ve 24 saatlik pencere (D−1 14:00 → D 13:55). Geçer: 09:30 çıkışını iki dönemde aşar (bp, n küçük → en fazla C+).
