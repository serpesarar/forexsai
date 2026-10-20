# Ön-kayıt — Sıkışma (SQZ) filtresi derin sınama (2026-10-20)

Kullanıcı: sıkışma filtresini kullanılabilir olana kadar araştır; olabildiğince çok örnek, kanıt, farklı algoritma.
Defter: **B14** (SQZ ATR14/ATR100 ≥1,00, GÖLGE, B — plasebo yalnız 1,00'da p=0,043; Ç3 negatif;
`analyst_reports/sikisma_filtresi_denetimi_2026-08-28.md`). Kural 2026-08-28'de donduruldu → **08-28 sonrası bot
işlemleri hiç seçimde kullanılmamış ileri dönemdir.** IO-20/E24: çok özellik içinden seçim → max-istatistik zorunlu.
Ön bilgi (bu oturum, `ndx_sl_zinciri_20261020`): tüm bot NDX ailelerinde SQZ<1 engeli +5,05R, yarılar +8,27/−3,22.

## Hipotez
H1 (botun iddiası): sıkışık piyasada (kısa vadeli oynaklık uzun vadeliden düşük) açılan girişler daha kötü sonuçlanır,
çünkü sinyali doğuran kıpırtı likidite fitilidir. Özellikle **momentum** tipi girişlerde beklenir.

## Algoritmalar (hepsi yalnız KAPANMIŞ 1m barlarla, karar anı)
- A1 `atr_14_100` = ortalama TR(14) / ortalama TR(100) — botun tanımı.
- A2 `atr_5_60`, A3 `atr_30_240` — farklı ufuk çiftleri.
- A4 `rv_14_100` = 1m getiri std oranı (TR değil).
- A5 `rng15_atr100` = son 15 dk yüksek−düşük / ATR100.
- A6 `bbw5_pct` = 5m Bollinger(20,2) genişliğinin son 288 bardaki (24 s) yüzdeliği.
- A7 `ttm_sqz` = 5m BB(20,2) Keltner(20, 1,5×ATR) içinde mi (0/1).
- A8 `atr14_seas` = ATR14 / aynı UTC dakika-diliminin önceki 20 iş günü medyan ATR14'ü (gün-içi U-şeklini arındırır).
- A9 `vol_14_100` = tick hacmi ortalaması oranı (14/100).
- A10 çok değişkenli: A1–A9 + saat → lojistik regresyon ve gradyan artırma, kronolojik yürüyen doğrulama (eğitim
  yalnız geçmiş), çıktı = engelleme olasılığı; eşik eğitim dönemindeki en kötü %40.
Eşikler: oranlar için {0,80, 0,90, 1,00, 1,10}; yüzdelik/mevsimsel için alt {%20, %30, %40} dilim; ikili için 1.

## Veri kaynakları (örnek sayısını çoğaltmak için)
- S1 bot gerçek işlemleri, tüm semboller, 06-30 → 10-20 (gerçek R). **S1-F = 08-28 sonrası (ileri, birincil).**
- S2 botun engellenen NDX SELL/BUY sinyalleri (kutu `gate_skipped`, 949 olay) — bot geometrisiyle simüle.
- S3 panel modeli NDX sinyalleri (753) — simüle. S4 decider NDX kararları (451) — simüle.
- S5 DAYCOMBO kuralı 2025 Dukascopy'de birebir (`canli_kart_20261009/daycombo_oos.py`, ~195) — simüle.
- S6 genel momentum olayları NDX 2025-01 → 2026-10: 5m kapanış 12-bar tepe/dibini gövdeli mumla kırar → kırılım
  yönüne giriş (M) ve tersine (R, ortalamaya dönüş). S7 aynısı DAX, petrol, altın (varsa 1m).
- S8 plasebo piyasa: saat başı rastgele yönlü giriş (sinyal yok) — SQZ'nin sinyalden bağımsız geometri etkisini ölçer.
Simülasyon: sinyalden sonraki 1m açılış + spread (NDX 1,5 puan; diğerleri sembol tipik spread), risk = fiyat×%0,373 (NDX
bot medyanı) / sembolde bot medyanı, RR 0,73, aynı barda iki bariyer → SL, 360 dk tavan.

## Ölçü ve geçme
Her (kaynak × algoritma × eşik): engellenen ve kalan ort R, kurtarılan R = −Σ engellenen R, gün-blok %95, kronolojik
4 çeyrek, **saat-eşli plasebo** (aynı UTC saatinden aynı sayıda rastgele olay engelle, 2.000), max-istatistik (tüm
algoritma×eşik içinde en iyi kurtarılan R'nin dairesel kaydırma boş dağılımı).
**"Kullanılabilir" (gölge→kart adayı) ancak hepsi:**
1. S1-F (ileri bot) kurtarılan R > 0 ve gün-blok P(>0) ≥ %90,
2. S1 tüm dönemde 4 çeyreğin ≥3'ü ≥ 0 ve saat-eşli plasebo ≥ %90,
3. en az iki bağımsız kaynakta (S2–S7) aynı işaret ve birinde %95 alt sınır > 0,
4. seçim düzeltmeli p ≤ 0,10 (yalnız S1 üzerinde çok algoritma denendiği için).
Geçmezse: "kullanılamaz" ve neden; hangi alt kümede (aile/yön/sembol) umut var, o da ön-kayıtsız keşif olarak ayrı.
Bot koduna dokunulmaz; geçen kural olursa canlıya alma kartı (2. KURAL) ayrı adım.
