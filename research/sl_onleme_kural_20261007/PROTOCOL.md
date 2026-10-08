# Ön-kayıt — "SL'leri en çok önleyen kural" araması (2026-10-07)

Kullanıcı: "hangi kural işe yarar, tüm bu SL'leri maksimum önleyebilecek olanı bul."
Hedef SL sayısı DEĞİL (en çok SL'yi önleyen kural = hiç işlem açmamak): hedef **net R** —
engellenen işlemlerin toplam R'sinin eksisi (kurtarılan SL − kaçırılan TP), ve bunun **hiç bakılmamış
dönemde** tutması. Defter: GF-01 (rastgele girişte tek-özellikli kapı yok), E12 (küçük alt küme %100), E17
(p-değeriyle seçim taşınmaz), IO-04/IO-05.

## Veri
`bot_trades` 2026-06-30 → 10-07, karar başına ilk bacak, gerçekleşen R (`r_exit`). Yalnız KARAR ANINDA
bilinen özellikler: `pre_*`, `geo_*` (be_wr hariç), `ctx_*`, saat, gün, ABD açılışına dakika, seans, aile.

## Bölme
Kronolojik: ilk %60 = EĞİTİM (kural seçimi), son %40 = SINAMA (yalnız bir kez okunur).
Ters yön kontrolü: son %60'ta seç, ilk %40'ta sına (dönem bağımlılığı).

## Kural uzayı (sabit)
- Kapsam: TÜMÜ + eğitimde ≥40 kararı olan her sembol-yön.
- Tekli: her sayısal özellik × eğitim yüzdelikleri {10,20,33,50,67,80,90} × {≥, ≤}; ikililer =1/=0;
  kategoriler (seans, aile, haftanın günü) = değer.
- İkili: kapsam başına eğitimde en iyi 30 tekli kuralın tüm AND çiftleri.
- Kısıt: eğitimde engellenen ≥10 karar ve kapsamın ≤%50'si.
- Eğitim sıralaması: kurtarılan R (= −Σ R engellenen).

## Değerlendirme
1. Her kapsamın en iyi 10 kuralı sınamada: kurtarılan R, engellenen SL/TP, rastgele eşit-sayı elemeye göre fark.
2. **Genelleme testi:** tüm kurallarda eğitim kurtarılan R ile sınama kurtarılan R arasında Spearman korelasyonu,
   ve eğitimin en iyi %5'inin sınamada pozitif olma oranı; plasebo = aynı engelleme oranında rastgele kurallar.
3. Geçme: sınamada pozitif VE rastgele elemeden iyi VE ters-yön kontrolünde de pozitif VE ≥10 sınama engellemesi.
   Geçen kural yalnız GÖLGE adayıdır (≥150 olay + canlıya alma kartı).
