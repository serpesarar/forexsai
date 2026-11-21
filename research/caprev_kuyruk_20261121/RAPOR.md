# CAPREV kâr çıkışı — kuyruk (çöküş) anatomisi ve tutuş koruması — RAPOR (2026-11-21)

- Ön kayıt `PROTOCOL.md`: KQ-01 (95698082), KQ-02 (6728468d), KQ-03 (8a7c71f4); her biri kendi sonuçlarından önce commit'lendi.
- Kod `src/kq_veri.py`, `src/kq_analiz.py` (KQ-01), `src/kq2_veri.py`, `src/kq2_analiz.py` (KQ-02), `src/kq3_analiz.py` (KQ-03 + kart).
  Sonuçlar `results/analiz.json`, `analiz2.json`, `analiz3.json`. Kart `backend/data/evolution/go_live_cards/caprev_ndx_kar_koruma.json`.
- Tutarlılık: yeni yol motoru CD'nin X_5_3.0_kar'ını ve canlı tabanı birebir veriyor (Duka NDX +105,9 / +47,9; DAX +21,3 / +37,6).

## Soru
Kâr çıkışında (kârlı ilk seans kapanışında çık, en çok D5, felaket stopu 3×dvol) en kötü %5 işlemin ortalaması −250 → −475 bp. Çöküş
olacağı önceden, girişte ya da giriş sonrasında, anlaşılır mı?

## Cevap
| Ne zaman | Çöküşü ayırt ediyor mu | Kanıt |
|---|---|---|
| Girişte | **Zayıf** | en iyi işaret VIX/SMA10, TEST AUC 0,68; KEŞİF'te 0,57'yi geçen yok (CD ile aynı) |
| **D0 kapanışında** | **Evet** | zarar derinliği z0 (çöken −1,1×dvol, dönen −0,5) AUC 0,70; kapanış gün dibinde (clv0) AUC 0,70; üç örneklemde aynı |
| D1 kapanışında | Güçlü ama geç | VIX tırmanışı AUC 0,69–0,82, sekmeme 0,72–0,78; çöküşlerin bir kısmı D1 kapanışından önce stopa gidiyor |

Tutulan işlemler (D0 kapanışında zararda) KEŞİF'te 191 ÇÖKÜŞ / 381 DÖNÜŞ / 40 SÜRÜNME; TEST 2018–26'da 52 / 138 / 11.
Kuyruğun stopları D1–D4'te. Karar anı D0 kapanışı.

## Tur tur
| Tur | Yapı | Hüküm | Düşen ölçüt |
|---|---|---|---|
| KQ-01 | korumasız kâr çıkışı + kapanış koruması (G1–G9, 276 hücre) | C | DAX CVaR5 −520 vs sınır −516 |
| KQ-02 | D0 tutma şartı (z0, clv0) × stop takvimi × s≥1 koruma (216 hücre), NDX + DAX | C | DAX taze beslemesi MT5_GER40 −20,9 bp |
| **KQ-03** | aynı ızgara, **NDX kapsamı**, ABD KEŞİF'inde seçim | **B** + kart **6/6 LIVE** | — |
| (karşılaştırma) korumasız kâr çıkışı, NDX kapsamı | | C | taze NQ'da CVaR5 −578 vs sınır −450 |

## KQ-03 seçilen yapı (ABD KEŞİF'i bağımsız seçimde KQ-02 ile aynı hücreyi buldu)
D0 gün içi stop 3×dvol → D0 kapanışı: kârdaysa çık; zararda ise **yalnız z0 > −0,5 ve kapanış gün dibinde değilse tut**, değilse çık →
tutulursa stop girişin **1,5×dvol** altına → D1…D4 kapanışında kârdaysa çık, **VIX ≥ girişteki dünkü VIX × 1,10** ise çık → en geç D5.

| | Taban (canlı aynı gün) | Korumasız kâr | **Korumalı kâr** |
|---|---|---|---|
| Duka NDX işlem başı | +47,9 | +105,9 | **+63,8** |
| isabet | %57 | %89 | **%70** |
| Sharpe | 0,71 | 1,34 | **0,84** |
| en kötü %5 ort. | −250 | −475 | **−426** |
| MT5 NAS100 | +46,3 / −284 | +111,3 / −461 | +64,1 / −424 |
| taze EET30 (fark / CVaR5) | / −303 | +57,6 / −514 | +15,0 / −463 |
| taze NQ (fark / CVaR5) | / −225 | +40,3 / **−578** | +14,6 / −411 |
| kör US500 / US30 / US2000 fark | | +22 / +21 / +14 | +6,2 / −0,9 / +7,3 |
| günlük 2016–26 NDX/GSPC/DJI/RUT fark | | +42 / +53 / +50 / +26 | +16 / +23 / +21 / +21 |
Havuz P 1,00. Tutuş: 101 işlemin 85'i D0'da kapanıyor (korumasızda 62), 16'sı D1–D3'te.

**Canlıya alma kartı** (ABD aile havuzu: Duka NDX + kör üç, 359 işlem): ort +53,6 bp, P(EV>0) 1,00, yarılar +36,9 / +70,3,
spread ×1,5 +52,8, icra iyimser farkı 1,7 bp (giriş zaten sonraki bar açılışı + gerçek spread), tek pozisyon 165 işlem +47,3 → **6/6 LIVE**.

## Bedel ve dürüst okuma
- Koruma kuyruğu ~%10 daraltıyor (−475 → −426), beklentinin ~%40'ını bırakıyor (+106 → +64). Neden: D0 kapanışında "çöküş gibi görünen"
  işlemlerin bir kısmı en büyük dönüşleri veriyor (2020-03-09 korumasız +377 / korumalı −158; 2020-03-12 +337 / −557). Çöküşü tanıyan
  işaret, dönüşü de kesiyor.
- 2020-03-12 korumalıda −557: D0 gün içi stop 3×dvol, kapanışta −2×dvol'dan çıkış → aynı gün taban (−334) daha iyiydi. En kötü tekil işlem
  ortadan kalkmıyor (korumasız −572 / korumalı −557); kalan kuyruk D0 gün içi geniş stoptan.
- Korumasız kâr çıkışı beklentide daha iyi ama ön kayıtta C (taze NQ kuyruğu). Kullanıcı isteği ön kayıt onayı olduğu için canlıya korumalı
  hâli bağlandı; korumasıza dönmek `CAPREV_KAR_GUARD = False`.
- ⚠️ Kapsam (NDX) ve çöküş işaretleri sonuç görüldükten sonra seçildi; KEŞİF-yalnız seçim ve dokunulmamış EET30/NQ beslemeleri bu riske karşı
  konuldu. İleri doğrulama canlı NDX işlemleriyle: 30 işlemde ort > canlı taban ve CVaR5 ≥ 2 × taban beklenir.
- DAX'ta kâr çıkışı (korumalı ya da değil) çalışmıyor; DAX bacağı aynı gün çıkışta kalır.

## KQ-04 — hiç kullanılmamış dört endeks (FTSE, Euro Stoxx 50, Nikkei 225, Hang Seng; ön kayıt c19d9127): **C**
| 2016–26 | n | Taban | Korumasız kâr (fark / CVaR5) | Korumalı (fark / CVaR5) |
|---|---|---|---|---|
| Stoxx 50 | 81 | | +30,0 / −623 | −9,9 / −517 |
| Nikkei 225 | 98 | | +31,4 / −657 | +3,6 / −480 |
| Hang Seng | 117 | | +8,5 / −526 | +4,3 / −300 |
| FTSE (2 işlem) | 2 | | | |
| **Havuz** | 298 | −16,3 / −227 | **+22,2 (P 0,98) / −596** | **+0,6 (P 0,54) / −430** |
1990–2015 (bu endeksler seçimde hiç yoktu): korumasız +25…+32 (4/4 artı), korumalı +0,6…+17.
Kapsam kuralı (KEŞİF toparlanma ≥ 0,65) DAX'ı 1990–2015 verisinden dışarıda bırakıyor (0,60), dört yeni endeksin dördünü içeride; ama dışarıda kalan
yeni endeks olmadığından kuralın kendisi bu örneklemde sınanamadı.

**Son okuma:** NDX'teki koruma kazancı başka piyasaya taşınmıyor: korumalı kural dokunulmamış piyasalarda tabana döner. "Kâra kadar tut" kenarı ise taşınıyor.
Kuyruk bu kenarın yapısal bedeli. Kuyruğu filtreyle kesmek kenarı da kesiyor; kalan seçenek bir risk/lot kararı:
- korumalı (canlıda): NDX'te B, kart 6/6, kuyruk küçük ama başka piyasada kenar ≈ 0;
- korumasız tam lot: kenar genelleşiyor, kuyruk ~2–2,6 × taban (ön kayıt kuyruk ölçütünü geçmiyor);
- korumasız düşük lot: kuyruğu tabana eşitleyen lot NDX'te ≈ 0,5 (−250/−475); o lotta beklenti ≈ +56 bp-lot (taban +48). Bu oran TEST'ten okunuyor,
  ön kayıtlı değil; KEŞİF oranıyla (≈ 0,38) NDX'te +40 < +48.

## KQ-05 — kısmi tutuş (D0 zararda yarısını kapat): **C**
| | Duka NDX (ort / isabet / CVaR5) | Dokunulmamış 4 endeks (fark / P / CVaR5; sınır −454) |
|---|---|---|
| Taban | +48 / %57 / −250 | — / — / −227 |
| Korumalı (KQ-03, canlıda) | +64 / %70 / −426 | +0,6 / 0,54 / −430 |
| Korumasız tam tutuş | +106 / %89 / −475 | +22,2 / 0,98 / −596 |
| KQ-05 seçimi (VIX korumalı, yarım tutuş) | +78 / %78 / −394 | +3,3 / 0,71 / −469 |
| Korumasız yarım tutuş (betimleyici, seçilmedi) | +80 / %79 / −405 | +8,7 / 0,91 / −471 |

## Kapanış
Beş ön kayıtlı tur. Kalıcı bulgular:
1. Çöküş girişte tanınmıyor; D0 kapanışında tanınıyor (AUC 0,70) ama tanınanları kesmek dönüşleri de kesiyor.
2. "Kâra kadar tut" kenarı genelleşiyor (dokunulmamış piyasalar +22 bp, P 0,98); kuyruk onun yapısal bedeli (taban × 2–2,6).
3. VIX tırmanışı çıkışı ABD dışında bir gün gecikmeli çalışır ve kenarı yer.
4. NDX'te her yapı B geçiyor; NDX + dokunulmamış piyasa birlikte, kuyruk sınırıyla, hiçbir yapı geçmiyor. Kuyruk ile kenar arasındaki seçim bir lot/risk kararıdır.

## KQ-06 — farklı giriş yeri + tutuş şartı (kullanıcı isteği): seçilen **bölünmüş giriş + yarım tutuş**, hüküm **C**
Yapı: tetikte yarım lot al, D0 seans kapanışında kalan yarımı al; her yarı için felaket stopu kendi girişinin 3×dvol altı; her yarının ilk kontrol kapanışında
(tetik yarısı D0, kapanış yarısı D1) zarardaysa yarısını kapat, kalanını kâra kadar (≤ 5 kapanış) taşı.

| | Ort. | İsabet | Sharpe | En kötü %5 |
|---|---|---|---|---|
| Taban (canlı aynı gün) Duka NDX | +48 | %57 | 0,71 | −250 |
| Korumasız kâr çıkışı | +106 | %89 | 1,34 | −475 |
| Korumalı (KQ-03, canlıda) | +64 | %70 | 0,84 | −426 |
| **Bölünmüş giriş + yarım tutuş** | **+76** | **%73** | **1,51** | **−253** |
| MT5 NAS100 / EET30 / NQ farkı (CVaR5) | +32 (−247) / +28 (−261) / +27 (−256) | | | |
| Yeni 10 piyasa (hiç kullanılmamış) | 10/10 artı; kapsam içi 4: +32,6 bp P 0,998 | | | |
| Kör MT5 US500 / US30 / US2000 | **−23 / −19 / −3** (ön kayıt ≥ 2/3 artı istiyordu) | | | |

**Okuma:** kuyruğu tabana indiren ve kenarı koruyan ilk yapı bu (NDX'te en kötü %5 −253 ≈ taban, Sharpe en yüksek). Kuyruğu küçülten mekanizma: çöküşün
çoğu D0 kapanışından sonra derinleşiyor; yarım lotu kapanışa bırakmak hem giriş fiyatını iyileştiriyor hem riskin yarısını çöküşün ilk gününden çıkarıyor.
Ön kayıt hükmü C: kör ABD CFD'lerinde D0 kapanışı yarısı eksi (aynı endekslerin günlük verisi artı; ayrım çözülmedi). DAX'ta uygulanmaz.
