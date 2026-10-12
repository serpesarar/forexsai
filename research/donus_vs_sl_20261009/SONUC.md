# Sonuç — "geri çekilip TP mi, doğrudan SL mi?" karar anı analizi (2026-10-09)

Ön-kayıt: [PROTOCOL.md](PROTOCOL.md) · `run.py --esik 0.5|0.3|0.7` · `results/`. Bot kararları, broker 1m,
D = SL yolunun yarısına (−0,5R) ilk değilen dakika; yalnız D'ye kadar kapanmış barlar.

## Olay sayısı ve taban
−0,5R'ye gelen 326 işlem: **A (döndü → TP) 110, B (SL) 216** → taban P(TP) %34.
"Her zaman D'de çık" net **−32,8R** (−0,10R/işlem). −0,3R: %44 TP, −36,4R · −0,7R: %25 TP, −42,0R.

## Hacim — kullanıcının sorusu
- Ham tick hacmi B'de düşük görünüyor (D dakikası medyan 196 vs 242; giriş öncesi 175 vs 213; iki yarıda tutarlı).
  **Ama bu saat etkisi:** aynı seans içinde fark yok (ABD seansı A 258 / B 256); Avrupa saatlerinde hacim düşük VE SL
  oranı yüksek (%75 vs ABD %61). Saatine göre düzeltilince D hacmi ×1,05 vs ×1,12 (AUC 0,54, yarılarda tutarsız).
- Hacim dinamiği hiç ayırmıyor: son 5 dk / önceki 10 dk oranı (A 1,01 / B 1,01, AUC 0,51), son 10 dk eğimi (AUC 0,50),
  aleyhte bacak / lehte bacak hacmi, aleyhte bacakta bar başı hacim yönü.
- Dakika dakika profil (D−20 … D+10): iki grup paralel; ikisinde de D dakikasında ~%10 sıçrama.

## Ayırt eden zayıf işaretler (iki yarıda aynı yön, q≈0,07)
| işaret | A (döndü→TP) | B (SL) | AUC |
|---|---:|---:|---:|
| ATR genişlemesi (D / giriş) | 0,99 | 1,03 | 0,59 |
| D barının kapanış konumu (aleyhte uca uzaklık) | 0,35 | 0,22 | 0,41 |
| son 3 bar alt-fitil (emilim) | 0,25 | 0,21 | 0,41 |
"Mum aleyhte ucundan geri kapanıyorsa ve oynaklık artmıyorsa dönme olasılığı biraz daha yüksek" — ama zayıf.

## Karar kuralı olarak — işe yaramıyor
- Tek özellik, bir yarıda seç → diğerinde sına: −11,7R / −3,1R (−0,3R: −13,3 / −4,6; −0,7R: −5,7 / −8,5).
- Lojistik (tüm özellikler): sınama AUC 0,55–0,60, plasebonun %95 üstü 0,58–0,60 sınırında; kural net −1,6…−18,1R.
- Neden: D'de çıkmak bir SL'de +0,5R kurtarır, bir TP'de ~1,23R kaybettirir → işaretlenenlerin ≥%71'i SL olmalı
  (taban %66). Bunun için AUC ~0,75+ gerekir; ölçülen 0,55–0,60.

## Hüküm
1m hacim ve gösterge dinamiğinde A/B ayrımı yok; ham hacim farkı seans etkisi. Geri dönüşü öngören tek iz mum
anatomisi (kapanış konumu/fitil) ve oynaklık genişlemesi — kâr ettirecek güçte değil. Defter IO-17.
Sonraki seçenek: MT5 tick verisinden tick-kuralı alım/satım dengesizliği (1m barda olmayan yeni bilgi) — ayrı aşama.

## Ek — tüm veriyle genişletme (`genis.py`, rapor `results/genis_rapor.txt`)
Veri: GERÇEK 300 olay (bot), SENTETİK 4.748 olay (bot benzeri pozisyon, saat başı, iki yön, sembolün gerçek risk/RR'si);
103 özellik = 24 bar + 56 gösterge (1m/5m/15m/1h RSI, EMA20/50/200 uzaklığı ve eğimi, MACD histogram ve değişimi,
Bollinger %b ve genişlik, Stochastic, ADX/DI, OBV eğimi, MFI, CMF, günlük VWAP, gün aralığı) + panel modelleri (son 30 dk
lehte/aleyhte) + VIX + 19 tick özelliği (MT5 kutusu, 28 Ağu+: 15/5/1 dk ve 30 sn tik sayısı ve tik-kuralı dengesi, 5 dk akış
ve yol, verimlilik, spread, 10 sn en büyük hareket, son 60 sn dipten sıçrama ve dibin yaşı). Tick geçmişi MT5'te
2026-08-28'den öncesine gitmiyor; tiklerde gerçek hacim ve alım/satım bayrağı yok (yalnız bid/ask).

| küme | n | aile | sınama AUC (ileri / geri) | plasebo %95 üst | kural net R |
|---|---:|---|---|---|---|
| gerçek | 300 | hepsi (84) | 0,52 / 0,53 | 0,58 / 0,59 | −12,9 / −4,1 |
| gerçek | 300 | gösterge (56) | 0,45 / 0,48 | 0,56 / 0,60 | −18,5 / −10,7 |
| gerçek tick dönemi | 52 | tick (19) | 0,52 / 0,45 | 0,70 / 0,67 | −2,1 / −9,4 |
| sentetik | 4.748 | bar (24) | 0,56 / 0,55 | 0,53 / 0,52 | +27,3 / +11,0 (taban "hep çık" +11,7 / +24,5) |
| sentetik | 4.748 | gösterge (56) | 0,52 / 0,52 | 0,53 / 0,53 | — |
| sentetik tick dönemi | 1.772 | tick (19) | 0,53 / 0,52 | 0,54 / 0,54 | +2,1 / −4,1 |

- Tek özellikte en güçlüsü sentetikte D mumunun kapanış konumu (AUC 0,46, her iki yarıda); sentetikte seçilen eşik botun
  gerçek işlemlerine taşınınca "bu olaylarda çık" −5,4 … −7,8R → taşınmıyor.
- ATR genişlemesi gerçek botta AUC 0,60 (tick döneminde 0,74, n=52) ama sentetikte TERS yönde (0,47) ve kural olarak negatif.
- Tick dengesizliği (son 1 dk) gerçek 52 olayda AUC 0,36 (aleyhte akış → SL) ama sentetik 1.772 olayda ayrım yok.
- Karar matematiği: −0,5R'de çıkmak, TP olasılığı p < 0,5/(1+RR) ≈ %29 iken doğru. Botun gerçek olaylarında p %33 (tutmak
  daha iyi), rastgele girişte %29 (başabaş) — bot girişleri rastgeleden biraz daha sık toparlanıyor.
**Hüküm (güncel):** 103 özelliğin hiçbiri, tek başına ya da birlikte, "geri çekilip TP" ile "doğrudan SL"yi kâr ettirecek
güçte ayırmıyor; tick verisi bilgi eklemiyor. Defter IO-17 güncellendi.
