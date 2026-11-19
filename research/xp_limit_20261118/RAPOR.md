# XL — korku gecesi + XP için limit (geri çekilme) girişi (2026-11-18)

Ön kayıt `PROTOCOL.md`; kod `src/xl.py`; çıktı `results/xl.json`. 1 bp = %0,01 (NAS100 ≈ 25.000'de 100 bp ≈ 250 puan; 100 puan ≈ 40 bp).

## Duka NDX 2018–26 (252 sinyal) — W2 (emir XP çıkışına kadar geçerli)
| Limit mesafesi | Dolum | Dolan isabet | Dolan ort. | En kötü | En kötü %10 ort. | Sinyal başı ort. | Toplam | En büyük düşüş | Kaçanların piyasa sonucu |
|---|---|---|---|---|---|---|---|---|---|
| 0 (piyasa) | %100 | %79 | +85 | −783 | −304 | **+84,6** | 21.330 | −1.106 | — |
| 10 bp (~25 puan) | %91 | %79 | +81 | −774 | −313 | +73,7 | 18.574 | −1.057 | +235, %100 kazanan |
| 25 bp (~60 puan) | %82 | %80 | +88 | −760 | −308 | +72,3 | 18.224 | −983 | +204, %100 |
| 50 bp (~125 puan) | %73 | %79 | +106 | −737 | −299 | +76,9 | 19.375 | −885 | +178, %99 |
| 75 bp (~190 puan) | %65 | %78 | +128 | −713 | −293 | +82,8 | 20.864 | −836 | +158, %98 |
| 100 bp (~250 puan) | %52 | %75 | +141 | −690 | −309 | +73,0 | 18.384 | −876 | +141, %96 |
| 150 bp | %37 | %73 | +146 | −642 | −294 | +54,0 | 13.600 | −642 | +143, %96 |
| 200 bp | %30 | %75 | +163 | −595 | −275 | +48,4 | 12.186 | −595 | +141, %94 |
| Yarım (½ piyasa + ½ limit 75 bp) | — | — | — | −748 | −273 | +83,7 | 21.097 | — | — |

Okuma: limit derinleştikçe **dolan** işlemler daha iyi görünür (isabet ≈ aynı, ortalama ↑, en kötü ↑), ama dolmayan işlemler
neredeyse hep kazananlardır (en güçlü toparlanmalar geri çekilmeden gider). Sinyal başına kâr 75 bp dışında belirgin düşer.

## Dönem ve besleme kontrolü (ön kayıtlı ölçüt: iki dönemde kâr düşmeyecek + kötü senaryo iyileşecek)
- 75 bp: ESKİ 94,8 vs 94,0 ✓, **YENİ 74,2 vs 78,0 ✗**; MT5 YENİ 69,8 vs 75,3 ✗; US500/US30/US2000 YENİ ✗ → **iyileştirme X**.
- Yarım 75 bp: kötü %10 her yerde iyi (Duka −273 vs −304, MT5 −287 vs −317), kâr ESKİ ≈ aynı, YENİ −%2…−4 → **risk takası (C)**.
- En büyük düşüş limitle her beslemede küçülüyor (Duka −1.106 → −836 @75 bp; US2000 −2.483 → −1.938).
Hüküm: limit giriş kâr artırmıyor ("limit veren öder", bu kez kazananlar kaçıyor); yalnız risk azaltmak için yarım-limit bir seçenek.
