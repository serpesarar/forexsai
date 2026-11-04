# fam_ml — BTC çok-faktörlü ML scalp seçimi: ÖN KAYIT

Yazılış: 2026-10-22, **hiçbir etiket, özellik dağılımı veya model sonucu görülmeden önce**. Bu dosya bir daha
düzenlenmez; değişiklikler yalnız en alttaki "Ekler (amendments)" bölümüne tarih ve gerekçeyle eklenir.

Soru: Elimizdeki tüm nedensel BTC faktörlerini (fiyat/oynaklık, spot+perp taker akışı, hacim, OI, funding, premium/baz,
L/S oranları, tasfiye vekilleri, defter derinliği, takvim, oynaklık rejimi) birlikte kullanan sızıntısız bir
LightGBM modeli, Pepperstone BTCUSD CFD maliyetleri sonrasında kârlı scalp girişleri **seçebilir mi**?

Bağlam/bağlayıcı kurallar: `research_notes/BTC scalping strateji araştırması/01…03` (özellikle 03 §5 "Scalp tasarım
kuralları"), `docs/KAPI_KAYIT_DEFTERI.md` §1 (E1–E50), §3. Ön beklenti (literatür + 03 notu): 1m bar düzeyinde
öngörü gücü küçük; brüt kenar ≥ ~0,15R gerekir; büyük olasılıkla **net kenar yok**. Bu çalışma bunu ML ile sınar.

## 1. Veri ve dışlamalar
- Tek dosya: `research/btc_scalp_20261021/data/btc_scalp_1m.parquet` (ts = bar açılışı, her değer bar kapanışında bilinir).
- İcra fiyatı: **Binance spot** 1m OHLC (`spot_*`, fizibilite motoruyla aynı seri; CFD'ye en yakın vekil).
- Kötü dakikalar (BAD): 2023-03-24 11:28–14:00 UTC; spot kapanışı eksik ardışık ≥5 dk; perp sıfır-hacim ardışık ≥5 dk.
  Bir karar, [karar−60 dk, giriş+H) penceresi BAD ile kesişirse atılır.
- Broker günlük molası: rollover = NY 17:00 (yaz 21:00 / kış 22:00 UTC). **Zorunlu kapanış R−2 dk (20:58/21:58 UTC)**.
  Uygulama: tutuşu (giriş + H) zorunlu kapanışı aşacak karar **açılmaz** (yani pozisyon hiçbir zaman rollover'ı kesmez);
  giriş dakikası [R−2, R+1) içindeyse açılmaz. Swap bu nedenle sıfır.

## 2. Karar ızgarası ve etiket
- Karar anı: her 5 dakikalık sınır T (dakika m = T'den önce kapanan bar, (m+1) mod 5 = 0). Özellikler yalnız m ve öncesi
  barlardan. **Giriş = sonraki 1m açılışı open[m+1]**.
- Geometri ailesi (8 hücre): yön ∈ {L, S} × TP çarpanı ∈ {1,0; 1,5} × zaman stopu H ∈ {30, 60} dk.
  SL mesafesi s = max(19 bp, 1,1 × ATR14(5m)) (ATR = karar anında tamamlanmış son 14 adet 5m bar); TP = s × çarpan.
- İlk-dokunuş [giriş barı, giriş+H): giriş barının high/low'u dahil. **Aynı barda TP+SL → SL**. SL dolumu boşluk-duyarlı
  (long min(SL, open[vuruş barı])), TP limit seviyeden, zaman çıkışı son barın kapanışı.
- Net R = (brüt bp − maliyet bp − 1 bp × [SL ile çıkış]) / s_bp. Maliyet senaryoları (gidiş-dönüş):
  **PEP 1,85 bp (birincil)** · PEP_STRESS 2,78 bp · PEP_FIX15 = 15 $/giriş fiyatı · BIN_MAKER 4 bp · BIN_TAKER 10 bp.
  Stop kayması 1 bp tüm senaryolarda.
- İyimser icra (kart ölçüt 5 karşılaştırması): giriş = karar barı kapanışı close[m], seviyeler bu fiyattan, maliyet 0,
  kayma 0, SL seviyeden; aynı-bar → SL korunur.
- Model hedefi: PEP birincil net R (regresyon). Ayrıca TP-önce ikili etiketi yalnız AUC raporu için.

## 3. Özellikler (hepsi nedensel; m kapanışında bilinir)
Grup etiketleri ablation içindir.
- **PRICE**: log getiriler 1/5/15/30/60/240/1440 dk (spot, bp ve σ-normalize); gerçekleşen oynaklık 15/60/240/1440 dk
  (1m getiri std) ve oranları; ATR14(1m), ATR14(5m) bp; s_bp ve s/ATR5 (taban bağlayıcı mı); aralık konumu 60/240/1440 dk;
  00:00 UTC çapalı VWAP'a ve 240 dk kayan VWAP'a uzaklık (ATR5 birimi); sıkışma genişliği (60 dk close std / 1440 dk oynaklık);
  son 5m barın gövde/aralık ve fitilleri; 24 s RV rejimi ve 30 g ortalamasına oranı.
- **FLOW**: perp ve spot taker dengesizliği (2·TB/V−1) 1/5/15/60 dk; perp CVD 60/240 dk (hacme normalize); spot−perp
  dengesizlik farkı; perp hacim ve işlem sayısı z (5 dk ve 60 dk toplamları, 30 g geçmişe göre); ortalama işlem büyüklüğü z;
  spot/perp hacim oranı.
- **DERIV**: OI değişimi 5/15/60/240 dk; `oi_chg_5m_z`; OI×fiyat çeyreği (60 dk getiri işareti × 60 dk OI değişimi işareti,
  ve sürekli çarpım); funding son oran, 30 g z, `funding_pred_running`, funding'e kalan dakika; premium bp ve 24 s z;
  perp−spot baz bp, z ve 60 dk değişimi; mark−index baz; L/S oranları (top hesap, top pozisyon, global hesap; log) +
  24 s değişimleri + eksiklik göstergeleri; taker L/S 5m oranı (log); tasfiye vekilleri (`liq_proxy_long/short_5m`,
  `liq_proxy_score_5m`, `liq_flow_long/short_1m` son 60 dk toplamı, `perp_ret_1m_z`, `perp_lvol_1m_z`); metrics yaşı.
- **DEPTH** (2023+; öncesi NaN + eksiklik göstergesi): `bd_imb_1/2/5` (bd_suspect=1 → NaN), 5 dk ortalama imb_1,
  ±%1 toplam derinlik (log) 30 g z.
- **CAL**: UTC saati, haftanın günü, hafta sonu, saat-içi dakika, rollover'a kalan dakika.
- Kullanılmayanlar: aggTrades 1 s özellikleri (yalnız 2026-04+, KEŞİF'te yok), ±%0,2 derinlik (2026-01+).
- Yön modeli: **her yön için ayrı model** (L ve S), aynı özellik seti.

## 4. Dönemler, eğitim, ayarlama
- KEŞİF (DISC) 2021-06-01 → 2023-12-31 · OOS 2024-01-11 → 2025-06-30 · KÖR (BLIND) 2025-07-01 → 2026-10-20.
- Arınma/ambargo: eğitim satırlarının etiket penceresi sonraki bloğa taşmaz; bloklar arasında ≥1 gün ambargo
  (DISC→OOS arasında zaten 10 gün boşluk; DISC+OOS→BLIND yeniden-fitinde son 1 gün atılır).
- İç CV (yalnız DISC içinde): genişleyen pencere, 4 doğrulama bloğu = DISC'in son 4 eşit parçası (≈ 2022-03'ten sonra);
  her fold eğitimi doğrulama başlangıcından 1 gün önce biter. 4 hiperparametre yapılandırması (önceden sabit):
  C1 leaves 15 / min_leaf 1000 / 300 ağaç / lr 0,03; C2 31 / 500 / 300 / 0,03; C3 63 / 2000 / 500 / 0,03;
  C4 15 / 3000 / 800 / 0,02. Hepsinde feature_fraction 0,7, bagging 0,7 (freq 1), lambda_l2 10, seed 7.
- Eşik kuralı (canlıda uygulanabilir): **"son 30 günün (bu modelin eğitim-dışı) tahminlerinin üst k%'sı"** (kayan nicel;
  geçmiş ≥7 gün gerekir, yoksa işlem yok). k ∈ {1, 2, 5, 10}%.
- Seçim (yalnız iç CV OOF tahminleriyle): her hücre için (yapılandırma, k) çifti = iç-CV birleşik ort. net R'yi en
  yükselten; iç-CV işlem sayısı ≥ 300 şartıyla. Bu (yapılandırma, k) **dondurulur**; DISC'in tamamında aynı
  yapılandırmayla son model eğitilir → OOS'a tek seferde uygulanır. Sonra DISC+OOS ile aynı yapılandırma/k ile yeniden
  eğitilip BLIND'a tek seferde uygulanır (BLIND'ın ilk 7 günü eşik ısınması, işlem yok).
- İkincil (yalnız rapor): mutlak eşik "tahmin > 0".
- "Öncelikli hücre": iç-CV ort. net R'si en yüksek hücre (8'den biri). Diğer 7 hücre de raporlanır (seçim yükü için Holm).

## 5. Değerlendirme ve geçme ölçütleri (OOS'ta, ayrıca BLIND)
Canlıya alma kartı (CLAUDE.md 2. Kural), seçilen işlemler üzerinde:
1. n ≥ 150 çözülmüş işlem.
2. ort. net R > 0 **ve** gün-blok bootstrap (2.000) P(EV>0) ≥ %90.
3. Kronolojik iki yarının ikisi de ≥ 0.
4. PEP_STRESS (2,78 bp) maliyetinde ort. R > 0.
5. |iyimser ort. R − gerçekçi ort. R| ≤ 0,5 × |gerçekçi ort. R| (E44: bp ölçeğinde fiilen "net ≥ 2×maliyet").
6. Tek pozisyon zinciri (önceki işlem kapanmadan yenisi yok, L ve S ayrı hücre) ort. R > 0.
Ek ölçütler (hepsi gerekli):
- **Plasebo A**: aynı sayıda rastgele giriş, aynı hücre geometrisi, aynı (yıl, UTC saati) tabakası, aynı dönemin geçerli
  karar noktalarından; ≥ 500 çekiliş; model ort. R'si plasebo dağılımının ≥ %95 yüzdeliğinde.
- **Plasebo B (etiket-karıştırılmış model)**: DISC etiketleri gün-blok halinde karıştırılıp aynı yapılandırma/k ile
  10 model; OOS ort. R'leri; gerçek model hepsinin üstünde.
- KÖR dönemde ort. net R > 0 (işaret).
- Holm (8 hücre, tek yönlü gün-blok bootstrap p) < 0,05 OOS'ta.
Verdikt: hepsi → **LIVE adayı (yine de önce GÖLGE)**; kart 6/6 ama ek ölçütlerden biri ✗ → SHADOW; kart < 6/6 → RED.
Raporlanacaklar (verdikti değiştirmez): yıl bazında ort. R ve bp; kalibrasyon (tahmin ondalıkları vs gerçekleşen);
AUC (net R>0 ve TP-önce); maliyet senaryoları (FIX15, BIN_MAKER, BIN_TAKER); kendi aynı-bar oranı; işlem/gün;
gain + TreeSHAP (LightGBM `pred_contrib`) önemleri, grup toplamları; ablation PRICE / +FLOW / +DERIV / +DEPTH(=tam)
(aynı yapılandırma/k, OOS); seçilen işlemlerin özellik profili (seçilen vs tüm, z-farkı).

## 6. Sızıntı öz-sınamaları (sonuçlardan önce koşar; biri düşerse sonuç geçersiz)
- T1 önek: veri m'den sonra kesildiğinde (rastgele 5 kesim) m ve öncesi kararların özellikleri birebir aynı.
- T2 giriş barı: giriş barı ve sonrası OHLCV/akış değerleri bozulduğunda karar özellikleri değişmez (T1'in özel hâli,
  ayrıca açıkça sınanır).
- T3 kaynak nedenselliği: `metrics_eff_ts ≤ ts`, `funding_last_time ≤ ts+1m`, `bd_snap_age_s ≥ 0`.
- T4 etiket motoru: rastgele 3.000 karar için vektörel ilk-dokunuş = basit döngü (sıfır uyuşmazlık).
- T5 kasıtlı sızıntı: bir özelliğe gelecek bilgisi (sonraki 15 dk getirisinin gürültülü hâli) eklenince OOS AUC ve
  ort. R patlamalı (harness sızıntıyı görebiliyor mu).

## 7. Çalışma süresi
Tam veri (5 dk ızgara ≈ 560 bin karar/yön) kullanılır; alt-örnekleme yapılırsa ek olarak yazılır.

## Ekler (amendments)
**EK-1 (2026-10-22, model sonuçları görülmeden; yalnız uygulama netleştirmeleri):**
- Kayan eşik **saatlik** yenilenir: her saat başında, o andan önceki 30 günün eğitim-dışı tahminlerinin (1−k) niceliği;
  o saat içindeki kararlar bu eşiği kullanır (canlıda aynısı uygulanabilir). Pencerede <100 tahmin varsa işlem yok.
  OOS'un eşik geçmişi 2024-01-01'den başlar (model-1 için eğitim-dışı boşluk günleri dahil).
- Plasebo B'de "gün-blok karıştırma" = DISC eğitim etiket dizisinin ≥30 günlük rastgele **dairesel kaydırması** (E48:
  blok/otokorelasyon korunur, özellik↔etiket bağı kopar). Model sayısı: kartı 6/6 geçen ya da OOS ort. R > 0 olan
  hücrelerde 10, diğerlerinde ≥3 (bilgi amaçlı).
- Ablation setleri: A0 PRICE · A1 PRICE+CAL · A2 +FLOW · A3 +DERIV · tam (+DEPTH) · ayrıca A3b PRICE+CAL+DERIV.
  (CAL taban sete eklendi; "yalnız fiyat" karşılaştırması A0'dır.)
- T4 notu: döngü referansı float32 `s_bp` okuyunca L_tp1_h60'ta 2/3.000 tam-eşitlik yuvarlama farkı; float64 ile 0/21.631.
- Plasebo A çekiliş sayısı 500, havuz = aynı segmentte eşik ısınmasından sonraki geçerli kararlar.
