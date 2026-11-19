# Paket (K1 + OPEX vetosu + XP) kaybeden/kazanan ayrımı — RAPOR (2026-11-19)

- **Ön kayıt:** `PROTOCOL.md` (+ EK-1, Tur 4). **Kod:** `src/motor.py` (özellik motoru, sızıntı testi), `src/ortak.py`, `src/tur1.py`, `src/tur23.py`, `src/tur4.py`.
- **Sonuçlar:** `results/tur1.json`, `results/tur23.json`, `results/tur4.json` (özellik tabloları ham fiyattan türetilmiş parquet, git dışı).
- **Veri:** paket işlemleri d ≤ 2026-11-05 (ileri gölge dönemine dokunulmadı). MT5 4 endeks + Duka NDX: KEŞİF 264/60 kaybeden (MT5), TEST 374/85.
  ÇAĞ: 1993–2017 ETF V1 vekili 2.680 işlem / 741 kaybeden.
- **Özellikler:** 6 TF (30 dk, 1/2/4 sa giriş anına çapalı; gün; hafta) × (4 kanal uzunluğu × z/eğim/R²/genişlik + Donchian + `ta`'nın 86 göstergesi)
  + TF hizalanma sayıları = 574; + XK'nin 117'si + yol şekli (26 + kNN) + çapraz varlık (9) = 668–732. Sızıntı testi: girişten sonraki veri
  silinince 574 özelliğin hepsi aynı.

## Sonuçlar

| Tur | Ne | En iyi model | Kör AUC (MT5 / piyasa > 0,55 / Duka) | Veto (vetolanan vs kalan, kâr×, zarar×) | Hüküm |
|---|---|---|---|---|---|
| 1 | Gün/hafta imzası ÇAĞ'da öğren → 2018–26 kör | L1 lojistik | 0,564 / 3 / 0,515 | +55 vs +83, ×0,86, ×0,77 | **X** |
| 2 | Gün içi çok TF, MT5 KEŞİF → TEST | LightGBM | 0,599 / 4 / 0,582 | +35 vs +84, ×0,90, ×0,74 | C |
| 3 | + XK 117 özellik | GBM | 0,615 / 4 / 0,599 | −20 vs +87, ×1,03, ×0,76 | C |
| 4 | Büyük eğitim kümesi + sürekli hedef + kNN + çapraz | LightGBM regresyon | **0,644** / 4 / 0,584 | +24 vs +88, ×0,93, ×0,70 | C |
| 4 | aynı | GBM sınıflandırıcı | 0,600 / 3 / **0,657** | +48 vs +80, ×0,88, ×0,76 | X |

- **Ayrışma çıtası** (MT5 ≥ 0,62 ∧ ≥ 3/4 piyasa ∧ Duka ≥ 0,60) **hiçbir modelde birlikte sağlanmadı**; her seferinde biri kıl payı kaçtı.
- **Tek tek:** 574–668 özellikten hiçbiri aile hatası eşiğini geçmedi (60–92 kaybedenle eşik |AUC − 0,5| ≈ 0,16). ÇAĞ'da 39 özellik geçti
  ama ÇAĞ ile 2018–26 AUC'leri arasındaki korelasyon 0,05: günlük imza 25 yılda gerçek, bugünün paketine taşınmıyor.
- **Kümeleme:** kaybeden yoğun küme yok (iki büyük kümede %24/%25 kaybeden). KEŞİF kaybedenlerinin çevresine düşen kazananlar %40–44.
- **Yeni aileler:** yol şekli kNN TEST AUC 0,517; çapraz varlık (DAX/altın/petrol) 0,39–0,54, KEŞİF ile ters → X.

## Kazananların ortak farkı (iki dönemde tutarlı, betimleyici)
- Küçük bir küme her iki dönemde de neredeyse hiç kaybetmiyor: **panik günleri** (Mart 2020, Nisan 2025, 2022 US500 sert günleri).
  VIX 27–58, gün içi düşüş −%1,6 … −%16, oynaklık bantları aşırı geniş. KEŞİF 12 işlem +475 bp (%8 kaybeden), TEST 10 işlem +334 bp (%0).
- Genel eğilim: kazananlarda oynaklık ve VIX daha yüksek.

## Kaybedenlerin ortak eğilimi (ayrıştırıcı değil)
- **Sakin ortamda derin kırılım:** düşük VIX (AUC 0,41 / 0,41), dar 4 sa Bollinger (0,44 / 0,40), fiyat 4 sa 20'lik kanalın daha derin altında
  (0,42 / 0,38). Yani korku gecesi "panikte" kazanır; "sakin piyasada beklenmedik düşüşte" daha sık kaybeder.
- Bu eğilimler kaybedenlerin ancak küçük bir bölümünü ayırır: en iyi modelle vetolanan %15'in ortalaması hâlâ artı (+24…+48 bp).

## Hüküm
- **Ayrışma: X.** 4 turda 8 model, 1.400'ü aşkın özellik ve 25 yıllık bağımsız vekille de kaybeden giriş anında kazanandan ayrılmıyor.
  Bilginin tavanı AUC ≈ 0,60–0,64 ve her turda aynı yerde.
- **Kalite filtresi: C** (§2.99 ile tutarlı). LightGBM regresyon vetosu zarar ×0,70, kâr ×0,93; kanal ∪ GBM ile aynı türden. Yeni gölge
  adayı olarak eklenmedi: mevcut ileri gölge (XK-05) aynı bilgiyi ölçüyor.
- **Sayılar:** Tur 1 157 özellik × 2 etiket; Tur 2 552, Tur 3 570 (× 2 etiket, 1.000 permütasyon); Tur 4 668 özellik; toplam 13 model kurulumu.
- **Sonraki adım ancak yeni bilgi kaynağıyla:** ES/NQ gece seansı yolu, opsiyon (GEX/0DTE, put/call gün içi), gün içi genişlik/TICK,
  emir akışı. Bunlar olmadan aynı veride daha çok gösterge denemek yalnız aşırı uyum üretir (§3-50, §3-51).
