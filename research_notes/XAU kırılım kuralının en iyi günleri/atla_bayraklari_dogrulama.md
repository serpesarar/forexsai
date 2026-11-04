# MK-04 / R0B_G1 için iki "ATLA" bayrağının (seri kırılım, önceki gün >%1) ve FOMC kuyruğunun doğrulama sınaması

Bu bir web araştırması değil, nicel bir doğrulama sınaması. Aşağıdaki tüm "kaynaklar" bu çalışmanın yerel dosyalarıdır.
- Kod ve çıktılar: `/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/`
  (`01_build.py` … `05_overlap.py`, `results/`).
- Ön kayıt: [PROTOCOL.md](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/PROTOCOL.md),
  **2026-10-16 04:31 UTC**'de, hiçbir sonuç hesaplanmadan yazıldı.
- Şu klasörler SALT-OKUNUR kullanıldı: `mekanik/`, `anatomi/`, `makro/`, `erken_sinyal/`. Hiçbirine yazılmadı. `docs/KAPI_KAYIT_DEFTERI.md`
  ve `yeni deneme/xau_shadow.py` değiştirilmedi.

Kısaltmalar:
- **S1** = seri kırılım. Son 24 kapanmış H1 barda ≥2 önceki 20-bar tepe kırılımı varsa atla.
- **S2** = önceki gün rallisi. Önceki UTC gününde altın >+%1 yükseldiyse atla.
- **S3** = FOMC açıklaması 20 saatlik tutma penceresine düşüyor (yalnız kuyruk etkisi).
- **d** = ortalama R farkı: bayraklı işlemler eksi bayraksız işlemler, tek pozisyonlu taban kümesinde.

## 1. Ön kayıt, tanımlar ve mutabakat

### Takeaway
Bayraklar araştırmacıların tanımıyla birebir yeniden kuruldu, eşikler yeniden ayarlanmadı. Kural aynen yeniden üretildi:
- 12.403 olay
- tek pozisyonda n=3.664, +290,5R, ortalama +0,0793R

Ön kayıt 6 ölçüt tanımladı (C1 seçim düzeltmesi, C2 plasebo, C3 çağ kararlılığı, C4 ileri kanıt, C5 pratik etki,
artı kuyruk ölçütleri). Verdikt şeması da hesaptan önce sabitlendi.

### Cited Findings
- **Mutabakat:**
  - Benim S1 sayımım anatomi `xa_brk_density24` ile 3.664/3.664 işlemde aynı çıktı.
  - Benim S2 bayrağım makro `F_gprev_up1` ile 3.664/3.664 işlemde aynı çıktı.
  - Taban kümesi aynı: n=3.664, toplam +290,5R.
  - S1: bayraklı −0,019 (n=1.643), bayraksız +0,159.
  - S2: bayraklı −0,188 (n=455), bayraksız +0,117.
  - S3: bayraklı +0,137 (n=95), bayraksız +0,078.
  - Kaynak: [01_build.py](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/01_build.py) (assert'ler)
- **S1 tanımı** (anatomi `build.py`):
  - Sinyal barı s için [s−24, s−1] aralığındaki R0 olay barları sayılır. Sinyal barı dahil değil.
  - Olay listesi `events(d,"R0",+1).sig`.
  - Atla: sayı ≥2. Komşuluk ≥1 ve ≥3 yalnız sağlamlık için.
  - Kaynak: [common.py `brk_density`](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/common.py)
- **S2 tanımı** (makro `04_features.add_feats`, `daily_gold` doğrudan import edildi):
  - g1 = giriş barının UTC gününden önceki son Duka UTC-gün kapanışı.
  - g2 = ondan bir önceki UTC-gün kapanışı. Pazar günleri ayrı gün sayılır.
  - gprev = g1/g2 − 1. Atla: gprev > %1,00. Komşuluk %0,75 ve %1,25.
  - Kaynak: [common.py `gprev_for`](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/common.py)
- **S3 tanımı** (makro `07_event_windows.win`):
  - Planlı FOMC açıklama anı [giriş, giriş+20 saat) içinde.
  - İleri dönem için iki tarih elle eklendi: 2026-07-29 ve 2026-09-16, ikisi de 18:00 UTC. Makro `calendar.csv` 2026-06-17'de bitiyordu.
  - Kaynak: [PROTOCOL.md §2](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/PROTOCOL.md)
- **Önceden bilinen sonuç (beyan edildi):** S1'in Duka uzatmasında ters döndüğü zaten biliniyordu (+0,181'e karşı +0,016).
  Bu nedenle S1'in C4 sonucu önceden kısmen biliniyordu. Kaynak: [PROTOCOL.md §0](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/PROTOCOL.md)
- **Kayıtlı sapmalar (§9):**
  - Aileye anatomi'nin "tekil ∧ ATH≤%2" etkileşim dilimi de eklendi. Bu aileyi büyütür, yani daha muhafazakârdır.
  - Özdeş bayraklar ayıklandı: erken F1 bir anatomi bayrağıyla aynıydı.
  - C5'in boş p'si keşif verisinde hesaplanır, bu yüzden seçim düzeltmeli değildir.
  - Kaynak: [PROTOCOL.md §9](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/PROTOCOL.md)

### Inferences
- Tanım mutabakatı tam. Aşağıdaki farklar araştırmacıların sayılarıyla doğrudan karşılaştırılabilir.

### Gaps
- Gün tanımı UTC takvim günü ve Pazar ayrı gün. Bu tanımın NY-17 gün sınırı karşısındaki duyarlılığı bilerek sınanmadı.
  Yeni bir varyant olurdu, yani çatallanma riski taşırdı.

## 2. Seçim düzeltmesi (C1): aramanın tamamı hesaba katılınca bayraklar ayakta mı?

### Takeaway
Arama ailesi yeniden kuruldu: 105 benzersiz ex-ante bayrak, sonuçlar yıl içinde dairesel kaydırıldı, 5.000 tekrar,
iki yönlü max-|z| ile p_sel hesaplandı.
- **S2 rahat geçiyor:** z −3,83, ailede 2. sıra, p_sel 0,016.
- **S1 sınırda geçiyor:** z −3,33, 4. sıra, p_sel 0,081. Eşik ≤0,10.
- **S3'ün kuyruk etkisi düzeltmeden geçmiyor:** P(R≥3) farkı z +3,10, p_sel 0,168.

Kalibrasyon için bir uyarı var. Aynı ailede p_sel'i 0,093 olan erken_sinyal F2 (D1 NR4/inside), ileri dönemde sönen bir
bayraktı. Yani S1'in seçim düzeltmeli düzeyi, geçmişte taşınamamış bir bulgunun düzeyiyle aynı bölgede.

### Cited Findings
- **Aile 105 bayraktan oluşuyor:**
  - anatomi 74: 33 ex-ante `xa_` özelliğinin beşli Q1 ve Q5 bayrakları ya da ikili =1, 3 seans, Pazartesi ve Cuma, 9 aday dilim
  - makro 22: 18 `F_` özelliği, FOMC/CPI/NFP/JH pencereleri, post-hoc tatil ve gvol≤0,73
  - erken_sinyal 9: F2–F10
  - Boş dağılımda max|z| yüzdelikleri: %50'de 2,64, %90'da 3,27, %95'te 3,48, %99'da 4,01.
  - Kaynak: [02_log.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/02_log.txt), [family.json](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/family.json)
- **S2 (önceki gün >%1):**
  - d −0,305, boş ortalaması +0,046, boş sd 0,092, z −3,83.
  - Ham p 0,0016, p_sel iki yönlü 0,016, yalnız negatif yönde 0,003, Holm 0,163.
  - Yalnız makro alt-ailesi içinde (K=22) p_sel 0,005.
  - Kaynak: [c1_family.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/c1_family.csv)
- **S1 (seri ≥2):**
  - d −0,177, boş ortalaması +0,016, boş sd 0,058, z −3,33.
  - Ham p 0,0006, p_sel iki yönlü 0,081, yalnız negatif yönde 0,026, Holm 0,062.
  - Yalnız anatomi alt-ailesi içinde (K=74) p_sel 0,058.
  - Aynı özelliğin Q5 dilimi (`xa_brk_density24_Q5`, en yoğun beşte bir): z −3,50, p_sel 0,046.
  - Kaynak: [c1_family.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/c1_family.csv)
- **Ailede p_sel ≤0,10 olan bayraklar:**

  | Bayrak | z | p_sel |
  |---|---|---|
  | tekil∧ATH≤%2 | +4,53 | 0,002 |
  | S2 | −3,83 | 0,016 |
  | density24_Q5 | −3,50 | 0,046 |
  | S1 | −3,33 | 0,081 |
  | erken F2 | +3,29 | 0,093 |

  Kaynak: [c1_family.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/c1_family.csv)
- **Kuyruk ailesi, P(R≥3) farkı:**
  - S3 FOMC penceresinde d +0,078 (%14,7'ye karşı %6,9), z +3,10, ailede 13. sıra, p_sel 0,168.
  - Bu ailede en güçlü bayraklar ATR düzeyi bayrakları. `xa_atrH1_pct500_Q1` z +5,80, p_sel <0,001. Bu, "dar stop =
    büyük R" ölçüm etkisidir (E31 adayı).
  - Kaynak: [c1_tail_family.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/c1_tail_family.csv)
- **Boş ortalaması sıfır değil:** S2'de +0,046, S1'de +0,016. Bayraklar yıllarla ilişkili.
  Yıl içinde kaydırma, yıl karışımını boşun içinde tutuyor. Bu yüzden z yıl-içi etkiyi ölçüyor.
  Kaynak: [c1_family.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/c1_family.csv)

### Inferences
- S2, "18 özellikten seçildi" eleştirisini aşıyor. 105 bayraklık genişletilmiş aramada bile tesadüfle açıklanması zor
  (p_sel 0,016).
- S1 düzeltmeden zar zor geçiyor. Aile birkaç eşik varyantıyla genişleseydi 0,10'u aşabilirdi. Ayrıca aynı p_sel
  bölgesindeki F2 ileriye taşınmamıştı (E12/E17). S1'in C1'i "geçti" yazıldı ama zayıf bir geçiş.

### Gaps
- Anatomi'nin gün düzeyindeki AUC taraması aileye girmedi. 54 özelliğin ex-post olanları ve farklı istatistik türü
  nedeniyle dışarıda kaldı. Bu taramadaki ek "bakışlar" aileyi biraz daha büyütürdü, yani gerçek p_sel biraz daha yüksek
  olabilir.
- Araştırmacıların bakıp not etmediği varyantlar bilinemez. Aile alt sınırdır.

## 3. Plasebo (C2): bayrak kurala mı özgü, yoksa piyasa geneli sürüklenme mi?

### Takeaway
İki bayrak da kuralın işlemlerine, aynı yıl, UTC saati ve bayrak durumundaki rastgele BUY'lardan **daha çok** zarar veriyor.
Dolayısıyla ikisi de yalnız piyasa geneli etki değil.
- **S2:** Rastgele BUY'da da +%1 günden sonra bir düşüş var: −0,044'e karşı +0,048, fark −0,092. Bu kısım "altın ralliden
  sonra ortalamaya döner" etkisi. Kuralda fark −0,305. Fark-içinde-fark (DiD) −0,213, P(DiD<0)=0,997. Etkinin yaklaşık
  %70'i kırılımı kovalamaya özgü.
- **S1:** DiD −0,123, P=0,983. Yaklaşık %30'u piyasa geneli: seri kırılım sonrası rastgele BUY da daha kötü.
- **S3:** Rastgele long da FOMC'yi taşıyınca aynı kuyruk artışını alıyor. DiD (P3) −0,003. Kurala özgü değil.

### Cited Findings
Plasebo yöntemi P1-F: aynı yıl × UTC saati × bayrak durumundaki tüm geçerli H1 barlarından 40 rastgele BUY, aynı geometri,
$0,12 spread. Gün-blok bootstrap 4.000. Kaynak: [c2_p1f.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/c2_p1f.csv)

| Bayrak | Kural (bayraklı / bayraksız) | Kural farkı | Plasebo (bayraklı / bayraksız) | Plasebo farkı | DiD | P(DiD<0) | %95 CI |
|---|---|---|---|---|---|---|---|
| S2 >%1 | −0,188 / +0,117 | −0,305 | −0,044 / +0,048 | −0,092 | **−0,213** | 0,997 | [−0,349, −0,076] |
| S2 >%0,75 | | | | | −0,161 | 0,993 | |
| S2 >%1,25 | | | | | −0,274 | 0,9998 | |
| S1 ≥2 | −0,019 / +0,159 | −0,177 | +0,014 / +0,069 | −0,055 | **−0,123** | 0,983 | [−0,234, −0,010] |
| S1 ≥1 | | | | | −0,099 | 0,953 | |
| S1 ≥3 | | | | | −0,167 | 0,998 | |
| S1 ∨ S2 | | | | | −0,124 | 0,984 | |
| S3, ortR | | | | | −0,227 | 0,84 (DiD<0 yönünde) | |
| S3, P(R≥3) | %14,7 / %6,9 | | %14,0 / %5,9 | | −0,003 | P(DiD>0) 0,45 | |

- Bu işaret, makro araştırmacısının daha kaba rastgele-BUY karşılaştırmasıyla tutarlı: o karşılaştırmada S2 için rastgele
  fark −0,089 idi — [makro_haber_baglami.md](/Users/melihcanodacioglu/Desktop/panel/research_notes/XAU%20k%C4%B1r%C4%B1l%C4%B1m%20kural%C4%B1n%C4%B1n%20en%20iyi%20g%C3%BCnleri/makro_haber_baglami.md)

### Inferences
- **S2'nin iki parçası var.**
  - Küçük parça (yaklaşık −0,09R) altının +%1 günden sonraki genel ertesi gün zayıflığı. Bu etki her BUY'a uygulanır.
  - Büyük parça (yaklaşık −0,21R) "ralli gününden sonra yeni 20 saatlik tepeyi kovalama" cezası. Defterin kovalama cezası
    (meta-ders 4, GF-15) ve "coşku dönmez" dersi ile aynı aile.
- **S1'in plasebo tarafı daha zayıf ve CI sıfıra yakın.** Etkinin önemli kısmı genel bir "art arda yeni tepelerden sonra
  yorulma" durumu.
- **S3 FOMC kuyruğu tümüyle piyasa geneli.** Kırılım, FOMC'yi long taşımanın getirdiği kuyruğa hiçbir şey eklemiyor.

### Gaps
- P1-F yıl × saat × bayrak eşlemesi aynı haftayı ya da günü kontrol etmiyor. Bu bilerek yapıldı: E15/E31 tuzağından
  kaçınmak için.

## 4. Çağ kararlılığı (C3) ve ileri kanıt (C4): Duka uzatması, broker 1m kasası, bir-çağ-hariç

### Takeaway
- **Çağlar:** İki bayrak da dört çağın dördünde negatif. Bir çağ çıkarıldığında kalan etki de her durumda negatif. C3 ikisinde de geçiyor.
- **İleri dönemde ayrışıyorlar:**
  - S2 iki beslemede de aynı yönde güçlü. Broker'da bayraklı −0,22'ye karşı bayraksız +0,20 (d −0,42, n=10).
    Duka'da d −0,60 (n=13).
  - S1 iki beslemede de **ters**. Broker d +0,37 (n=25), Duka d +0,17 (n=26).
- **Ters dönüşün kaynağı:** S1'in ileri dönemdeki ters dönüşünün neredeyse tamamı S1∧¬S2 işlemlerinden geliyor.
  Bu işlemler broker'da 16 işlemde +0,59, Duka'da +0,41. S1∧S2 işlemleri ileride de negatif.
- **Güç uyarısı:** İleri dönem 56 işlem ve iki besleme aynı takvimi kapsıyor. Yalnız işaret okunabilir.

### Cited Findings
- **Çağlar, ortR farkı d** — [c3_eras.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/c3_eras.csv):

  | Bayrak | 2008-12 | 2013-16 | 2017-20 | 2021-26 | Çağ hariç d aralığı |
  |---|---|---|---|---|---|
  | S2 | −0,388 | −0,322 | −0,198 | −0,310 | −0,267 … −0,332 |
  | S1 | −0,244 | −0,216 | −0,054 | −0,207 | −0,151 … −0,211 |

  S2'nin komşu eşikleri dört çağda da negatif: %0,75'te −0,17 … −0,35, %1,25'te −0,16 … −0,48.
  S1'in ≥1 ve ≥3 eşikleri de dört çağda da negatif.
- **Yıl bazında:** S2 farkı 19 yılın 17'sinde negatif (yalnız 2017 +0,07 ve 2023 +0,29 pozitif). S1 farkı 19 yılın 13'ünde negatif.
  Kaynak: [02_log.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/02_log.txt)
- **İleri dönem tabanları:**
  - Duka 06-17→09-30: tek pozisyonda 56 işlem, +0,093R, +5,2R. Anatomi uzatmasıyla aynı.
  - Broker 1m 06-17→10-14: 56 işlem, +0,122R, +6,9R. erken_sinyal kasasıyla aynı.
  - Kaynak: [03_log.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/03_log.txt)
- **İleri dönem bayrak farkları** — [c4_forward.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/c4_forward.csv),
  [c4_perm.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/c4_perm.csv):

  | Küme | Bayrak | n bayraklı/56 | bayraklı / bayraksız | d | etiket-permütasyon P(boş ≤ d) |
  |---|---|---|---|---|---|
  | broker | S2 | 10 | −0,223 / +0,198 | −0,421 | 0,24 |
  | Duka | S2 | 13 | −0,369 / +0,232 | −0,601 | 0,12 |
  | broker | S1 | 25 | +0,326 / −0,042 | +0,368 | 0,80 |
  | Duka | S1 | 26 | +0,181 / +0,016 | +0,165 | 0,65 |
  | broker | S1∨S2 | 26 | | +0,285 | 0,74 |
  | Duka | S1∨S2 | 29 | | −0,070 | 0,43 |

  S2'nin komşu eşiklerinde d: broker −0,52 / −0,31, Duka −0,68 / −0,43.
- **İleri dönem 2×2, işlem sayısı ve ortR:**

  | Hücre | Broker | Duka |
  |---|---|---|
  | ¬S1¬S2 | 30 işlem, −0,01 | 27 işlem, +0,13 |
  | ¬S1 S2 | 1 işlem, −1,00 | 3 işlem, −1,00 |
  | S1 ¬S2 | 16 işlem, +0,59 | 16 işlem, +0,41 |
  | S1 S2 | 9 işlem, −0,14 | 10 işlem, −0,18 |

  Ana küme: ¬S1¬S2 1.973 işlem +0,167 · ¬S1 S2 48 işlem −0,160 · S1 ¬S2 1.236 işlem +0,038 · S1 S2 407 işlem −0,191.
  Kaynak: [05_log.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/05_log.txt)
- **S2 ile S1 iç içe:** S2 işlemlerinin %89'u (407/455) aynı zamanda S1. S2 işlemlerinde dens24 medyanı 6, diğerlerinde 1.
  - S1 içinde S2'nin etkisi −0,229.
  - S1 dışında S2'nin etkisi −0,326 (n=48).
  - S2 dışında S1'in etkisi −0,128.
  - S2 içinde S1'in etkisi yalnız −0,031.
  - Kaynak: [05_log.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/05_log.txt)
- **S3'ün ileri dönem işlemleri:** FOMC penceresinde broker'da 3, Duka'da 4 işlem var (06-17, 07-29, 09-16 FOMC'leri).
  Ortalama R broker'da +0,21, Duka'da −0,07. Hiçbiri R≥3 değil. İleri dönemde FOMC penceresi kuyruğu gözlenmedi, ama n=3–4.
  Kaynak: [c4_forward.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/c4_forward.csv)

### Inferences
- **S2 dört çağda, iki ileri beslemede ve üç eşik komşuluğunda aynı işareti veriyor.** Eşiğe hassas değil ve
  büyüklüğü eşikle monoton büyüyor (%0,75'ten %1,25'e). Bu, gerçek bir mekanizmanın imzası.
- **S1'in bilgisi büyük ölçüde S2 ile ortak.** S1'in tam örneklemdeki etkisinin bir kısmı, S2'nin S1 içindeki işlemlerinden
  geliyor: S2 dışında S1 etkisi −0,128, S2 içinde −0,031. S1'in kendine özgü kısmı (S1∧¬S2) ileri dönemde ters döndü.
  Bu tek başına çürütme değil (P(boş ≥ d) yaklaşık 0,20), ama C1'deki sınırda geçişle birlikte ciddi bir uyarı.

### Gaps
- İleri dönemde bağımsız tek gözlem var: aynı 4 ay, iki besleme. S2'nin ileri dönem permütasyon p'si 0,12–0,24 ile anlamlı
  değil, yalnız işaret tutarlı. Ön kayıt C4'ü zaten "yalnız işaret" diye tanımladı.
- 2026 çağı yalnız 5,5 ay ve 2021-26 çağına dahil.

## 5. Pratik etki (C5): filtre olarak tek pozisyonla yeniden yürütme. En iyi günlere bağımlılık azalıyor mu?

### Takeaway
Keşif verisinde iki filtre de eğriyi her ölçüde iyileştiriyor: ortalama R, toplam R, R/hafta, maksimum düşüş, Sharpe ve
en iyi günlere bağımlılık. Bu iyileşme kaydırılmış boşa göre anlamlı. Ancak keşif verisinde ölçüldüğü için seçim
düzeltmeli değil.

| Ölçü | Taban | S2 atla | S1 atla |
|---|---|---|---|
| işlem/hafta | 3,80 | 3,38 | 2,12 |
| ortR | +0,079 | +0,110 | +0,162 |
| toplam R | 290 | 357 | 332 |
| R/hafta | 0,301 | 0,370 | 0,344 |
| maks. düşüş | −59R | −49R | −37R |
| en iyi 20 günün payı | %61,6 | %50,2 | %48,5 |

İleri dönemde yalnız S2 filtresi iyileştiriyor:
- S2: broker'da toplam +6,9R'den +11,8R'ye, Duka'da +5,2R'den +12,6R'ye.
- S1: broker'da +6,9R'den +1,1R'ye düşüyor.

Birleşik filtre (S1 ∨ S2) keşifte en yüksek Sharpe'ı veriyor ama ileride S2 tek başına daha iyi.

### Cited Findings
Ana küme Duka 2008-01→2026-06-16, 964 takvim haftası. Boş: (R, süre) yıl içinde dairesel kaydırıldı, 2.000 tekrar.
Kaynak: [c5_practical.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/c5_practical.csv),
[04_log.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/04_log.txt)

| Varyant | n | /hafta | ortR | toplam R | maks DD | +hafta (aktif) | R/hafta | Sharpe_h | en iyi-20 gün payı | en iyi-20 hariç ortR | ortR artış p | toplam R artış p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Taban | 3.664 | 3,80 | +0,079 | 290,5 | −59,1 | %46,7 | 0,301 | 0,094 | %61,6 | +0,031 | — | — |
| **S2 atla (>%1)** | 3.259 | 3,38 | +0,110 | 356,8 | −48,6 | %48,0 | 0,370 | 0,116 | %50,2 | +0,055 | <0,001 | 0,004 |
| S2 atla >%0,75 | 3.109 | 3,23 | +0,117 | 365,0 | −54,2 | %48,1 | 0,379 | 0,120 | %49,0 | +0,060 | <0,001 | 0,004 |
| S2 atla >%1,25 | 3.392 | 3,52 | +0,103 | 348,9 | −47,7 | %48,1 | 0,362 | 0,113 | %51,3 | +0,051 | <0,001 | 0,005 |
| **S1 atla (≥2)** | 2.047 | 2,12 | +0,162 | 332,1 | −36,6 | %48,2 | 0,344 | 0,135 | %48,5 | +0,084 | 0,004 | 0,039 |
| S1 atla ≥1 | 1.450 | 1,50 | +0,146 | 211,0 | −27,4 | %42,4 | 0,219 | 0,102 | %69,2 | +0,046 | 0,26 | 0,71 |
| S1 atla ≥3 | 2.457 | 2,55 | +0,134 | 328,7 | −33,1 | %49,8 | 0,341 | 0,127 | %49,3 | +0,069 | 0,006 | 0,033 |
| *S1 ∨ S2 atla (ikincil)* | 1.996 | 2,07 | +0,170 | 340,1 | −36,6 | %48,4 | 0,353 | 0,139 | %47,4 | +0,091 | 0,002 | 0,031 |

- **Yıllık toplam R:**
  - S2 filtresi 19 yılın 13'ünde tabanı geçiyor (S1 filtresi 11'inde). Büyük kayıplar 2024 (37,2'den 28,6'ya) ve 2023 (14,0'dan 6,4'e).
  - S1 filtresi 2009 (56,4'ten 26,3'e), 2025 (60,3'ten 28,9'a), 2017 ve 2023'te belirgin kaybettiriyor; 2012, 2014,
    2018 ve 2022'de belirgin kazandırıyor.
  - Pozitif yıl sayısı: taban 14/19, S2 16/19, S1 14/19.
  - Kaynak: [c5_yearly.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/c5_yearly.csv)
- **İleri dönem filtre sonuçları** — [04_log.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/04_log.txt):

  | Varyant | Broker n / ortR / toplam / maks DD | Duka n / ortR / toplam / maks DD |
  |---|---|---|
  | Taban | 56 / +0,122 / +6,9R / −5,9 | 56 / +0,093 / +5,2R / −7,5 |
  | S2 atla | 46 / +0,256 / +11,8R / −4,7 | 43 / +0,294 / +12,6R / −5,0 |
  | S1 atla | 32 / +0,033 / +1,1R / −7,7 | 31 / +0,088 / +2,7R / −7,7 |
  | S1 ∨ S2 atla | 31 / +0,067 / +2,1R | 28 / +0,205 / +5,7R |

- **Filtrede ek kazanç kaynağı:** Atlanan olay pozisyonu kilitlemediği için, sonraki bayraksız kırılım alınabiliyor.
  Bu yüzden S2 atlamanın kazancı (+66R), yalnız S2 işlemlerinin toplamından büyük: tabanda S2 işlemleri −85R'ydi,
  ama yerlerine giren işlemler de var.
  - Yalnız S2∧¬S1 atlandığında küçük bir iyileşme kalıyor: +0,083R, toplam 301R.
  - Kaynak: [05_log.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/05_log.txt)

### Inferences
- **En iyi günlere bağımlılık azalıyor ama kaybolmuyor.**
  - S2 atlandığında en iyi 20 günün payı %62'den %50'ye iniyor; en iyi 20 gün hariç ortR iki katına çıkıyor (+0,031'den +0,055'e).
  - Ancak en iyi 50 gün hâlâ toplam R'nin %103'ü. Yani 50 gün dışında kalan günler toplamda hâlâ yaklaşık başabaş.
  - Filtre kuyruğu büyütmüyor; kötü günleri (testere ve kovalama) kesiyor.
- **S1 filtresi işlemlerin %44'ünü atıyor ve stratejiyi kökten değiştiriyor.**
  - Haftada 2,1 işlem kalıyor.
  - 2009 ve 2025 gibi büyük boğa yıllarında R'nin yarısını kaybediyor.
  - İleride ters döndü.
  - S2 ise işlemlerin yalnız %11'ini atıyor ve R/hafta'yı en çok artıran tek bayrak (0,301'den 0,370'e).
- **Keşif verisindeki C5 iyileşmeleri ileride küçülmeli (kazananın laneti).** S2 için C1'den sonra kalan makul beklenti,
  örneklem içi −0,305 farkın yarısı ile üçte ikisi arasında bir fark. Bu bir tahmin; resmi küçültme yapılmadı.

### Gaps
- Swap ve finansman maliyeti modellenmedi (MK-06 ile aynı).
- R/hafta ölçüsü 1R sabit risk varsayıyor. Lot sabitken dolar etkisi farklı olur (E31).
- C5'in p'leri keşif verisinde. Seçim düzeltmeli bir pratik-etki boşu kurulmadı: her tekrarda aileyi filtre olarak yeniden
  yürütmek pahalı ve bu yapılmadı.

## 6. Verdikt ve `yeni deneme/xau_shadow.py` entegrasyon tarifi

### Takeaway
Ön-kayıtlı şemaya göre sonuçlar:

| Madde | Verdikt | Kısa gerekçe |
|---|---|---|
| **S2 (önceki gün >%1 → atla)** | **A** | Beş ölçüt de geçti. Etkinin yaklaşık %30'u piyasa geneli "+%1 gün sonrası dönüş", yaklaşık %70'i kırılımı kovalama cezası. |
| **S1 (seri kırılım ≥2 → atla)** | **B** | Yalnız C4 düştü, ama zayıf bir B. Uygulama önerim: canlı ve gölge filtresi olarak **uygulanmasın**, yalnız kayıt alanı olarak yazılsın. |
| **S3 (FOMC penceresi)** | **RED** (kurala özgü kuyruk) | C1 ve C2 düştü. FOMC'yi long taşımanın genel kuyruğu betimsel C. |
| **Birleşik (S1 ∨ S2)** | — (ikincil) | Keşifte en yüksek Sharpe, ileride S2 tek başına daha iyi. Önerilmez. |

S2'nin A'sı MK-04 kuralının kendi sınıfını değiştirmez. Kural hâlâ gölgede (B+). A, "gölge simülasyonunda ve kural canlıya
alınırsa canlıda bu atlama uygulanır" anlamına gelir.

### Cited Findings
**Ölçüt tablosu** (ölçütler [PROTOCOL.md §3–8](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/PROTOCOL.md)'de tanımlı):

| Ölçüt | S2 >%1 | S1 ≥2 | S3 FOMC (kuyruk) |
|---|---|---|---|
| C1 seçim (p_sel ≤0,10) | ✓ 0,016 | ✓ 0,081 (sınırda) | ✗ 0,168 (P3) |
| C2 P1-F DiD | ✓ −0,213, P 0,997 | ✓ −0,123, P 0,983 | ✗ −0,003 (P3) |
| C3 çağlar ve bir-çağ-hariç | ✓ 4/4, hariç d'lerin hepsi <0 | ✓ 4/4, hariç d'lerin hepsi <0 | ✓ 4/4 P3>0 |
| C4 broker işareti (d ≤0) | ✓ −0,421 (Duka −0,601) | ✗ +0,368 (Duka +0,165) | n=3, kuyruk yok |
| C5 pratik | ✓ ortR p<0,001, R/hafta ↑, DD ↑ | ✓ ortR p 0,004, R/hafta ↑, DD ↑ | — |
| Verdikt | **A** | **B** | **RED** (betimsel C) |

Kaynak: [02_log.txt](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/02_log.txt),
[c4_forward.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/c4_forward.csv),
[c5_practical.csv](/Users/melihcanodacioglu/Desktop/panel/research/xau_best_days_20261015/dogrulama/results/c5_practical.csv)

**Mevcut gölge kodunun okunan durumu** ([yeni deneme/xau_shadow.py](/Users/melihcanodacioglu/Desktop/panel/yeni%20deneme/xau_shadow.py), değiştirilmedi):
- `poll` son kapanmış 200 H1 barı (`copy_rates_from_pos(…, 1, 200)`) broker ofseti düşülmüş UTC 't' ile alıyor.
- Tek pozisyon kuralı: açık olay varken gelen yeni sinyal 'overlap' olarak kaydediliyor.
- ATR'yi sinyal barı **hariç** 14 bardan hesaplıyor (`atr_before`). Mekanik R0B_G1'in ATR'si ise sinyal barını **dahil** ediyor
  (`mech.prep_h1`: `tr.rolling(14).mean()` sinyal barı indeksinde). Bu, bu çalışmanın kapsamı dışında bir tutarsızlık.
  Not edildi, düzeltilmedi.

**Entegrasyon tarifi** (karar anı = sinyal barı i kapandıktan sonraki ilk poll; yalnız kapanmış barlar):
1. **S2 (uygulanacak atlama, A):**
   - Giriş barının UTC takvim tarihi = date_UTC(t_i + 3600).
   - g1 = tarihi giriş tarihinden küçük olan **son** barın kapanışı.
   - g2 = tarihi g1 barının tarihinden küçük olan son barın kapanışı. Bar olan herhangi bir UTC günü sayılır,
     Pazar akşamı oturumu da ayrı gündür. Örnek: Pazartesi girişinde g1 = Pazar 21–23 UTC oturumunun son kapanışı,
     g2 = Cuma kapanışı. Pazar girişinde g1 = Cuma, g2 = Perşembe.
   - prevday_ret = g1/g2 − 1. **skip_s2 = prevday_ret > 0,010.**
   - 200 barlık pencere yeterli.
   - Kayıt: `prevday_ret`, `skip_s2`.
   - Gölgede atlanan olay **pozisyonu kilitlemez.** Araştırmadaki filtre yeniden yürütmesi böyle çalışır. Bu yüzden
     mevcut tek "açık olay" durum makinesinin yanına ikinci bir **filtreli varyant** durumu gerekir (örn. `open_f`).
     Böylece hem filtresiz MK-04 hem "MK-04 + S2" eğrisi karşılaştırılabilir.
2. **S1 (yalnız kayıt, B):**
   - dens24 = Σ_{j=i−24}^{i−1} [high_j ≥ max(high_{j−20..j−1})].
   - Pencere ham bar sırasıdır, hafta sonu boşluğu kırılmaz (`rolling(20)` gibi). Araştırmadaki olay listesinde, sonraki barı
     >3 saat boşluktan sonra gelen bar (Cuma son barı) olay sayılmaz; aynı koşul uygulanmalı.
   - En az 45 kapanmış bar gerekir.
   - Kayıt: `dens24`, `skip_s1_candidate = dens24 ≥ 2`. **Emir veya atlama kararına girmez.**
3. **S3 (yalnız kayıt):**
   - `fomc_in_window` = planlı FOMC açıklama anı ∈ [giriş, giriş+20 saat).
   - Takvim elle tutulur. 2026'nın kalanı: 10-28 ve 12-09, 14:00 ET.
4. **Hedef yeniden-değerlendirme:** S2 için gölgede ≥30 bayraklı olay (bugünkü sıklıkla yaklaşık 15–20 hafta) birikince
   d'nin işareti ve büyüklüğü yeniden ölçülmeli. S1 için ≥50 S1∧¬S2 olay birikmeli.

### Inferences
- **S2 neden A:**
  - Mekanizması nettir: ralli gününün ertesinde 20 saatlik tepeyi kovalamak.
  - Ex-ante ve sızıntısızdır: önceki UTC günü giriş gününden önce kapanmıştır.
  - Eşiğe duyarsızdır, dört çağda tutarlıdır, plaseboyu geçer.
  - İleride iki beslemede de işaret korunur.
  - Seçim düzeltmesinden geçer.
  - Uyarılar: ileri n=10–13, yani büyüklük belirsiz. Ayrıca R/hafta artışının bir kısmı serbest kalan pozisyon yuvasından
    geliyor. Bu kısım canlıda broker ve Duka besleme farkına duyarlı olabilir; ama iki beslemede de aynı çıktı.
- **S1 neden pratikte B−:**
  - p_sel 0,081, ileride sönen F2 ile aynı düzeyde.
  - Bilgisinin önemli kısmı S2 ile ortak.
  - Kendine özgü kısmı (S1∧¬S2) ileride ters döndü.
  - İşlemlerin %44'ünü atıyor ve büyük boğa yıllarında (2009, 2025) R'yi yarıya indiriyor.
  - Defterin E12/E17 dersi tam bu profili tarif ediyor.
- **S3:** Kuyruk etkisi gerçek ama piyasa geneli: rastgele long FOMC'yi taşıyınca da aynı kuyruk var. Giriş filtresi olamaz.
  Yalnız "FOMC haftasında tutma süresini değiştir" gibi bir çıkış deneyi için gözlem. O deney sınanmadı.

### Gaps
- S2'nin canlı icrada (broker spread'i, kayma) ve swap ile etkisi ölçülmedi. Broker kasasındaki 1m yol ile sabit $0,12
  spread kullanıldı.
- Gölgede ikinci durum makinesinin (filtreli varyant) kodu yazılmadı. Görev kapsamı dışında, dosya değiştirilmedi.
- Kuralın kendisinin seçim sorunu (MK-06: sürüklenme-üstü farkın max-z p_sel'i 0,47, E30) bu çalışmanın konusu değil.
  S2'nin A'sı "kural içinde filtre" düzeyindedir.

### Defter satırı önerileri
(`docs/KAPI_KAYIT_DEFTERI.md` §2.6 MK serisine. Defter bu çalışmada değiştirilmedi. ID'ler öneri: diğer üç notta MK-07…MK-11
çakışarak önerildiği için defter sahibi numaralandırmalı.)

| ID | Tarih | Fikir | Sonuç | Sınıf |
|---|---|---|---|---|
| MK-12 | 2026-10-16 | **R0B_G1 (MK-04) + "önceki UTC günü altın >+%1 ise kırılımı ATLA"** (`research/xau_best_days_20261015/dogrulama/`, ön kayıt PROTOCOL.md 04:31 UTC). Makro notunun 18 özellikten post-hoc bulduğu bayrağın doğrulaması. 105 bayraklık arama ailesi; yıl-içi dairesel kaydırma max-\|z\|; P1-F (yıl × saat × bayrak) DiD; 4 çağ + bir-çağ-hariç; Duka 06-17→09-30 + broker 1m 06-17→10-14; tek-poz filtre yeniden yürütmesi | Duka 2008→2026-06: −0,188 vs +0,117 (d −0,305, z −3,83, **p_sel 0,016**). P1-F DiD −0,213 (P 0,997); rastgele BUY'da yalnız −0,09 → etkinin ~%70'i kırılım-kovalama cezası. 4/4 çağ − (−0,20…−0,39), 17/19 yıl −, eşik %0,75/%1,25'te aynı. İleri: broker d −0,42 (n=10/56), Duka −0,60 (n=13). Filtre: ortR +0,079→+0,110, toplam 290→357R, R/hafta 0,30→0,37, maks DD −59→−49R, en iyi 20 gün payı %62→%50; ileride broker +6,9→+11,8R. S2 işlemlerinin %89'u aynı zamanda seri kırılım | **A** (kural içi filtre; MK-04'ün kendi sınıfı değişmez; gölgede filtreli varyant olarak izle, ≥30 bayraklı olayda yeniden ölç) |
| MK-13 | 2026-10-16 | **R0B_G1 + "son 24 H1'de ≥2 önceki kırılım (seri) ise ATLA"** (aynı çalışma) | d −0,177 (z −3,33, **p_sel 0,081** — ileride sönen F2 ile aynı bölge); DiD −0,123 (P 0,983); 4/4 çağ −; ama ileride iki beslemede TERS (broker +0,37, Duka +0,17), ters dönüş tamamen S1∧¬S2 işlemlerinden (+0,59/+0,41, n=16); S2 dışında etkisi −0,128, S2 içinde −0,031 → bilgisinin önemli kısmı S2. Filtre işlemlerin %44'ünü atıyor, 2009/2025'te R'yi yarıya indiriyor; ileride broker +6,9→+1,1R | **B** (protokol) → uygulamada **C**: filtre değil, gölgede `dens24` kaydı |
| MK-14 | 2026-10-16 | R0B_G1 FOMC açıklamasını tutma penceresinde taşıma → kuyruk | P(R≥3) %14,7 vs %6,9 (z +3,10) ama **p_sel 0,168**; P1-F DiD(P3) −0,003 → rastgele long FOMC'yi taşıyınca aynı kuyruk; ileride 3–4 işlem, R≥3 yok | **RED** (kurala özgü değil) · C (piyasa geneli FOMC kuyruğu, betimsel) |

§1 için önerilen tuzak:

| ID | Tuzak | Bedeli (vaka) | Önlem |
|---|---|---|---|
| E32 | **İç içe geçmiş iki post-hoc bayrak ayrı ayrı "doğrulanmış" sayılır.** Geniş bayrak (seri kırılım, işlemlerin %45'i) dar bayrağın (önceki gün >%1, %12) etkisini büyük ölçüde içinde taşır; geniş bayrağın kendine özgü kısmı ayrı sınanmazsa ölü ağırlık filtreye girer | MK-13: S2'nin %89'u S1 içinde; S1'in S2 dışındaki etkisi −0,13, içindeki −0,03; ileride S1∧¬S2 +0,59R (ters) | her bayrak için 2×2 (A∧¬B, ¬A∧B) raporla; filtre önerisini kendine özgü hücre ileride tutuyorsa ver |
