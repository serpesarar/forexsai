# FAZ 4 — Modelleme (NOM, 2026-11-13)

Kod: `src/faz4_train.py` (`main`, `compare`). Çıktı: `results/oos/<ufuk>_<yön>_<geom>.parquet` (WF OOS tahminleri),
`results/faz4_metrics.csv` (40 hedef × 7 kat + havuz), `results/faz4_compare.json`, grafikler `results/plots/dev_reliability_*.svg`.
Şema: Faz 3 (genişleyen WF, arındırma + 1 gün ambargo, iç kalibrasyon, final kilitli). Değerlendirme ızgarası 15 dk.

## Tabanlar
1. **İklim tabanı (asıl rakip):** eğitim katındaki sınıf oranları × NY saati (24 kova, az örnekli kova büzülür).
2. **Basit kural:** H1 EMA50 tarafı × M15 RSI14 kovası (<30/30–70/>70) × saat → kova oranı.
3. **ndx_reflex_engine mom_cont:** yeniden koşulmadı — sızıntısız sürümü defterde zaten kanıtlı olarak eksi (GF-13/E16:
   −0,08R, P(EV>0) %13). Olay-tabanlı bir dedektör olduğundan "her an" olasılık sorusunun rakibi değil.

## Ana model
LightGBM çok-sınıflı (TP/SL/zaman), **yön başına ayrı**, 132 özellik, sabit parametre (arama yok), erken durdurma
kalibrasyon kümesinde, sınıf başına isotonic + normalize. 40 hedef (4 ufuk × 5 geometri × 2 yön) × 7 kat = 280 eğitim.

## Sonuçlar — WF havuzu (2023-01 → 2026-04, geliştirme)

| Ufuk | Brier becerisi (model, saat-iklimine göre) | Brier becerisi (kural) | Log-loss becerisi | AUC TP: model / iklim / kural |
|---|---|---|---|---|
| 15 dk | **+0,059** | +0,002 | +0,049 | 0,699 / 0,669 / 0,671 |
| 1 saat | **+0,015** | −0,004 | +0,011 | 0,705 / 0,698 / 0,696 |
| 4 saat | **+0,011** | −0,002 | +0,004 | 0,728 / 0,724 / 0,725 |
| seans sonu | **−0,001** | −0,001 | −0,025 | 0,657 / 0,666 / 0,665 |

Kat başına (Brier becerisi, 10 hedef ortalaması):

| Ufuk | 2023H1 | 2023H2 | 2024H1 | 2024H2 | 2025H1 | 2025H2 | 2026Q1 |
|---|---|---|---|---|---|---|---|
| 15 dk | 0,075 | 0,074 | 0,059 | 0,051 | 0,053 | 0,043 | 0,063 |
| 1 saat | 0,002 | 0,007 | 0,016 | 0,012 | 0,021 | 0,032 | 0,019 |
| 4 saat | −0,032 | 0,007 | 0,017 | 0,009 | 0,029 | 0,034 | 0,025 |
| seans | −0,056 | −0,001 | 0,001 | −0,001 | 0,011 | 0,036 | 0,018 |

280 kat×hedef hücresinin 44'ünde beceri < 0 (çoğu ilk kat ve seans ufku: az eğitim verisi).

**Okuma:**
- Model **gerçek ama küçük** bir bilgi taşıyor ve bu bilgi büyük ölçüde **oynaklık/zamanlama** bilgisi: 15 dk'da beceri
  en yüksek (barierlere ulaşma hızı spread'e göre çok değişken), en çok Asya seansında (+0,11), en az NY öğlesi/açılışında
  (+0,01/+0,02; 1 s'te NY açılışında **negatif**). Yön bilgisi taşıyacak RSI/EMA/seviye özelliklerinin katkısı küçük
  (Faz 2), kural tabanı saat-iklimine **hiçbir şey eklemiyor**.
- Beceri eğitim verisi arttıkça büyüyor (1 s: 2023H1 0,002 → 2025H2 0,032) — veri kısıtlı bir öğrenici.
- **Seans sonu ufku iklimi yenemiyor** (kat başına ~1.400 satır; aşırı uyum). Bu ufukta model kullanılmamalı (bkz. Faz 5).

## Kalibrasyon (reliability, WF havuzu)
Ondalık kovalarda tahmin ≈ gerçekleşen, monoton. Örnek 1 s LONG 1/1: (0,038→0,060), (0,129→0,138), (0,215→0,232),
(0,268→0,277), (0,320→0,317), (0,377→0,370), (0,450→**0,414**). 4 s LONG 1/1 üst kova 0,501→**0,449**. Yani üst uçta hafif
**aşırı güven** (~3–5 puan), alt uçta hafif düşük tahmin. "%45 dediğinde ~%41–45 tutuyor." Grafikler:
`results/plots/dev_reliability_{15m,1h,4h,session}.svg` (model turuncu, saat-iklimi gri).

## Karşılaştırmalar (`faz4_compare.json`)
- **Yön-koşullu tek model** (1 s 1,5/1, long+short birlikte, yön bayrağı): Brier long 0,5191 / short 0,5226 vs ayrı modeller
  0,5231 / 0,5259 → tek model **biraz daha iyi** (~%0,7). Ön kayıt ayrı modeli ana model seçtiği için üretimde değiştirilmedi;
  v2 adayı (backlog).
- **XGBoost** (1 s 1/1 long, aynı katlar): kat Brier'leri LightGBM ile ±0,002 içinde (7 katın 4'ünde LGB, 3'ünde XGB
  biraz iyi) → mimari farkı yok, sınır veride.
- **P2 karıştırılmış-etiket plasebosu** (gün-blok, 20 tekrar, 3 son kat): gerçek beceri **+0,0183** (katlar 0,008 / 0,016 /
  0,031); plasebo p95 **−0,0003** (tümü negatif) → becerinin şans olmadığı kanıtlı.
- **Derin modeller (TCN/LSTM/Transformer):** ortamda torch yok; ön kayıt kuralı "ancak boosting tabanı geçerse" idi —
  boosting'in saat-iklimine üstünlüğü 1 s'te +0,015 Brier mertebesinde ve yön bilgisi neredeyse yok; derin modelin bu
  veride (5 yıl, tek enstrüman) anlamlı ek bilgi bulacağına dair gerekçe yok. **Denenmedi, bırakıldı.**
- **Ensemble/stacking:** XGB ≈ LGB, aynı özellik bilgisi → anlamlı iyileşme beklenmez, yapılmadı.
