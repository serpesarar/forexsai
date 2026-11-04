# Decider XAUUSD — ön-kayıtlı giriş kuralları × TP/SL geometrisi (DX-02, 2026-10-15)

> Kapsam: decider'ın kendi XAU kararlarına (DX-01 analiz kümesi: BUY 595 / SELL 81 bağımsızlaştırılmış OPEN) uygulanan
> 8 mekanizma-temelli kural × 3 önceden seçilmiş geometri. Web araması yok; kaynaklar yereldeki kod, veri ve sonuç dosyaları.
> Kod + sonuçlar: `/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/`
> (`PROTOCOL.md` ön-kayıt, `01_features.py` → `02_simulate.py` → `03_evaluate.py` → `04_selection_and_explore.py` → `05_reality_check.py`; ham çıktılar `results/`).
> R = pnl / SL mesafesi, spread girişte (BUY'da ask), giriş = karar ts'den sonraki ilk 1m açılışı (68 icra dahil herkes için aynı taban).

## 1. Ön-kayıt: hangi kurallar, hangi mekanizma, sızıntı denetimi

### Takeaway
8 kural, 3 geometri ve 7 geçme ölçütü **2026-10-15 04:41 UTC'de, hiçbir kural sonucu hesaplanmadan** `PROTOCOL.md`'ye donduruldu. Ön-kayıt öncesinde yalnız özellik dağılımlarına bakıldı. Bar-tabanlı özelliklerde sızıntı ihlali 0/900, önek testi farkı 0/200. Defter §0 kontrolüne göre bu çalışma IO-12'nin (decider gösterge-eşik araması) **yeniden açılması** sayılır. Gerekçeler: dürüst 1m broker simülasyonu, 3 geometri, 8 kuralla sınırlı mekanizma seti, aynı-gün tetik kontrolü ve D2 için 09-14 sonrası örneklem-dışı dilim.

### Cited Findings
- Ön-kayıt metni, kural tanımları, eşikler, geometriler (G1 TP1,0/SL1,5×ATR5 mevcut; G2 TP1,25/SL0,75 DX-01'in post-hoc adayı; G3 TP3,0/SL1,5 + 120 dk zaman çıkışı), kontroller (C1 rastgele alt küme ×4.000; C2 aynı UTC dakikası ±10 gün rastgele zaman ×300; C3 tetik popülasyonu) ve verdikt şeması (A/B/C/RED) — [PROTOCOL.md](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/PROTOCOL.md)
- **Kurallar** (BUY tanımı; SELL'de aynası):

| ID | Kural | Dayandığı kanıt |
|---|---|---|
| R1 | 5m baskın aşırılık (channel_z / vwap_z) **yukarı** (güç/kırılım) | XAU kenarı gücü almak (günlük swing'de "dip 2. giriş reddedildi", MK-04) |
| R2 | D2 engellemiyor (`entry_quality.assess`) | bıçak + hacim patlaması |
| R3 | 1h kapanış > EMA50 | — |
| R4 | günlük kapanış > SMA10 | — |
| R5 | 07–16 UTC | — |
| R6 | ATR5 / 24 s medyan < 1,5 | — |
| R7 | 20 saatlik tepeye ≤ 1×ATR1h | — |
| R8 | size_factor ≥ 0,20 (lot ≥ 0,02) | — |

  — [PROTOCOL.md](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/PROTOCOL.md), [rules_lib.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/rules_lib.py)
- **Özellik dağılımı** (sonuçsuz, ön-kayıt öncesi), BUY n=595:
  - güç tetiği 271 / dip 318; D2 bloklu 114; 1h-EMA50 üstü 262; günlük yukarı 286.
  - 07–16 UTC 264; ATR oranı ≥1,5 71; 20 s tepeye ≤1 ATR 116; size ≥0,2 291.
  - Aylar: Haz 6, Tem 165, Ağu 111, Eyl 115, Eki 198. SELL n=81 / 12 gün, 69'u Temmuz.

  — [results/01_feature_marginals.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/01_feature_marginals.txt)
- **Sızıntı denetimi:**
  - Bar özellikleri yalnız `t_end ≤ ts` barlardan alındı; 900 örnekte ihlal 0.
  - Önek testinde 1m seri ts'de kesilip özellikler yeniden hesaplandı; 40 kayıt × 5 özellikte fark 0.
  - Journal'ın `multi_tf` ve `forensics` alanları karar öncesi anlık görüntüler.
  - D2 için decider'ın kendi `entry_quality.assess` fonksiyonu import edildi (birebir tanım).

  — [results/01_feature_marginals.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/01_feature_marginals.txt), [claude_decider/entry_quality.py](/Users/melihcanodacioglu/Desktop/panel/claude_decider/entry_quality.py)
- Defterde örtüşen önceki işler:
  - IO-12 (2026-10-08): decider sembol başına gösterge-eşik araması. "Gerçek 138 vs plasebo medyan 142 → gösterge-eşik kuralı YOK"; XAU BUY seçim değeri +0,20R (OPEN +0,06 vs WAIT-cf −0,14).
  - D2: chz_dir ≥ 2,0 veya vol ≥ 1,5, GÖLGE, A− (decider'da).
  - DX-01: geometri hücrelerinin hiçbiri Bonferroni'den geçmiyor.

  — [docs/KAPI_KAYIT_DEFTERI.md](/Users/melihcanodacioglu/Desktop/panel/docs/KAPI_KAYIT_DEFTERI.md) (satır 107, 218, 226), [research/decider_kural_20261008/SONUC.md](/Users/melihcanodacioglu/Desktop/panel/research/decider_kural_20261008/SONUC.md)
- **Taban doğrulaması:** ortak giriş tabanıyla BUY G1 −0,001R; DX-01'deki orijinal-geometri değeri +0,003. G2 +0,063; DX-01'de +0,072 (fark icra dolumu tabanından). — [results/03_evaluate.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/03_evaluate.txt), [tpsl_karsi_olgu.md](/Users/melihcanodacioglu/Desktop/panel/research_notes/Decider%20XAUUSD%20TPSL%20ve%20giri%C5%9F%20kurallar%C4%B1/tpsl_karsi_olgu.md)

### Inferences
- Ön-kayıt gerçek, ama veri bağımsız değil (E23): aynı 595 karara DX-01 ve IO-12 ile en az 3. kez bakılıyor. G2 geometrisi bu verinin sonuçlarından seçildi. Bu yüzden B'nin üstündeki hiçbir hüküm bu veriden çıkamaz.
- R5–R7 eşikleri yuvarlak/önceden var olan değerler. R1'in "işaret" tanımı eşiksiz. Eşik seçimi kaynaklı serbestlik düşük.

### Gaps
- Kutu çevrimdışı. 10-14 06:57 UTC sonrasında karar ve bar yok; bağımsız ileri dönem bu çalışmada mevcut değil.
- `multi_tf` alanlarının kutuda tam olarak hangi bar kesitinde (koşan bar dahil mi) hesaplandığı bu turda kodla doğrulanmadı. Bunlar karar öncesi değerler olduğu için sızıntı yaratmaz, ancak placebo/C3 ile birebir yeniden üretilemez.

## 2. BUY: kural × geometri sonuçları ve verdiktler

### Takeaway
**A sınıfı kural yok. Bu veriyle hiçbir kural decider'ın XAU BUY'larını güvenle kârlı yapmıyor.**
- Ön-kayıt şemasına göre tek **B**: R1 (güç-tetikli BUY) × G2. +0,151R [−0,001, +0,299], P %97, n=271 / 30 gün, gerçek lotla +0,94$/işlem.
- Ancak üç zaafı var:
  1. Aile-bazlı seçim düzeltmesini geçmiyor (p_FW 0,67, RC p 0,22, t 1,94 < Bonferroni 2,87).
  2. Kronolojik ikinci yarısı ≈0 (+0,007).
  3. Kural, G1'de RED (yarılar +0,14 / −0,07).
- Keşif dökümünde etki büyük ölçüde Temmuz'a ve G2 geometrisine bağlı. Pratikte C kalitesinde bir gölge adayı.
- G2'deki diğer 7 satır (R2–R8) **C**: P<0,90 ve/veya C1<%90 ve/veya +1 dk gecikmede EV'nin yarısından fazlası kayboluyor. G1'de R4 ve R8 C, gerisi RED. G3'te (geniş TP + zaman çıkışı) 8 kuralın 8'i RED.

### Cited Findings
**Kural × geometri tablosu (BUY)**

Hücre okuma sırası:
- EV R [%95 gün-blok],
- P(EV>0) · kronolojik yarılar,
- C1 / C2 plasebo yüzdeliği,
- +1 dk gecikmede EV,
- gerçek lotla $/işlem (lot = 0,10×min(size, 0,3)),
- verdikt.

Başabaş WR: G1 %60, G2 %37,5.

| Kural | n / gün | G1 TP1,0/SL1,5 | G2 TP1,25/SL0,75 | G3 TP3/SL1,5 + 120 dk |
|---|---|---|---|---|
| TABAN (kuralsız) | 595/35 | −0,001 [−0,08, +0,07] P0,49 · +0,02/−0,03 · C2 87 · +1 dk +0,009 · +0,41$ | +0,063 [−0,06, +0,19] P0,84 · +0,02/+0,11 · C2 100 · +1 dk +0,013 · +0,52$ | −0,044 [−0,19, +0,10] P0,28 · −0,13/+0,05 · C2 53 · +1 dk −0,038 · +0,06$ |
| R1 güç tetiği | 271/30 | +0,033 [−0,07, +0,12] P0,76 · +0,14/−0,07 · C1 83 C2 95 · +0,058 · +0,74$ → **RED** | **+0,151 [−0,00, +0,30] P0,97 · +0,29/+0,01 · C1 93 C2 100 · +0,092 · +0,94$ → B** | +0,006 · P0,51 · +0,03/−0,02 → **RED** |
| R2 D2-temiz | 475/33 | +0,019 · P0,68 · +0,08/−0,04 · C1 88 C2 98 → **RED** | +0,068 [−0,06, +0,21] P0,85 · +0,10/+0,03 · C1 56 C2 100 · +0,044 → **C** | −0,044 → **RED** |
| R3 1h > EMA50 | 262/26 | +0,005 · +0,04/−0,03 → **RED** | +0,109 [−0,08, +0,29] P0,88 · +0,14/+0,08 · C1 76 C2 99 · +0,018 · +1,30$ → **C** | −0,089 → **RED** |
| R4 günlük yukarı | 286/18 | +0,023 [−0,05, +0,10] P0,73 · +0,03/+0,02 · C1 76 C2 78 → **C** | +0,028 · P0,63 · C1 26 → **C** | −0,151 P0,07 · C1 3 C2 6 → **RED** |
| R5 07–16 UTC | 264/27 | +0,029 · +0,07/−0,02 → **RED** | +0,030 · P0,64 · C1 28 → **C** | −0,077 → **RED** |
| R6 oynaklık patlaması yok | 524/35 | −0,012 · P0,36 → **RED** | +0,055 · P0,78 · C1 30 · +1 dk −0,013 → **C** | −0,067 → **RED** |
| R7 20 s tepeye yakın | 116/23 | −0,052 · +0,06/−0,17 → **RED** | +0,195 [−0,07, +0,40] P0,93 · +0,33/+0,06 · C1 87 C2 100 · +1 dk +0,034 · +1,42$ → **C** | −0,072 → **RED** |
| R8 size ≥0,2 | 291/35 | +0,022 · P0,67 · +0,00/+0,04 · C1 77 → **C** | +0,038 · P0,65 · C1 31 · +1 dk −0,047 → **C** | −0,074 → **RED** |

— [results/rules_table.csv](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/rules_table.csv), [results/03_evaluate.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/03_evaluate.txt)

**R1 × G2 ayrıntısı** (tek B)
- WR %43,2 vs başabaş %37,5.
- Stres testleri: spread ×1,5 → +0,132; tek pozisyon → +0,125 (n=237); +1 dk gecikme → +0,092 (kayıp %39, ölçüt 5 geçer).
- Tamamlayıcı küme (dip BUY'ları, n=324): −0,010.
- Gerçek lotla toplam +254$ (271 karar).
- Seçim düzeltmeli permütasyon (24 test): z +1,55, p_FW 0,67.
- Mutlak EV için ortak gün-blok max-t: t 1,94, RC p 0,22. Bonferroni z*(24) = 2,87, z*(48) = 3,08.
- C3 tetik popülasyonunda (decider'ın açmadığı 976 danışma, BUY simüle): güç −0,097 vs dip −0,125 (aynı işaret, +0,03). G1'de ters işaret: −0,131 vs −0,093.

— [results/03_evaluate.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/03_evaluate.txt), [results/05_reality_check.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/05_reality_check.txt)

**Keşif dökümü** (ön-kayıt sonrası; verdikt almaz)

R1 güç vs dip, aylara göre (G1 / G2):

| Ay | Güç (n, G1 / G2) | Dip (n, G1 / G2) |
|---|---|---|
| Tem | 67: +0,119 / +0,154 | 98: −0,150 / −0,238 |
| Ağu | 47: +0,064 / +0,362 | 64: +0,172 / +0,167 |
| Eyl | 61: +0,011 / +0,180 | 54: +0,111 / +0,136 |
| Eki | 96: −0,028 / +0,028 | 102: −0,093 / +0,052 |

- G1'de güç Ağustos ve Eylül'de dipten kötü. G2'de Ekim'de ters.
- Ekim demo icraları: güç 36 işlem +0,157 / +0,407, dip 32 işlem −0,062 / +0,083 (küçük n). — [results/04_selection_explore.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/04_selection_explore.txt)

**R2 (D2), 09-14 donmasından SONRA** (D2 için örneklem-dışı; n=198, 9 gün)
- D2-temiz vs D2-blok: G1 −0,055 (n=156) vs −0,087 (n=42); G2 +0,013 vs **+0,143**; G3 −0,097 vs **+0,056**.
- Öncesi (D2'nin kendi örneklemi): G1 +0,055 vs −0,051.

D2'nin XAU'daki etkisi örneklem-dışında tekrarlanmıyor (G2/G3'te ters). — [results/04_selection_explore.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/04_selection_explore.txt)

**R7 (tepeye yakın), aylara göre G2:**
- Decider BUY: Tem −0,030 vs −0,082; Ağu +0,244 vs +0,251; Eyl +0,212 vs +0,138; Eki +0,206 vs −0,004.
- C3 açılmamış danışmalar: Tem +, Ağu −, Eyl +, Eki − (yakın − uzak).

Bu karışık tablo bir mekanizma imzası değil. — [results/04_selection_explore.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/04_selection_explore.txt)

### Inferences
- "Güçlü aşırılıkta al, dipte alma" (R1) XAU'nun kanıtlı mekanizmasıyla (gücü al) aynı yönde. Kural Temmuz'da çok belirgin (dip BUY'lar −0,15 / −0,24R). Ama Ağustos–Eylül'de G1'de tersine dönüyor ve aile-bazlı düzeltmeden geçmiyor. Bu, E24 örüntüsü: "kazancın çoğu tek ay". Ön-kayıt verdikti B; kanıtın içeriği C. **Varsayılan kural yapma, yalnız gölge `policy_*` notu.**
- Kuralların neredeyse tamamı yalnız G2'de pozitif. Pozitifliğin büyük kısmı kuralın değil G2 geometrisinin (+0,063 taban), G2'nin kendisi de DX-01'de post-hoc seçildi. G1'de (mevcut geometri) hiçbir kural +0,035R'yi geçmiyor ve hiçbiri P≥0,90'a ulaşmıyor.
- Geniş TP + zaman çıkışı (G3) her kuralda negatif. Daha önceki "zaman çıkışı kazancı = sürüklenme" bulgusu (DX-01) kural koşullu alt kümelerde de geçerli. §3 ders 5 ("braket ≠ zaman") decider XAU'nun 5m tetiklerine **taşınmıyor**.
- D2 (A−, decider genelinde) XAU'da örneklem-dışı tekrarlanmıyor. Bu, XAU'nun "bıçak" mekanizmasının diğer sembollerden farklı olabileceğine işaret ediyor (E18). n=42 bloklu, kesin değil.

### Gaps
- Kural birleşimleri (R1∧R3 vb.) aile şişmesini önlemek için test edilmedi.
- G2'nin journal-ATR tabanına duyarlılığı (DX-01'de +0,018'e düşüyordu) bu turda kural alt kümelerinde tekrarlanmadı. Burada yalnız kapalı-bar ATR kullanıldı.
- $ rakamları ATR tanımına duyarlı: kuralsız G1 gerçek lotla +245$ (sabit 0,01 lotla +85$), oysa DX-01'in orijinal-mesafe sürümü +11,5$/0,01 lot. Birincil ölçü R olmalı.
- Günlük 10 emir tavanı ve "sembol başına 1 pozisyon" kısıtı simüle edilmedi; tek-pozisyon EV'si bilgi olarak verildi.

## 3. SELL: herhangi bir kural kurtarıyor mu?

### Takeaway
**Hayır.** 8 kural × 3 geometrinin 24'ü de **RED**. Kural alt kümelerinin çoğu güçsüz (n<60 veya <10 gün; SELL'in tamamı 81 karar / 12 gün, 69'u Temmuz). Örneklemi yeterli olanlar (R2 n=63, R6 n=68) negatif veya bir yarısı negatif. Önsel (XAU SELL ölü, B1) değişmiyor.

### Cited Findings
- **SELL tabanı:** G1 −0,040 [−0,24, +0,43]; G2 +0,036 (yarılar −0,12 / +0,20); G3 −0,224. Gerçek lotla G1 −1,23$/işlem, toplam −99,7$.
- **Kural satırları:**
  - R2 D2-temiz (n=63/10): G1 −0,162 (C1 %0) — D2'nin SELL'i bloklaması burada kâr etmezdi; tamamlayıcı küme +0,389 (n=18).
  - R3 1h-altı (n=61/9): G3 −0,459 [−0,58, −0,16].
  - R6 (n=68/10): G2 +0,116 ama yarılar −0,18 / +0,41.
  - R5 G2 +0,185 (n=45/9, güçsüz).
  - R8 size ≥0,2 (n=43/4): G1 −0,238 — decider'ın büyük SELL boyutları daha kötü.

  — [results/03_evaluate.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/03_evaluate.txt)
- **Yön seçimi:** decider'ın SELL açtığı 43 tetik anında aynı anın BUY karşı-olgusu G1 −0,109 / G2 −0,194 / G3 +0,132. SELL'in kendi değerleri −0,031 / +0,054 / −0,114. Temmuz'un 43 olayında SELL seçimi dar geometride BUY'dan iyi, geniş geometride kötü; n küçük ve işaret geometriye bağlı. — [results/04_selection_explore.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/04_selection_explore.txt)

### Inferences
- XAU SELL yasağı (B1, HARD_BANS) için yeni bir karşı-kanıt yok. FREE_EXPLORER'ın gölge SELL'leri bu soruyu cevaplamaya yetecek hacim üretmedi (Ağustos'tan beri 12 SELL).

### Gaps
- SELL'in 12 günü tek bir rejime (Temmuz, yükselen altın) ait. Düşen altın rejiminde XAU SELL hiç ölçülmedi.

## 4. Decider'ın seçimi (OPEN, size_factor) XAU içinde bilgi taşıyor mu?

### Takeaway
**Ölçülebilir bir seçim alfası yok.**
- size_factor ile R arasında ilişki yok: Spearman +0,03 / −0,04 / −0,03, aralıkların hepsi sıfırı kapsıyor. Lot kademeleri G2/G3'te monoton değil. R8, C1 plasebosunun yalnız %31–77'sinde.
- OPEN'lar aynı günlerin açılmamış tetik anlarından G1'de +0,062R iyi, ama %95 aralık [−0,12, +0,22].
- IO-12'nin XAU "seçim değeri +0,20R" ve bu turdaki tüm-günler farkı (+0,11R) **dönem karışımı**. Açılmamış tetiklerin çoğu decider'ın ölü olduğu Eylül CLI-hata günlerinden geliyor (466 sahte WAIT, −0,147R).

### Cited Findings
- **(i) Spearman(size_factor, R), BUY n=595:**
  - G1 +0,034 [−0,052, +0,114]
  - G2 −0,043 [−0,116, +0,033]
  - G3 −0,033 [−0,112, +0,055]
- **(ii) Lot kademesine göre EV:**

| Lot | n | G1 | G2 | G3 |
|---|---|---|---|---|
| 0,01 | 304 | −0,024 | +0,088 | −0,014 |
| 0,02 | 198 | +0,023 | +0,094 | −0,070 |
| 0,03 | 93 | +0,022 | −0,082 | −0,085 |

  G1'de gerçek lotla toplam +245$, sabit 0,01 lotla +85$. — [results/04_selection_explore.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/04_selection_explore.txt)
- **(iii) Aynı 22 gün** (C3, extremity ≥1,6; OPEN BUY 289 vs açılmamış 187, bunun 143'ü sahte WAIT):
  - G1: +0,078 vs +0,016 → fark +0,062 [−0,119, +0,222], P 0,74.
  - G2: +0,107 vs +0,062 → fark +0,045 [−0,24, +0,30].
  - G3: +0,070 vs +0,062.
- Yalnız gerçek WAIT'lerle (15 gün): OPEN 199 vs WAIT 44; G1 +0,072 vs +0,038, G2 +0,032 vs **+0,281**.
- Aylara göre: Temmuz'da OPEN kötü (G1 −0,100 vs +0,091); Ağustos'ta iyi (+0,123 vs +0,019).

  — [results/04_selection_explore.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/04_selection_explore.txt), [results/04b_period_confound.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/04b_period_confound.txt)
- **Tüm günler (karışık):** OPEN BUY n=471 G1 +0,003 vs açılmamış n=976 −0,111. Açılmamışların dağılımı:
  - Eylül sahte WAIT 466: −0,147
  - Ekim sahte WAIT 119: −0,168
  - Temmuz gerçek WAIT 199: −0,081

  — [results/04b_period_confound.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/04b_period_confound.txt)
- **(iv)** Gerçek WAIT (n=226) −0,065 / −0,031 vs sahte WAIT (n=750) −0,125 / −0,136 (G1 / G2). Dönem bileşimleri farklı (gerçek WAIT'lerin çoğu Temmuz, sahte WAIT'lerin çoğu Eylül), bu yüzden karşılaştırılamaz. — [results/04_selection_explore.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/04_selection_explore.txt)
- **Rastgele zamana karşı:** decider BUY'ları G2'de rastgele-zaman BUY'larından iyi (C2 yüzdeliği %100, taban −0,072). Ama aynı günlerin açılmamış tetik anları da G2'de +0,062. Avantaj LLM seçiminden çok **tetik anının (|z|≥1,6) kendisinden** geliyor olabilir. — [results/03_evaluate.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/03_evaluate.txt)

### Inferences
- FREE_EXPLORER ile model neredeyse her geçerli danışmada OPEN yazıyor: tetik popülasyonunda gerçek WAIT Eylül'de 18, Ekim'de 1. Bu yüzden XAU'da LLM'in seçimi fiilen yalnız boyut + yön. Boyutun bilgi taşımadığı ölçüldü; lot ölçeklemesi gerçek $'ı ATR ağırlığıyla oynatıyor ama R'yi iyileştirmiyor.
- IO-12'nin "XAU BUY seçim değerli" hükmü gün-eşlemeli kontrolle zayıflıyor. Defterdeki IO-12 satırına "dönem karışımı" notu düşülmeli (aşağıda öneri).

### Gaps
- Aynı-gün eşleşmeli kıyas yalnız 22 gün; Ekim'de karşılaştırma kümesi yok (4 açılmamış danışma).
- `batch_eval` alanındaki geriye dönük model görüşleri (Eylül sahte WAIT'ler için) kullanılmadı. Bunlar "aynı anlarda model ne derdi" için ayrı bir sınama olabilir.

## 5. Sonuç: kurallar + geometri decider XAU'yu kârlı yapabilir mi?

### Takeaway
**Bu veriyle hayır.**
- En iyi ön-kayıtlı kombinasyon "güç-tetikli BUY + TP1,25/SL0,75" (+0,15R, gerçek lotla ≈ +0,94$/işlem). Ama aile-bazlı düzeltmeden geçmiyor, ikinci yarıda sıfıra iniyor ve tek aya yaslanıyor.
- Mevcut geometride (G1) hiçbir kural P≥0,90'a ulaşmıyor. SELL'i kurtaran kural yok. Decider'ın kendi boyut seçimi bilgisiz.
- Kanıt sınıfı: **X** (kurallarla kârlılık), **C** (R1×G2 yalnız gölge izleme adayı).

### Cited Findings
- Verdikt sayımı:
  - BUY (24 test): 1 B (R1×G2), 9 C (R2–R8 × G2 = 7; R4×G1 ve R8×G1 = 2), 14 RED.
  - SELL: 24/24 RED.
  - 48 testin hiçbiri Bonferroni z*(48) = 3,08'i geçmiyor; en iyi mutlak t 1,94.

  — [results/rules_table.csv](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/rules_table.csv), [results/05_reality_check.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/05_reality_check.txt)
- Canlıya alma kartı (2. KURAL) açısından R1×G2:
  - Hacim ≥150 ✓ (271).
  - P≥%90 ✓ (0,97).
  - İki yarı ≥0 ✓, ama +0,007 sınırda.
  - Spread ×1,5 ✓ (+0,132).
  - İcra (+1 dk) ✓ (kayıp %39).
  - Tek pozisyon ✓ (+0,125).

  Kart 6/6 geçer görünüyor. Ama kart seçim düzeltmesi içermiyor (E24); burada p_FW 0,67, RC p 0,22. **Bu yüzden LIVE değil, SHADOW.** — [CLAUDE.md 2. Kural](/Users/melihcanodacioglu/Desktop/panel/CLAUDE.md), [results/03_evaluate.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/kurallar/results/03_evaluate.txt)

### Inferences
- **Önerilen adım (gölge, kod gerektirmez):** journal zaten `multi_tf.5m` channel_z / vwap_z ve `trade.atr`'yi yazıyor. Ön-kayıtlı izleme şu olabilir: "R1 = baskın 5m z > 0 olan OPEN BUY'lar, TP1,25/SL0,75" vs "kuralsız OPEN BUY, TP1,0/SL1,5". 2026-10-15'ten itibaren **ileri dönemde ≥150 yeni karar** (bugünkü hızla ~2–3 hafta) biriktiğinde aynı ölçütlerle karar verilir. Temmuz dışı aylarda R1'in G1'de ters işaret vermesi, ileri dönemin büyük ihtimalle bunu çürüteceğini düşündürüyor. Önsel olasılık düşük tutulmalı.
- Decider XAU'nun EV'si sistematik olarak sıfır civarında. Ne geometri (DX-01) ne mekanizma kuralları (DX-02) bunu güvenilir biçimde pozitife taşıyor. XAU'daki tek sağlam kanıt saat-gün ölçeğinde trend (günlük swing, MK-04). Decider'ın 5m-aşırılık tetiği bu ölçeğe hiç bakmıyor. Kârlılık hedefleniyorsa tetiğin kendisi değişmeli (ör. MK-04 tipi 1h yeni-tepe olayında danış). Bu ayrı bir ön-kayıt gerektirir.
- Prompt/PLAYBOOK'taki "NY seansında canlı %15", "Salı zayıf" gibi saat/gün notları bu veride kural olarak (R5) doğrulanmadı. LLM'e giden bu tür gözlemler gürültü kaynağı.

### Gaps
- Bağımsız ileri dönem yok; tüm hükümler 35 günlük tek rejime (VIX 15–20, yükselen altın) dayanıyor.
- Dukascopy veya kutu MT5'ten çok yıllık XAU 1m verisiyle R1'in **mekanik** sürümü ("5m aşırılık yukarıyken BUY, TP1,25/SL0,75") decider'dan bağımsız sınanabilir. Bu sınama yapılmadı.

## Defter satırı önerileri

`docs/KAPI_KAYIT_DEFTERI.md` §2.7'ye (DX-01'in altına), §6 biçiminde:

| ID | Tarih | Fikir (kural, parametreler) | Sonuç (sayılar + hangi veri/dönem) | Sınıf |
|---|---|---|---|---|
| DX-02 | 2026-10-15 | **Decider XAU ön-kayıtlı giriş kuralları × 3 geometri** (`research/decider_xau_tpsl_20261015/kurallar/`, PROTOCOL 04:41 UTC). DX-01 kümesi (BUY 595/35 gün, SELL 81/12 gün; broker 1m, sonraki-M1 + spread). Kurallar: R1 5m baskın aşırılık yukarı (güç), R2 D2-temiz, R3 1h>EMA50, R4 günlük>SMA10, R5 07–16 UTC, R6 ATR5/24 s medyan<1,5, R7 20 s tepeye ≤1 ATR1h, R8 size≥0,2. Geometriler: G1 TP1/SL1,5, G2 TP1,25/SL0,75 (post-hoc), G3 TP3/SL1,5+120 dk. Kontroller: rastgele alt küme ×4.000, aynı-dakika ±10 gün rastgele zaman ×300, decider'ın açmadığı tetik anları (C3), +1 dk, seçim-düzeltmeli permütasyon + gün-blok max-t | A yok. Tek B: R1×G2 +0,151R [−0,00, +0,30] P %97, n=271/30 gün, yarılar +0,29/+0,01, C1 %93 C2 %100, +1 dk +0,092, +0,94$/işlem (gerçek lot). Ama p_FW 0,67, RC p 0,22, t 1,94 < z*(24) 2,87; G1'de RED (+0,14/−0,07); keşifte etki Temmuz'a yaslı (dip BUY Tem −0,15/−0,24; Ağu–Eyl G1'de ters). G2'de R2–R8 C (7), G1'de R4/R8 C; G3'te 8/8 RED (zaman çıkışı kural koşulunda da negatif). SELL 24/24 RED (n 19–68, 3–10 gün). Mevcut geometride hiçbir kural P≥0,90 değil | X (kurallarla kârlılık) · C (R1×G2 yalnız gölge `policy_*` izleme; ≥150 ileri karar) |
| DX-03 | 2026-10-15 | **Decider XAU seçim alfası, gün-eşlemeli** (aynı veri): size_factor↔R, lot kademeleri, OPEN vs aynı-günün açılmamış tetik anları (extremity≥1,6, BUY simüle), gerçek vs sahte WAIT | Spearman(size, R) +0,03/−0,04/−0,03 (hepsi ∋0). Lot 0,01/0,02/0,03 → G1 −0,024/+0,023/+0,022, G2 +0,088/+0,094/−0,082 (monoton değil). OPEN vs aynı 22 günün açılmamış danışmaları: G1 +0,078 vs +0,016, fark +0,062 [−0,12, +0,22] P 0,74; G2 fark +0,045 [−0,24, +0,30]. Tüm-günler farkı (+0,11R; IO-12'de +0,20R) **dönem karışımı**: açılmamışların 585'i Eylül/Ekim CLI-hata günlerinin sahte WAIT'leri (−0,15/−0,17R). Eylül–Ekim'de gerçek WAIT 18/1 (FREE_EXPLORER) → seçim fiilen yalnız boyut | X (XAU içi seçim alfası) — IO-12 XAU satırına "gün-eşlemesiz, dönem karışık" notu |
| D2-XAU | 2026-10-15 | D2'nin (`chz_dir≥2,0` veya `vol≥1,5`) XAU BUY'da 09-14 dondurma SONRASI örneklem-dışı tekrarı (n=198, 9 gün) | D2-temiz vs blok: G1 −0,055 (n156) vs −0,087 (n42); G2 +0,013 vs +0,143; G3 −0,097 vs +0,056 → tekrarlanmıyor (öncesi G1 +0,055 vs −0,051) | D2 satırına not: XAU'da örneklem-dışı tutmadı (E18; n küçük) |

§1 için olası yeni tuzak satırı (öneri):

| ID | Tuzak | Bedeli (vaka) | Önlem |
|---|---|---|---|
| E29 | **Seçim-değeri (OPEN vs WAIT-cf) kıyası, kontrol kümesi farklı dönemlerden geliyorsa dönem etkisini ölçer.** Decider'ın öldüğü/hata verdiği günlerin "WAIT"leri kontrol kümesini doldurur | XAU BUY "seçim değeri" tüm-günlerde +0,11R (IO-12'de +0,20R); aynı-gün eşlemesinde +0,06R [−0,12, +0,22] | kıyası aynı günlerle (veya gün sabit etkisiyle) yap; sahte WAIT'leri ayrı raporla |
