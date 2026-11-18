# Korku gecesi sepeti — K1'in NDX + US30 + US2000'de birlikte işlenmesi (2026-11-18)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md). Kod: `src/sp.py`. Veri MT5 M30, eşit risk (endeksin K1 σ'sı).

## Sonuç: X
| günlük Sharpe | ESKİ | YENİ | tüm | maxDD (σ) |
|---|---|---|---|---|
| yalnız NAS100 | **1,49** | **1,10** | **1,27** | −4,1 |
| 3'lü sepet (1/3 risk) | 1,16 | 1,01 | 1,07 | −4,0 |
| 2021 sonrası 4'lü (+US500) | — | — | 0,85 | −3,9 |

- Ortak gecelerde getiri korelasyonu yüksek: NAS100–US30 0,88, NAS100–US2000 0,86, NAS100–US500 0,96. Çeşitlendirme yok denecek kadar az.
- Öteki endekslerin K1 kenarı NDX'ten zayıf (GI-02: +23…+31 bp, NDX +53). Riski bölmek ortalamayı düşürüyor.
- **Sonuç:** korku gecesi için en iyi araç NDX'in kendisi. Öteki ABD endeksleri yalnız kuralın geçerliliğinin kanıtı, işlem aracı değil.
