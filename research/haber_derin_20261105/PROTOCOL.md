# Ön-kayıt — Haber neden etkilemiyor, kâr eden bir yapı var mı? (HB-03, 2026-11-05)

Fiyat sonucuna bakılmadan yazıldı. Görülen tek şey başlık biçimi ve satır sayısıdır. Değişiklik olursa sona tarihli EK düşülür.

## Neden yeniden açılıyor (Defter §0)
HB-01/02 tek rejimli 10 haftaydı, karar anı `created_at`'ti ve "haber = tek tür" sayıyordu. Makro sürpriz hiç sınanmadı (Defter §2.24 dersi).
Yeni veri: FinancialJuice Telegram arşivi 2020→ (`ACTUAL x (FORECAST y, PREVIOUS z)` başlıkta), WalterBloomberg 2024→, Trump Truth arşivi 2022→, Dukascopy 1m bid/ask 2020→ dört sembol.
Yeni tanım: sürpriz, başlık yeniliği, haberli/habersiz şok, sıra-sonrası tepki.
BTC-SC-VS09 (BTC, sürprizsiz) ve MK-09/15 (gün seçimi) farklı soru; tekrar değil. GF-07 FOMC öncesi SELL yasağıydı; burada uzun sürüklenme ayrı tanım.

## Dönemler
- KEŞİF: 2020-01-01 → 2024-12-31. Tüm seçimler burada.
- DOĞRULAMA: 2025-01-01 → 2025-12-31. Keşifte geçen hücreler, sabit parametreyle.
- KÖR: 2026-01-01 → 2026-11-04. Yalnız doğrulamayı geçenler, bir kez bakılır.
Canlı motor (`news_stories`) ileri dönem olur.

## İcra
Karar anı t0: başlığın Telegram yayın damgası (saniye). Giriş: t0'dan SONRA açılan ilk 1m bar, buy=ask_open, sell=bid open. Çıkış: ufuk barı kapanışı, buy=bid close, sell=ask close. Bu, bar içi gerçek spread'i (E7) verir ve 0–60 sn arası gecikme içerir.
Stres: spread ×1,5 ek maliyet + yan başına 1 medyan spread kayma.
Birim: nominal **bp** birincil (E50 ATR paydası tuzağı). R = t0 öncesi kapanmış 15m ATR(14) ikincil.
Veri boşluğu: giriş barı t0'dan > 3 dk sonraysa ya da ufukta > 10 dk boşluk varsa olay atılır. Ufuklar 5, 15, 60, 240 dk ve NY kapanış (16:55 ET).
Damga denetimi: sınamadan önce D1 pozitif kontrolü geçmeli; geçmeyen sembol dışarıda kalır.

## Teşhis (işlem değil; soru: neden etkilemiyor gibi görünüyor?)
- **D1 Pozitif kontrol:** takvimli US veri (CPI, NFP, FOMC) dakikasında |getiri| oranı, aynı ISO hafta + aynı saat (±0) rastgele günlere göre. Beklenti ≫1. Geçmezse ölçüm yanlıştır.
- **D2 Öncü/izleyen eğrisi:** başlık sınıfları için t∈[−60,+60] dk |1m getiri|/o dakikanın olağan değeri. Sınıflar: makro ACTUAL (FJ), FJ diğer, Walter, Truth (kelime eşleşen), HB-01 başlıkları. Tepe t<0 ise haber geç. Ayrıca H=önceki 15 dk yönlü getiri ile sonraki 15 dk yönlü getiri korelasyonu.
- **D3 Ters sorgu:** takvim dışı büyük hareketler (5 dk |getiri| ≥ 5× o saatin medyanı, 30 dk aralıklı): hareketin başlangıcına göre ilk ilgili başlığın zamanı. Pay: önce / ±1 dk / 1–5 dk sonra / 5–30 dk sonra / hiç. Bu "haber geç mi" sorusunun doğrudan ölçüsüdür.
- **D4 Yenilik:** başlık, son 24 saatteki başlıklarla token kapsama ≥0,6 ise tekrar. Yeni/tekrar için |getiri| oranı.
- **D5 Tepki hızı:** makro sürprizlerde 240 dk'lık hareketin ilk 1/5/15 dk'daki payı; 1 dk sonra girene kalan pay.

## Sürprizin tanımı
`ACTUAL a (FORECAST f, PREVIOUS p)` ayrıştırılır; birim eşlemesi yoksa satır atılır. Başlık ailesi normalize edilir (ülke + gösterge). z = (a−f)/s; s = o ailenin yalnız GEÇMİŞ sürprizlerinin standart sapması, en az 12 gözlem (sızıntı yok, ilk 12 atılır).
Yalnız şu aileler (önceden sabit, US + DE/EZ): US CPI MoM/YoY/Core, NFP, işsizlik, PCE core, PPI, ISM imalat/hizmet, perakende, GDP, işsizlik başvuruları, FOMC/ECB faiz; Almanya CPI/IFO/ZEW, Euro CPI; EIA ham petrol stok (USOIL).
Tek olay anında birden çok satır varsa: aynı dakika içinde önem sırasındaki ilk aile (CPI core > CPI > NFP > diğerleri).

## Stratejiler
Sembol × aile × ufuk hücreleri; her aile (S1…S7) kendi maxT'si. Yönler önceden sabit veya geçmişten öğrenilir, sonuçtan seçilmez.

- **S1 Sürpriz-yön (ekonomik öncül):** |z|≥1. Sıcak enflasyon / güçlü istihdam-büyüme → XAU SELL, NDX & DAX SELL (enflasyon), EIA stok beklentiden az → USOIL BUY. Soğuk → ters.
- **S2 Sürpriz-yön (öğrenilen işaret):** |z|≥1. Aile×sembol için son 12 olayın ilk-5-dk tepki işareti ile z işaretinin çarpımı işareti (kayan, geçmiş). 2022 sonrası "iyi haber kötü" rejimini yakalar.
- **S3 Tepkiye uy (haber sonrası sürüklenme):** ilk 1 dk (t0'ın başladığı bar + sonraki bar) |getiri| ≥ 1,5×ATR1m-ölçeği ve |z|≥1, tepki yönüne giriş.
- **S4 Sürprizsiz tepkiyi söndür:** |z|<0,5 ama ilk 1 dk hareket büyük; ters yöne giriş. Hipotez: bilgi yok, emir akışı/likidite kaynaklı; geri döner.
- **S5 Reddedilen haber:** |z|≥1 ve 5 dk tepki sürprizin öncül yönünün tersi. Piyasa yönünde giriş 5. dk kapanışından sonra. Hipotez: konumlanma bilgisi.
- **S6 Haberli vs habersiz şok (Chan 2003):** takvim dışı 5 dk şok (D3 tanımı); son 10 dk'da ilgili yeni başlık varsa devam, yoksa söndür. Şok barı kapanışından sonraki bar açılışı. Ayrı: haberli-söndür, habersiz-devam yalnız ayna raporu. FJ + Walter (2024→ Walter).
- **S7 FOMC öncesi sürüklenme (Lucca-Moench):** açıklamadan 24 sa önce uzun, açıklamadan 5 dk önce çık; ikinci tip açıklama sonrası ertesi gün ters. NDX, DAX, XAU. Takvim önceden ilanlı.
- **S8 Konu yön kuralları:** Önceden sabit sözlük. Tırmanma (attack, strikes, missile, Hormuz closure) → USOIL BUY, XAU BUY; yumuşama (ceasefire, truce, peace deal) → USOIL SELL, XAU SELL. OPEC kesinti → USOIL BUY; artış → SELL. Tarife artışı → NDX SELL; tarife ertelendi/anlaşma → NDX BUY. Fed "cut" yorumu güvercin → NDX BUY. 30 dk bağımsız olay, yeni başlık.
- **S9 Truth Social:** Trump gönderisi, sözlük tarife/Fed/Çin/petrol. Yeni bağımsız olay (60 dk). Yön: gönderi sonrası ilk 2 dk tepkiye uy; işaret sözlüğü S8. Beğeni/yanıt sayıları sonradan oluştuğu için KULLANILMAZ.
- **S10 Sıra-sonrası aralık:** Takvim barı sonrası hareket Zaman Makinesi %90 bandını (60 dk, aynı saatin olağanı) aşınca söndür. Yeni özellik + haber kombinasyonu.
- **S11 Haber kapısı mevcut işlemlerde:** Bot işlemleri (`bot_trades`) + DAYCOMBO/REENTRY replay; ±30 dk takvim, son 15 dk ilgili yeni başlık sayısı, sessiz/yoğun kırılımı. İşlem eklemez, eler.
- **S12 NDX ORB × haber (DTS-02 C):** ORB uzun, yalnız veri günü / veri olmayan gün kırılımı.

## Geçme ölçütü (keşif)
ort. net bp > 0 · gün-blok bootstrap P(EV>0) ≥ %95 · kronolojik iki yarı ≥ 0 · stres > 0 · aynı hafta+saat plasebo p ≤ 0,05 (2.000 çekiliş, aynı yön dağılımı) · maxT ≤ 0,10 (aile içi) · n ≥ 30 bağımsız olay.
Doğrulama 2025: aynı parametreyle ort. > 0 ve P ≥ %80. Kör 2026: ort. > 0. **"Kârlı" denebilmesi için üçü de ve 2. KURAL kartındaki 6 ölçüt gerekir.** Tek keşif hücresi kâr değildir.

## Dürüstlük
Bu araştırmanın hedefi "olumlu bulmak" olsa da, ölçüt gevşetilmez. Geçen yoksa hüküm X yazılır ve neden açıklanır.

## EK-1 (2026-11-05, fiyat sonucu görülmeden; yalnız veri erişimi değişti)
- Dukascopy saatte ~40 dosyayla sınırlı (M19-07 notu), 2020'den dört sembol indirilemez. HistData belirteç istiyor, kullanılmadı. Sıra: NDX tam, diğerleri olay günü.
- FinancialJuice arşivi fiilen 2024/25'te başlıyor (2020'de küçük kalıntı). Bu yüzden dönemler: **KEŞİF 2024-01-01 → 2025-12-31 · DOĞRULAMA 2026-01-01 → 2026-06-30 · KÖR 2026-07-01 → 2026-11-04.**
- NDX barları: Dukascopy 2024 ve 2026 yalnız BID (ask = NY saatine göre 2025 medyan spread), 2025 gözlenen bid/ask. Veri dakikasında gerçek spread ortalamadan büyük olduğu için tahmini ask iyimserdir: stres ölçütü bu yüzden şarttır, olay dakikası spread'i 2025 gözlemiyle ayrıca raporlanır.
- XAU/USOIL/DAX yalnız 2026-02+ önbellek ve olay-günü Dukascopy; D1 eksen denetimi şart (E76, E92).
- Takvim tabanlı S7, S12 ve Truth S9 için aynı dönemler.

## EK-2 (2026-11-05, S7/S9 keşif sonuçları görüldükten sonra, yeni aileler; o sonuçlardan parametre seçilmedi)
Genel aile düzeltmesi: her aile için aynı kaydırılmış etiketle maxT (2.000 çekiliş). Ölçüt: maxT ≤ 0,10.
- **S13 Bilanço primi (Frazzini-Lamont):** AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA kapanış sonrası bilanço günü D. (a) D−1 15:55 ET → D 15:55 ET uzun NDX. (b) D 15:55 → D+1 09:35 ET uzun (tepki gecesi). Çakışan günler tek olay. Gece finansmanı ek 1 bp.
- **S14 Hafta sonu boşluğu:** Paz açılış − Cum kapanış; |boşluk| ≥ 20 bp. Sol: Pazartesi 09:25 ET'ye kadar boşluk yönüne ters. Kırılım: hafta sonu Truth tarife/Çin gönderisi var/yok.
- **S15 Olay patlaması söndürme:** CPI, NFP, FOMC: ilk 1 dk ve ilk 5 dk tepkisinin tersi; 15/60/240 dk.
- **S16 Çift yönlü durdurma (bracket):** olaydan 1 dk önce ±X (X = 0,5/1/2 × olay öncesi 60 dk 1m |getiri| ortalaması × 5), TP = 2X, SL = karşı uç, 15 dk süre. Aynı barda iki uç → zarar. Kayma: 1 spread.
- **S9b Truth metin yönü:** tırmanma sözlüğü → NDX SELL, anlaşma sözlüğü → NDX BUY; tepkiyi beklemeden gönderi damgasından sonraki bar.

## EK-3 (2026-11-05, keşif sonuçları görüldü: S13b/c ve S14-yön aday)
Bağımsız dönem sınaması; parametre değişmez, tanım aynı:
- S13c/S13b: QQQ günlük (kapanış → ertesi açılış), 2012→2023. Kıyas: aynı dönemdeki bütün geceler ve bilanço dışı geceler, fark için gün-blok bootstrap. Geçer: fark > 0, P ≥ %95, iki yarı ≥ 0, maliyet 2 bp sonrası > 0.
- S14-yön: NDX 1h 2016→2023. |boşluk| ≥ 20 bp, reopen sonrası ilk tam saat kapanışında gir, Pzt 09:00 ET'ye en yakın saat kapanışında çık; 3 pt spread. Geçer: ort > 0, P ≥ %90, iki yarı ≥ 0.
- 1m sağlamlık (2024-25): giriş gecikmesi 5/15/60 dk, eşik 10/20/40 bp. Seçim yapılmaz, yalnız duyarlılık.
Geçerse: Doğrulama 2026-H1 + Kör 2026-H2 (1m), bir kez.

## EK-4 (2026-11-05, S14 bağımsız dönemde X; S13b geçti) — S13b şüphe sınaması, 2012→2025, 2026 hâlâ görülmedi
Ölçüt önceden: (1) D−3…D+3 komşu geceler: D belirgin üstün değilse "bilanço" değil "mevsim" → yeniden yorum. (2) Negatif kontrol: sabah raporlayanlar (JPM, WMT, GS, JNJ, PG, KO, HD, UNH) AYNI gece D−1 → D sabahı raporu; indeks ağırlığı düşük, beklenti yok/az. (3) Kesit dışı: NFLX, AVGO, AMD, ADBE, COST, INTC, CSCO, QCOM kapanış sonrası: işaret + ve 7 şirketten küçük olmalı. (4) FOMC açıklaması / CPI / NFP ertesi gecesiyle çakışanlar çıkarılınca fark kalmalı. (5) SPY ile aynı geceler: işaret + (ağırlık küçük). (6) NDX 1h 2016→2023 ile icra: 16:00 ET kapanış → ertesi 09:00 bar kapanışı (10:00 ET) ve 3 pt spread + 2 bp gece. (7) Yıl yıl tablo: tek yıl mı taşıyor. (8) Plasebo: aynı yılın rastgele aynı sayıda gecesi, 5.000 çekiliş.
Tümü geçmeden 2026'ya bakılmaz.

## EK-5 (2026-11-05) S13b 2026 açılışı (bir kez)
Kural sabit: 7 şirket (AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA), kapanış sonrası bilanço günü D, D 15:55 ET uzun NDX, D+1 09:35 ET çıkış, gece finansmanı 2 bp. Doğrulama 2026-01-01→06-30, Kör 07-01→11-04. QQQ (kapanış→açılış) ve NDX 1m (2026-02-08+).
Geçer: doğrulama ort > 0 ve P ≥ %80 (kısa dönem), kör ort > 0. 2. KURAL kartı 2012→2025 + 2026 toplu ayrıca hesaplanır.

## EK-6 (2026-11-05) S13b hükmü + yeni aileler
**S13b: 2012→2025 geçti (plasebo p 0,0016, 12/14 yıl +), 2026 doğrulama −14,2 bp ve kör −30,1 bp (17 gece): ölçüt tutmadı → C, canlı önerilmez.**
- **S18 Bilanço sonrası tepkiye uy:** D 16:00→16:30 ET hareket (|≥15 bp|) yönünde 16:31 giriş, D+1 09:35 çıkış. Keşif 2024-25 (1m).
- **S19 Bilanço sabahı gün içi:** D+1 09:35'te gece boşluğu yönü (|≥30 bp|): uy / ters, 15:55 çıkış.
- **S12 ORB × takvim:** DTS-02 birincil (NDX 5m, OR15, or_mid stop, 2R, uzun) 2024 Dukascopy'de bağımsız sınama (daha önce görülmedi) ve 2024-25 veri günü (CPI, NFP, FOMC) / bilanço ertesi / diğer kırılımı.

## EK-7 (2026-11-05) S12 hüküm hazırlığı: ORB uzun
2024 bağımsızda geçti (n=184, +0,165R, P %95, yarılar +). Şimdi önceden yazılan sınamalar, parametre aynı (OR15, or_mid, 2R, uzun, 5m):
(a) Ayı: 30m barlarda OR30 aynı mantık, 2021-07→2023-02 (5m yok), ve 15m OR15 2023-03→2023-12. Karşı: aynı TF'de 2024-26.
(b) Taban: aynı gün, aynı risk mesafesi, aynı hedef; giriş OR sonu ve seans içi rastgele bar. Fark gün-blok bootstrap.
(c) Kısa ayna + yön: kısa aynı kuralla.
(d) bp: işlem başına nominal bp ve yıl toplamı; R paydasının etkisi (E32/E50): stop mesafesi kovalarına göre.
(e) Spread stres: 1,3 → 3,4 pt.
(f) VIX kovası (önceki gün kapanışı, 18,4) yalnız rapor.
Geçer: (a) ayıda ort. ≥ −0,02R ve toplam > 0; (b) fark > 0, P ≥ %90; (d) bp > 1; (e) stres > 0. Geçerse 2. KURAL kartı.

## EK-8 (2026-11-05) ORB ara hüküm + VIX kombinasyonu ön kaydı
Görülen: (a) ayı geçti, (d),(e) geçti. **(b) eşleşik fark +0,057R P %85: ÖLÇÜT (P ≥ %90) TUTMADI.** Bu sonuç silinmez. Sorun: "aynı gün" kıyası, kırılımın olacağını baştan bilen günleri seçtiği için gelecek bilgisi taşır (DTS-02b'de de yanlı denmişti). Ek olarak iki bilgisi temiz taban: (b2) tüm günlerden aynı sayıda rastgele gün + rastgele bar (5.000 çekiliş). (b3) aynı gün, kırılım OLDUKTAN SONRAKİ rastgele bar (yalnız o anda bilinen bilgi). Hüküm (b)'yi de (b2-b3)'ü de birlikte yazar; (b) başarısızlığı raporda kalır.
Kombinasyon C1 = ORB uzun ∧ önceki gün VIX ≥ 18,4 (Defter K1 eşiği, burada seçilmedi; (f) yalnız birleşik 2024-26 görüldü, yıl/TF kırılımı görülmedi).
Sınama: yıl yıl 5m 2024/25/26, 15m 2023-26, 30m 2021-26. Geçer: 30m 2021-23 ve 2026 (5m) ayrı ayrı > 0, tüm birleşik P ≥ %95, VIX≥18,4 − VIX<18,4 farkı > 0 (ayrı P), rastgele long VIX≥18,4 tabanından iyi. Eşik duyarlılığı 15/18,4/20/25 yalnız rapor.

## EK-9 (2026-11-05) C1 geçti (EK-8 ölçütleri); kart + bağımsız ek sınamalar
Kural sabit. (i) 2. KURAL 6 ölçüt 5m 2024-26. (ii) NDX 1h 2016-06→2021-06, ilk tam saat OR (görülmemiş). (iii) Broker verisi bars_used 2026 (MT5/önbellek). (iv) Aktarım: DAX 15m, XAU/USOIL yalnız rapor (E92 ekseni XAU/USOIL'de bozuk). (v) Sıra/DD: yıllık işlem, en kötü seri, en büyük düşüş R, gün başına ≤1 işlem. (vi) bot_trades ile çakışma: aynı gün aynı yön canlı kaynaklar. Hiçbiri kuralı değiştirmez; (ii) negatif çıkarsa hüküm C'ye iner.

## EK-10 (2026-11-05) Makro aileleri kodu (`makro.py`), sonuç görülmeden; KEŞİF = 2025 (FJ arşivi 2025'te başlıyor), yalnız NDX. Öncül işaret: sıcak enflasyon/güçlü büyüme → NDX SELL. XAU/USOIL için olay-günü Dukascopy, NDX'te aday çıkarsa veya EIA için ayrıca.

## EK-11 (2026-11-05) S6/S8 Walter arşivi (FJ beklenmeden), NDX
S6 (haberli devam, habersiz söndür) ve S8 sözlüğü aynen; ilgili başlık düzeni makro.py REL. KEŞİF 2024-01→2025-12; kapalı 2026. Ek teşhis: şok başlangıcına göre ilk ilgili yeni başlığın zamanı (D3), plaseboya karşı. Haber yoğunluğu → sonraki 60 dk oynaklık (yalnız bilgi).

## EK-12 (2026-11-05) S6 haberli devam 60 dk keşifte geçti
n=408, +7,15 bp, P %99,4, yarılar +5,0/+9,3, stres +4,0, plasebo p 0,000, maxT 0,027.
Kural sabit: NDX 1m; 5 dk |getiri| ≥ 5× o UTC saatin 5 dk medyanı (medyan KEŞİF'ten sabit), 30 dk aralıklı, takvim ±30 dk dışında; son 10 dk içinde Walter'da REL başlığı; şok barından sonraki dakika, şok yönünde, 60 dk tut. Doğrulama 2026-02-08→06-30 (ort>0, P≥%80), Kör 07-01→11-04 (ort>0). Tek bakış. Sonra: FJ kaynağıyla bağımsız, XAU/USOIL M5, ters kol.

## EK-13 (2026-11-05, getiri görülmeden) Sürpriz ölçeği
Arşiv 2025'te başladığı için geçmiş std (12 gözlem) aylık verilerde kullanılamaz. Yerine önceden sabit birim: CPI/PPI/PCE/işsizlik 0,1 · NFP 40k · ADP 30k · başvuru 10k · ISM 1,0 · perakende 0,3 · GDP 0,3 · IFO 0,5 · ZEW 3 · FED/ECB faiz 0,25 · EIA/API 2M. z = (gerçek−beklenti)/birim. |z|≥1 sürpriz, |z|<0,5 sürprizsiz. Parite kapsamı başlık adlarından sayılır; aileler eşleşmeyen isimle genişletilirse eklenir (getiri bakılmadan).

## EK-14 (2026-11-05) Makro keşif sonucu: geçen hücre yok (n düşük: NDX 124, XAU 82, USOIL 81 olay)
İki iz: S4 NDX 60/240 (n=13), S1 USOIL 240 (n=9, EIA+API). 2026 (NDX 02-09+, XAU/USOIL 01-01+) açılır, S1-S5 hepsi rapor; ek iz seçilmez. S4 ve S1-USOIL için geçer: ort>0, P≥%80; birleşik n≥30, P≥%95.

## EK-15 (2026-11-05) Makro: NDX/XAU X. USOIL S5 karşıtı (görülerek türedi, post-hoc)
S5m: USOIL, ilk 5 dk tepki sürpriz öncülünün tersi → 5 dk sonra sürpriz yönünde gir. Aile EIA ham + API + büyüme verisi ayrı; 2025 / 2026 ayrı. Walter'dan EIA/API "est" başlıklarıyla 2024 bağımsız sınanır. n≥30 yoksa hüküm C. M1 2026-07+ ve spread ×2 stres.

## EK-16 (2026-11-05) D5 sonuç + H-HIZ ön kaydı (tick)
FJ gecikmesi p50 47 sn, p90 150 sn. Büyük sürprizde 1. dk 15 bp; öncül işaret uyumu CPI/PCE 100%. Görülerek türedi; ölçüt:
H-HIZ: resmi an t0 (BLS/BEA 08:30, ISM 10:00), yön = sürpriz öncülü, giriş t0+d (d = 0,5/1/2/5/10/20/30/47/60/120 sn) gerçek tick ask/bid, çıkış t0+60/120/300/900 sn gerçek bid/ask. Aile: Enflasyon (Core CPI MoM öncelikli, CPI MoM, Core PCE, PPI) ve İstihdam-Büyüme (NFP, başvuru, ISM, perakende). 2025 Dukascopy tick (spread gerçek). |z|≥1. Geçer: d=47'de bile > 0 ise mevcut hatla işlem; aksi halde 'gerekli azami gecikme' raporlanır. 2026 aynı kural, tick indirilirse.
