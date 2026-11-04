# Aile: stres dönüşü — CAPREV-BTC, düşüş sonrası geri dönüş, 1 saatlik şok fade + negatif kontroller (BTC, 5 yıl, sızıntısız)

> Kapsam: yalnız bu aile. Ön-kayıt sonuçlardan önce yazıldı:
> [prereg.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/prereg.md) (sonradan yalnız
> "Değişiklik 1" eklendi, post-hoc ve verdikti değiştirmiyor). Kod: `fam_stres/engine.py` (1m icra motoru, seyrek tablo ile
> ilk-dokunuş araması, kaba kuvvet döngüsüyle 300 rastgele işlemde birebir doğrulandı), `run_stres.py` (75 hücre),
> `analyze.py` (seçim, kart, Holm, max-z, asimetri, N2), `posthoc_g2.py`, `make_tables.py`. Çıktılar `fam_stres/results/`:
> `cells.csv`, `analysis.json`, `posthoc_g2.json`, `tables.md`, `trades_placebo.pkl`.
> Kaynak "URL"leri yerel dosyalar. Kodlar commit edilmedi, kutuya ve Supabase'e dokunulmadı.
>
> Yöntem özeti: Binance BTCUSDT 1m. Karar barın kapanışında alınıyor, giriş sonraki 1m açılışında ±S/2 ile yapılıyor.
> Stop ve zaman çıkışı 1m yol üzerinde çözülüyor; aynı barda TP ve SL birlikte vurursa SL sayılıyor. Spread taban %0,0185,
> stres %0,028, ayrıca sabit 15 $ varyantı var. Swap her 17:00 NY rollover'ında: long −%14/365, short +%2/365.
> R = net PnL / stop mesafesi. Segmentler KEŞİF 2021-06→2023-12, OOS 2024-01-11→2025-06, KÖR 2025-07→2026-10-20.
> Parametre seçimi yalnız KEŞİF'te, onay örneklemi OOS∪KÖR. Gün-blok bootstrap 5.000 tekrar. P1 plasebosu aynı segment,
> aynı yıl ve aynı UTC saat:dakikada rastgele gün çekiyor, yön ve geometri aynı, 200 tekrar.

---

## S1. CAPREV BTC'de tutuyor mu? (stres ∧ korku → önceki gün dibi altı ilk kapanışta BUY, σ-stop, zaman çıkışı)

### Takeaway
**Ön-kayıtlı haliyle hayır.** VIX'li sürüm (G1) bağımsız dönemde tutmadı. BTC'nin kendi RV rejimini kullanan sürümde (G2)
KEŞİF'te seçilen hücre (H4 çıkışı) OOS'ta negatif (−0,063R) çıktı. Holm sonrası 4 onay testinin hiçbiri anlamlı değil
(hepsi p=1,0). Sonradan bakıldığında BTC'de NDX'teki 2×2 deseninin aynısı görülüyor: stres ∧ yüksek RV pozitif,
stres ∧ düşük RV belirgin negatif. Ama olay sayısı yılda ~12; bu bir bulgu değil, ileri veriyle sınanacak bir aday (C).

### Cited Findings
- **Seçim (yalnız KEŞİF, n≥20):**
  - G1 (VIX≥18,4): 12 adaydan `G1_k1.5_US_D1` seçildi (KEŞİF +0,380R, n 20). Max-z p_sel 0,35.
  - G2 (RV yüksek): KEŞİF n≥20 koşulunu yalnız 3 hücre sağladı; `G2_k1.0_UTC_H4` seçildi (KEŞİF +0,295R, n 20).
    Max-z p_sel 0,005, yani KEŞİF'te seçim sonrası bile plasebonun üstündeydi.
  — [analysis.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/analysis.json) (`secim`, `maxz`)
- **Onay (OOS∪KÖR), G1 seçilen hücre:**
  - n 20, WR %45 (başabaş %41), ortR +0,091, %95 GA [−0,49, +0,77], P(EV>0) %59,5.
  - Plasebo yüzdeliği %64. OOS +0,171, KÖR +0,011. Kart 4/6, verdikt RED (hacim + beklenti).
  — aynı dosya (`kart_onay.G1`)
- **Onay, G2 seçilen hücre:**
  - n 44, ortR +0,047, GA [−0,14, +0,23], P %68,2, plasebo %80.
  - OOS −0,063, KÖR +0,207. Yarılar −0,052 / +0,146. Kart 3/6, RED.
  — aynı dosya (`kart_onay.G2`)
- **Hacim yapısal olarak yetersiz.** Tüm 5,4 yılda G1'in birincil hücreleri 25–97 olay, G2'ninkiler 25–64 olay üretiyor.
  Kartın ≥150 eşiği, NDX CAPREV'de olduğu gibi tek sembolde geçilemez.
  — [cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/cells.csv)
- **24 birincil CAPREV hücresinin hepsi (KEŞİF / OOS / KÖR ortR):**
  - VIX'li UTC penceresi k=1,0: D0 −0,116 / −0,141 / +0,207 · H4 −0,005 / −0,318 / +0,068 · D1 −0,089 / −0,073 / −0,024.
  - US penceresi (13:30–20:00 UTC) hücreleri KEŞİF'te çoğunlukla negatif, OOS ve KÖR'de pozitif. Örnek: G1_k1.0_US_D0
    −0,160 / +0,133 / +0,353; G2_k1.0_US_D0 −0,179 / +0,155 / +0,310. Bu, ETF sonrası yapı değişimiyle uyumlu olabilir;
    ancak bu sonradan yapılmış bir okumadır ve seçim kuralı bu hücreleri seçmedi.
  — [tables.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/tables.md)
- **Ön-kayıtlı kontrol hücreleri (UTC×D0, TÜM / onay):**
  - stres(k=1) ∧ ¬RV: KEŞİF −0,234 / OOS −0,334 / KÖR −0,123, onay P(EV>0) %2,1. Nominal −44 bp/işlem.
  - ¬stres ∧ RV: −0,049 / −0,075 / −0,166.
  - stres, korku şartı yok: −0,123 / −0,048 / +0,022.
  - Her gün dip-altı tetik (filtresiz): −0,006 / −0,066 / −0,138; onay plasebo yüzdeliği %1. Filtresiz "dip altına inince al"
    BTC'de rastgele girişten kötü.
  - VIX ayrımı tutarsız: stres ∧ VIX<18,4 −0,139 / +0,034 / −0,102; ¬stres ∧ VIX −0,038 / −0,097 / −0,175.
  — [cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/cells.csv)
- **Literal NDX eşiği (−%1,5 / −%4):**
  - VIX'le: −0,058 / −0,084 / −0,042, X.
  - RV'yle: +0,076 / +0,142 / +0,070; onay P %82, n 109.
  — aynı dosya
- **SONRADAN (prereg Değişiklik 1), G2 deseni plato mu?** Pencere UTC, çıkış D0.
  - RV>medyan: k=0,75 / 1,0 / 1,25 / 1,5 / 2,0 için TÜM ortR +0,157 / +0,225 / +0,246 / +0,383 / +0,365, n 84 / 64 / 45 / 34 / 17.
    k ≤ 1,5'te üç segment de pozitif.
  - RV>%60 yüzdelik: +0,206…+0,517. RV>%40'ta etki çöküyor: +0,022…+0,175, KÖR negatif.
  - Ayna stres ∧ RV≤medyan her k'da negatif: −0,158 / −0,224 / −0,213 / −0,163 / −0,579, P(EV>0) %0–8,5, üç segmentte de negatif.
  — [posthoc_g2.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/posthoc_g2.json)
- **Post-hoc en iyi hücre `G2_k1.0_UTC_D0`:**
  - TÜM n 64, ortR +0,225, P %95,5, yıllar 5/6 pozitif, tek-pozisyonda en iyi 5 gün hariç +1,75R. Nominal +77 bp/işlem.
    Stop medyanı fiyatın %2,7'si, işlem başına ortalama 0,77 gece swap.
  - Onay n 44: +0,247, P %92,6, plasebo %96,5, yarılar +, ×1,5 spread +, icra farkı 0,005, tek-poz +. Kartın 5/6'sını geçiyor,
    yalnız hacimden düşüyor.
  - **Bu hücre ön-kayıtlı seçim değildi.** Seçim yükü taşıyor; ileri veriyle sınanmadan kanıt sayılmaz.
  — [analysis.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/analysis.json) (`posthoc_uc_segment_pozitif`)
- **Pazartesi–Perşembe alt kümesi (bilgi, onay):** G1 n 10, +0,005; G2 n 27, +0,088. NDX'teki gün kısıtı katkı vermiyor. — aynı dosya (`pzt_per`)

### Inferences
- **VIX→BTC taşınmıyor.** NDX'te CAPREV'in iki ayağından biri olan VIX≥18,4, BTC'de yönü ayırmıyor. 2×2 hücreleri
  dönemler arasında işaret değiştiriyor. Literatür de VIX-rejimi→BTC yönü için OOS kanıt bulamamıştı (03 §5).
- **"Korku" BTC'nin kendi oynaklığıyla ölçüldüğünde** NDX'in yapısal deseni yeniden ortaya çıkıyor: stres günü dip kırılımı
  yalnız yüksek-oynaklık rejiminde dönüyor, sakin rejimde devam ediyor. Bu "korku döner" ilkesiyle tutarlı.
  Ancak bu desen (a) yalnız sonradan okundu, (b) yılda ~12 olaydan geliyor. KEŞİF'teki 365 günlük ısınma yüzünden G2'nin
  KEŞİF hücreleri yalnız 12–20 olaydı ve ön-kayıtlı seçim çıkış boyutunda gürültüyü seçti (H4).
- **Pratik çıkarım (kapı adayı).** Ön-kayıtlı bir kontrol hücresi olan "stres ∧ sakin RV günü dip altı BUY" üç segmentte de
  negatif (−0,12…−0,33R). BTC'ye bir dip alım kuralı bağlanırsa bu durum yasaklanmalı. Bu bir veto adayıdır, kenar değildir.
- **Portföy.** BTC CAPREV-RV olay günlerinin NDX/DAX CAPREV günleriyle örtüşmesi ölçülmedi. Örtüşme yüksekse portföye
  katkısı bağımsız bir işlemden çok kaldıraç olur.

### Gaps
- 2021-06 öncesi BTC verisi yok. RV ısınması yüzünden G2'nin KEŞİF dönemi fiilen 2021-11→2023-12. G2 için daha uzun bir
  bağımsız geçmiş (ör. 2017–2021 Coinbase/Bitstamp 1m) ile tek seferlik sınama yapılmadı.
- Broker BTCUSD ile ileri kasa sınaması yapılmadı: ~68 günlük M1'de bu aileden 0–2 olay beklenir, anlamsız.
- BTC ile NDX CAPREV gün örtüşmesi ölçülmedi.

---

## S2. Düşüş sonrası ertesi gün BUY (GR-01 karşılığı, G3) ve negatif kontrol coşku aynası (N1)

### Takeaway
**BTC'de düşüş sonrası günlük geri dönüş yok.** Seçilen hücre onayda −0,090R (P %7), plasebo yüzdeliği %6 ve OOS ile KÖR'ün
ikisi de negatif. k=2,0 (büyük düşüş) daha da kötü: onay D1 −0,338R, P %0,8, yani büyük düşüşün ertesi günü devam
ediyor. Coşku aynası SELL (N1a/N1b) beklendiği gibi kenarsız (≈0 veya negatif).

### Cited Findings
- **G3 seçim ve onay:**
  - KEŞİF'te `G3_k1.0_D1` seçildi (+0,036, n 111). Max-z p_sel 0,93.
  - Onay n 129: WR %44,2 (başabaş %52,0), ortR −0,090, GA [−0,21, +0,03], P %7,0. OOS −0,106, KÖR −0,073.
    Kart 1/6, RED. Yıllar 2024/25/26'nın üçü de negatif.
  — [analysis.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/analysis.json)
- **G3 tüm hücreler (onay ortR):** k=0 D0 −0,016 / D1 −0,012 · k=1 D0 −0,056 / D1 −0,090 · k=2 D0 −0,157 / D1 −0,338
  (plasebo %1).
- **Tabanlar:** her gün 00:00 BUY 2σ-stop D0 → onay −0,005, D1 +0,003; 1σ-stop D0 → +0,015. — [cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/cells.csv)
- **N1a coşku aynası (yükseliş günü ertesi SELL, 2σ, D0/D1), onay:**
  k=0 −0,012 / −0,013 · k=1 −0,003 / −0,029 · k=2 −0,021 / −0,028. Hiçbiri pozitif değil.
- **N1b gün-içi ayna (önceki gün tepesi üstü ilk 1h kapanış SELL, D0), onay:** k=1 −0,052 (n 119), k=1,5 −0,002 (n 53).
  — aynı dosya

### Inferences
- NDX ve DAX'taki "düşüş sonrası al" (GR-01: kazancın tamamı düşüş sonrasında) BTC'ye taşınmıyor. Literatürdeki "büyük ve
  likit coin'ler günlük momentum gösterir" bulgusuyla uyumlu (03 §2, Zaremba vd. 2021). k=2'nin onayda belirgin negatif
  olması, büyük düşüş gününden sonra BTC'nin ertesi gün devam etme eğilimini işaret ediyor. Bu bir SELL kenarı iddiası
  değildir; sınanmadı.
- Coşku aynası SELL beklendiği gibi kenarsız. "Coşku dönmez" kısmı günlük ölçekte BTC'de de geçerli.

### Gaps
- Ertesi gün SELL-devam (büyük düşüş → SELL) ön-kayıtta yoktu; sınanmadı.

---

## S3. 1 saatlik negatif şok fade (literatür H4, G4) ve asimetri (G5 yukarı şok SELL, H5)

### Takeaway
**Negatif şok fade'i BTC'de maliyet sonrası kenarsız.** Seçilen hücre onayda −0,021R (plasebo %53) ve 8 hücrenin hiçbiri
onayda P≥%90'a ulaşmıyor. **Yukarı şok fade'i (SELL) ise sistematik olarak kaybettiriyor:** onayda −0,194R, P %0,1, plasebo
yüzdeliği %0,5, üç segmentte de yaklaşık −0,13…−0,19. Ön-kayıtlı asimetri ölçütü seçilen hücre çiftinde geçiyor (fark +0,173,
P %96,7). Ancak asimetrinin kaynağı "korku döner" değil, **"coşku dönmez"**: yukarı şoklar 1–4 saat devam ediyor.

### Cited Findings
- **G4 seçim ve onay:**
  - KEŞİF'te `G4_z3.5_s1.0_h4` seçildi (+0,058, n 263). Max-z p_sel 0,835.
  - Onay n 339 (264 gün): WR %39,2 (başabaş %40,2), ortR −0,021, GA [−0,157, +0,126], P %37,8. OOS −0,092, KÖR +0,060.
    ×1,5 spread −0,030, kart 1/6.
  — [analysis.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/analysis.json)
- **G4'ün 8 hücresi onayda** −0,048…+0,013 aralığında. En iyisi z3.5/s1/h1 +0,013 (plasebo %88,5). z=2,5'in dört hücresi
  KEŞİF dahil her segmentte negatif. — [cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/cells.csv)
- **G5 (yukarı şok → SELL), seçilen hücrenin aynası:**
  - Onay n 322: ortR −0,194, GA [−0,309, −0,079], P(EV>0) %0,08. OOS −0,194, KÖR −0,194. Tüm dönem −0,162 (n 624).
  - Plasebo ortalaması −0,015, gerçek değer yüzdelik %0,5'te.
  - Aynı aile z3.5/s1/h1 onay −0,095 · z3.5/s2/h4 −0,081.
  — aynı dosyalar
- **Asimetri G4 − G5 (onay):** z3.5/s1/h4 +0,173 (P %96,7, KEŞİF +0,193) · z3.5/s1/h1 +0,108 (P %92,5) ·
  z2.5 hücreleri ≈0 veya negatif (−0,02…−0,007). — `asimetri_G4_eksi_G5`
- **SONRADAN (G5 aynası, başka bir ailenin alanı):** yukarı şok → BUY devam z3.5/s1/h4 TÜM +0,113R, P %94,9, ancak
  segmentlere göre azalıyor (KEŞİF +0,184 / OOS +0,061 / KÖR +0,020). z2.5/h4 +0,060, KÖR −0,055.
  — [posthoc_g2.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/posthoc_g2.json)
- **E32 örneği:** G4 seçilen hücre OOS'ta R −0,092 ama nominal −0,6 bp; tüm dönemde R +0,015 vs +6,3 bp. ATR(1h)-stoplu
  R, şoktan önceki sakin barlarla ölçülen dar ATR yüzünden nominal getiriden ayrışıyor. — `kart_onay.G4`, `kart_tum.G4`

### Inferences
- De Nicola'nın (2021) 1–4 saatlik negatif otokorelasyonu, eğer BTCUSDT 2021–2026'da varsa, %0,0185 spread, sonraki-1m
  icrası ve 1×ATR stopla işlem kenarına dönüşmüyor. z=2,5'te her segmentte negatif.
- "Coşku dönmez" BTC'de 1–4 saat ölçeğinde güçlü biçimde görülüyor: yukarı şoku satmak plasebonun çok altında. Bunun
  pratik karşılığı bir **SELL yasağı adayı**: "son 60 dk ≥ +3,5σ ise BTC'de SELL açma". Bu kenar değil, bir veto adayıdır
  ve bot SELL popülasyonunda ayrıca ölçülmelidir (E18/E19).
- Yukarı şok sonrası BUY devamının azalan seyri, momentumu bir kenar olarak almadan önce dikkatli olmayı gerektiriyor.
  Bu momentum ailesinin alanı.

### Gaps
- Şok tanımında yalnız 60 dk pencere ve 1/2×ATR stop sınandı. Daha geniş stop veya stopsuz fade ön-kayıtta yoktu.
- Şok anındaki gerçek broker spread genişlemesi (volatil dakikada ort. 23,7 $, p90 41,8 $; 02 notu) modellenmedi;
  ×1,5 stres bunun altında kalıyor. SELL-fade zaten negatif olduğundan sonuç değişmez; BUY-fade için daha da kötü olur.

---

## S4. Stres günü SELL yasağı (K5b karşılığı, N2) ve CAPREV olaylarında SELL

### Takeaway
**BTC'de stres günü SELL yasağı desteklenmiyor.** KEŞİF'te stres ∧ dip altı saat başı SELL'ler eşlenik tabandan **iyiydi**
(+0,204R). Onayda fark −0,042 ve P(fark<0) %75; yarılar ters işaretli. CAPREV olaylarında SELL karışık sonuç veriyor:
VIX'li hücrede KEŞİF +0,19 / onay −0,13, RV'li hücrede her segmentte negatif.

### Cited Findings
- **N2, taban üreteç (saat başı SELL, 1×ATR14(1h) stop, 4 s çıkış), hücre = stres(k=1) ∧ son 1h kapanış < pdl,
  aynı yıl × UTC saatiyle eşlenik fark:**
  - KEŞİF: n 708 saat / 79 gün, hücre ortR +0,173 vs hücre-dışı −0,039, eşlenik fark **+0,204** [−0,011, +0,422], P(fark<0) %3,2.
  - Onay: 963 saat / 106 gün, fark −0,042 [−0,171, +0,090], P(fark<0) %75,2, yarılar −0,148 / +0,065.
  - Tüm dönem: fark +0,062, P(fark<0) %15,9.
  — [analysis.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/analysis.json) (`N2`)
- **CAPREV olaylarında SELL (stop giriş×(1+σ20), D0):**
  - k=1 VIX: KEŞİF +0,190 / OOS −0,260 / KÖR +0,017.
  - k=1 RV: −0,191 / −0,344 / −0,002; nominal −69 bp.
  - k=1,5 VIX: −0,219 / −0,080 / +0,330.
  — [cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/cells.csv)

### Inferences
- NDX'teki K5b (stres günü dip altında SELL yok; GF-11) BTC'ye genel bir kapı olarak taşınmıyor. Yalnız stres ∧ yüksek RV
  günlerinde dip altı SELL tutarlı biçimde kötü. Bu, S1'deki G2 BUY deseninin aynası ve aynı seçim yükünü taşıyor.

### Gaps
- Taban SELL üreteci sentetik (saat başı). Botun gerçek BTC SELL sinyalleri henüz yok, veto katkısı portföyde ölçülemedi (E19).

---

## Özet tablo — ön-kayıtlı seçilen hücreler, onay örneklemi (OOS∪KÖR)

| grup | seçilen hücre (KEŞİF) | n onay | WR / başabaş | ortR | %95 GA | P(EV>0) | yarılar | ×1,5 spread | iyimser (fark) | 15$ | tek-poz | plasebo ort / yüzdelik | OOS | KÖR | kart | Holm p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G1 | `G1_k1.5_US_D1` | 20 (20 gün) | %45.0 / %41.3 | +0.091 | [-0.494, +0.771] | %59.5 | +0.171 / +0.011 | +0.089 | +0.096 (0.004) | +0.091 | +0.213 | +0.021 / %64 | +0.171 (n 10) | +0.011 (n 10) | 4/6 RED | 1.0 |
| G2 | `G2_k1.0_UTC_H4` | 44 (44 gün) | %56.8 / %52.2 | +0.047 | [-0.141, +0.231] | %68.2 | -0.052 / +0.146 | +0.044 | +0.054 (0.006) | +0.046 | +0.047 | -0.001 / %80 | -0.063 (n 26) | +0.207 (n 18) | 3/6 RED | 1.0 |
| G3 | `G3_k1.0_D1` | 129 (129 gün) | %44.2 / %52.0 | -0.090 | [-0.211, +0.030] | %7.0 | -0.127 / -0.054 | -0.092 | -0.087 (0.003) | -0.090 | -0.079 | +0.009 / %6 | -0.106 (n 67) | -0.073 (n 62) | 1/6 RED | 1.0 |
| G4 | `G4_z3.5_s1.0_h4` | 339 (264 gün) | %39.2 / %40.2 | -0.021 | [-0.157, +0.126] | %37.8 | -0.077 / +0.033 | -0.030 | -0.006 (0.016) | -0.022 | -0.021 | -0.026 / %53 | -0.092 (n 181) | +0.060 (n 158) | 1/6 SHADOW | 1.0 |
| G5 | `G5_z3.5_s1.0_h4` | 322 (251 gün) | %36.3 / %46.8 | -0.194 | [-0.309, -0.079] | %0.1 | -0.204 / -0.184 | -0.208 | -0.170 (0.024) | -0.201 | -0.194 | -0.015 / %0 | -0.194 (n 183) | -0.194 (n 139) | 2/6 SHADOW | — |

Ek kart ölçütleri:
- Holm 4 onay testi: hepsi p=1,0.
- Seçimsiz 38 birincil hücrede Holm: en küçük ham p 0,038 (`G1_k1.0_US_D0`), Holm sonrası 1,0.
- KEŞİF max-z p_sel: G1 0,35 · G2 0,005 · G3 0,93 · G4 0,835.
- KÖR işareti: G1 + (+0,011), G2 + (+0,207), G3 −, G4 + (+0,060), G5 −.
- Hiçbir grup kartı geçmiyor. **Aile verdikti: ön-kayıtlı hipotezlerin hiçbiri BTC'de canlıya alınabilir değil.**

### Tüm hücreler (75; seçim yapılmadan, hepsi raporlandı)

| hücre | KEŞİF n / ortR / plasebo% | OOS n / ortR | KÖR n / ortR | ONAY ortR / P(EV>0) / plasebo% | TÜM n / ortR |
|---|---|---|---|---|---|
| `G1_k1.0_UTC_D0` | 53 / -0.116 / +0.330 | 24 / -0.141 | 20 / +0.207 | +0.017 / +0.530 / +0.550 | 97 / -0.055 |
| `G1_k1.0_UTC_H4` | 53 / -0.005 / +0.560 | 24 / -0.318 | 20 / +0.068 | -0.143 / +0.077 / +0.010 | 97 / -0.068 |
| `G1_k1.0_UTC_D1` | 53 / -0.088 / +0.530 | 24 / -0.073 | 20 / -0.024 | -0.051 / +0.384 / +0.395 | 97 / -0.071 |
| `G1_k1.0_US_D0` | 42 / -0.160 / +0.105 | 20 / +0.133 | 19 / +0.353 | +0.240 / +0.962 / +0.970 | 81 / +0.033 |
| `G1_k1.0_US_H4` | 42 / -0.012 / +0.530 | 20 / +0.008 | 19 / +0.222 | +0.112 / +0.822 / +0.910 | 81 / +0.048 |
| `G1_k1.0_US_D1` | 42 / +0.036 / +0.775 | 20 / +0.271 | 19 / +0.130 | +0.203 / +0.830 / +0.855 | 81 / +0.116 |
| `G1_k1.5_UTC_D0` | 27 / +0.070 / +0.780 | 12 / -0.143 | 11 / +0.005 | -0.072 / +0.356 / +0.340 | 50 / +0.004 |
| `G1_k1.5_UTC_H4` | 27 / +0.124 / +0.970 | 12 / -0.386 | 11 / -0.025 | -0.214 / +0.075 / +0.005 | 50 / -0.031 |
| `G1_k1.5_UTC_D1` | 27 / +0.153 / +0.850 | 12 / -0.470 | 11 / -0.255 | -0.367 / +0.062 / +0.045 | 50 / -0.086 |
| `G1_k1.5_US_D0` | 20 / +0.053 / +0.740 | 10 / +0.132 | 10 / +0.171 | +0.151 / +0.761 / +0.855 | 40 / +0.102 |
| `G1_k1.5_US_H4` | 20 / +0.044 / +0.725 | 10 / +0.061 | 10 / +0.163 | +0.112 / +0.701 / +0.825 | 40 / +0.078 |
| `G1_k1.5_US_D1` | 20 / +0.380 / +0.955 | 10 / +0.171 | 10 / +0.011 | +0.091 / +0.595 / +0.640 | 40 / +0.236 |
| `G2_k1.0_UTC_D0` | 20 / +0.174 / +0.875 | 26 / +0.226 | 18 / +0.278 | +0.247 / +0.926 / +0.965 | 64 / +0.225 |
| `G2_k1.0_UTC_H4` | 20 / +0.294 / +1.000 | 26 / -0.063 | 18 / +0.207 | +0.047 / +0.682 / +0.795 | 64 / +0.125 |
| `G2_k1.0_UTC_D1` | 20 / -0.026 / +0.630 | 26 / +0.230 | 18 / -0.188 | +0.059 / +0.625 / +0.595 | 64 / +0.032 |
| `G2_k1.0_US_D0` | 14 / -0.179 / +0.170 | 21 / +0.155 | 16 / +0.310 | +0.222 / +0.955 / +0.975 | 51 / +0.112 |
| `G2_k1.0_US_H4` | 14 / +0.005 / +0.660 | 21 / +0.109 | 16 / +0.134 | +0.119 / +0.830 / +0.925 | 51 / +0.088 |
| `G2_k1.0_US_D1` | 14 / -0.486 / +0.060 | 21 / +0.201 | 16 / -0.008 | +0.110 / +0.724 / +0.730 | 51 / -0.053 |
| `G2_k1.5_UTC_D0` | 12 / +0.323 / +0.945 | 11 / +0.554 | 11 / +0.277 | +0.416 / +0.932 / +0.975 | 34 / +0.383 |
| `G2_k1.5_UTC_H4` | 12 / +0.334 / +0.995 | 11 / -0.130 | 11 / +0.146 | +0.008 / +0.514 / +0.600 | 34 / +0.123 |
| `G2_k1.5_UTC_D1` | 12 / +0.077 / +0.755 | 11 / +0.166 | 11 / -0.575 | -0.205 / +0.198 / +0.185 | 34 / -0.105 |
| `G2_k1.5_US_D0` | 8 / -0.200 / +0.210 | 8 / +0.513 | 9 / +0.215 | +0.355 / +0.956 / +0.980 | 25 / +0.178 |
| `G2_k1.5_US_H4` | 8 / -0.075 / +0.410 | 8 / +0.294 | 9 / +0.067 | +0.174 / +0.797 / +0.910 | 25 / +0.094 |
| `G2_k1.5_US_D1` | 8 / -0.537 / +0.080 | 8 / +0.505 | 9 / -0.372 | +0.041 / +0.531 / +0.570 | 25 / -0.144 |
| `G3_k0.0_D0` | 473 / -0.001 / +0.310 | 256 / -0.007 | 244 / -0.025 | -0.016 / +0.253 / +0.355 | 978 / -0.006 |
| `G3_k0.0_D1` | 472 / -0.003 / +0.210 | 256 / +0.004 | 244 / -0.029 | -0.012 / +0.349 / +0.355 | 977 / -0.004 |
| `N1a_k0.0_D0` | 449 / -0.016 / +0.400 | 281 / -0.026 | 233 / +0.006 | -0.012 / +0.276 / +0.440 | 968 / -0.014 |
| `N1a_k0.0_D1` | 449 / -0.022 / +0.240 | 281 / -0.047 | 233 / +0.027 | -0.013 / +0.330 / +0.495 | 968 / -0.017 |
| `G3_k1.0_D0` | 111 / +0.025 / +0.570 | 67 / -0.075 | 62 / -0.035 | -0.056 / +0.152 / +0.165 | 241 / -0.016 |
| `G3_k1.0_D1` | 111 / +0.036 / +0.580 | 67 / -0.106 | 62 / -0.073 | -0.090 / +0.070 / +0.060 | 241 / -0.029 |
| `N1a_k1.0_D0` | 121 / -0.038 / +0.215 | 82 / -0.002 | 62 / -0.004 | -0.003 / +0.486 / +0.575 | 268 / -0.019 |
| `N1a_k1.0_D1` | 121 / -0.028 / +0.380 | 82 / -0.049 | 62 / -0.004 | -0.029 / +0.304 / +0.405 | 268 / -0.025 |
| `G3_k2.0_D0` | 27 / -0.011 / +0.485 | 13 / -0.063 | 16 / -0.233 | -0.157 / +0.116 / +0.085 | 57 / -0.073 |
| `G3_k2.0_D1` | 27 / -0.041 / +0.385 | 13 / -0.439 | 16 / -0.255 | -0.338 / +0.008 / +0.010 | 57 / -0.180 |
| `N1a_k2.0_D0` | 39 / -0.090 / +0.215 | 21 / +0.083 | 16 / -0.158 | -0.021 / +0.390 / +0.455 | 78 / -0.056 |
| `N1a_k2.0_D1` | 39 / -0.109 / +0.205 | 21 / -0.018 | 16 / -0.040 | -0.028 / +0.383 / +0.490 | 78 / -0.057 |
| `G4_z2.5_s1.0_h1` | 584 / -0.064 / +0.095 | 366 / -0.056 | 342 / -0.006 | -0.032 / +0.185 / +0.460 | 1299 / -0.047 |
| `G4_z2.5_s1.0_h4` | 584 / -0.081 / +0.075 | 366 / -0.038 | 342 / -0.036 | -0.037 / +0.213 / +0.390 | 1299 / -0.058 |
| `G4_z2.5_s2.0_h1` | 584 / -0.036 / +0.065 | 366 / -0.056 | 342 / -0.003 | -0.030 / +0.074 / +0.205 | 1299 / -0.033 |
| `G4_z2.5_s2.0_h4` | 584 / -0.052 / +0.095 | 366 / -0.076 | 342 / -0.018 | -0.048 / +0.052 / +0.090 | 1299 / -0.049 |
| `G5_z2.5_s1.0_h1` | 603 / -0.064 / +0.095 | 397 / -0.026 | 326 / -0.007 | -0.017 / +0.318 / +0.695 | 1340 / -0.034 |
| `G5_z2.5_s1.0_h4` | 603 / -0.060 / +0.315 | 397 / +0.007 | 326 / -0.046 | -0.017 / +0.377 / +0.635 | 1340 / -0.037 |
| `G5_z2.5_s2.0_h1` | 603 / -0.032 / +0.185 | 397 / -0.028 | 326 / -0.018 | -0.023 / +0.137 / +0.355 | 1340 / -0.026 |
| `G5_z2.5_s2.0_h4` | 603 / -0.020 / +0.405 | 397 / -0.032 | 326 / -0.027 | -0.030 / +0.165 / +0.260 | 1340 / -0.027 |
| `G4_z3.5_s1.0_h1` | 263 / -0.037 / +0.390 | 181 / +0.026 | 158 / -0.002 | +0.013 / +0.594 / +0.885 | 607 / -0.008 |
| `G4_z3.5_s1.0_h4` | 263 / +0.058 / +0.800 | 181 / -0.092 | 158 / +0.060 | -0.021 / +0.378 / +0.530 | 607 / +0.015 |
| `G4_z3.5_s2.0_h1` | 263 / -0.062 / +0.020 | 181 / -0.008 | 158 / -0.029 | -0.018 / +0.287 / +0.515 | 607 / -0.037 |
| `G4_z3.5_s2.0_h4` | 263 / -0.025 / +0.445 | 181 / -0.051 | 158 / -0.002 | -0.028 / +0.272 / +0.410 | 607 / -0.026 |
| `G5_z3.5_s1.0_h1` | 294 / -0.130 / +0.005 | 183 / -0.110 | 139 / -0.075 | -0.095 / +0.026 / +0.055 | 624 / -0.105 |
| `G5_z3.5_s1.0_h4` | 294 / -0.135 / +0.045 | 183 / -0.194 | 139 / -0.194 | -0.194 / +0.001 / +0.005 | 624 / -0.162 |
| `G5_z3.5_s2.0_h1` | 294 / -0.069 / +0.010 | 183 / -0.025 | 139 / -0.034 | -0.029 / +0.168 / +0.300 | 624 / -0.046 |
| `G5_z3.5_s2.0_h4` | 294 / -0.061 / +0.150 | 183 / -0.114 | 139 / -0.037 | -0.081 / +0.022 / +0.035 | 624 / -0.070 |
| `N1b_k1.0_UTC_D0` | 95 / -0.051 / +0.330 | 65 / -0.076 | 54 / -0.022 | -0.052 / +0.219 / +0.250 | 215 / -0.050 |
| `N1b_k1.5_UTC_D0` | 47 / -0.164 / +0.090 | 28 / -0.017 | 25 / +0.014 | -0.002 / +0.484 / +0.525 | 101 / -0.076 |
| `K_k1.0_stres_ve_notVIX_UTC_D0` | 22 / -0.139 / — | 27 / +0.034 | 30 / -0.102 | -0.038 / +0.384 / — | 79 / -0.066 |
| `K_k1.0_notstres_ve_VIX_UTC_D0` | 121 / +0.037 / — | 34 / -0.097 | 28 / -0.175 | -0.132 / +0.068 / — | 183 / -0.020 |
| `K_k1.0_stres_ve_VIX_SELL_UTC_D0` | 53 / +0.190 / — | 24 / -0.260 | 20 / +0.017 | -0.134 / +0.195 / — | 97 / +0.043 |
| `K_k1.0_stres_ve_notRV_UTC_D0` | 46 / -0.234 / — | 25 / -0.334 | 32 / -0.123 | -0.215 / +0.021 / — | 103 / -0.224 |
| `K_k1.0_notstres_ve_RV_UTC_D0` | 57 / -0.049 / — | 67 / -0.075 | 54 / -0.166 | -0.116 / +0.022 / — | 181 / -0.068 |
| `K_k1.0_stres_ve_RV_SELL_UTC_D0` | 20 / -0.191 / — | 26 / -0.344 | 18 / -0.002 | -0.204 / +0.118 / — | 64 / -0.200 |
| `K_k1.0_stres_korkusuz_UTC_D0` | 75 / -0.123 / — | 51 / -0.048 | 50 / +0.022 | -0.014 / +0.440 / — | 176 / -0.060 |
| `K_k1.5_stres_ve_notVIX_UTC_D0` | 11 / -0.072 / — | 11 / +0.233 | 18 / +0.055 | +0.123 / +0.737 / — | 40 / +0.069 |
| `K_k1.5_notstres_ve_VIX_UTC_D0` | 147 / -0.024 / — | 46 / -0.107 | 37 / -0.022 | -0.069 / +0.203 / — | 230 / -0.040 |
| `K_k1.5_stres_ve_VIX_SELL_UTC_D0` | 27 / -0.219 / — | 12 / -0.080 | 11 / +0.330 | +0.116 / +0.640 / — | 50 / -0.065 |
| `K_k1.5_stres_ve_notRV_UTC_D0` | 22 / -0.055 / — | 12 / -0.438 | 18 / -0.111 | -0.242 / +0.071 / — | 52 / -0.163 |
| `K_k1.5_notstres_ve_RV_UTC_D0` | 65 / -0.049 / — | 82 / -0.064 | 61 / -0.115 | -0.086 / +0.068 / — | 211 / -0.051 |
| `K_k1.5_stres_ve_RV_SELL_UTC_D0` | 12 / -0.061 / — | 11 / -0.324 | 11 / +0.208 | -0.058 / +0.402 / — | 34 / -0.059 |
| `K_k1.5_stres_korkusuz_UTC_D0` | 38 / +0.029 / — | 23 / +0.036 | 29 / +0.036 | +0.036 / +0.589 / — | 90 / +0.033 |
| `K_literal_VIX_UTC_D0` | 87 / -0.058 / — | 27 / -0.084 | 30 / -0.042 | -0.062 / +0.314 / — | 144 / -0.060 |
| `K_literal_RV_UTC_D0` | 35 / +0.076 / — | 39 / +0.142 | 34 / +0.070 | +0.108 / +0.824 / — | 109 / +0.113 |
| `K_tetik_hergun_UTC_D0` | 277 / -0.005 / +0.440 | 173 / -0.066 | 167 / -0.138 | -0.101 / +0.012 / +0.010 | 620 / -0.051 |
| `K_tetik_hergun_US_D0` | 243 / -0.032 / +0.155 | 164 / +0.043 | 155 / -0.048 | -0.001 / +0.489 / +0.510 | 563 / -0.014 |
| `K_hergun_0000_BUY_1sig_D0` | 922 / +0.026 / +0.620 | 537 / +0.051 | 477 / -0.026 | +0.015 / +0.678 / +0.470 | 1946 / +0.022 |
| `K_hergun_0000_BUY_2sig_D0` | 922 / +0.015 / +0.505 | 537 / +0.009 | 477 / -0.020 | -0.005 / +0.391 / +0.450 | 1946 / +0.006 |
| `K_hergun_0000_BUY_2sig_D1` | 921 / +0.033 / +0.485 | 537 / +0.019 | 477 / -0.015 | +0.003 / +0.542 / +0.515 | 1945 / +0.018 |

(Plasebo yüzdeliği yalnız birincil, ayna ve taban hücrelerinde hesaplandı. "K_" kontrol hücrelerinde "—".)

---

## Defter satırı taslağı

`docs/KAPI_KAYIT_DEFTERI.md` §6 biçimi. Önerilen yeni alt bölüm: "§2.11 BTC kenar araştırması (`research/btc_5y_20261021/`)".

| ID | Tarih | Fikir (kural, parametreler) | Sonuç (sayılar + hangi veri/dönem) | Sınıf |
|---|---|---|---|---|
| BTC-S01 | 2026-10-21 | **CAPREV-BTC, VIX'li** (GF-16 portu): stres = dün ≤ −k·σ20 VEYA 5g ≤ −k·σ20·√5 (k 1,0/1,5) ∧ önceki ABD günü VIX ≥ 18,4; UTC 00–20 1h veya US 13:30–20:00 30m penceresinde önceki UTC günü dibi altı ilk kapanış → BUY; stop giriş×(1−σ20); çıkış D0/+4s/D1. Binance 1m, sonraki 1m açılış + %0,0185 spread, swap. Ön kayıt `fam_stres/prereg.md` | 12 hücre. KEŞİF seçimi k1,5/US/D1 (+0,38, n 20) → onay (2024-01-11→2026-10-20) n 20, +0,091, P %60, plasebo %64; Holm 1,0; max-z p_sel 0,35. VIX 2×2 hücreleri dönemler arası işaret değiştiriyor; literal −%1,5/−%4 + VIX her segmentte negatif. **VIX ayağı BTC'ye taşınmıyor.** Kanıt `research/btc_5y_20261021/fam_stres/results/analysis.json` | X |
| BTC-S02 | 2026-10-21 | **CAPREV-BTC, RV korkulu**: BTC-S01 ile aynı, VIX yerine σ30 > önceki 365g medyanı | Ön-kayıtlı seçim (k1,0/UTC/H4, KEŞİF n 20, max-z p_sel 0,005) onayda n 44, +0,047, P %68, OOS −0,063 / KÖR +0,207 → tutmadı. **Sonradan:** aynı ailede D0 çıkışı k 0,75–2,0 ve RV>%50–60 eşiklerinde hep pozitif (TÜM +0,16…+0,52R). `G2_k1.0_UTC_D0`: n 64 / 5,4 yıl, +0,225R, P %95,5, onay +0,247, plasebo %96,5, kart 5/6 (hacim ✗). Yılda ~12 olay; seçim yükü var. İleri gölgede ön-kayıtlı k=1,0 / D0 ile sınanmalı | C (aday) |
| BTC-S03 | 2026-10-21 | **Stres ∧ sakin RV günü dip-altı BUY** (BTC-S02'nin ön-kayıtlı kontrol hücresi; veto adayı) | k=1: KEŞİF −0,234 / OOS −0,334 / KÖR −0,123 (n 46/25/32), onay P(EV>0) %2,1, nominal −44 bp. Sonradan k 0,75–2,0'ın hepsinde negatif (−0,16…−0,58). NDX'teki "stres ∧ düşük VIX negatif" ile aynı desen, korku ölçüsü BTC'nin kendi RV'si | B− (veto adayı; dip-alım kuralı bağlanırsa) |
| BTC-S04 | 2026-10-21 | **Düşüş sonrası ertesi gün BUY** (GR-01 portu): dün ≤ −k·σ20 (k 0/1/2) → 00:00 UTC BUY, stop 2σ20, D0/D1 | Seçim k1/D1 → onay n 129, −0,090R, P %7, plasebo %6, OOS ve KÖR negatif. k=2 D1 onay −0,338 (P %0,8): büyük düşüş ertesi gün devam ediyor. Her gün BUY tabanı ≈0. **BTC'de günlük geri dönüş yok** | X |
| BTC-S05 | 2026-10-21 | **1 saatlik negatif şok fade** (literatür H4, De Nicola 2021): 5m ızgarada 60 dk getiri ≤ −z·σ60 (z 2,5/3,5; σ60 = önceki 30 gün), ≥4 s epizod aralığı → BUY; stop 1/2×ATR14(1h); 1/4 s çıkış | 8 hücre. Seçim z3,5/s1/h4 → onay n 339, −0,021R, P %38, plasebo %53, OOS −0,092 / KÖR +0,060; z=2,5'in tüm hücreleri her segmentte negatif. Maliyet ve sonraki-1m icrasında kenar yok | X |
| BTC-S06 | 2026-10-21 | **1 saatlik yukarı şok fade (SELL)** — BTC-S05'in aynası (H5, asimetri) | z3,5/s1/h4 onay n 322, **−0,194R**, GA [−0,31, −0,08], P(EV>0) %0,1, plasebo yüzdeliği %0,5; KEŞİF −0,135 / OOS −0,194 / KÖR −0,194. Asimetri G4−G5 +0,173 (P %96,7) → ön-kayıtlı ölçüt geçti, ancak kaynağı "coşku dönmez" (yukarı şok 1–4 s devam ediyor), "korku döner" değil. **Pratik: "60 dk ≥ +3,5σ → BTC SELL yok" veto adayı** | X (strateji) / B (veto adayı) |
| BTC-S07 | 2026-10-21 | **Coşku aynası SELL** (GF-12 portu, negatif kontrol): dün ≥ +k·σ20 → ertesi gün SELL 2σ, D0/D1; gün-içi önceki gün tepesi üstü ilk 1h kapanış SELL σ-stop D0 | 8 hücrenin onayda hepsi ≤ 0 (−0,052…−0,002). Beklendiği gibi kenarsız; "coşku dönmez" günlük ölçekte de geçerli | X (beklenen) |
| BTC-S08 | 2026-10-21 | **Stres günü SELL yasağı** (K5b/GF-11 portu): saat başı SELL (1×ATR14 1h, 4 s), hücre stres(k=1) ∧ son 1h kapanış < önceki gün dibi; aynı yıl × UTC saati eşlenik fark | KEŞİF fark **+0,204** (hücredeki SELL'ler daha İYİ, P(fark<0) %3), onay −0,042 (P %75, yarılar ters) → yasak desteklenmiyor. CAPREV olaylarında SELL: VIX'li karışık, RV'li her segmentte negatif (BTC-S02'nin aynası) | X |

---

## Yeni yöntem tuzakları

| ID önerisi | Tuzak | Bedeli (bu vaka) | Önlem |
|---|---|---|---|
| E40 | **Isınma penceresi uzun olan rejim göstergesi (365 g RV medyanı) KEŞİF dönemini sessizce kısaltıyor.** Seçim artık 12–20 olayla yapılıyor ve seçim, en gürültülü boyutu (çıkış) seçiyor | G2: KEŞİF'te çıkış seçimi n=20 ile H4'ü seçti (max-z p_sel 0,005 ile "anlamlı"), onayda OOS negatif. Seçilmeyen D0 çıkışı üç segmentte de pozitifti | Ön kayıtta her hücrenin KEŞİF'te beklenen olay sayısını ısınmadan sonra hesapla. n<50 ise seçim yapma: çıkışı ön-kayıtta tek değere sabitle veya hücreleri havuzla. Max-z'nin "anlamlı" çıkması küçük n'de çoğaltmayı garanti etmez |
| E41 | **Asimetri ölçütü (BUY-fade − SELL-fade > 0) "korku döner" teyidi sanılabilir.** Fark, BUY kolunun kazanmasından değil, SELL kolunun kaybetmesinden (yukarı devamdan) gelebilir | BTC-S06: fark +0,173, P %96,7. Ama BUY-fade onayda −0,021 (≈0), SELL-fade −0,194 | Asimetri ölçütünü iki kolun mutlak işaretleriyle birlikte yaz. "Korku döner" için BUY kolu tek başına > 0 ve plasebonun üstünde olmalı |
| (E32'nin BTC örneği) | ATR(1h)-stoplu şok işlemlerinde R ile nominal getiri ayrışıyor (şok öncesi dar ATR) | G4 OOS R −0,092 vs −0,6 bp; tüm dönem +0,015R vs +6,3 bp | Şok/kırılım ailelerinde R'yi her zaman bp ile birlikte raporla |

Not: VIX'i BTC'ye `merge_asof(avail_utc ≤ gün başı)` ile bağlamak sızıntısız. Ancak ABD tatillerinde Yahoo'nun bayat VIX
satırları var (02 notu). Bu yüzden `qqq_close` NaN olan satırlar dışlandı ve VIX ileri taşındı. Bu adım ön kayıtta açıkça
yazılmamıştı; etkisi en fazla birkaç gün.
