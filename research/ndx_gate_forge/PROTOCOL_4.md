# Tur 4 — diğer ajanın sentez raporuyla karşılaştırma → varyasyonlar (ön-kayıt, 2026-10-02)

Karşılaştırılan: `research/ndx_synthesis_20261002/NIHAI_RAPOR.md`. O rapor CAPREV'i M1'de 11 olayla denetledi
(+11,1R ama en iyi 5 gün çıkınca −1,35R; TP80/SL110 ile +1,07R), stressiz/yüksek-VIX kontrolünü pozitif buldu
(+3,35R/33), dip geri-alımını bekleyen varyantı küçük örnekte pozitif buldu (+5,8R/9), 1h'te 09:00 seans dibini eleştirdi.

## Açık sorular → varyasyonlar (parametreler sabit; uzun veri 1h 2016-26 / 30m 2021-26 / 15m 2023-26 + 1m)

| # | Soru | Varyasyon | Tahmin (mekanizma: "korku döner") |
|---|---|---|---|
| W1 | Etkiyi stres mi taşıyor, VIX mi? | Önceki RTH dibi altında ilk kapanış → BUY, 4 hücre: stres×VIX(≥/<18,4) | yüksek VIX tek başına da pozitif; en güçlü stres∧yüksek VIX; düşük VIX'te yok |
| W2 | Kriz piyangosu mu? | VIX kovası (18,4–25 / 25–35 / >35); kırpılmış ortalama (üst+alt %5), en iyi %10 olayın toplamdaki payı; aynı günlerde rastgele saat BUY plasebosu (200 tekrar) | 18,4–25 kovası da pozitif; kırpılmış ortalama > 0; olay-zamanlaması plasebonun üst %5'inde |
| W3 | Seans dibi tanımı | 1h'te önceki dip: (a) 09:00–16:00 barları, (b) 10:00–16:00 barları (09:30–10:00 kaçar); 30m/15m kesin 09:30 | işaret ve büyüklük iki yaklaşımda benzer |
| W4 | Kenar nerede: zaman mı braket mi? | Çıkış eğrisi: aynı gün 16:00, ertesi gün 10:00, ertesi gün 16:00, 2. gün 16:00, 4. gün 16:00; 1×gvol stop | getiri ufukla artar (toparlanma sürüklenmesi); aynı eğri rastgele-saat kontrolünde düz |
| W5 | Kırılımda mı al, geri alımda mı? | (i) ilk kapanış < dip (anında), (ii) dip altı görüldükten sonra ilk kapanış > dip (geri alım) | ikisi de pozitif; anında alım daha fazla olay |
| W6 | Kart hacmi (≥150 olay) | W1'de hangi hücre(ler) birleşebilir → 10 yılda olay sayısı | yüksek VIX ∪ stres genişlemesi hacmi 150'nin üstüne taşır |

Ek düzeltmeler: macro yamasında 30 Eylül tamamlanmış değerlerle güncellenir; NIHAI_RAPOR'daki "kovalama K5b'yi içerir"
ifadesi ve μ∝σ² kesinliği düzeltilir.

## Ek W7 (DAX/günlük-endeks sonucu görüldükten sonra; açıkça sonradan)
Günlük veride "stres∧VIX≥18,4 gününde açılıştan BUY" kontrolü dip-kırılımı sürümüyle aynı getiriyi verdi.
W7: gün-içi veride (NDX 1h/30m/15m, DAX 1h/30m) üç giriş karşılaştırılır — (a) seans açılışında BUY (NY 09:30 / Berlin 09:00),
(b) CAPREV dip kırılımı, (c) birleşik: açılışta 1 birim + kırılımda 2. birim. Aynı stop (1×gvol, her birim kendi girişinden),
çıkış aynı gün / ertesi gün seans kapanışı. Kart hacmi için 10 yıldaki olay sayısı raporlanır.
