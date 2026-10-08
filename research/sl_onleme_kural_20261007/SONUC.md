# Sonuç — "SL'leri en çok önleyen kural" araması (2026-10-07)

Ön-kayıt: [PROTOCOL.md](PROTOCOL.md) · kod: `search.py` · ham: `results/ileri.csv`, `results/geri.csv`.
553 bağımsız karar (2026-06-30 → 10-07). İleri: ilk %60'ta seç → son %40'ta sına (1.946 kural).
Geri: son %60'ta seç → ilk %40'ta sına (2.158 kural). Kurallar: giriş anında bilinen tüm özellikler × 7 eşik
× 2 yön, kategoriler, kapsam başına en iyi 30 tekli kuralın AND çiftleri; TÜMÜ + her sembol-yön.

## Genelleme testi (asıl cevap)

| | ileri | geri |
|---|---:|---:|
| eğitim başarısı ↔ sınama başarısı (Spearman) | **+0,03** | **−0,08** |
| eğitimin en iyi %5'i sınamada pozitif | %60 | %34 |
| eğitimin en iyi %5'i rastgele elemeden iyi | %82* | %30 |
| tüm kurallar sınamada pozitif | %46 | %42 |

\* İleri sınama döneminde ortalama R pozitif olduğu için rastgele eleme kendiliğinden para kaybettirir; bu oran
o yüzden şişkin, geri yönde %30'a düşüyor.

**Eğitimde iyi görünen kuralın sınamada da iyi olma olasılığı yazı-turadan farksız.** Seçim işe yaramıyor.

## Eğitimin en iyileri sınamada (TÜMÜ kapsamı)

| kural (giriş anında bu varsa AÇMA) | eğitim R | sınama R |
|---|---:|---:|
| son 3 mumda aleyhte fitil oranı ≤ 0,19 | +19,9 | +3,0 |
| son 5 dk hacmi / önceki 60 dk ≤ 0,97 | +16,1 | **−11,7** |
| saat ≥ 15 UTC | +15,9 | **−7,6** |
| açık pozisyon ≤ 1 | +14,8 | **−18,6** |
| SL yapı ucuna ≤ 1,27 ATR | +14,0 | −2,4 |
| aleyhte RSI diverjansı (IO-05) | +13,0 | +3,1 (23 engel) |
| ardışık ≥2 aleyhte mum | +12,9 | −4,3 |
| 1h EMA50'den ≥ 1,89 ATR uzak | +12,6 | −2,0 |

Eğitimde +10…+20R kurtaran kuralların çoğu sınamada para kaybettiriyor. İlk sıradaki fitil kuralı da
`islem_otopsi` odak sınamasında −1,8R vermişti (iki bağımsız kesitte işaret değiştiriyor).

## Hüküm
Bu işlem kümesinde SL'leri öngörülebilir biçimde ayıran bir giriş kuralı **yok** (defter GF-01, E12, E17 ile
tutarlı). Öncelik sırası: (1) çıkış/kilit kuralları elendi (M9, IO-07, IO-10); (2) geri çekilme limiti elendi
(IO-09); (3) giriş vetoları genelleşmiyor (IO-11). Tek takip edilen gölge adayı aleyhte RSI diverjansı (IO-05,
backlog bl_1145875a46) — bu aramada da iki bölmede pozitif ama küçük (23 sınama engeli).
SL'ler bu stratejilerin braketinin doğal maliyeti: kenar, SL'yi önlemekte değil, beklentisi pozitif
sinyal ailelerini (NDX BUY, DAYCOMBO, REENTRY) seçmekte ve lot/risk dağılımında.
