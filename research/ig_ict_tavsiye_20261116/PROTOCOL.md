# IG-ICT — Instagram "1 dakikada kârsızdan kârlıya" (iki trader, 9 tavsiye) — ön kayıt

Tarih: 2026-11-16 · Yazıldı: sonuçlara bakılmadan, kod yazılmadan önce.

Kullanıcı: videodaki tavsiyeleri sırayla analiz et. Defter (§2.5 GF-02, §2.17 SM-01…05, §2.21 MZ-01…04,
§2.37 HL, §2.44 OR, §2.55 YL, §2.57 NX) 9 tavsiyenin 7'sini zaten kapsıyor → yalnız iki **yeni tanım** sınanır:

## T1 — SMT uyumsuzluğu + yapı teyidi (IG-01)
Yeniden açma gerekçesi: defterde SMT (iki korele endeksin aynı likiditede uyumsuzluğu) hiç ölçülmedi; YL-06
yalnız US500 öncülüğünü (getiri gecikmesi) ölçtü, uyumsuzluğu değil.

- Veri: Pepperstone MT5 M5 NAS100 + US500 (yon_lab_20261114/data/mt5), ortak barlar; sunucu = NY + 7 sa.
  Spread: NAS100 `sp × 0,1` puan (giriş + çıkışta yarım-yarım değil, giriş anında tam spread).
- Seans: RTH 09:30–16:00 ET (giriş ≤ 15:00, 16:00 zaman çıkışı).
- Likidite: her sembolün kendi önceki RTH tepe/dibi (PDH/PDL) ve gece (18:00–09:25 ET) tepe/dibi (ONH/ONL).
- **Ayı SMT olayı:** RTH barında sembollerden biri ilk kez seviyesinin tepesini aşar (`high > seviye`) ve o bara kadar
  diğeri karşılık gelen seviyesini seans içinde HİÇ aşmamıştır. Boğa aynası dip tarafında. Gün × seviye × yön başına ilk olay.
- **Kontrol olayı (uyumsuzluk yok):** aynı bar civarında (±2 bar) iki sembol de seviyesini aşmış → süpürme var, SMT yok.
- İşlem yalnız NAS100'de, uyumsuzluk yönünde (ayı SMT → SAT).
  - **U (teyitsiz):** olay barının kapanışından sonraki bar açılışında gir.
  - **K (yapı teyitli = videonun iddiası):** olaydan sonra ≤ 12 bar içinde NAS100 5m kapanışı, olaydan önceki son teyitli
    fraktal dibinin (k 2, sağ 2 bar kapanınca bilinir) altına iner (ayı; boğa aynası) → sonraki bar açılışı.
  - Stop: olay barından girişe kadar NAS100 uç noktası (ayıda en yüksek) + spread. Hedef 2R (ana), 1R ve 3R duyarlılık.
    Aynı barda stop + hedef → stop. 16:00 ET'de kapat.
- Ölçütler (ana hücre K · 2R · tüm seviyeler):
  1. ortR > 0 ve bootstrap (gün blok) P(EV>0) ≥ %90; 2. kronolojik iki yarı ≥ 0; 3. **K_SMT − K_kontrol > 0** (SMT süpürmeye
  bilgi ekliyor mu), P ≥ %90; 4. K − U > 0 (videonun "teyit şart" iddiası); 5. spread × 1,5 ile hâlâ > 0.
  Hepsi → B (tek broker, ~17 ay); biri düşerse X. Teyit iddiası (4) ayrıca kendi başına raporlanır.

## T2 — "AM seansından önce 400 puandan fazla düştüyse PM'i bekle" (IG-02)
Yeniden açma gerekçesi: GF-02 H4 premarket ve NX-11 S1 (korku boşluğu → 09:30 AL) var, ama **AM'yi atla / PM'de işlem yap**
karşılaştırması (aynı günde iki seansın işlem kalitesi) ölçülmedi.

- Veri: Dukascopy NDX 1m v3 2018-01 → 2026-11 (UTC epoch → America/New_York).
- Düşüş günü: `D = 09:30 açılış − önceki RTH 16:00 kapanışı`. Tanımlar: **P400** D ≤ −400 puan (videonun kelimesi);
  **R16** D ≤ −%1,6 (400 puanın bugünkü NDX'teki karşılığı, eski yıllara ölçekli). Kontrol: diğer tüm günler.
- AM = 09:30–12:00, PM = 13:30–16:00 ET.
- Ölçümler (her gün, her seans):
  - (a) yön: seans getirisi (bp), uzun ve kısa;
  - (b) testere: verim oranı |net| / (tepe − dip); 1 ATR-seans (önceki 20 günün aynı seans aralığı medyanı × 0,25) iki taraflı
    yarışta "önce bir tarafa vurup sonra öbür tarafa da vurma" oranı;
  - (c) genel taktik vekili: seansın ilk 15 dk aralığı kırılımı (her iki yön, ilk kırılım), stop aralığın karşı ucu, 2R, seans sonu
    çıkışı, sonraki 1m açılışı + gerçek spread. AM-ORB ve PM-ORB (13:30–13:45 aralığı) aynı kural.
- Videonun iddiası geçer ancak: düşüş gününde **PM-ORB − AM-ORB > 0** (P ≥ %90) **ve** bu fark kontrol günlerindekinden büyük
  (etkileşim > 0) **ve** (b)'de AM testeresi kontrol günlerinden kötü. İki dönem (2018-21 / 2022-26) aynı işaret.
  Aksi → X. Ayrıca not: düşüş gününde AM uzun getirisi (S1/CAPREV ailesi) raporlanır — "bekle" tavsiyesinin bedeli.

## Kapsam dışı (defterle yanıtlanır, yeni sınama yok)
Tavsiye 2 (günlük bias < son likidite reaksiyonu) SM-01/MZ-01…04 + bias karnesi; 3 (stopu korunan uca) SM-04/HL-01/§3 braket;
4 (10:00 devamı yarım risk) GF-02 H5 + ORB × VIX (NX-02); 6 (fraktal zaman, HTF FVG likidite) MZ-01…04 + YL-01/02 + FC-03;
7 (iki/tek aşamalı prop hesabı) piyasa kenarı değil, kumarbazın iflası aritmetiği; 8–9 (stop yalnız fikrin yanlışlandığı yer,
FVG girişi ↔ FVG stopu) SM-01 FVG limit + YL-01 D/(U+D).

---

# EK-1 — Derin tur: seans dilimi × haftanın günü × eşik ızgarası (2026-11-16, sonuçlardan önce)

Kullanıcı: "daha detaylı incele, farklı seans dilimlerinde ve gün bazında test et, bir yerde bir şey olmalı."
Çok hücre = şans eseri kazanan. Bu yüzden hüküm **hücre** ve **aile** düzeyinde verilir:

- **Dönemler:** KEŞİF 2018-01-02 → 2022-12-30 · TEST 2023-01-03 → 2026-11-12 (Duka NDX 1m v3). SMT'de ayrıca BAĞIMSIZ =
  Pepperstone M5 2025-06 → 2026-11 (US500 Duka indirmesi tamamlanırsa KEŞİF/TEST Duka, BAĞIMSIZ broker).
- **Hücre geçer:** KEŞİF |t| ≥ 2,0 ∧ TEST aynı işaret t ≥ 1,65 ∧ TEST n ≥ 30 gün (olay) ∧ spread sonrası. Gün kümeli t.
- **Aile geçer:** geçen hücre sayısı, koşul etiketlerinin yıl içinde günler arası permütasyonuyla (200 tekrar) elde edilen sıfır
  dağılımının %95'inden büyük. Ayrıca KEŞİF ilk-20 hücrenin TEST ortalaması raporlanır.
- Geçen hücre → en fazla **C** (sonradan seçim); kart ancak ayrı ön kayıtla.

## F5 — Açılış öncesi düşüş / yükseliş günü × seans dilimi × gün (madde 5)
Koşul (44): ölçü {önceki 16:00 kapanış → 09:30, önceki 18:00 → 09:30} × yön {düşüş, yükseliş} × eşik {puan 150/250/400/600,
yüzde 0,5/1/1,6/2,5, z (20 g günlük getiri σ) 1/1,5/2,5}. Dilim (9): 09:30-10, 10-11, 11-12, 12-13:30, 13:30-15, 15-16, AM, PM, gün.
Gün (6): Pzt…Cum + hepsi. Metrik: dilimin uzun getirisi (bp, spread düşülmüş) − aynı gün grubunda koşulsuz günlerin ortalaması.

## F4 — Açılış hareketi / 10:00 devamı / "manipülasyon" (madde 4)
Giriş T0 ∈ {09:45, 10:00, 10:15, 10:30} açılışı, yön = 09:30 → T0 hareketi (devam; negatif ortalama = dönüş), çıkış
T1 ∈ {11:00, 12:00, 16:00}. Koşul: {hepsi, Judas var, yok} × boşluk {hepsi, yukarı > 0,5σ, aşağı, düz} × VIX {hepsi, ≥ 18,4, <} ×
gün {hepsi, Pzt…Cum}. Judas = ilk 15 dk yönü d1 ve T0'da fiyat 09:30 açılışının öbür tarafında. Yarım risk boyuttur, işaret
değiştirmez → sınanmaz.

## F2 — Günlük bias mı, son likiditeye tepki mi (madde 2)
Seviye {PDH, PDL, ONH, ONL} RTH'de ilk dokunuş τ; tepki penceresi w {5, 15, 30} dk; tepki = τ+w kapanışı seviyenin
içinde (ret) ya da dışında (kabul). Sinyaller: tepki yönü, bias b1 (dünkü RTH getirisi işareti), b2 (kapanış > SMA20),
b3 (dünkü kapanışın aralıktaki üçte biri), b4 (gece yönü 18:00 → 09:30), tepki ∧ b1 uyumu. Giriş τ+w+1 açılışı, çıkış
{+60 dk, +120 dk, 16:00}. τ dilimi {AM, öğle 12-13:30, PM}. Ek doğrudan kıyas: aynı girişlerde tepki-yönü − bias-yönü farkı.

## F3 — "Stop olduktan sonra hedefe gidiyorsa stopu korunan uca koy" (madde 3)
Taban işlemler: 15 dk aralık kırılımı 09:30, 10:00, 13:30 (ilk kapanış dışarıda → sonraki açılış). Hedef fiyatı sabit
(giriş ± 2 × taban risk). Stop: taban (aralığın karşı ucu), korunan (girişten önceki son teyitli 5m fraktal, k 2), geniş 1,5×,
dar 0,5×. Sonuç taban risk biriminde. Ayrıca "pişmanlık oranı" (taban stop sonrası hedefe varma) ve aynı stoplarla **yazı-tura
yön plasebosu**: pişmanlık plaseboda da aynıysa bilgi değil geometridir.

## F6 — Üst TF FVG'leri likidite mi (madde 6)
FVG: boğa low[i] > high[i−2], ayı high[i] < low[i−2], i kapanınca bilinir; ilk dokunuşta dolmuş sayılır. TF {5m, 1H, 4H
(18:00 ET çapası)} × yaş {hepsi, ≤ 1 gün} × ızgara dilimi {03:00-09:30, AM, PM} (15 dk ızgara). Her noktada en yakın dolmamış
üst/alt FVG kenarı (U, D), yarış seans sonuna (16:00; gece için 16:00) kadar. Gözlenen "önce üst" − analitik D/(U+D) farkı (gün kümeli t).
Mıknatıs iddiası = fark ≠ 0 ve iki dönemde aynı işaret.

## F1 — SMT ızgarası (madde 1)
Seans {Asya 18:00-02:00, Londra 02:00-08:00, NY sabah 09:30-12:00, öğle 12-13:30, öğleden sonra 13:30-16:00} × seviye
{PDH/PDL, gece H/L, Asya H/L, Londra H/L, son 60 dk H/L} × teyit {yok, fraktal k2, fraktal k3, seviyenin içine geri kapanış}
× hedef {1R, 2R, 3R, seans sonu} × gün {hepsi, Pzt…Cum}; her hücrede SMT − kontrol (aynı barda iki endeks) farkı da.

### EK-1b — F1 veri değişikliği (sonuçlardan önce, 2026-11-16)
Dukascopy USA500 indirmesi 503/URLError ile kısıtlandı (50 dk'da 23 gün) → durduruldu. Yerine broker M30
(`c1_turev_20261105/data/mt5/{NAS100,US500}_M30.csv.gz`). Eksen denetimi: NAS100 açılış hacmi tepesi 2018–2026 her yıl 09:30 ET
(%66–74); US500 M30 2019 ve öncesi günlük bar, **2020 kısmen bir bar kayık** (getiri korelasyonu gecikme 0: 0,46, gecikme 1: 0,31),
2021+ temiz (gecikme 0: 0,88–0,97, ±1: |r| ≤ 0,03). Dönemler: KEŞİF 2021-01 → 2023-06 · TEST 2023-07 → 2025-06-17 (M30) ·
BAĞIMSIZ 2025-06-18 → 2026-11-13 (M5, IG-01 verisi). M30'da teyit penceresi 4 bar (2 sa), fraktal k 2; M5'te 12 bar (1 sa).
Seans ızgarası, seviyeler, teyit türleri, hedefler, gün ve geçme ölçütleri EK-1 F1'deki gibi; "son 60 dk H/L" M30'da önceki 2 bar.
