# XAUUSD mekanik giriş kuralları + açık TP/SL — uzun (2008→2026) ön-kayıtlı test ve canlıya alma kartları (MK-06, 2026-10-15)

> Kapsam: yarıda kalan `research/decider_xau_tpsl_20261015/mekanik/` çalışmasının tamamlanması. 6 BUY kuralı × 3 geometri = 18 birincil hücre (+18 SELL kontrol aynası), Dukascopy XAUUSD H1 BID+ASK 2008-01 → 2026-06-16 (111.195 bar), broker (Pepperstone) 1m kasası 2026-06-17 → 10-14.
> Web araması yok — tüm kaynaklar yerel kod/veri/sonuç dosyaları.
> Kod: `/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/`. Çalışma sırası: `PROTOCOL.md` (ön kayıt), `run_main.py`, `holdout.py`, `analyze.py`, ardından **post-hoc** `posthoc.py` + `posthoc_holdout.py` + `posthoc_onepos.py`. Sonuçlar `results/` altında.
> Birimler: R = (çıkış − giriş) / SL mesafesi. Spread A = $0,12 (karar modeli). Giriş = sinyal barından sonraki H1 açılışı + spread. Aynı barda TP+SL = LOSS.

## 1. Yarıda kalan iş: ne tamamdı, ne eksikti, ne yapıldı

### Takeaway
- Veri indirmesi **tamamdı**. 226/226 aylık H1 dosyası (BID+ASK) 2008-01 → 2026-10 indirilmiş; 225 ayda veri var, en az bar sayısı ≥300.
- Ana koşu (`results/cells.csv`, 200 plasebo tekrarı) da tamamdı. Yeniden koşturunca **birebir aynı** çıktı (tüm sayısal sütunlarda fark 0).
- Eksik olan 2 adımdı: kasa (`holdout.py` bir saat-dilimi karşılaştırma hatasıyla çöküyordu, düzeltildi) ve kart/verdikt (`analyze.py` hiç koşmamıştı, koşturuldu).
- Yeni veri indirilmedi.

### Cited Findings
- **İndirme günlükleri:** son tur "DONE ok/skip" ile bitti; aradaki `fail`'ler sonraki turlarda tamamlandı (`skip` sayısı artıyor).
  - `raw/BID_H1` ve `raw/ASK_H1`: 2008-01-01.bi5 → 2026-10-01.bi5, her biri 226 dosya.
  - `raw/BID` ve `raw/ASK` (1m gün dosyası): yalnız 2025-01'den 12 gün. Erken deneme, kullanılmadı.
  - Kaynak: [dl_hour*.log](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/data/duka/), [00_duka_download.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/00_duka_download.py)
- **`duka_h1.parquet`:** 112.933 bar, 2008-01-01 00:00 → 2026-09-30 23:00 UTC. Hacmi 0 olan barlar atıldı.
  - Duka'nın kendi ask−bid medyanı yıla göre: 2008 $0,46 · 2010 $0,51 · 2014 $0,29 · 2017-18 $0,24 · 2024 $0,38 · 2025 $0,59 · 2026 $0,69.
  - Bu değerler canlı Pepperstone ölçümü olan $0,12'nin 2–6 katı.
  - Kaynak: [01_build_duka.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/01_build_duka.py)
- `results_cc/` = aynı kodun candle_cache 1h üzerinde 20 tekrarla geliştirme koşusu (Duka verisi inmeden önce). Verdikte kullanılmadı. — [results_cc/cells.csv](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results_cc/cells.csv)
- **Bu oturumda yapılan kod düzeltmeleri** (sonuç görülmeden önce/sırasında; mantık değişmedi):
  1. `holdout.py`: tz-aware ↔ naive datetime karşılaştırması çöküyordu. `hts`/`T` naive UTC datetime64'e çevrildi.
  2. `analyze.py`: taslakta PROTOCOL §5'te olmayan bir ek kural vardı ("n<150 → doğrudan RED"). Ön kayda uymak için kaldırıldı. Etkisi yok: tüm BUY hücrelerinde n ≥ 865.
  - Kaynak: [holdout.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/holdout.py), [analyze.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/analyze.py)
- **Bağımsız denetim** (scratchpad `verify.py`):
  - `path_sim`, döngülü kaba-kuvvet simülatörle 18 hücre × 150 rastgele olayda karşılaştırıldı: maks |ΔR| = 0.
  - Önek (prefix) sızıntı testi: veri 2015-06-30 14:00 ve 2021-03-10 09:00'da kesilip olaylar yeniden üretildi. 6 kuralın 6'sında kesimden önceki olay kümesi farkı 0, ATR farkı 0. D1/H4 durumları yalnız kapanmış barlardan geliyor.

### Inferences
- Önceki ajanın ana koşusu güvenilir ve tekrarlanabilir. Tamamlanan adımlar kodu değil, yalnız eksik çıktıları üretti.

### Gaps
- Dukascopy 1m (2008–2024) indirilmedi. Ana dönemde yol H1 çözünürlükte, aynı-bar=LOSS ile kötümser. 1m ile H1 yol farkı yalnız kasada ölçüldü (§3).

## 2. Dukascopy ↔ broker kalibrasyonu (örtüşme 2026-06-17 → 09-30)

### Takeaway
- Saat ekseni hizalı (ofset 0).
- Duka kapanışı broker'dan sabit ≈ $0,30 düşük.
- H1 aralıkları aynı (oran 0,994). ATR-tabanlı geometriler iki besleme arasında birebir taşınır.

### Cited Findings
- 1.626 ortak tam saat (≥50 broker 1m barı olan saatler).
- Kapanış farkı ve getiri korelasyonu, Duka zaman damgası kaydırılarak:

| Kaydırma | |Δclose| medyan | Δ-getiri korelasyonu |
|---|---|---|
| −2 s | $9,72 | 0,041 |
| −1 s | $6,83 | 0,041 |
| **0 s** | **$0,295** | **0,970** |
| +1 s | $6,64 | 0,062 |
| +2 s | $9,71 | 0,035 |

- Duka − broker medyan farkı: kapanış −$0,295, high −$0,305, low −$0,195. H1 aralık oranı Duka/broker 0,994.
- Kaynak: [results/calibration.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results/calibration.txt)

### Inferences
- $0,30'luk sabit seviye farkı R'yi etkilemez. Duka BID yolu ile broker BID yolu aynı TP/SL olaylarını üretir.
- E2/E3 tipi saat kayması bu veride yok.

### Gaps
- Kalibrasyon yalnız 2026'nın 3,5 ayı için. Eski yıllarda Duka ↔ broker farkı ölçülemez (broker geçmişi yok).

## 3. Kural × geometri sonuçları (gerçek icra, sürüklenme plasebosu, yarılar, yıllar)

### Takeaway
- 18 BUY hücresinin 12'si sürüklenmeyi geçemiyor ya da negatif.
- Sürüklenmenin belirgin üstünde kalan tek aile, **stopsuz/zaman çıkışlı "yukarı kırılımı al"**:
  - **R0B_G1** (MK-04: 1h yeni 20-bar tepesi, SL 1,5×ATR_H1, TP yok, 20 bar): +0,102R vs rastgele BUY +0,049.
  - **R4B_G3** (BB sıkışma kırılımı + D1 trend, SL 1,5, 12 bar): +0,122 vs +0,039.
- Braketli (TP'li) geometrilerin hepsi taban ya da altında: G2 TP1/SL1 her kuralda negatif.
- Londra Asya-kırılımı (R2) her geometride negatif.
- H4 kırılımı (R5) ve 48-bar kırılım (R1) mutlak olarak pozitif, ama sürüklenmeyle aynı ve 2008-15'te negatif.

### Cited Findings
**Ana tablo (BUY, spread A $0,12, sonraki-bar açılışı girişi, 2008-01 → 2026-06-16)**

Sütun açıklamaları:
- **P** = gün-blok bootstrap P(EV>0).
- **P1** = aynı yıl + aynı UTC saati + aynı tutma süresiyle rastgele BUY (gün-kaydırma, 200 tekrar).
- **yüzd.** = kural ortR'sinin P1 dağılımındaki yüzdeliği.
- **iyimser** = sinyal barı kapanışından giriş, spread 0.

| Hücre | n (/hafta) | WR | ortR [%95] | P | yarılar | ×1,5 spread | iyimser | tek-poz | 2008-15 / 2016-26 | P1 (yüzd.) |
|---|---|---|---|---|---|---|---|---|---|---|
| **R0B_G1** SL1,5 TP yok 20 bar | 12.403 (12,9) | %36,5 | **+0,102** [+0,044, +0,160] | 1,00 | +0,087 / +0,117 | +0,088 | +0,127 | +0,079 (n 3.664) | +0,081 / +0,117 | +0,049 (0,96) |
| R0B_G2 TP1/SL1 12 bar | 12.403 | %48,1 | −0,036 | 0,00 | −0,063 / −0,008 | −0,053 | −0,002 | −0,046 | −0,064 / −0,016 | −0,053 (0,91) |
| R0B_G3 TP2/SL1,5 24 bar | 12.403 | %44,1 | +0,009 | 0,71 | −0,003 / +0,021 | −0,003 | +0,033 | +0,007 | −0,010 / +0,021 | −0,019 (0,97) |
| R1B_G1 48-bar kapanış kırılımı + D1/H4 trend, TP2/SL1,5 24 bar | 2.706 (2,8) | %45,3 | +0,039 | 0,90 | +0,028 / +0,049 | +0,029 | +0,061 | +0,039 | −0,018 / +0,063 | +0,007 (0,82) |
| R1B_G2 | 2.706 | | −0,018 | 0,19 | | | | | −0,085 / +0,011 | −0,036 (0,71) |
| R1B_G3 | 2.706 | | +0,030 | 0,79 | | | | | −0,028 / +0,055 | +0,031 (0,49) |
| R2B_G1/G2/G3 Londra Asya-high kırılımı | 1.153 (1,2) | | −0,072 / −0,070 / −0,014 | 0,02 / 0,01 / 0,41 | | | | | −0,175 / −0,014 (G1) | ≈ kural (0,45–0,51) |
| R3B_G1 NY sabah gücü, SL1,5 → NY16 | 1.087 (1,1) | %45,9 | +0,070 [−0,004, +0,142] | 0,97 | +0,013 / +0,126 | +0,056 | +0,094 | +0,070 | +0,014 / +0,093 | +0,016 (0,93) |
| R3B_G2 / G3 | 1.087 | | −0,043 / −0,073 | 0,10 / 0,01 | | | | | | 0,42 / 0,36 |
| R4B_G1 / G2 BB sıkışma kırılımı | 865 (0,9) | | −0,015 / +0,027 | 0,35 / 0,79 | | | | | | 0,47 / 0,995 |
| **R4B_G3** SL1,5 TP yok 12 bar | 865 (0,9) | %39,1 | **+0,122** [+0,014, +0,235] | 0,99 | +0,122 / +0,122 | +0,110 | +0,151 | +0,122 | +0,095 / +0,137 | +0,039 (0,96) |
| R5B_G1 H4 20-bar kırılım + D1 trend, TP2/SL1,5 ATR_H4 | 1.369 (1,4) | %51,0 | +0,078 [+0,020, +0,136] | 1,00 | +0,023 / +0,132 | +0,073 | +0,088 | +0,072 | −0,019 / +0,125 | +0,054 (0,75) |
| R5B_G2 TP1/SL1 | 1.369 | %52,9 | +0,058 | 0,98 | +0,024 / +0,092 | | +0,079 | +0,053 | −0,038 / +0,105 | +0,022 (0,87) |
| R5B_G3 SL1 TP yok | 1.369 | | +0,095 | 0,98 | +0,060 / +0,130 | | +0,116 | +0,107 | −0,004 / +0,145 | +0,088 (0,60) |

Kaynak: [results/summary.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results/summary.txt), [results/verdicts.csv](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results/verdicts.csv), [results/cells.csv](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results/cells.csv)

**Spread B ve aynı-bar varsayımı**
- Spread B (Duka'nın tarihsel gerçek ask−bid'i, medyan $0,36–0,40) ile mutlak EV:
  - R0B_G1 +0,048, R4B_G3 +0,075, R5B_G1 +0,055, R3B_G1 +0,022.
  - Diğer tüm hücreler ≤ 0.
- Aynı-bar=WIN iyimser sınırı stopsuz hücreleri değiştirmiyor. Braketli R0B_G2'yi −0,036'dan +0,006'ya çıkarıyor (braketler aynı-bar varsayımına duyarlı).
- Kaynak: [results/summary.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results/summary.txt)

**Yıllık ortR, R0B_G1** (tüm olaylar, spread A)

| 2008 | 2009 | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| +0,26 | +0,20 | +0,21 | +0,06 | −0,02 | −0,12 | −0,01 | −0,10 | +0,19 | +0,05 | −0,06 | +0,04 | +0,35 | +0,01 | +0,02 | −0,01 | +0,04 | +0,34 | +0,26 |

- Yıl başına 324–961 olay; 13/19 yıl pozitif.
- Negatif yıllar altının ayı dönemi (2012–15) ve 2018.
- Kaynak: [results/yearly.csv](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results/yearly.csv)

**POST-HOC (ön kayıtta yok; verdikti değiştirmez): sürüklenmeyi aşan kısım (kural − P1), yıl ve çağ bazında**

R0B_G1:
- 2008-15: +0,081 vs +0,024 → fark **+0,057** (yüzd. 0,89).
- 2016-26: +0,117 vs +0,057 → fark **+0,060** (yüzd. 0,92).
- 14/19 yılda fark > 0; yıllık fark medyanı +0,036. 2013-15 ayı piyasasında fark ≈0…+0,06: kural düşüşte kaybediyor ama rastgele BUY'dan daha az.
- Tek-pozisyon sürümü kendi tek-pozisyon plasebosuyla kıyaslandı: +0,079 vs +0,030 (yüzd. 0,98), 3,80 işlem/hafta.
- Spread B ile, aynı spread modelindeki plaseboya göre fark yine +0,058 (yüzd. 0,97). Yani sürüklenme-üstü kısım spread varsayımından bağımsız.
- Yoğunlaşma:
  - En iyi 5 gün hariç +0,077.
  - En iyi 20 gün hariç **+0,029**; toplam R'nin %72'si en iyi 20 günden (≈4.600 işlem gününden). Sağ kuyruğa bağımlı trend takibi imzası.
- Tek-pozisyon risk profili:
  - R dağılımının sd'si 1,70. p10/p50/p90 = −1 / −1 / +2,45, maks +15,6R. WR %35,6.
  - 18,5 yılda toplam +290R, **maks. düşüş −59R**.
  - Haftaların yalnız %46'sı pozitif (haftalık sd 3,2R).
  - Yıl toplamları: 2013 −15,5R, 2014 −11,2R, 2018 −30,5R, 2025 +60,3R.

Diğer hücrelerde sürüklenme-üstü fark:
- **R4B_G3**:
  - 2008-15 fark +0,079 (yüzd. 0,81), 2016-26 fark +0,084 (yüzd. 0,89); 10/13 yılda fark > 0.
  - Ama en iyi 20 gün hariç −0,030. Toplam R'nin %124'ü 20 günden geliyor.
- **R3B_G1**: fark yalnız 2016-26'da (+0,086). 2008-15'te −0,042.
- **R5B_G1**: 2008-15 −0,058, 2016-26 +0,070; 7/15 yıl.
- **R1B_G1**: 2008-15 −0,008, 2016-26 +0,046; 7/15 yıl.
- Kaynak: [results/posthoc.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results/posthoc.txt), [posthoc.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/posthoc.py)

**SELL kontrolleri (verdikt yok)**
- R0S_G1 (yeni 20-bar dibi SELL, stopsuz 20 bar): +0,050 vs P1 −0,016 (yüzd. 0,98). Ama 2008-15 +0,134 / 2016-26 **−0,017**.
- R2S_G3: +0,318, ancak P1 +0,227. 2008-15 +0,524 / 2016-26 −0,006.
- 2016-26'da hiçbir SELL aynası anlamlı pozitif değil.
- Kaynak: [results/summary.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results/summary.txt)

### Inferences
- XAU'da çalışan şey "kırılımı al **ve braketsiz zamanla tut**". Bu, defterin "braket ≠ zaman" (§3 ders 5) ve "gücü al" ilkeleriyle aynı yönde. Aynı tetikler TP1/SL1 braketiyle her yerde negatif.
- **MK-04'ün bağımsız replikasyonu tuttu.**
  - Farklı besleme (Dukascopy): +0,102 vs MK-04'ün +0,107.
  - Hiç görülmemiş 2008-15 dönemi, 2011-15 ayı piyasası dahil: sürüklenme-üstü fark +0,057, sonraki dönemle aynı büyüklükte.
- İcra ölçütü bu kez geçti (iyimser +0,127 vs gerçek +0,102, fark 0,025 ≤ 0,051). MK-04'te ✗'tu (+0,169 vs +0,107). Fark büyük olasılıkla besleme kaynaklı: candle_cache'te kapanış ↔ sonraki açılış boşluğu daha büyüktü. Bu satır ölçülmedi, çıkarımdır.
- Mutlak EV'nin yaklaşık yarısı altının yapısal yukarı sürüklenmesi (P1 +0,049). Sürüklenme 2013-15 gibi dönemlerde yıllarca negatife döner; kural da o yıllarda kaybeder.
- R5 (H4) ve R1 (48-bar + trend filtreleri), D1 trend filtresiyle sürüklenmeyi seçiyor. Kendi tetik katkıları yok: 2008-15'te negatif fark.

### Gaps
- Ana dönemde 1m yol yok. Stopsuz hücreler (G1, R4B_G3) yalnız SL dokunuşuna duyarlı, bu yüzden H1 ↔ 1m farkı küçük (kasada 0,005R).
- P1 plasebosu "aynı yıl + UTC saati" koşullu. Rejim (D1 trend) koşullu P2 de raporlandı (R0B_G1 yüzd. 1,00, R4B_G3 0,98), ama P2 ön kayıtta bilgi amaçlıydı.

## 4. Çoklu test düzeltmesi ve verdiktler (PROTOCOL §5 aynen)

### Takeaway
**Ön-kayıtlı karta göre R0B_G1 = LIVE (10/10).** Bu, MK-04'ün kendisidir.

Ancak seçim-düzeltmeli "sürüklenmeyi aşma" testi geçmiyor:
- max-z p = 0,47; 18 hücrenin hiçbiri boş dağılımın %95'ini (2,66) aşmıyor.
- Holm'u yalnız mutlak EV'de geçiyor (sürüklenme dahil).

Diğer sınıflar:
- **SHADOW (ön kayıt şemasıyla):** R4B_G3, R3B_G1, R1B_G1, R5B_G1/G2/G3.
  - R5 ve R1'in içeriği sürüklenmedir; protokol boşluğu yüzünden RED'e düşmüyorlar (aşağıya bakın).
- **RED:** diğer 11 hücre.

Benim okumam: R0B_G1 kartı geçen ilk XAU gün-içi kuralı. Kenar küçük ama gerçek: sürüklenmenin üstünde ~+0,05R/işlem; iki çağda ve kasada aynı işaret. Seçim düzeltmesi ve kuyruk bağımlılığı yüzünden "A" değil **B+**. Canlıya alma kararı kullanıcıda.

### Cited Findings
**Kart ölçütleri** (✓/✗ sırası 1 hacim · 2 EV+P≥0,90 · 3 yarılar · 4 ×1,5 spread · 5 icra · 6 tek-poz | 7 P1 ≥%95 · 8 2008-15>0 · 9 Holm · 10 kasa işareti):

| Hücre | kart 1–6 | ek 7–10 | z (P1) | p_sel (max-z) | gün-kümeli t (p) | Verdikt |
|---|---|---|---|---|---|---|
| **R0B_G1** | ✓✓✓✓✓✓ | ✓✓✓✓ | 1,79 | 0,47 | 3,42 (0,0003) Holm ✓ | **LIVE** |
| R4B_G3 | ✓✓✓✓✓✓ | ✓✓✗✗ | 1,71 | 0,51 | 2,16 (0,016) | SHADOW |
| R3B_G1 | ✓✓✓✓✓✓ | ✗✓✗✗ | 1,33 | 0,82 | 1,82 (0,034) | SHADOW |
| R5B_G1 | ✓✓✓✓✓✓ | ✗✗✗✗ | 0,69 | 1,00 | 2,57 (0,005) | SHADOW* |
| R5B_G2 | ✓✓✓✓✓✓ | ✗✗✗✗ | 1,16 | 0,90 | 2,04 (0,021) | SHADOW* |
| R5B_G3 | ✓✓✓✓✓✓ | ✗✗✗✗ | 0,16 | 1,00 | 2,00 (0,023) | SHADOW* |
| R1B_G1 | ✓✓✓✓✗✓ | ✗✗✗✓ | 1,04 | 0,95 | 1,32 (0,093) | SHADOW |
| R0B_G2, R0B_G3, R1B_G2/G3, R2B_G1/G2/G3, R3B_G2/G3, R4B_G1/G2 | 2+ kart ✗ ve/veya ortR ≤ P1 | | | | | RED |

- Boş max-z dağılımı (P1, 200 tekrar, 18 hücre): medyan 1,72, %95 **2,66**.
- Gerçek en büyük z: R4B_G2 2,23 (kendisi RED, EV +0,027).
- Holm (m=18, α=0,05 tek yönlü): yalnız R0B_G1 geçiyor (p=0,0003 < 0,05/18 = 0,0028). Sıradaki R5B_G1 p=0,005 > 0,05/17.
- \* **Protokol boşluğu:** §5'te "kart geçer ama 7–10'dan **2 veya daha fazlası** düşer" durumu tanımlı değil. RED tanımı (ortR ≤ P1 veya 2+ kart ✗) bunları kapsamıyor, `analyze.py` SHADOW atıyor. İçerik olarak R5 ailesi sürüklenmedir (P1 yüzd. 0,60–0,87, 2008-15 negatif). Gölgeye bile değer görmüyorum.
- Kaynak: [results/verdicts.csv](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results/verdicts.csv), [results/summary.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results/summary.txt), [PROTOCOL.md](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/PROTOCOL.md)

**"Denenen her şey" bağlamı (E23/E24)**
- Bu turda 18 birincil BUY hücresi + 18 SELL kontrolü.
- Aynı fikir ailesi daha önce şu turlarda görüldü:
  - MK-03/04/05: candle_cache 1h 2016-26.
  - DX-01: 356 geometri hücresi, decider kararları.
  - DX-02: 8 kural × 3 geometri.
  - XAU swing araştırması.
- R0 = MK-04 bir önceki turda post-hoc seçilmiş bir alt kümeydi. Bu yüzden R0 için gerçekten bağımsız kanıt yalnız şunlar:
  - (i) 2008-15 Dukascopy dilimi: fark +0,057, tek başına yüzd. 0,89.
  - (ii) broker kasası: §5.
- 2016-26 dilimi MK-04'ün gördüğü dönemle aynı (farklı besleme). Kaynak: [docs/KAPI_KAYIT_DEFTERI.md](/Users/melihcanodacioglu/Desktop/panel/docs/KAPI_KAYIT_DEFTERI.md) (MK-04 satırı, E23, E24)

### Inferences
- Kart ölçütü 7 (tek hücre P1 yüzdeliği ≥ %95) seçim düzeltmesi içermiyor. R0B_G1'in 0,96'sı, 18 hücrede tesadüfen beklenen ~1 "geçen" düzeyinde.
- R0B_G1'i ayakta tutan şey tek bir test değil, tutarlılık:
  - İki çağda aynı fark (+0,057 / +0,060).
  - 14/19 yıl.
  - Tek-poz yüzd. 0,98.
  - Spread B'de de fark +0,058.
  - Kasada (düşen D1 trendinde) fark +0,135.
  - İki bağımsız beslemede (candle_cache, Duka) aynı büyüklük.
- Bu tutarlılık tek bir p değerinden daha güçlü kanıt, ama "kenar küçük" gerçeğini değiştirmiyor.
- R4B_G3'ün sürüklenme-üstü farkı daha büyük (+0,08), ama 865 olayda en iyi 20 gün çıkınca negatife dönüyor ve kasada n=8. Ön kayıt verdikti SHADOW yerinde.

### Gaps
- Seçim düzeltmesi yalnız bu turun 18 hücresi için. Projenin XAU'ya önceki bakışları (DX-01/02, MK-03/05) boş dağılıma katılmadı; nicel olarak yapılamaz (farklı popülasyon/veri).

## 5. Broker kasası (2026-06-17 → 10-14, 1m yol, 17 hafta) + H1 ↔ 1m yol farkı

### Takeaway
- Kasa dönemi neredeyse tamamen **D1 EMA200 altında** (altın 4.340 → 3.995 → 4.150). Bu yüzden D1 trend filtreli R1–R5 BUY kuralları 4–22 kez tetiklendi; kasa onlar için bilgisiz.
- R0B_G1 (filtresiz):
  - n=205 / 56 gün, ortR **+0,145** (1m yol), P 0,71.
  - Aynı-saat rastgele BUY'a göre +0,135 (yüzd. 0,76; post-hoc).
  - Tek-poz 56 işlem +7,5R.
- H1 ve 1m yol neredeyse aynı (+0,140 vs +0,145).

### Cited Findings
- **Kasa, 1m yol** (n / ortR_1m / H1-yol / P):
  - R0B_G1: 205 / +0,145 / +0,140 / 0,71 [%95 −0,29, +0,61].
  - R0B_G2: 205 / −0,024 / −0,047.
  - R0B_G3: 205 / +0,058 / +0,053.
  - R1B_G1: 22 / +0,103.
  - R2B: 4.
  - R3B_G1: 10 / −0,288.
  - R4B_G3: 8 / −0,565.
  - R5B_G1/G2/G3: 12 / −0,255 / −0,460 / −0,635.
  - Kaynak: [results/holdout.csv](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results/holdout.csv)
- **H1 ↔ 1m yol farkı:** stopsuz hücrelerde ≤ 0,005R. Braketli R0B_G2'de 1m yol +0,023R daha iyi; H1 yol aynı-bar=LOSS yüzünden kötümser. R3B G2/G3'te n=10 ile ±0,2 fark var.
- **POST-HOC kasa plasebosu** (kasa günleri içinde gün-kaydırma, aynı UTC saati/tutma, broker H1 yolu, 500 tekrar):
  - R0B_G1: +0,140 vs P1 +0,005 (yüzd. 0,76). Tek-poz 3,3/hafta, +0,134 vs tek-poz P1 −0,023 (yüzd. 0,84). Çıkış kodları SL 113 / TIME 92.
  - R4B_G3: n=8, −0,565 vs −0,055.
  - Kaynak: [results/posthoc_holdout.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results/posthoc_holdout.txt), [posthoc_holdout.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/posthoc_holdout.py)

### Inferences
- Kasa yalnız işaret ölçütü için tasarlanmıştı (n küçük). R0B_G1'in işareti pozitif.
- Önemli nokta: kural sürüklenme olmayan (aşağı eğilimli) bir dönemde de rastgele BUY'ı geçti. Bu, "kural = sürüklenme" itirazını zayıflatır. Ama P=0,71 ile istatistiksel kanıt değildir.

### Gaps
- Kutu çevrimdışı. 10-14 06:57 UTC sonrası broker verisi yok.
- MK-04 gölgesi (`xau_shadow.jsonl`, 2026-10-12'den beri) okunmadı: kutuda, ve birkaç günlük veri anlamlı değil.

## 6. Hayatta kalan kural için decider entegrasyonu (R0B_G1 = MK-04)

### Takeaway
- **Tetik:** her H1 kapanışında bar high ≥ önceki 20 H1 barın en yüksek high'ı → sonraki H1 açılışında BUY (filtre yok).
- **Geometri:** SL = giriş − 1,5×ATR14(H1, kapanmış barlar). **TP yok.** Çıkış = giriş barı dahil 20. H1 barın kapanışı. Hafta sonu boşluğundan önce kapat.
- **Pozisyon:** aynı anda tek pozisyon; açıkken gelen tetikler atlanır. ≈3,8 işlem/hafta.
- **Beklenti:** uzun dönem tek-poz +0,079R/işlem; bunun ~+0,05R'si sürüklenme üstü.
  - Güncel ATR ile 1R ≈ $25 / 0,01 lot.
  - 0,01 lotta ≈ +$2/işlem, ≈ +$7,5/hafta.
  - 0,03 lotta ≈ +$6/işlem, ≈ +$22/hafta.
  - Haftaların %54'ü zararlı; tarihsel maks. düşüş −59R (0,03 lotta ≈ −$4.400).
- Decider'a "LLM onaylı" değil, **mekanik** olarak bağlanmalı: DX-02/IO-12'ye göre decider'ın seçim alfası yok.

### Cited Findings
- **Kural ve parametreler (ön kayıt, aynen):** R0 G1, SL 1,5×ATR_H1, TP yok, 20 bar. Hafta sonu/tatil (>3 saat boşluk) öncesi son bar kapanışında çıkış. Sinyal ile giriş barı arasında boşluk varsa olay atılır. — [PROTOCOL.md](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/PROTOCOL.md) §2–3, §9
- **Sıklık:** ham 12,9 tetik/hafta; tek-pozisyonla 3.664 işlem / 18,5 yıl = 3,80/hafta (kasada 3,3/hafta).
- **SL$ (= 1,5×ATR_H1):**
  - Tarihsel yıl medyanı: 2017-19 $3,3–3,5 · 2024 $8,1 · 2025 $15,0 · 2026 H1 $33,4.
  - Kasada medyan $25,1 (p10 $20,5 – p90 $33,9).
  - 0,01 lot = 1 ons → 1R ≈ $25.
  - Kaynak: [results/posthoc_holdout.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results/posthoc_holdout.txt)
- **R ve $ dağılımı (tek-poz, 2008-26):**
  - WR %35,6, medyan işlem −1R, p90 +2,45R, maks +15,6R.
  - Toplam +290R; maks. düşüş −59R; pozitif hafta %46; haftalık sd 3,2R.
  - Kaybeden yıllar: 2012-15 (toplam −33R) ve 2018 (−30,5R).
  - Kaynak: [results/posthoc_onepos.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results/posthoc_onepos.txt), [posthoc_onepos.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/posthoc_onepos.py)
- **Mevcut gölgeyle tanım farkları** (`yeni deneme/xau_shadow.py`, MK-04 gölgesi):
  1. Gölgenin ATR'si sinyal barını **hariç** tutuyor (önceki 14 bar). Bu çalışma sinyal barını **dahil** ediyor. İkisi de sızıntısız.
  2. Gölgede "çıkış barında gelen sinyal overlap sayılır". `one_position` ise o sinyali açar (ent > çıkış barı).
  - İkisi de küçük farklar. Canlıya bağlanacak sürüm tek tanıma sabitlenmeli.
  - Kaynak: [yeni deneme/xau_shadow.py](/Users/melihcanodacioglu/Desktop/panel/yeni%20deneme/xau_shadow.py)
- **Decider'ın mevcut XAU geometrisi** (TP1/SL1,5 ×ATR5) DX-01'de +0,003R, yani başabaş. G3-tipi zaman çıkışları decider'ın 5m tetiklerinde negatif (DX-02).
  - Bu kuralın kenarı decider'ın 5m kararlarına değil, **H1 ölçeğindeki tetik + 20 saatlik tutuşa** ait.
  - Kaynak: [decider_giris_kurallari.md](/Users/melihcanodacioglu/Desktop/panel/research_notes/Decider%20XAUUSD%20TPSL%20ve%20giri%C5%9F%20kurallar%C4%B1/decider_giris_kurallari.md), [tpsl_karsi_olgu.md](/Users/melihcanodacioglu/Desktop/panel/research_notes/Decider%20XAUUSD%20TPSL%20ve%20giri%C5%9F%20kurallar%C4%B1/tpsl_karsi_olgu.md)

### Inferences
**Önerilen entegrasyon (kullanıcı onayı gerekir; üretim koduna dokunulmadı)**
1. **Mekanik yol** (`policy_xau_mk04`): tetik H1 kapanışında. Emir sonraki dakikanın ilk ask'ında, ≤0,01–0,03 lot (decider demo tavanı). SL sabit; trailing, BE ve kısmi TP yok (M9/BE kilit kuralları reddedilmişti). 20. barda zaman çıkışı. Cuma son bardan önce kapat.
2. **LLM'in rolü:** yalnız kayıt ve açıklama. Veto hakkı **yok**: decider vetosu XAU'da doğrulanmadı ve E18 riski var. Veto istenirse önce gölge karnesiyle ölçülmeli.
3. **Mevcut XAU decider açılışlarıyla çakışma:** tek-pozisyon kuralı nedeniyle bu politikanın pozisyonu açıkken decider'ın 5m XAU BUY'ları ya kapatılmalı ya ayrı magic ile sayılmalı. Aksi halde portföy etkisi (E19) ölçülemez.
4. **Beklenti dili:** "+0,08R/işlem, yarısı altının sürüklenmesi". Ayı yıllarında (2013-15) yıllık −10…−15R normal. Getiri birkaç büyük trend gününden gelir; kısa vadeli zarar serileri kenarın bittiğini göstermez.
5. **Durdurma ölçütü (öneri):** 100 işlemde (≈6 ay) ortR, aynı dönemin rastgele-BUY tabanının altındaysa geri çek. Tek başına "zarar" ölçüt değildir, çünkü kural sürüklenmeyle birlikte kaybedebilir.

### Gaps
- Gerçek dolum (slip) ve swap/finansman maliyeti modellenmedi. 20 saatlik tutuş genelde bir gece taşıma demek. Pepperstone XAU long swap'ı ölçülmedi; R'den düşülmeli. Tahmini büyüklük bilinmiyor.
- Kural filtresiz. Post-hoc fikir **R0 ∧ D1>EMA200** (2013-15 kayıplarını azaltabilir) test **edilmedi**; ayrı ön kayıt gerekir.
- MK-04 gölgesinin gerçek `slip_r` alanı henüz okunamadı (kutu çevrimdışı).

### Defter satırı önerileri
(§6 biçimi; `docs/KAPI_KAYIT_DEFTERI.md`'ye bu oturumda yazılmadı. Kullanıcı/ana oturum ekler.)

| ID | Tarih | Fikir (kural, parametreler) | Sonuç (sayılar + hangi veri/dönem) | Sınıf |
|---|---|---|---|---|
| MK-06 | 2026-10-15 | **XAU mekanik kurallar uzun test** (`research/decider_xau_tpsl_20261015/mekanik/`, ön kayıt `PROTOCOL.md`). Dukascopy H1 BID+ASK 2008-01→2026-06 + broker 1m kasası 06-17→10-14. 6 BUY kuralı × 3 geometri; sonraki-bar açılışı + $0,12 spread; aynı-bar=LOSS; P1 aynı-yıl/UTC-saat rastgele BUY plasebosu; max-z seçim düzeltmesi + Holm | **R0B_G1 = MK-04 replikasyonu** (1h yeni 20-tepe BUY, SL 1,5×ATR_H1, TP yok, 20 bar): 12.403 olay, +0,102R [+0,044,+0,160] vs P1 +0,049 (yüzd. 0,96); görülmemiş 2008-15 +0,081 (fark +0,057), 2016-26 +0,117 (fark +0,060); yarılar +0,087/+0,117; ×1,5 spread +0,088; icra farkı 0,025 ✓; tek-poz 3,8/hafta +0,079 vs tek-poz P1 +0,030; Holm ✓ (p 0,0003); kasa +0,145 (n 205) vs rastgele +0,005 → **kart 10/10 LIVE**. Uyarılar: max-z p_sel 0,47 (sürüklenme-üstü fark seçim düzeltmesinden geçmiyor); en iyi 20 gün hariç +0,029; maks. düşüş −59R; 2012-15/2018 kaybeden yıllar | **B+** (kart LIVE; canlıya alma kullanıcı kararı) |
| MK-07 | 2026-10-15 | Aynı çalışma, diğer 17 hücre: R1 48-bar kırılım + D1/H4 trend; R2 Londra Asya-high kırılımı; R3 NY 09 gücü; R4 BB sıkışma kırılımı; R5 H4 20-bar kırılım + D1 trend; her biri TP1/SL1, TP2/SL1,5 veya stopsuz zaman çıkışıyla | **Braketli (TP'li) geometrilerin hepsi taban/altı** (TP1/SL1 her kuralda −0,02…−0,07). R2 her geometride negatif (2008-15 −0,175). R5 ve R1 mutlak + (+0,04…+0,10) ama P1 yüzd. 0,49–0,87 ve 2008-15 negatif → D1 trend filtresi sürüklenmeyi seçiyor, tetik katkısı yok. R4B_G3 (stopsuz 12 bar) +0,122 vs P1 +0,039, iki çağda fark +0,08, ama en iyi 20 gün hariç −0,030, kasa n=8 −0,565 → SHADOW. R3B_G1 fark yalnız 2016-26 → SHADOW. 2016-26'da hiçbir SELL aynası pozitif değil | X (R1/R2/R5, braketler) · C (R4B_G3, R3B_G1 gölge adayı) |
| E29 (§1 önerisi) | 2026-10-15 | Kart ölçütü 7 (tek hücre plasebo yüzdeliği ≥%95) ve ölçüt 9 (Holm, **mutlak** EV) çok hücreli turda **sürüklenme-üstü** seçim düzeltmesi sağlamaz; ayrıca ön kayıtta "kart geçer, ek ölçütlerden 2+ düşer" durumu tanımsız kaldı | MK-06: R0B_G1 10/10 LIVE ama max-z p_sel 0,47; R5 ailesi (içerik = sürüklenme) protokol boşluğuyla SHADOW | Önlem: kartta sürüklenme-üstü ölçütü seçim düzeltmeli yap (max-z p ≤ 0,10) ve verdikt şemasını tüm kombinasyonlar için tanımla |
