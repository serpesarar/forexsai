# Ön kayıt — BTC scalp ailesi "volatilite + fiyat yapısı" (fam_volyapi)

Yazım: 2026-10-22, **hiçbir sonuç hesaplanmadan önce**. Bu dosya bir daha düzenlenmez; değişiklik yalnız sonuna
"EK-n" başlığıyla, tarih ve gerekçeyle eklenir.

Girdi notları: `research_notes/BTC scalping strateji araştırması/01…03`, `research_notes/BTC trader bot kenar araştırması/05`,
`docs/KAPI_KAYIT_DEFTERI.md` §0, §1 (E1–E50), §2.11, §3.

## 0. Defter kontrolü (3. KURAL) — neden yeniden açılıyor?
- BTC'de daha önce denenip X çıkanlar: 5m Donchian48 kırılımı (BTC-T08), kanal-sınır dönüşü 15m/1h (BTC-M01), ABD nakit saatleri
  L/S (BTC-M05), ilk-30-dk momentumu (BTC-T07/H3), saat-of-gün (BTC-M03). **Burada bunlar tekrarlanmıyor.** Yeni tanımlar:
  (i) *sıkışma koşullu* kırılım (BB genişlik yüzdeliği), (ii) VWAP sapması (BTC'de hiç sınanmadı), (iii) seans açılış aralığı
  kırılımı / başarısız kırılım (BTC'de hiç sınanmadı; NDX'te OLD-15/FG'de X), (iv) önceki saat/gün ucu süpürme-geri alma
  (fakeout fikrinin BTC'de strateji olarak ilk sınaması), (v) makro olay dakikası (BTC'de ilk), (vi) BTC-T07'nin C sınıfı yan
  gözleminin (ABD seansında stoplu+zamanlı rastgele long VE short ikisi de +) açık plasebolu sınaması (E43).
- Yeni gerekçe: scalp ölçeği (SL ≥ 19 bp, 10–60 dk) ve ortak maliyet/icra protokolü (not 03 §5) daha önce bu ailelerde
  uygulanmadı. NDX/XAU'daki olumsuz sonuçlar (OLD-15, FG, GF-02, MK-07 R4) başka piyasada; BTC yeni veri.
- Ön beklenti (kayıt için): defter §3 ilke 1 ("rastgele girişte tek-özellikli durum kapısı yok") ve scalp notu §5-G
  ("dürüst kısa-vade kenarları 0,03–0,1R") nedeniyle **çoğu hücrenin plasebo düzeyinde kalması beklenir**.

## 1. Veri ve icra (ortak protokol, tüm hücreler)
- Fiyat: `research/btc_scalp_20261021/data/btc_scalp_1m.parquet` **spot** OHLCV (Binance BTCUSDT). Perp (`perp_*`) yalnız
  seçilen adaylar için çapraz kontrol (aynı sinyal, perp yolunda sonuç).
- ts satırı [ts, ts+60s) dakikası; değerleri ts+60s'de bilinir. Karar = dakika t'nin kapanışı; giriş = **t+1 açılışı** (e = t+1).
- Dışlama: 2023-03-24 11:28–14:00 UTC; `spot_missing` dakikaları NaN; ≥5 dk süren boşluklar BAD. Giriş, [e, e+L) penceresi
  BAD ile kesişirse atılır (lib.py kuralı). <5 dk boşluk dakikaları dokunuşsuz sayılır.
- Geometri (tek kural): SL mesafesi s = max(19 bp, 1,1×ATR14(5m)) (ATR: e'den önce tamamlanmış son 14 adet 5m bar,
  bp = ATR / close[t]). TP = r·s, r ∈ {1, 2}. Zaman stopu H ∈ {30, 60} dk. → 4 geometri:
  G1 = (r1, H30), G2 = (r1, H60), G3 = (r2, H30), G4 = (r2, H60).
- **Rollover zorunlu kapanışı:** broker rollover'ı NY 17:00 (yaz 21:00 / kış 22:00 UTC). Pozisyon en geç NY 16:58'de
  (16:57 barının kapanışı) kapanır: L_eff = min(H, NY16:58 − e). L_eff < 10 dk ise giriş yok; NY 16:55–17:05 arası giriş yok.
- Dolum: giriş open[e]. TP limit, seviyeden. SL: ilk dokunan barda long için min(SL, open[hit]) (boşluk-duyarlı), short ayna;
  **kayma** 1 bp, o dakikanın |1m kapanış getirisi| takvim yılının %99 yüzdeliğinin üstündeyse 5 bp. Zaman çıkışı: son barın
  kapanışı. Aynı barda TP+SL → **SL** (ana); ayrıca iyimser (→TP) ve OHLC-sezgisel (o barın açılışı hangi seviyeye yakınsa o
  önce; giriş barında açılış = giriş fiyatı → yakın olan SL'dir (r ≥ 1)) raporlanır. Stratejinin aynı-bar oranı ≥ %0,5 ise hücre
  "geçersiz (alt-dakika gerekir)" damgası alır.
- Maliyet (gidiş-dönüş, bp, brüt getiriden düşülür): **PEP 1,85** (birincil) · PEP_STRESS 2,78 · PEP_FIX15 = 15 $ / giriş fiyatı ·
  BIN_MAKER 4 · BIN_TAKER 10. R = net bp / s.
- İyimser icra (kart ölçütü 5): aynı seviyeler, maliyet 0, kayma 0, aynı-bar → TP. (BTC 1m'de close[t] ≈ open[t+1]; spot ardışık
  boşluk medyanı 0,00 bp — not 03 §3 — bu yüzden giriş fiyatı farkı ihmal edilir ve iyimser = open[e] girişli maliyetsiz sürüm.)

## 2. Bölmeler (sabit)
DISCOVERY 2021-06-01 → 2023-12-31 · OOS 2024-01-11 → 2025-06-30 · BLIND 2025-07-01 → 2026-10-20 (giriş anına göre).
2024-01-01→01-10 hiçbir bölmeye girmez. Parametre/geometri/varyant seçimi **yalnız DISCOVERY**'de. Kart penceresi = POST = OOS ∪ BLIND.

## 3. Hipotezler ve tetik tanımları (hepsi nedensel; yalnız ≤ t bilgisi)

Ortak: her hücre = hipotez varyantı × yön (L/S) × geometri (G1–G4). Tetik dakikası t; giriş t+1.

### VS1 — 5m sıkışma kırılımı
- 5m barlar UTC ızgarası (kova = dakika//5), yalnız tamamlanmış barlar. BBW_k = std20(close5)/sma20(close5).
- Sıkışma: önceki 5m barın (k−1) BBW'sinin, kendisinden önceki 2016 adet 5m barın (7 gün) BBW dağılımındaki yüzdeliği ≤ 10.
- Tetik L: 5m bar k kapanışı > önceki 12 adet 5m barın (k−12…k−1) en yüksek high'ı ∧ sıkışma(k−1). S ayna (low).
  t = bar k'nın son dakikası. Aynı yönde son tetikten ≥60 dk sonra yeniden tetiklenebilir.
- Kontrol hücresi VS1-C: aynı kırılım, sıkışma koşulu yok (sıkışmanın katkısını ölçer).

### VS2 — 1m sıkışma kırılımı (not 01 H11'in akışsız hâli)
- BBW60_t = std(close[t−60…t−1])/ort; sıkışma: BBW60_{t−1} önceki 1440 dakikanın BBW60 değerlerinin yüzdeliği ≤ 5.
- Tetik L: close[t] > max(high[t−60…t−1]) ∧ sıkışma(t−1). S ayna. Yön başına 60 dk tetik aralığı.
- Kontrol VS2-C: aynı 60 dk kırılım, sıkışmasız.

### ST — ABD seansı "straddle" (BTC-T07 yan gözlemi; E43 sınaması)
- **ST-H (replikasyon, scalp değil; teşhis):** her hafta içi gün (Pzt–Cum), NY 10:00 açılışında long VE short; SL = 1×ATR14(1h)
  (son tamamlanmış UTC 1h barları), TP yok, çıkış NY 15:59 barının kapanışı. PEP maliyeti. Tüm bölmelerde L, S, (L+S)/2.
  Teşhisler (hepsi önceden tanımlı):
  (a) **saat plasebosu**: aynı kural NY 00:00…23:00 her tam saat çapası, 6 saat tutuş (rollover'ı geçebilir, swap yok sayılır;
      yalnız yol dinamiği için); 10:00 çapasının (L+S)/2 değerinin 24 çapa içindeki sırası;
  (b) **sentetik martingal plasebosu**: göreli (o,h,l,c)/önceki kapanış dörtlüleri aynı NY dakika-of-gün içinde günler arasında
      karıştırılır (gün-içi oynaklık profili korunur, seri bağımlılık yok edilir; E42), yol yeniden kurulur; 20 tekrar;
      beklenti (L+S)/2 ≈ −maliyet/2R;
  (c) gün-blok bootstrap ile (L+S)/2 > 0 olasılığı; (d) ABD seansı 10–16 NY varyans oranı VR = Var(6s getiri)/(6·Var(1s getiri))
      bölme bazında.
  Karar kuralı: (L+S)/2 > 0 üç bölmenin üçünde ∧ saat plasebosunda ilk %10'da (24 çapada ilk 3) ∧ sentetikte tüm 20 tekrar
  altında → "gerçek yönsüz devam etkisi"; aksi hâlde "E43 artefaktı/gürültü".
- **ST-S (scalp):** çapa NY 09:30 ve NY 10:00 (iki varyant); çapa dakikasında (karar = önceki dakikanın kapanışı) long ve short
  ortak geometriyle (G1–G4). Hücreler L ve S ayrı; ayrıca (L+S)/2 raporlanır. Bu, sabit-saat kuralıdır; plasebo (aynı saat
  rastgele dakika) neredeyse kendisidir → asıl kıyas: sentetik değil, **aynı geometrinin aynı saat tabanı** ve L+S toplamı.

### OR — Açılış aralığı (seans açılışları)
- Seanslar: ASYA 00:00 UTC (OR 30 dk) · LONDRA 08:00 Europe/London (OR 30 dk) · ABD 09:30 America/New_York (OR 15 ve 30 dk) → 4 varyant.
- ORH/ORL = OR penceresindeki high/low. İzleme penceresi: OR bitişinden sonraki 120 dk.
- **ORB (kırılım):** izleme penceresinde ilk 1m kapanış > ORH → L, < ORL → S; seans başına yalnız ilk kırılım (hangi taraf önceyse).
- **ORF (başarısız kırılım/süpürme dönüşü):** j = izleme penceresinde high > ORH olan ilk bar; tetik = j…j+3 içinde ilk kapanış < ORH,
  koşul: max(high[j…tetik]) − ORH ≤ 1×ATR14(5m) → **S**. Ayna: low < ORL, kapanış > ORL → **L**. Seans başına taraf başına ilk dürtme.

### VW — VWAP sapması
- Çapa: D = 00:00 UTC günlük; U = NY 09:30 (U yalnız NY 09:30–15:59 aktif). VWAP_t = Σ q / Σ v (çapadan t'ye, dahil;
  q = spot quote hacmi, v = spot baz hacmi); σ_t = hacim-ağırlıklı std (dakika tipik fiyatı p_i = q_i/v_i, VWAP etrafında).
  Aktivasyon: D çapadan ≥60 dk, U ≥30 dk sonra.
- **VW-REV (dönüş):** close[t] > VWAP_t + kσ_t ∧ close[t−1] ≤ VWAP_{t−1} + kσ_{t−1} → **S**; alt ayna → **L**. k ∈ {2, 3}.
  Yön başına 30 dk tetik aralığı.
- **VW-REC (geri alma devamı):** son 120 dk içinde bir kapanış ≤ VWAP − kσ olmuş ∧ close[t] > VWAP_t ∧ close[t−1] ≤ VWAP_{t−1}
  → **L**; ayna → **S**. k ∈ {1,5; 2,5}. Yön başına 30 dk tetik aralığı.

### LS — Likidite süpürme + hızlı geri alma (fakeout fade'in scalp sınaması)
- Seviyeler: PH/PL = önceki tamamlanmış UTC saatinin high/low'u (yalnız içinde bulunulan saat boyunca geçerli);
  PDH/PDL = önceki UTC gününün high/low'u (gün boyunca geçerli).
- Tetik S: j = seviyenin (o saat/gün içinde) ilk aşıldığı bar (high[j] > PH); j…j+3 içinde ilk kapanış < PH ∧
  max(high[j…tetik]) − PH ≤ 1×ATR14(5m). Ayna L (low < PL, kapanış > PL). Seviye başına taraf başına ilk süpürme.
- Varyantlar: LS-H (saat), LS-D (gün).

### MA — Makro olay dakikası
- Takvim: repoda zaten var olan `research/xau_best_days_20261015/makro/out/calendar.csv` (yalnız okunur; FOMC 14:00 ET,
  CPI/NFP 08:30 ET, DST-doğru UTC). **Yeni indirme yok.** Bilinen kapsam boşluğu: FOMC 2026-07 ve 2026-09 kayıtlı değil.
- Olay dakikası T (bar ts = açıklama dakikası). r0 = log(close[T]/open[T]). Karar = T barının kapanışı, giriş T+1.
- **MA-C** devam: yön = sign(r0); **MA-F** dönüş: yön = −sign(r0); r0 = 0 → olay yok. Gruplar: CPI+NFP birlikte, FOMC ayrı.
  (Yön L/S ayrılmaz; hücre = grup × C/F × geometri.)
- n küçük (bölme başına ~25–65 olay) → ancak bilgi/gölge kanıtı; kart hacmi yapısal olarak geçilemez.

Hücre sayısı: VS1 16 + VS1-C 16 + VS2 8 + VS2-C 8 + ST-S 16 + ORB 32 + ORF 32 + VW-REV 32 + VW-REC 32 + LS 16 + MA 16 = **224**.
(ST-H teşhis hücreleri çoklu-test sayımına girmez.)

## 4. Kıyas, istatistik ve seçim
- **Plasebo (P1):** her işlem için aynı takvim yılı × aynı UTC saatinden, aynı geometri kuralına uygun (geçerli giriş, ATR var,
  L_eff ≥ 10) rastgele dakika, aynı yön, aynı geometri kuralı (o dakikanın kendi ATR'si); 200 tekrar. Hücre ortR'sinin plasebo
  ortR dağılımındaki yüzdeliği; P1 ortalaması "taban" olarak raporlanır. MA için aynı yıl × aynı UTC saat (olay olmayan günler dahil).
- Gün-blok bootstrap (giriş UTC günü, 2000 tekrar): %95 GA ve P(EV>0).
- **Holm** (α = 0,05, 224 hücre): DISCOVERY'de tek yönlü, gün-kümeli z = ortR / SE_küme, H0: ortR ≤ 0.
- **max-z seçim düzeltmesi** (E24/E30): z_c = (ortR_c − ort(P1_c))/sd(P1_c); boş dağılım = her plasebo tekrarında
  z_{c,b} = (P1_{c,b} − ort(P1_c))/sd(P1_c)'nin hücreler üzerinden maksimumu; p_sel = P(max z_b ≥ z_seçilen). DISCOVERY'de.
- **Seçim:** her hipotez ailesinde (VS1, VS2, ST-S, ORB, ORF, VW-REV, VW-REC, LS, MA; kontrol hücreleri seçilmez) DISCOVERY net ortR
  (PEP) en yüksek hücre, yalnız n_DISC ≥ 50 olanlar arasından (E40). Seçilen hücre POST'ta (OOS ∪ BLIND) karta girer.
- Brüt kenar çıtası: (brüt ortR − brüt P1 ortR) ≥ 0,15R **veya** ≥ 2 × (maliyet/R ortalaması).

## 5. Canlıya alma kartı ve verdikt (POST penceresinde)
1 n ≥ 150 · 2 ortR > 0 ∧ gün-blok P(EV>0) ≥ %90 · 3 kronolojik iki yarının ikisi de ≥ 0 · 4 PEP_STRESS'te ortR > 0 ·
5 |ortR(iyimser) − ortR(gerçek)| ≤ 0,5·|ortR(gerçek)| · 6 tek pozisyon (önceki çıkıştan önce gelen tetik atlanır) ortR > 0.
Ek: (7) P1 yüzdeliği ≥ %95 · (8) BLIND ortR > 0 · (9) brüt kenar çıtası · (10) aynı-bar < %0,5 · (11) DISCOVERY max-z p_sel ≤ 0,10.
- **LIVE-aday:** 1–11 hepsi. **SHADOW:** kart 1–6'dan ≥5 ∧ (7) ≥ %90 ∧ (8). **RED:** diğer her durum.
  (Kural (11) ve Holm bilgi olarak da raporlanır; LIVE-aday için (11) zorunlu.)

## 6. Raporlanacaklar (her hücre, her bölme)
n, WR, ortR (PEP), ort bp (net), %95 GA, P(EV>0), yarılar, stres, iyimser fark, tek-poz ortR, P1 ortR ve yüzdelik, BLIND,
yıl bazında ortR işaretleri, işlem/gün, aynı-bar oranı, maliyet varyantları (FIX15, BIN_MAKER, BIN_TAKER).
Seçilen adaylar için ayrıca: perp yolu çapraz kontrolü, R ↔ bp tutarlılığı (E50).

---
## EK-1 (2026-10-22, sonuç hesaplanmadan önce — tanım boşluğu kapatma)
- §3'te gün kapsamı yazılmamıştı. Sabitlenen: **OR (ASYA/LONDRA/ABD), ST-S, ST-H ve VW-U** yalnız ilgili yerel takvimin
  hafta içi günlerinde (ASYA: UTC tarihi Pzt–Cum; LONDRA: Londra tarihi Pzt–Cum; ABD/U: New York tarihi Pzt–Cum; resmî tatiller
  ayıklanmaz). **VS1, VS2, VW-D, LS, MA** 7/24 (MA zaten olay günleri).
- VS1 5m BBW yüzdeliği: pandas `rolling(2017).rank(pct=True)` (pencere bar k−1'in kendisini içerir; min 1000 bar);
  VS2: `rolling(1441).rank(pct=True)` (min 1000). Yüzdelik ≤ eşik.
- Kayma eşiği (%99 |1m getiri|) takvim yılı bazında tüm dakikalardan hesaplanır (maliyet varsayımı, sinyal değil).
- ST-H çıkışında SL kayması ve aynı kurallar ortak motorla aynıdır; ST-H saat plasebosu çapaları NY tam saatleridir.

## EK-2 (2026-10-22, hücre sonuçları okunmadan önce; yalnız sayım düzeltmesi)
- §3'teki hücre sayımı aritmetik hatalıydı (VS1 ve VS1-C 2 yön × 4 geometri = 8'er hücre, 16 değil). Tanımlar değişmeden
  gerçek hücre sayısı **208**. Holm m = 208 ile uygulanır; muhafazakâr kontrol olarak m = 224 sonucu da yazılır.
- ST-H sentetik plasebosunda karıştırma "aynı takvim ayı × aynı NY dakika-of-gün" grupları içinde yapıldı (oynaklık rejimi korunur);
  bu, §3'teki "aynı NY dakika-of-gün içinde günler arasında" tanımının alt kümesidir.
