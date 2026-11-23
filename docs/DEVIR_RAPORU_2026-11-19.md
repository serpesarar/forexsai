# Devir raporu — NASDAQ kapı araştırması ve "korku gecesi" geliştirmesi (2026-11-19)

> **Yeni Claude Code oturumu için:** önce bu dosyayı, sonra `CLAUDE.md` + `docs/KAPI_KAYIT_DEFTERI.md` (§0, §1, §2.65–§2.99, §3-36…50)
> oku. Burada 2026-11-17 → 2026-11-19 arasındaki tek uzun oturumun tüm bulguları, açık işleri ve devam planı var. Sayılar commit'li
> sonuç dosyalarından alındı. Kaynak yolu her bölümde yazıyor. Okunur sayfa sürümü: `https://claude.ai/artifact/HN4B8uyVzqy39amWobV8rq`.
> **2026-11-23 güncellemesi:** §6 bugünkü duruma göre yeniden yazıldı; rapordan sonra başka oturumlarda canlıya alınan işler orada.

---

## 1. Tek paragrafta durum

- **Ana bulgu: "korku gecesi" (K1).** NASDAQ gün içinde TWAP'ın en az %0,5 altına düşüp son saatte de düşüşle kapanırsa 16:00 NY'de uzun girilir. 2018–2026'da 9/9 yıl artı; kör US500/US30/US2000'de de artı; günlük vekille 1993–2017'de de sağlam.
- **En iyi paket:** K1 + OPEX vetosu + XP çıkışı.
  - Duka NDX: yılda 24 işlem, isabet %83, işlem başı +103 bp. MT5 NAS100: %80, +96 bp.
  - En kötü işlem −783/−786 bp; maks düşüş −801/−814 bp.
  - **2026-11-19 sonunda canlıya alındı** (kullanıcı kararı): eşik −%0,3 (T30), 0,75 lot, `yeni deneme/korku_live.py`, magic +16, kart `ndx_korku_t30_paket` 6/6. Bu tablodaki sayılar −%0,5 eşiğine ait; T30: Duka n 324, %77, +74 bp.
- **Son gün:** kullanıcının hedefi "kâr aynı kalsın, zarar en az yarıya insin" idi. 10 yol + destek limiti + 117 özellikli kaybeden analizi denendi; ön kayıtlı hiçbir kural bunu kör dönemde sağlamadı.
- **En yakın aday:** 1 sa kanal dibi ∪ GBM vetosu. TEST'te kâr ×0,956, zarar ×0,46. Ama sonradan kuruldu, yani ileri gölge sınaması gerekiyor (backlog `bl_00fc2245ad`).

---

## 2. Canlıda çalışan kurallar (bu oturumda değiştirilmedi)

Kaynak `docs/KURAL_LOT_SEVIYELERI.md` + `yeni deneme/kural_katalogu.py`. Kutudaki gerçek durumu `python3 scripts/remote.py health` ve
`remote.py sh "type remote_agent\\agent_state.json"` ile doğrula. Bu oturum kutuya hiçbir şey göndermedi.

| Kural | Magic | Lot | Geçmiş | Sınıf |
|---|---|---|---|---|
| C3b NDX RSI2 geri dönüşü | +8 | 2.0 | %78, +65 bp | A |
| CAPREV kapitülasyon alımı (NDX+DAX) | +7 | 1.0 | +0,22R | B+ |
| ORB × VIX (VIX ≥ 18,4, TP 3R) | +9 | 0.75 | +0,199R | B |
| FR-15 teyitli çekiç (NAS100+GER40) | +10 | 0.5 | ≈ +0,07R | B |
| KSG kapanış saati gecesi | +11 | 0.5 | +7 bp/gece | C+ |
| AY SONU son seans (NAS100+US500) | +12 | 1.0 | +38/+44 bp | B |
| AY BAŞI uzun | +13 | 0.75 | +56 bp | B |
| XAU 1h yeni tepe (R0B_G1+S2) | +14 | 0.05 | +0,109R | B+ |
| VIXREG-FX (16 FX çifti) | +15 | 0.01 | kart 6/6 | — |

Bu oturumun bulgularından biri olan **KSG OPEX vetosu (B)** 2026-11-20'de canlı KSG kuralına eklendi (`824922d3`, GX-06). Korku gecesi de artık canlı (+16, 0,75 lot); güncel tablo `docs/KURAL_LOT_SEVIYELERI.md`.

---

## 3. Kapı karnesi — onaylanabilir kapılar aynı düzenekte (§2.95, `research/son_rapor_20261118/`)

Düzenek: Dukascopy NDX 1m + MT5 NAS100 M30, 2018-04 → 2026-11, aynı maliyet ve finansman, 11/11 birim testi. Sayfa: claude.ai
artifact `CsNW68azHXJwRPLPwcLKx1` (kapı karnesi). Komut: `cd research/son_rapor_20261118/src && python rapor.py kos`.

| # | Kapı (Duka NDX 2018–26) | İşlem/yıl | İsabet | Ort bp | En kötü %10 | Maks düşüş | Yıl | Hüküm |
|---|---|---|---|---|---|---|---|---|
| 00 | Taban: korku gecesi K1 (16:00 → ertesi 16:00) | 29,6 | %60 | +54,7 | −251 | −841 | 9/9 | taban |
| 01 | + OPEX korku vetosu (vadeye 0–2 işlem günü kala açma) | 24,3 | %65 | +70,0 | −254 | −745 | 9/9 | **onay (B)** |
| 02 | + XP çıkışı (ilk yükselen 16:00 kapanışı, en çok 5 gün) | 29,6 | %79 | +84,6 | −304 | −1.106 | 9/9 | **onay (B)**; US2000'de riskli |
| 03 | **Önerilen paket: K1 + OPEX vetosu + XP** | 24,3 | **%83** | **+103,1** | −285 | −801 | 9/9 | **önerilen** (MT5: %80, +95,6, −814) |
| 04 | Korku ertesi seansı (09:30→16:00, gece yok) | 29,5 | %61 | +37,0 | −220 | −623 | 9/9 | onay (B, kart 6/6) |
| 05 | Art arda korku dozu ×1,5 | 29,6 | %60 | +64,8 | −279 | −905 | 9/9 | onay (kör 3/3) |
| 06 | Olay günü vetosu (takvim düzeltmesiyle, E148) | 24,9 | %62 | +59,8 (eski +61,1) | −257 | −841 | 9/9 | koşullu: NASDAQ'ta zayıf (P 0,87), kör 3/3 güçlü |
| 07 | Vade sonrası 3–7. gün dozu ×1,5 | 29,6 | %60 | +63,7 | −282 | −786 | 9/9 | zayıf (B−) |
| 08 | Korku ∧ ters VIX eğrisi dozu ×1,5 | 29,6 | %60 | +68,8 | −296 | −1.147 | 9/9 | onay (+173 vs +32, kör 3/3) |
| 09 | Korku ∧ C3b aynı gün dozu ×1,5 | 29,6 | %60 | +65,2 | −284 | −1.199 | 9/9 | zayıf (tekrar etmedi) |
| 10 | K3 son saat korkusu (son saat ≤ −%0,3) | 37,6 | %60 | +38,7 | −277 | −1.260 | 9/9 | onay (B) |
| 11 | Geniş fitilli KSG (2 sa fitil, 15:30 → ertesi 16:00) | 25,5 | %63 | +49,9 | −289 | −1.153 | 9/9 | onay (B); US2000 maksDD −3.536 |
| 12 | Referans fitilli KSG | 21,5 | %63 | +27,6 | −212 | −687 | 8/9 | onay (NASDAQ) |
| 13 | KSG OPEX vetosu (canlı KSG'ye) | 85,3 | %58 | +11,0 (taban +9,5) | −151 | −971 | 7/9 | **onay (B, 6/6 besleme)** |
| 14 | C3b + OPEX vetosu (taban C3b +68,1) | 12,9 | %80 | +83,1 | −249 | −796 | 9/9 | onay |
| 15 | NDX korkusu → Avrupa (DAX+CAC+STOXX) | 78,2 | %55 | +14,8 | −190 | −3.184 | 5/9 | zayıf |

**Gölge kartları (2. KURAL, `backend/data/evolution/go_live_cards/`, hepsi SHADOW):**
`ndx_opex_korku_vetosu`, `ndx_ksg_opex_vetosu`, `ndx_vade_sonrasi_korku_dozu`, `ndx_korku_twap`, `ndx_korku_sonsaat`,
`ndx_korku_ertesi_seans`, `ndx_korku_birlesik`, `ndx_vix_ters_egri_5g`, `ndx_ksg_fitil`, `ndx_ksg_fitil_genis`.
`ndx_vw_w1b_vix` = RED.

---

## 4. Bu oturumda bulunan diğer stratejiler (defter §2.65–§2.94)

Sınıflar: A/B = kanıtlı · C+ = gölge adayı · C = iz · X = yok. Ayrıntı ve kanıt dosyası her satırın § numarasında.

### B ve üstü (kullanılabilir)
- **Korku gecesi K1 / K3** (§2.71): 16:00 → ertesi 16:00. K1 +53 bp, K3 +36 bp. Kör test + 3 besleme, fitilden bağımsız, 9/9 yıl.
- **K1'in ABD endekslerine taşınması** (§2.72): US30/US2000/US500 +23…+31 bp, iki dönem artı. B+.
- **XP çıkışı** (§2.77): ilk yükselen kapanışta çık. Isabet %60 → %77; Sharpe artışı ılımlı. B.
- **Korku ertesi seansı tek başına** (§2.80): 09:30 → 16:00. Kart 6/6, B.
- **Art arda korku dozu ve olay günü vetosu** (§2.82): bağımsız dönemde B'ye yükseldi.
- **Korku gecesi 1993–2017** (§2.82): günlük vekille 23/24 dönem artı; aile ayı çağlarında da sağlam.
- **OPEX Çar/Per korku alımı vetosu** (§2.91): 1985–99 ^NDX −240 bp, gün içi 5/5 besleme eksi, kart 5/6. B.
- **Vade sonrası 3.–7. gün korku dozu** (§2.93): +0,105z, P 0,9986. B−. Etki ABD vadesine özgü.
- **KSG OPEX vetosu** (§2.94): bağımsız 6/6 besleme, havuz P 1,00, kart 6/6. B.
- **Geniş fitilli KSG** (§2.70): +41,1 vs −0,6 bp, kart 6/6, 9/9 yıl. B. Referans fitilli KSG da B.
- **Korku ∧ ters VIX eğrisi / korku ∧ C3b doz artırıcıları** (§2.75): B. C3b dozu karnede tekrar etmedi → zayıf.
- **Pazartesi 03:00 → Salı 03:00 uzun** (§2.62): kart 6/6, +22,7 bp, gün plasebosu P 0,999.

### C+ (gölge adayı)
- **Ters VIX eğrisi → 5 gün AL** (§2.74): kör +138 bp, ama 37 epizot ve maksDD −%30.
- **Fitilli KSG kesişimi** (§2.68): +28,6 vs +1,9 bp.
- **Habersiz korku / habersiz gün içi ≥ %1 düşüş → ertesi gün** (§2.81): +74 bp; olay gününde −126.
- **NASDAQ korku dışı adaylar** (§2.83):
  - çeyrek OPEX sonrası hafta eksi;
  - olay günü yükselişini SAT;
  - habersiz yükselişi AL;
  - 6 gün seri momentumu sonradan X'e indi.
- **Sabah trendine katılmak** (§2.84).
- **K1 × gece/gün içi çekişmesi** (§2.87): yalnız 2021 sonrası.
- **ORB×VIX OPEX vetosu, Perşembe vetosu, OPEX Çar → Cum SAT** (§2.91).
- **Vade Cuma 09:30 → Pazartesi 09:30 SAT** (§2.92): QQQ 27 yıl.
- **Haftalık korku W2 ve ayıda son saat rallisini SAT** (§2.80): W2 1999–2017'de çöktü → X.

### C (iz)
- 1h fitil + ilk iki 5m yeşil → AL (§2.67).
- Daralan liderlik tepesi (§2.88).
- Fiyat ↑ ∧ VIX ↑ → ertesi gün SAT; korkusuz düşüş AL (§2.89).
- Boğada sert düşüş AL (§2.90).
- Tatil öncesi (§2.94).
- Gece/gün içi çekişmesi; dar liderlik (§2.86).

### X (denendi, tutmadı — tekrar denemeden önce defteri oku)
- **Fiyat yapıları:** 3,5 sa fitil + 15m gövde kuralları (§2.65); V/W dip (§2.66, kart RED); coşku gecesi SAT (§2.73); rejime bağlı vurkaç (§2.76).
- **Korkunun sınırları:** gece seansı korkusu, MOC, genişlik, sepet, ölü kedi (§2.79); korku gecesi küresel değil, Avrupa ve Japonya 0/5.
- **Tuzak tezleri:** algo tuzak tezi ve LETF akışı (§2.84).
- **Mekanik akış:** oynaklık hedefli fon, varyans primi, Hazine ihalesi, BTC hafta sonu (§2.85, §2.87).
- **Dış piyasalar:** mega-cap korelasyonu, yen carry, FOMC çift haftası (§2.88); put/call (§2.89); çapraz varlık şokları (§2.90).
- **Takvim:** OPEX takvim ızgarası (§2.92); Fed put, bilanço sezonu (§2.94).
- **Fibonacci:** ORB × Fibonacci ve makro eklemeleri (§2.69, §2.78).

---

## 5. Korku gecesi geliştirmesi — bu oturumun son bölümü (§2.96–§2.99)

### Strateji tanımı (değişmedi)
- **Sinyal (K1):**
  - 16:00 NY fiyatı ≤ TWAP(09:30–16:00) × (1 − %0,5);
  - ve 15:00 → 16:00 aşağı.
- **Giriş:** 16:00 ask, uzun.
- **Veto:** OPEX'e (ayın 3. Cuması, tatilse önceki gün) 0–2 işlem günü kala açma. Takvim NYSE iş günleriyle ileri uzatılmalı; veriden türetilen takvim gelecek vadeleri bilmez.
- **Çıkış (XP):** sonraki her 16:00'da, kapanış bir önceki 16:00'nın (ilk gün: giriş) üstündeyse çık. En geç 5. işlem günü.
- **Sabit TP/SL yok.**

### Ne denendi, ne çıktı

| ID | Kullanıcı fikri / soru | Sonuç | Hüküm |
|---|---|---|---|
| XL-01 (§2.96) | 16:00'ın 10–200 bp altına limit | Dolanlar iyileşir ama kaçanların %96'sı kazanan → kâr −%14 | X; yarım limit 75 bp risk takası C |
| XG-01 (§2.97) | Kaybeden anatomisi (32 özellik) | 1 günde çıkan +165 bp, 3/4/5 günde çıkan −166/−254/−602; zararın %39'u en kötü 10 işlemde | bilgi |
| XG-02 | Erken çıkış/stop (09:30, 04:00, tutuş tavanı) | Zarar ×1,04–1,44 (kaybedenler sonra toparlanıyor) | X |
| XG-03 | 4'lü veto (OPEX + olay + son saat hafif + VIX düşük) | TEST kâr ×0,44–0,80, zarar ×0,39–0,81; işlem başı +111 vs +78 | hedef X; kalite takası C |
| XG-04 | Lojistik/GBM (eski özellikler) | TEST AUC 0,50–0,62 | X |
| XG-05 | Korumalı (NDX al + diğer endeksleri sat) | Zarar azalmıyor | X |
| XG-06 | Teyitli kademe (½ lot + sabah artıdaysa ekle) | Lot küçültmekle aynı | C |
| XG-07/08 | Felaket stopu / oynaklığa göre lot | Zarar ×1,2–2,0 artıyor | X |
| XG-09 | Veto + −400 bp stop + lot ölçeği | NDX zarar ×0,40 ama kâr ×0,75–0,81; kör piyasada yok | C |
| XG-10 | Zarardayken satma, başabaşı bekle | KEŞİF geçti, TEST çöktü (2022 ayısı, DD ×3) | X |
| XD-01 (§2.98) | Girişi geçmiş haftanın desteklerine limit | TEST 30 hücrenin 29'u piyasanın altında; kaçanlar %89–100 kazanan | X |
| XD-02 | "Destekten tepki" | Gerçek seviye = hayalet seviye (%40–64 dönme); D5 gün dibi zayıf iz | X / C− |
| XK-01 (§2.99) | 117 özellik tek tek (gösterge, uyumsuzluk, tik hacmi, formasyon, S/R, kanal, düşüş yapısı) | Yalnız son yarım saat çoklu test eşiğini geçti, TEST'te X. Uyumsuzluk, formasyon, S/R X. **1 sa kanal dibi (80 sa z, alt %20) vetosu: kâr ×0,99 zarar ×0,57, 4/4 piyasa** | X; kanal C |
| XK-02 | Kümeleme | Kaybeden kümesi yok (%23,7 / %23,6); kaybeden tipleri: 12 çöküş (−295 bp) + 177 sıradan (tanınmıyor) | X |
| XK-03 | 190 ikili kesişim + 4 model | Kesişimler TEST'te çöktü. **GBM: TEST AUC 0,615, Duka 0,632, kâr ×1,005 zarar ×0,72, 5 tohum ve 6/6 yıl kararlı** | kesişim X; GBM C |
| XK-04 | Sağlamlık (sonradan) | Kanal 80 saatte keskin tepe (40/120/200 sa kâr ×0,74–0,97), 1 sa RSI ile ρ 0,72. **Kanal ∪ GBM: 160 veto, kâr ×0,956, zarar ×0,46** | C+ gölge adayı |

**Meta dersler (§3-48, 49, 50):**
- Kaybeden işlem giriş anında tanınmıyor.
- Erken kesmek kazananları da öldürüyor.
- Limit girişi, kazanan bir sinyalde hemen dönen kazananları kaçırıyor.
- Gözle görülen "destekten tepki", kazanan sinyalin yan ürünü.
- "Zarar yarıya, kâr aynı" ancak sıfır beklentili işlemleri eleyen kalite filtreleriyle mümkün. Ölçüt "vetolananlar < 0" değil, "vetolananlar ≈ 0 ve kâr korunuyor" olmalı.

### Araçlar (claude.ai artifact; kullanıcının hesabında, özel)

| Araç | Bağlantı | Ne yapar | Nasıl yeniden kurulur |
|---|---|---|---|
| **İşlem oynatıcı** | `https://claude.ai/artifact/43y1hXyMWfSdYfDWsPtfdt` | 249 K1+XP işlemi gerçek 30 dk mumlarda: giriş, TWAP, 16:00 kontrolleri, dip, çıkış; D5/P5/W8 destek çizgileri ve limit kartı; işlem başına not | `python research/xp_gelistir_20261119/src/replay_veri.py` → `src/oynatici_kur.py` → `korku_gecesi_oynatici.html` |
| **Korku gecesi laboratuvarı** | `https://claude.ai/artifact/YH4gw9soS4p2vSiXNoNQx3` | Vetoları ve çıkışları aç/kapa, önce/sonra eğrileri (token harcamadan) | `research/xp_gelistir_20261119/arac_sablon.html` + `results/arac_veri.json` |
| **Kapı karnesi** | `https://claude.ai/artifact/CsNW68azHXJwRPLPwcLKx1` | 14 kapı tek tabloda | `research/son_rapor_20261118/kapi_karnesi.html` |

Oynatıcının gömülü verisi ham fiyat içerdiği için git dışında. Yalnız şablon ve kurucu betikler commit'li.

---

## 6. Devam planı (yeni oturum buradan başlasın) — 2026-11-23 güncel

**Bu rapordan sonra yapılanlar (başka oturumlar, 2026-11-19 → 11-22):**
- Korku gecesi **T30 paketi canlı**: K1 eşiği −%0,3 + OPEX vetosu + XP, NAS100 0,75 lot, tek pozisyon, acil SL %13. Durdurma ölçütü: canlı n 40'ta ortalama net < 0 (EV-05, §2.101).
- **Kanal ∪ GBM vetosu ileri gölgede** (XK-05, `research/korku_golge_20261119/`). Model `model/gbm_kesif.joblib`, yalnız etiket yazar. Backlog `bl_00fc2245ad` açık. XA-01…04 (§2.100) 570 özellikle aynı sonucu buldu: ayrışma X, veto C.
- **KSG OPEX vetosu canlı** (KZ-05/GX-06) + `ksg_shadow.py` gölgesi.
- **Korku koşullu ekleme gölgede** (KR-03/04, §2.110): D1 16:00 zararı ≥ 50 bp → sanal +1 birim. Emir yok; bedeli maks. düşüş ×1,6.
- **CAPREV:** NDX kâr çıkışı + tutuş koruması + bölünmüş giriş canlı; NDX lotu 0,4 (KQ-08).

**Önerilen sıra.** K1'e yeni filtre arama. Beş tur denendi (XG, XL, XD, XK, XA), hepsi X; kaybeden girişte tanınmıyor (§3-48, §3-50). Aynı veriyle bir tur daha büyük olasılıkla aynı sonucu verir. İlerleme yeni veriden gelir, yani canlı ve gölge işlemlerden.

1. **Korku sepeti risk defteri** — **2026-11-23 yapıldı, sonuç X** (KS-01…04, defter §2.113, `research/korku_sepeti_20261123/RAPOR.md`).
   - **Sonuç:** en kötü 10 günün hepsinde ≥ 2 korku kuralı açık; C3B kârın %36'sı, kuyruğun %57'si. Ama aynı günler en kârlı günler. Aile tavanı ve çakışmada yarım lot kuyruğu ve kârı aynı oranda kesiyor; tekdüze lot küçültmeden farksız (5/5 X). KR-03 kitapta düşüşü büyütmüyor. Kuyruk küçültülmek istenirse araç toplam lot kararıdır.
   - Aşağıdaki gerekçe ve plan kayıt için duruyor.
   - **Neden:** NAS100'de beş canlı kural aynı bahsi yapıyor: endeks korkuyla düştükten sonra AL. Bunlar C3b 2,0 (vade haftası 1,0), KSG 0,5 (VIX ≥ 25'te 1,0), KORKU 0,75, CAPREV 0,4 ve ORB×VIX 0,75. Meta-analizde (§2.35, MA-03; eski bot aileleri, 06-30 → 11-09) en kötü 5 gün toplam net kâra eşitti. Lot tavanı 5 ise en kötü 5 gün −22,0 bin $'dan −7,8 bin $'a iniyor, günlük Sharpe 0,111'den 0,154'e çıkıyordu (örneklem içi, C). Bugünkü tek koruma kaba: sembolde 4,5 lot aşılırsa sonraki kural atlanıyor.
   - **Ne yapılacak:**
     - Her kuralın 2018–26 işlem listesi gün gün üst üste konur. Duka NDX 1m + MT5 NAS100, aynı maliyet; `research/son_rapor_20261118/rapor.py` düzeneği yeniden kullanılır.
     - Ölçülecekler: aynı gün kaç kural birlikte tetikleniyor; en kötü 10 günde toplam açık lot ve zarar; maks. düşüşün ne kadarının çakışma günlerinden geldiği; 4,5 tavanı hangi günlerde hangi kuralı atlatıyor.
     - **Ön kayıtlı adaylar:** (a) bugünkü kural (tavan 4,5, ilk gelen alır); (b) aile toplam tavanı 2,5 / 3,0 / 3,5; (c) eşit risk payı (her kural oynaklığa göre); (d) çakışma gününde ikinci ve sonraki kurala yarım lot.
     - **Geçme ölçütü:** aylık Sharpe ≥ bugünkü ve maks. düşüş ile en kötü 10 gün ≤ bugünkünün %70'i, iki besleme ve iki yarıda.
   - **Çıktı:** aile lot tavanı + paylaşım önerisi + 2. KURAL kartı. Kâr artırmak hedef değil; amaç en kötü günü küçültmek. "Zarar yarıya" hedefinin gerçekçi yolu bu.
   - KR-03 koşullu ekleme (D1'de +1 birim) bu defterin içinde değerlendirilmeli: tam da çakışma günlerinde lot artırır.
2. **İleri gölgeleri izle, yeni karar verme.**
   - Kanal ∪ GBM etiketi ≥ 40 işlemde "vetolananlar ≈ 0 ve kalanlar > taban" ise B'ye yükseltme önerilir.
   - Korku canlı n 40'ta durdurma ölçütüne bakılır.
   - Koşullu ekleme gölgesinin sonucu toplanır. Kararlar kullanıcıda.
3. **Çöküş tipi kaybedenler** (12 işlem, ortalama −295 bp; 20:00'dan sonra kesintisiz düşüş). Önce risk defterine bak: bu günler çoğunlukla çakışma günleriyse çözüm lot tavanıdır, giriş filtresi değil.
4. **Oynatıcıya kanal z ve GBM etiketi ekleme** (isteğe bağlı). Yeni kullanıcı fikri gelince önce defteri kontrol et (3. KURAL).

**Önerilmeyenler:** korku gecesi için yeni gösterge, formasyon ya da destek/direnç fikri (XD, XK ve XA'da X); korkusuz SAT kuralları ("coşku dönmez", birçok kez tekrarlandı).

---

## 7. Dosya haritası

| Klasör | İçerik |
|---|---|
| `research/son_rapor_20261118/` | Kapı karnesi düzeneği: `rapor.py` (takvim, OPEX döngüsü, K1, KSG, C3b, metrikler, 11 test), `genis.py`, `ek_kapilar.py`, `tablo.py` |
| `research/xp_limit_20261118/` | XL-01 limit girişi (`xl.py`: K1 sinyal + XP çıkış simülasyonu, yeniden kullanılır) |
| `research/xp_gelistir_20261119/` | XG-01…10 (`veri.py` → `results/islemler.parquet`: 1.013 işlem × 54 sütun, 5 besleme), lab ve oynatıcı |
| `research/xp_destek_20261119/` | XD-01/02 destek limiti + hayalet seviye (`destek.py`) |
| `research/xp_kaybeden_20261119/` | XK-01…04: `ozellik.py` (117 özellik, MT5 tik hacmi), `analiz.py`, `saglamlik.py` |
| `docs/KAPI_KAYIT_DEFTERI.md` | Tüm denenen kapılar: §2.95–2.99 bu bölüm, §3-48…50 meta dersler |
| `backend/data/evolution/go_live_cards/` | Gölge kartları |

**Veri kaynakları:**
- Dukascopy NDX 1m: `G.ndx_bars()` (`research/son_rapor_20261118/src/rapor.py` → `ox.G`).
- MT5 M30 + tik hacmi: `research/c1_turev_20261105/data/mt5/{NAS100,US500,US30,US2000}_M30.csv.gz`. Saat dönüşümü `kaynak.server_to_utc`.
- VIX: `research/qs03_akis_takvim_20261111/data/VIX.parquet`.
- QQQ: `research/nq_yapi2_20261118/data/QQQ.parquet`.
- Dönemler: KEŞİF ≤ 2021-10-31, TEST 2021-11 →.

---

## 8. Çalışma kuralları ve tuzaklar (bu oturumda öğrenilenler)

- **Ön kayıt:** her araştırmada önce `PROTOCOL.md` yaz (tanım + geçme ölçütü), sonra koş. Sonradan bakılanı `EK-n` olarak işaretle; hüküm değiştirmez.
- **Kontrol:** hayalet seviye/plasebo (E105), aynı yıl tabanı, kör piyasa (US500/US30/US2000) ve ikinci besleme (Duka ↔ MT5).
- **Etiket:** işlemi **giriş tarihine** göre etiketle (E147). Seviye karar anında tek ve belli olmalı (E109). Geçmiş bar için `_bars_upto` kullan.
- **Paylaşılan dosyalar:** `analyses.json`, `KAPI_KAYIT_DEFTERI.md` ve `backlog.json` başka oturumların (Codex dahil) commit edilmemiş satırlarını taşır.
  - Önce oku, sonra **ayrı adımda** yaz. `open(p,'w').write(f(open(p).read()))` dosyayı boşaltır; 2026-11-19'da bu oldu, 3 Codex girdisi `~/.codex/sessions/` kayıtlarından geri kuruldu.
  - Commit'e yalnız kendi satırlarını almak için süzülmüş blob kullan (`git hash-object -w` + `git update-index --cacheinfo`). Defterdeki **§2.69 ve §2.78** blokları başka oturumun, commit'e katma.
- **Ham veri** (`*.parquet`, `data/`, gömülü fiyatlı HTML) commit edilmez.
- **Push:** bu oturumdaki commit'ler yerelde, **push edilmedi**. Araştırma olduğu için kutuya gitmesi gereken bir şey yok. Canlı koda dokunan iş `main`'e push ister (CLAUDE.md).
- **Her oturum sonunda:**
  - `python3 backend/scripts/evolution_session_log.py "özet" --files ...` (1. KURAL);
  - deftere satır (3. KURAL);
  - yeni scope'a canlıya alma kartı (2. KURAL).

**Bu bölümün commit'leri (yeniden eskiye):** `490dbb71` XK · `45bce54c` XD · `1b2faad0`/`4de89b65`/`8093a848` oynatıcı ·
`0b82b2be`…`b525a58b` XG-01…10 · `d3ca0b84` lab · `2be6b23d` XL-01 · `18cf42ed`…`a51e608f` kapı karnesi · `edad197e`…`87f93fca`
§2.65–§2.94.
