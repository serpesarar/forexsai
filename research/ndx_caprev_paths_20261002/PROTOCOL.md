# CAPREV — olay zamanı ve kâr taşıma mekanizması

2 Ekim 2026. Karşılaştırılan diğer `ndx_gate_forge/NIHAI_RAPOR.md`, önceki
`ndx_synthesis_20261002/NIHAI_RAPOR.md` içinde zaten denetlenmiş rapordur.
Bu yeni tur eski 22 denemeyi yeniden keşif diye saymaz. Aşağıdaki tanımlar
sonuçlarından önce sabittir; sonuçtan sonra eşik seçilmeyecek.

## Sabit beş yeni varyasyon

Taban: önceki nakit seans NDX getirisi<=−1.5% veya5 seans<=−4%; önceki
VIX>=18.4. Pzt–Per NY03:00–15:00 ilk önceki RTH dibi-altı tam kapanış;
sonraki yürütme barı açılışında BUY. Stop=önceki20 nakit getiri std×giriş ask.
TP yok, NY16:00 açılışında kapat; günde bir net pozisyon.

1. **P1 FRESH_CROSS:** zaten altında olmak yeterli değil; aynı gün ve ardışık
   tam kapanış önceki seviyenin üzerinde/eşitken yeni kapanış altına geçmeli.
   03:00–15:00 ilk böyle olay. Önceki kapanış da03:00 sonrası olsun.
2. **P2 CASH_ONLY:** yalnız09:30–15:00 arasında ilk dip-altı kapanış. Başka
   trend/teyit şartı yok. Açılış likiditesinde olay farklı olabilir.
3. **P3 FAIL_10:** taban girişini koru. Giriş10:00'dan önceyse10:00'a kadar
   tamamlanan en son tam mum kapanışı önceki RTH dibine<= ise10:00 açılışında
   kapat; üzerinde ise16:00'a taşı. Giriş>=10:00 ise taban çıkışı. Stop her zaman etkin.
4. **P4 HALF_RUNNER:** taban giriş/stop. Başlangıç pozisyonunun yarısını+1R
   hedefte kapat, kalan yarıyı aynı ilk stopla16:00'a taşı. Breakeven/trailing yok.
   Aynı net pozisyonun kısmi çıkışı; toplam başlangıç riski tabanla eşit.
5. **P5 VIX_COOLING:** taban olay yalnız önceki VIX kapanışı bir önceki nakit
   seans VIX kapanışından düşükse. Şok seviyesi yüksekken korkunun gevşemesi
   ile yeni hızlanmasını ayırır; sadece tamamlanmış günlük veri.

Kontroller: BASE, ALREADY_BELOW (03:00 sonrası ilk uygun mum zaten dip altındaysa),
FULL_TP1 (tam pozisyon+1R hedef/−1R stop), ALWAYS_10 (erken girişleri şartsız10:00'da
kapat), VIX_RISING (önceki VIX artmış/eşit). Toplam **10 yapılandırma**.

## Veri ve doğrulama

Yeni ham veri çekilmeyecek. Yeni dokunulmamış gün henüz yok; bütün sonuçlar
**retrospektif**. M1 yürütme: mevcut saat onarılmış MT5/cache ve2025 Dukascopy;
M1/M5/M15 tam tetikleyiciler, ortak M1 fiyat yolu. Uzun native15m(2023+),
30m(2021+) veH1(2016+) OHLC ayrıca, 2026-07-15 öncesi. Native barların broker
etiketi NY+7 saatten UTC'ye dönüştürülür; gün içi volatilite saatleri ve M1
çakışması denetlenir. Doğrudan üst-zaman dilimi sonraki bar açılışı, **next-M1
icra diye sunulmayacak**. Native yıllık bulgular aynı sağlayıcının örtüşen fiyatlarıdır.

M1/15m/30m önceki RTH seviyesi tam09:30–16:00 (390/tf bar), eksikse olay yok.
H1 09:30 sınırını çözemez:09:00–16:00 min yalnız gerçek RTH dibinin alt sınır
yaklaşımıdır; ayrı `H1_LEVEL_PROXY` etiketiyle raporlanır, birebir doğrulama sayılmaz.

Native verinin spreadi bilinmiyor: giriş ve çıkışta ayrı0.6 baz puan=0.00006
oransal fiyat payı (toplam1.2bp), ayrıca her tarafta0.2 puan kayma. Bu varsayım,
gerçek bid/ask değildir. M1'de Duka gerçek ask/bid, direktMT5 kayıtlı spread,
cache1.3 puan varsayımı. Ana, spread3, kayma1, +1 yürütme barı gecikme
kontrolleri. Giriş gecikmesinde olay bilgisi ve stopun günlük-vol ölçeği korunur;
fiyat yeni dolumdan hesaplanır. Dönemler arası taşan işlem etiketi dışarıda.

Ana 2025ilk/ikinci,2026Şub11–May15,May20–Ağu28,Eyl1–Eki1 bölmeleri; uzun
veride2016–20/2021–23/2024–25/2026 ve yıl yıl sonuç. Beş varyasyon için
gün-eşleştirmeli toplam-R farkı, etkilenen günler, kronolojik yarılar, gün
bootstrapı ve5-hipotez düzeltmesi. Bu düzeltme önceki turların seçimini silmez.
En iyi1/3/5 olay çıkarma denetimi; tek açık toplam pozisyon; örnek ilk kazanan
ve kaybeden çizilir. Canlı kod/Windows yapılandırması/emirler değişmez.

Karar kuralı: daha iyi görünen varyasyonu LIVE sayma. Final kural için>=150
çözülmüş uygun olay, gerçek yürütme ve yeni dönem doğrulaması gerekir.
