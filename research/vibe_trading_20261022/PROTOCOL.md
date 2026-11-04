# Vibe-Trading — çevrimdışı inceleme ve nedensel sınama

Ön kayıt: 2026-10-22; hiçbir strateji getirisi hesaplanmadan yazıldı.
Kaynak: https://github.com/HKUDS/Vibe-Trading
Sabit commit: 11cff3f3a2d89605c89148b03dcc2dd0fcfb60db.

## Amaç ve kapsam
Çerçevenin hazır sinyal örneklerinin yerel ForexSAI verisinde çalışabilirliğini,
geçmiş kararların gelecek barlardan etkilenip etkilenmediğini ve maliyet sonrası
sonuçlarını ölç. Bu bir LLM takımının geçmişteki bilgiyi gerçekten bilmeden
verdiği kararların doğrulaması değildir. Güncel LLM'ye eski tarih yazmak eğitim
verisi sızıntısını önlemez. Haber/web/broker araçları kapalı; çalışma çevrimdışı.
Canlı sistem, hesaplar, işlem kapıları ve bot ayarları değiştirilmez.

## Veri
Dört işlem sembolü NDX.INDX / GDAXI.INDX / XAUUSD / USOIL.FOREX.
Uzun 1h: ndx_gate_forge long_1h_utc, dax_1h (yalnız 2019+), pinbar XAUUSD/USOIL_1h
(yalnız src=broker; Yahoo vadeli fiyatları dışarıda). Ham 1m: output/islem_otopsi/_cache;
normalize_snapshot_clock ile 2026-07-28 öncesi −3h düzeltme, belirsiz geçişi atma.
Son dakika mumu eksik olabilir; son bar dışarıda. 5m/1h toplama sağ kenar etiketli,
yalnız tam dakika kapsamlı pencereler; eksik barlardan hayali OHLC üretilmez.
Uzun ve yakın veriler ayrı raporlanır, farklı fiyat kaynakları birleştirilmez.

## Sabit değerlendirme
- Hazır örneklerin parametreleri değiştirilmez. Uygun örnek listesi kaynak kod
  incelendikten sonra, getirilere bakılmadan EK-1'e yazılacak.
- Sinyaller yalnız kapanmış OHLCV öneki üzerinde çalıştırılır. Gelecek pertürbasyonu
  ve prefix tutarlılığı sınanır. Sağdan teyit gerektiren pivotlar geciktirilmeden
  geçmişe yerleştiriliyorsa orijinal örnek başarısız diye raporlanır.
- Giriş sonraki M1 açılışı (1m kapsamındaki deney) / sonraki 1h açılışı (uzun 1h
  taraması). Uzun 1h sonuçları M1 icra kartı değildir.
- Sinyal durumunu long/flat/short hedef pozisyon olarak uygula; yalnız BUY/SELL
  olay üreten örnekte karşıt olay gelene kadar tut. Tam semantik EK-1'de sabitlenir.
- Tek pozisyon/sembol/strateji. Masraf: proje otopsi sabitleri NDX 1,5; DAX 1,5;
  XAU 0,25; OIL 0,03 fiyat birimi tam spread + her dolum 0,1×spread kayma.
  Stres spread×1,5; kayma da aynı oranda. Gerçek tarihsel spread ve swap mevcut
  değil; sonuçlar tahmini maliyetli araştırma, canlı uygunluk kanıtı değil.
- Yeni giriş sonrasında aynı barın kapanışını giriş fiyatı olarak kullanma.
- Veri boşluğu veya hafta sonunu aşan açık işlemler boşluk sonrasındaki ilk açılışta
  kapanır (boşluktan önceki kapanışı geleceği bilerek seçme). Eksik yolun riski raporlanır.
- Uzun veri geliştirme <2024, sınama 2024+; yakın 1m verisi geliştirme <2026-09-01,
  sınama >=2026-09-01. Bölünmede açık pozisyon taşınmaz; yeni dönem kendi başına
  başlar. Isınma için önceki fiyatlar kullanılabilir, sonuçlar kullanılamaz.
- Hiçbir sonuçla parametre/strateji seçimi yapılmaz. Tüm denenmiş örnekler, başarısız
  ve desteklenmeyenler dahil raporlanır. Daha önce araştırmada görülen piyasa
  geçmişi olduğu için "hiç görülmemiş bağımsız veri" iddiası yok.
- Win rate + Wilson aralığı, işlem sayısı, net bp ve net R (kararda 2×ATR14 risk
  referansı; stop uygulanmadıysa açıkça belirt), toplam R, kapanmış işlem DD,
  yön/dönem dökümü, spread stresi. Gün-blok bootstrap 2000 tekrar.
- Kontrol: aynı dönem ve saatlerde yön işaretleri rastgele çevrilmiş aynı giriş/
  çıkış yolları (1000 tekrar); buy-and-hold ayrıca. Bunlar strateji seçimi veya
  canlı kapı değildir. Tüm örnekler için çoklu sınama Holm düzeltmesi.
- 150+ işlem, iki dönemde pozitif beklenti, maliyet dayanımı ve kontrol üstü katkı
  araştırma adaylığı için gerekli; M1 gerçek spread ve bağımsız ileri gölge yoksa
  hiçbir hücre LIVE olmaz.

## Deneme sayacı
Parametre optimizasyonu 0; kesin hazır örnek sayısı EK-1'de kaydedilecek.

## EK-1 — kaynak incelemesinden sonra, getirilerden önce sabit kapsam
Yedi bağımsız OHLC[V] SignalEngine örneği: technical-basic, candlestick, ichimoku,
volatility, seasonal, harmonic (yerleşik fallback), elliott-wave. Varsayılan
kurucular aynen; 0=FLAT, ±1=hedef yön (upstream BaseEngine hizalama semantiği).
Olay tarzı Ichimoku/harmonic/Elliott sinyalleri böylece genellikle bir bar tutulur;
karşıt sinyale kadar tutma eklenmez. Her biri uzun 1h ve yakın 5m'de dört sembolde
sınanır; technical-basic için uzun XAU/OIL hacmi eksik, bu iki hücre desteklenmez.
Toplam 7×4×2−2=54 performans hücresi; parametre optimizasyonu sıfır. Veri frekansı
aktarımıdır: günlük örneğin 20 barı 1h/5m'de 20 gün değildir; sonuç bu uyarlamaya ait.

Kalan 9 örnek kapsam envanterinde: minute-analysis işlem sinyali üretmiyor;
event-driven için PIT event_score, fundamental-filter için PIT bilanço,
options-strategy için opsiyon zinciri/kontratları yok; pair-trading için önceden
belirlenmiş hedge ve spread icrası yok; multi-factor portföy ağırlığı üretir (bu
tur tek sembol sinyal sınaması); chanlun/SMC ek bağımlılıkları ayrı inceleme.
cross-market-strategy dört CFD adını a_share varsayar ve tüm geçmişe sondaki
volatilite ağırlığını uygular: çoklu-sembol prefix testinde sayısal sinyal sızıntısı
aranacak, sızıntılı çıktıya performans puanı verilmeyecek.

Prefix denetimi: her sembolde yakın 5m ilk 800 bar, 12 sabit önek + desen
örneklerinde ilk 12 sıfır-dışı sinyal bitişi; kalan geleceği 5× fiyat / 3× hacim
ile değiştirme; geçmiş sayısal sinyallerin tamamını karşılaştır. Prefix'i
bozulan motor metriklere girmez. Büyük veri üretimi için ek erken/orta/geç
önek testleri; örneklem testi matematiksel ispat değildir.

## EK-2 — istatistik çözünürlüğü düzeltmesi (özet getirilere bakılmadan)
54 Holm testi için ilk eşik 0,05/54=0,000926. 1000 plasebo ile en küçük Monte Carlo
p değeri 1/1001=0,000999 olduğundan ilk eşik matematiksel olarak geçilemiyor.
Kontrol tekrar sayısı 10.000'e çıkarıldı (minimum p=1/10001); ana stratejiler,
eşikler, masraflar ve veri bölünmeleri değişmedi. Çalışmanın ilk çıktıları 1000'lik
geçici kontrol içerir; nihai summary.csv kaydedilen trades.csv'den bu düzeltmeyle
tekrar hesaplanır. Bu bir performansa göre kural seçimi değildir.
