# XG — korku gecesi + XP: kârı koruyup zararı en az yarıya indirmek

Ön kayıt: 2026-11-19. Kullanıcı hedefi: kâr artsın ya da en az aynı kalsın, zarar en az yarıya insin.
Veri `results/islemler.parquet` (`src/veri.py`): K1 + XP işlemleri; giriş anı (16:00) özellikleri yalnız o anda bilinen bilgiden;
işlem sonrası yol. KEŞİF ≤ 2021-10-31, TEST 2021-11 →. Beslemeler: Duka NDX, MT5 NAS100, kör MT5 US500/US30/US2000.

## KEŞİF'te görülen (yalnız ≤ 2021-10)
- Anatomi: 1 günde çıkanlar +165 bp, 3/4/5 günde −166/−254/−602; kaybedenler 04:00'te −56, 09:30'da −92.
- Yol tabanlı çıkışlar (tutuş tavanı 1/2/3 gün, 09:30 ≤ −100 bp stop, 04:00 ≤ −75 bp stop) **tüm piyasalarda zararı artırdı** → elendi.
- Giriş vetoları (eşikler KEŞİF'ten, piyasa başına, `results/esikler_kesif.json`; NDX: son saat > −25,6 bp, VIX < 17,37):
  V_saat = son saat düşüşü hafif (piyasanın KEŞİF %80'liği üstü); V_vix = dünkü VIX piyasanın KEŞİF %20'liği altı;
  V_olay = CPI/NFP/FOMC/JH günü; V_opex = OPEX'e 0–2 işlem günü. Dördünün mekanizması defterde önceden var (K3, VIXREG, ZA-04, SV-01).

## Dondurulan 4 paket (TEST'e bakılmadan)
P1 V_saat · P2 V_saat + V_olay · P3 V_saat + V_vix + V_olay · P4 V_saat + V_vix + V_olay + V_opex.

## Başarı ölçütü (TEST)
Hedef: **kâr× ≥ 1,00 ve brüt zarar× ≤ 0,50** (taban = aynı dönem K1 + XP) hem Duka NDX hem MT5 NAS100'de; kör US500/US30/US2000'in
≥ 2/3'ünde kâr× ≥ 0,90 ve zarar× ≤ 0,60. Ek ölçüler: en kötü %10 ort., en büyük düşüş, en kötü işlem, işlem sayısı.
Hedefi geçen paket yoksa: en iyi risk takası raporlanır, "hedef tutmadı" denir.

## TEST sonucu (paketler)
P1–P4 zararı ×0,39–0,81 azalttı ama kârı da ×0,44–0,80 düşürdü (Duka/MT5/kör üç piyasa) → **hedef tutmadı**; vetolanan TEST
işlemleri ortalamada kârlı (vetolar fiilen lot küçültme gibi davranıyor).

## EK-1 (2026-11-19) — seri/eğri kuralları ve çok özellikli sınıflandırıcı
(a) Seri: önceki tamamlanmış K1 işlemi zararla kapandıysa sonraki işlem ½ lot (S1) / atla (S2); eğri freni: son 3 işlemin toplamı < 0
ise ½ lot (S3). (b) Sınıflandırıcı: lojistik regresyon (standartlaştırılmış 32 özellik, L2) ve sığ gradyan artırma (derinlik 2,
100 ağaç), hedef = işlem zararla kapanır; eğitim yalnız KEŞİF (dört ayrı piyasa havuzu), TEST'te tahmin edilen zarar olasılığının en
yüksek %20'si veto (eşik KEŞİF'in %80'liği). Ayrıca olasılığa göre lot: ½ (en riskli üçte bir) / 1 / 1,5 (en güvenli üçte bir).
Ölçüt aynı: TEST'te kâr× ≥ 1,00 ve zarar× ≤ 0,50 (Duka + MT5 NAS100), kör ≥ 2/3.

## EK-1 sonucu
Seri/eğri kuralları kâr ×0,55–0,96, zarar ×0,68–0,99; sınıflandırıcı TEST AUC 0,50–0,62 (kaybeden giriş anında tanınmıyor) → X.

## EK-2 (2026-11-19) — korumalı korku gecesi (NASDAQ al + başka ABD endeksi sat)
Kayıpların büyüğü piyasanın toptan düştüğü gecelerden; NDX'in korku toparlanması diğer endekslerden güçlü (K1 ort. NDX +50…+55,
US500 +27, US30 +33, US2000 +33). Kural: MT5 NAS100 K1 + XP işleminin giriş/çıkış anlarında karşı bacak H ∈ {US500, US30, US2000}
SAT, nominal oran h ∈ {0,5; 1,0} ve nedensel beta (önceki 60 günün günlük getiri betası). Maliyet: iki bacağın spread'i, uzun finansman,
kısa bacak için −0,5 bp/gün. **Ölçek:** korumalı paketin KEŞİF toplamı tabanın KEŞİF toplamına eşit olacak katsayı (KEŞİF'ten
dondurulur). Geçme: TEST'te ölçekli paket kâr× ≥ 1,00 ve zarar× ≤ 0,50 (en az bir karşı bacak; tercihen hepsi aynı yönde), ayrıca en kötü
%10 ve en büyük düşüş. US500 MT5 verisi 2020 öncesi seyrek → US500 bacağı yalnız 2020+.

## EK-2 sonucu
Korumalı paket X: h 0,5 korelasyon 0,87–0,98 (koruma etkisiz), h 1,0/beta kazancın çoğunu siler, ölçekle kâr korununca zarar ×1,6–3,6.

## EK-3 (2026-11-19) — teyitli kademeli giriş
16:00'da f0 lot (0,33 / 0,50), kontrol noktasında (04:00 / ertesi 09:30 / ertesi 12:00) pozisyon > +e bp (e ∈ {0, 25}) ise ek fa lot
(0,5 / 1,0 / 1,5). Ek bacağın getirisi = çıkış − kontrol noktası değeri − 1 bp ek spread (çıkış XP ile aynı). Kontrol noktası çıkıştan
önce olmalı. Seçim yalnız KEŞİF (dört ayrı piyasa havuzu, Duka NDX dahil): kâr× ≥ 1,00 iken zarar×'ı en küçük yapan hücre; ayrıca
"en az zarar× ≤ 0,50 ile en yüksek kâr×" hücresi. İkisi de dondurulup TEST'te (Duka NDX, MT5 NAS100, kör US500/US30/US2000) ölçülür.
Geçme: TEST'te kâr× ≥ 1,00 ve zarar× ≤ 0,50 (Duka + MT5), kör ≥ 2/3'te kâr× ≥ 0,90, zarar× ≤ 0,60.

## EK-3 sonucu
Kademeli giriş kâr ve zararı aynı oranda küçültüyor (B hücresi: zarar ×0,45–0,52, kâr ×0,40–0,44); A hücresi NDX TEST kâr ×1,09–1,14,
zarar ×0,89–0,97, kör US30 kâr ×0,49 → hedef tutmadı.

## EK-4 (2026-11-19) — derin felaket stopu XP tutuşunda
İşlem yolunun en düşüğü (mae) ≤ −S ise çıkış −S − 5 bp kayma; S ∈ {200, 250, 300, 400, 500, 600} bp. Ayrıca stop ∧ 4'lü veto (P4) ve
stop ∧ kademe A. S KEŞİF'te seçilir (kâr× ≥ 1,0 iken zarar×'ı en küçük; dört piyasa ortalaması), TEST'te aynı ölçüt.

## EK-4 sonucu
Derin felaket stopu (−200…−600 bp) her piyasada ve iki dönemde zararı ×1,2–2,0 artırdı (kesilen işlemlerin çoğu sonradan kazanana
dönüyordu). Stop + 4'lü veto: zarar ×0,29–0,44 ama kâr ×0,27–0,61 → hedef yine tutmadı.

## EK-5 (2026-11-19) — işlem başı oynaklığa göre lot (risk eşitleme)
Lot w = c / rv20 (giriş günü, nedensel), w tavan 2,0 taban 0,25; ayrıca w = c / VIX ve w = c / max(rv20, VIX). c her piyasada KEŞİF toplam
kârını tabana eşitleyecek şekilde KEŞİF'ten dondurulur. Ölçüt aynı: TEST'te kâr× ≥ 1,00 ve zarar× ≤ 0,50 (Duka + MT5), kör ≥ 2/3.

## EK-5 sonucu
Oynaklığa göre lot (1/rv20, 1/VIX, 1/max) KEŞİF'te kârı tabana eşitleyince zarar ×0,98–1,71; TEST'te zarar ×1,07–1,97 → X
(korku gecesinin kazancı yüksek oynaklık günlerinde; lotu orada küçültüp sakin günde büyütmek zararı artırıyor).

## EK-6 (2026-11-19) — birleşim + lot ölçeği (oran hedefi)
Hedefin matematiği: TEST'te kâr×/zarar× ≥ 2 olan bir yapı, lotla ölçeklenince kâr ×1 / zarar ×0,5 verir. Kayıtlarda bu orana yaklaşan
tek birleşim S400 + P4 (TEST'te görüldü → seçimi TEST'e bakarak yapılmış sayılır). Dürüst sınama: lot çarpanı L = 1 / (KEŞİF kâr×),
piyasa başına KEŞİF'ten dondurulur; TEST'te L × (S400 + P4) uygulanır. Geçme: Duka + MT5 kâr× ≥ 1,0 ve zarar× ≤ 0,5; kör ≥ 2/3.
Not: seçim TEST'i gördükten sonra yapıldığı için geçse bile en fazla C+ (ileri gölge gerekir).

## EK-6 sonucu
KEŞİF'ten dondurulan lot (Duka ×1,39, MT5 ×1,22) ile TEST: Duka kâr ×0,81 / zarar ×0,40 / kötü10 ×0,52 / DD ×0,52; MT5 kâr ×0,75 /
zarar ×0,38 / DD ×0,44. Kör US500/US30/US2000 kâr×/zarar× oranı 0,84–1,11 (iyileşme yok). → Hedefe en yakın sonuç ama kâr %19–25 eksik
ve kör piyasalarda tutmuyor: C (NDX'e özgü, ileri gölge gerekir).
