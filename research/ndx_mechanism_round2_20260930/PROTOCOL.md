# Mekanizma türetme turu — 30 Eylül 2026

Bu tur önceki örneklerden türetilmiş **retrospektif** araştırmadır. 2025, 2026 ve Eylül sonuçları önceki çalışmalarda görüldü. Tarihsel sıraya göre seçim ve sınama tekrar edilir; Eylül yeni bağımsız holdout diye adlandırılmaz. Canlı bot/ayar/emir değişmez.

Kaynak fikirler: `ndx_five_gates_20260930` donmuş adayları, `trend_gate/FINDINGS.md` gerçek işlemleri, DAYCOMBO ve MOD-E kodu, `ndx_gate_forge/RAPOR.md` stres rejimi. Raporlanan başarı yeni kanıt sayılmaz; kazananlar kadar kaybedenler/elenen fırsatlar da ölçülür.

## Önceden sabitlenen beş türev

1. **D1 — Yönlerin birleştiği geri çekilme.** `efficient_pullback_30_efficiency_both` sinyali, son tamamlanmış M15 close>EMA20 ve EMA20 üç bar eğimi yönle aynıysa kabul. İki varyant: M15 / M15+H1 EMA50 hizası. Amaç trend kapısının yararını yerel toparlanma tetikleyicisiyle birleştirmek.
2. **D2 — Geri alınan seviyenin kabulü.** `failed_break_60_none_both`, eski sınırı geri aldıktan sonra 2 veya 5 dakika bekle. Aradaki **bütün kapanışlar** sınırın doğru tarafında kalsın; bekleme sonunda giriş sinyal kapanışından yönünde en fazla 0,5 ATR70 uzaklaşmış olsun. Sonraki M1 açılışında gir. Amaç tek mumluk geri dönüşü kalıcı kabulden ayırmak.
3. **D3 — Sabırlı ve fiyatı kovalamayan giriş.** D1'in M15 varyantı sinyalinden 3 veya 5 dakika sonra: aradaki aleyhte uç ≤1,28·ATR14·√bekleme; son fiyat sinyal kapanışından yönünde ≤0,5 ATR70 ilerlemiş olsun. Sonraki M1 açılışında gir. Karşılaştırmalar: hemen giriş, aynı süre kör bekleme, yalnız gürültü bandı, band+fiyat sınırı. Bu MOD-E'nin aynısı değildir; yeni birleşimdir.
4. **D4 — Stres sonrası teyitli toparlanma.** `failed_break_60_none_buy` VEYA `efficient_pullback_30_efficiency_buy`; kapalı M15 trendi yukarı. İki makro varyant: önceki nakit işlem gününün NDX getirisi ≤−%1,5 veya 5g ≤−%4; / 5g getiri/(20g günlük std·√5)≤−1. Yalnız önceki günler bilinir. BUY izinli; aynı anın SELL karşılığı da ölçülür. Amaç günlük dönüş fikrine gün içi toparlanma teyidi eklemek; sırf düşüşten sonra kör BUY üretmemek.
5. **D5 — Yol ve tetikleyici uyumu.** `variance_switch_30_quiet_both_core` ham olayları. Kırılım dalında son 120 **M1** gözlemle ölçülen VR5>1,2, ER60>0,2 ve 60dk hareket yönü işlemle aynı; dönüş dalında VR5<0,8 ve M15 yönü işlemle aynı. İki varyant: yalnız kırılım / iki dal. Amaç kısa VR penceresinin kararsızlığını azaltmak ve portföy doluluğunun tesadüfen seçtiği kazançları açıklamak.

Her ailenin 2 varyantı × 2 çıkış geometrisi = **20 aday tanımı**. CORE: SL=max(35,5·ATR70), TP=1,5R, 90dk. FIXED: SL110/TP80, 90dk. 3/5m aktarım, ablasyon, ters yön ve stres kontrolü ayrıca sayılır; yeni gizli ayar taraması yapılmaz.

## Seçim, kontrol ve yürütme

- Dönemler: 2025 H1 keşif; 2025 H2 ve düzeltilmiş Şubat–Mayıs 2026 kronolojik doğrulama; MT5 Mayıs–Ağustos ve Eylül yeniden sınama. Hepsi artık görülmüş tarihsel veri.
- Her ailede 4 aday arasından yalnız ilk üç dönemle seçim. ≥100 toplam karar, her dilimde ≥15, üç dilimde EV>0, gap stresi EV≥0 şartı. Uygun aday yoksa en yüksek en-kötü-dilim EV'si sadece inceleme için seçilir; başarısız seçim durumu korunur.
- Karar kapalı mumla, gerçek UTC; cache 2026-03-08 öncesinde +60dk. ATR/istatistikler kapalı M1'den; tamamlanmış M15/H1, tazelik ve aradaki her dakikanın bulunması zorunlu.
- BUY ask / SELL bid; çıkışta ters kotasyon, 0,2 puan/fill; stop gap'i kötü açılış, belirsiz TP+SL stop önce. Gerçek Dukascopy ask OHLC; MT5 kaydedilen spread. Geometri gecikmiş **yeni giriş** anında sabitlenir, sinyalin eski riskinden kullanılmaz.
- NY03:00–15:30, Pazartesi–Perşembe; 15:55 flat. Her tanım tek pozisyon, ≥10dk ara. Eş zamanlı tüm öneriler ayrı portföyde sabit D1→D5 önceliğiyle toplam tek pozisyon.
- Split sınırına taşan sonuçlar purge edilir. Boşluklar ayrı etiketlenir, hepsini en az −1R yapan stres raporlanır.
- Kabul edilen, reddedilen ve kapısız **aynı ana strateji** ayrı ölçülür. Seçilen EV artışı kadar toplam R ve kaçırılan kazanç da gösterilir. Aynı günün gelecekteki ortalaması giriş özelliği veya seçim ölçütü olmaz.
- Plasebo: dönem/saat/yön içindeki ana olaylarda aynı sayıda rastgele kabul, tek pozisyonla 300 tekrar. Doluluk: önceki portföyün sıraya alma etkisi nötr rastgele boşluk takvimleriyle ayrıca karşılaştırılır. Bunlar geçmiş etiketli tanısal kontrollerdir, gelecekte görülen sonuç kullanılmaz.
- Gün bloklu bootstrap, %95 EV aralığı; hacim ≥150, pozitif EV ve bootstrap oranı≥%90, iki yarı pozitif, maliyet stresi, sonraki M1+spread, tek pozisyon. Bar kartı yeterli olsa bile bu tur geçmiş sonuçlardan türetilmiştir ve actual shadow execution/sonraki gerçekten yeni dönem beklenir.
- Maliyet stresleri ×1,5 ve ×3 spread, 1 puan/fill kayma, ek 1dk giriş gecikmesi. 1/3/5m aynı yol olduğundan bağımsız üç deney değildir. D2/D3 beklemesi her zaman M1 dakika süresidir; z/VR pencereleri M1 olarak korunur.

Kod ve protokol SHA256 sonuç dosyasında saklanır. Fiilen ölçülen bütün varyant/ablasyon/stres/aktarım sayısı raporlanır; seçilen 5 için çoklu hipotez düzeltmesi tek başına tüm geçmiş taramayı temizlemez. LIVE önerisi çıkarılmaz.
