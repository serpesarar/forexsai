# Nasdaq rapor sentezi — sonuç öncesi sabit protokol

2026-10-02. Karşılaştırılan kaynaklar: `ndx_gate_forge/RAPOR.md` (TUR2 dahil),
`ndx_mechanism_round2_20260930/RAPOR.md` ve ilk beşli portföy.
Bütün 2025–2026-09-30 geçmişi daha önce görülmüştür. Bu turdaki tarihsel
bölmeler bağımsız OOS değildir. Sonuçlara bakarak eşik/öncelik değiştirilmeyecek.

## Beş sabit hipotez

1. **H1 seçici stres SELL vetosu:** önceki nakit seans getirisi <=−1.5% veya
   beş seans getirisi <=−4% VE fiyat önceki tam RTH seansının dibinin altında.
   Kontrol: K5, stresli günlerin bütün SELL işlemlerini engellemek.
2. **H2 saat-normalize hacim vetosu:** son tamamlanmış M5 tick hacmi hem önceki
   20 M5 ortalamasının hem aynı NY saat diliminin önceki 20 gözlem medyanının
   >=1.5 katı. Saat medyanı için en az 10 geçmiş gözlem, veri kaynağı değişiminde
   sıfırlama. Kontrol: yalnızca ham 1.5 kat hacim vetosu. Eksik özellik veto üretmez.
3. **H3 yalnızca şokta bekle:** H2 koşulu varsa üç dakika bekle; bu arada ters
   ekstrem hareket <=1.28*ilk ATR14*sqrt(3) ve son kapanışın yönlü ilerlemesi
   <=0.5*ilk ATR70 ise yeni M1 açılışından gir. Şok yoksa ilk giriş korunur.
   Kontrol: aynı beklemeyi bütün sinyallere uygulamak. Bekleyen niyet sermaye
   işgal etmez, oluşan girişler portföyün sabit öncelik sırasına tabidir.
4. **H4 seçici uzama BUY vetosu:** önceki nakit kapanış MA200'den >%10 yukarıda
   VE fiyat son kesintisiz 240 M1 aralığının üst %20'sinde ise BUY engellenir.
   Kontrol: K6, günlük uzama olan bütün BUY işlemlerini engellemek.
5. **H5 stres sonrası dip geri alımı BUY:** H1'in stres koşulunda, önceki tam
   RTH dibinin altından üstüne kapanış geçişi, son 15 M1 dip penetrasyonu en az
   0.5*ATR70, CLV>0.2. Tamamlanmış mumdan sonra giriş. Kontroller: stres şartı
   olmadan aynı BUY, yalnızca stressiz BUY ve aynı stresli olayı SELL yapmak.
   TP80/SL110, 90 dakika. Bu yeni giriş portföy vetolarıyla aynı işlem evreni değildir.

H1–H4, daha önce dondurulan beşli portföye ayrı ayrı uygulanır: opening_break,
exhaustion SELL, sweep SELL, variance_switch, failed_break BUY; aynı öncelik ve
fast/core/slow stop-hedef geometrileri korunur. Ayrıca H1+H2+H3+H4 birleşimi
önceden belirlenmiş tanısal kontrol olarak çalıştırılır (H2 şoku veto ettiği için
birleşimde H3 beklemesi fiilen etkisizdir; toplamsallık varsayılmayacak).

Toplam **14 yapılandırma**: bir taban, dört ana veto/bekleme, dört kontrolleri,
bir birleşim, H5 ve üç kontrolü. 1/3/5 dakikalık tetikleyiciler aynı M1 işlem
yolu üzerinde kontrol edilir; bağımsız veri değildir. Beş tarih bölmesi:
2025 ilk/ikinci yarı, 2026 Şubat11–Mayıs15, Mayıs20–Ağustos28, Eylül1–29;
Eylül30 ayrıca önceden görülmüş ek gün. Yeni veri alınabilirse Ekim1 yalnızca
protokol sabitlendikten sonra değerlendirilir. Tek yeni gün yeterli doğrulama değildir.

## Yürütme ve ölçüm

Next-M1-open, BUY ask/SELL bid, ters kotasyondan çıkış, kayıtlı spread,
her tarafta 0.2 puan kayma; tek açık pozisyon, girişler arası 10 dakika,
NY03:00–15:30 Pazartesi–Perşembe, 15:55 kapanış. Spread3, kayma1 ve +1M1
gecikme stresleri ayrıca; ana sonuçta 1.5 ve 3 kat spreadi eşik seçimi için kullanma.
Veri boşluğu kapanışları görünür ve hepsi en az −1R sayılan alt sınır raporlanır.
USD kârı ileri sürülmez; R başlangıç riskine göre simülasyon ölçüsüdür.

Ana ölçü veto sonrası **tek pozisyonlu toplam R farkı**, etkilenen gün sayısı,
gün bloklu eşleştirilmiş bootstrap ve dönemler arası işaret tutarlılığıdır.
Sıfır etkili günler atılmaz; çoklu deneme düzeltmesi beş ana hipotez için raporlanır,
ancak daha önceki binlerce denemeyi temizlemez. Küçük örneklem ve aynı veri
üzerinden geliştirme nedeniyle başarılı görünenler de araştırma/SHADOW adayıdır.
Canlı kod, Windows yapılandırması ve emirler değiştirilmeyecek.
