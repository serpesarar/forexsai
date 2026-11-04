# İkinci aşama — iki sabit birleşim

İlk10 tanımın sonuçları görüldükten sonra 2 Ekim 2026 tarihinde yazıldı.
VIX sakinleşmesi örnekleri zayıf; VIX artışı kontrolü15m/30m'de daha iyi,
H1 ilk yarıda zayıf. Yarı kâr-alma ve tam+1R hedef uç-gün bağımlılığını azaltıyor.
Bu iki mekanizmayı birleştiren yalnız iki tanım, yeni eşik/ızgara yok:

1. **HALF_RISING:** BASE şartları+önceki VIX değişimi>=0; yarıyı+1R'de kapat,
   yarı16:00'a, aynı ilk−1R stop. VIX_RISING ile aynı olaylar.
2. **TP1_RISING:** aynı giriş koşulları; bütün pozisyon+1R hedef/−1R stop,
   en geç16:00. VIX_RISING ile aynı olaylar.

Aynı M1/native veri, dönemler, maliyetler; değişmeyen BASE ve kendi VIX_RISING
kontrolüyle karşılaştır. Bütün veri zaten görüldü; yeni OOS değildir. Aşama1
10+aşama2 2=**12 toplam yapılandırma**. Kontrollerden öğrenildiği için
sonradan güçlü görünen FULL_TP1 veya bu birleşimleri 'başından beri ana hipotez'
diye sunma. Daha iyi risk dengesi daha fazla beklenen para demek değildir.
Canlı/gölge süreç kurulmaz; sonraki dokunulmamış veri ayrı gerekliliktir.
