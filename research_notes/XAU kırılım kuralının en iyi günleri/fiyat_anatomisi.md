# XAU 1h 20-bar kırılım BUY kuralının (MK-04 / R0B_G1) en iyi günlerinin fiyat anatomisi

Kapsam: yalnız fiyat verisi (Dukascopy XAUUSD H1 BID, 2008-01-02 → 2026-06-14 girişleri; ana koşunun `END_MAIN=2026-06-17` kesimi aynen). Kural: H1 high ≥ önceki 20 H1 tepesi → sonraki H1 açılışında BUY (+$0,12), SL = giriş − 1,5×ATR14(H1), TP yok, 20 H1 bar sonra (veya >3 saatlik hafta sonu/tatil boşluğundan önceki son barda) çıkış, aynı anda tek pozisyon. Simülasyon `mekanik/` modülleri DEĞİŞTİRİLMEDEN import edilerek yeniden üretildi ve birebir tuttu: **n=3.664, WR %35,6, ort +0,0793R, toplam +290,5R** ([build.py çıktısı](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/build.py); referans [posthoc_onepos.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/results/posthoc_onepos.txt)).

**"En iyi gün" tanımı:** giriş barının **UTC takvim günü**; gün skoru = o gün GİRİLEN tek-pozisyon işlemlerinin R toplamı. 3.047 işlem günü var. Gruplar: **top-20**, **top-50**, **top-%1 = top-30**, **worst-20** (kontrast). Gün başına özellikler için "temsilci işlem" = günün |R|'si en büyük işlemi. Günlük fiyat özellikleri UTC takvim günü D1 barlarından (Cmt/Paz UTC barları → Pazartesi), ex-ante olanlar yalnız sinyal gününden ÖNCE kapanmış D1/W1 barlarıyla. Her özellik **EX-ANTE** (sinyal barı kapanışında bilinir, `xa_`) veya **EX-POST** (sonradan bilinir, `xp_`) olarak etiketli.

Kod + ham çıktılar: `/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/` — `build.py` (işlem+özellik tablosu), `days.py` (gün tablosu, CSV), `analyze.py` (yoğunlaşma/kümelenme/özellikler/mekanizma/altın günleri → `results/analysis.txt`), `extra.py` (aday dilimler, regresyon, top-20 ayrıntı → `results/extra.txt`), `placebo_feat.py` (koşulların rastgele-BUY'da etkisi → `results/placebo_features.txt`), `gold_days.py` (→ `results/gold_days.txt`). Gün listesi: [best_days.csv](/Users/melihcanodacioglu/Desktop/panel/research_notes/XAU%20k%C4%B1r%C4%B1l%C4%B1m%20kural%C4%B1n%C4%B1n%20en%20iyi%20g%C3%BCnleri/best_days.csv) (top-20 + 21-50 + worst-20; `in_top1pct_(top30)` bayrağı; 46 kolon); tüm günler `results/all_days.csv`.

## 1. En iyi günler hangileri ve getiri ne kadar yoğun? (tanım + "%72" mutabakatı)

### Takeaway
Tek-pozisyon simülasyonunda en iyi 20 giriş günü toplam R'nin **%61,6**'sını (178,9R) taşıyor; bu günler çıkınca ortalama +0,031R/işlem kalıyor. Önceki notlardaki "%72 / +0,029" rakamı tek-pozisyondan DEĞİL, örtüşmeli tüm-olay setinden (n=12.403, sinyal günü) geliyor. En iyi 30 gün (%1) toplamın %85'i, en iyi 50 gün %127'si — yani 50 gün dışındaki ~3.000 gün toplamda zarar.

### Cited Findings
- Tek-pozisyon (giriş UTC günü): en iyi 5 gün %20,1 (hariç +0,0635), 10 gün %35,6 (+0,0512), **20 gün %61,6 (+0,0306)**, 30 gün %85,1 (+0,0120), **50 gün %127,1 (hariç −0,0219)**; en kötü 20 gün −60,7R (hariç +0,0975) — [analysis.txt §1](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt)
- Örtüşmeli tüm-olay seti (n=12.403, sinyal UTC günü) ile eski hesap birebir yeniden üretildi: en iyi 20 gün %72,0, hariç +0,0292; en iyi 30 gün %97,4; en iyi 50 gün %142,6 (hariç −0,0455). Görev özetindeki "tek-pozisyon … %72" ifadesi bu iki seti karıştırıyor — [analysis.txt §1](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt); kaynak kod [posthoc.py satır 80-86](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik/posthoc.py)
- NY-17 işlem günüyle sıralama neredeyse aynı: top-20 payı %61,3; UTC top-20 ile NY-17 top-20 aynı işlemleri 17/20 paylaşıyor — [analysis.txt §1](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt)
- İşlem düzeyinde: en iyi 20 İŞLEM 180,9R (%62); R≥5 olan yalnız 71 işlem (%1,9) toplam 479,9R = net toplamın %165'i. Günlük R dağılımı: medyan −1,00, ort +0,095, sd 1,86, çarpıklık 1,74, p99 +6,60 — [analysis.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt), [extra.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/extra.txt)
- Top-20 günlerin 17'si tek işlemli; gün başına işlem top-20'de 1,15, genelde 1,20. Tüm top-20 temsilci işlemler **TIME** çıkışı (SL yok) — [analysis.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt)
- Worst-20 kontrastı bağlarla dolu: yalnız 12 gün ≤ −3R (3–4 ardışık SL), 151 gün ≤ −2R; worst-20'nin son 8 sırası −3/−2,5 bandından keyfî bağ kırma — [days.parquet kontrolü](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/all_days.csv)

**Top-20 listesi** (R = gün toplamı; saat = giriş saati UTC; gün% = altının giriş günü getirisi; ATR = getiri/ATR_D1(dün); aralık = gün aralığı/ATR_D1; +1/+3/+5g = giriş günü kapanışından sonraki getiriler; R@gün sonu = giriş günü bitiminde birikmiş R; mfe = maks. lehte R; post20 = çıkıştan sonraki 20 barda kaçırılan/kaçınılan R) — [extra.txt §E](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/extra.txt):

| # | tarih (gün) | saat | R | gün% | ATR | aralık | +1g | +3g | +5g | R@gün sonu | mfe | post20 | ATH'ye mesafe | D1>EMA200 | BBW %120 | önceki 24 barda kırılım |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2008-09-17 Çar | 10 | 15,63 | +11,0% | 3,69 | 3,94 | −1,1% | +4,0% | +1,6% | 15,79 | 20,2 | −2,7 | −24% | (EMA200 ısınmada) | 0,05 | 1 |
| 2 | 2023-10-13 Cum | 10 | 11,37 | +3,3% | 2,94 | 2,97 | −0,7% | +0,9% | +2,5% | 11,37 | 11,4 | −3,5 | −9% | hayır | 0,53 | 3 |
| 3 | 2012-11-06 Sal | 11 | 10,93 | +1,5% | 1,44 | 2,13 | +0,3% | +1,1% | +0,9% | 6,22 | 11,4 | −2,8 | −12% | evet | 0,23 | 7 |
| 4 | 2012-11-23 Cum | 8 | 10,38 | +1,1% | 1,16 | 1,49 | 0,0% | −1,5% | −2,0% | 10,38 | 13,2 | +0,3 | −10% | evet | 0,08 | 0 |
| 5 | 2016-09-06 Sal | 8 | 9,95 | +1,6% | 1,58 | 2,01 | −0,4% | −1,6% | −2,1% | 8,73 | 10,2 | −2,2 | −31% | evet | 0,03 | 0 |
| 6 | 2020-07-21 Sal | 7 | 9,91 | +1,4% | 1,36 | 1,72 | +1,5% | +3,1% | +6,1% | 5,85 | 12,4 | +4,6 | −5% | evet | 0,15 | 5 |
| 7 | 2022-02-23 Çar | 15 | 9,19 | +0,7% | 0,53 | 0,94 | −0,2% | −0,2% | +0,9% | 0,72 | 11,3 | −7,9 | −8% | evet | 0,15 | 0 |
| 8 | 2011-08-18 Per | 7 | 9,13 | +2,2% | 0,93 | 1,08 | +1,4% | +0,7% | −3,3% | 6,20 | 9,2 | +2,4 | −1% | evet | 0,10 | 4 |
| 9 | 2023-03-17 Cum | 7 | 8,95 | +3,5% | 2,54 | 2,71 | −0,6% | −0,9% | −0,5% | 8,95 | 9,1 | −1,7 | −7% | evet | 0,30 | 0 |
| 10 | 2024-03-20 Çar | 5,15 | 8,02 | +2,2% | 1,73 | 2,70 | −1,0% | −1,4% | −0,6% | 8,39 | 11,8 | −7,1 | −2% | evet | 0,04 | 1 |
| 11 | 2011-08-02 Sal | 12 | 7,91 | +2,2% | 1,75 | 2,12 | +0,4% | +0,6% | +6,6% | 4,87 | 9,0 | −0,3 | 0% | evet | 0,53 | 3 |
| 12 | 2020-02-18 Sal | 0 | 7,83 | +1,0% | 1,13 | 1,42 | +0,6% | +2,6% | +2,4% | 7,83 | 9,5 | +2,6 | −18% | evet | 0,05 | 3 |
| 13 | 2019-07-02 Sal | 14 | 7,68 | +3,3% | 2,20 | 2,51 | −0,9% | −2,3% | −2,5% | 8,90 | 10,4 | −3,4 | −28% | evet | 0,27 | 0 |
| 14 | 2015-05-13 Çar | 9 | 7,68 | +1,8% | 1,30 | 1,69 | +0,6% | +0,9% | −0,3% | 7,62 | 9,6 | +2,4 | −38% | hayır | 0,07 | 1 |
| 15 | 2025-05-05 Pzt | 2,23 | 7,61 | +2,9% | 1,13 | 1,20 | +2,0% | −0,5% | −2,9% | 0,23 | 4,9 | −1,7 | −5% | evet | 0,83 | 9 |
| 16 | 2025-04-15 Sal | 22 | 7,56 | +1,2% | 0,56 | 0,59 | +3,0% | +5,6% | +2,0% | 1,61 | 7,9 | −2,9 | −0,5% | evet | 0,01 | 0 |
| 17 | 2018-10-10 Çar | 19 | 7,46 | +0,3% | 0,33 | 0,78 | +2,3% | +2,8% | +2,4% | 0,51 | 7,8 | −0,2 | −38% | hayır | 0,09 | 0 |
| 18 | 2008-02-19 Sal | 1 | 7,44 | +2,5% | 1,32 | 1,49 | +1,4% | +1,7% | +2,3% | 7,44 | 8,7 | −0,9 | −3% | (EMA200 ısınmada) | 0,09 | 0 |
| 19 | 2019-06-19 Çar | 19 | 7,31 | +0,9% | 0,83 | 1,42 | +2,4% | +5,0% | +3,9% | 1,26 | 9,2 | +2,6 | −30% | evet | 0,01 | 0 |
| 20 | 2010-01-04 Pzt | 0,5 | 7,01 | +2,2% | 1,41 | 1,76 | −0,2% | +0,6% | +2,6% | 7,90 | 9,1 | −0,6 | −10% | evet | 0,15 | 2 |

(2025-05-05: iki işlem, temsilci 23 UTC olanı 4,73R; 2024-03-20 ve 2010-01-04: ilki SL, ikincisi büyük kazanç; ATH = 2008'den beri koşan D1 tepe maksimumu.)

### Inferences
- Kuralın bütün net kârı ~50 günden geliyor; geri kalan günler net negatif (−0,022R/işlem). Bu, bir "ortalama kenar" değil, kuyruk yakalama profilidir. Tek-pozisyon için doğru rakam %62 (20 gün) / %85 (30 gün); %72 rakamı örtüşmeli setin özelliği ve iki set için ayrı raporlanmalı.
- Top-20 günlerin 15'inde altın o gün ≥ +1 ATR_D1 yükseldi; 4'ünde (2022-02-23, 2018-10-10, 2019-06-19, 2025-04-15) giriş geç saatte (15–22 UTC) olduğu için asıl hareket ertesi güne düştü ("R@gün sonu" < 2).

### Gaps
- 2008-02-19 ve 2008-09-17 için D1 EMA200 henüz ısınmadı (veri 2008-01'de başlıyor, min 200 gün); bu iki gün EMA200 özelliklerinde "bilinmiyor" (ham tabloda 0 olarak kodlu — best_days.csv'de d1_gt_ema200 bu iki gün için yok sayılmalı). Grup trend payları 2008-12 sonrası günlerle hesaplandı.
- Worst-20 sıralaması −3R'lik bağlar yüzünden kısmen keyfî; kontrast için "≤ −3R olan 12 gün" daha temiz bir tanım.

## 2. En iyi günler zamanda kümeleniyor mu (kriz haftaları)? Kaç ayrı epizod? İyi gün iyi günü izliyor mu?

### Takeaway
Hayır. Top-20 = **19 ayrı epizod** (≤14 gün aralıkla), 18 ayrı ay, 13 ayrı yıl — rastgele 20 işlem gününden ayırt edilemez. Top-50 rastgeleden bile DAHA dağınık. Günlük R'de otokorelasyon hafif negatif; iyi günler iyi günleri izlemiyor. Kriz ayları (2008-10, 2020-03) top-20'de yok.

### Cited Findings
- Top-20: 19 epizod; tek çok-günlü epizod 2019-06-19 + 2019-07-02. Rastgele 20 işlem günü (2.000 çekiliş) medyan 19 epizod (%5 = 18), P(sim ≤ gözlenen) = 0,546 — [analysis.txt §2](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt)
- Top-50: 49 epizod, 46 ayrı ay; rastgele medyan 45 (%5 = 42), P(sim ≤ gözlenen) = 0,995 → gözlenen dağılım rastgeleden daha yayılmış — [analysis.txt §2](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt)
- Yıllara göre top-50 (gözlenen/beklenen): 2016 6/2,5, 2024 6/2,8, 2017 0/2,8; ki-kare p = 0,44 (yıl dağılımı işlem günü sayısıyla orantılı) — [analysis.txt §2](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt)
- Kriz dönemleri: 2008 krizinden yalnız 2008-09-17 (gün +%11,0); 2008-10/11 günleri top-20'de yok; 2020'den 2020-02-18 (COVID çöküşü ÖNCESİ) ve 2020-07-21; 2020-03 yok; 2011'den iki gün (08-02, 08-18); 2023'ten iki (03-17, 10-13) — [extra.txt §E](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/extra.txt)
- Günlük R Spearman otokorelasyonu (işlem günü sırası): lag1 −0,042 (p 0,02), lag2 +0,002, lag3 −0,030, lag5 +0,008; iş-günü takviminde (işlemsiz gün=0) lag1 −0,065 (p<0,001); haftalık lag1 −0,021; aylık lag1 +0,066 — [analysis.txt §2](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt)
- P(sonraki 5 işlem gününde top-%10 gün | bugün top-%10) = 0,384 vs koşulsuz 0,427 — [analysis.txt §2](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt)
- Ay düzeyinde: en iyi 10 ay (2020-07 20,0R; 2023-10 19,9; 2012-11 18,3; 2011-08 17,4; 2009-05 15,8; 2016-02 15,5; 2010-10 14,6; 2023-03 14,2; 2026-01 14,2; 2025-01 13,4) toplamın %56'sı (222 ay içinde) — [analysis.txt §2](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt)

### Inferences
- "En iyi günler aslında birkaç kriz epizodu" hipotezi reddedildi: kuyruk 18,5 yıla yayılmış bağımsız tek-günlük şoklardan oluşuyor. Bu, (a) sonucu tek bir döneme bağımlılıktan koruyor ama (b) iyi günü önceden "rejimle" yakalamayı imkânsıza yakın kılıyor — iyi bir günden sonra büyütmek/küçültmek (otokorelasyon) işe yaramaz.
- Ay düzeyinde yoğunlaşma günden daha az aşırı değil (%56 / 10 ay) — kenarın aylık bazda bile birkaç aya dayandığı anlamına gelir; aylık lag1 +0,07 zayıf.

### Gaps
- Epizod eşiği (14 gün) keyfî; 7 ve 30 gün denenmedi (top-20'nin 18 ayrı ayda olması sonucu değiştirmeyeceğini düşündürüyor).

## 3. Hangi özellikler en iyi günleri sıradan ve en kötü günlerden ayırıyor? (etki büyüklükleri, EX-ANTE vs EX-POST)

### Takeaway
Ayıran özelliklerin neredeyse tamamı EX-POST (altının o günkü hareketi, işlem içi volatilite genişlemesi). EX-ANTE tarafta en iyi günlerin imzası **"sessiz saatlik taban"**: ATR_H1/ATR_D1 düşük (AUC 0,22), ATR_H1 kendi geçmişine göre düşük (0,32), Bollinger sıkışması (0,35), sabah/Asya-Londra saatleri, 52 haftalık tepeye yakınlık (0,66). Ama işlem düzeyinde dürüst sınamada bunlar **ortalama R'yi değil kuyruk büyüklüğünü** tahmin ediyor (dar stop = daha çok SL + daha büyük kazanan). Ortalama R'de iki yarıda ve yıl-sabit-etkili regresyonda ayakta kalan iki ex-ante sinyal var: **seri kırılım cezası** (son 24 barda ≥2 kırılım, t −3,5) ve **ATH yakınlığı** (t +2,5). Ancak ATH etkisi büyük ölçüde altının genel sürüklenme rejimi (rastgele BUY'da da var). Her şey post-hoc; Haziran–Eylül 2026 uzatmasında seri-kırılım cezası tersine döndü (n küçük).

### Cited Findings
**Gün düzeyi (temsilci işlem), top-20 vs diğer günler (worst-20 hariç); AUC = P(top-gün değeri > diğer); 54 özellik → Bonferroni α = 0,0009** — [feature_effects.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/feature_effects.csv), [analysis.txt §3](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt):
- EX-ANTE, ATR_H1/ATR_D1: top-20 medyan 0,125 vs 0,171; Cohen d −0,89; AUC 0,219 (p<0,001; top-50 AUC 0,271, p<0,001; top-30 AUC 0,235, p<0,0001) — Bonferroni'yi geçen tek ex-ante özellik.
- EX-ANTE, ATR_H1 500-bar yüzdeliği: 0,237 vs 0,438; AUC 0,316 (p 0,004); top-50 0,286 (p<0,001).
- EX-ANTE, BB(20,2) genişliği 120-bar yüzdeliği: 0,096 vs 0,242; AUC 0,350 (p 0,020); top-50 0,358 (p 0,001). Top-20'nin %70'i ≤%20 yüzdelikte, diğer günlerin %44'ü.
- EX-ANTE, sinyal saati (UTC): top-50 AUC 0,368 (p 0,001), top-30 medyan 7,5 vs 12; top-20 seans: Asya %35 / Londra %35 / NY %30 vs diğer %25 / %34 / %41. 13–14 UTC (diğer günlerin en sık giriş saatleri, %25) top-20'de yalnız 1 kez.
- EX-ANTE, 52-haftalık tepeye mesafe: −2,2 vs −5,8 ATR_D1; AUC 0,663 (p 0,014); top-30 0,662 (p 0,003). ATH'ye mesafe % : −9,5% vs −13,4%, AUC 0,58 (p 0,21).
- EX-ANTE, D1 EMA50 eğimi (10 gün, ATR biriminde): 0,84 vs 0,18; AUC 0,60 (p 0,13; top-50 p 0,017). 20 günlük önceki getiri medyanı +3,1% vs +0,6% (AUC 0,61, p 0,11).
- EX-ANTE, trend durumu (EMA200 ısınması sonrası): D1>EMA50 top-20 %72 vs diğer %59; D1>EMA200 %83 vs %68; W1>EMA20 %78 vs %64 — ama worst-20'de de %68 / %79 / %68, EMA50>EMA200 worst-20'de %89 → trend durumu en iyiyi en kötüden ayırmıyor — [ek kontrol, all_days.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/all_days.csv)
- EX-ANTE, kırılım barı: gövde/aralık oranı 0,33 vs 0,54 (AUC 0,365, p 0,037); seviyenin ötesine taşma (high) 0,34 vs 0,49 ATR_H1 (AUC 0,455, p 0,49); kapanış-seviye farkı AUC 0,446; gövde/ATR AUC 0,40 (p 0,13). Tick hacmi / aynı-saat medyanı 1,105 vs 1,117 (AUC 0,511, p 0,86) — **kırılım barının hacmi en iyi günleri ayırmıyor**.
- EX-ANTE, açılış boşluğu (gap/ATR_D1): AUC 0,444 (p 0,39); 24 saatlik şok barı (maks gövde/ATR_H1): 1,63 vs 1,87, AUC 0,39 (p 0,09) — en iyi günler şok/gap SONRASI değil.
- EX-ANTE, ATR_D1 rejimi (252 g yüzdelik): 0,52 vs 0,45, AUC 0,61 (p 0,11); top-50'de 0,517 (p 0,69) — **en iyi günler yüksek-volatilite rejiminde değil**. Tam-örneklem ATR yüzdeliği (EX-POST, betimsel) 0,39 vs 0,50.
- EX-ANTE, "ilk kırılım" (önceki 20-tepe olayından bu yana bar): top-20 22 vs 23 (AUC 0,515); ama **worst-20 8 bar** (AUC 0,342, p 0,015) ve son 24 barda kırılım sayısı worst-20'de 3 vs 1 (AUC 0,621, p 0,05). Seviye yaşı: top-20 16 bar vs 10, worst-20 5 bar (AUC 0,36, p 0,03).
- EX-POST: MFE 9,5 vs 1,0R (AUC 0,997); giriş günü sonunda birikmiş R 7,5 vs −0,37 (0,935); altının giriş günü getirisi 1,34 vs 0,28 ATR_D1 (0,911; d 2,08); gün aralığı 1,71 vs 0,92 ATR_D1 (0,827); işlem içi volatilite genişlemesi (ort. TR / giriş ATR_H1) 1,98 vs 1,12 (0,840); tutma 20 vs 9 bar; sonraki 1/3/5 gün getirisi +0,3%/+0,8%/+1,3% vs 0,0/+0,1/+0,2% (AUC 0,59/0,61/0,59, p 0,16/0,09/0,19).
- Haftanın günü (n=20, anlamlılık yok): Sal 8, Çar 6, Cum 3, Pzt 2, Per 1; diğer günler ~%20 eşit; worst-20'de Perşembe %35 — [analysis.txt §3](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt)

**İşlem düzeyi dürüst sınama (tek-poz n=3.664; beşli dilimler, iki yarı 2008-16 / 2017-26)** — [exante_quintiles.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/exante_quintiles.csv), [candidate_slices.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/candidate_slices.csv):
- ATR_H1/ATR_D1 beşlisi: ortR Q1..Q5 = 0,107 / 0,081 / 0,121 / 0,002 / 0,079 (monoton değil; yarılarda Q5−Q1 +0,002 / −0,060, işaret tutarsız) ama P(R≥5) Q1 %4,0 vs Q5 %0,7; AUC(R≥5) 0,313.
- ATR_H1 500-bar yüzdeliği: Q1 0,140 → Q5 0,043 (yarılar −0,091 / −0,103, tutarlı); P(R≥5) %4,3 vs %0,7. "≤0,2" dilimi: 0,122 vs 0,066, Welch p 0,46.
- Sinyal saati beşlisi: Q1 (en erken saatler) 0,228, diğer dilimler 0,015–0,078; yarılar −0,222 / −0,202. "Asya 23-06 UTC" dilimi: 0,160 vs 0,059, Welch p 0,18 (yarılar +0,010 / +0,180).
- **Seri kırılım (son 24 barda ≥2 önceki kırılım):** −0,019 (n=1.643) vs +0,159; Welch t −3,16 (p 0,002); yarılar −0,221 / −0,139; yılların %68'inde fark negatif.
- **ATH'ye ≤%2:** +0,322 (n=453) vs +0,045; Welch t 2,85 (p 0,005); yarılar +0,170 / +0,389. Etkileşim: tekil (≤1 kırılım) ∧ ATH≤%2 → +0,709 (n=184), seri ∧ ATH≤%2 → +0,057, tekil ∧ ATH>%2 → +0,104, seri ∧ ATH>%2 → −0,033 — [extra.txt §B](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/extra.txt)
- Çoklu regresyon (standart özellikler + yıl sabit etkisi, gün-kümeli SE): seri-kırılım yoğunluğu β −0,106 R/sd, **t −3,54**; ATH≤%2 β +0,088, **t +2,45**; Asya t +1,26; ATR yüzdeliği t −0,91; BB genişliği t +0,32; seviye yaşı t +1,34 — [extra.txt §C](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/extra.txt)
- **Plasebo (her H1 barından aynı geometriyle rastgele BUY, n=110.104):** seri kırılım sonrası rastgele barlar da kötü (+0,012 vs +0,052, fark −0,040); kuralda fark −0,086 → kurala özgü kısım ≈ −0,05. ATH≤%2 rastgele barlarda +0,240 vs +0,008 (fark +0,232), kuralda +0,275 → **ATH etkisinin ~%85'i altının genel rejim sürüklenmesi**. Tekil∧ATH: kural barı +0,732 vs aynı koşulda kural-dışı bar +0,477. Asya saati: kuralda +0,039, rastgelede −0,030 (kurala özgü, küçük). Düşük ATR: kuralda +0,057, rastgelede −0,013 — [placebo_features.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/placebo_features.txt)
- Tekil∧ATH≤%2 yalnız 9 yılda var (2008-11, 2020, 2023-26); gün-kümeli t 4,50; en iyi 3 işlem hariç +0,591; WR %47,3, medyan −0,23R — [placebo_features.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/placebo_features.txt)
- Dukascopy uzatması 2026-06-17 → 09-30 (görülmemiş, n=56, +0,093R, toplam +5,2R; en iyi 5 gün +16,8R, hariç −0,233R): seri kırılım +0,181 (n=26) vs tekil +0,016 → **in-sample cezanın tersi**; ATH≤%2 koşulunda hiç işlem yok (altın ATH'nin %19–28 altında) — [build.py END=2026-10-01 koşusu, trades_ext.parquet](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/build.py)

### Inferences
- En iyi günlerin ex-ante "imzası" (düşük saatlik ATR, BB sıkışması, sabah saatleri) mekanik olarak R paydasından geliyor: SL = 1,5×ATR_H1 dar olduğunda aynı dolar hareketi daha çok R'dir; ama dar stop daha sık da vurulur. Sonuç: bu özellikler kuyruğun boyunu büyütüyor, ortalamayı değil. Bunlarla filtrelemek beklentiyi anlamlı artırmaz, yalnız dağılımı daha çarpık yapar.
- Ortalama R'de tutarlı iki sinyal: (1) seri kırılımdan kaçın — ilk/tekil kırılım daha iyi; worst günler tam olarak gün içinde 3–4 kez yeniden kırılıp her seferinde SL olan "testere" günleri. (2) ATH yakınlığı — ama bu kırılım tetiğinin değil altının ATH yakınındaki genel momentum rejiminin özelliği; kural buna yalnız küçük bir artı ekliyor. İkisi de post-hoc, 30+ özellik taramasından seçildi ve 3,5 aylık uzatmada seri-ceza tersine döndü → filtre değil, ön-kayıtlı ileri test adayı.
- Kırılım barının hacmi, seviyenin ne kadar aşıldığı, açılış boşluğu ve D1/W1 trend durumu en iyi günleri ayırmıyor; trend durumu worst günlerde de aynı sıklıkta.

### Gaps
- Ex-ante özelliklerin AUC'leri tek bir örneklemde; ileri doğrulama yalnız 56 işlemlik uzatmada yapılabildi. Broker 1m kasası (`xau_1m_utc.csv.gz`, 2026-06-17 → 10-14) bu anatomide kullanılmadı; uzatma Dukascopy H1 ile yapıldı.
- Plasebo, kural olaylarını rastgele barlarla kıyaslıyor; tek-pozisyon kısıtlı plasebo bu koşullar için koşulmadı.
- Swap/finansman maliyeti modellenmedi (20 saatlik tutuş).

## 4. Mekanizma: sağ kuyruğu ne üretiyor — sıkışma sonrası volatilite genişlemesi mi, güçlü trend devamı mı, gap/şok mu, çok-günlü bacak mı?

### Takeaway
Baskın mekanizma **gün-içi volatilite genişlemesi**: top-20 işlemlerinin %90'ında işlem içi volatilite girişteki saatlik ATR'nin ≥1,5 katına çıktı (diğer günler %29), %65'i ex-ante BB sıkışmasından geliyor (diğer %16) ve top-20 R'sinin **%73'ü giriş UTC günü bitmeden** birikti. Çok-günlü trend bacağı ikincil (top-20'nin %25'i), gap/şok sonrası giriş neredeyse yok (%5). R'nin büyüklüğünü %83 oranında hareketin kendisi (ATR_D1 biriminde ~1,35 günlük ATR), %17 oranında dar payda açıklıyor. 20 barlık zaman çıkışı bacağı kesmiyor; tersine top-20'de çıkıştan sonraki 20 bar ortalama −1,15R.

### Cited Findings
- Top-20 temsilci işlem ort 8,90R: giriş günü sonuna kadar 6,54R, sonrası 2,37R → R'nin giriş günü SONRASI payı %27 (top-50 %23; diğer günler %36); TIME çıkışı %100; tutma medyanı 20 bar; MFE ort 10,32R, geri verme 1,41R (MFE'nin %86'sı yakalandı); çıkış = işlemin en yüksek kapanışı %45 (diğer %22); çıkış sonrası 20 bar ort −1,15R, yalnız %30'u pozitif (top-50: −0,10R, %50) — [analysis.txt §4](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt)
- İşlem içi volatilite genişlemesi (ort. TR / giriş ATR_H1) medyanı: top-20 1,98, top-50 1,77, diğer 1,11, worst-20 1,37 — [analysis.txt §4](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt)
- Mekanizma bayrakları (top-20 % / top-50 % / diğer % / worst-20 % / top-20 R payı) — [mechanism_flags.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/mechanism_flags.csv):
  - sıkışma→genişleme (BBW ≤%20 ∧ genişleme ≥1,5): 65 / 48 / 16 / 20 / %65
  - yalnız sıkışma (ex-ante BBW ≤%20): 70 / 62 / 44 / 40 / %70
  - genişleme ≥1,5 (ex-post): 90 / 78 / 29 / 45 / %92
  - güçlü trend devamı (c>EMA50>EMA200 ∧ 52wH'ye ≤1 ATR_D1): 30 / 30 / 12 / 25 / %29
  - ATH'ye ≤1 ATR_D1: 15 / 22 / 9 / 25 / %14
  - boşluk/şok (|gap|≥0,5 ATR_D1 veya son 24 saatte ≥3 ATR_H1 gövde): 5 / 8 / 15 / 10 / %4
  - çok-günlü bacak (R'nin >%50'si giriş günü sonrası): 25 / 18 / 9 / 0 / %22
  - ilk kırılım (önceki 20-tepeden ≥20 bar sonra): 70 / 68 / 60 / 35 / %71
  - yüksek vol rejimi (ATR_D1 252g ≥p80): 30 / 22 / 18 / 0 / %31
  - giriş günü altın ≥ +2 ATR_D1 (ex-post): 20 / 16 / 0,9 / 0 / %24
- Öncelikli tekil sınıflama, top-50 (n, toplam R): sıkışma→genişleme 24 / 187,5R; diğer 18 / 128,9R; trend devamı 6 / 39,6R; şok/gap 2 / 13,3R — [analysis.txt §4](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt)
- R paydası ayrıştırması: R≥5 işlemlerde çıkış hareketi medyan 1,35 ATR_D1 ve ATR_H1/ATR_D1 0,139; 0<R<5 kazananlarda 0,375 ATR_D1 ve 0,180 → log-oran payı hareket %83, dar payda %17 — [extra.txt §D](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/extra.txt)
- Top-20 içindeki çeşitlilik: EMA200'ü bilinen 18 günün 3'ü D1<EMA200 (2023-10-13, 2015-05-13, 2018-10-10), 7'si D1<EMA50; 6 gün ATH'nin %24–38 altında (2008-09-17, 2016-09-06, 2019-07-02, 2015-05-13, 2018-10-10, 2019-06-19), 2020-02-18 %18 altında — [extra.txt §E](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/extra.txt)
- Çıkıştan sonra hareketi sürdüren top-20 işlemleri (post20 > 0): 2020-07-21 +4,6R, 2020-02-18 +2,6, 2019-06-19 +2,6, 2011-08-18 +2,4, 2015-05-13 +2,4, 2012-11-23 +0,3; diğer 14'ünde çıkıştan sonra geri dönüş (2022-02-23 −7,9R, 2024-03-20 −7,1R) — [extra.txt §E](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/extra.txt)

### Inferences
- Tipik en iyi gün anatomisi: sakin bir Asya/Londra sabahında (dar saatlik ATR, BB sıkışması) yaşlı bir 20-bar tepesi aşılıyor → aynı UTC gününde altın 1–3 günlük ATR yükseliyor (genellikle NY seansında) → stop hiç tehdit edilmiyor (MAE medyan −0,42R) → 20 bar sonra zaman çıkışı, çoğunlukla hareketin tepesine yakın. Yani "kırılım sonrası gün-içi volatilite genişlemesi"; trend devamı çok-günlü bacak olarak değil, aynı günün genişlemesi olarak.
- Güçlü trend durumu kuyruğun gerekli koşulu değil (top-20'nin %30'u), gap/şok ise neredeyse hiç (şok SONRASI kırılımlar zaten genişlemiş bir ATR ile girdiği için R küçük).
- 20 barlık zaman çıkışının uzatılması top-20'ye fayda sağlamazdı (çıkış sonrası ort −1,15R); kuyruk zaten gün-içi bir olay.

### Gaps
- "Sıkışma→genişleme" bayrağının genişleme kısmı ex-post ve kaybeden işlemlerde kısa tutuş yüzünden yanlı ölçülüyor (diğer günlerde bu bayrak ort −0,67R çıkıyor) — sınıflama betimseldir, sinyal değildir.
- Olay/haber atfı (FOMC, savaş, banka krizi vb.) kapsam dışı bırakıldı (yalnız fiyat verisi); en iyi günlerin hangi takvim olaylarına denk geldiği bu notta ölçülmedi.

## 5. Kuralın en iyi günleri altının en büyük yükseliş günleri mi?

### Takeaway
Büyük ölçüde evet, ama birebir değil. Kural altının en iyi 50 yükseliş gününün **hepsinde** o gün işleme girdi ve bu 50 günden toplam R'nin %53'ünü (yüzde getiri sırası) / %66'sını (ATR-normalize sıra) aldı; altının en iyi 100 günü (ATR-normalize, işlem günlerinin ~%2'si) çıkarılınca kural **−0,013R/işlem**. Ters yönde: kuralın top-20 gününün 14'ü altının en iyi %10 günü içinde, ama yalnız 5'i en iyi 50 günde (medyan sıra 172/4.753) — dar saatlik ATR ve giriş saati, "en büyük % gün" ile "en büyük R günü" arasında fark yaratıyor.

### Cited Findings
- Altının en iyi 50 günü (% getiri): o gün giriş %100, açık pozisyon %100; giriş R ort +3,08 (medyan +2,37), toplam giriş R 154,2; o gün açık işlemlerin R toplamı 188,9 — [analysis.txt §5](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt), [gold_top50_ret1.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/gold_top50_ret1.csv)
- Altının en iyi 50 günü (ATR_D1-normalize): giriş %98, giriş R ort +3,89 (medyan +3,75), toplam 190,4 — [gold_top50_ret_atr.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/gold_top50_ret_atr.csv)
- Altının en iyi k gününde girilen işlemlerin toplam R payı ve bu günler hariç ortR (% getiri / ATR-normalize): k=20 %24 / %27 (hariç +0,061 / +0,058); k=47 (%1) %49 / %61 (+0,041 / +0,031); k=50 %53 / %66 (+0,038 / +0,028); **k=100 %93 / %116 (+0,006 / −0,013)**. Altının en kötü 50 gününde yalnız 4 / 7 giriş, hepsi −1R — [gold_days.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/gold_days.txt)
- Gün R'si, giriş günü altın getirisi dilimine göre (ATR_D1): ≤−1: −1,16 (n 37); −1…−0,5: −1,20; −0,5…0: −1,00 (n 603); 0…0,5: −0,38 (n 1.271); 0,5…1: +1,00 (n 704); 1…2: +2,68 (n 271); >2: +3,53 (n 36) — [gold_days.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/gold_days.txt)
- Kuralın top-20 günleri altın sırasında: % getiri top-50'de 5/20, top-%1'de (47) 4/20, top-%10'da 14/20, medyan sıra 172/4.753; ATR-getiri top-50'de 6/20. Top-50 kural gününün 9'u altın top-50'de, 36'sı top-%10'da. Uç örnekler: 2022-02-23 (altın sırası 1.076; 15 UTC giriş, hareket ertesi Asya'da), 2018-10-10 (sıra 1.655; 19 UTC giriş, ertesi gün sırası 100), 2025-04-15 (sıra 496; 22 UTC giriş, ertesi gün sırası 44) — [analysis.txt §5](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt)
- Spearman(gün R, altının giriş günü ATR-getirisi) = 0,601; (gün R, ertesi gün getirisi) = 0,129 — [analysis.txt §5](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/analysis.txt)
- Altının en büyük günlerinde kuralın kaçırdığı/az aldığı örnekler: 2026-01-28 (+%6,6, giriş −1R ama açık işlemler +4,2R), 2026-02-06 (+%5,5, +0,43R), 2016-02-11 (+2,5 ATR, giriş +0,45R) — [gold_top50_ret1.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/gold_top50_ret1.csv), [gold_top50_ret_atr.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/anatomi/results/gold_top50_ret_atr.csv)

### Inferences
- Kural pratikte "altının nadir büyük yükseliş günlerine her seferinde bilet alan, diğer günlerde −1R'lik küçük primler ödeyen" bir opsiyon gibi davranıyor: altın günü +0,5 ATR_D1'in altında kapattığında kural ortalama zarar ediyor; tüm net kâr ~100 büyük yükseliş gününden. Daha önce ölçülen sürüklenme-üstü fark (+0,079 vs plasebo +0,030) "o büyük günlere rastgele BUY'dan daha iyi konumlanma" olarak okunmalı.
- Kuralın en iyi günü = "altının en büyük % günü" değil, "saatlik ATR'ye göre en büyük gün-içi genişleme" günü; geç saatte girilen işlemlerde hareket ertesi takvim gününe düşüyor (gün tanımı UTC olduğu için).
- Bu profil, kenarın hangi yılda/ayda olacağını değil, kaç büyük yükseliş günü olacağını bekleyen bir bahis; 2012-15 gibi az büyük yükseliş günü olan dönemlerde kural doğal olarak eriyor.

### Gaps
- "Büyük gün" sayısının ileriye dönük tahmini (rejim) bu çalışmada yapılmadı; §2 sonuçları bunun zor olduğunu gösteriyor.
- Kuralın büyük günlerde rastgele BUY'dan ne kadar iyi olduğunu (aynı gün, aynı saat) doğrudan ölçen gün-koşullu plasebo koşulmadı.

## Defter satırı önerileri

(docs/KAPI_KAYIT_DEFTERI.md düzenlenmedi; aşağıdakiler öneri.)

| ID önerisi | tarih | fikir | sonuç | sınıf |
|---|---|---|---|---|
| MK-08 | 2026-10-16 | **MK-04 en iyi günlerin fiyat anatomisi** (`research/xau_best_days_20261015/anatomi/`). Tek-poz n=3.664, gün = giriş UTC günü | Tek-poz yoğunlaşma: top-20 gün %61,6 (hariç +0,031), top-30 %85, top-50 %127 (hariç −0,022). **"%72" rakamı örtüşmeli tüm-olay setine ait** (n=12.403), tek-pozisyona değil. Top-20 = 19 ayrı epizod, rastgeleden ayırt edilemez; kriz kümelenmesi yok, günlük R otokor ≈0/negatif. Kuyruk = gün-içi volatilite genişlemesi (top-20'nin %90'ı genişleme ≥1,5×, %73 R aynı UTC gününde, gap/şok %5, çok-günlü bacak %25); 20-bar çıkış bacağı kesmiyor (çıkış sonrası −1,15R). Altının en iyi 100 günü (ATR-normalize) çıkınca kural −0,013R. Kırılım barı hacmi/taşma/gap/trend durumu en iyi günleri ayırmıyor | Betimsel (kenar sınıfı değişmez: MK-04 B+) |
| MK-09 | 2026-10-16 | Ex-ante kuyruk imzası: düşük ATR_H1/ATR_D1, BB sıkışması, sabah saatleri | Kuyruk boyunu tahmin ediyor (P(R≥5) Q1 %4 vs Q5 %0,7; gün AUC 0,22) ama ortalama R'yi değil (beşli monoton değil, yarılar tutarsız) — dar stop = daha çok SL + daha büyük kazanan; filtre olarak beklenti katmaz | X (filtre olarak) |
| MK-10 | 2026-10-16 | Seri kırılım cezası (son 24 H1'de ≥2 önceki 20-tepe kırılımı → atla) | In-sample −0,019 vs +0,159 (Welch t −3,2; yıl-FE regresyon t −3,5; iki yarı negatif; worst günlerin imzası). Rastgele-BUY'da da −0,040 (kurala özgü kısım ≈ −0,05). Post-hoc (30+ özellikten) ve 2026-06→09 uzatmasında TERS (+0,181 vs +0,016, n=56) | C (ön-kayıtlı ileri test adayı; canlıya bağlanmaz) |
| MK-11 | 2026-10-16 | ATH yakınlığı (≤%2) / tekil kırılım ∧ ATH≤%2 | +0,322 vs +0,045 (t 2,85); tekil∧ATH +0,709 (n=184, gün-kümeli t 4,5) ama rastgele-BUY'da ATH≤%2 +0,240 vs +0,008 → etkinin ~%85'i altının ATH-yakını sürüklenme rejimi, kırılıma özgü değil; yalnız 9 yılda gözlenebiliyor; uzatmada koşul hiç oluşmadı | C (rejim gözlemi; kural filtresi değil) |

Yöntem tuzağı önerisi (§1 için): "Yoğunlaşma oranları (en iyi N gün payı) örtüşmeli olay seti ile tek-pozisyon seti arasında belirgin farklı (%72 vs %62); rapor ederken hangi set ve hangi gün tanımı (sinyal/giriş, UTC/NY-17) kullanıldığı yazılmalı."
