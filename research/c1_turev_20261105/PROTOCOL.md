# Ön-kayıt — C1 türevleri ve karşıtları; NDX → XAU → USOIL (TR-01…, 2026-11-05)

Kullanıcı isteği: kenarın mantığından türev + karşıt türev üret, kredi bitene kadar ara. Bu, çoklu sınama riskini büyütür. Önlem:

1. **Her hücre `results/denemeler.csv` defterine yazılır** (silinmez); rapor toplam deneme sayısını söyler.
2. **Üç kademe:** KEŞİF 5m 2024-25 → BAĞIMSIZ 30m 2021-07→2023 ve 1h 2016-06→2021-06 (OR eşlemesi 30/60 dk, aynı filtre+çıkış) → SON 5m 2026.
3. **Aday ölçütü:** keşif n ≥ 40, ort R > 0, P ≥ %95, iki yarı ≥ 0 · bağımsızların ikisi de ort > 0 ve birleşik P ≥ %95 · 2026 ort ≥ 0 (n ≥ 15) · bp > 1 · spread 3,4 pt'de > 0. **C1'den farklı olmalı:** C1 işlemleriyle gün çakışması raporlanır; çakışması ≥ %70 olan hücre "yeni kenar" değil C1 varyantıdır.
4. **Şans kıyası:** keşif eşiğini geçen hücre sayısı, aynı aile için gün etiketleri karıştırılmış filtreyle üretilen sayıyla kıyaslanır.
5. Çıkış/stop hücreleri aynı işlemleri paylaşır (E61): aile başına tek oy.
6. Kart (2. KURAL) hepsini geçene çıkarılır. Canlı/lot kararı kullanıcıda.

## Mantık
C1: korku rejiminde (VIX ≥ 18,4) sabah yukarı kırılım sürer; sakin rejimde sürmez. "Korku döner coşku dönmez" ile aynı aile (CAPREV, K1).
Türevler: rejim ölçüsü (VIX değişimi, VIX/VIX3M, gerçekleşen vol), bağlam (boşluk, önceki gün, ilk bar), aralık uzunluğu, çıkış, geri test, ikinci şans, saat çapaları.
Karşıtlar: kısa kırılım × rejim, kırılımı söndür, başarısız kırılımdan dönüş, sakin rejimde tepe kırılımını satma, stop sonrası ters dönüş.

## EK-1 (2026-11-05) Broker verisi + XAU/USOIL
Kutudan salt okunur MT5: M5 2025-06→, M15 2022-08→, M30 2018-05→ (H1 2016-17 ekseni şüpheli, 2018 öncesi kullanılmaz; sunucu = NY+7 denetlendi: NDX 09:30, XAU 08:30, USOIL 09:00-10:30, GER40 03:00 ET tepeleri her yıl beklenen yerde).
Kademeler (üç sembol, OR30): KEŞİF M15 2022-08→2024 · BAĞIMSIZ M30 2018-05→2022-07 · SON M15 2025→2026-11 · yan M5 2025-06→ OR15.
Spread: NDX 1,3 · XAU 0,25 · USOIL 0,03. Aday ölçütü: keşif n≥40, R>0, P≥%95, yarılar ≥0; bağımsız R>0, P≥%90; son R≥0.
Çapalar: NDX 09:30/10:00; XAU 08:30/09:30/03:00; USOIL 09:00/09:30/03:00.
Rejim: VIX + kendi örtük oynaklığı (GVZ, OVX; önceki 252 gün medyanı üstü, nedensel) + kendi gerçekleşen volü.

## EK-2 (2026-11-05) Günlük + gece aileleri (QQQ 1999→)
Korku mantığı gün-içi dışında: gece tutma, 1 gün, 3 gün; koşullar: VIX kovaları, dün düşüş, kapanış günün dibinde, RSI2<10, 5 gün dibi, ardışık düşüş. Karşıt: coşku (VIX<15, RSI2>90, 5 gün zirvesi) kısa. KEŞİF 2012-2023 · BAĞIMSIZ 1999-2011 · SON 2024-2026. Maliyet: 2 bp + gece başına 2 bp. Ölçüt: aynı çıkışın koşulsuz ortalamasını geçmeli (uzun kayması E13), P ≥ %95, iki yarı + ; bağımsız fark > 0 ; son fark ≥ 0.

## EK-3 (2026-11-05) C3 korku geri dönüşü: broker icrası, üç sembol
QQQ taraması (r3.py) günlük koşullarda güçlü iz verdi; ama aynı gün VIX'ini ve kapanış fiyatını kullanıyordu, gerçek icra değil. Burada: karar anı fiyatı S = giriş barından önceki bar kapanışı (her gün aynı saat), RSI2/5 gün dibi/ardışık düşüş S serisinden; VIX/iv önceki gün; giriş o bar açılışı + spread; çıkış h gün sonra aynı bar açılışı; finansman 2 bp/gece, bid taraf; stop yok (R = 1×20 gün vol; yalnız raporda). Dönemler: k 2022-08→2024, b 2018-05→2022-07, s 2025→. Ölçüt: aynı saat+h koşulsuz tabanı geçer (P ≥ %95), yarılar +, bağımsız fark > 0, son fark ≥ 0. CAPREV ile çakışma raporlanır.

## EK-4 (2026-11-05) C3 detay sınaması
Aday: NAS100, karar 15:30 ET, RSI2(S) < 10 → uzun, ertesi gün aynı saat çıkış, stop yok. Parametre sabit; aşağıdakiler duyarlılık: eşik 5/10/15/20/25, RSI3, saat 15:30/15:45/15:55, çıkış ertesi 09:30 / ertesi aynı saat / ilk yükseliş (≤5 gün), felaket stopu 2×dvol. Permütasyon: yıl içi rastgele gün. Kart: 6 ölçüt. CAPREV çakışması, Cuma girişi, GER40 aktarım. QQQ 1999-2018 bağlam.

## EK-5 (2026-11-05) C3 türevleri (T5) ve C1×C3 (T6), XAU/USOIL dahil
Mantık: kısa vadeli satış aşırılığı ertesi güne geri döner. Türev: IBS, N gün z-skor, VIX aşırılığı (VIX/10g ort, gün içi VIX sıçraması), varlıklar arası tasfiye (NDX+XAU birlikte düşüş, NDX düş∧XAU çık), sıralı düşüş sayısı. Karşıt: coşkuda uzun (RSI2>90, 5g zirve) ve kısa. T6: C3 ertesi günü ORB uzun; C3 tutulurken ORB gelirse kapanışa kadar kal. Aynı k/b/s ölçütleri; XAU/USOIL kendi S serisiyle, tasfiye diğer sembollerin S'iyle.

## EK-6 (2026-11-05) İki iz için görülmemiş dönem + C1×C3
Şans hesabı: üç bağımsız dönemde min P ≥ p olma olasılığı (1−p)³; 1.524 hücrede USOIL 0,883 → beklenen ≈ 2,6, XAU 0,931 → ≈ 0,5, NDX C3 ≈ 4e-7. Bu nedenle: H1 2010-05→2018-05 (M30'a girmemiş, saat ekseni ±1 sa şüpheli ama günlük kural için önemsiz). O1: SpotCrude VIX sıçrama > %10 → kısa h=1 (15:00 bar). X1: XAU RSI2<10 ∧ NAS100 RSI2>50 → uzun h=1 (08:00 bar). Geçer: ort > 0, tabanı geçer P ≥ %90.
T6: C1 ∧ dün C3 sinyali; C3 tutulan gün ORB; C3 çıkış uzatma.

## EK-7 (2026-11-05) O1/X1 X; portföy P1 = C3 + C1'; saat penceresi taraması T7
O1 2010-18 −26,6 bp X. X1 saat değişince işaret dönüyor X.
C1' = C1 ∧ dün C3 sinyali yok (sonuç görülerek türedi: post-hoc). Doğrulama: Dukascopy 5m 2024 ve 1h 2016-21, 30m 2021-23 eski arşivlerde. Geçer: üçünde de C1' > C1∧dün C3.
T7 saat penceresi: başlangıç 0..23 ET × süre 2/4/6/8/12/16 sa × uzun/kısa × tümü/iv yüksek/iv düşük; M30 k/b/s. Üç dönem de + ve min P eşiği, şans hesabı (1−p)³×hücre. Altının gece etkisi bilinen hipotez (önceden yazıldı): Asya/Londra uzun, NY kısa.

## EK-8 (2026-11-05) XAU 18:00 ET sonrası uzun (T7 izi) — sahtelik sınaması
Şüphe: 17:00-18:00 ET bakım/rollover'da spread açılır, BID açılış suni düşük görünür. Sınama: gerçek bar spread'i (M5/M15), giriş gecikmesi 18:00/18:15/18:30/19:00/20:00, çıkış 22:00; maliyet giriş+çıkış gerçek spread, stres ×2. Kutudaki tick kaydı varsa doğrudan ölçüm. Geçer: gecikme 19:00'da da > 0 ve P ≥ %95.

## EK-9 (2026-11-05) XAU 18:00 X (E97); C3 kartı + P1 portföyü + C1' eski veri doğrulaması
Bar spread'i yeniden açılış spread'ini göstermiyor: ilk tick 0,75-0,90$, bar 0,08-0,14$. 18:05+ etki 2025-26 rallisi. Hüküm X.
C3 kartı 6 ölçüt: 15:30 RSI2<10, ertesi 15:30; k/b/s + spread×1,5 + icra (S kapanış girişi vs sonraki açılış) + tek pozisyon. P1: C3 + C1' M30 2018-2026, yıl yıl bp, DD, eşit nominal. C1' 5m 2024-26 Duka, 30m 2021-23, 1h 2016-21 eski arşiv.
Felaket stopu kararı: yok (1×vol −34 bp bedel); risk = pozisyon büyüklüğü.

## EK-10 (2026-11-05) Sonraki aileler
- T8 NDX gün içi RSI2: M5/M15/M30 RSI2<5,<10 ∧ VIX kovası, N bar tut. Ayna RSI2>95 kısa ∧ VIX<15.
- T9 C3 çıkış: ilk yükselen kapanış, ertesi 09:35, ertesi 15:30; giriş aynı.
- T10 Haftalık/aylık ölçek: haftalık RSI2<10, aylık düşüş → 1 hafta uzun.
- T11 XAU/USOIL için kendi mantık: rejim sonrası trend (N gün zirvesi × iv düşük), Donchian kısa vadeli (5/10/20), haftanın günü, ay dönümü, EIA Çarşamba saatleri, CPI/NFP günü pencere.
- T12 Makro sürpriz S1–S8 (arşiv inince, makro.py).

## EK-11 (2026-11-05) C3b ve C4 (r9 izinden; şans: 310 hücrede minP≥.95 beklenen 0,04, gözlenen 5)
C3b: C3 girişi, çıkış ilk yükselen S (≤5 gün). C4: 55 gün dibi (S) → 10 gün uzun. Tek pozisyon, 2 bp/gece. Bağımsız: QQQ kapanış→kapanış 1999→2018, 4 bp + gece. Taban: tüm günlerde aynı süre uzun. C3b için çok önemli: uzun tutmanın kuyruk riski (en kötü, DD, 2000-02 ve 2008).

## EK-12 (2026-11-05) XAU/USOIL günlük izleri bağımsız: GC=F, CL=F 2001→2018 (r9'da hiç kullanılmadı); C3b kesit: SPY, DIA, IWM, EFA.
Önceden liste: XAU 20g zirve uzun h1/h3; 55g zirve uzun h5; 20g dip uzun h5; 10g dip uzun h3; 5g dip uzun h5; ay dönümü uzun; C3b. USOIL 55g zirve uzun h5/h10; 20g zirve uzun h3; 10g dip uzun h5; 5g dip uzun h10; C3b. Geçer: tabanı geçer (ort − süre×gün ort) ve P ≥ %95, iki yarı +, tek pozisyon. Maliyet 3 bp + 2 bp/gece.

## EK-13 (2026-11-05) C3 karşıtı kapı: canlı işlemler (bot_trades)
Hipotez, önceden: RSI2<10 iken NDX SELL kötü, RSI2>90 iken ... kanıt yok. Kapı adayı: "RSI2(son 15:30) < 10 iken NDX SELL açma". Ölçü: 06-29→ tüm NDX bot işlemleri, bp ve $, hücre RSI2 kovası × yön × kaynak, plasebo: yıl içi aynı kova oranlı rastgele gün yok (kısa dönem) → gün-blok P. Sızıntı yok: RSI2 işlem açılışından önceki son 15:30 S'i.
Aynı mantık decider (magic ayrımı) ve VIX≥18,4 kısa.
XAU/USOIL günlük izleri X: GC=F, CL=F 2001-18 fazla ≤ +23 bp P %88,5, C3b ≤ 0 ; C3b endeks etkisi: SPY +39,6, IWM +27,9, EFA +23, DIA +14,9 (bağımsız kesit).

## EK-14 (2026-11-05) Gate_bot X (SELL∧RSI2<10 n=48 −0,7 bp). T13 varlıklar arası şok: hedef QQQ, GC=F, CL=F; sinyal VIX, TNX, DXY, CL, GC, QQQ, SPY/QQQ göreli, IWM/QQQ; günlük değişim z (60 gün, nedensel) ≤ −2, ≤ −1,5, ≥ 1,5, ≥ 2; uzun/kısa, h=1/3. Veri 2001→. KEŞİF 2012-2023 · BAĞIMSIZ 2001-2011 · SON 2024-2026. Kapanıştan gir (S), 3 bp + 2 bp/gece; taban fazlası. minP şans hesabı (E98).

## EK-15 (2026-11-05) T13 izleri için zaman hizası (E99 adayı)
GC=F/CL=F Yahoo kapanışı uzlaşma (13:30/14:30 ET), VIX/TNX/DXY/QQQ kapanışı daha sonra: "ertesi gün" getirisi sinyal gününün öğleden sonrasını içerir, sızıntı. Sınama: broker M30, sinyal D kapanışı, giriş D 18:30 ET (rollover sonrası, E97), çıkış D+h aynı uzlaşma saati XAU 13:30 / USOIL 14:30. Sonuç < QQQ etkisi (NDX zaten 16:00 ortak). Geçer: 3 dönem ort > 0 & taban fazlası > 0; minP ≥ 0,9. Aday: X2 VIX z≤−1,5 uzun; X2b z≤−2; X3 DXY z≥1,5 kısa; X4 QQQ z≤−2 kısa; X5 TNX z≤−2 uzun; O2 SPY/QQQ z≤−2 kısa; O3 DXY z≤−2 kısa; O4 IWM/QQQ z≤−2 kısa.

## EK-16 (2026-11-05) C3b KÖR SINAMA (sonuç görülmeden, kural donduruldu)
Kural: 15:30 ET bar açılışı öncesi kapanış S; günlük S serisi RSI2 (Wilder) < 10 → o açılışta uzun (ask); ilk S_t > S_{t−1} olduğunda o gün aynı bar açılışında çık, en geç 5 işlem günü; tek pozisyon; stop yok; finansman 2 bp/gece; spread sembolün medyan bar spread'i × 1,5.
Kör veri: broker US500, US30, GER40 M30 2018-05→ (C3b bu sembollerde hiç koşulmadı; GER40'ta yalnız C3 görüldü); NDX Dukascopy 1m 2024-01→2026-11 (farklı besleme, 2026-01..02-08 yok); NAS100 H1 2016→2018-05 (M30 öncesi; 15:00 barı).
ÖNCEDEN GEÇME ÖLÇÜTÜ: (a) US500 ve US30'un ikisi de ort > taban×süre, P(fazla) ≥ %90, iki yarı ≥ 0. (b) Dukascopy NDX ort > 0, P ≥ %90, broker ile aynı dönemde fark < 20 bp. (c) Kart hacmi: NDX broker + H1 ≥ 150 işlem, birleşik 6 ölçüt. Biri tutmazsa hüküm düşürülür ve yazılır; parametre değişmez. GER40 yalnız rapor (kesit dışı; önceden zayıf görüldü).
