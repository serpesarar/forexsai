# Korku gecesi + XP: geçmiş haftanın desteklerine limit girişi — RAPOR (2026-11-19)

Ön kayıt: `PROTOCOL.md`. Kod: `src/destek.py`. Sonuçlar: `results/destek.json`, `results/seviyeler.csv`. Hüküm: **X**.

## Soru
Kullanıcının gözlemi: korku gecesinden sonra fiyat geçen haftanın desteklerinden tepki alıyor gibi. Öneri: 16:00'da piyasadan almak
yerine alım limitini o desteklere koymak.

## Kurulum
- Sinyal ve çıkış değişmedi (K1 + XP).
- Altı destek ailesi var: önceki 5 ve 20 günün gün dipleri (D5, D20), D5'teki ikinci dip (D5_2), 1 saatlik fraktal salınım dipleri (P5, P20) ve son 8 haftanın hafta dipleri (W8).
- Seviye 16:00 alışının 15–300 bp altındaki en yakın seviyedir. Seviyeler yalnız 16:00 öncesi bilgiden kurulur.
- Limit XP çıkışına kadar (W2) veya ertesi 16:00'ya kadar (W1) bekler.
- Seviye yoksa üç kural var: piyasa girişi (B, ana), işlem yok (A), ya da yarı piyasa + yarı limit (YARIM).
- **Hayalet seviye:** seviye uzaklıkları sinyaller arasında karıştırılır (500 permütasyon). **Tepki:** dokunuştan sonra fiyat önce +50 bp mi gider, −50 bp mi.

## Sonuç (sinyal başı ort. bp, W2 + B; TEST = 2021-11 → 2026-11)
| Besleme | Piyasa | D5 | D5_2 | D20 | P5 | P20 | W8 |
|---|---|---|---|---|---|---|---|
| Duka NDX | **78,0** | 57,8 | 56,3 | 54,1 | 56,1 | 59,2 | 57,4 |
| MT5 NAS100 | **75,3** | 52,2 | 53,3 | 49,5 | 49,1 | 56,4 | 52,2 |
| MT5 US500 | **72,7** | 57,3 | 55,6 | 53,6 | 61,1 | 59,0 | 46,3 |
| MT5 US30 | **41,0** | 30,1 | 35,3 | 27,8 | 27,1 | 25,2 | 30,6 |
| MT5 US2000 | 51,1 | 48,6 | 43,7 | 50,6 | 43,0 | 48,6 | 53,5 |

- TEST'te 30 hücrenin 29'u piyasa girişinin altında (−%3…−%38). KEŞİF'te de en iyi hücre yalnız eşit (P5 94,4 vs 94,0).
- **Neden:** limit dolmayan işlemlerin %89–100'ü kazanandı ve piyasa girişiyle ortalama +130…+190 bp getirmişti. Bu, XL-01'deki tablonun aynısı. Limit, düşmeye devam eden işlemleri yakalıyor, hemen dönenleri kaçırıyor.
- **Yarım limit** kârı TEST'te −%12…−%15 düşürüyor. En kötü %10 ancak birkaç bp iyileşiyor. Bu, C ölçütünü (≤ %5 kâr kaybı) de geçmiyor.
- **W8 hafta dipleri** en kötü %10'u ve maksDD'yi düzeltiyor (Duka TEST: −336 → −279, −1.106 → −1.014), ama kâr −%26 düşüyor. C değil.
- **Hayalet:** gerçek seviye hayaletten anlamlı biçimde iyi değil. P ≥ 0,90 olan hücre yalnız şans düzeyinde ve işaret beslemeden beslemeye dönüyor.
- **Tepki:** dokunulan desteklerin yarısı döndü (%40–64), hayalet seviyeler de aynı oranda döndü. Ön kayıtlı ölçüt (KEŞİF ve TEST'in ikisinde +5 puan, P ≥ 0,90) hiçbir ailede sağlanmadı.
  - P5: TEST +9,7 puan (P 0,96), KEŞİF −0,3.
  - W8: KEŞİF +9,3, TEST −6,5.
  - En istikrarlı iz D5 oldu: 10 besleme × dönem hücresinin 8'inde gerçek > hayalet, ama farklar +2…+12 puan ve hücre başına n 20–45. **C−** (iz), kural değil.

## Gözle görülen "tepki" nereden geliyor
Korku gecesi işlemlerinin %76–80'i zaten kazanıyor. Yani fiyat çoğu gece aşağı bir yere kadar inip dönüyor. Döndüğü yerin yakınında
neredeyse her zaman bir geçmiş dip bulunuyor: seviyelerin medyan uzaklığı 30–110 bp. Bu yüzden grafikte "destekten döndü" görünüyor.
Ancak aynı uzaklıktaki rastgele seviyeler de aynı sıklıkla "tutuyor".

## Hücre sayısı
6 aile × 2 pencere × 3 kural × 5 besleme × 2 dönem = 360 strateji hücresi, ayrıca 60 hayalet ve 60 tepki karşılaştırması.

## Hüküm
- Destekte limit girişi: **X**.
- Desteğe tepki: **X**; D5 gün dibi tepkisi **C−** iz.
- Oynatıcıda her işlemde D5, D5_2, P5 ve W8 çizgileri ve limitin dolup dolmadığı gösterilir (`research/xp_gelistir_20261119/src/oynatici_kur.py`).
