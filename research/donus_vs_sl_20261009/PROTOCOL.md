# Ön-kayıt — "geri çekilip TP olacak mı, doğrudan SL mi?" karar anı analizi (2026-10-09)

Kullanıcı: işlem aleyhe döndüğünde iki tip var — (A) geri çekilir, sonra TP olur; (B) doğrudan SL'ye gider.
O anda hacim ve göstergelerin dakika dakika değişimiyle (ör. "hacim 450'den 300'e düştü") bu ikisini önceden
ayırt etmek istiyor. Defter: IO-03 (hacim genelde SL/TP'yi ayırmıyor — ama karar anına koşullu değildi),
IO-07/M9 (erken çıkışlar net negatif), LESSONS "dwell-dodge 24 varyant kanıtsız, sürünenlerin %31'i toparlıyor"
(zaman/fiyatla; hacim dinamiği yoktu).

## Karar anı (D)
İşlem sırasında barın aleyhte ucu ilk kez **−0,5R**'ye (SL yolunun yarısı) değdiği 1m bar; D KAPANDIĞINDA bilinenler.
İkincil: −0,3R ve −0,7R. D, çıkış barından önce olmalı (aynı dakikada SL'ye düşenler dışarıda, sayılır).
Etiket: gerçek sonuç TP (A) / tam SL (B); BE/iz/diğer çıkışlar dışarıda. Karar başına ilk bacak.

## Özellikler (yalnız D'ye kadar KAPANMIŞ barlar; yönle işaretli)
Hacim (ham tick + saatine göre): giriş öncesi 60 dk ort, son 5 dk ort, önceki 10 dk ort, son5/önceki10 oranı, D barı,
son 10 dk eğim, son 10 dk en büyük (mevsimsel), lehte bacak (giriş→en iyi nokta) vs aleyhte bacak (en iyi nokta→D)
bar-başı hacim oranı, aleyhte bacakta düşen/yükselen bar başı hacim (log2).
Fiyat/hız: D'ye kadar en iyi nokta (TP'nin kesri — "önce TP'ye yaklaştı mı"), girişten D'ye dk, en iyi noktadan D'ye dk,
düşüş hızı (R/dk), son 10 dk aleyhte bar sayısı, en büyük aleyhte gövde/ATR, son 3 bar alt-fitil (emilim), D barının
kapanış konumu, ATR genişlemesi (D/giriş), SL'ye kalan mesafe/ATR, giriş öncesi yapı ucu kırıldı mı.
Gösterge: RSI 1m ve 5m (yönle), 1m EMA20 uzaklığı/ATR, 5m EMA20'nin altına kapanış.

## Değerlendirme
1. Özellik başına A vs B: medyanlar, AUC, permütasyon p, BH q, iki kronolojik yarıda aynı yön.
2. Çok değişkenli: lojistik regresyon (L2, numpy), 1. yarıda eğit → 2. yarıda AUC ve tersi; plasebo = eğitim etiketleri
   karıştırılarak 200 kez.
3. Karar kuralı: "D'de koşul varsa D kapanışında çık" — net R = Σ(R_D − R_sonuç), 1. yarıda seç → 2. yarıda ölç.
   Taban: "her zaman D'de çık".
4. Sayısal profil: D'den −20 … +10 dk ham hacim medyanı (A vs B) + örnek işlemlerin dakika dakika hacim dizileri.
Geçme: 2. yarıda AUC ≥ 0,60 ve plaseboyu aşma VE kural net R iki yönde de > 0. Saniye/tick verisi bu aşamada yok
(Supabase 1m); 1m'de sinyal varsa kutudan MT5 tick verisiyle ikinci aşama.
