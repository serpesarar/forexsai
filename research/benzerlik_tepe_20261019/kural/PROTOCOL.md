# ME-10 ön-kayıt — "Dalgalı tepe aralığı" yapısının KURAL tabanlı tanımı ve sonuç testi

> 2026-10-19. **Bu dosya ileri getiri (sonuç) hiç hesaplanmadan yazıldı ve donduruldu.** Bu noktaya kadar yalnız
> `01_sablon_ozellikleri.py` çalıştı: şablonların özellikleri + özelliklerin geliştirme dönemindeki dağılımı
> (`results/01_sablon_ozellikleri.json`, `results/01_stdout.txt`). Kural sıklıkları da henüz hesaplanmadı.
> Paralel araştırmacı aynı yapıyı şablon-şekil benzerliğiyle sınıyor; bu çalışma ondan bağımsız, yorumlanabilir
> özelliklerle bir operasyonelleştirme. Defter kontrolü: ME-02…ME-08 (şekil benzerliği yön/büyüklük taşımıyor),
> GR-01 (düşüş sonrası günlük geri dönüş olgusu), GF-12 / meta-ders 2 ("korku döner, coşku dönmez"); tuzaklar E6, E13,
> E15, E23, E26–E28. Bu çalışma tek NDX geçmişine yapılan ≥ 9. bakış (E23) → DAX bağımsız piyasa zorunlu.

## 1. Veri
- NDX CFD 1h: `research/ndx_gate_forge/data/long_1h_utc.parquet` (2016-05 → 2026-07-14) + `ndx_pattern_motifs/data/bars_15m.parquet`
  1h'e toplanmış uzatma (→ 2026-10-02 04:00) — `research/benzerlik_ornek_20261019/merdiven_test.py::load()`. Zaman damgası UTC bar başı.
  Bilinen etiket kusuru: 2017-11-05 → 2018-02-26 etiketler 60 dk geç (gün ölçekli özellik ve bar-indeksli ufuklarda sızıntı yaratmaz; not edilir).
- DAX 1h: `research/nasdaq_derin_20261013/caprev_dax_recheck/data_fixed/dax_1h.parquet` (eksen düzeltilmiş kopya, brief'teki
  `dax_1h.parquet`'in düzeltilmiş hâli), yalnız 2020-01-01 sonrası.

## 2. Sorgu anı ve özellikler (hepsi ≤ t; `tepe_ozellik.py`)
- Sorgu anı t: NDX → her işlem günü 20:00 UTC'de başlayan barın kapanışı; DAX → 19:00 UTC barı (düzeltilmiş eksen).
- Pencere W = **9 sorgu-günü** (şablon süreleri 10 / 9 / 6 gün → medyan 9): (Q[k−9], Q[k]] barları.
- σ_ref = son 252 sorgu-gününün (t hariç) günlük getirisinden MAD-σ (1,4826 × medyan |r|), ≥ 126 gün şart. Mesafeler σ_ref biriminde
  (`_s`) → 10 yıl ve DAX arasında ölçeksiz.
- `pos` = (kapanış − pencere dibi)/(pencere tepesi − dibi) (high/low); `net_s` = pencere net log getirisi / σ_ref;
  `dist60_s` = (pencere tepesi − son 60 günün tepesi)/σ_ref (≤ 0); `rv_ratio` = pencere 1h getiri std'si / aynı ölçünün son 252
  günlük medyanı; `swings` = kapanışlarda 1×σ_ref dönüşlü zigzag'ın ≥ θ bacak sayısı; `eff` = |net| / Σ|1h getiri|;
  `lh` = ardışık zigzag tepelerinden alçalan tepe sayısı. Zigzag eşiği (1×σ_ref) şablonlara bakılmadan seçildi.

## 3. Şablonlar ve ölçüm (sonuç değil)
- Kullanıcı tarihleri: T1 07-06→07-21, T2 07-17→07-29, T3 08-13→08-20 (2026). **İnceltme (belgelenmiş):** kullanıcı yapıyı
  "düşüşle biten" diye tarif ediyor; T1'in son 5 işlem günündeki en düşük kapanış 07-17 (kullanıcı sonu 07-21 kısmi toparlanmayı
  içeriyor: pos 0,55). Birincil T1 sonu **07-17**; T2 ve T3'te aynı kural kullanıcı sonunu verdi (07-29, 08-20).
- W = 9 sondaki pencerede ölçülen değerler (geliştirme 2016-12→2025-11 yüzdeliği):

| özellik | T1 (07-17) | T2 (07-29) | T3 (08-20) | T1 kullanıcı (07-21) |
|---|---|---|---|---|
| pos | 0,221 [14] | 0,035 [3] | 0,093 [6] | 0,549 [37] |
| net_s | −3,90 [11] | −5,97 [5] | −1,52 [22] | −0,23 [33] |
| dist60_s (≈ %) | −3,02 (−%3,0) [25] | −4,83 (−%5,2) [17] | −1,64 (−%1,7) [34] | −3,02 |
| rv_ratio | 1,12 [61] | 1,59 [84] | 0,74 [20] | 0,92 |
| swings (≥1σ) | 6 [60] | 11 [86] | 3 [26] | 7 |
| eff | 0,101 [64] | 0,128 [75] | 0,064 [42] | 0,007 |
| lh | 1 [70] | 4 [95] | 0 [42] | 2 |

  Okuma (sonuçtan önce): şablonları ortak ayıran tek seçici özellik **"pencerenin dibine düşüşle biten"** (pos, net_s). Oynaklık
  (T3 yıllıklandırılmış %13,8; 10 yılın 32. yüzdeliği), salınım sayısı ve verimlilik medyan civarı — "dalgalı/çalkantılı" izlenim
  2026'nın kendi geçmiş yılına göre ölçüde görünmüyor (T2 hariç). Tepeye yakınlık gevşek (son 60 günün tepesinin %1,7–5,2 altı).

## 4. Kurallar (eşikler şablon değerlerinden, dışa doğru 3 ondalığa yuvarlanmış; DONDURULDU)
- **K1 — gevşek (3 şablon, her özellikte en gevşek şablon değeri):** pos ≤ 0,222 ∧ net_s ≤ −1,524 ∧ dist60_s ≥ −4,827 ∧
  rv_ratio ≥ 0,742 ∧ swings ≥ 3 ∧ eff ≤ 0,129. (Üç şablon sonunda da yanar — yapı gereği.)
- **K2 — çalkantı-vurgulu (T1+T2; kullanıcının "oynak, derin geri çekilmeli, alçalan tepeli" tarifi):** pos ≤ 0,222 ∧
  net_s ≤ −3,901 ∧ dist60_s ≥ −4,827 ∧ rv_ratio ≥ 1,115 ∧ swings ≥ 6 ∧ eff ≤ 0,129 ∧ lh ≥ 1. (T3'te yanmaz — belgelenir.)
- **K3 — tepe-şartsız kontrol:** K1 eksi dist60_s (yakın-tepe koşulu yok). K1 ⊂ K3; "tepeye yakınlık" bir şey katıyor mu?
- Aile dışı duyarlılık (yalnız tanımlayıcı): K1-lit (T1 sonu kullanıcının 07-21'i: pos ≤ 0,549, net_s ≤ −0,225), W = 6 ve 12'de aynı
  yöntemle yeniden türetilmiş K1.

## 5. Olaylar (sızıntısız; her olay t'de bilinir)
- Yanan gün: kural t'de doğru. **Bölüm (epizod):** ardışık yanan günler arası ≤ 10 sorgu-günü ise aynı bölüm.
- **(a) Oluşum:** her bölümün ilk yanan günü.
- **(b) Tamamlanma:** kural t−2 ve t−1'de doğru, t'de yanlış (≥ 2 gün sürmüş düşüş bacağı bitti) → tamamlanma sinyali; sinyaller
  aynı ≤ 10 gün kuralıyla kümelenir, her kümenin İLK sinyali olaydır.
- Olay = bölüm başına 1 → olay düzeyi = bölüm düzeyi (E6). Ek tanımlayıcı: tüm yanan günler (gün düzeyi, E6 uyarılı).

## 6. Sonuç ve kıyaslar
- Getiri r_h = log(c[t+h]) − log(c[t]); NDX h = 1 bar (+1 s), 24 bar (+1 g), 120 bar (+5 g). DAX: 1 bar, sonraki sorgu günü,
  5 sorgu günü sonrası (DAX'ta günde ~20 bar olduğu için bar yerine gün).
- (i) **Koşulsuz:** aynı dönemdeki tüm geçerli sorgu günlerinin ortalaması.
- (ii) **Getiri+oynaklık eşli (asıl kıyas):** geliştirme günlerinden 10 × 10 hücre = sondaki 9 günlük log getiri ondalığı ×
  sondaki 9 günlük 1h-getiri std ondalığı. Kontrol havuzu: kural t, t−1, t−2'de yanmayan geliştirme günleri. Hücrede < 10 kontrol
  varsa aynı oynaklık ondalığında getiri ondalığı ±1, ±2… genişletilir. Fark = r − hücre ortalaması.
- (iii) **Plasebo:** olay göstergesinin geliştirme sorgu-günü dizisinde dairesel kaydırılması (k ∈ [60, N−60], 2.000 tekrar),
  aynı eşli fark; gerçek ortalamanın plasebo dağılımındaki yüzdeliği.
- Belirsizlik: olay farkları üzerinde **takvim-ayı blok bootstrap** B = 10.000 (ME-08 `mboot`).
- Olay düzeyi raporu: olay sayısı, ortalama/medyan fark, negatif fark payı, ham getirinin negatif payı, en kötü (en negatif) olay
  hariç ve en iyi olay hariç ortalama.
- Yarılar: 2016–2020 / 2021-01 → 2025-11 (DAX: 2020-07→2022-12 / 2023-01→2025-11).

## 7. Dönemler
- Geliştirme: sonucu (t + h) 2025-11-30 23:00 UTC'yi geçmeyen sorgular (özellik geçerliliği ~2016-12'den).
- Doğrulama (bir kez): 2025-12-01 → veri sonu; pencere ∪ ufku şablon aralığıyla (2026-07-06 → 2026-08-20) çakışan sorgular hariç.
  Taban = geliştirme hücre ortalamaları; güç MDE₈₀ = 2,80 × sd(geliştirme farkları)/√n raporlanır.
- DAX: aynı eşikler, aynı tanımlar (σ-birimli, ölçeksiz); geliştirme 2020-07 → 2025-11, doğrulama 2025-12 →.

## 8. Başarı ölçütü (ön-kayıtlı)
- **H1 (birincil, "tepe → aşağı devam"):** fark < 0. **H2 (ikincil, ters: "korku döner", meta-ders 2 / GR-01):** fark > 0.
- Bir hücre (kural × olay × ufuk; NDX geliştirme; aile = 3 × 2 × 3 = 18 hücre, iki yön) **geçer**: (1) eşli fark ilgili yönde,
  ay-blok P ≥ 0,975; (2) iki yarıda da aynı işaret; (3) ≥ 20 bağımsız olay; (4) olay düzeyi: medyan fark aynı işaret, aynı işaretli
  fark payı ≥ %50, uç olay (o yöndeki en büyük) hariç ortalama aynı işaret.
- **Güçlü:** + P ≥ 0,99861 (Bonferroni: 18 hücre, iki yönlü α 0,05) + plasebo yüzdeliği ≤ %5 (H1) / ≥ %95 (H2) + DAX'ta aynı işaret ve
  P ≥ 0,95.
- E26/E28: her iki yönde P ≥ 0,975 olan hücre sayıları birlikte raporlanır; anlamlı kötü hücre ters sinyal sayılmaz.
- Hiçbir hücre geçmezse sınıf X (tahmin); dedektör tanımlayıcı olarak kalabilir.

## 9. Ek tanımlayıcılar
- Her kuralın yanma payı (gün %), yılda bölüm sayısı; şablonlarda yanıyor mu; Haziran–Eylül 2026'da yanan günler.
- Bölüm içi yol: oluşumdan tamamlanmaya getiri ve süre.
- **Bugün:** son sorgu günü (2026-10-01 20:00 UTC) ve son bar (2026-10-02 04:00 UTC) için kural durumu + özellikler (NDX ve DAX).
