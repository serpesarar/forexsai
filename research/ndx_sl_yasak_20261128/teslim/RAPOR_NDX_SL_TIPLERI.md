# NASDAQ (NAS100) — SL ile kapanan işlem tiplerinin araştırması

**Tam rapor · 2026-11-28 · bağımsız inceleme için hazırlandı**

> Bu rapor kendi başına okunacak biçimde yazıldı. Tüm sayılar ekteki dosyalardan yeniden üretilebilir (§11).
> İnceleyen kişiden ya da modelden beklenen: yöntemdeki hataları, gözden kaçan SL tiplerini ve sınanabilir yeni
> hipotezleri bulmak (§10).

---

## 0. Özet (bir sayfa)

- **Soru:** Bugüne kadar hep "TP yapan" işlemleri aradık. Bu sefer SL ile kapanan işlemlerin ortak tiplerini (yanlış giriş
  yerleri, kötü koşullar) bulup kural olarak yasaklamak ve kâr marjını yükseltmek istiyoruz.
- **Ana bulgu:** Tek tek işlem düzeyinde SL **girişte tanınmıyor**. Bir kural SL'lerin %X'ini engelliyorsa TP'lerin de
  yaklaşık %X'ini kesiyor. Bu oturumda bu ilişkinin korelasyonu **0,98** çıktı; önceki 9 yıllık çalışmada **0,996**
  çıkmıştı. Projede bu dördüncü bağımsız teyit.
- **Tanınan tek düzey aile×yön.** Canlı kitapta üç tip SL üretip kâr getirmiyor: **NDX MOMSR BUY, CHREV BUY, VIXREG SELL**.
  Birlikte 244 karar, SL oranı %43, toplam +327 $, buna karşılık 132.897 $ risk taşıyorlar.
- **Geriye dönük etki (örneklem içi):** bu üç tip çıkarılırsa SL sayısı 168'den 63'e iniyor, kâr/risk %13,3'ten %23,1'e
  çıkıyor, ortalama R +0,076'dan +0,171'e çıkıyor, net $ neredeyse aynı kalıyor (−326 $). En kötü gün ve en derin düşüş
  değişmiyor.
- **Durum:** Yasak kodda var ama **GÖLGE** modunda: engellemiyor, yalnız "burayı engellerdim" diye kaydediyor. Kullanıcı
  kararı: canlıya almadan önce geliştirilecek.
- **Sınanıp elenenler:** dar stop (tersine çıktı), zarardaki pozisyonun üstüne ekleme (en güçlü iz ama ölçüt dışı),
  aynı yönde açık pozisyon, günde 2 SL'den sonra devam etmek, kovalama, FOMC / CPI / NFP günleri (FOMC tersine çıktı).

---

## 1. Sistem bağlamı

- **Enstrüman:** NAS100 CFD (Pepperstone demo, MT5). Tüm saatler UTC; broker saatinden fiyat eşleştirmesiyle hizalandı.
- **Canlı bot ailesi** (magic numarasıyla ayrılıyor):

| Aile | Ne yapar | Braket |
|---|---|---|
| DAYCOMBO (DC) | Güçlü 5m mum + probasyon sonrası BUY | TP 80 / SL 110 puan; 2026-11-23'ten beri oynaklığa göre SL = max(110, 2,5×ATR5), lot eşit $ risk |
| REENTRY (RE) | DC TP'sinden 5 dk, SL'sinden 1 dk sonra aynı yönde yeniden giriş | DC ile aynı |
| VIXREG | VIX ≥ 18,4 → BUY lehte, altı → SELL; model oyları teyit | TP 80, SL 2×ATR (60–200) |
| MOMSR | Momentum/SR, panel modellerinin oyu | Değişken |
| CHREV | Trend kanalı kenarından ortalamaya dönüş | Değişken |
| DECIDER | LLM tabanlı karar ajanı, ≤ 0,03 lot | Kendi braketi |
| C3B / KSG / CAPREV / ORBVIX / ÇEKİÇ | Zaman çıkışlı kurallar (gece/gün tutma) | Acil SL |

- **R tanımı:** karar net $ / karar ilk risk $ (|giriş − ilk SL| × lot × puan değeri). DC/RE'de TP = +0,727R, SL = −1R;
  başabaş isabet oranı %57,9.

---

## 2. Daha önce ne denendi (aynı soru bu projede 4. kez soruluyor)

| ID | Tarih | Ne denendi | Sonuç |
|---|---|---|---|
| IO-02 | 10-07 | SL mekanizmaları bota özgü mü (yön doğru / hiç çalışmadı / neredeyse TP / yön yanlış) | Rastgele girişlerle aynı dağılım: mekanizmalar braketin doğası |
| IO-03 | 10-07 | SL'ye giderken hacim düşüyor/artıyor mu (12 ölçü) | Ayırmıyor |
| IO-04 | 10-07 | "Kötü bağlam" bayrakları: 1h ters trend, kovalama, MTF çelişki, kayıp sonrası tekrar, VIX karşıtı, aralık ucu | SL oranı farkı 0…−3 puan |
| IO-11 | 10-07 | Kaba kuvvet: 4.104 tekli/ikili veto, kronolojik bölme | Eğitim ↔ sınama Spearman ≈ 0; eğitimde +16R olan kural sınamada −12R |
| IO-17 | 10-09 | −0,5R'ye inen işlem döner mi, SL mi olur (hacim/gösterge dinamiği) | AUC 0,50–0,59 |
| IO-18/20 | 10-09/10 | Sembol-yön başına ≈ 100 özellik, SL kümeleme, benzer-işlem kNN | Yalnız "NDX SELL düşüşü kovalama" çıktı; sağlamlık turunda seçim düzeltmeli p = 0,57 |
| IO-26 | 10-29 | Donmuş adayların ileri dönem sınaması + lojistik model | RSI diverjansı ve kovalama **tersine döndü**; model AUC 0,73 (içi) → 0,496 (ileri) |
| SL-01…07 | 11-23 | DC+RE, Dukascopy 1m 2018–2026, 41 aday / 9 aile | SL-engel % ↔ TP-kayıp % korelasyonu **0,996**; canlı gecikme (≈1 dk) tabanında hiçbir aday kalmadı |
| SL-08 | 11-23 | Oynaklığa göre braket + eşit $ risk | Kart 6/6, plasebo p = 0,000 → **canlıda**. SL'yi tanımıyor; oynak günün gürültü SL'sini azaltıyor |
| IO-29 Y2 | 11-12 | Başka ailenin zarardaki pozisyonunun üstüne ekleme | −0,157R vs +0,003R, P 0,87 → C, gölgede |

**Bu oturumda yeni olan:** (1) 10-10 → 11-26 arası canlı veri, önceki SL çalışmalarının hiçbirinde görülmedi.
(2) Arama tek bir ailede değil, tüm canlı NDX kitabında, aile tabakalı yapıldı. (3) DC/RE için makro olay günü
ilk kez sınandı. (4) Kullanıcının ölçüsü (engellenen SL % − kaybedilen TP %) her aday için zorunlu tutuldu.

---

## 3. Veri

| Set | Kaynak | Dönem | Birim | n |
|---|---|---|---|---|
| **Canlı** | Supabase `bot_trades` (gerçek MT5 kapanışları), broker 1m `indicator_snapshots` | 2026-06-30 → 11-26 | karar (aynı aile+yön, 2 dk içindeki bacaklar birleşik) | 452 karar (21 bacak hizalanamadı, dışlandı; kesin hizalama %95) |
| **Replay** | Dukascopy + broker 1m, DC+RE canlı kuralının birebir taklidi (TD-01 motoru) | 2018-04 → 2026-11-20 | işlem | 3.517 |
| **Takvim** | FOMC / CPI / NFP saatleri | 2008 → 2027 | olay | 654 |

**Dönem bölmesi (canlı):** ÖN < 2026-10-10 (CK-01 kartından önce) · İLERİ ≥ 10-10 · İLERİ-2 ≥ 10-30 (IO-26'dan sonra).

---

## 4. Yöntem (ön kayıt — eşikler sonuçlardan ÖNCE yazıldı, `PROTOCOL.md`)

**A. Aile/yön yasağı:** her aile×yön (≥ 30 karar) için. Yasak ancak şunların hepsi tutarsa önerilecekti:
ort R < 0, gün-blok bootstrap P(EV<0) ≥ %80, ÖN ve İLERİ dönemlerin ikisinde de ort R ≤ 0, $ toplamı < 0.

**B. İşlem tipi bayrakları** (girişte bilinen bilgiyle, mekanizmadan türetildi):

| Bayrak | Tanım | Neden |
|---|---|---|
| B1 dar stop | SL puanı / (ATR14(1m)·√30) < 0,5 | 11-23 vakası: SL, 30 dk'lık beklenen hareketin yarısından küçüktü |
| B2 Y2 | Aynı yönde açık başka NDX pozisyonu var VE o pozisyon girişte zararda | IO-29 |
| B3 Y1 | Aynı yönde açık başka NDX pozisyonu var | Yığılma |
| B4 kötü gün | Aynı UTC gününde girişten önce kapanmış ≥ 2 SL kararı | "Kötü günde dur" sezgisi |
| B5 kovalama | Son 60 dk hareket işlem yönünde ≥ 1,5×ATR14(5m) | IO-18/29 |

Ölçütler (hepsi tutmalıydı):
- Δ = bayraklı − bayraksız ort R, aile×yön içinde hesaplanıp ağırlıklandırıldı (tabakalı)
- bayraklı n ≥ 20; gün-blok bootstrap P(Δ<0) ≥ %90
- ÖN ve İLERİ dönemlerin ikisinde de Δ < 0
- **engellenen SL % − kaybedilen TP % ≥ 10 puan**
- Holm düzeltmesi (5 bayrak)
- Plasebo: bayrak dizisi aile×yön içinde dairesel kaydırıldı (×1000)

**EK-1. Makro olay günü** (A/B sonuçlarından sonra, olay sonuçlarına bakmadan eklendi), replay 9 yıl:
- Bayraklar: E1 FOMC günü · E2 FOMC'den 120 dk önce → 60 dk sonra · E3 CPI ya da NFP günü · E4 herhangi biri
- Ölçütler: bayraklı n ≥ 40; bayraklı ort R < 0 ve kalan ort R tabandan yüksek; P ≥ %90; üç çağın üçünde de eksi
  (2018–20 / 2021–23 / 2024–26); SL oranı tabandan ≥ 10 puan yüksek; plasebo (aynı sayıda olaysız gün, haftanın günü
  eşli) yüzdeliği ≤ %5.

---

## 5. Sonuç A — Aile/yön karnesi (canlı, 452 karar)

| Aile·yön | Karar | SL | SL % | Ort R | Net $ | Risk $ | ÖN R | İLERİ R | Son işlem |
|---|---|---|---|---|---|---|---|---|---|
| DAYCOMBO BUY | 48 | 14 | 29,2 | **+0,222** | +12.266 | 81.884 | +0,281 | +0,114 (17) | 11-26 |
| REENTRY BUY | 23 | 5 | 21,7 | **+0,347** | +20.496 | 67.496 | +0,516 | +0,238 (14) | 11-11 |
| REENTRY SELL | 14 | 2 | 14,3 | +0,481 | +6.102 | 11.010 | +0,382 | +0,727 (4) | 11-12 |
| DECIDER SELL | 100 | 35 | 35,0 | +0,085 | +37 | 526 | +0,042 | +0,088 (92) | 11-19 |
| **VIXREG SELL** | **210** | **91** | **43,3** | **+0,003** | **+454** | **112.660** | −0,000 | +0,166 (4) | 11-12 |
| **MOMSR BUY** | **21** | **8** | **38,1** | **−0,040** | **+382** | **13.079** | −0,040 | — | 07-31 |
| **CHREV BUY** | **13** | **6** | **46,2** | **−0,071** | **−505** | **7.155** | −0,071 | — | 07-15 |
| CHREV SELL | 15 | 6 | 40,0 | +0,035 | +685 | 8.820 | +0,035 | — | 09-29 |
| VIXREG BUY | 3 | 0 | 0 | +0,712 | +1.176 | 1.650 | | | 07-20 |
| Diğer (CAPREV, ÇEKİÇ, KSG, MANUEL) | 5 | 1 | | | | | | | |
| **Toplam** | **452** | **168** | 37,2 | +0,076 | +40.964 | 308.773 | | | |

**Yorum.**
- Ön kayıtlı yasak ölçütünü hiçbir aile tam tutmadı. MOMSR BUY ve CHREV BUY eksi, ama n < 30 ve ikisi de Temmuz'dan beri
  işlem açmıyor.
- VIXREG SELL tam anlamıyla "kenarsız". 210 kararda ortalama +0,003R ile başabaşta, ama kitabın en büyük riskini
  (%36) ve SL'lerin yarısından fazlasını (91/168) üretiyor.
- Kâr DAYCOMBO + REENTRY'den geliyor (+38.864 $, NDX netinin %95'i).
- SL'lerin aileye dağılımı: VIXREG SELL 91, DECIDER SELL 35, DAYCOMBO 14, CHREV 12, MOMSR 8, REENTRY 7, ÇEKİÇ 1.

---

## 6. Sonuç B — İşlem tipi bayrakları (canlı, aile tabakalı)

| Bayrak | n | R bayraklı | R diğer | Δ tabakalı | ÖN / İLERİ / İLERİ-2 Δ | SL engel % | TP kayıp % | P(Δ<0) | Plasebo yüzdelik | Holm p | Hüküm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B1 dar stop | 47 | +0,240 | +0,057 | **+0,246** | +0,34 / +0,13 / +0,31 | 8,3 | 11,9 | 0,04 | 0,98 | 0,97 | **X, tersine** |
| B2 Y2 | 23 | −0,199 | +0,091 | **−0,352** | −0,25 / −0,76 / −0,65 | 7,7 | 3,6 | 0,92 | **0,025** | 0,39 | **C** (ölçüt dışı) |
| B3 Y1 | 40 | +0,098 | +0,074 | −0,072 | −0,13 / +0,20 / +0,35 | 8,9 | 8,6 | 0,61 | 0,28 | 1,00 | X |
| B4 kötü gün | 181 | +0,078 | +0,075 | +0,084 | +0,14 / −0,18 / −0,20 | 41,7 | 39,9 | 0,17 | 0,82 | 1,00 | X |
| B5 kovalama | 139 | +0,044 | +0,090 | −0,098 | −0,10 / −0,18 / −0,16 | 32,7 | 29,9 | 0,87 | 0,15 | 0,51 | X |

**Kullanıcı ölçüsü:** beş bayrağın (SL engel %, TP kayıp %) noktaları arasında korelasyon **0,98**. Engellenen SL ile
kaybedilen TP arasındaki en iyi fark 4 puan (B2); hedef ≥ 10 puandı.

**B2 (Y2) neden yasaklanmadı?**
- 23 olayın 18'i Temmuz–Eylül'de CHREV SELL ile VIXREG SELL'in aynı fikri birkaç dakika arayla açmasından geliyor; bu iki
  aile artık işlem açmıyor.
- Kalan 5 olayın 3'ü DAYCOMBO (2 SL / 1 TP). Önceki çalışmada (IO-21) DAYCOMBO'nun 315 işlemlik geçmişinde "üst üste
  açılan" işlemler **+0,198R** çıkmıştı, yani ters yönde.
- Kutudaki Y2 gölge karnesinde 11-12'den beri **0 olay** var.
- Sonuç: gerçek bir etki olabilir, ama ileri dönemi taşıyacak popülasyon kalmadı.

**B1 neden önemli?** "SL çok dar, gürültüde vuruldu" sezgisi canlı kitapta tersine çalıştı: dar stoplu işlemler daha iyi
sonuç verdi. Bu, SL-08'in bulgusuyla tutarlı: oynaklık braketi SL'yi tanıdığı için değil, $ salınımını azalttığı için
işe yarıyor.

---

## 7. Sonuç EK-1 — Makro olay günü (replay, DC+RE 9 yıl; taban +0,034R / SL %39,9)

| Bayrak | n (gün) | Ort R | SL % | P(ortR<0) | Plasebo yüzdelik | 2018–20 / 2021–23 / 2024–26 | Hüküm |
|---|---|---|---|---|---|---|---|
| E1 FOMC günü | 204 (39) | **+0,081** | 37,3 | 0,09 | 0,58 | +0,17 / +0,02 / +0,09 | X, **tersine** |
| E2 FOMC −120…+60 dk | 108 (35) | +0,101 | 36,1 | 0,10 | 0,66 | +0,04 / +0,10 / +0,16 | X |
| E3 CPI/NFP günü | 241 (56) | −0,024 | 43,2 | 0,66 | 0,19 | +0,02 / **−0,13** / +0,06 | X (yalnız tek çağ eksi) |
| E4 herhangi | 431 (92) | +0,021 | 40,6 | 0,33 | 0,27 | +0,09 / −0,06 / +0,07 | X |

Not: replay tabanında giriş sinyalden hemen sonra (lag 0), canlıda yaklaşık 1 dk sonra. Gün düzeyindeki bir vetoda bu
farkın sonucu değiştirmemesi beklenir, ama doğrulanmadı.

---

## 8. Yasak adayı ve geriye dönük etkisi

**B22 — SL tipi yasağı (aday):** NDX'te MOMSR BUY, CHREV BUY ve VIXREG SELL açılmasın.

| | Karar | SL | Net $ | Risk $ | **Kâr/risk** | Ort R | İsabet | Maks. düşüş | En kötü gün | Günlük SR |
|---|---|---|---|---|---|---|---|---|---|---|
| Şu anki hâl | 452 | 168 | +40.964 | 308.773 | %13,3 | +0,076 | %61,5 | −18.092 | −8.628 | 0,167 |
| Yasakla | 208 | **63** | +40.638 | 175.876 | **%23,1** | **+0,171** | %69,2 | −18.892 | −8.628 | 0,189 |

**Uyarılar:**
- Bu hesap **örneklem içi**: yasak listesi aynı verinin üstünden seçildi.
- Net $ neredeyse aynı kalıyor. "Kâr marjı" artışı aynı kârın daha az riskle elde edilmesinden geliyor; boşalan riski
  kanıtlı ailelere aktarmak ayrı bir lot kararı.
- En kötü gün ve en derin düşüş değişmiyor. Bunlar DAYCOMBO/REENTRY'nin 30 lotluk günlerinden geliyor (örnek: 2026-10-19,
  −8.628 $).
- MOMSR BUY ve CHREV BUY zaten işlem açmıyor; pratikte yasağın tek etkisi VIXREG SELL üzerinde.

**Koddaki durum:**
- `yeni deneme/phase_rules.py` → `SL_TYPE_BAN_ENABLED=True`, `SL_TYPE_BAN_BLOCK=False` (**GÖLGE**), `SL_TYPE_BAN` listesi.
- Bot `_sl_type_ban_blocks()` üç giriş noktasında çağrılıyor: momentum, CHREV, VIXREG.
- Gölgede her aday giriş `gate_skipped.jsonl`'e `reason=sl_type_ban, shadow=true` olarak yazılıyor.
- Commit'ler: 6ae71ae4 (yasak), 2d453c0c (rapor), 4961c66b (gölgeye alma).

---

## 9. Sınırlar ve bilinen tuzaklar

1. **Küçük n:** MOMSR BUY 21, CHREV BUY 13. Tek başına anlamlılık yok.
2. **Popülasyon değişti:** İLERİ dönemde kitabın %80'inden fazlası DECIDER ve DC/RE. VIXREG/MOMSR/CHREV ileri dönemde
   neredeyse yok, dolayısıyla aile hükümleri ağırlıkla ÖN döneme dayanıyor.
3. **Seçim yükü:** aynı NDX geçmişine bu projede çok kez bakıldı. Bootstrap p değerleri bu yükü temizlemez; bağımsız
   piyasa ya da ileri dönem gerekir.
4. **Hizalama:** 21 bacak saat ekseni eşleştirilemediği için dışlandı. Broker saati UTC değil (UTC+2/+3).
5. **Sorgu tuzağı (bu oturumda yakalandı):** `normalized_symbol ILIKE '%NDX%'` filtresi `GDAXI.INDX`'i de yakalıyor.
   DAX işlemleri NDX sanılabilir. Analiz `symbol == 'NDX.INDX'` ile yapıldı, doğru.
6. **Kâğıt ↔ gerçek icra:** R gerçek dolum fiyatıyla hesaplandı; spread ve kayma içinde.
7. **Replay lag 0:** EK-1 tabanı canlıdan yaklaşık 1 dk erken giriyor.

---

## 10. İnceleyen için açık sorular ve sınanmamış ipuçları

**Gözden geçirilmesi istenenler:**
- Aile tabakalı Δ ve plasebo (aile×yön içinde dairesel kaydırma) bu veri için doğru boş hipotez mi?
- Karar birleştirmesi (2 dk) Y1/Y2 bayraklarını yapay biçimde etkiliyor mu?
- "SL-engel % ≈ TP-kayıp %" sınırı bu stratejiler için yapısal mı (rastgele yürüyüşte sabit braket), yoksa doğru bilgi
  sınıfını mı arayamadık?

**Sınanmamış ipuçları (sonradan görüldü — ön kayıt olmadan KANIT DEĞİL):**
- Giriş saatine göre canlı ortalama R: 15 UTC −0,141 (n 50), 23 UTC −0,303 (n 17), 03 UTC −0,163 (n 8), 12–14 UTC
  +0,23…+0,51. 24 saat arasından seçildiği için çoklu karşılaştırma riski çok yüksek; daha önce NDX'te koşulsuz saat yönü
  "X" çıkmıştı (SD-01). Aile içi ve ileri dönemde ölçülmeli.
- VIXREG SELL'in SL'leri belirli bir VIX bandında ya da trend rejiminde yoğunlaşıyor mu? (IO-15: düşüş aylarında VIXREG
  BUY kötüydü; SELL tarafı ayrıca sınanmadı.)
- DECIDER SELL: 100 kararda +0,085R. Lot küçük olduğu için $ etkisi yok; bu aile büyütülürse SL tipleri ayrıca sınanmalı.

**Yeni bilgi sınıfı önerileri (bizde yok ya da zayıf):** emir defteri / derinlik, opsiyon akışı (gamma, 0DTE), haber
saniyesi, NQ vadeli ile CFD arasındaki baz farkı.

---

## 11. Dosyalar

| Dosya | İçerik |
|---|---|
| `NDX_SL_tipleri_islem_listesi.xlsx` | Sayfalar: Ozet_aile_yon · Canli_kararlar_452 · Yasak_adaylari_244 · Tum_SL_kararlari (168) · Replay_9yil_DC_RE (3.517) |
| `canli_ndx_kararlar_452.csv` | Canlı kararlar + tüm bayraklar + `yasak_adayi_B22` |
| `replay_9yil_daycombo_reentry.csv` | 9 yıllık DC+RE replay + FOMC / CPI-NFP etiketleri |
| `../PROTOCOL.md` | Ön kayıt (A, B, EK-1) |
| `../RAPOR.md` | Çalışma raporu (defter biçimi) |
| `../src/sy.py`, `../src/ek1_olay.py` | Analiz kodu |
| `../results/sonuc.json`, `../results/ek1_olay.json` | Ham sonuçlar |

**Liste sütunları (canlı):**
- `giris_utc` / `cikis_utc` · `aile` · `yon` · `bacak` · `giris_fiyati` · `sl_mesafesi_puan`
- `sonuc`: SL = R ≤ −0,7 · TP/kâr = R > 0 · başabaş/küçük zarar
- `R` · `net_usd` · `risk_usd` · `donem`
- `B1…B5` bayrakları · `yasak_adayi_B22`
