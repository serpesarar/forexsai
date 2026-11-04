# BTC scalping — Aile ML: tüm faktörleri birleştiren sızıntısız çok-faktörlü model (fam_ml)

Kapsam: 2026-10-22. Yerel veriden nicel sınama: yeni indirme yok, kutuya/Supabase'e dokunulmadı, commit yok. Yalnız
`research/btc_scalp_20261021/fam_ml/` altına yazıldı.
Python: `/Users/melihcanodacioglu/Desktop/panel/.venv/bin/python -I` (numpy 2.4.6, pandas 2.3.3, sklearn 1.5.0, LightGBM 4.3.0).
Veri: `data/btc_scalp_1m.parquet`, 2021-06-01 → 2026-10-20, 2.833.920 dakika. **Alt-örnekleme yapılmadı.**
Karar ızgarası 5 dakikada bir: 566.771 karar, H=30'da 552.625, H=60'ta 540.757 geçerli.

Ön kayıt: [fam_ml/prereg.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/prereg.md).
Hiçbir sonuç görülmeden yazıldı. EK-1 yalnız uygulama netleştirmeleri içeriyor (saatlik eşik yenileme, Plasebo B için
dairesel kaydırma, ablation set tanımı, T4 notu) ve o da model sonuçlarından önce eklendi.

Betikler, sırasıyla:
- `feat.py`: 120 nedensel özellik ve rollover takvimi
- `labels.py`: etiket motoru
- `01_build.py`: veri seti kurulumu
- `02_selftest.py` + `02b_t4_recheck.py`: öz-sınamalar
- `mlcore.py` + `03_train.py`: iç CV, dondurma, final modeller
- `04_eval.py`: kart, plasebo A, Holm, kalibrasyon
- `05_extra.py`: sızıntı T5, Plasebo B, ablation, TreeSHAP
- `06_diag.py`: **post-hoc** teşhis (ön kayıtta yok, verdikti değiştirmez)

Sonuçlar `fam_ml/results/`, günlükler `fam_ml/logs/`.

Tasarım özeti:
- Giriş, sonraki 1m açılışında (spot). SL = max(19 bp, 1,1×ATR14(5m)), TP = SL×{1; 1,5}, zaman stopu H ∈ {30, 60} dk.
- Aynı barda TP+SL → SL. SL dolumu boşluk-duyarlı. Net R'ye 1,85 bp maliyet ve SL çıkışlarında 1 bp kayma eklendi.
- Zorunlu kapanış rollover'dan 2 dk önce (20:58/21:58 UTC). Tutuşu bu saati aşacak işlem açılmaz.
- 8 hücre: yön {L, S} × TP {1; 1,5} × H {30, 60}. Her hücre için ayrı LightGBM regresyonu, hedef net R.
- Dönemler: DISC 2021-06→2023-12 · OOS 2024-01-11→2025-06-30 · BLIND 2025-07-01→2026-10-20.
- Seçim kuralı: son 30 günün eğitim-dışı tahminlerinin üst k%'sı (saatlik yenilenir, 7 gün ısınma).
  Yapılandırma ve k yalnız DISC iç-CV'sinde seçildi (4 genişleyen fold, 1 gün ambargo).
- Sonra model DISC üzerinde eğitildi ve OOS'a tek seferde uygulandı. Ardından DISC+OOS ile aynı yapılandırmayla yeniden
  eğitilip BLIND'a tek seferde uygulandı.

---

## Sızıntı öz-sınamaları: harness geçerli mi?

### Takeaway
**Öz-sınamaların hepsi GEÇTİ; sonuçlar geçerli.**
- Sızıntı sınamaları T1 (önek), T2 (giriş barı bozma), T3 (kaynak nedenselliği) ilk koşuda sıfır uyuşmazlıkla geçti.
- `02_selftest.log` sonundaki "TÜM ÖZ-SINAMALAR: DÜŞTÜ" satırı yalnız T4'ten geliyor. T4 bir sızıntı sınaması değil,
  etiket motorunun doğruluk sınaması. L_tp1_h60'taki 2/3.000 uyuşmazlık, döngü referansının SL mesafesini parquet'ten
  **float32** okumasından kaynaklanan tam-eşitlik yuvarlama farkı. Aynı motor float64 SL ile 8 hücrenin hepsinde 0/24.000
  uyuşmazlık verdi.
- Kasıtlı sızıntı sınaması (T5) sızıntıyı çok net yakaladı. Harness gelecek bilgisini görebiliyor; gerçek modelde böyle
  bir patlama yok.

### Cited Findings
- **T1 önek testi:** veri 5 rastgele dakikada kesildi (538.515, 552.287, 1.514.558, 1.753.509, 2.298.649). Kesime kadar
  olan her satırdaki 120 özellik birebir aynı çıktı, uyuşmazlık 0 — [selftest.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/results/selftest.json)
- **T2 giriş barı bozma testi:** kesimden sonraki tüm sayısal sütunlar (giriş barı dahil) ×1,37 + gürültüyle bozuldu.
  Kesime kadar 0 uyuşmazlık. Kesimden sonraki ilk 2.000 satırda ~202–206 bin hücre değişti, yani test duyarlı — aynı dosya
- **T3 kaynak nedenselliği:** `metrics_eff_ts > ts` 0, `funding_last_time > ts+1m` 0, `bd_snap_age_s < 0` 0. 2024-03-04
  metrics damga değişimi upstream'de `eff_ts` ile çözülmüş durumda ([02_orderflow_turev_veri.md](file:///Users/melihcanodacioglu/Desktop/panel/research_notes/BTC%20scalping%20strateji%20ara%C5%9Ft%C4%B1rmas%C4%B1/02_orderflow_turev_veri.md)) — aynı dosya
- **T4 etiket motoru:**
  - İlk koşu: 7 hücre 0/3.000, L_tp1_h60 2/3.000.
  - Teşhis: döngü float64 `s` ile koşunca 21.631 kararda 0 uyuşmazlık.
  - Yeniden üretilebilir sınama `02b_t4_recheck.py`: 8 hücre × 3.000, float64 0 uyuşmazlık, "T4 float64: GEÇTİ" — [selftest_t4_float64.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/results/selftest_t4_float64.json), [02b_t4.log](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/logs/02b_t4.log)
- **T5 kasıtlı sızıntı:** gelecek 15 dk getirisi + N(0, k·σ) gürültüsü özellik olarak eklendi; aynı yapılandırma/k, DISC→OOS — [extra_leak.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/results/extra_leak.json)

  | hücre | gürültü | OOS AUC | OOS ort R (top 1%) | gerçek model ort R / AUC |
  |---|---|---|---|---|
  | L_tp1.5_h60 | 1σ | 0,698 | **+1,198** | +0,082 / 0,513 |
  | L_tp1.5_h60 | 3σ | 0,580 | +0,614 | |
  | S_tp1_h30 | 1σ | 0,712 | **+0,819** | +0,051 / 0,521 |
  | S_tp1_h30 | 3σ | 0,587 | +0,442 | |

### Inferences
- Gerçek modelin OOS AUC'si 0,51–0,52. Bu, sızıntı imzasından (0,58–0,71) çok uzak ve bilinen BTC kısa-ufuk öngörü
  düzeyiyle tutarlı. Önceki projelerdeki sızıntı tipleri (E1 ileri bakan bar, E16 sol-etiket resample) burada yapısal
  olarak yok, çünkü tüm pencereler 1m ızgarada m'de bitiyor ve T1/T2 bunu doğruluyor.
- Etiketler yalnız ileriye bakıyor ve özelliklerle aynı satırda tutuluyor. Örtüşen etiketler (5 dk ızgara, 30/60 dk ufuk)
  için iç CV'de ≥1 gün ambargo, OOS'ta 10 gün boşluk, BLIND yeniden-fitinde son 1 gün arınma uygulandı.

### Gaps
- Upstream birleştirmenin (`07_assemble.py`) canlı yayın gecikmesi (metrics +1 dk pay) gerçek canlı akışla ölçülmedi;
  bu yalnız yerel varsayım.
- Önek testi özellik kodunu sınıyor. Upstream parquet'in kendi nedenselliği T3 ve `08_validate.py` ile sınandı.

---

## Çok-faktörlü model maliyet sonrası kârlı scalp seçebiliyor mu? (kart, plaseboler, BLIND)

### Takeaway
**Hayır. 8 hücrenin 8'i de ön-kayda göre RED.** En iyi kart 5/6.
- Ölçüt 5 (iyimser−gerçekçi farkı ≤ ½|ortR|) her hücrede düşüyor. Bu, kenarın maliyetin iki katına bile ulaşmadığı
  anlamına geliyor (E44).
- Holm p ≥ 0,16. BLIND işareti 8 hücrenin 5'inde negatif.
- Öncelikli hücre (iç-CV'nin en iyisi) L_tp1.5_h60:
  - OOS: +0,082R (2,17 bp), P(EV>0) %93,6, kart 5/6.
  - BLIND: **+0,012R**, P %58,7, kart 3/6. 2026'da −0,017R.
- Model gerçek ama küçük bir yön bilgisi taşıyor: seçilen işlemler rastgele girişi ve etiketi kaydırılmış modellerin
  hepsini yeniyor. Ancak bu bilgi brüt ~2–5 bp/işlem. 1,85 bp spread ve ~0,5 bp ortalama stop kaymasından sonra ≈0 kalıyor.

### Cited Findings
Dondurulmuş seçim (iç-CV): her hücrede k=%1 seçildi, yani ~3,2 işlem/gün/hücre. Yapılandırmalar:
L_tp1_h30 C4 · L_tp1_h60 C1 · L_tp1.5_h30 C1 · L_tp1.5_h60 C1 · S_tp1_h30 C3 · S_tp1_h60 C4 · S_tp1.5_h30 C3 · S_tp1.5_h60 C3 —
[frozen_spec.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/results/frozen_spec.json), [innercv.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/results/innercv.csv)

Ana tablo (PEP 1,85 bp + 1 bp SL kayması; "taban" = aynı segmentte filtresiz tüm geçerli kararlar) —
[cells_summary.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/results/cells_summary.csv), [eval.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/results/eval.json):

| hücre | iç-CV ortR | OOS n / ortR / net bp / P | OOS yarılar | OOS stres | OOS tek-poz (n / R) | OOS kart | BLIND n / ortR / net bp / P | BLIND kart | taban OOS / BLIND |
|---|---|---|---|---|---|---|---|---|---|
| L_tp1_h30 | +0,021 | 1691 / −0,005 / +0,21 / 0,44 | +0,060 / −0,070 | −0,037 | 947 / −0,018 | 1 | 1505 / −0,013 / +0,20 / 0,35 | 2 | −0,100 / −0,114 |
| L_tp1_h60 | +0,035 | 1757 / +0,049 / +1,38 / 0,87 | +0,072 / +0,026 | +0,018 | 845 / −0,009 | 3 | 1436 / +0,003 / −0,10 / 0,52 | 2 | −0,107 / −0,122 |
| L_tp1.5_h30 | +0,019 | 1744 / +0,019 / +0,53 / 0,68 | +0,075 / −0,038 | −0,014 | 819 / +0,050 | 2 | 1476 / −0,049 / −0,18 / 0,12 | 1 | −0,092 / −0,109 |
| **L_tp1.5_h60** | **+0,069** | 1754 / **+0,082** / +2,17 / **0,936** | +0,122 / +0,041 | +0,048 | 654 / +0,052 | **5** | 1493 / **+0,012** / +1,36 / 0,59 | 3 | −0,097 / −0,122 |
| S_tp1_h30 | +0,056 | 1752 / +0,051 / +2,76 / 0,943 | +0,024 / +0,079 | +0,017 | 1040 / +0,031 | 5 | 1488 / −0,025 / −0,67 / 0,22 | 1 | −0,099 / −0,092 |
| S_tp1_h60 | +0,056 | 1781 / +0,024 / +2,94 / 0,74 | −0,006 / +0,054 | −0,009 | 821 / +0,031 | 2 | 1655 / −0,038 / −0,39 / 0,18 | 2 | −0,100 / −0,094 |
| S_tp1.5_h30 | +0,031 | 1664 / +0,077 / +4,47 / **0,980** | +0,088 / +0,065 | +0,043 | 855 / +0,070 | 5 | 1482 / −0,056 / −1,33 / 0,09 | 1 | −0,095 / −0,085 |
| S_tp1.5_h60 | +0,042 | 1647 / +0,057 / +3,21 / 0,89 | +0,061 / +0,054 | +0,021 | 688 / +0,068 | 4 | 1562 / −0,072 / −1,71 / 0,08 | 1 | −0,099 / −0,085 |

Kart ölçüt 5 (icra farkı) her hücrede ✗:
- OOS iyimser ortR ile gerçekçi arasındaki fark 0,076–0,093R. Bu fark tam olarak maliyet/R (≈ (1,85 + ~0,5 kayma) / ~33 bp).
- Ortalama R'nin yarısı ise ≤0,041.

Ek ölçütler (OOS, `eval.json` + [placeboB_summary.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/results/placeboB_summary.json)):

| hücre | Plasebo A (yıl×saat, 500 çekiliş) yüzdelik; plasebo ort | Plasebo B (etiketi kaydırılmış modeller): null ort / maks; null AUC | Holm p | BLIND işaret | ön-kayıt verdikti |
|---|---|---|---|---|---|
| L_tp1_h30 | %100; −0,094 | −0,075 / −0,052 (3 model); 0,503 | 0,775 | − | RED |
| L_tp1_h60 | %100; −0,105 | −0,107 / −0,044 (10); 0,499 | 0,535 | + | RED |
| L_tp1.5_h30 | %100; −0,087 | −0,075 / −0,002; 0,500 | 0,775 | − | RED |
| L_tp1.5_h60 | %100; −0,094 | −0,090 / −0,014; 0,499 | 0,402 | + | RED (kart 5/6) |
| S_tp1_h30 | %100; −0,097 | −0,100 / −0,060; 0,502 | 0,402 | − | RED (kart 5/6) |
| S_tp1_h60 | %100; −0,094 | −0,112 / −0,053; 0,500 | 0,775 | − | RED |
| S_tp1.5_h30 | %100; −0,089 | −0,086 / −0,026; 0,502 | 0,160 | − | RED (kart 5/6) |
| S_tp1.5_h60 | %100; −0,093 | −0,095 / −0,049; 0,499 | 0,535 | − | RED |

Yıl bazında (ortR / net bp):
- L_tp1.5_h60: OOS 2024 +0,096 / +2,14 (n 1.158), 2025 +0,054 / +2,22 (596). BLIND 2025-H2 +0,064 / +2,54 (544), **2026 −0,017 / +0,68** (949).
- S_tp1_h30: OOS 2024 +0,047, 2025 +0,060. BLIND 2025-H2 −0,016, 2026 −0,032 / −1,29 bp.
- S_tp1.5_h30: BLIND 2026 −0,119 / −3,82 bp.
- Kısa hücrelerin hepsi 2026'da negatif — `eval.json` `by_year`

Maliyet senaryoları (OOS ortR):
- PEP_FIX15 (15 $ sabit, 2024-25 ≈ 1,5–2,3 bp): −0,013…+0,071.
- BIN_MAKER (4 bp): −0,080…+0,003.
- **BIN_TAKER (10 bp): −0,215…−0,289, her hücrede**.
- BLIND'da BIN_MAKER ve BIN_TAKER her hücrede negatif — `cells_summary.csv`

Diğer ölçümler:
- Aynı-bar TP+SL oranı seçilen işlemlerde %0–0,19. Ön kayıttaki ≤%0,5 sınırının altında, yani 1m çözünürlük bu braket için yeterli.
- Kazanma oranı %44–56; tek başına anlamsız (E14).
- Mutlak eşik "tahmin > 0" (ikincil): OOS her hücrede −0,038…−0,066R; BLIND −0,017…−0,065R.
- Sabit ondalık eşik: üst ondalık OOS'ta −0,008…−0,060R. Pozitif kalan yalnız kayan üst %1 — `eval.json` (`abs_thr0`, `top_decile_mean_r`)
- k duyarlılığı (OOS): k=%2'de 8 hücrenin 4'ü negatif, k=%5–10'da neredeyse hepsi negatif. Kenar yalnız dağılımın uç
  kuyruğunda — [k_sensitivity.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/results/k_sensitivity.csv)

**Post-hoc teşhis** ([diag_posthoc.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/results/diag_posthoc.json); ön kayıtta yok, yalnız yorum için):
- Seçim yüksek oynaklık anlarına kayıyor.
  - Seçilenlerin SL'i ort. 30–40 bp, havuzun 22–25 bp.
  - 19 bp tabanının bağladığı işlem payı: seçilenlerde %16–56, havuzda %57–70.
- Yıl×saat×s_bp-ondalığı ile **oynaklığa eşlenmiş plasebo** ve **maliyetsiz brüt R** ile bakınca:

  | hücre | seg | brüt R seçilen | eşlenik plasebo brüt R (yüzdelik) | aynı anlarda ters yön brüt R | brüt bp seçilen |
  |---|---|---|---|---|---|
  | L_tp1.5_h60 | OOS | +0,165 | +0,007 (%100) | −0,122 | +4,48 |
  | L_tp1.5_h60 | BLIND | +0,091 | −0,004 (%100) | −0,085 | +3,67 |
  | L_tp1_h60 | BLIND | +0,074 | −0,009 (%100) | −0,075 | +2,13 |
  | S_tp1_h30 | OOS | +0,134 | −0,002 (%100) | −0,134 | +4,94 |
  | S_tp1_h30 | BLIND | +0,068 | +0,018 (%98,8) | −0,068 | +1,51 |
  | S_tp1.5_h60 | BLIND | +0,032 | +0,033 (%46) | −0,026 | +0,60 |

### Inferences
- **Sinyal gerçek.** Etiketi kaydırılmış modellerin hepsi 8/8 hücrede gerçek modelin altında; eşlenik plasebo brüt R'si ≈0.
  Aynı anlarda ters yön simetrik olarak kaybediyor, yani bilgi oynaklık seçimi değil **yön bilgisi**.
- **Sinyal küçük ve maliyete yeniliyor.** Brüt kenar OOS'ta +0,07…+0,17R (≈2–7 bp). Not 03'ün çıtası (brüt ≥ ~0,15R ve
  maliyet/R ≤ %10) ancak OOS'taki en iyi hücrelerde sınırda tutuyor; BLIND'da brüt +0,03…+0,09R'ye iniyor.
- **Uzun taraf kısmen dayanıklı, kısa taraf çöktü.** Kısa hücrelerin BLIND/2026'daki çöküşü, yön bilgisinin rejime bağlı
  olduğunu gösteriyor (§3 meta-ders: "coşku dönmez" türü asimetriler dönemlere taşınmayabilir). Uzun taraf BLIND'da brüt
  +0,02…+0,09R'de kaldı (4 hücrenin 3'ünde eşlenik plaseboda ≥%99,8; L_tp1.5_h30 +0,023, %71) ama net ≈0.
- **Plasebo A ve B burada ayırt edici değil.** Rastgele girişin tabanı −maliyet/R (≈ −0,10R). Herhangi bir küçük bilgi
  bu plaseboyu %100'de geçer. Bağlayıcı sınama mutlak net R ve BLIND (yeni tuzak E51).
- Kart sonucu E44 ile birebir: bp düzeyindeki kurallarda ölçüt 5 fiilen "net ≥ 2×maliyet" demek ve hiçbir hücre buna yaklaşmıyor.

### Gaps
- Broker M1 (Pepperstone, 16 gün) ile teyit yapılmadı (E47). 16 gün × ~3 işlem/gün istatistik vermez. Broker'ın 2,3 kat
  geniş bar-içi aralığı 30–40 bp SL'de sonucu ≤0,015R kötüleştirir (not 03 §3).
- Gerçek CFD spread'i yüksek oynaklık anlarında genişler (p90 ~42 $ ≈ 5 bp). Model tam bu anları seçtiği için gerçek maliyet
  1,85 bp'den büyük olabilir. Bu, sonucu daha da kötüleştirir.

---

## Model ne öğrendi: kalibrasyon, AUC, sıralama gücü

### Takeaway
Sıralama gücü zayıf ama tutarlı: OOS AUC 0,513–0,522, Spearman 0,04–0,12. Null modellerde AUC ≈0,50.
Kalibrasyon kötü: tahminler aşırı yayılmış ve iyimser. En üst ondalığın tahmini +0,10R iken gerçekleşen −0,06R. Sıralama
monoton olduğu için yalnız kayan uç-kuyruk seçimi (üst %1) çalışıyor.

### Cited Findings
- AUC (net R > 0): OOS 0,513–0,522, BLIND 0,516–0,525, iç-CV 0,520–0,533. TP-önce AUC'si 0,504–0,525 — `cells_summary.csv`
- Kalibrasyon, L_tp1.5_h60 OOS (tahmin / gerçekleşen, ondalıklar): −0,295/−0,168 … −0,022/−0,098, +0,017/−0,076, **+0,100/−0,060**.
  S_tp1_h30 OOS en üst ondalık +0,139/−0,021 — [calibration.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/results/calibration.csv)
- İç-CV Spearman yapılandırmalar arasında çok az değişiyor (0,057–0,099), ama üst %1'in ortR'si yapılandırmaya göre işaret
  değiştiriyor. Örnek L_tp1_h30: C1 −0,022 / C4 +0,021. Seçim gürültülü — `innercv.csv`

### Inferences
- Mutlak tahmin değeri ("beklenen R > 0") kullanılamaz. Canlı kural ancak göreli (kayan nicel) olabilir.
- Kenar uç kuyrukta yoğunlaşıyor (k=%1). İşlem sayısı artınca kenar maliyetin altına düşüyor; kapasite yok.

### Gaps
- Olasılık kalibrasyonu (izotonik) denenmedi. Ön kayıtta yoktu ve seçim kuralı göreli olduğu için sonucu değiştirmez.

---

## Hangi faktörler önemli ve birlikte çalışıyor? (TreeSHAP, ablation, seçilen-işlem profili)

### Takeaway
Bilginin çoğu **türev konumlanmasından** (top-trader/global L/S oranları ve 24 s değişimleri, funding tahmini) ve **defter
derinliği dengesizliğinden** (±%5) geliyor. Bunlar yüksek aktivite/oynaklık rejimiyle birlikte çalışıyor. Yalnız fiyat
özellikleri OOS'ta negatif sonuç veriyor.
- Ablation'da her grup ortalamada küçük bir artış ekliyor:
  - A0 yalnız fiyat: −0,061R
  - A1 +takvim: +0,002
  - A2 +akış: +0,010
  - A3 +türev: +0,026
  - tam (+derinlik): **+0,044R** (8 hücre ortalaması, OOS)
- Ancak hücre bazında farklar gürültü düzeyinde (±0,05R) ve sıralama tutarlı değil.

### Cited Findings
- **TreeSHAP grup ortalaması |katkı|** (OOS 40 bin örnek, model-1). Her hücrede DERIV birinci, PRICE ikinci, DEPTH ≈ FLOW, CAL en küçük.
  Örnek L_tp1.5_h60: DERIV 0,184 · PRICE 0,097 · DEPTH 0,056 · FLOW 0,043 · CAL 0,022 — [extra_shap.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/results/extra_shap.json)
- **En önemli özellikler** (çoğu hücrede ilk 6, sıra hücreye göre değişiyor): `bd_imb_5`, `ls_top_pos`, `ls_global`,
  `ls_global_chg24`, `ls_top_pos_chg24`, `funding_pred_bp`. Sonra `vwapd_dist_atr`, `rangepos_60`, `vol_60/240`,
  `min_to_funding`, `oichg_240`, `bd_depth1_log`, `prem_z24` — aynı dosya
- **Ablation** (aynı yapılandırma/k, DISC→OOS, ortR) — [extra_ablation.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/results/extra_ablation.json):

  | hücre | A0 PRICE | A1 +CAL | A2 +FLOW | A3 +DERIV | A3b PRICE+CAL+DERIV | tam |
  |---|---|---|---|---|---|---|
  | L_tp1_h30 | −0,033 | −0,000 | +0,018 | −0,000 | +0,014 | −0,005 |
  | L_tp1_h60 | −0,072 | −0,003 | +0,001 | −0,004 | −0,017 | +0,049 |
  | L_tp1.5_h30 | −0,064 | −0,009 | +0,023 | +0,066 | −0,029 | +0,019 |
  | L_tp1.5_h60 | −0,027 | +0,009 | +0,096 | +0,059 | −0,016 | +0,082 |
  | S_tp1_h30 | −0,079 | −0,031 | −0,026 | +0,001 | +0,063 | +0,051 |
  | S_tp1_h60 | −0,028 | +0,051 | +0,044 | +0,056 | +0,109 | +0,024 |
  | S_tp1.5_h30 | −0,108 | −0,022 | −0,024 | −0,025 | +0,066 | +0,077 |
  | S_tp1.5_h60 | −0,077 | +0,018 | −0,051 | +0,056 | +0,056 | +0,057 |
  | **ortalama** | **−0,061** | +0,002 | +0,010 | +0,026 | +0,031 | **+0,044** |

  AUC tüm setlerde 0,507–0,521. Fark sıralama gücünden çok uç kuyruğun içeriğinden geliyor.
- **Seçilen-işlem profili** (seçilen − havuz, havuz std'si biriminde, hücre ortalaması) — [selected_profile.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/fam_ml/results/selected_profile.csv):
  - **Long seçimleri (OOS):**
    - yüksek aktivite: hacim z (`pvolz_60` +0,98, `svolz_60` +1,01), işlem sayısı z +0,95, ATR/oynaklık +0,8…+0,9
    - 24 s'de düşen L/S oranları: `ls_top_acc_chg24` −0,80, `ls_top_pos_chg24` −0,78, `ls_global_chg24` −0,70
    - daha düşük funding tahmini: `funding_pred_bp` −0,49
    - kısa vadeli düşüş: `ret_5`/`ret_15` −0,40, `rangepos_60` −0,37
    - BLIND'da ayrıca spot satış akışı (`scvd_60` −0,99) ve `ret_60` −0,61.
  - **Short seçimleri (OOS):**
    - satış tarafı ağır defter: `bd_imb_5` −0,89, `bd_imb_2` −0,82, `bd_imb_1` −0,77
    - yükselen top-trader pozisyon oranı: `ls_top_pos_chg24` +0,73
    - yüksek funding tahmini: +0,71
    - yüksek aktivite (+0,6…+0,86), hafta içi (`weekend` −0,33).
- **SHAP üst %5 itişleri:**
  - Long'da `ls_global`, `ls_top_pos`, `funding_pred_bp`, `bd_imb_5`, `pcvd_240` birlikte.
  - Short'ta `bd_imb_5`, `funding_pred_bp`, `bd_imb_2`, `basis_mark_index_bp`, `ls_top_pos_chg24` birlikte — `extra_shap.json`

### Inferences
- Birlikte çalışan örüntü **"kalabalık konumlanmasının tersine, yüksek aktivitede"**:
  - **long:** kalabalık ve top-trader'lar son 24 saatte long azaltmış (L/S düşüyor), funding tahmini düşük, fiyat kısa
    vadede düşmüş ve spot satıyor, aktivite yüksek → kısa ufuklu dönüş alımı. "Korku döner" ile uyumlu.
  - **short:** top-trader pozisyon oranı yükselmiş, funding tahmini yüksek (kalabalık long), satış tarafında derinlik ağır,
    aktivite yüksek → kısa ufuklu düşüş.
- Kısa taraf BLIND'da (2026) çöktü. Defter dengesizliği DISC'te yalnız 2023'te vardı (2021–22 NaN). Bu yüzden derinlik
  bilgisinin dönemler arası kararlılığı zayıf kanıtlı.
- Literatür haritasında (not 01 §6) OI/funding/L/S için "kısa ufuk kanıtı yok" yazıyor. Bu çalışma küçük bir **brüt** bilgi
  buluyor (≈2–5 bp, AUC ~0,52). Ama maliyet sonrası işlem kenarı yok. Literatürdeki "sub-bp ile birkaç bp" ölçeği ve
  ücret-sonrası kârlılığın gösterilmemiş olmasıyla tutarlı.
- Takvim (A0→A1) R'yi her hücrede iyileştiriyor. Bu muhtemelen yön değil, **maliyet/R ve zaman-çıkışı** etkisi: saat ve
  rollover'a kalan süre oynaklık rejimini temsil ediyor (not 03 §2: saat yalnız maliyet/hız filtresidir).

### Gaps
- Bağımsız çiftli etkileşim ölçümü (SHAP interaction values) LightGBM'de yok; `shap` paketi kurulu değil. "Birlikte
  çalışma" seçilen-işlem profili, üst %5 SHAP itişleri ve ablation ile çıkarıldı.
- aggTrades 1 sn özellikleri (2026-04+) ve ±%0,2 derinlik (2026-01+) DISC'te olmadığı için kullanılmadı.

---

## En iyi aday(lar)

**Canlıya alma kartını geçen aday YOK. GÖLGE adayı da yok** (ön kayıt: kart < 6/6 → RED). Bu hattın çıktısı bir strateji
değil, yalnız "gerçek ama maliyete yenilen yön bilgisi" bulgusu.

Kayıt için en yakın hücre, **dondurulmuş tanımıyla**:
- **Hücre:** L_tp1.5_h60 (BTCUSD long). Karar her 5 dk sınırında. Giriş sonraki 1m açılışı.
- **Geometri:** SL = max(19 bp, 1,1×ATR14(5m)), TP = 1,5×SL, zaman stopu 60 dk. Rollover'ı (yaz 21:00 / kış 22:00 UTC)
  aşacak işlem açılmaz.
- **Model:** LightGBM regresyon, hedef net R (1,85 bp + 1 bp SL kayması). Yapılandırma C1: num_leaves 15,
  min_data_in_leaf 1000, 300 ağaç, lr 0,03, colsample 0,7, subsample 0,7 (freq 1), lambda_l2 10, seed 7.
  Eğitim DISC (OOS sınaması için) veya DISC+OOS (BLIND için).
- **Özellik listesi:** `frozen_spec.json` → `features` (120 özellik):
  - PRICE 41: getiriler ve σ-normalize getiriler 1–1440 dk, oynaklık 15–1440 dk, ATR1/ATR5, s_bp, aralık konumu, VWAP
    uzaklıkları, sıkışma, 5m bar şekli, RV24
  - FLOW 22: perp/spot taker dengesizliği 1–60 dk, CVD, hacim/işlem z, işlem büyüklüğü, spot/perp hacim oranı
  - DERIV 44: OI değişimleri ve OI×fiyat çeyreği, funding seviye/z/tahmin, funding'e kalan dakika, premium/baz z, L/S
    oranları ve 24 s değişimleri + eksiklik göstergeleri, tasfiye vekilleri, metrics yaşı
  - DEPTH 8: bd_imb_1/2/5 vb.
  - CAL 5: saat, gün, hafta sonu, saat-içi dakika, kapanışa kalan dakika
  - Model dosyaları `fam_ml/cache/models/L_tp1.5_h60_m1.txt` ve `_m2.txt`.
- **Eşik:** saatlik yenilenen, son 30 günün eğitim-dışı tahminlerinin üst %1'i (k=0,01), ≥7 gün ısınma.
- **Beklenen işlem/gün:** ~3,3 (tek pozisyon zincirinde ~1,2–1,3: OOS 654 işlem / 537 gün, BLIND 609 / 477 gün).
- **Sonuç:** OOS +0,082R (+2,2 bp, P %93,6, kart 5/6) → BLIND +0,012R (P %59, kart 3/6), 2026'da −0,017R. Plasebo A ve B
  geçiyor; Holm 0,40 ve ölçüt 5 düşüyor. **RED.**

Pratik öneri:
- Bu modeli Pepperstone'da işlem kuralı olarak bağlama.
- Uzun tarafın BLIND'da da korunan brüt bilgisi (+0,06…+0,09R; 3/4 hücrede eşlenik plaseboda ≥%99,8) yalnız **bağlam/süzgeç adayı**
  olarak ileride sınanabilir; örneğin daha geniş braketli veya daha uzun ufuklu bir stratejide ters yönlü girişleri
  engellemek için. Bunun için yeni ön kayıt ve yeni veri (≥ 2026-10-21 sonrası gölge) gerekir.

---

## Faktör önemi ve hangi faktörler birlikte çalışıyor

- **Sıralama (SHAP, her hücrede):** DERIV (L/S oranları, 24 s değişimleri, funding tahmini, funding saati, OI 240 dk)
  > PRICE (VWAP uzaklığı, 60 dk aralık konumu, oynaklık) > DEPTH (±%5/±%2 dengesizlik, toplam derinlik) ≈ FLOW
  (60–240 dk CVD, spot dengesizliği, işlem sayısı z) > CAL.
- **Ablation:** yalnız fiyat −0,061R → +takvim +0,002 → +akış +0,010 → +türev +0,026 → +derinlik +0,044R (OOS, 8 hücre
  ortalaması). Gruplar ortalamada üst üste küçük artışlar ekliyor; hiçbiri tek başına maliyeti aşmıyor ve hücre bazında
  gürültülü.
- **Birlikte çalışan kombinasyonlar:**
  - **Long:** 24 s'de düşen L/S oranları (kalabalık long azaltıyor) + düşük funding tahmini + kısa vadeli düşüş / spot satış
    akışı + yüksek hacim/oynaklık.
  - **Short:** satış tarafı ağır defter (±%2–5) + yükselen top-trader pozisyon oranı + yüksek funding tahmini + yüksek
    aktivite + hafta içi.
  - Ortak tema: kalabalık konumlanmasının tersine, aktif piyasada kısa ufuklu dönüş.
- **Büyüklük:** bu kombinasyonların yön bilgisi brüt ≈2–5 bp/işlem (OOS). BLIND'da long ≈2–4 bp kalıyor, short ≈0,6–1,5
  bp'ye düşüyor. Pepperstone gidiş-dönüş maliyeti + stop kayması ≈2,3 bp.

---

## Defter satırı taslağı (§2.11'e, §6 biçimi)

| ID | Tarih | Fikir (kural, parametreler) | Sonuç (sayılar + hangi veri/dönem) | Sınıf |
|---|---|---|---|---|
| BTC-SC-ML01 | 2026-10-22 | **Çok-faktörlü LightGBM scalp seçici** (120 nedensel özellik: fiyat/oynaklık, spot+perp akış, OI, funding, premium/baz, L/S, tasfiye vekili, derinlik, takvim). 5 dk ızgara, giriş sonraki 1m açılışı. SL=max(19 bp, 1,1×ATR5m), TP {1; 1,5}×SL, H {30, 60} dk, L/S ayrı model (8 hücre). Hedef net R (1,85 bp + 1 bp SL kayması). Eşik: kayan 30 g üst k% (iç-CV → k=%1 her hücrede). DISC 21-06→23-12 / OOS 24-01-11→25-06 / BLIND 25-07→26-10-20. Ön kayıt `fam_ml/prereg.md` | 8/8 RED. En iyi L_tp1.5_h60: OOS n 1.754 +0,082R (+2,2 bp) P %93,6 kart 5/6 → BLIND n 1.493 +0,012R P %59 kart 3/6, 2026 −0,017. Ölçüt 5 her hücrede ✗ (icra farkı 0,08–0,09R = maliyet/R; E44). Holm ≥ 0,16. BLIND 5/8 negatif. BIN_TAKER her hücrede −0,2…−0,4R. Öz-sınamalar T1–T5 geçti. Kanıt `research/btc_scalp_20261021/fam_ml/results/eval.json`, `cells_summary.csv` | X (strateji) |
| BTC-SC-ML02 | 2026-10-22 | ML01'in yön bilgisi gerçek mi? Plasebo A (yıl×saat), Plasebo B (etiketi ≥30 g dairesel kaydırılmış 3–10 model), post-hoc oynaklık-eşli plasebo + brüt R + aynı anlarda ters yön | Gerçek: 8/8 hücrede null modellerin hepsinin üstünde (null ort −0,07…−0,11, AUC 0,50 vs 0,513–0,522). Seçilenlerin brüt R'si OOS +0,07…+0,17 (≈2–7 bp) vs eşlenik plasebo ≈0 (%100); ters yön simetrik kaybediyor. BLIND long brüt +0,02…+0,09 (3/4 hücre ≥%99,8), short +0,03…+0,07 (%46–99). Kenar yalnız uç kuyrukta (k=%2'de yarısı, k≥%5'te hemen hepsi negatif). Kalibrasyon aşırı iyimser. Kanıt `fam_ml/results/placeboB_summary.json`, `diag_posthoc.json`, `k_sensitivity.csv` | B (bilgi var, maliyetin altında; süzgeç adayı olarak yeni ön kayıt gerekir) |
| BTC-SC-ML03 | 2026-10-22 | Faktör grupları (TreeSHAP + ablation A0 fiyat / +takvim / +akış / +türev / +derinlik) | SHAP: DERIV > PRICE > DEPTH ≈ FLOW > CAL. Öne çıkanlar `bd_imb_5`, `ls_top_pos`, `ls_global`, L/S 24 s değişimleri, `funding_pred_bp`. Ablation ortalaması OOS: −0,061 / +0,002 / +0,010 / +0,026 / +0,044R; hücre bazında gürültülü (±0,05). Long = kalabalık long azaltırken düşüşte al; short = satış tarafı ağır defter + kalabalık long. Kanıt `fam_ml/results/extra_shap.json`, `extra_ablation.json`, `selected_profile.csv` | C |
| BTC-SC-ML04 | 2026-10-22 | Kısa (S) hücrelerin dönem kararlılığı | OOS 4/4 pozitif (+0,024…+0,077, P %74–98) → BLIND 4/4 negatif (−0,025…−0,072); 2026'da −0,03…−0,12R. Derinlik dengesizliği DISC'te yalnız 2023'te vardı | X |
| BTC-SC-ML05 | 2026-10-22 | Aynı seçimlerin venue maliyetleri | OOS: PEP_FIX15 −0,013…+0,071, BIN_MAKER −0,080…+0,003, BIN_TAKER −0,215…−0,289. BLIND: maker ve taker her hücrede negatif. Not 03'ün sınırı ML seçimiyle de aşılmıyor | A (maliyet olgusu) |

---

## Yeni yöntem tuzakları

| ID | Tuzak | Bedeli (vaka) | Önlem |
|---|---|---|---|
| E51 | **Rastgele-giriş plasebosu, tabanı −maliyet/R olan kurallarda neredeyse otomatik geçilir.** Küçük bir bilgisi olan her seçici "%100 yüzdelik" alır | BTC-SC-ML01: 8/8 hücre Plasebo A'da %100 ve Plasebo B'de tüm null'ların üstünde, ama net ≈0 ve 8/8 RED | Plaseboyu "bilgi var mı?" sorusu için kullan. Kârlılık kararını mutlak net R + BLIND + "net ≥ 2×maliyet" ile ver. Brüt R ve eşlenik plaseboyu ayrıca raporla |
| E52 | **Net-R hedefli seçici yüksek oynaklık anlarını seçer.** ATR büyüdükçe maliyet/R küçüldüğü için "R kenarı" kısmen maliyet rejimidir; yıl×saat plasebosu bunu eşlemez | ML01: seçilen SL ort. 30–40 bp vs havuz 22–25 bp; taban-bağlı pay %16–56 vs %57–70 | Plaseboyu SL/ATR ondalığıyla da eşle. Brüt R'yi ve aynı anlarda ters yönü raporla (yön bilgisi ↔ rejim ayrımı). R ve bp'yi birlikte yaz (E50; ML01'de L_tp1_h30 OOS −0,005R / +0,21 bp, L_tp1.5_h60 2026 −0,017R / +0,68 bp) |
| E53 | **Aşırı yayılmış (kalibre olmayan) regresyon tahminleriyle mutlak eşik ("beklenen R > 0").** Ağaç modeli uçlarda iyimser | ML01: en üst ondalık tahmini +0,10R → gerçekleşen −0,06R; "tahmin > 0" eşiği OOS ve BLIND'da her hücrede negatif | Mutlak eşik yerine nedensel kayan nicel kullan. Kalibrasyon tablosunu zorunlu raporla |
| E54 | **İç-CV ile k seçimi en uç kuyruğu seçer** (8/8 hücrede k=%1); kenar yalnız orada yaşar ve kapasite/kararlılık yoktur | ML01: k=%2'de OOS hücrelerinin yarısı, k≥%5'te hemen hepsi negatif; yapılandırma değişince üst %1'in işareti dönüyor (L_tp1_h30 C1 −0,022 / C4 +0,021) | k duyarlılık eğrisini ön kayıtta zorunlu rapor yap. Kenar yalnız tek bir k'da varsa "seçim yüklü" say ve n'yi bağımsız gün olarak oku |
| E55 | **Öz-sınamada etiket motoru referansını kaydedilmiş float32 parametreden kurmak** tam-eşitlik sınırında sahte uyuşmazlık üretir ve "DÜŞTÜ" yazar | fam_ml T4: L_tp1_h60 2/3.000 (float32 `s_bp`); float64 ile 0/24.000 | Seviye/eşik parametrelerini float64 sakla veya referansı üretimle aynı hassasiyetle kur. Etiket doğruluk testini sızıntı testlerinden ayrı raporla |
