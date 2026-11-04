# BTC strateji inşası: Core + kol portföyü, scalp icra zamanlaması, kaldıraç, bot şartnamesi ve ileri gölge planı

Kapsam: 2026-10-22. Önceki iki turun (BTC trader bot kenar araştırması 01–07, BTC scalping strateji araştırması 01–06) adaylarının
**dondurulmuş** tanımlarıyla birleştirilmesi. Yeni indirme yok, kutuya/Supabase'e dokunulmadı, bot değiştirilmedi, commit yok.
Tüm kod/çıktı: [strateji/](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/) —
ön kayıt [prereg.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/prereg.md) (08:00 UTC, sonuçtan ÖNCE; EK-1 sonuç sonrası,
verdikti değiştirmez), motor `lib_st.py`, kollar `sleeves.py`, betikler `00_selftest.py` → `05_extras.py`, günlükler `logs/`, tablolar `results/`.
Python `.venv` (numpy 2.4.6), `-I`. Tablolarda ondalık nokta, metinde virgül. 07 (ML) notu bu yazım sırasında yoktu; ML çıktısı (`fam_ml/results/eval.json`) §5'te okundu — portföye eklenecek ML kolu yok.

**Kısa hüküm (dürüst cevap):** Canlıya (LIVE) alınabilecek bir BTC stratejisi **yok**. Bu turda LIVE verdikti yapısal olarak verilemezdi de:
adayların hepsi POST'a (OOS∪BLIND) bakılarak aday listesine girdi. Ölçülebilen en iyi şey **ön-kayıtlı kollardan bir GÖLGE portföyü (P-PRE:
Core + MAX10 + QB + X04)**: POST'ta 1.571 işlem, **+0,026R/işlem (+6,9 bp)**, P(EV>0) %95,7, kart 5/6 (icra ölçütü QB yüzünden ✗), BLIND +0,014R —
ama **son 12 ayda −0,008R (P %37)** ve en iyi 20 gün çıkınca −0,013R. Post-hoc kolları (CAPREV-RV, OF02) eklemek kartı 6/6'ya çıkarıyor
(+0,038R), fakat bu kollar POST'a bakılarak bulunduğu için bu kanıt değil. "Scalping" bu stratejiye en olası yerden — Core'un girişini
limitle geri-çekilmeden almak — **katkı vermiyor**: dolmayan sinyaller tam olarak en çok kazananlar (ters seçilim). Öneri: P-PRE dondurulmuş
tanımıyla ileri gölge; canlı risk 0; kullanıcı onaylı bir icra probu olursa işlem başı **%0,25** risk.

---

## 1. Motor ve kollar doğru kuruldu mu, önceki sayılar yeniden üretildi mi?

### Takeaway
Evet. Yeni motor (`lib_trend` ilk-dokunuşu + SL kayması + limit giriş + swap) kaba döngüyle **3.000/3.000** birebir, kayma kapalıyken T03'te
`lib_trend.M1.simulate` ile **311/311** birebir. Yedi kolun olay sayıları ve ortalama R'leri önceki notlarla örtüşüyor; tek fark, emir-akışı/baz
kollarında maliyet konvansiyonundan gelen +0,03R (aşağıda).

### Cited Findings
- Öz-sınama: sıcak dakika eşiği (DISC |1m log getiri| %99) **29,30 bp** (OF ailesinin 29,29'u ile aynı); T03 lib_trend ile 0 uyuşmazlık
  (ortR her ikisinde +0,2410, kaymasız); 3.000 rastgele olay (piyasa / limit-skip / limit-market, iki yön, TP'li/TP'siz, base/stress/$15, kaymalı)
  kaba döngü ile 0 uyuşmazlık — [00_selftest.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/logs/00_selftest.log)
- Yeniden üretim (bu motor, SL kayması dahil) — [sleeve_reproduction.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/results/sleeve_reproduction.csv):

| Kol | önceki not | bu çalışma |
|---|---|---|
| S1 CORE (T03) tüm olay | TAM 305 +0,236; POST 224 +0,206; tek-poz POST 96 +0,114 | TAM 305 **+0,232**; POST 224 +0,202; tek-poz POST 96 **+0,110** |
| S2 MAX10 | 353 +0,034 | 353 +0,034 |
| S3 QB (stopsuz, R/ATR1h) | 1.958 +0,029R / +3,68 bp | 1.958 +0,0286 / +3,68 bp |
| S4 X04 | DISC 207 +0,211; POST 267 +0,034 | DISC 207 +0,211; POST 267 +0,035 |
| S5 CAPREV-RV D0 | TÜM 64 +0,225; onay 44 +0,247 | 64 +0,221; POST 44 +0,245 |
| S6 OF02 W15 θ5 | 80 +0,176 | 79 **+0,210** |
| S7 DV04c-U | DISC 352 −0,064; POST 117 +0,243, aynı-bar %0,85 | DISC 352 −0,061; POST 117 **+0,273**, aynı-bar %0,85 |

- QB'nin bot biçimi (sunucu SL'si zorunlu → 2×ATR14(1h) felaket stopu, ön kayıtta tanımlı): POST SL vuruş payı %4,4; stopsuz POST
  +0,042 ATR1h / +4,25 bp → stoplu +0,031 ATR1h / **+3,67 bp** (stop ~0,6 bp yiyor) — [05_extras.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/logs/05_extras.log)

### Inferences
- S6/S7 farkı bir hata değil, konvansiyon farkı: önceki motor bariyerleri mid'den ölçüp 1,85 bp'yi PnL'den düşüyordu; bu motor MT5 gibi
  çalışıyor (ask'tan gir, TP/SL dolum fiyatından ölçülür, bid tetikler → spread yolda ödenir). Rastgele girişte iki konvansiyon aynı
  beklentiyi verir; bariyeri güçlü geçen olaylarda (akış/şok) yol-içi konvansiyon ~+0,03R daha iyi görünür. Bot gerçeği bu motordur ama fark
  bir belirsizlik bandı olarak okunmalı (yeni tuzak önerisi E-ST4).

### Gaps
- Broker BTCUSD M1 (yalnız 16 gün) ile kol bazında teyit yapılamadı: kolların çoğu bu pencerede ≤ birkaç olay üretir (E47).

---

## 2. "Scalping'i giriş zamanlaması olarak" kullanmak Core'a yardım ediyor mu?

### Takeaway
**Hayır.** 8 limit-geri-çekilme hücresinin (k ∈ {0,25; 0,5}×ATR5m, W ∈ {15, 60} dk, dolmazsa skip/market) **hiçbiri** DISC'te piyasa girişini
geçmedi (en iyisi −0,007R/sinyal); ön kayıt gereği Core = **piyasa girişi**. Mekanizma ters seçilim: limit dolmayan sinyaller, dolanlardan çok daha
fazla kazanıyor; dolan işlemdeki fiyat iyileşmesi (5–11 bp) 250 bp'lik stopun yanında 0,005–0,05R.

### Cited Findings
— [core_exec_grid.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/results/core_exec_grid.csv),
[core_exec_choice.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/results/core_exec_choice.json)
(Core olayları: ATR5m medyanı 21,6 bp, SL medyanı 249 bp):

| hücre | DISC dolum | DISC R/sinyal | POST dolum | POST R/sinyal | POST piyasa-R dolan / dolmayan | POST dolan işlemde iyileşme | POST tek-poz R |
|---|---|---|---|---|---|---|---|
| PİYASA (seçilen) | %100 | **+0,315** | %100 | +0,202 | — | — | +0,110 |
| k0,25 W15 skip | %72,8 | +0,196 | %74,1 | +0,175 | +0,221 / +0,147 | +0,014 | +0,183 |
| k0,25 W15 market | %72,8 | +0,305 | %74,1 | +0,181 | aynı | +0,014 | +0,123 |
| k0,25 W60 skip | %85,2 | +0,255 | %86,6 | +0,172 | +0,175 / **+0,375** | +0,023 | +0,122 |
| k0,25 W60 market | %85,2 | +0,300 | %86,6 | +0,177 | aynı | +0,023 | +0,101 |
| k0,5 W15 skip | %61,7 | +0,165 | %54,0 | +0,070 | +0,077 / **+0,349** | +0,053 | +0,093 |
| k0,5 W15 market | %61,7 | +0,308 | %54,0 | +0,185 | aynı | +0,053 | +0,136 |
| k0,5 W60 skip | %77,8 | +0,223 | %75,9 | +0,093 | +0,071 / **+0,615** | +0,051 | +0,090 |
| k0,5 W60 market | %77,8 | +0,266 | %75,9 | +0,177 | aynı | +0,051 | +0,101 |

- DISC'te de aynı yön: dolan sinyallerin piyasa-R'si +0,26…+0,29, dolmayanların +0,41…+0,45.

### Inferences
- Kırılım sinyalinde geri-çekilme gelmemesi, kırılımın güçlü olduğunun işaretidir; limit, tam olarak en iyi işlemleri kaçırır. "Market
  yedekli" hücreler bunu kısmen telafi eder ama yedek giriş daha yüksekten olduğu için kazanç sıfırlanır. Bu, not 03'ün "kenar varsa yön
  tahmininde değil geometride/zamanda; mikro zamanlama ±0,02–0,04R" tespitinin Core üzerindeki doğrudan karşılığı.
- CFD'de limit emir maker rebate getirmiyor (spread yine ödenir); yani BTC CFD'de scalp icrasının tek olası katkısı fiyat iyileşmesiydi ve o
  ters seçilimle siliniyor. Kısa ufuklu kollar (OF02, DV04c) "scalp"in kendisi; onların durumu §3'te.

### Gaps
- Alt-dakika veri olmadan dolum dakikasındaki sıra (önce dip mi, önce SL mi) kötümser varsayıldı; Core'da SL çok uzak olduğu için etkisiz.

---

## 3. Kollar tek tek ve portföy olarak kartı geçiyor mu?

### Takeaway
Tek kol POST kartını geçmiyor. **P-PRE (post-hoc kolsuz)** POST'ta 5/6 (+0,026R, P %95,7; icra ölçütü ✗), BLIND +0,014, son 12 ay −0,008R →
**GÖLGE**. P-ALL−DV ve P-ALL 6/6 ve plasebo %100 veriyor ama kazancın yarısı POST'a bakılarak bulunmuş kollardan → kanıt sayılmaz.
Core, botun gerçekte açacağı **tek-pozisyon** hâlinde zayıf: POST +0,110R, P %79, **BLIND −0,055**, son 12 ay 10 işlem −0,43R.

### Cited Findings
Kol kartları (POST, kol-içi tek pozisyon, motor bu çalışma) — [cards_table.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/results/cards_table.csv),
[cards.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/results/cards.json):

| kol | n | ortR | bp | P(EV>0) | yarılar | stres | icra farkı | en iyi 20 gün hariç | BLIND | plasebo % | kart | yıl 24/25/26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 CORE (tek-poz) | 96 | +0.110 | +25.6 | 0.79 | +0.29 / −0.07 | +0.109 | 0.019 | −0.38 | −0.055 | 73.0 | 3/6 | +0.28 / +0.01 / −0.27 (n 8) |
| S2 MAX10 | 194 | +0.029 | +12.2 | 0.86 | +0.04 / +0.02 | +0.028 | 0.003 | −0.07 | +0.026 | 79.5 | 5/6 | +0.05 / −0.00 / +0.03 |
| S3 QB (2×ATR1h stop) | 1014 | +0.016 | +3.7 | 0.86 | +0.01 / +0.02 | +0.006 | 0.017 ✗ | −0.02 | +0.013 | 98.0 | 4/6 | +0.04 / +0.03 / −0.03 |
| S4 X04 | 267 | +0.035 | +8.9 | 0.79 | +0.05 / +0.02 | +0.028 | 0.009 | −0.08 | +0.026 | 84.0 | 5/6 | +0.01 / +0.08 / +0.01 |
| S5 CAPREV-RV (post-hoc) | 44 | +0.245 | +68.2 | 0.92 | +0.09 / +0.40 | +0.242 | 0.008 | (n küçük) | +0.276 | 96.0 | 5/6 | +0.08 / +0.31 / +0.45 |
| S6 OF02 (post-hoc) | 57 | +0.205 | +11.3 | 0.98 | +0.20 / +0.21 | +0.184 | 0.055 | −0.28 | +0.164 | 100 | 5/6 | +0.21 / +0.29 / +0.15 |
| S7 DV04c (geçersiz) | 117 | +0.273 | +17.9 | 0.99 | +0.39 / +0.16 | +0.270 | 0.025 | −0.16 | +0.373 | 100 | 5/6 | +0.30 / +0.04 / +0.76; DISC 352 −0.061 |

Portföyler (eşit risk/işlem, kol başı tek pozisyon, kollar arası eşzamanlı serbest):

| portföy | dönem | n | ortR | bp | P(EV>0) [GA] | yarılar | stres / $15 | icra farkı | küresel tek-poz | en iyi 20 gün hariç | maxDD (R) | BLIND | plasebo % (ort) | kart |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P-CORE | POST | 96 | +0.110 | +25.6 | 0.79 | +0.29 / −0.07 | +0.109 / +0.123 | 0.019 | +0.110 | −0.38 | 8.7 | −0.055 | 73.0 | 3/6 |
| **P-PRE** | DISC | 1356 | +0.051 | +15.6 | 0.998 | +0.03 / +0.07 | +0.045 / +0.030 | 0.013 | +0.051 | −0.005 | 18.0 | — | 100 | 6/6 |
| **P-PRE** | **POST** | **1571** | **+0.026** | **+6.9** | **0.957 [−0.004, +0.057]** | +0.044 / +0.009 | +0.019 / +0.027 | **0.014 ✗** | +0.033 | **−0.013** | 12.1 | **+0.014** | 100 (−0.008) | **5/6** |
| P-ALL−DV | POST | 1672 | +0.038 | +8.7 | 0.992 [+0.007, +0.070] | +0.055 / +0.022 | +0.030 / +0.038 | 0.015 | +0.045 | −0.001 | 14.3 | +0.027 | 100 (−0.011) | 6/6 |
| P-ALL | POST | 1789 | +0.054 | +9.3 | 0.998 [+0.021, +0.088] | +0.071 / +0.036 | +0.046 / +0.054 | 0.016 | +0.054 | +0.011 | 16.1 | +0.037 | 100 (−0.016) | 6/6 |

- Yıl bazında P-PRE: 2024 +0.053 (n 574), 2025 +0.033 (553), **2026 −0.017 (444)**; P-ALL−DV 2026 +0.004 — aynı dosya.
- Son 12 ay (2025-10-20 →): P-PRE n 541, **−0,008R / −0,33 bp, P(EV>0) %37**; P-ALL−DV n 589 +0,015R, P %72; Core 10 işlem −0,431,
  QB 366 işlem −0,013, MAX10 +0,032, X04 +0,029 — [05_extras.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/logs/05_extras.log)
- POST ΣR katkısı (R): Core 10,5 · MAX10 5,7 · QB 15,7 · X04 9,4 · CAPREV 10,8 · OF02 11,7 · DV04c 32,0. P-ALL'ın 95,8R'sinin 54,4'ü post-hoc/geçersiz
  kollardan — [contrib.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/results/contrib.json)
- Kol korelasyonu (POST günlük ΣR, Pearson): Core–MAX10 **0,28**, MAX10–QB 0,14, diğer tüm çiftler |ρ| ≤ 0,07 —
  [corr_post.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/results/corr_post.csv). Eşzamanlı açık pozisyon en çok 3
  (P-PRE ve P-ALL−DV) — [leverage_meta.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/results/leverage_meta.json)
- Swap −%22,5 varyantı (Pepperstone PDF'i): Core POST +0,110 → +0,090, MAX10 +0,029 → +0,026, CAPREV +0,245 → +0,238; QB/X04/OF02/DV gece taşımıyor —
  [swap_sensitivity.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/results/swap_sensitivity.csv)
- Post-hoc kolların POST kenarı yarıya inerse: P-ALL−DV +0,038 → +0,031; P-ALL +0,054 → +0,038 — [05_extras.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/logs/05_extras.log)

### Inferences
- **Seçim yanlılığı iki katmanlı.** (1) S5/S6/S7 POST'a bakılarak bulundu → onların POST kartı doğrulama değil (E53/T5). (2) P-PRE'nin kolları da
  230+ hücrelik iki turdan "ayakta kalanlar" olarak seçildi; bu seçim kısmen POST sonuçlarına bakılarak yapıldı → P-PRE'nin POST'u da
  tam bağımsız değil. Bu yüzden P-PRE'nin +0,026R'si bir **üst sınır** gibi okunmalı; son 12 aydaki ≈0 sonucu bunu destekliyor.
- **Portföyün plasebo %100'ü büyük-n etkisi** (E51'in portföy yüzü): kol plasebo yüzdelikleri 73 / 79,5 / 98 / 84 iken havuzda n=1.571 olunca
  %100 oluyor. Hacim ölçütünü de esas olarak QB dolduruyor (P-PRE POST işlemlerinin %65'i), ki QB'nin kenarı ≈2 spread ve icra ölçütünü
  tek başına düşürüyor (E44).
- **Core'un "B" sınıfı tek-pozisyonda B−'ye iner.** Örtüşmeli olay setinde BLIND +0,266 iken botun açabileceği tek-pozisyon zincirinde
  −0,055: kâr, aynı kırılım kümesindeki 2./3. sinyallerde. Bu bir "piramitleme" fikrine işaret eder ama yeni bir serbestlik derecesidir
  (bu turda sınanmadı; yalnız ileri ön kayıtla açılabilir).
- Diversifikasyon gerçek (çapraz korelasyonlar ≈0) ama sıfıra yakın beş kenarı toplamak tek bir sağlam kenar üretmiyor; toplamın işareti
  2026'da sıfıra yaklaşıyor.

### Gaps
- 2021-06 öncesi bağımsız BTC 1m geçmişi (Coinbase/Bitstamp 2017–2021) yok; dondurulmuş P-PRE'nin tek seferlik bağımsız sınavı bu veriyle
  yapılabilirdi (indirme izni gerektirir).

---

## 4. Vetolar (B/B−) bu kollarda katkı veriyor mu?

### Takeaway
**Hayır — tutarlı katkı yok.** Vetolar POST'ta portföyü küçük artırıyor (+0,004…+0,006R) ama DISC'te aynı miktarda düşürüyor (−0,007…−0,014R);
sildikleri işlemler dönemler arasında işaret değiştiriyor. Vetolar bu kollara **bağlanmamalı**, gölgede yalnız etiket olarak loglanmalı (E18).

### Cited Findings
— [vetoes.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/results/vetoes.csv), [cards_table.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/results/cards_table.csv)

| veto | kol | DISC silinen n / ortR | POST silinen n / ortR |
|---|---|---|---|
| V1 (60 dk ≥ +3,5σ sonrası SELL yok) | X04 | 10 / **+0,573** | 13 / −0,105 |
| V2 (stres ∧ sakin RV günü dip-altı BUY yok) | QB | 28 / −0,095 | 37 / −0,008 |
| V2 | X04 | 7 / +0,120 | 9 / −0,073 |
| V2 | OF02 | 7 / +0,299 | 8 / −0,163 |
| V2 | DV04c | 28 / +0,335 | 12 / +0,438 |
| V3 (VWAP+2σ / önceki gün tepesi süpürmesi sonrası SELL yok) | X04 | 41 / **+0,306** | 71 / −0,071 |
| V3 | OF02 | 6 / +0,322 | 12 / +0,143 |

- Portföy ortR (vetosuz → vetolu): P-PRE DISC +0,051 → +0,044, POST +0,026 → +0,032 (kart 5/6 → 6/6); P-ALL−DV DISC +0,055 → +0,047,
  POST +0,038 → +0,044; P-ALL DISC +0,032 → +0,018, POST +0,054 → +0,058.

### Inferences
- P-PRE'nin vetolu POST kartının 6/6 olması (icra ölçütünü kıl payı geçiyor) bir iyileşme kanıtı değil: aynı vetolar DISC'te kazananları siliyor.
  Vetoların kaynağı başka popülasyonlar (rastgele SELL'ler, dip alımları); X04'ün SELL'leri ve QB'nin 21:01 alımları farklı popülasyon (E18).
- V2 hiçbir kolda pozitif kanıt vermedi; CAPREV-RV tanımı gereği V2 ile hiç çakışmıyor (yüksek RV ister).

### Gaps
- Vetoların asıl hedefi olan "botun kendi BTC sinyalleri" yok (bot BTC işlemiyor); katkı ancak gölge popülasyonunda ölçülebilir.

---

## 5. ML ailesi (07) portföye eklenebilecek bir kol veriyor mu?

### Takeaway
**Hayır.** ML ailesinin 8 dondurulmuş hücresinin (L/S × TP 1/1,5 × 30/60 dk) hiçbiri OOS ve BLIND'ı birlikte geçmiyor; BLIND'da en iyisi
+0,012R (P %59, kart 3/6). Portföye eklenecek ML kolu yok (eklenseydi de post-hoc olurdu; dondurulmuş portföy değişmez).

### Cited Findings
- `fam_ml/results/eval.json` (07 notu bu yazım sırasında henüz yoktu; sayılar doğrudan çıktıdan) — [eval.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/results/eval.json):

| hücre | OOS n / ortR / P / kart | BLIND n / ortR / P / kart |
|---|---|---|
| L_tp1_h30 | 1691 / −0.005 / 0.44 / 1 | 1505 / −0.013 / 0.35 / 2 |
| L_tp1_h60 | 1757 / +0.049 / 0.87 / 3 | 1436 / +0.003 / 0.52 / 2 |
| L_tp1.5_h30 | 1744 / +0.019 / 0.68 / 2 | 1476 / −0.049 / 0.12 / 1 |
| L_tp1.5_h60 | 1754 / +0.081 / 0.94 / 5 | 1493 / +0.012 / 0.59 / 3 |
| S_tp1_h30 | 1752 / +0.051 / 0.94 / 5 | 1488 / −0.025 / 0.22 / 1 |
| S_tp1_h60 | 1781 / +0.024 / 0.74 / 2 | 1655 / −0.038 / 0.17 / 2 |
| S_tp1.5_h30 | 1664 / +0.077 / 0.98 / 5 | 1482 / −0.056 / 0.09 / 1 |
| S_tp1.5_h60 | 1647 / +0.057 / 0.89 / 4 | 1562 / −0.072 / 0.08 / 1 |

- Örnek L_tp1_h30: AUC (net>0) OOS 0,519 / BLIND 0,525; icra farkı ~0,077R (ortalama |R|'nin çok üstünde); plasebo %100 ama net ≈0 (E51 deseni).

### Inferences
- ML, kural ailelerinin bulduğu tabloyu tekrar ediyor: plasebodan iyi sıralama (AUC ~0,52) ama maliyet sonrası ≈0; OOS'ta görünen +0,05…+0,08R
  BLIND'da sönüyor (2024 rejimi). Gelecekte bir ML kolu ancak yeni ön kayıt + ileri gölge ile düşünülebilir.

### Gaps
- 07 notunun kendi yorumu ve seçim prosedürü ayrıntısı bu notta okunmadı (not henüz yazılmamıştı).

---

## Önerilen strateji (dondurulmuş tanım)

### Takeaway
**"BTC-ST GÖLGE PORTFÖYÜ v1" = P-PRE**, dört kol, eşit risk/işlem, kol başı tek pozisyon, vetosuz. Statü: **GÖLGE (canlı emir yok)**.
Yanında yalnız-log iki C kolu (CAPREV-RV D0, OF02 θ5). DV04c-U bırakıldı (aynı-bar geçersiz, DISC negatif).

### Cited Findings
| Kol | Zaman dilimi / saat (UTC) | Giriş | Stop (sunucu) | Hedef | Çıkış | POST kanıtı |
|---|---|---|---|---|---|---|
| **CORE** (BTC-T03 H4D20-T-L) | UTC-hizalı H4 (00/04/08/12/16/20) | H4 kapanışı ≥ önceki 20 H4 barın en yükseği **∧** son tamamlanmış UTC D1 kapanışı > EMA200(D1) → sonraki dakika açılışında **piyasa BUY** (limit YOK, §2) | 2×ATR14(H4, Wilder) | 4×ATR14 (sunucu TP) | 30 H4 bar (=5 gün) sonra piyasa kapanış; gece swap'ı kabul | n 96, +0,110R, P %79 |
| **MAX10** (BTC-T02) | UTC D1 | D1 kapanışı = son 10 D1 kapanışının en yükseği → 00:00 UTC piyasa BUY | 2×ATR14(D1) felaket | yok | 24 s sonra (ertesi 00:00 UTC) | n 194, +0,029R, P %86 |
| **QB** (BTC-M02) | her gün | NY 17:00 rollover + 1 dk (yaz 21:01 / kış 22:01 UTC) piyasa BUY | 2×ATR14(1h) felaket | yok | 22:59 UTC barının kapanışı (23:00 UTC) | n 1.014, +0,016R (2×ATR) = +3,7 bp, P %86 |
| **X04** (BTC-X04) | QQQ işlem günleri | gz = ln(QQQ açılış / önceki kapanış) / std20(QQQ günlük log getirisi, dün dahil) ; \|gz\| > 0,5 → 10:00 ET'de boşluğun **tersine** piyasa | 1×dvol20 (son 20 tamamlanmış UTC günü log getirisi std'si) × fiyat | yok | 16:58 ET (rollover − 2 dk) | n 267, +0,035R, P %79 |
| CAPREV-RV D0 (C, yalnız log) | UTC gün | stres(k=1) ∧ σ30 > 365 g medyanı; başı ≤19:00 olan ilk 1h kapanışı < önceki gün dibi → BUY | giriş×(1−σ20) | yok | 00:00 UTC | n 44, +0,245R (post-hoc) |
| OF02 θ5 (C, yalnız çevrimdışı log) | 1m | \|z(perp taker delta 15 dk)\| ≥ 5 ∧ \|z(spot 15 dk getiri)\| ≤ 0,5 → akışın tersi | max(19 bp, 1,1×ATR5m) | 1×SL | 15 dk / RO−2 | n 57, +0,205R (post-hoc) |

### Inferences
- Portföy beklentisi, iyimser okumayla **+0,02…+0,03R/işlem, ~565 işlem/yıl** (çoğu QB). Son 12 ay ≈0. Bu, para kazandıran bir strateji
  değil, **sınanmaya değer en iyi dondurulmuş hipotez**.
- "Scalping'den para" sorusunun dürüst cevabı: BTC CFD maliyetinde (1,85 bp) 60 dk altı hiçbir kural ayakta kalmadı; OF02/DV04c gibi
  pozitif görünen kısa ufuklu köşeler POST'a bakılarak bulundu ve canlı veri gerektiriyor (Binance perp akışı/bazı; kutudan REST erişimi
  engelli — not 02). Scalp ölçeği burada yalnız bir **icra** konusu (giriş dakikası, spread, kayma) ve en iyi icra = sonraki dakikada piyasa.

### Gaps
- Gerçek dolum/kayma, gerçek swap tahakkuk anı, komisyon ve rollover-açılışı (21:01) spread'i ölçülmedi — QB'nin tüm kenarı bunlara bağlı.

---

## Kaldıraç ve pozisyon boyutu

### Takeaway
Kaldıraç çıktıdır: **lot = özsermaye × risk% / SL_$** (1 lot = 1 BTC, adım 0,01, min 0,01, maks 22); nominal/özsermaye = risk% / SL%.
Önerilen: **gölgede 0 canlı risk; kullanıcı onaylı icra probunda işlem başı %0,25.** %0,5 perakende 2:1 tavanını eşzamanlı pozisyonlarda aşıyor;
%1, kenar sıfırsa yılda %25 olasılıkla ≥%20 düşüş demek.

### Cited Findings
Lot ve kaldıraç (son fiyat 83.028 $, BLIND medyan stop) — [leverage_table.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/results/leverage_table.csv):

| kol | SL % | SL $/BTC | 2:1'de azami risk% | 1:20'de azami risk% | 10k$ @%0,25 lot (nominal/özs) | 10k$ @%0,5 | 50k$ @%0,25 | 50k$ @%0,5 | işlem/yıl |
|---|---|---|---|---|---|---|---|---|---|
| CORE | 1.82 | 1,510 | 3.64 | 36.4 | 0.01 (0.08×; fiilen %0,15 risk) | 0.03 (0.25×) | 0.08 (0.13×) | 0.16 (0.27×) | 35 |
| MAX10 | 5.58 | 4,635 | 11.2 | 112 | 0.01 (0.08×; min lot → %0,46 risk ⚠) | 0.01 | 0.02 (0.03×) | 0.05 (0.08×) | 70 |
| QB | 1.21 | 1,005 | 2.42 | 24.2 | 0.02 (0.17×) | 0.04 (0.33×) | 0.12 (0.20×) | 0.24 (0.40×) | 365 |
| X04 | 1.90 | 1,579 | 3.80 | 38.0 | 0.01 (0.08×) | 0.03 (0.25×) | 0.07 (0.12×) | 0.15 (0.25×) | 96 |
| CAPREV-RV | 2.37 | 1,969 | 4.74 | 47.4 | 0.01 | 0.02 (0.17×) | 0.06 (0.10×) | 0.12 (0.20×) | 16 |
| OF02 | 0.25 | 204 | **0.49** | 4.9 | 0.12 (1.00×) | 0.24 (**1.99×**) | 0.61 (1.01×) | 1.22 (**2.03×**) | 20 |

- Eşzamanlılık (POST): P-PRE en çok 3 açık pozisyon; %0,5 riskte **azami toplam nominal 2,27× özsermaye** (P-ALL−DV 3,23×), medyan 0,28× →
  %0,25'te 1,14× (2:1 içinde) — [leverage_meta.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/results/leverage_meta.json)
- Monte Carlo (POST işlem dizisi, gün blokları, 365 gün × 10.000 yol, bileşik) — [mc_risk.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/results/mc_risk.csv):

| portföy · senaryo (kenar R) | risk | medyan yıl getirisi | %5 yüzdelik | P(zarar) | medyan maxDD | P(DD≥%20) | P(DD≥%50) |
|---|---|---|---|---|---|---|---|
| P-PRE · ölçülen (+0,026) | %0,25 | +%3,6 | −%2,5 | %16,9 | %2,9 | %0 | %0 |
| P-PRE · ölçülen | %0,5 | +%7,2 | −%5,0 | %17,4 | %5,7 | %0 | %0 |
| P-PRE · ölçülen | %1 | +%14,4 | −%10,1 | %18,5 | %11,1 | %6,2 | %0 |
| P-PRE · yarı kenar (+0,013) | %0,5 | +%3,4 | −%8,4 | %32,6 | %6,6 | %0,1 | %0 |
| P-PRE · yarı kenar | %1 | +%6,4 | −%16,5 | %33,8 | %12,9 | %13,3 | %0 |
| **P-PRE · sıfır kenar** | %0,25 | −%0,1 | −%6,0 | %51,1 | %4,0 | %0 | %0 |
| **P-PRE · sıfır kenar** | %0,5 | −%0,3 | −%11,8 | %51,8 | %7,9 | %0,4 | %0 |
| **P-PRE · sıfır kenar** | %1 | −%1,2 | −%22,6 | %53,1 | %15,3 | **%25,2** | %0 |
| P-CORE · ölçülen (+0,110) | %0,5 | +%1,8 | −%4,5 | %33,3 | %3,2 | %0 | %0 |
| P-ALL−DV · ölçülen (+0,038) | %0,5 | +%11,9 | −%2,1 | %8,8 | %5,4 | %0 | %0 |
| P-ALL−DV · sıfır kenar | %1 | −%1,4 | −%24,3 | %53,5 | %16,6 | %31,6 | %0 |

- Kenarı 2σ ile görmek için gereken işlem: P-PRE (μ +0,026, σ 0,60) **~2.090 işlem ≈ 3,7 yıl**; P-ALL−DV ~1.090 ≈ 1,8 yıl; P-CORE (μ +0,110, σ 1,39) ~640 ≈ 18 yıl —
  [04_leverage_mc.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/logs/04_leverage_mc.log)
- Perakende Pepperstone kripto kaldıracı 2:1, demo 1:20 (not 03 §4); kutudaki demo hesap 1:200 hesap / %5 sembol marjini (not 02).

### Inferences
- **Risk önerisi (ön-kayıtlı kurala göre):** kanıt sınıfı < A → **≤ %0,25**. MC'de "P(DD≥%20) ≤ %10 ∧ P(zarar) ≤ %25" kuralını ölçülen kenarda
  %0,5 sağlıyor ama yarı-kenarda P(zarar) %33 → sağlamıyor; sıfır-kenarda hiçbir risk düzeyi P(zarar) ≤ %25 vermiyor. Yani kanıt-sonrası
  tavan ancak ileri gölge kenarı doğrularsa %0,5 olur; %1 yalnız ≥ +0,10R kanıtlı kenarla (not 03 kural H).
- **Küçük hesapta min-lot tuzağı:** 10.000 $'da %0,25 riskle CORE/X04 lotu 0,01'e yuvarlanınca gerçek risk %0,15; MAX10'da min lot gerçek riski
  %0,46'ya çıkarır. Bot `lot < 0,01` ise işlemi **atlamalı** (yukarı yuvarlamamalı) ya da gerçek riski loglamalı.
- OF02 gibi 19–25 bp stoplu kollar perakende 2:1'de en fazla ~%0,5 riskle açılabilir; eşzamanlı başka pozisyon varsa daha az. Endeks botunun
  5,0 lot ayarı BTC'ye **asla** taşınmamalı (5 BTC ≈ 415 bin $ nominal).

### Gaps
- Gerçek hesap türü (perakende 2:1 mi, Pro mu), BTC komisyonu ve canlı marjin çağrısı davranışı doğrulanmadı. MC eşzamanlı işlemleri sırayla
  bileşikliyor (yaklaşım) ve gün blokları gün-içi bağımlılığı korur ama günler arası rejim kalıcılığını korumaz → düşüşler alt sınırdır.

---

## Bot entegrasyon şartnamesi

### Takeaway
Ayrı bir modül (`caprev_live.py` kalıbında, örn. `btc_portfolio.py`), **önce yalnız GÖLGE** (emir yok, JSONL). Kritik şartlar: `symbol_select("BTCUSD")`,
broker barlarını **UTC'ye hizalayarak yeniden örnekleme** (broker H4/D1 sunucu saatine hizalı), sunucu SL'si, rollover zaman çizelgesi, kol başı
ayrı magic + `_bot_magics()` + günlük fren, spread koruması, ayrıntılı gölge kaydı. Bu turda bot kodu DEĞİŞTİRİLMEDİ; aşağıdakiler okunan koda göre
yazıldı.

### Cited Findings
- Bot yapısı: ana döngü `forexsai_demo_bot.py::main` — CAPREV çıkışları fren `continue`'undan ÖNCE çağrılıyor, gölge modülleri SONRA (satır ~2611–2720);
  `_bot_magics()` (satır 252) günlük fren (`today_realized_pnl`, broker-saati ofsetli, satır 345) ve global tavan sayımında kullanılıyor;
  kullanılan magic'ler MAGIC_NUMBER(52890969)+0/+1/+2/+3/+4/+5/+6/+7, decider ayrıca +20 (`claude_decider/execute_mt5.py`);
  `resolve_symbol` `symbol_select` yapıyor ama BTC için iğne listesi yok; `_mk_comment` ≤28 ASCII karakter; `MAX_TOTAL_POSITIONS = 6`,
  `DAILY_MAX_LOSS = 3000` (repo config'i; kutu config'i farklı olabilir, E11) — [forexsai_demo_bot.py](file:///Users/melihcanodacioglu/Desktop/panel/yeni%20deneme/forexsai_demo_bot.py),
  [caprev_live.py](file:///Users/melihcanodacioglu/Desktop/panel/yeni%20deneme/caprev_live.py), [config.py](file:///Users/melihcanodacioglu/Desktop/panel/yeni%20deneme/config.py)
- `trade_manager.py` yönetimi sembol bazlı (NDX/GDAXI/USOIL…); BTCUSD listede yok → BTC pozisyonlarına BE/zaman stopu uygulanmaz
  (dondurulmuş tanımlarda da yok) — [trade_manager.py](file:///Users/melihcanodacioglu/Desktop/panel/yeni%20deneme/trade_manager.py)
- Broker: BTCUSD gizli (`visible=False`) → `symbol_select` şart; sunucu UTC+3 (2026-11-01'den UTC+2); günlük 2 dk kapanış (yaz 20:59–21:01 UTC),
  Cuma 6 dk; hafta sonu düzensiz bakım boşlukları (129 dk'ya kadar); spread ~15 $ sabit, p99 ~40 $ (not 02 / rapor).

### Inferences
**Şartname (önerilen, uygulanmadı):**
1. **Sembol:** `config.SYMBOL_MAP["BTCUSD"]="BTCUSD"`; `resolve_symbol` iğnesi yalnız tam ad `BTCUSD` (BTCAUD/BTCEUR/BTCGBP değil); her
   başlatmada `mt5.symbol_select("BTCUSD", True)`; `symbol_info` ile `trade_contract_size==1`, `volume_step==0.01`, `volume_min==0.01` doğrula, değilse modülü kapat.
2. **Zaman:** tüm kurallar UTC. Broker M1/H1 `copy_rates_from_pos` → `time − ofset` (ofseti BTCUSD'nin kendi tick'inden ölç; hafta sonu da işlem gördüğü
   için endeks tick'lerinden daha güvenilir) → UTC H4 (00/04/…) ve UTC D1 **yeniden örnekle**; broker'ın H4/D1 barlarını doğrudan KULLANMA
   (sunucu gece yarısı = 21:00/22:00 UTC'ye hizalı → farklı kural, E-ST5). EMA200(D1) için ≥ 600 gün H1 geçmişi (ısınma).
   `copy_rates_from` yerine `_from_pos` (E1). Karar yalnız bar KAPANDIKTAN sonra; giriş en geç 60 sn içinde (araştırma ≤10 dk gecikmeyi kabul etti).
3. **Emirler:** piyasa emri (IOC), `deviation` bot ayarı; **sunucu SL zorunlu** her kolda (CORE 2×ATR(H4), MAX10 2×ATR(D1), QB 2×ATR(1h), X04 1×dvol20);
   CORE için sunucu TP = 4×ATR(H4) (koştur yok, dondurulmuş tanım). TP'siz kollarda zaman çıkışı bot tarafından; çıkış zamanı state dosyasına
   yazılır, yeniden başlatmada vadesi geçmiş pozisyon hemen kapatılır (caprev_live `MAX_HOLD_S` kalıbı).
4. **Rollover/çıkış takvimi (UTC):** gün-içi kollar (X04, OF02, DV) NY 16:58'de kapanır = **yaz 20:58 / kış 21:58** (2026-11-01 sonrası 21:58);
   [RO−2, RO+3) içinde yeni giriş yok; QB girişi RO+1 (21:01 / 22:01), çıkış 23:00; CORE/MAX10/CAPREV gece taşır (swap kabul, kanıtta dahil).
   DST'yi `zoneinfo("America/New_York")` 17:00 ile hesapla, sabit +3 kullanma.
5. **Hafta sonu:** açık (blok için kanıt yok, BTC-X12); her kayda `weekend=True` etiketi; sunucu SL zorunluluğu tam da bakım boşlukları yüzünden.
6. **Magic:** önerilen `MAGIC_NUMBER + 30` CORE, `+31` MAX10, `+32` QB, `+33` X04, `+34` CAPREV-RV (gölge), `+35/+36` OF02/DV rezerve. Hepsi
   `_bot_magics()`'e (günlük fren + global tavan) eklenir — IO-21 / 2026-10-20 dersi: kümede olmayan magic'in zararı freni tetiklemiyordu.
   `trade_manager` kapsamına EKLENMEZ. Kol başı tek pozisyon = magic başına `positions_get` sayısı ≤ 1. Yorum: `_mk_comment("fxs BTC ", "CORE")` (≤28).
7. **Günlük fren ve gölge:** BTC canlı çıkış yönetimi frenin `continue`'undan ÖNCE çağrılmalı (CAPREV gibi); **gölge kaydı da frenden ÖNCE**
   çağrılmalı — aksi hâlde fren günlerinde gölge örneklemi delikli olur (E-ST6).
8. **Lot:** `lot = floor(equity × risk / (SL_fiyat_mesafesi × contract_size) / 0.01) × 0.01`; `< 0.01` ise **atla + logla** (yukarı yuvarlama yok);
   `≤ 22`. Göndermeden önce `mt5.order_calc_margin` ile serbest marjin kontrolü; tüm BTC açık nominali ≤ 2 × özsermaye (perakende tavan; demo'da da
   aynı disiplin). Risk: gölge = 0; prob = %0,25.
9. **Spread koruması (sınanmadı, önerilen):** girişte `ask−bid > 25 $` ise QB/X04/OF02 için gir­me (kenarları ≤ 9 bp); CORE/MAX10/CAPREV için `> 40 $`
   (p99). QB'de RO+1'deki **yeniden açılış** dakikası en riskli an: gölgede hem "RO+1'de ne olursa" (birincil, dondurulmuş) hem "korumalı" fiyatı kaydet.
10. **Veri bağımlılıkları:** X04 için QQQ günlük açılış/kapanış (kutuda `QQQ.US` var mı doğrulanmalı; yoksa yfinance) 10:00 ET'de; OF02/DV04c Binance perp
    akışı/baz ister ve kutudan Binance REST erişimi engelli (not 02) → bu iki kol **canlıda yürütülemez**, yalnız data.binance.vision günlük arşiviyle
    T+1 çevrimdışı gölge.
11. **Gölge kaydı (`btc_portfolio_shadow.jsonl`, her sinyal):** kol, karar UTC, sinyal barı OHLC (UTC'ye çevrilmiş) + gösterge değerleri (hh20, ATR14,
    EMA200, D1 kapanış; QQQ gz; σ20/σ30/rvhi), broker bid/ask ve spread (karar ve giriş anı), Binance referans fiyatı (varsa), hesaplanan SL/TP/çıkış
    zamanı, varsayımsal lot ve gerçek risk%, varsayımsal dolum (ask/bid), çıkış nedeni/zamanı/fiyatı, MFE/MAE, rollover sayısı ve swap (canlıda
    deal `swap` alanından), V1/V2/V3 bayrakları, `weekend`, kullanılan ofset/DST, bot kesinti aralıkları, aynı-dakika TP+SL belirsizliği bayrağı.

### Gaps
- Kutuda `QQQ.US` sembolü ve BTCUSD H1 geçmiş derinliği doğrulanmadı (kutuya dokunulmadı).

---

## İleri gölge planı ve karar kuralı

### Takeaway
Gölge, kanıtın tek gerçek yeni kaynağı. P-PRE'nin **+0,026R'lik iddiası 2σ ile ~3,7 yılda** görülebilir; 1 yılda karar büyük olasılıkla "belirsiz"
çıkar. Daha hızlı meşru yol: dondurulmuş P-PRE'nin 2017–2021 bağımsız BTC 1m geçmişinde **tek seferlik** sınavı (indirme kullanıcı onayı ister).

### Cited Findings
Beklenen n=150 süresi (POST işlem hızıyla) — [leverage_table.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/strateji/results/leverage_table.csv):
QB ~0,4 yıl (365/yıl) · X04 ~1,6 yıl (96/yıl) · MAX10 ~2,1 yıl (70/yıl) · CORE ~4,3 yıl (35/yıl) · CAPREV-RV ~9,5 yıl (16/yıl) · OF02 ~7,3 yıl (20/yıl).
P-PRE ~566 işlem/yıl → n 150'ye ~3 ay (ama bunun %65'i QB).

### Inferences
**Ön-kayıtlı karar kuralı (strateji/prereg.md §11 ile aynı; buraya sayılarla):**
- Başlangıç: gölge modülü kutuda çalışmaya başladığı UTC günü. Tanımlar bu nottaki tablo; hiçbir parametre değişmez.
- **Durdurma (her kol, n = 50 ve n = 100'de):** ortR < 0 ∧ P(EV>0) < %20 → kol bırakılır, gölge kaydı sürer ama portföyden çıkar.
  Ara bakışta erken başarı ilanı YOK.
- **Portföy GO (→ 2. KURAL go_live_gate kartı + kullanıcı kararı):** ileri veride P-PRE n ≥ 500 **ve** her kolun n ≥ 50 olduğu ilk ay sonunda
  (beklenen ~12–18 ay): (i) ortR > 0 ∧ gün-bloklu P(EV>0) ≥ %90, (ii) iki kronolojik yarı ≥ 0, (iii) spread×1,5 > 0, (iv) gerçek dolum ile
  model dolumu arasındaki fark ≤ ortR/2 (ölçüt 5'in ileri karşılığı), (v) plasebo ≥ %95 (aynı yöntem), (vi) ölçülen spread/swap/kayma
  model varsayımlarının içinde (spread medyanı ≤ 17 $, long swap ≤ %22,5/yıl).
- **NO-GO:** (i) sağlanmazsa veya son 6 ay ortR < 0 ise portföy RED; kollar ayrı ayrı yalnız kendi n ≥ 150'lerinde yeniden değerlendirilir.
- **Kol bazında LIVE** yalnız o kolun ileri n ≥ 150 + 6 ölçüt + plasebo ≥ %95 ile (QB ~5 ay, X04 ~1,6 yıl…). C kolları (CAPREV-RV, OF02) yalnız
  betimsel; portföye katılmaları ayrı ön kayıt ister.
- **İcra probu (opsiyonel, kullanıcı kararı):** 0,01 lot, strateji iddiası taşımayan tek tük gerçek emir; amaç komisyon, swap tahakkuk anı/bölücü,
  rollover-açılışı spread'i ve kaymayı ölçmek. Bu bir emir açılması demektir; burada yapılmadı.

### Gaps
- Gölge 2026-11-01 DST geçişini kapsayacak; geçiş haftası ayrıca etiketlenmeli (E46).

---

## Defter satırı taslağı (`docs/KAPI_KAYIT_DEFTERI.md` §2.11'e; biçim §6; kanıt kökü `research/btc_scalp_20261021/strateji/`)

### Takeaway
Sekiz satır. Defter bu ajan tarafından düzenlenmedi (yazma kısıtı).

### Cited Findings
| ID | Tarih | Fikir (kural, parametreler) | Sonuç (sayılar + hangi veri/dönem) | Sınıf |
|---|---|---|---|---|
| BTC-ST01 | 2026-10-22 | **Core (BTC-T03) için scalp-icra: limit geri-çekilme girişi** k∈{0,25;0,5}×ATR5m, W∈{15,60} dk, dolmazsa skip/market; dolum yalnız limitin ≥1 bp içinden geçince; seçim DISC'te (+0,02R/sinyal eşiği). Ön kayıt `strateji/prereg.md` §4 | 8/8 hücre DISC'te piyasadan kötü (en iyisi −0,007R/sinyal) → Core = piyasa girişi. Ters seçilim: POST dolmayan sinyallerin piyasa-R'si +0,15…+0,61, dolanların +0,07…+0,22; dolan işlemde iyileşme yalnız +0,005…+0,05R (stop 249 bp). Kanıt `results/core_exec_grid.csv` | X |
| BTC-ST02 | 2026-10-22 | **Core tek-pozisyon (botun açabileceği hâl)**, SL kaymalı (1 bp / sıcak dk 5 bp) | POST n 96 +0,110R, P %79, yarılar +0,29/−0,07, **BLIND −0,055** (örtüşmeli setin BLIND'ı +0,266), en iyi 20 gün hariç −0,38, plasebo %73, kart 3/6; son 12 ay 10 işlem −0,43; swap −%22,5'te +0,090. Kanıt `results/cards.json` | B− (BTC-T03'ün B'si tek-pozisyonda düşer) |
| BTC-ST03 | 2026-10-22 | **P-PRE GÖLGE portföyü**: Core + MAX10 + QB (2×ATR1h felaket stoplu) + X04, eşit risk, kol başı tek pozisyon | POST n 1.571, +0,026R (+6,9 bp), P %95,7 [−0,004; +0,057], yarılar +0,044/+0,009, stres +0,019, icra farkı 0,014 > 0,013 ✗ (QB), BLIND +0,014, kart 5/6; 2026 −0,017, son 12 ay −0,008 (P %37); en iyi 20 gün hariç −0,013; kol korelasyonları ≤0,28; kollar arası seçim POST'u görmüş → üst sınır. Kanıt `results/cards_table.csv`, `logs/05_extras.log` | C (GÖLGE; ileri sınama) |
| BTC-ST04 | 2026-10-22 | **P-ALL−DV / P-ALL** (P-PRE + CAPREV-RV D0 + OF02 θ5 [+ DV04c-U]) | POST 6/6: +0,038R P %99,2 / +0,054R P %99,8, plasebo %100 — ama ΣR'nin %57'si POST'a bakılarak bulunmuş/geçersiz kollardan (DV04c tek başına 32R); post-hoc kenar yarıya inerse +0,031 / +0,038. Kanıt değil | C (seçim yanlılığı) |
| BTC-ST05 | 2026-10-22 | **B/B− vetolarının bu kollarda katkısı** (V1 +3,5σ sonrası SELL yok, V2 stres∧sakin RV dip alımı yok, V3 VWAP+2σ/PDH süpürmesi sonrası SELL yok) | Portföy Δ DISC −0,007…−0,014R, POST +0,004…+0,006R; X04'te V3 DISC'te +0,306'lık 41 işlemi, POST'ta −0,071'lik 71 işlemi siliyor; V1 DISC +0,573 (n 10) / POST −0,105 (n 13). Taşınmıyor (E18). Kanıt `results/vetoes.csv` | X (bu kollara kapı olarak) / vetolar kendi popülasyonlarında B/B− kalır |
| BTC-ST06 | 2026-10-22 | **Kaldıraç/boyut**: lot = özs×risk%/SL$, nominal = risk%/SL%; gün-bloklu 1 yıl MC | P-PRE sıfır kenarda %1 risk → P(DD≥%20) %25, %0,5 → %0,4; ölçülen kenarda %0,5 → medyan +%7,2, P(zarar) %17. %0,5'te azami eşzamanlı nominal 2,27× (perakende 2:1'i aşar), %0,25'te 1,14×. OF02 2:1'de azami %0,49 risk. Min-lot tuzağı (10k$ MAX10 → %0,46). Kanıt `results/mc_risk.csv`, `leverage_table.csv` | A (matematik/olgu) |
| BTC-ST07 | 2026-10-22 | **QB'ye sunucu SL'si (2×ATR14 1h felaket stopu)** | POST SL vuruşu %4,4; +4,25 bp → +3,67 bp (~0,6 bp maliyet), 2×ATR biriminde +0,016R; icra ölçütü hâlâ ✗ (kenar ≈ 2 spread, E44). Kanıt `logs/05_extras.log` | B (maliyet olgusu) |
| BTC-ST08 | 2026-10-22 | **İleri gölge karar kuralı + bot şartnamesi** (UTC yeniden örnekleme, magic +30…+36, fren-öncesi gölge, spread koruması 25/40 $) | Uygulanmadı; n=150 süreleri QB 0,4 / X04 1,6 / MAX10 2,1 / Core 4,3 / CAPREV 9,5 / OF02 7,3 yıl; P-PRE 2σ ~3,7 yıl | — (plan) |

---

## Yeni yöntem tuzakları

### Takeaway
Altı öneri (numara koordinatöre bırakıldı; §1 E50'de bitiyor, not 04/05/06'nın E51–E54/T1–T5 önerileriyle çakışmasın diye "E-ST" öneki).

### Cited Findings
| öneri | Tuzak | Vaka | Önlem |
|---|---|---|---|
| E-ST1 | **Örtüşmeli olay kartı, tek-pozisyonlu botun göreceği sonucu temsil etmez — işaret bile dönebilir** (E31'in sonucu değiştiren hâli): kırılım kümelerinde kâr 2./3. sinyallerde, bot ise yalnız ilkini alır | BTC-T03 BLIND: örtüşmeli +0,266 (n 62) vs tek-poz −0,055 (n 27); POST +0,202 vs +0,110 | kartı daima botun gerçek pozisyon kuralıyla (tek-poz zinciri) raporla; örtüşmeli set yalnız "sinyal kalitesi" bilgisidir |
| E-ST2 | **Limit/geri-çekilme girişinde ters seçilim:** dolmayan sinyaller en güçlü olanlardır; "işlem başı R arttı" sinyal başı kaybı gizler | Core: dolan işlemde +0,005…+0,05R iyileşme, sinyal başı −0,007…−0,15R; dolmayanların piyasa-R'si +0,35…+0,61 | limit varyantlarını **sinyal başı** (skip=0) ve dolan/dolmayan piyasa-R'siyle raporla |
| E-ST3 | **Portföy birleştirmesi büyük-n plasebo/hacim ölçütlerini yapay geçirir** (E51'in portföy yüzü): sıfıra yakın kollar havuzlanınca plasebo %100, hacim ölçütünü en sık işlem yapan küçük-kenarlı kol doldurur | P-PRE plasebo %100 iken kollar %73/79,5/98/84; işlemlerin %65'i QB (+3,7 bp, ölçüt 5 ✗) | portföy kartında kol bazında plasebo ve n'yi yanında yaz; hacmi "en az iki kolun her biri ≥ X" şartıyla oku; kenarı bp ile ver |
| E-ST4 | **Spread'i bariyer yolunda (bid/ask) mı PnL'den mi düşmek** güçlü-hareket olaylarında sistematik fark üretir | OF02 +0,210 (yol-içi, MT5 gibi) vs +0,176 (mid bariyer + PnL'den maliyet); DV04c +0,273 vs +0,243 | bot gerçeği yol-içi konvansiyondur; ikisini birlikte raporla, fark ≥ 0,02R ise sonucu belirsizlik bandıyla ver |
| E-ST5 | **Broker H4/D1 barları sunucu saatine hizalı** (Pepperstone UTC+3 → D1 21:00 UTC'de başlar); UTC-hizalı araştırma kurallarını broker barlarıyla uygulamak başka bir kuraldır (E2'nin 7/24 varlık uzantısı) | BTC-T03 (UTC H4 00/04/…) ve MAX10/CAPREV (UTC günü) broker D1/H4 ile farklı olay üretir | botta M1/H1'i UTC'ye çevirip yeniden örnekle; gölge kaydında bar sınırlarını UTC ile yaz |
| E-ST6 | **Günlük zarar freni `continue` ettiğinde frenden sonra çağrılan gölge modülleri de susar** → gölge örneklemi kötü günlerde delikli, seçilmiş olur | `forexsai_demo_bot.py` ana döngüsü: fren bloğu `continue`; CAPREV/XAU gölge çağrıları sonra | emir göndermeyen gölge/izleme çağrılarını frenden ÖNCE yap; fren günlerini gölge kaydında etiketle |

### Inferences
- Bu turun ana metodolojik dersi: **iyileştirme aramadan önce kartı botun gerçekten uygulayacağı hâlle kur** (tek pozisyon, sunucu SL'si,
  yol-içi spread, UTC'ye hizalı barlar). Bu dört düzeltme Core'u B'den B−'ye, QB'yi +3,7'den +3,7−0,6 bp'ye indirdi; hiçbiri adayı
  güçlendirmedi.

### Gaps
- 1. KURAL (Evrim Paneli oturum notu + backlog) ve 3. KURAL (defter satırları) yazma kısıtı nedeniyle yapılmadı. Önerilen backlog:
  "BTC-ST gölge portföyü v1 modülü (gölge, emir yok)" (wiring, high) · "P-PRE 2017–21 bağımsız tek seferlik sınav — indirme onayı" (experiment, high) ·
  "BTC icra probu 0,01 lot — kullanıcı kararı" (decision, medium) · "Core piramitleme (küme içi 2./3. sinyal) — yeni ön kayıt" (idea, low).
