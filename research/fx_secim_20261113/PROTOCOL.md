# FX-01 — Döviz çifti seçimi + zorunlu akış kapıları (ön kayıt)

Tarih: 2026-11-13 · Ön kayıt sonuçlara bakılmadan yazıldı. Sonradan eşik/pencere seçmek yasak; ek fikirler `EK-n` olarak tarihli eklenir.

## 0. Kullanıcı sorusu ve yeniden açma gerekçesi
"Forex'te az riskli, yüksek kazançlı, oynak ve tahmin edilebilirliği en yüksek döviz çifti hangisi? Verisini kutudan al,
üzerinde kazanç kapısı bulana kadar işlem sına." Defterde (§2) FX çifti üzerine hiç sınama yok → yeni alan, yeni veri
(Pepperstone broker FX barları, kutudan). Defter §3-21 ("kim işlem yapmak zorunda?") ve §3-25 ("zorunlu akış takvime kilitli")
bu çalışmanın yön gösterici ilkeleri; §3-26 ("sıklık kenarın düşmanı") ve §3-28 nedeniyle gün-içi koşulsuz saat yönü düşük öncelik.

## 1. Veri
- Pepperstone-Demo (login 61628380) MT5, salt-okuma: 27 çift × D1/H1/M15/M5/M1, `copy_rates_from_pos` döngüsü,
  sütunlar t (sunucu saati), o,h,l,c, tick hacmi, bar spread'i (puan). Sunucu = New York + 7 saat (projede denetlendi; FX'te
  tekrar denetlenecek: EURUSD 08:30 ET NFP dakikası ve 17:00 ET devir boşluğu).
- Bağımsız/kör ek veri: Dukascopy 1m (gerekirse, aynı kural farklı besleme), yfinance günlük (yalnız günlük kurallar).
- Takvim: `research/kt02_takvim_seans_20261111/takvim.csv` (FOMC 2008-01→2026-10, 150 olay). VIX: yfinance `^VIX` günlük.
- Bölmeler: **KEŞİF** veri başı → 2021-12-31 · **KÖR** 2022-01-01 → 2026-11-13. KÖR'e yalnız ön-kayıtlı hücreler girer.

## 2. Çift seçimi (ölçüm; hüküm değil)
Her çift için son 3 yıl (2023-11→2026-11):
- σ_d: günlük (17:00 ET devirli) log getiri std, bp; ADR: ortalama günlük aralık bp.
- κ = medyan likit-saat spread'i (bp, 07–17 UTC H1 bar spread'i) / σ_d → **maliyet/oynaklık oranı** (düşük = işlem edilebilir).
- Gecelik swap (bp/gece, iki yön) — anlık sembol bilgisi.
- "Öngörülebilirlik" vekilleri, KEŞİF ve KÖR ayrı: günlük getiri AC1, VR(5) günlük, saatlik AC1. İşaret iki bölmede aynı değilse
  vekil anlamsız sayılır. Uyarı (§3-21, E27): vekil öngörülebilirlik kenar değildir; asıl ölçüt §3'teki kapılardır.
- Seçim kuralı: κ en düşük üçte bir **ve** en az bir ön-kayıtlı mekanizmanın (§3) uygulanabildiği çift. Swap iki yönde de < −5 bp/gece
  olan çift gece taşıyan hiçbir kurala girmez.

## 3. Hipotezler (mekanizma = zorunlu akış veya risk primi)
Ortak icra: giriş = karar anından SONRAKİ bar açılışı + bar spread'i (spread=0 ise o yılın aynı saat medyanı); çıkış bid/ask yarı
spread'i; tek pozisyon (aynı kural için örtüşme yok); getiri bp ve sepetlerde eşit ağırlık. Maliyet stresi spread × 1,5.

**H8 Gotobi / Tokyo fix (birincil).** Japon ithalatçıları ayın 5,10,15,20,25,30. günleri (hafta sonu/JP tatili → önceki iş günü;
ay sonu iş günü de dahil) 09:55 JST fiksinde USD alır (Ito & Yamada 2017). Kural H8a: gotobi günü **USDJPY uzun 08:00 JST →
09:55 JST** (= 23:00 → 00:55 UTC, M5; M5 yoksa M15 00:45 çıkışı). H8b: aynı gün **10:00 → 15:00 JST kısa** (fiks sonrası geri verme).
Kontrol: aynı pencere gotobi olmayan hafta içi günler (fark = kural − kontrol). Kör piyasalar: EURJPY, AUDJPY, GBPJPY (aynı pencere,
JPY satışı akışı). Beklenen olay ~6/ay.

**H1 Ay sonu 16:00 Londra fiksi, öz sermaye hedge dengelemesi (birincil).** Melvin & Prins (2015): ABD hissesi ay içinde yabancıdan
iyi gittiyse hedge eden yabancı yatırımcılar ay sonu fiksinde USD satar. s = sign(US500 ay-içi getirisi − GER40 ay-içi getirisi),
ayın son iş günü 10:00 Londra'da bilinen değerlerle. Kural: 10:00 → 16:00 Londra (fiks dakikası 16:00 dahil değil; çıkış 15:55 M5
veya 15:45 M15) s>0 ise USD sepeti kısa (EURUSD, GBPUSD, AUDUSD uzun; USDJPY, USDCHF, USDCAD kısa), s<0 uzun. H1b: 16:00 → 20:00
Londra ters yön (fiks sonrası dönüş). ~12 olay/yıl → sepet olay sayısı yıl × 12.

**H3 FOMC günü USD zayıflığı (birincil).** Mueller-Tahbaz-Salehi-Vedolin (2017): FOMC günleri USD karşısında risk primli para birimleri
kazanır. Kural: FOMC-1 17:00 ET (devirden 1 saat sonra, E97: 18:00 ET giriş) → FOMC günü 16:00 ET, USD sepeti kısa (H1 sepeti).
H3b yalnız duyuru öncesi (→ 13:55 ET). Kontrol: aynı haftanın diğer günleri aynı pencere.

**H4 Taşıma çözülmesi = korku dönüşü (birincil, defter §3-2 aktarımı).** Brunnermeier-Nagel-Pedersen (2008): stres günlerinde taşıma
pozisyonları zorla kapanır, aşırılık geri döner. Kural: önceki gün VIX kapanışı ≥ 18,4 (projenin VIXREG eşiği, sonradan seçilmedi) ∧
AUDJPY günlük (17:00 ET) RSI2 < 10 → 18:00 ET uzun; çıkış ilk yükselen günlük kapanış (17:00 ET) veya en geç 5 gün. Gecelik swap
gerçek sembol değeriyle düşülür. Kör piyasalar: NZDJPY, CADJPY, AUDUSD, NZDUSD, EURJPY. Ayna (coşku dönmez kontrolü): VIX < 18,4 ∧
RSI2 > 90 kısa — kenar beklenmez. Taban: aynı dönem rastgele 18:00 ET uzun, aynı tutuş süresi dağılımı (≥1.000 çekiliş).

**H2 Gün içi mevsimsellik (ikincil, düşük ön olasılık; SD-01 X).** Breedon & Ranaldo (2013): para birimi kendi iş saatlerinde değer
kaybeder. EURUSD/GBPUSD: Avrupa 07–12 UTC kısa, ABD 13–20 UTC uzun; USDJPY: Tokyo 00–06 UTC uzun, ABD 13–20 UTC kısa; her
dilim ayrı hücre.

## 4. Geçme ölçütleri (hücre başına; seçim KEŞİF'te değil, kural önceden sabit)
1. n ≥ 150 olay (H4 için ≥ 60 + ≥3 kör piyasa — seyrek kural, §3-21)
2. Net ort > 0 bp ve gün-kümeli bootstrap P(EV>0) ≥ 0,90 (tüm veri)
3. KEŞİF ve KÖR ikisinde de net ≥ 0
4. Spread × 1,5'te net > 0
5. İcra farkı (bar kapanışı vs sonraki açılış) ort'un yarısını aşmaz
6. Tek pozisyon kısıtıyla pozitif
Ek: kontrol hücresine göre fark > 0 (P ≥ 0,90); birincil 4 hücre (H8a, H1, H3, H4) Holm ile düzeltilir (α = 0,10 tek yönlü).
Hepsini geçen → kart (2. KURAL) + GÖLGE önerisi. Hiçbiri canlıya bağlanmaz (karar kullanıcıda).

## 5. Tuzak kontrol listesi
E1 (copy_rates_from ileri bakış) — `copy_rates_from_pos` kullanılıyor; E2/E68 saat ekseni denetimi; E7 icra; E15 aynı-gün ortalaması
taban yasak; E27 taban isabeti; E97 devir dakikası spread'i (17:00 ET'de giriş yok); E99 VIX kapanışı 16:15 ET → önceki günün VIX'i;
E102 örtüşme; E110 portföy; E114 takvim kontrol hücresi.

## EK-1 (2026-11-13, sonuç görülmeden — veri kısıtı)
Terminal "max bars" = 100.000: H1 ≈ 2010-10 →, M15 ≈ 2022-11 →, M5 ≈ 2025 →. Saat ekseni denetlendi: EURUSD M15 NFP |getiri| tepesi
2022–2026 her yıl 08:30 ET (sunucu = ET+7 doğru). Bu nedenle:
- **H8a ana hücre H1:** gotobi günü USDJPY uzun 23:00 UTC bar açılışı → 01:00 UTC bar açılışı (= 10:00 JST; fiks 09:55 dahil, 5 dk
  sonrası içeride). KEŞİF 2010-10→2021, KÖR 2022→. H8b: 01:00 → 06:00 UTC kısa. M15 (2022-11→, çıkış 00:45 UTC) ve Dukascopy 1m
  (2012→, çıkış 00:55 UTC, farklı besleme) sağlamlık hücreleri; hüküm H1 + KÖR'e göre.
- **H1 (ay sonu):** H1 barlarıyla 10:00 → 16:00 Londra bar açılışı (fiks penceresinin yarısı içeride); H1b 16:00 → 20:00 Londra.
- **H3 (FOMC):** H1, giriş 18:00 ET bar açılışı, çıkış 16:00 ET bar açılışı (H3b 14:00 ET bar açılışı).
- Gotobi takvimi: gün ∈ {5,10,15,20,25,30} veya ayın son iş günü; JP tatili/hafta sonuysa önceki JP iş günü (`holidays.JP`);
  ABD/İngiltere tatilleri dışlanmaz (Tokyo akışı).

## EK-2 (2026-11-13 ~18:35 UTC — USDJPY H1 sonuçları görüldükten SONRA, kör piyasalar görülmeden ÖNCE)
Görülenler: H8a USDJPY net +0,45 bp (P 0,84, kontrol −0,43) → ölçüt 2'de kalır. H8b USDJPY net +1,72 bp (P 0,965; KEŞİF +1,65 /
KÖR +1,88; kontrol +0,05, fark P 0,949). H2 altı hücrenin hiçbiri geçmedi (X). H8b ikincil hücreydi; tek başına USDJPY'de geçmesi
seçim etkisine açık (H8a/H8b × 4 çift = 8 hücre). Bu nedenle H8b için AŞAĞIDAKİLER sonuç görülmeden sabitlenir:
- **Kör çiftler:** EURJPY, AUDJPY, GBPJPY H1, aynı pencere (01:00→06:00 UTC kısa). Geçer: üçünün en az ikisinde net > 0 ve
  havuz (eşit ağırlık, gün kümeli) P ≥ 0,90; kontrol farkı havuzda > 0.
- **Ayrı besleme:** Dukascopy USDJPY 1m (indirilebildiği kadar), 01:00→06:00 UTC, aynı gotobi takvimi; brüt işareti aynı olmalı.
- **M15 (2022-11→):** giriş 01:00, çıkış 06:00 UTC; ayrıca fiks hemen sonrası 01:00→02:00 alt penceresi bilgi amaçlı.
- **Seçim düzeltmesi:** 8 hücrelik aile içinde max-t permütasyonu (gotobi etiketlerini yıl içinde dairesel kaydır, 1.000 tekrar;
  istatistik = 8 hücrenin en büyük kontrol-farkı t'si). p ≤ 0,10 şart.
- Birleşik "gotobi günü" stratejisi (H8a uzun + H8b kısa) bilgi amaçlı raporlanır, ayrı hüküm verilmez.
- **Komisyon:** hesabın FX komisyonu kutudaki deal geçmişinden okunur; maliyete eklenir (Razor ise ≈ $7/lot RT).

## EK-3 (2026-11-13 ~19:30 UTC — §2 seçim tablosundan SONRA, sınamadan ÖNCE)
Görülen: H1/H1b X, H3 n=128 (net +5,85, kontrol farkı P 0,925), H3b +4,36 P 0,949 ama olay isabeti %50,8, ilk 5 olay çıkınca +2,45,
2025–26 eksi → C+. H8 ailesi 8/8 hücrede kontrol farkı > 0; EK-2 havuz ölçütü (P 0,71) geçmedi; max-t B_EURJPY p 0,013, B_USDJPY 0,198.
Seçim tablosu: günlük VR5 iki dönemde de < 0,9 olan çiftler AUDCAD (0,86/0,82), EURGBP (0,94/0,80), GBPCHF (0,96/0,89), EURAUD (0,95/0,88).
**Uyarı: H5 bu tablo görüldükten sonra yazıldı → seçim yüklü; hüküm yalnız KÖR + görülmemiş çiftlerle.**

**H5 Benzer ekonomili çapraz çiftte ortalamaya dönüş.** Günlük (17:00 ET) z = (kapanış − SMA20) / std20. z ≤ −2 → ertesi 18:00 ET uzun,
z ≥ +2 → kısa; çıkış kapanış SMA20'yi geçince (18:00 ET) veya en geç 10 gün; tek pozisyon; gerçek swap. Çiftler: AUDCAD, EURGBP,
GBPCHF, EURAUD (tabloda görülen) + **görülmemiş/kör** AUDNZD, EURCHF, NZDCAD, CADCHF, AUDCHF (veri varsa). Taban: aynı tutuş süreli
rastgele giriş (1.000 çekiliş), aynı yön payı. Geçer: §4 ölçütleri havuzda + kör çiftlerin ≥ yarısında KÖR net > 0 + plasebo yüzdelik ≥ 0,90.

## EK-4 (2026-11-13 ~19:50 UTC — H4/H5 X ve M15 ayrıştırması görüldükten SONRA, H8c sınanmadan ÖNCE)
Görülen: H4 6/6 çiftte uzun kol ≤ 0 (AUDJPY −31,5 bp) → FX'te stres sonrası aşırı satım dönmüyor (X). H5 kör çiftler AUDNZD −17,6,
EURCHF −3,9 → X. M15 (2022-11→, tümü KÖR dönemi): JPY çiftlerinde gotobi sabahı yükseliş 08:00→08:45 JST'de bitiyor, fiks çevresi eksi,
10:00→15:00 JST kısa dördünde de kontrolden iyi. 08:45 zamanlaması KÖR veriden görüldü → **yeni pencere ancak Dukascopy 2012–2021 ile
sınanabilir; şimdilik hüküm yok.**
**H8c (koşullu fiks sonrası dönüş):** gotobi günü 23:00→01:00 UTC getirisi > 0 (sabah akışı fiyatı itti) → 01:00→06:00 UTC kısa; aksi hâlde
işlem yok. Mekanizma: zorunlu akışın geçici fiyat etkisi geri döner. Kontrol: gotobi olmayan günlerde aynı koşul. Çiftler: USDJPY (ana),
EURJPY, GBPJPY, AUDJPY (kör). H1, KEŞİF/KÖR. Geçer: §4 + kontrol farkı P ≥ 0,90 + 4 çiftin ≥ 3'ünde net > 0.

## EK-5 (2026-11-13 ~20:15 UTC — H8c kartı 5/6 çıktıktan SONRA, H9 sınanmadan ÖNCE)
**H9 Ay sonu Londra fiksi geçici etki dönüşü (H8c mekanizmasının Londra karşılığı).** Ayın son iş günü, çift başına 10:00→16:00 Londra
getirisi r_pre; |r_pre| > 0 → 16:00→20:00 Londra ters yön (−sign(r_pre)). Çiftler: EURUSD (ana), GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD
(sepet, eşit ağırlık). Kontrol: ay sonu olmayan iş günlerinde aynı koşul. Maliyet: bar spread'i ile tick spread'i büyüğü + Razor komisyonu
(EURUSD 0,60, GBPUSD 0,53, USDJPY/USDCHF/USDCAD 0,70, AUDUSD 1,07 bp). Geçer: §4 + kontrol farkı P ≥ 0,90 + 6 çiftin ≥ 4'ünde net > 0.
Doz-tepki (|r_pre| üçte birlikleri) bilgi amaçlı.

## EK-6 (2026-11-13 ~20:00 UTC — H8c/H9 kartları 5/6 (5. ölçüt: maliyet) çıktıktan SONRA, aşağıdakiler sınanmadan ÖNCE)
Sorun: kenar maliyete ince (brüt ≈3,2, maliyet ≈1,4 bp). Doz-tepki her iki kuralda görüldü → eşik seçimi seçim yüklü olur; bu yüzden eşik
**nedensel ve sabit** tanımlanır, doğrulama **hiç görülmemiş çiftlerde** yapılır.
- **H9-KÖR:** H9 kuralı birebir, H9 sepetinde OLMAYAN çiftlerde: NZDUSD, EURJPY, GBPJPY, AUDJPY, CADJPY, NZDJPY, EURGBP, EURCHF, EURAUD,
  GBPAUD, AUDCAD, EURCAD, GBPCHF, AUDNZD (maliyet = bar/tick büyüğü + komisyon; tick ölçümü yoksa bar spread × 2). Geçer: havuz net > 0,
  P ≥ 0,90, çiftlerin ≥ yarısı > 0, kontrol farkı > 0.
- **Doz eşiği D (nedensel):** olay günü fiks öncesi hareketin |r_pre| değeri, aynı çiftin aynı penceresinin **önceki 250 iş günündeki |r|
  dağılımının 67. yüzdeliğinin** üstündeyse işlem (yalnız geçmiş bilgi). Bu eşik iki kurala da aynen uygulanır:
  - **H9-D:** 6 çift sepet + H9-KÖR çiftleri ayrı raporlanır.
  - **H8c-D:** USDJPY gotobi, sabah itmesi > 0 ve > 250 günlük 23→01 UTC getirilerinin 67. yüzdeliği; EURJPY/GBPJPY/AUDJPY kör.
- Kart: 6 ölçüt (5. ölçüt aynı tanım). Bir kural ancak kendi KÖR çiftlerinde de net > 0 ise "LIVE adayı" sayılır; aksi hâlde GÖLGE.

## EK-7 (2026-11-13 — H8c-D havuzu 4/6, H9-KÖR X görüldükten SONRA, H10 sınanmadan ÖNCE)
Gün içi fiks kenarları maliyete ince → defter §3-26/§3-21: seyrek, günlerce tutulan, maliyete dayanıklı kol. H4'te JPY çaprazlarında iki uç da
devam etti (momentum işareti); XAU'da günlük Donchian + EMA200 tek kazanan (hafıza: xauusd-daily-swing-edge). Mekanizma: faiz/politika
döngüleri ve risk primi yavaş fiyatlanır (Menkhoff vd. 2012 döviz momentumu; CTA getirileri).
**H10 Günlük trend takibi (Donchian 55 / EMA200).** Broker D1 (17:00 ET kapanış). Uzun: kapanış > önceki 55 günün en yükseği ∧ kapanış > EMA200;
kısa: kapanış < önceki 55 günün en düşüğü ∧ kapanış < EMA200. Giriş ertesi D1 açılışı. Çıkış: kapanış önceki 20 günün karşı ucunu kırınca
(ertesi açılış) veya stop = giriş ∓ 2×ATR20 (gün içi dokunuş, stop fiyatından). Tek pozisyon/çift. R = 2×ATR20.
Maliyet: 2 × (o yılın medyan bar spread'i) + komisyon + gerçek gecelik swap (bugünkü sembol değeri; E72 uyarısı) + Çarşamba ×3.
Çiftler — **ana (önceden):** EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD; **kör:** 14 çapraz (EK-6 listesi) + USDMXN, USDZAR,
USDNOK, USDSEK. Dönemler: **D1** veri başı → 2009 · **D2** 2010–2021 · **D3** 2022 → (en yeni). Taban: aynı çift, aynı yön payı, aynı tutuş
süresi dağılımlı rastgele girişler (500 çekiliş). Geçer: ana havuz ort R > 0, P ≥ 0,90, D1/D2/D3 üçünde de ≥ 0, plasebo yüzdelik ≥ 0,90,
kör havuz ort R > 0; en büyük 5 işlem çıkınca hâlâ > 0 (E101). Ayna (karşı-trend aynı tetik) bilgi amaçlı.

## EK-8 (2026-11-13 ~22:30 UTC — EK-6/7 sonuçlarından SONRA, H11 sınanmadan ÖNCE)
**H11 Taşıma × VIX rejimi.** Mekanizma: taşıma pozisyonları sakin rejimde birikir, stres başlayınca zorla kapanır (H4: stres günü JPY çaprazı
düşmeye DEVAM ediyor). Kural (günlük, broker D1 17:00 ET kapanışları): t+1 günü getirisi için pozisyon, **t−1 günü VIX kapanışı** < 18,4 ise
UZUN taşıma çifti, aksi hâlde DÜZ (bir gün fazladan gecikme → E99 güvenli). Maliyet: her giriş/çıkışta 2 × yıllık medyan spread + komisyon;
spot getiri (tarihsel faiz farkı YOK → taşıma lehine olan getiri dışarıda, ihtiyatlı); bugünkü swap ayrıca bilgi amaçlı.
Çiftler — **ana:** AUDJPY, NZDJPY, CADJPY (JPY fonlu); **kör:** AUDUSD, NZDUSD, USDJPY, GBPJPY, EURJPY, USDMXN (kısa = MXN uzun), USDZAR (kısa).
Dönemler: P1 veri başı→2009, P2 2010–2021, P3 2022→. Ölçüt (ana havuz, günlük eşit ağırlık): (a) içeride gün ort − dışarıda gün ort > 0 ve
gün-blok (21 gün) bootstrap P ≥ 0,90; (b) içeride ort > 0 her üç dönemde; (c) filtreli stratejinin Sharpe'ı al-tut Sharpe'ından büyük her
üç dönemde; (d) kör havuzda (a) aynı işaret. Ters ayna (VIX ≥ 18,4 → uzun) bilgi amaçlı. Kart ölçütleri ayrıca raporlanır (olay = rejim girişi).

## EK-9 (2026-11-13 ~22:45 UTC — H11 ve aynası görüldükten SONRA, H12 kör çiftleri sınanmadan ÖNCE)
Görülen: H11 X. Ayna (VIX ≥ 18,4 → uzun) ≤2009'da eksi, 2010→'da ana ve kör havuzda +; P3'te 10/10 çift aynı yön. Bu, NDX VIXREG'in (VIX ≥ 18,4
→ BUY lehte) FX karşılığı olabilir (Fed çağı "korku döner"). **Seçim yüklü** → hüküm yalnız H11'de HİÇ kullanılmamış çiftlerle.
**H12 (VIXREG-FX):** t−1 VIX kapanışı ≥ 18,4 → risk para birimi UZUN (aksi düz), yalnız 2010-01→. Maliyet H11 gibi.
**Kör çiftler (önceden):** USDNOK (kısa), USDSEK (kısa), USDCAD (kısa), EURAUD (kısa), EURCAD (kısa), GBPAUD (kısa), AUDCAD? HAYIR (iki taraf
risk). Geçer: kör havuzda içeride − dışarıda > 0 hem P2 hem P3'te, havuz blok P ≥ 0,90, strateji Sharpe ≥ al-tut Sharpe (P2+P3),
6 çiftin ≥ 4'ünde fark > 0. Ayrıca H11'deki 10 çiftin 2010→ sonucu "görülen" diye ayrı yazılır.
