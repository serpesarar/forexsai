# XL — korku gecesi + "ilk yükselen kapanışta çık" (XP) için limit (geri çekilme) girişi

Ön kayıt: 2026-11-18, sonuçlara bakılmadan. Kullanıcı: "işlem tespit edildikten sonra 100 pips aşağısına emir konsa hedefleri, kâr
marjını nasıl etkiler?" Strateji: K1 (16:00 ≤ TWAP −%0,5 ∧ 15:00→16:00 aşağı) → normalde 16:00'da piyasadan AL; XP çıkışı = sinyal
gününden sonraki ilk yükselen 16:00 kapanışı (en geç 5 işlem günü).

## Defter kontrolü
KT-01 / Y-01 / TL: limit ve geri çekilme girişleri başka kurallarda kaybettirdi ("limit veren öder": dolan emirler kötü işlemlerdir).
E105/E144: kontrol = aynı sinyal, aynı çıkış, hemen giriş. K1 + XP için limit giriş hiç sınanmadı.

## Kural
Sinyal anında (16:00) ask fiyatı A. Alım limiti L = A × (1 − x), x ∈ {10, 25, 50, 75, 100, 150, 200} bp
(NAS100 ≈ 25.000'de 100 bp ≈ 250 puan; 100 puan ≈ 40 bp). Dolum: 1m yolunda ask'ın en düşüğü ≤ L olan ilk bar; dolum fiyatı
min(L, barın ask açılışı) (boşlukla aşağı açılışta daha iyi fiyat). Geçerlilik iki türlü: **W1** ertesi işlem günü 16:00'ya kadar;
**W2** XP çıkış anına kadar (en çok 5 gün). Dolmazsa işlem yok (0). Çıkış XP ile aynı (16:00 bid), finansman sinyal gününden.
Ek varyant **YARIM**: lotun yarısı 16:00'da piyasadan, yarısı limitle.

## Ölçüler
Dolum oranı; dolan işlemlerin isabeti, ortalaması, en kötüsü, en kötü %10 ortalaması; **sinyal başına** ortalama (dolmayan = 0) ve
toplam; en büyük düşüş; artı yıl. Kaçırılan işlemlerin piyasa girişli sonucu (kim doluyor: kazananlar mı kaybedenler mi?).

## Geçme (bir mesafe "iyileştirme" sayılır)
Duka'da ESKİ (2018-04 → 2021-10) ve YENİ (2021-11 →) iki yarıda da **sinyal başına toplam kazanç** tabandan (x = 0) düşmeyecek **ve**
en kötü %10 ortalaması daha iyi; bağımsız MT5 NAS100 ve kör US500/US30/US2000'in ≥ 3/4'ünde aynı. Yalnız isabet artışı iyileştirme
sayılmaz (dolmayan kazananlar kaybolur).
