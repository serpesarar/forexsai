# ME-11 sonuç: "dalgalı tepe" yapısından sonra risk (oynaklık ve düşüş derinliği), çoklu zaman dilimi

> Ön-kayıt: `PROTOCOL.md` (sonuçlar görülmeden yazıldı). Betik: `risk_testi.py` → `results/hucreler.csv`,
> `results/gelistirme_karar.csv`, `results/ozet.json`. Sonradan yapılan saat tanılaması (ön-kayıt dışı, kararı
> değiştirmiyor): `tanilama_saat.py` → `results/tanilama_saat.csv`.

## Ne yapıldı
- Yapı **mum sayısıyla** tanımlandı, zaman dilimine bağlı değil: kullanıcının 3 örneğinin (1h'te 138–276 mum) şekli
  NDX 5m/15m/30m/1h/4h ve DAX 15m/30m/1h/4h grafiklerinde 166/207/248 mumluk pencerelerde arandı (D1 = şekil benzerliği,
  her TF'nin en benzer %2'si). Yanına ME-10'un kural tanımı (D2 = K1, 207 mum) kondu. Her 23 mumda bir sorgu yapıldı.
- Ölçülenler, sonraki 23/69/115 mumda: gerçekleşen oynaklık (log RV), en derin düşüş (σ biriminde) ve 2σ'dan derin
  düşüş olasılığı.
- Kıyas: aynı geriye-dönük 207 mum getirisi × oynaklığı ondalık hücresindeki yapı-olmayan anlar (birincil); HAR +
  kaldıraç regresyonu artığı (ikincil). Takvim-ayı blok bootstrap, olay düzeyi, iki yarı, DAX, tek bakışlık doğrulama
  (2025-12 →).

## 1) Ham cevap: evet, yapıdan sonra risk yüksek
| seri | D1 sonraki 23 mum oynaklık / ortalama | en derin düşüş: yapı vs ortalama | P(düşüş ≤ −2σ): yapı vs ortalama |
|---|---|---|---|
| NDX 5m | 1,25× | −1,10σ vs −1,18σ | %15 vs %17 |
| NDX 15m | 1,68× | −1,90σ vs −1,05σ | %32 vs %15 |
| NDX 30m | 1,51× | −1,41σ vs −0,99σ | %19 vs %13 |
| NDX 1h | 2,01× | −1,81σ vs −0,96σ | %26 vs %13 |
| NDX 4h | 1,96× (6 olay) | −1,89σ vs −1,00σ | %27 vs %14 |
| DAX 15m / 30m / 1h | 1,20× / 1,45× / 1,24× | −1,24 / −1,41 / −0,76σ vs ≈ −0,95σ | %16 / %25 / %11 vs ≈ %12 |

## 2) Asıl soru: bunu şekil mi söylüyor, yoksa "zaten oynak ve düşmüştü" mü? → şekil bir şey katmıyor
- Aynı geriye-dönük getiri × oynaklık hücresiyle kıyaslanınca farkın büyük kısmı siliniyor (NDX 1h oynaklık
  2,01× → 1,23×; düşüş −0,85σ → −0,31σ, P 0,71).
- Ön-kayıtlı aile (NDX 60 hücre: 5 TF × 2 dedektör × 3 ufuk × 2 hedef): **4 hücre risk-artışı yönünde, 4 hücre de tam
  ters yönde geçti** (binom p 0,063 ikisi için de) → simetrik, sistematik etki yok. Bonferroni'yi tek hücre aştı
  (NDX 15m D1, oynaklık, 23 mum, +0,31 log, P 1,000). DAX: 0/48 (ters yönde 1). Kural dedektörü (D2) hiçbir TF'de
  oynaklık eklemiyor (fark −0,08…+0,07).
- **Ön-kayıtlı karar: C.** Yapıdan sonraki yüksek risk, bilinen oynaklık kümelenmesi ve kaldıraç etkisinin yansıması.
  Bu bilgi son ~200 mumun gerçekleşen oynaklığı ve getirisiyle zaten elde ediliyor.

## 3) Sonradan tanılama: saat etkisi (ön-kayıt dışı)
- 5m/15m/30m'de 23 mumluk adım gün içinde kayıyor, ileriye dönük oynaklık da güçlü biçimde günün saatine bağlı.
  Ters yönde geçen 4 hücre (NDX 5m D1) **saat artefaktı** çıktı: yapı sorgularının %39'u NY 18–20'de (kapanış
  sonrası sakin saatler). Saat eşlenince fark −0,17'den +0,01'e iniyor.
- Saat eşlendikten sonra yalnız **şekil dedektöründe NDX 15m ve 1h**'te ileriye dönük oynaklık fazlası kalıyor:
  15m +%23 / +%17 / +%14 (23/69/115 mum, P 1,00/0,99/0,99); 1h +%31 / +%36 / +%28 (P 0,99/1,00/0,99); 15m
  doğrulaması +%31 (9 olay, P 0,97).
- Karşı kanıt: aradaki 30m'de yok (+%1…+%5), DAX'ın hiçbir TF'sinde yok (−%3…+%9), kural dedektöründe yok,
  düşüş derinliğinde yok (NDX 15m −0,55σ, P 0,94; diğerleri karışık). Sonradan bulundu ve TF'ler arasında tutarsız.
  **Sınıf: aday.** Yeni veriyle ve ön-kayıtla yeniden sınanması gerekir (backlog).

## 4) Çoklu zaman diliminde tespit
- Yapı 5m'den 4h'e kadar her grafikte bulunabiliyor: D1 tanım gereği sorguların %2'sinde, D2 %3–5'inde yanıyor
  (NDX 5m %3,2, 15m %3,7, 30m %4,5, 1h %3,8; DAX %4–5). 4h'te 10 yılda yalnız 6 olay var, test için yetersiz.
- Son veride (2026-10-02 sabahı) NDX'in hiçbir TF'sinde yapı yok (benzerlik yüzdeliği %46–77). DAX 4h'te kural
  yanıyor (10-02 01:00); DAX 15m/30m şekil yüzdeliği %5–7, yani eşiğe yakın ama eşiği geçmiyor.

## Pratik anlam
- Risk yönetimi için bu yapıyı ayrıca aramaya gerek yok. Yapının "uyardığı" yüksek riskin neredeyse tamamı, son
  dönemin gerçekleşen oynaklığı ve son düşüşten okunabiliyor. Stop ve lot oynaklığa göre ayarlanmalı (panelde ATR
  merdiveni bunu yapıyor).
- Yön ME-09/ME-10'da zaten yazı-tura çıkmıştı; risk tarafında da şekle özgü, taşınabilir bir bilgi yok. Açık kalan
  tek aday, NDX 15m/1h şekil eşleşmesinden sonra oynaklığın %20–35 fazla olması (sonradan bulundu).
