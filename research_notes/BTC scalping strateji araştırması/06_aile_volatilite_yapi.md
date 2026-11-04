# BTC scalp ailesi: volatilite + fiyat yapısı (sıkışma kırılımı, ABD seansı straddle, VWAP, açılış aralığı, likidite süpürme, makro dakika)

Kapsam: 2026-10-22. Yalnız mevcut veriyle sızıntısız backtest: yeni indirme yok, kutuya ya da Supabase'e dokunulmadı, commit yok.
Tüm dosyalar [fam_volyapi/](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/) altında.
Ön kayıt [prereg.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/prereg.md) sonuçlardan önce yazıldı.
Sonuçları görmeden iki ek yapıldı: EK-1 hafta içi kapsamı ve sıralama tanımı, EK-2 hücre sayımı düzeltmesi (224 değil **208**).
Tablolarda ondalık ayırıcı nokta, metinde virgül.

**Kısa hüküm:** 9 hipotez ailesi ve 208 hücre sınandı. **LIVE ya da SHADOW adayı yok.**
- KEŞİF'te Holm'u geçen hücre yok: 0/208 (m = 224 ile de 0).
- KEŞİF'te seçilen 9 hücrenin 9'u RED aldı, kartta en iyisi 2/6.
- Tüm dönem net ortR'si pozitif olan yalnız 3/208 hücre var, en iyisi +0,062R.
- ABD seansındaki "iki yön de +" gözlemi gerçek bir saat-ölçeği devam etkisiydi. 2021–23'te güçlüydü (VR 1,25), 2025–26'da ≈0'a indi (VR 1,006). Scalp ölçeğine de hiç taşınmıyor.

---

## 1. Protokol ve motor: sonuçlara güvenilebilir mi?

### Takeaway
Ortak protokol birebir uygulandı:
- giriş sonraki 1m açılışında;
- SL = max(19 bp, 1,1×ATR5m), TP/SL ∈ {1, 2}, zaman stopu 30/60 dk;
- aynı barda TP ve SL → SL;
- SL'de 1 bp kayma, |getiri|'si yılın en üst %1'indeki dakikalarda 5 bp;
- NY 16:58'de zorunlu kapanış;
- Pepperstone 1,85 bp maliyeti, aynı yıl × UTC saati × aynı yön için 200 tekrarlı rastgele giriş plasebosu.

Motor kaba döngüyle 24.000 karşılaştırmada birebir tuttu. 28 tetik varyantının 28'i önek (sızıntı) testini geçti. Perp yolu verdiktleri değiştirmiyor; sıfıra yakın hücrelerde işaret dönebiliyor.

### Cited Findings
- Kaba döngü eşlemesi: 3.000 rastgele giriş × 2 yön × 4 geometri, **0/24.000 uyuşmazlık**. ATR5/SL önek testi OK. 2.801.454 geçerli giriş dakikası (toplam 2.833.920). — [logs/00_selftest.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/logs/00_selftest.log), [common.py](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/common.py)
- Sızıntı (önek) testi: 2023-06-15 13:37 sonrası fiyat ve hacim bozuldu. Bozulmanın öncesindeki tetikler 28 varyantın hepsinde birebir aynı kaldı (VS1 2.584 … MA 17 tetik). — [logs/01_prefix.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/logs/01_prefix.log)
- Rastgele girişin (P1) net beklentisi medyan **−0,094R (KEŞİF) / −0,098R (POST)**. Maliyet/R medyanı 0,072 / 0,084. Yani taban ≈ −(spread + kayma)/R; strateji "0'a" göre değil, bu tabana göre okunmalı. — [results/cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/cells.csv)
- Perp yolu kontrolü (aynı spot sinyalleri, perp OHLC'de çözüm, 15 hücre × KEŞİF/POST/KÖR):
  - Büyük etkiler perp'te aynı çıkıyor: ORB-US15 S G4 KEŞİF +0,140 spot / +0,151 perp, POST −0,158 / −0,178; LS-D L G3 KÖR +0,168 / +0,164.
  - Sıfıra yakın hücrelerde işaret dönebiliyor: LS-D L POST +0,012 / −0,003; ORF-ASIA30 S POST +0,014 / −0,007.
  - Küçük n'li hücrelerde fark 0,1R'ye çıkıyor: MA-CPINFP-C KEŞİF −0,007 / −0,105; VWREV-U3 L KEŞİF −0,249 / −0,341.
  - Hiçbir hücrenin verdikti değişmiyor. — [results/crosscheck.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/crosscheck.csv)
- Aynı-bar oranı seçilen hücrelerde %0,00–0,06. Tek istisna VWREV-D3 L G2 (%0,81, eşik %0,5'i aşıyor, geçersiz damgası). — [results/selection_card.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/selection_card.csv)

### Inferences
- SL tabanı 19 bp ve 2023+ rejiminde ATR5m'nin ~1,1–1,6 katı olduğundan aynı-bar belirsizliği ihmal edilebilir düzeyde. 1m çözünürlük bu geometri için yeterli (not 03 §5-D ile tutarlı).
- 1m'de BTC spot kapanışı ≈ sonraki açılış. Bu yüzden ölçüt 5'teki "icra farkı" fiilen maliyet/R'ye (0,06–0,10R) eşit. Ölçüt 5 burada "net ≥ 2 × maliyet" anlamına geliyor (E44).

### Gaps
- Broker M1 teyidi yapılmadı. Broker verisi yalnız 16 gün (2026-10-05→21) ve bu pencereye düşen işlem sayısı birkaç düzine. E47'ye göre 15 bp altı stoplarda Binance yolu iyimser; burada SL ≥19 bp olduğundan fark ≤0,015R bekleniyor (not 03 §3), ama ölçülmedi.
- Pepperstone'da 2021–25 arası tarihsel spread bilinmiyor. FIX15 varyantı raporlandı, işaretler değişmiyor.

---

## 2. Volatilite sıkışması → genişleme kırılımı (VS1 5m, VS2 1m) kâr veriyor mu?

### Takeaway
Hayır. Sıkışma koşullu kırılımların 16 hücresinin hepsi her bölmede net negatif (POST −0,08…−0,13R). Sıkışma koşulu, aynı kırılımın sıkışmasız sürümüne en fazla +0,04R ekliyor ve bu katkının işareti bölmeler arasında değişiyor. Sıkışmasız kırılım (kontrol) KEŞİF'te rastgele girişin bile **altında**.

### Cited Findings
- VS1 (5m BBW yüzdeliği ≤%10, önceki 12 adet 5m barın ucunu kapanışla kırma):
  - L G1: KEŞİF −0,151 (P1 %1), OOS −0,086, KÖR −0,089; POST n 1.703, WR %44,3, −0,087R, −1,67 bp, P(EV>0) 0,00, yıl 0/6 pozitif.
  - S G1: POST −0,094R [−0,131, −0,057], 1,67 işlem/gün.
  — [results/summary.md §1–2](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/summary.md)
- VS2 (1m BBW60 yüzdeliği ≤%5, 60 dk ucunu kapanışla kırma):
  - L G3: POST −0,084R.
  - S G1: −0,105R [−0,141, −0,070], 1,96 işlem/gün, yıl 1/6 pozitif.
  — aynı
- Sıkışmanın katkısı (sıkışmalı − sıkışmasız, G1–G4 ortalaması):
  - VS1 L: KEŞİF −0,018 / OOS +0,022 / KÖR +0,057
  - VS1 S: +0,000 / +0,022 / −0,009
  - VS2 L: −0,039 / −0,002 / +0,005
  - VS2 S: +0,000 / +0,039 / +0,011
  — [summary.md §4](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/summary.md)
- Plasebo simetrisi: KEŞİF'te VS1-C hücrelerinin 8/8'i P1 yüzdeliği ≤%5'te (rastgeleden kötü). VS1 6/8, VS2 5/8 rastgeleden kötü. Rastgeleden iyi (≥%95) hücre 0. — [summary.md §3](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/summary.md)
- Teşhis (KEŞİF, G1): VS1-C L brüt −0,059R vs plasebo −0,022R. Kaymasız da −0,044 vs −0,005. Stratejinin SL çıkışlarının yalnız %3,9'u 5 bp kaymalı dakikada (plasebo %6,6). Yani açık kayma kaynaklı değil, **giriş zamanlamasından** geliyor. — [results/below_placebo_diag.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/below_placebo_diag.csv)

### Inferences
- BTC 1m/5m'de kısa ölçekli kırılım sonrası hafif bir geri dönüş var (not 03'teki 1m VR < 1 ile tutarlı). Bu yüzden kırılımı kovalamak rastgele girişten ~0,04R kötü. Bu, 5m Donchian48'in (BTC-T08, −0,20R) daha küçük ölçekli bir tekrarı.
- Sıkışma filtresi (defter B14/IO-22 SQZ'nin NDX'teki C hükmüyle aynı yönde) BTC'de de kenar üretmiyor. Not 01 H11'in akış teyitli hâli bu ailenin kapsamı dışında kaldı (orderflow ailesi).

### Gaps
- BBW yüzdelik eşiği ve kırılım penceresi tek değerde dondurulmuştu (q 10/5, 12×5m / 60×1m). Plato taraması yapılmadı. Tabanın altında kalan bir sonucu eşik taramasıyla kurtarmak E24 riski taşırdı.

---

## 3. ABD seansı "straddle" gözlemi (BTC-T07 yan bulgusu) gerçek mi, E43 artefaktı mı?

### Takeaway
**Gerçekti ama sönümlendi.** NY 10:00→16:00 aralığında, SL 1×ATR14(1h) ve zaman çıkışıyla long ve short'un ortalaması (L+S)/2 şöyle:

| dönem | (L+S)/2 | P | VR (10→16) |
|---|---|---|---|
| KEŞİF | +0,158R | %100 | 1,25 [1,10; 1,39] |
| OOS | +0,072R | %91 | — |
| KÖR | +0,015R | %60 | 1,006 |

Motor artefaktı değil:
- Sentetik martingalde (aynı ay × NY dakikası içinde OHLC dörtlüsü karıştırma) değer −0,02…−0,03.
- 24 saat çapası arasında 10:00 KEŞİF, OOS ve POST'ta 1., KÖR'de 3. sırada.

Ön-kayıtlı karar kuralı ("üç bölmede de sentetiğin 20 tekrarının hepsinin üstünde") OOS ve KÖR'de sağlanmadı. Hüküm: **bugün için sağlam bir yönsüz etki yok.** Scalp geometrisine (ST-S) taşındığında (L+S)/2 rastgele tabanla aynı (−0,09…−0,11R).

### Cited Findings
- ST-H gerçek (PEP, 1–5 bp SL kayması dahil) — [results/st_h_real.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/st_h_real.csv), [summary.md §6](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/summary.md):

  | bölme | n | L | S | (L+S)/2 [%95 GA] | stop sonrası kalan L/S (R) | SL medyanı |
  |---|---|---|---|---|---|---|
  | KEŞİF | 674 | +0,109 | +0,207 | +0,158 [+0,068, +0,254] | −0,30 / −0,42 | 77 bp |
  | OOS | 383 | +0,093 | +0,052 | +0,072 [−0,029, +0,180] | −0,32 / −0,06 | 67 bp |
  | KÖR | 341 | +0,001 | +0,028 | +0,015 [−0,090, +0,129] | −0,13 / −0,09 | 57 bp |
  | POST | 724 | +0,050 | +0,041 | +0,045 [−0,030, +0,120], P 0,87 | −0,23 / −0,08 | 62 bp |

- Orijinal gözlem POST penceresinden geliyordu (+0,087 / +0,067). Bizim POST değerimiz (+0,050 / +0,041) daha düşük. Farkın büyük kısmı burada eklenen 1–5 bp SL kaymasından geliyor (62 bp stopta ≈0,02–0,05R). — [05_aile_trend_kirilim.md](file:///Users/melihcanodacioglu/Desktop/panel/research_notes/BTC%20trader%20bot%20kenar%20ara%C5%9Ft%C4%B1rmas%C4%B1/05_aile_trend_kirilim.md)
- Saat plasebosu, (L+S)/2 6 saatlik tutuş:
  - POST'ta yalnız 09:00 (+0,014), 10:00 (+0,045) ve 03:00 (+0,006) pozitif; diğer 21 saat −0,002…−0,069.
  - KEŞİF'te 10:00 +0,158, 11:00 +0,067; diğer saatler ≤ +0,018.
  — [results/st_h_hours.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/st_h_hours.csv)
- Sentetik martingal (20 tekrar, 10:00 çapası): ortalama/min/maks
  - KEŞİF −0,021 [−0,055, +0,026]
  - OOS −0,033 [−0,095, +0,081]
  - KÖR −0,032 [−0,105, +0,097]
  
  Gerçek değer KEŞİF'te tüm tekrarların üstünde. OOS'ta (+0,072) ve KÖR'de (+0,015) sentetik maksimumun altında. — [results/st_h_synth.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/st_h_synth.csv)
- Varyans oranı VR = Var(6 s)/Σ Var(saatlik), NY 10→16:
  - KEŞİF 1,253 [1,10; 1,39]
  - OOS 1,074 [0,92; 1,24]
  - KÖR 1,006 [0,82; 1,20]
  - Diğer çapalar POST'ta çoğunlukla < 1 (ör. 14:00 0,81, 15:00 0,80).
  — [results/st_h_vr.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/st_h_vr.json)
- ST-S scalp straddle (NY 09:30/10:00 çapası, SL ≥19 bp, 30/60 dk): (L+S)/2 POST −0,040…−0,115. Aynı saat P1 tabanı −0,075…−0,106. Fark ≈0. KEŞİF'te 8 hücrenin hepsi −0,084…−0,107. — [summary.md §5](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/summary.md)

### Inferences
- Stoplu ve zamanlı bacaklarda L+S > 0 olması, martingalde (stop seviyeden doluyorsa) imkânsızdır. Kaynak, ≥1 ATR(1h) hareketlerden sonra **saat ölçeğinde devam** (VR > 1). Yani E43'ün "yönsüz kenar" uyarısı burada motor hatası değil, gerçek ama dönemsel bir yol dinamiğiydi.
- Etki 2021–23'te güçlü, 2025–26'da yok. Etkinin 10:00 ET'de (ABD hisse açılışı +30 dk) toplanması, 2021–23'te BTC'nin ABD açılışına oynaklık ithal etmesiyle tutarlı. Bunu ETF sonrası ölçülen başka bir değişiklikle (BTC-M05 H12) bağlayan doğrudan bir kanıt yok. Kesin mekanizma bilinmiyor.
- Devam, scalp ölçeğinde (19–30 bp, 30–60 dk) görünmüyor. Etki yalnız 60–80 bp'lik 1 ATR(1h) hareketlerinden sonra, saatler içinde ortaya çıkıyordu. Bu yüzden scalp straddle'ı bu gözlemden türetilemez.
- KEŞİF dönemi, orijinal gözlemin (POST) dışında ve ondan önce olduğu için **bağımsız bir doğrulama** sayılır. Ama doğruladığı şey geçmişte var olan bir etki; güncel dönem (KÖR) taşımıyor (yeni tuzak önerisi E52).

### Gaps
- NYSE tatilleri ayıklanmadı (hafta içi = Pzt–Cum). Etkisi birkaç gün.
- Etkinin çöküş tarihi (ör. ETF'in 2024-01'de başlaması) yıl/çeyrek ayrıntısında ayrıştırılmadı. Yalnız bölme düzeyinde ölçüldü.

---

## 4. VWAP sapması: kσ'da dönüş mü, geri almada devam mı?

### Takeaway
İkisi de kâr vermiyor. Günlük (00:00 UTC) ve ABD seansı (09:30 ET) çapalı VWAP'ta 64 hücrenin POST'ta pozitif çıkanları yalnız n=42–57'lik 3σ hücreleri; bunlar da KEŞİF'te güçlü negatif. **Yukarı sapmayı satmak** (VW-REV S) rastgeleden belirgin kötü (KEŞİF'te 32 hücrenin 15'i plasebo ≤%5) — "coşku dönmez" BTC'de dakika ölçeğinde de geçerli. Aşağı sapmayı almak plasebo düzeyinde.

### Cited Findings
- VW-REV günlük çapa:
  - D2 S G3: KEŞİF −0,141 (P1 %0), POST −0,110R.
  - D2 L G1: POST −0,090R, 3,26 işlem/gün, yıl 0/6 pozitif.
  - D3 L G2: POST −0,044 [−0,143, +0,051], plasebo %95,5, aynı-bar %0,81 (geçersiz).
  - D3 S G4: POST −0,224.
  — [summary.md §2](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/summary.md)
- VW-REV ABD çapası:
  - U3 L G1: KEŞİF −0,249 (P1 %4) → OOS +0,238, KÖR +0,109, POST n 42, +0,180R, P 0,90. Brüt kenar +0,275, ama n küçük ve KEŞİF tersi.
  - U2 L/S: POST −0,122 / −0,191.
  — aynı
- VW-REC geri alma devamı:
  - D2.5 S G4 KEŞİF'te seçildi: +0,008 → OOS −0,104 / KÖR +0,068; POST −0,018 [−0,120, +0,083], kart 1/6.
  - D1.5 L/S POST −0,083 / −0,060.
  - U1.5 L −0,146, U2.5 L −0,240.
  — [selection_card.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/selection_card.csv)
- Teşhis (KEŞİF, G1):
  - VWREV-D2 S: brüt −0,072 vs plasebo −0,010 (kaymasız −0,041 vs +0,006); SL oranı 0,43 vs 0,32. SL'lerin %21,8'i 5 bp kaymalı dakikada (plasebo %7,6).
  - VWREV-D2 L: kaymasız −0,010 vs −0,012 (plasebo düzeyi).
  — [below_placebo_diag.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/below_placebo_diag.csv)

### Inferences
- Yukarı σ-bandını satmanın kaybı iki kaynaktan geliyor: daha sık stop (gerçek devam) ve hızlı dakikalarda kayma. İkincisi canlıda da aynen yaşanır. Yukarı yönlü fade, BTC-S06'nın (60 dk +3,5σ sonrası SELL −0,19R) dakika ölçeğindeki karşılığı.
- Aşağı yönde fade'in plasebo düzeyinde kalması, "korku döner" ilkesinin BTC dakika ölçeğine taşınmadığını gösteriyor (BTC-S05 ile tutarlı).

### Gaps
- Not 01 H10'daki "sakin rejim" (RV alt tercil ve ΔOI) koşulu bu ailede yoktu (türev/akış ailelerinin kapsamı). Uygulanmadı.

---

## 5. Seans açılış aralığı: kırılım (ORB) ve başarısız kırılım dönüşü (ORF)

### Takeaway
Kenar yok. KEŞİF'te en iyi hücre ABD 15 dk ORB **short** idi: +0,140R, P1 %99,5, Holm öncesi en küçük p 0,032. POST'ta −0,158R oldu (KÖR −0,245; 2024, 2025 ve 2026'nın üçünde de negatif). Bu klasik bir seçim/rejim dönüşü (E12/E49). ORF (sweep dönüşü) her seansta negatif ya da plasebo düzeyinde.

### Cited Findings
- **ORB-US15 S G4** (seçilen):
  - KEŞİF n 352, +0,140, z 1,85, p_sel **0,42**;
  - OOS −0,082, KÖR −0,245;
  - POST n 359, WR %32,3, −0,158R [−0,306, −0,012], −5,33 bp, P(EV>0) 0,015, P1 yüzdeliği %14,5, kart 2/6, **RED**.
  
  Yıl bazında tüm dönem: 2021 +0,196, 2022 +0,095, 2023 +0,149, 2024 −0,084, 2025 −0,097, 2026 −0,327. — [cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/cells.csv), [disc_maxz.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/disc_maxz.csv)
- **ORF-US30 S G2** (seçilen): KEŞİF +0,005 → POST −0,152 [−0,262, −0,033], P 0,004, RED. ORF-US15 L POST −0,178; ORF-LON30 S −0,202. — [selection_card.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/selection_card.csv)
- Asya/Londra:
  - ORB-ASIA30 L G3: KEŞİF +0,012 → POST −0,136.
  - ORB-LON30 L/S POST −0,073 / −0,058.
  - ORF-ASIA30 S G3 POST +0,014 (P 0,60).
  — [summary.md §2](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/summary.md)
- Tüm dönemin en iyi hücresi ORB-US30 S G4: n 679, +0,062R, +0,28 bp, P 0,88, P1 %99,5. Yıllar: 2021 −, 2022 −, 2023 +0,23, 2024 +0,07, 2025 +0,12, 2026 −0,06. KEŞİF'te seçilmedi (aile seçimi US15'i verdi). Net bp ≈0 olduğundan R pozitifliği E50 türü. — [cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/cells.csv)
- Plasebo simetrisi: ORB'de POST'ta ≥%95 olan 9, ≤%5 olan 1 hücre var. Ama 4 geometri aynı işlemleri paylaşıyor: 9 hücre 8 varyant×yönün 5'inden geliyor (US30 S 3, US30 L 2, LON30 L 2, LON30 S 1, US15 L 1). Bunların hiçbiri KEŞİF'te seçilmedi; US30 L ve US15 L KÖR'de negatif. — [summary.md §3](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/summary.md)

### Inferences
- ORB'nin ABD açılışındaki rastgele-üstü performansı, §3'teki ABD saati devam etkisinin scalp ölçekte kalan zayıf izi olabilir. Ama mutlak net ≈0 ve yön KEŞİF/POST arasında dönüyor. Strateji olarak işe yaramıyor.
- NDX'teki sonuçlarla (OLD-15, FG: ORB −0,89R, başarısız kırılım BUY −2,63R) aynı yönde. Açılış aralığı ailesi iki piyasada da kenarsız.

### Gaps
- OR uzunluğu ve izleme penceresi (120 dk) tek değerde. ORB'nin kırılım ötesi aşım filtresi (BTC-T08'deki ≤0,5 ATR) eklenmedi.

---

## 6. Önceki saat/gün ucunda likidite süpürme + hızlı geri alma (fakeout fade'in scalp sınaması)

### Takeaway
Strateji olarak kenar yok.
- **Saatlik süpürme (LS-H):** rastgele girişe göre küçük ama tutarlı bir brüt üstünlük taşıyor (KEŞİF ~+0,02–0,03R). Bu, maliyetin (0,08R) üçte biri; net −0,08…−0,11R, günde ~6,8 işlem.
- **Günlük süpürme (LS-D) long:** POST +0,012R (P 0,55). Bölmeler arasında −0,133 ↔ +0,168 salınıyor; gürültü.

### Cited Findings
- LS-H:
  - S G3: KEŞİF −0,059 (P1 %98), z_sel 2,35 ama p_sel 0,655.
  - L G1: POST n 6.876, −0,112R, P 0,00, yıl 0/6 pozitif.
  - Teşhis L G1 KEŞİF: brüt −0,003 vs plasebo −0,025, kaymasız +0,018 vs −0,008 (fark ≈ +0,026R).
  — [disc_maxz.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/disc_maxz.csv), [below_placebo_diag.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/below_placebo_diag.csv)
- **LS-D L G3** (seçilen):
  - KEŞİF n 190, +0,018 (P1 %94,5) → OOS −0,133, KÖR +0,168;
  - POST n 222, +0,012R [−0,150, +0,170], −0,13 bp, yarılar −0,152 / +0,177, stres −0,027;
  - P1 %99, brüt kenar +0,117 (< 0,15 ve < 2×maliyet 0,158), kart 2/6, RED.
  - Yıllar: 2021 −0,16, 2022 +0,12, 2023 +0,07, 2024 −0,23, 2025 +0,08, 2026 +0,21. 0,22 işlem/gün.
  — [selection_card.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/selection_card.csv), [cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/cells.csv)
- LS-D S G4: KÖR −0,361 (P1 %2). Yukarı süpürmeyi satmak yine kaybettiriyor ("coşku dönmez"). — aynı

### Inferences
- Fakeout radarının NDX'te filtre olarak taşıdığı bilgi, BTC'de saatlik süpürmede rastgeleden ~0,02–0,03R iyi bir giriş zamanlamasına karşılık geliyor. Bu, Pepperstone 1,85 bp maliyetinin (≈0,08R) çok altında. Ancak maliyeti ~0'a indiren bir ortamda (maker rebate) anlamlı olabilir; o da mevcut venue tablosunda yok (Binance maker 4 bp daha kötü).
- Süpürme etkisinin bir filtre olarak (başka bir girişin zamanlamasını iyileştirmek için) değeri bu çalışmada ölçülmedi.

### Gaps
- Not 01 H8'deki akış teyidi (kırılım barında z_F ≥ 2) bu ailede yoktu (orderflow ailesi).

---

## 7. Makro olay dakikası (CPI/NFP/FOMC) devam mı, dönüş mü?

### Takeaway
Takvim repoda mevcuttu ([calendar.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/makro/out/calendar.csv), yalnız okundu). n çok küçük (CPI+NFP 127, FOMC 41 olay; bölme başına 20–64). Hiçbir hücre tutarlı değil. Olay dakikasının yönünde devam (CPI/NFP) POST'ta −0,354R.

### Cited Findings
- MA-CPINFP-C G3 (seçilen): KEŞİF −0,007 → OOS −0,253, KÖR −0,475; POST n 64, −0,354R [−0,671, −0,016], −6,20 bp, P1 %4,5, RED. — [selection_card.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/selection_card.csv)
- MA-CPINFP-F G3: POST −0,070. MA-FOMC-C G3: KÖR −0,834 (n 20). MA-FOMC-F G4: KEŞİF −0,117, OOS −0,402, KÖR +0,771 (n 20). Aynı-bar oranı %5 (n 20'de 1 olay). — [summary.md §2](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/summary.md)
- Takvimde FOMC 2026-07 ve 2026-09 kararları yok (kapsam boşluğu, kaydedildi). — [prereg.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/prereg.md)

### Inferences
- Olay barının yönünde 1. dakikadan girmek, CPI/NFP'de 2024+ döneminde sistematik olarak kaybettiriyor (ilk tepki sonrası kısmi geri dönüş). Fade de pozitif değil. Yönden bağımsız olarak geniş SL ve olay oynaklığı, kaymayı büyütüyor.
- Yılda ~30 olay → kart hacmi (≥150) ~5 yılda bile yapısal olarak geçilemiyor. Makro dakika ancak bir veto ("olay dakikasında BTC scalp açma") olarak düşünülebilir.

### Gaps
- Açıklama sürprizi (beklenti − gerçekleşen) verisi yok. Yön, yalnız fiyat tepkisinden okunabildi.

---

## 8. Çoklu test ve genel hüküm

### Takeaway
208 hücrede seçim düzeltmesiyle hiçbir şey anlamlı değil:
- Holm 0/208;
- max-z boş dağılımının %95'i z = 3,30, en iyi hücrenin z'si 2,59 (p_sel 0,42);
- POST'ta P1 yüzdeliği ≥%95 olan hücre 27, ≤%5 olan 39 (E26 simetrisi aleyhte);
- tüm dönem net ortR > 0 olan yalnız 3/208 hücre.

### Cited Findings
- Holm: en küçük tek yönlü p 0,032 (ORB-US15 S G4), eşik 0,05/208 = 0,00024 → 0 geçen. — [multiple_testing.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/multiple_testing.json)
- max-z (seçime aday 184 hücre: kontrol değil, n_KEŞİF ≥ 50): boş dağılımda maksimum z'nin p50/p90/p95 değerleri 2,52 / 3,11 / 3,30. ORB-US15 S G4 z 2,59 → p_sel 0,42. Diğer aile seçimlerinin p_sel değeri 1,00. — [disc_maxz.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/disc_maxz.csv)
- Plasebo simetrisi (≥%95 / ≤%5 hücre): KEŞİF 12/46, OOS 13/24, KÖR 23/28, POST 27/39. — [summary.md §3](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/summary.md)
- POST'ta brüt kenarı ≥0,15R olan 7 hücrenin hepsi n ≤ 42 olan küçük hücreler (VWREV-U3 L ×3, MA-FOMC-F ×4) ve KEŞİF'te negatif. — [cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/cells.csv)
- KEŞİF seçimlerinin kart özeti (POST): kart 1–2/6, verdikt 9/9 RED. — [selection_card.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_volyapi/results/selection_card.csv)

### Inferences
- Bu ailede BTC scalp'ı için Pepperstone maliyetiyle (ve haydi haydi Binance maker/taker ile) kâr eden bir kural yok. Binance taker'da POST'ta 208 hücrenin hepsi negatif (−0,126…−0,894R); maker'da en iyisi +0,103 (VWREV-U3 L G2, n 42, KEŞİF'te −0,25).
- Ölçülen brüt zamanlama etkileri ±0,02–0,04R düzeyinde: saatlik süpürme +, kırılım kovalama −, yukarı fade −. Maliyet/R (0,07–0,10) bunların 2–4 katı. Not 03'ün "brüt ≥0,15R gerekli" çıtasının çok altında.
- Kaldıraç bu tabloyu değiştirmez: negatif net beklenti, kaldıraçla yalnız ölçeklenir (not 03 §4).

### Gaps
- Akış/türev teyitli varyantlar (H8, H10, H11) ve ML kombinasyonları diğer ailelerin işi; bu notta yok.

---

## En iyi aday(lar)

**LIVE veya SHADOW adayı yok.** Ön-kayıtlı kurallara göre 9/9 seçim RED. Yalnız bilgi amaçlı, en az kötü üç gözlem (hepsi seçim yüklü ya da gürültü düzeyinde):

1. **ST-H yönsüz ABD seansı devam etkisi (scalp değil).** NY 10:00→16:00, SL 1×ATR(1h). (L+S)/2: KEŞİF +0,158 (VR 1,25), OOS +0,072, KÖR +0,015. Sönümleniyor; ön-kayıtlı "gerçek etki" kuralı OOS ve KÖR'de geçmedi. Yalnız ileri gölgede, KÖR sonrası veriyle yeniden ölçülmeye değer. Ölçüt: VR(10→16) > 1,1 ve (L+S)/2 > 0.
2. **LS-H saatlik süpürme dönüşü:** rastgeleden ~+0,02–0,03R brüt iyi zamanlama, ama maliyetin altında. Strateji değil; başka bir girişte zamanlama filtresi olarak sınanabilir (ayrı ön-kayıt gerekir).
3. **ORB-US30 S G4:** tüm dönem +0,062R, ama net +0,28 bp ≈0, KEŞİF'te seçilmedi, 2021/22/26 negatif → C bile değil, kayıt amaçlı.

Veto adayı (kanıt sınıfı B−): **BTC'de yukarı σ-sapmasını / yukarı süpürmeyi scalp ölçeğinde satma.** VW-REV S, KEŞİF'te 15/32 hücre plasebo ≤%5; LS-D S KÖR −0,36. Bu, BTC-S06'nın dakika ölçeğindeki tekrarı.

---

## Defter satırı taslağı

(§6 biçimi, önerilen bölüm "§2.12 BTC scalp ailesi volatilite+yapı — `research/btc_scalp_20261021/fam_volyapi/`". Ortak: Binance spot 1m 2021-06→2026-10-20, giriş sonraki 1m açılışı, SL max(19 bp; 1,1×ATR5m), TP/SL 1/2, 30/60 dk, NY 16:58 zorunlu kapanış, PEP 1,85 bp + 1/5 bp SL kayması, P1 = aynı yıl × UTC saati × yön, 200 tekrar.)

| ID | Tarih | Fikir (kural, parametreler) | Sonuç (sayılar + hangi veri/dönem) | Sınıf |
|---|---|---|---|---|
| BTC-SC-VS01 | 2026-10-22 | **Volatilite sıkışması → kırılım:** 5m BBW20 yüzdeliği (7 g) ≤%10 ∧ 5m kapanış > önceki 12×5m ucu (VS1); 1m BBW60 yüzdeliği (24 s) ≤%5 ∧ 60 dk ucunu kırma (VS2); iki yön; sıkışmasız kontrol | 16 hücrenin 16'sı her bölmede negatif. POST: VS1 L −0,087 / S −0,094, VS2 L −0,084 / S −0,105 (n 1.700–2.000, P 0,00, yıl 0–1/6 +). Sıkışmanın katkısı −0,04…+0,06, işaret değişken. Sıkışmasız kırılım KEŞİF'te P1'in altında (8/8 hücre ≤%5; brüt −0,059 vs −0,022, kaymasız da). Kanıt `fam_volyapi/results/summary.md`, `below_placebo_diag.csv` | X |
| BTC-SC-VS02 | 2026-10-22 | **ABD seansı yönsüz devam (BTC-T07 C yan gözleminin ön-kayıtlı sınaması):** NY 10:00 long + short, SL 1×ATR14(1h), 16:00 çıkış; 24 saat çapası plasebosu, sentetik martingal (aynı ay × NY dakikası OHLC karıştırma, 20 tekrar), VR(10→16) | (L+S)/2: KEŞİF +0,158 [+0,07, +0,25] (VR 1,25 [1,10; 1,39], sentetik −0,02, 24 çapada 1.) · OOS +0,072 (P 0,91, VR 1,07) · KÖR +0,015 (P 0,60, VR 1,006, 24 çapada 3.). Motor artefaktı değil (sentetik ≈ −maliyet), gerçek ama sönümlenmiş saat-ölçeği devamı. Ön-kayıtlı kural (sentetik maks. üstü üç bölmede) OOS/KÖR'de ✗. Kanıt `st_h_real.csv`, `st_h_hours.csv`, `st_h_synth.csv`, `st_h_vr.json` | B (2021–23 tarihsel olgu) / X (güncel strateji) |
| BTC-SC-VS03 | 2026-10-22 | **Scalp straddle:** NY 09:30 ve 10:00 çapasında long ve short, scalp geometrisi (G1–G4) | (L+S)/2 POST −0,040…−0,115 vs aynı saat P1 −0,075…−0,106; KEŞİF 8/8 hücre −0,08…−0,11. Seçilen ST-S-1000 S G4 POST −0,094 (P 0,04) RED. Saat-ölçeği devam etkisi 19–30 bp / ≤60 dk'ya taşınmıyor | X |
| BTC-SC-VS04 | 2026-10-22 | **Açılış aralığı kırılımı (ORB):** ASYA 00:00 UTC / LONDRA 08:00 / ABD 09:30 ET (OR 15/30 dk), sonraki 120 dk'da ilk kapanış dışarıda → kırılım yönü | KEŞİF seçimi ORB-US15 S G4 +0,140 (P1 %99,5, p_sel 0,42) → OOS −0,082, KÖR −0,245, POST −0,158 [−0,31, −0,01] P 0,015, RED; 2021–23 +, 2024–26 − (E12/E49). Tüm dönem en iyisi ORB-US30 S G4 +0,062R ama +0,28 bp (E50). ASYA/LONDRA POST −0,06…−0,14 | X |
| BTC-SC-VS05 | 2026-10-22 | **Başarısız açılış kırılımı dönüşü (ORF/sweep):** OR ucu aşılıp ≤3 bar içinde aralığa kapanış, aşım ≤1×ATR5m → ters yön | Seçilen ORF-US30 S G2 KEŞİF +0,005 → POST −0,152 [−0,26, −0,03] P 0,004 RED; ORF-LON30 S −0,202, ORF-US15 L −0,178; yalnız ORF-ASIA30 S +0,014 (P 0,60). NDX OLD-15/FG ile aynı | X |
| BTC-SC-VS06 | 2026-10-22 | **VWAP σ-bandı dönüşü:** 00:00 UTC ve 09:30 ET çapalı VWAP, hacim-ağırlıklı σ; kσ'yı kapanışla geçince fade, k 2/3 | 32 hücrenin POST'ta pozitif olanları yalnız U3 L (n 42, +0,18, KEŞİF −0,25). Yukarı fade (S) KEŞİF'te 15/32 hücre P1 ≤%5; D2 S brüt −0,072 vs P1 −0,010, SL oranı 0,43 vs 0,32, SL'lerin %22'si 5 bp kaymalı dakikada. Aşağı fade plasebo düzeyinde | X (strateji) / B− (veto: BTC yukarı σ sapmasını scalp'ta satma) |
| BTC-SC-VS07 | 2026-10-22 | **VWAP geri alma devamı:** son 120 dk'da ≤ −kσ olduktan sonra VWAP'ı yukarı geri alma → L (ayna S); k 1,5/2,5 | Seçilen D2.5 S G4 KEŞİF +0,008 → POST −0,018 [−0,12, +0,08], kart 1/6 RED; diğerleri POST −0,04…−0,24 | X |
| BTC-SC-VS08 | 2026-10-22 | **Önceki saat/gün ucu likidite süpürmesi + ≤3 bar geri alma** (fakeout fade'in scalp sınaması), aşım ≤1×ATR5m | LS-H: P1'den brüt ~+0,02–0,03R iyi (KEŞİF kaymasız +0,018 vs −0,008) ama net −0,08…−0,11, 6,8 işlem/gün, yıl 0/6 +. LS-D L G3 (seçilen): POST +0,012 [−0,15, +0,17], P 0,55, OOS −0,133 / KÖR +0,168, brüt kenar +0,117 < çıta, RED. LS-D S KÖR −0,36 | X (strateji) / C (LS-H zamanlama filtresi adayı) |
| BTC-SC-VS09 | 2026-10-22 | **Makro olay dakikası** (repo takvimi `xau_best_days_20261015/makro/out/calendar.csv`; CPI+NFP 08:30 ET, FOMC 14:00 ET): olay barı yönünde devam / ters | CPI+NFP devam POST n 64 −0,354 [−0,67, −0,02] (KÖR −0,475); fade −0,070; FOMC n 20/bölme, işaretler dönemler arasında dönüyor (KÖR fade +0,77, devam −0,83). Hacim yapısal olarak geçilemez (~30 olay/yıl). FOMC 2026-07/09 takvimde yok | X |

---

## Yeni yöntem tuzakları

| ID önerisi | Tuzak | Vaka | Önlem |
|---|---|---|---|
| E51 | **Saat×yıl eşlemeli plasebo, oynaklık durumunu eşlemez; "hızlı dakikada %5 kayma" gibi durum-bağımlı maliyetler, oynaklık olayında tetiklenen stratejilere orantısız biner.** Strateji ile plasebo farkı kısmen maliyet modelinin ürünü olur | VWREV-D2 S: SL'lerin %21,8'i 5 bp kaymalı dakikada (P1 %7,6); VWREV-D2 L'nin P1 altı kalması kaymasız hesapta tamamen kayboluyor (−0,010 vs −0,012) | Strateji–plasebo farkını kaymalı ve kaymasız brüt olarak birlikte raporla; durum-bağımlı maliyeti gerçekçi tut ama "zamanlama kenarı" hükmünü kaymasız brüt farka dayandır |
| E52 | **Bir dönemde (POST) bulunan gözlemin, daha ESKİ ve görülmemiş bir dönemde (KEŞİF) "bağımsız doğrulanması", etkinin bugün sürdüğünü göstermez.** Etki en güçlü eski dönemdeyse doğrulama geriye bakar | ST-H: orijinal gözlem POST'tan; KEŞİF'te çok daha güçlü (+0,158, VR 1,25), ama KÖR'de +0,015 (VR 1,006) | Doğrulamayı her zaman EN YENİ dönemde iste; bölme bazında yıllık eğilimi raporla; etkinin büyüklüğü zamanla monoton düşüyorsa "sönümlenen" diye sınıfla |
| E53 | **Sabit saatli kurallarda (ör. her gün 09:30 straddle) P1 plasebosu (aynı saat rastgele dakika) kuralın neredeyse kendisidir, bilgi vermez.** "Plasebo yüzdeliği" anlamsız ya da yanıltıcı olur | ST-S: (L+S)/2 ≈ aynı saat P1; ST-H'de anlamlı kıyas ancak 24 saat çapası + sentetik martingal + varyans oranıyla kuruldu | Saat-sabit kurallar için plasebo = diğer saat çapaları + yol karıştırmalı (E42) sentetik + VR; aynı-saat P1'i yalnız tetikli kurallarda kullan |
| E54 | **Aynı işlemleri paylaşan geometri hücreleri (TP/SL × zaman stopu) plasebo-simetri sayımlarını şişirir**: "≥%95 hücre sayısı" bağımsız sinyal sayısı değildir | ORB POST'ta 9 hücre ≥%95, ama bunlar 8 varyant×yönün 5'inden geliyor; US30 S tek başına 3 hücre | E26 simetri sayımını varyant×yön düzeyinde (geometri başına en iyi değil, hepsi birlikte tek oy) yap |
