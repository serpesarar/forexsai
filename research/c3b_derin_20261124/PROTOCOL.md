# C3D — C3b derin araştırma: zarar eden işlemleri küçült, kazananları büyüt, "%40 iyileşme" hedefi — ÖN KAYIT (2026-11-24, aday sonuçlarından ÖNCE)

## Kullanıcı isteği
> "C3b kârın %36'sını getiriyor, en kötü 10 günün zararının %57'sini taşıyor dedin; C3b'yi detaylı derin araştırmaya sok, SL'lerin SL olmasını
> engelleyip yaptığı TP'leri arttır, %40'lık bir iyileşme oranı garantisiyle gelene kadar çalış, farklı bakış açılarından bak."

**Ölçüt tanımı (kullanıcının dilinin dürüst karşılığı):** C3b'de stop yok. "SL" burada zararla kapanan işlem, "TP" kârla kapanan işlem.
Lotu büyütmek her şeyi büyütür, bu yüzden iyileşme **aynı riskte** ölçülür:
- **Birincil ölçü:** Calmar = toplam net / |maks. düşüş|. Bu, ölçekten bağımsızdır. "Calmar ×1,40" demek, maks. düşüş aynı tutulduğunda
  (lotlar tekdüze ölçeklendiğinde) net kârın %40 artması demektir.
- **Kullanıcı dilinde rapor (betimleyici):** eşit maks. düşüşe ölçeklenmiş kitapta zararla kapanan işlemlerin toplam zararı ve kârla kapananların toplam kârı,
  ayrıca en kötü 10 gün.
- **"Garanti" sınırı:** geçmiş veride ve bağımsız veride ölçülen iyileşme garanti edilebilir. Gelecek garanti edilemez; rapor bunu açıkça söyler.

## Defter kontrolü (3. KURAL) — C3b'de daha önce denenenler
- Stop kenarı siler (TR-C3, KZ/CR aileleri). Limit girişi X (KT-01 A3). Erken giriş X (A1). Çıkış sonrası tutma / kısa X (A5/H1).
  Süre tavanı 3/5/8 komşuluğu ≈ aynı (NX B ızgarası) → yeniden denenmez.
- 16:00 girişi C+ (KT-01 A2, NX-03): +9 bp/işlem. Bağımsız dönem yok.
- Kademeli ekleme C+ (A4): birim kalitesi iyi, Sharpe düşüyor (A4, KD-08).
- **z5 derinlik (KD-02):** z5 ≤ −1,072 → +111,5 vs +26,2 bp; boyut 1,5/0,5 → NAS100 Sharpe 1,46 → 1,65, düşüş −798 → −597; broker 4/5. **A− / boyut B.**
- **Stres (KS-01b):** VIX ≥ 18,4 → C3b ↑, B. Süzgeç olarak portföy Sharpe'ını artırmıyor (E110).
- **KD-09 (sonradan, C):** z5 × stres 2×2: stres∧derin 158 / stres∧sığ 15 / sakin∧derin 35 / sakin∧sığ 40 bp (keşif); broker 92/28/15/17,
  ABD < 2018 52/11/5/6, yabancı 13/−4/−6/−13. "Ön kayıt gerekli" denmişti → **bu çalışma o ön kayıttır.** Ortalamalar görüldü; portföy düzeyinde Calmar /
  Sharpe dozu hiç ölçülmedi. Taze veri: aşağıdaki I1 seti C3b için hiç kullanılmadı.
- OPEX haftası yarım lot canlı (B−). Ters VIX eğrisi dozu C+ (DB-01).
- Bu oturumda (ön kayıttan önce) Duka 132 işlemin betimleyici otopsisi yapıldı: `src/otopsi.py`. Görülen: VIX ≥ 18,4 ∧ derin n 40 +162 bp
  (toplamın %72'si), diğer üç hücre +17…+37; zirveye %4'ten yakın işlemler +8 bp; ≥ 3 gün tutulanlar ort. eksi. **Bu, KD-09'un yeniden üretimidir;
  eşikler (18,4 ve −1,072) önceki çalışmalardan sabittir, burada ayarlanmaz.**

## Veri
- **Ana:** Dukascopy NDX 1m 2018-01 → 2026-11 (`ndx_10y_1m_20261116/src/lib.py`). Kural `rules.c3b` ile birebir (n 132 / +68,1 bp yeniden üretilmeli).
  Canlı lot 2,0, OPEX haftası 1,0. Kitap gün sonu 1m kapanışıyla işaretlenir (`korku_sepeti_20261123/src/kitap.Marker`).
- **Broker (görüldü):** MT5 M30 NAS100, US500, US30, US2000, GER40 2018-05 → 2026-11 (`kt02_derinlik_20261111/kd_ortak.broker_panel`, KT-01 maliyet modeli).
- **Günlük, görüldü:** ABD 4 endeks (NDX, GSPC, DJI, RUT) 2018-05 öncesi; 17 yabancı endeks (`kd_ortak.KOR17`). Kapanış vekili, −3 bp − 2 bp/gün.
- **I1 — TAZE (C3b için hiç kullanılmadı):** `korku_evren_20261119/data/` 38 ABD aracı (QQQ, SPY, RSP, MDY, 20 sektör/sanayi ETF'i, 17 büyük hisse),
  günlük 1993/1998 → 2026-11. Aynı kapanış vekili ve maliyet. QQQ ve SPY NDX/GSPC'ye çok yakındır; havuzda yer alır ama ayrıca "QQQ/SPY hariç" de raporlanır.
- **Stres tanımı:** ABD araçlarında dünkü VIX ≥ 18,4 (`geri_cekilme_20261106/data/VIX.csv`, Duka'da `lib.vix_prev_map`). Yabancı endekslerde RV20 > kendi
  252 günlük medyanı (KS-01b tanımı). **z5** = (S_d / S_{d−5} − 1) / (dvol·√5), dvol = son 20 günlük getirinin std'si, d−1'e kadar (`kd_ortak._multi`).

## Adaylar (7; eşik ve ağırlıklar sabit)
VD = stres ∧ z5 ≤ −1,072 (giriş günü bilgisiyle).

**Bakış 1 — boyut (doz).** Çıkış ve giriş aynı; yalnız lot oranı değişir:
- **D1:** VD → 1 birim, diğerleri → 1/3 birim.
- **D2:** birim = 0,25 + 0,375·[stres] + 0,375·[derin] → 0,25 / 0,625 / 1,0.
- **D3 (süzgeç):** yalnız VD işlemleri; diğerleri açılmaz. E110 uyarısı gereği aday olarak alınır, beklenti düşüktür.

**Bakış 2 — çıkış (zararlıyı zarar ettirmeden kapatmak):**
- **X1:** VD dışındaki işlemler C3 çıkışıyla (ertesi 15:30) kapanır; VD işlemleri C3b çıkışıyla. Zayıf işlemin maruziyetini kısaltır.
- **X2 (başabaş çıkışı):** yükseliş günü çıkışı ancak S_t ≥ giriş fiyatıysa yapılır; değilse en çok 5 güne kadar beklenir (süre sonu yine çıkış).

**Bakış 3 — birleşim:**
- **K1:** D1 + 16:00 girişi (çıkış yine 15:30 fiyatında; NX-03).
- **K2:** D2 + 16:00 girişi.

**Kontroller:** taban C3b (canlı OPEX yarım lot dahil, bütün adaylarda OPEX çarpanı aynen uygulanır). K = tekdüze ölçek (Calmar tanım gereği aynı).
**Plasebo (G5):** D1'in ağırlık şeması, VD etiketi yıl içinde rastgele karıştırılarak (aynı sayıda ağır işlem) 2.000 kez uygulanır. Gerçek Calmar
kazancı plasebo dağılımının yüzde kaçını aşıyor.

## Ölçüler
Calmar, aylık Sharpe (2018-01 → 2026-11, boş ay 0), toplam, maks. düşüş, en kötü gün, en kötü 10 gün, eşit düşüşte zarar toplamı ve kâr toplamı, yıl yıl.
Aday − taban aylık Sharpe farkı için aylık eşli bootstrap P (4.000). Günlük ve broker setlerinde P&L çıkış gününe yazılır (gerçekleşen).

## Geçme ölçütü ("%40 iyileşme kanıtı")
- **G1:** Duka NDX işaretli kitapta Calmar ≥ 1,40 × taban **ve** Sharpe ≥ taban.
- **G2:** ESKİ (≤ 2021-10-31) ve YENİ yarılarda ayrı ayrı Calmar ≥ 1,20 × taban ve Sharpe ≥ taban.
- **G3:** MT5 NAS100 broker kitabında Calmar ≥ 1,20 × taban.
- **G4 (taze):** I1'de araç başına aylık Sharpe artışı ≥ %70 araçta; eşit ağırlıklı I1 havuz kitabında Sharpe farkı P ≥ 0,95 ve Calmar ≥ 1,20 × taban.
  "QQQ/SPY hariç" de aynı yönde olmalı.
- **G5:** Duka Calmar kazancı plasebonun %95'inden büyük (yalnız D-ailesi ve K-ailesi için; X'lerde plasebo = aynı sayıda rastgele işlemde aynı çıkış).
- **G6 (görülmüş bağımsız):** ABD < 2018 dört endeks + 17 yabancı + diğer dört broker setinin ≥ %70'inde Sharpe artışı.
- **A:** G1…G6. **B:** G1 + G2 + G3 + G4 (G5 veya G6 eksik). **C:** G1 + (G2 veya G4). **X:** diğerleri.
- Birden çok aday A/B ise öneri: en az değişiklik (D → X → K sırası), eşitlikte daha yüksek G4 havuz Sharpe'ı.
- A/B çıkarsa: 2. KURAL kartı, canlı kitapta (8 kural, `korku_sepeti_20261123`) etki, ve canlı lot önerisi (eşit C3b maks. düşüşte VD lotu / diğer lot).
  **Canlıya bağlama kullanıcı kararıdır; bu görevde canlı koda dokunulmaz.**

## Sızıntı ve tuzaklar
- VD, z5, dvol ve VIX karar anına kadarki bilgiyle (VIX dünkü kapanış). Lot işlem sonucundan bağımsızdır.
- X2'de "S_t ≥ giriş" karar anında bilinir (S_t 15:30 öncesi son bar kapanışı).
- Sonuç görüldükten sonra yeni aday veya eşik eklenirse EK-n olarak işaretlenir ve hüküm değiştirmez.
- Calmar tek bir düşüşe bağlıdır; bu yüzden yarılar, broker, taze set ve plasebo zorunludur.

---

## TUR 1 sonucu (kısa; ayrıntı RAPOR.md)
Yedi adayın yedisi X. K2 Duka Calmar ×1,398 (G1 çıtası 1,40, iki binde biri altında; yuvarlanmadı), G2 ✓, G3 ✓, G5 ✓; **G4 ✗**: taze 38 araçta
Sharpe artışı %44–51, havuz Sharpe ×0,89–0,95, QQQ 1999–2026'da D1 Sharpe 0,99 → 0,93. Doz 2018–26 NDX'ine özgü görünüyor.

## TUR 2 — ön kayıt (2026-11-24, TUR 1 sonuçlarından SONRA, TUR 2 sonuçlarından ÖNCE)
Gerekçe: TUR 1'de zarar kaynağı dozla değil, çöküşün sürmesiyle ilgili. Projede çöküş sürmesine karşı tek doğrulanmış koruma CAPREV KQ-03'ün
"VIX +%10 → çık" kuralıdır (NDX B, canlı). C3b'de hiç denenmedi. Sızıntısız seans ayrıştırması (`src/ayristir.py`): tutuşun gece ve gün içi dilimleri
ikisi de artı; tek zayıf dilim 15:30 → 16:00 (−11 bp) = bilinen NX-03.
- **V1 (VIX koruması):** pozisyon açıkken k. günün 15:30 kararında dünkü VIX kapanışı ≥ 1,10 × girişteki "dünkü VIX" ise çık (yükseliş/süre kuralına ek).
  Eşik KQ-03'ten sabit, ayarlanmaz.
- **E16:** yalnız 16:00 girişi (NX-03 C+; %40 çıtasına karşı ölçülür).
- **V1K2:** K2 (D2 dozu + 16:00) + V1.
Ölçüt TUR 1'in G1…G6'sının aynısı. Plasebo: V1 için aynı sayıda çıkışın rastgele günlerde yapılması (yıl içi, aynı tutuş günü dağılımı) 500 kez.
Taze set uyarısı: I1 TUR 1'de doz için kullanıldı; V1 hipotezi için ilk kez kullanılıyor (yarı taze). Günlük setlerde VIX dünkü kapanış, karar kapanışta.
Deneme sayacı: TUR 1 7 + TUR 2 3 = 10 aday.

## TUR 2 sonucu (kısa)
V1 her sette kötü (Duka Calmar ×0,94, Sharpe 1,50 → 1,38; I1 havuz ×0,66) → X. E16 Duka ×1,30 / Sharpe 1,61 (P 0,96), yarılar ×1,49 / ×1,28, MT5 ×1,56,
diğer broker ×0,88 → G1 ✗ → X (bilinen C+ ile tutarlı). V1K2 X. 10 adayın 10'u X.

## TUR 3 — ön kayıt (2026-11-24, TUR 2'den SONRA, TUR 3 sonuçlarından ÖNCE)
Açı: çıkış günü zamanlaması. Defterde "1 gün daha tut" (ertesi 15:30) X (KT-01 A5), ama yalnız çıkış gecesini tutmak (ertesi 09:30) ya da 16:00 kapanışında
çıkmak denenmedi. Mekanizma: KSG'nin C3b gecelerindeki +23,9 bp'si (KT-01 H3) çıkış gecesine taşınabilir mi?
- **Y1:** çıkış kararı 15:30'da aynen, çıkış 16:00 kapanışında (son 1m kapanışı).
- **Y2:** çıkış kararı aynen, çıkış ertesi işlem günü 09:30 açılışında (çıkış gecesini tutar). Ertesi gün yeni sinyal ancak 15:30'da doğar, çakışma yok.
- **Y3:** E16 + Y2.
Günlük setlerde Y1 = taban (kapanış), Y2 = ertesi açılış (Open). Broker'da 16:00 / ertesi 09:30 barları. Ölçüt aynı (G1…G6). Deneme sayacı 13.
**Uyarı:** KSG canlıdır ve bu gecelerin çoğunda zaten açık; kitap düzeyindeki etki ayrıca betimlenir (aynı bahis riski).
