# Ön kayıt — Büyük alt fitilden sonra giriş ZAMANLAMASI: ilk / ikinci giriş, ikinci mum, 5 dk mumlar (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## 0. Kaynak ve gerekçe

**Kullanıcı hedefi:** "Büyük fitil bıraktıktan sonra kâr yakala. İlk girişte, ikinci girişte, ikinci mumda ya da 5 dakikalık farklı bir
mumda. Bakış açını değiştir."

**Önceki sonuçlar:**
- §2.65: 3,5 sa fitil + 15m seviyeler X.
- §2.66: V/W dip X.
- FR-15: 1h teyitli çekiç = "ikinci mumda" girişin 1h hâli. 7 Kasım'da B'ydi; NX-01 9 yıllık 1m'de +0,082R, P 0,81, zayıf.

**Yeni bakış açısı:** "Nerede gir" yerine "fitilden sonraki ilk dakikalarda fiyatın ilk tepkisi nasıl okunur" sorusu. 5 dk mumlarla
mikro teyit, ilk geri çekilmeden sonraki ikinci giriş ve aynı zaman dilimindeki ikinci mum. Bu zamanlama ailesi defterde
sınanmadı: FR-10 gecikme/5m teyit 1h'te denendi ve X çıktı, 210m tetikte hiç denenmedi.

## 1. Veri ve dönemler

- **NDX:** Dukascopy 1m (sabit kaynak `lib.load_m1`), ask = bid + spr.
  - KEŞİF 2018-01-02 → 2021-10-31: tüm seçim.
  - TEST 2021-11-01 → 2026-11-15: bir kez.
- **Bağımsız piyasa:** DAX Dukascopy 1m 2018-01 → 2026-11, kural aynen (`fibo_altin_bolge_20261116/cache/DAX_1m.npz`).
- **Bağımsız besleme:** NQ vadeli 5m 2019-08 → 2024-08 (`ndx_tf_yapilandirma/out/ek/NQ_kalibre.parquet`). 5m çözünürlük; aynı mumda
  TP+SL → SL. Spread NQ için sabit 0,25 puan.
- **VIX:** önceki günün kapanışı.

## 2. Tetik (büyük alt fitil)

Tetik zaman dilimi TF ∈ {1h, 210m}. 1h: NY saat sınırı; 210m: NY 17:00 ızgarası.

Tetik koşulu: alt fitil ≥ fiyatın %0,50'si ve üst fitil ≤ alt fitil / 2 (kullanıcının kuralı, §2.65 EK-1).

Karar anı t_c = tetik mumunun kapanışı. 5m mumlar t_c'den sonra açılanlardır.

## 3. Giriş zamanlaması (7 tip)

Giriş her durumda karar mumunun kapanışından sonraki ilk 1m açılışındadır.

| kod | giriş |
|---|---|
| Z0 | hemen (t_c) — taban |
| Z1 | ilk 5m mum yeşilse, kapanışında |
| Z2 | ilk iki 5m mumun ikisi de yeşilse, ikincinin kapanışında |
| Z3 | 12 adet 5m (1 sa) içinde, tetik mumunun son 5m tepesinin üstünde kapanan ilk 5m |
| Z4 | **ikinci giriş:** t_c'den sonraki ilk kırmızı 5m'den sonra, o kırmızının tepesinin üstünde kapanan ilk 5m (24 mum içinde) |
| Z5 | **ikinci mum (aynı TF):** sonraki TF mumu yeşil ve tetik kapanışının üstünde kapanırsa, kapanışında |
| Z6 | **teyitli:** sonraki TF mumu tetik mumunun tepesinin üstünde kapanırsa, kapanışında |

## 4. Izgara

Stop:
- **Sa:** tetik dibi − %0,10.
- **Sb:** t_c ile giriş arasındaki 5m dipleri − %0,05. Arada mum yoksa Sa.

Diğer boyutlar:
- TP: {1R, 2R, 3R}.
- Zaman: {1 sa, 4 sa, ertesi işlem günü NY 16:00}.
- VIX: {hepsi, ≥ 18,4}.

2 TF × 7 × 2 × 3 × 3 × 2 = **504 hücre**. En az risk 5 bp. Aynı barda TP ve SL → SL. Uzunda gecelik finansman.

## 5. Seçim (yalnız KEŞİF)

Aday hücre:
- n ≥ 40,
- ort R > 0,
- gün-küme P ≥ %90,
- spread × 1,5 > 0.

Izgara plasebosu: girişler ±1–7 gün kaydırılır (aynı saat, aynı % stop), 20 kopya.

Dondurma: KEŞİF t'ye göre en iyi en fazla 5 aday; aynı giriş tipinden en fazla 2.

## 6. Doğrulama — "kâr kapısı" ölçütü (hepsi)

1. NDX TEST ort R > 0 ve küme P ≥ 1 − 0,10/K (K = dondurulan aday sayısı; 5 → %98).
2. DAX 2018–26 ort R > 0 ve küme P ≥ %90.
3. NQ 2019–24 ort R > 0.
4. TEST spread × 1,5 > 0.
5. TEST eşli plasebodan iyi (P ≥ %90).
6. İcra farkı (iyimser − gerçek) < 0,5 × |gerçek|.
7. Tek pozisyon kısıtıyla > 0.
8. Toplam n ≥ 150.

**Hüküm:**
- Hepsi geçerse **B**: kâr kapısı, 2. KURAL kartı, SHADOW, canlı kararı kullanıcıda.
- TEST + DAX artı ama başka ölçüt düşerse C.
- Aksi hâlde X.

## 7. Sonraki turlar (geçmezse; sonuçlardan önce belirlendi)

Tur sınırı 3:
- **Tur Z2 — yön tersi:** aynı tetik, aynı 7 zamanlama, **SAT**. Fitil "likidite süpürmesi + devam" olabilir; defter §3-15'e göre
  süpürme dönüş değil, devam.
- **Tur Z3 — tetik eşiği oynaklığa göre:** alt fitil ≥ k × ATR14(TF), k ∈ {1, 1,5, 2}, %0,50 yerine. Aynı zamanlama ızgarası.

Birikimli K tüm turların dondurulan adaylarıdır. Üç turda geçen yoksa aile X olur ve arama durur.
