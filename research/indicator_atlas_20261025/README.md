# Indicator Research Atlas — 25 October 2026

Bu paket, altın (`XAUUSD`), WTI petrol (`USOIL.FOREX`), DAX (`GDAXI.INDX`) ve Nasdaq 100 (`NDX.INDX`) için indikatör ve analiz yöntemlerinin kaynak araştırmasıdır. Yöntem adları İngilizce, Japonca ve Çince biçimleriyle korunmuştur.

## Buradan başlayın

- [ForexSAI / bot karşılaştırması](system_comparison/REPORT_TR.md): 120 kartın kullanım matrisi, aynı veriyle formül kıyası ve yerel model-girdi sözleşmesi denetimi.
- [Aranabilir çevrimdışı katalog](catalog.html): yöntem aileleri, kod uygulamaları ve TradingView yayınları arasında arama.
- [Araştırma raporu](REPORT.md): dört piyasaya veri uyumu, önemli kod farkları ve erişim sınırları.
- [120 yöntem ailesinin çalışma kartları](FAMILIES.md): hesap mantığı, veri ihtiyacı, uygulama ayrıntısı ve eşleşen kodlar.
- [1.480 kaynak uygulama kaydı](IMPLEMENTATIONS.md): dil, dosya, kaynak bağlantısı ve kayıt türü.
- [496 TradingView yayını](TRADINGVIEW_PUBLICATIONS.md): 24 konunun ilk sayfalarından keşfedilen yayınlar ve seçili açık-kod kontrolleri.
- [İlk araştırmadaki 239 resmî yardım sayfası](TRADINGVIEW_BUILTINS_239.md).
- [Kaynak ve lisans defteri](SOURCES_AND_LICENSES.md): 13 depo, sabit commitler ve yeniden dağıtım ayrımları.

`vendor/` altında 2.132 kaynak/belge dosyası yerel araştırma kopyası olarak bulunur; bunlardan 210'u Pine dosyasıdır. Sayılar aynı yöntemin farklı uygulamalarını ve yardımcı bileşenleri içerir. **1.480 farklı matematiksel indikatör veya doğrulanmış kazanç sistemi bulunduğu iddia edilmiyor.**

## Kod durumu

Dosyaların varlığı, SHA256 bütünlüğü ve kaynak satır bağlantıları kontrol edildi. Yabancı kütüphaneler kurulmadı, import edilmedi veya çalıştırılmadı. Böylece bu araştırma mevcut botun bağımlılıklarını değiştirmez. Derleme uyumu, sayısal doğruluk, bütün algoritmaların nedenselliği ve performansları ayrıca doğrulanmalıdır.

Paket yerleşik TradingView yardım kataloğunu, seçilen kamu yayınlarını ve seçilen kaynak depolarını kapsar. Tüm TradingView kütüphanesi, tüm geçmiş sürümler, bütün ülkelerdeki tüm yöntemler veya özel/davetli kodlar kapsamda değildir. Topluluk keşfinde sayfalama yapılmadı; aynı yayın kimliği tekrarları kaldırıldı. Açık-kod rozeti yalnız seçili detay sayfalarında doğrulandı. Bu kayıtların Pine kodu ayrıca indirilmiş gibi sunulmuyor.

`SOURCE_MANIFEST.json` her kaynak dosyasının hash bilgisini ve commitini içerir. `IMPLEMENTATIONS.json`, `FAMILIES.json` ve `TRADINGVIEW_DISCOVERY.json` makineyle işlenebilir dökümlerdir. Bunlar çalışma için gerekli trading verilerini içermez.

## Yeniden üretme

Yerel dosyalardan endeksi tekrar üretmek için yalnız Python standart kütüphanesi yeterlidir:

```sh
python3 research/indicator_atlas_20261025/build_catalog.py
python3 research/indicator_atlas_20261025/publish_catalog.py
```

Kaynakları yeniden indirmek ağ erişimi gerektirir ve varsayılan dalların o andaki yeni commitlerini toplar; eski snapshot'ı korumak istiyorsanız bunu aynı klasörde çalıştırmayın:

```sh
python3 research/indicator_atlas_20261025/collect_sources.py
```

TradingView keşif scripti `beautifulsoup4` kullanır; mevcut bilgisayarda hazırdı. Endeksleyici, indirdiği kodu çalıştırmaz. Kaynak snapshot'ları tam derlenebilir depo ihracı değildir; tam yapı için manifestteki sabit commitin bütün deposu gerekir.

## Arşiv

`indicator_atlas_sources.zip`, raporları ve lisans metni elde bulunan 11 deponun seçili kodlarını içerir. MyTT'nin tam lisans sürümü/metni ve CZSC'nin alt bileşen lisansları net olmadığı için bu iki deponun kodu dağıtım ZIP'ine alınmadı; kaynak bağlantıları ve metadata korunur. Bu iki klasördeki yerel araştırma kopyaları arşivin kapsamından daha geniştir. Arşiv içindeki HTML, bu iki kaynağın yerel bağlantısını açamaz; sabit upstream bağlantısı kullanılabilir.

## İşlem ve kanıt durumu

Bu bir kaynak envanteridir; fiyat verisi üzerinde strateji seçimi/backtest yapılmadı. Altın, petrol, DAX veya Nasdaq için bir kazanç oranı, optimal ayar ya da LIVE sonucu çıkarılmadı. Üretim sinyalleri, canlı bot, broker, uzak makine ve veritabanı değiştirilmedi. Kaynak katalog kaydı Evolution'a eklendi; genel defterde test yapılmadığı açıkça belirtildi.
