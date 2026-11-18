# Ön kayıt — "Önce kazandır, sonra ters çevir": uzun sakinlik sert düşüşü haber verir mi? (^NDX 1985–2026) (2026-11-18)

Sonuçlara bakılmadan yazıldı. Kullanıcının tezi: büyük oyuncular önce "her şey yolunda" görüntüsüyle piyasayı yukarı taşır, sonra ani
dönüşle algoları ve işlem açanları ters bırakır; son 5 yılda (algo/AI çağı) bu daha belirgin.

## Ölçüler (^NDX günlük, yfinance; `ndx_seri_opex_20261118/data/NDX_1985.parquet`)
- Sakinlik: 20 günlük gerçekleşen oynaklık (RV20) önceki 250 günün alt %20'sinde **ve** fiyat 50 günlük ortalamanın üstünde (yükselen,
  sakin piyasa). Sakinlik süresi S = bu koşulun kesintisiz sürdüğü gün sayısı.
- Gelecek: 20 işlem günü içinde kapanış bazında en büyük düşüş (MDD20) ≤ −%5 olasılığı; 20 günlük getiri.
- Kovalar: sakin değil / S 1–20 / S 21–60 / S > 60.

## Hipotez ve ölçüt
- **Tez doğru ise:** P(MDD20 ≤ −%5) uzun sakinlikte (S > 60) sakin olmayan günlerden **yüksek** ve S ile artar.
- Ölçüt: 1985–2007, 2008–2020, 2021–2026 (son 5 yıl) üç dönemde de P(S > 60) > P(sakin değil) → tez desteklenir (C+; SAT/koruma
  aday kuralı ayrı ön kayıt ister). Son 5 yılda tek başına → "son 5 yıla özgü" iz. Değilse tez desteklenmez (X).
- Bilgi: 20 günlük getiri ortalaması kovalara göre (sakinlik uzun pozisyon için kötü mü?).
