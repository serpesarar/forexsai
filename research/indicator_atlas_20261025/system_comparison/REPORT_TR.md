# ForexSAI ve bot, indikatör atlasının ne kadarını kullanıyor?

Tarih: 25 Ekim 2026. İnceleme: mevcut yerel kaynak kodu, doğrudan çağrı yolları ve yerel model dosyaları. Windows'ta çalışan süreçler, gizli yerel config, Railway ortamı ve dağıtımdaki model hash'leri sorgulanmadı. Bu nedenle aşağıdaki sayılar **kodda bağlı kullanım** içindir; bugün canlıda kesin açık olan gösterge sayısı değildir.

## Sayısal sonuç

| Kapsam | Sonuç | Sayımın anlamı |
|---|---:|---|
| Atlasın 120 kartından sistemde karşılığı bağlı olanlar | **34** | Karar hesabı, ML girdisi, güven düzeltmesi veya karar bağlamı; bazı kartların yalnız bir alt yöntemi mevcut |
| Backend/panel tarafında karşılığı bağlı olanlar | **32** | Ana gösterge hesapları + SMC, formasyon, hacim ve bağlam servisleri |
| Botun kendi yerel hesap/karar dalları | **9** | Backend'den aldığı hazır sinyalin içindekiler ayrıca buraya kopyalanmadı; dallar config/scope koşullarına bağlı |
| Claude Decider'a hesap/bağlam olarak verilenler | **9** | Kanal, EMA, ATR, ADX, pivot, hacim ve makro bağlamı; ayrı ayrı kârlı sinyal sayısı değil |
| Genel EMEL/Pulse hesaplayıcısının klasik gösterge aileleri | **12** | Williams %R dahil; bazıları sadeleştirilmiş formül |
| Botun `compute_all` kayıt modülünün klasik aileleri | **10** | 29 alan üretir; tüm alanların emir kararında kullanılması anlamına gelmez |

**32 + 9 + 9 toplanmaz:** aynı EMA, ATR, kanal vb. birden fazla bileşende bulunur. Birleşik atlas karşılığı 34'tür. EMA20/50/200 üç farklı indikatör ailesi sayılmadı. Wilder yumuşatma ayrı bir bağımsız sinyal sayılmadı. EXPMA/TAQ gibi başka ailelerin takma adı olan kartlar sayıyı büyütmedi.

34 kart, 34 eksiksiz TradingView scriptinin port edildiği anlamına da gelmez. Örneğin “OBV/PVT/ADL” kartında OBV var; PVT ve ADL'nin aynı kararda çalıştığı iddia edilmiyor. “Gold real-yield/dollar/GVZ” kartında DXY/nominal US10Y/VIX bağlamı var; gerçek faiz ve GVZ girdisi olduğu iddia edilmiyor. Kullanılan kodlar, belirli bir TradingView yazarının yayınladığı kodla eşdeğer kabul edilmedi.

**[120 kartın tamamının kaynak satırlı karşılaştırması](USAGE_MATRIX.md)** ve **[makineyle okunur matris](USAGE_MATRIX.json)** hazır.

## Klasik çekirdek: ne nerede hesaplanıyor?

| Yöntem | Backend/panel | Botun yerel karar yolu | Bot kayıt modülü |
|---|---|---|---|
| EMA | Genel ML, EMEL/Pulse, altın v2, rejim | Trend hizası, giriş filtresi, breakout/CHREV | EMA20/50/200 |
| SMA | Genel hesaplayıcı ve MTF | Ayrı SMA yön kuralı kurulmuş olarak sayılmadı | SMA20 |
| RSI | Genel hesaplayıcı ve altın v2 | SELL RSI ölçümü gölge dalında | RSI14 |
| MACD | Genel hat sadeleştirilmiş; altın v2 gerçek sinyal/histogram hesaplıyor | Mainscriptte ayrı yerel MACD karar hesabı kurulmuş olarak sayılmadı | MACD, sinyal ve histogram |
| Stochastic | Genel hat K hesaplıyor, D=K | Ayrı yerel karar hesabı kurulmuş olarak sayılmadı | K ve 3 dönem D |
| Bollinger | Genel hat, Pulse/MTF, altın v2 | Ayrı yerel BB giriş kuralı kurulmuş olarak sayılmadı | Üst/orta/alt, genişlik, %B |
| ATR | Rejim, ML girdisi, ölçekleme ve hedef/stop | Geometri, esneme ve sıkışma kontrolleri | Wilder ATR14 |
| ADX/DMI | Rejim ve teknik hesap | Trend/giriş ve CHREV filtreleri | ADX ve ±DI |
| Williams %R | Genel teknik hesap ve eşlenen ML sütunları | Ayrı yerel hesap bulunmadı | Yok |
| MFI | Genel teknik hesap ve ML sütunları | Ayrı yerel hesap bulunmadı | Yok |
| Momentum/ROC | Fiyat değişimi ve yön teyidi | Yöne göre 30/60 mum gerilme, CAPREV günlük değişim | Ayrı ROC alanı yok |
| Tarihsel oynaklık | Genel teknik hesap | CAPREV günlük getiri standart sapması | ATR% var; tarihsel getiri oynaklığıyla aynı şey değil |
| Parabolic SAR | Altın v2 girdisi; eski genel ML'de PSAR isimleri varsayılan doldurulabiliyor | Ayrı yerel SAR giriş kuralı kurulmuş olarak sayılmadı | SAR ve ATR-normalize mesafe |
| VWAP | Özellikle petrol/bağlam hesapları | CHREV için VWAP z-skoru | Son 50 mum ağırlıklı VWAP z-skoru |

Temel kaynaklar: [genel hesaplayıcı](../../../backend/services/ml_prediction_service.py), [altın v2](../../../backend/services/xauusd_v2_service.py), [bot kayıt göstergeleri](../../../yeni%20deneme/indicators.py), [bot veri kaydedicisi](../../../yeni%20deneme/data_recorder.py), [giriş kapısı](../../../yeni%20deneme/entry_gate.py), [CHREV kanal hesabı](../../../yeni%20deneme/channel_filter.py). Matris dosyası bunların doğrulanmış mutlak kaynak/satır bağlantılarını da içerir.

`compute_all` çağrısı ana emir döngüsünden değil `data_recorder.py` içinden geliyor. Dolayısıyla “bot klasöründe MACD var” ifadesi, “bot her emirde MACD'ye bakıyor” sonucunu vermez. Backend'in gönderdiği yön sinyali MACD'den etkilenebilir; bu dolaylı kullanım ile botun kendisinin MACD hesaplaması ayrı sütunlardır.

## Klasik çekirdeğin dışındaki eşleşmeler

- **Yapı ve seviyeler:** regression channel, swing/pivot, BOS/CHoCH, order block, FVG, liquidity sweep, önceki seans dibi, Fibonacci, pivot seviyeleri.
- **Formasyonlar:** harmonikler ve klasik grafik formasyonları; ayrıca mum formasyonu güven düzeltmeleri.
- **Hacim:** OBV, MFI, göreli hacim, VWAP ve yaklaşık fiyat-hacim profili.
- **Petrolün sentetik akışı:** `calculate_synthetic_cvd`, mum yeşilse `+0.6×volume`, kırmızıysa `−0.6×volume` kullanıyor. Bu gerçek bid/ask agresör deltası veya footprint değildir.
- **Bağlam:** açılış aralığı/ORB, COT/OI, seasonality, makro korelasyonlar, DXY/VIX/US10Y ve DAX'a özel CAPREV seans profili.

Bu araçların bir kısmı BUY/SELL puanını değiştiriyor; bir kısmı güveni, giriş uygunluğunu veya stop boyutunu; bir kısmı da LLM'nin gördüğü bağlamı etkiliyor. Bunları tek bir “yön tahmin eden indikatör” torbasına koymak yanıltıcı olur.

## Henüz kullanılmayanlar ve yanıltıcı isimler

| Durum | Atlas kartı sayısı | Örnek / anlam |
|---|---:|---|
| Karar/hesap/bağlam yoluna bağlı tam veya kısmi karşılık | **34** | Yukarıda sayılanlar |
| Yalnız gölge eşleşmesi | **1** | Donchian; USOIL breakout varsayılan `USOIL_BREAKOUT_LIVE=False`, XAU swing ayrıca shadow |
| Yalnız adı/varsayılan alanı | **2** | Ichimoku ve CMF/Chaikin kartı; gerçek hesap kurulmuş olarak sayılmadı |
| Yalnız araştırma hesabı | **1** | CCI; permutation batch'te var, ana yön hattında kurulu olduğu doğrulanmadı |
| İç yumuşatma yardımcısı | **1** | Wilder RMA |
| İsim/takma ad; ayrıca sayılmadı | **2** | EXPMA ve TAQ |
| İlgili kavram var, aynı yöntem değil | **5** | BIAS yerine ATR-normalize mesafe; MAD yerine Hampel varsaymamak; ATR sıkışması≠TTM Squeeze; analog kNN≠Lorentzian; VIX girdisi≠opsiyon gamma motoru |
| Veri bağlantısı çalışır olarak bulunmadı | **1** | Petrol servisindeki EIA inventory fetch kasıtlı olarak `None` döndürüyor |
| İncelenen karar yollarında bulunamadı | **73** | Örneğin Supertrend, HalfTrend, QQE, WaveTrend, KDJ, BBI, KAMA, FRAMA, Kalman, Ehlers filtreleri, TPO, gerçek footprint/DOM |

“Bulunamadı” bütün depoda hiçbir dosyada bu kelime yok demek değildir. Atlasın yeni indirdiğimiz `vendor/` klasörünü, geçmiş araştırmaları, testleri ve yedekleri üretim kullanımına dahil etmedim. Sayım, incelenen karar yolları ve doğrudan bağımlılıklarıyla sınırlı. 26 ilgili kaynak dosyasının hash'i [SOURCE_EVIDENCE.json](SOURCE_EVIDENCE.json) içinde korunuyor.

## Aynı veriyle hesap karşılaştırması

Üç hattın saf hesap fonksiyonlarını aynı **400 sentetik OHLCV mumuyla** çalıştırdım. Bunlar güncel veya tarihsel Nasdaq/altın fiyatları değildir; yalnız formül karşılaştırması için üretilmiş sayılardır. Broker, API, DB veya vendor atlas kodu çalıştırılmadı.

| Hesap | Genel panel/legacy | Bot kayıt hesabı |
|---|---:|---:|
| EMA20 | 1019.44856 | 1019.44856 |
| SMA20 | 1019.53812 | 1019.53812 |
| RSI14 | 30.33854 | 35.74667 |
| ATR14 | 1.98992 | 2.01737 |
| ADX14 | 25.17197 | 25.17197 |
| MACD line | -1.11032 | -1.11032 |
| MACD signal | 0.00000 | -1.00941 |
| MACD histogram | -1.11032 | -0.10092 |
| Stochastic K | 36.15907 | 36.15907 |
| Stochastic D | 36.15907 | 34.82445 |
| Bollinger upper | 1023.47788 | 1023.47788 |
| Bollinger lower | 1015.59837 | 1015.59837 |

Önemli farkların nedeni doğrudan kaynakta görülebiliyor:

1. **Genel MACD:** `signal=0`, `histogram=MACD line`, `hist_diff=0`. Dolayısıyla standart 12/26/9 histogramı değil.
2. **Genel stochastic:** `%D=%K`; D'nin bağımsız yumuşatması yapılmıyor.
3. **Genel RSI ve ATR:** son pencerenin basit ortalamaları kullanılıyor. Bot kayıt modülü Wilder yumuşatması uyguluyor.
4. **Altın v2 ayrı:** MACD sinyal çizgisi gerçekten hesaplanıyor; RSI/ATR ve ek özellikler kendi fonksiyonlarından geliyor. Genel legacy hattının sadeleştirmelerini altın v2'ye mal etmemek gerekiyor.

Bu tek örnekteki eşitlikler bütün seri/bütün başlangıç koşulları için parity sertifikası değildir. Farklar da hangi sürümün daha kârlı olduğunu söylemez. Eğitimde kullanılan formül neyse, tahminde aynı sözleşmenin korunması gerekir; formülü tek başına değiştirmek mevcut modeli bozabilir.

## ML yön tahmininde gerçekte hangi girişler var?

### Nasdaq ve DAX: yerel modelin 810 giriş sütunu var

Kodda NDX ve GDAXI aynı `model_lgbm_nasdaq.joblib` model ailesine yönleniyor. Yerel dosyanın `feature_names_in_` listesi **810** sütun içeriyor; eski dokümanlardaki “150 feature” ifadesi bu dosyayı doğru tarif etmiyor.

Mevcut `_build_feature_vector` ile doğrulanan dağılım:

| Girdi türü | Sütun |
|---|---:|
| Kodun açık haritasında eşleşen | **103** |
| Kategorik varsayılan / trend etiketi | **3** |
| Eksik özellik varsayılanı ile doldurulan | **704** |
| Toplam | **810** |

**103'ü de 103 ayrı gerçek indikatör olarak okumamak gerekir.** OHLC, aynı yöntemin farklı TF/periyotları ve sabit olan MACD sinyal/histogram-fark alanları da bu grupta. Bazı H1/H4 OHLC anahtarları son ana-zaman-dilimi mumundan kopyalanıyor. 704 sütun ise adına göre 0, 0.5, 0.01 veya son fiyat gibi değerlerle dolduruluyor. Gerçek Ichimoku/OBV/CMF hesabı veya gerçek çapraz-piyasa korelasyonu sırf sütun adında geçti diye mevcut sayılamaz.

Bu durum, modelin o sütunları matematiksel olarak “hiç kullanmadığı” anlamına gelmez. Model sabit/varsayılan girdilerle de karar verebilir. Ancak eğitimdeki gerçek özellik dağılımının tahminde yeniden üretildiği gösterilmiş olmaz. Bu inceleme bu farklılığın isabet veya PnL üzerindeki büyüklüğünü ölçmedi.

### Altın: ayrı 133 özellikli BUY/SELL paketi

`get_ml_prediction` altını önce `predict_xauusd_v2` yoluna alıyor. Yerel pakette **133 giriş sütunu**, ayrı BUY/SELL modelleri ve kalibratörler var. M30/H1/H4 teknik özellikler, M15 kovalama karşıtı özellikler, seans/saat ve DXY/US10Y/VIX türevleri oluşturuluyor.

Bunlar 133 farklı indikatör değildir. EMA/RSI/ATR/MACD/Bollinger/ADX/SAR/regression channel/momentum gibi ailelerin mesafe, eğim, TF ve geometri türevleri var. Eksik makro/TF verisi yine eksik değer/imputasyon davranışına girebilir; bu inceleme canlı veri doluluğunu sorgulamadı.

### Petrol: güncel yerel model eşleşmesinde bundle/estimator uyumsuzluğu

Burada ayrı bir somut bulgu çıktı:

- `USOIL.FOREX` genel model ailesi olarak `XAUUSD` anahtarına eşleniyor.
- Bu anahtarın dosyası şu anda **`model_xauusd_v2.joblib`**.
- Dosya bir sklearn estimator değil, BUY/SELL modellerini içeren bir **dict bundle**.
- Genel `_load_model`, `.feature_names_in_` arıyor; dict üzerinde olmadığı için giriş listesini boş bırakıyor.
- `_build_feature_vector` bu durumda **None** dönüyor. `get_ml_prediction` de bu koşulda `_rule_based_prediction` yoluna gidiyor.

Bunu ayrı saf-fonksiyon ortamında, mevcut model dosyalarıyla **taze yükleme** yaparak doğruladım. Canlı servisin belleğinde hangi eski modelin önceden yüklü olduğunu veya dağıtımdaki dosyanın aynı olduğunu iddia etmiyorum.

Diskte eski `model_lgbm_xauusd.joblib` adlı 150 girişli bir pipeline da var. Karşılaştırma amacıyla sözleşmesi okundu: 94 eşlenen + 3 kategorik + 53 varsayılan sütun. **Fakat mevcut dosya eşlemesi bu eski pipeline'ı seçmiyor.** Bu yüzden “petrol bugün 150 özellikli ML ile çalışıyor” sonucu çıkarılamaz. Altının v2 yolu hata verirse genel geri dönüş de aynı bundle sözleşmesi sorununa takılabilir.

### COT sembol eşlemesi

Saf `_normalize_symbol` fonksiyonunu dört sembolle kontrol ettim: NDX→NASDAQ, XAU→XAUUSD doğru anahtarlara gidiyor; **GDAXI→NASDAQ, USOIL→XAUUSD** sonucunu veriyor. `GDAXI.INDX`, noktalar kaldırılınca `GDAXIINDX` oluyor ve içindeki `NDX` alt dizisi nedeniyle Nasdaq koşuluna takılıyor. Bu, bu fonksiyondan geçen COT çağrılarında DAX için Nasdaq, petrol için altın kontratı bağlamı seçilebileceği anlamına gelir. COT var diye her sembolün kendi doğru kontratının işlendiği varsayılmamalı. Ayrıca sağlayıcı başarısızlığında servis sabit fallback veri kullanabiliyor.

## Gelecekteki yön açısından nasıl okumalıyız?

Sistemde üç farklı rol var:

1. **Yön/güven girdileri:** EMA, RSI, momentum, bazı formasyonlar ve ML özellikleri.
2. **Rejim ve giriş uygunluğu:** ADX, göreli hacim, regression channel, seviyeler ve seans koşulları.
3. **Risk/çıkış ölçeği:** ATR, günlük oynaklık ve stop/mesafe kuralları.

Bir gösterge bunlardan yalnız birine hizmet edebilir. ATR hesaplanıyor diye kendisi gelecekteki yönü tahmin ediyor denemez. LLM'ye bir bağlamın verilmesi, o alanın her kararda belirleyici olduğunu veya ölçülebilir bir katkı sağladığını da kanıtlamaz. Aynı şekilde eğitim modelindeki feature importance veya split sayısı tahmin doğruluğu değildir.

Bu karşılaştırma **hangi yöntemlerin bağlı olduğunu ve hangi sayının hesaplandığını** gösteriyor. Yeni göstergelerin mevcut sistemden daha iyi yön tahmini yapıp yapmadığını belirlemek için ayrıca dondurulmuş tanım, aynı zaman/etiket/icra koşulları ve bağımsız ileri dönem testi gerekir. Bu görevde öyle bir başarı testi yapılmadı.

Mevcut bulgulara göre yeni bir gösterge eklemeden önce incelenmesi gereken en somut konu, zaten kullandığımız özelliklerin/model dosyalarının sözleşme uyumudur. Petrol bundle yönlendirmesi, Nasdaq varsayılan sütunları, genel MACD/Stochastic formülleri ve COT sembol eşlemesi raporlandı; bu görev kapsamında işlem davranışı değiştirilmedi.

## Kanıt dosyaları ve tekrar üretme

- [120 satırlık kaynak matrisi](USAGE_MATRIX.md)
- [Hesap, model sözleşmesi ve taze yükleme sonucu](CALCULATION_AND_MODEL_AUDIT.json)
- [Yerel model metadata dökümü](MODEL_METADATA.json)
- [Kaynak dosyalarının hash'leri](SOURCE_EVIDENCE.json)

```sh
python3 research/indicator_atlas_20261025/system_comparison/build_usage_matrix.py
.venv/bin/python research/indicator_atlas_20261025/system_comparison/audit_calculations.py
```

İkinci komut yerel numpy/pandas/joblib/LightGBM ortamını ve projeye ait güvenilen model dosyalarını kullanır. Modellerin tamamı veya hesap fonksiyonlarının bağımlılıkları değişirse bulgular yeniden üretilmelidir. Ağ, broker, DB, canlı emir veya vendor atlas kodu çalıştırmaz. Model dosyaları yüklenir; piyasa yön tahmini/backtest yapılmaz.
