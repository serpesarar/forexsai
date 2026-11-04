# Nasdaq — iki araştırmanın sentezi ve nihai icra raporu

Tarih: 2 Ekim 2026. Durum: **offline araştırma; hiçbir strateji LIVE onayı almadı.**

**Sonuç:** İki rapordan beş yeni varyasyon türettim; diğer raporun sonradan fark edilen TUR3 ekindeki CAPREV ve kovalama endeksini de denetledim. En güçlü araştırma fikri **yüksek VIX altında, günlük volatilite stoplu ve seans kapanışına taşınan CAPREV**. En makul seçici veto **K5b/H1**. İkisinin de kanıtı canlıya geçmek için yetersiz. Diğer filtreleri üst üste eklemek net bir iyileştirme getirmedi.

Bu tur **22 sabit yapılandırma, 924 dönem/zaman dilimi/maliyet değerlendirme hücresi** içerir. Bunlar 924 bağımsız deneme değildir. İlk 14 tanım ana protokolde, son 8 tanım ek protokolde sonuçlarından önce yazıldı; yeni sonuçla eşik seçilmedi. 2025–Eylül 2026 geçmişi önceki turlarda görülmüştür. Bu turun tarih bölmeleri yeni, dokunulmamış OOS diye sunulamaz.

## 1. İki rapor nerede birleşiyor, nerede ayrılıyor?

| Konu | Birlikte çıkarılan sonuç |
|---|---|
| Stres sonrası SELL | Diğer raporun K5b bulgusunu gerçek bot örneklerinde tekrar elde ettim: 41 karar / 5 gün, ortalama −12,82 puan. Bu küçük ve önceden görülmüş örneklem. Yeni portföyde etkisi ayrıca ölçüldü. |
| Teyit beklemek | Bizim koşulsuz bekleme filtremiz birçok dönemde kazananı kaçırdı. Diğer rapor bunu teyitsiz alıma bağladı. Bu, mantıklı hipotez; günlük ölçekte bütün teyitlerin zararlı olduğu kanıtlanmış değil. |
| Hacim şoku | Ham M5 oranı botun 18 kararında olumsuz; aynı saatin geçmişiyle normalize edilince yalnız 2 bot kararı kalıyor. Evrensel ve taşınabilir bir hacim kapısı henüz yok. |
| Kovalama | Bot örneklerinde kötü alt kümeler var; özgün beşli portföye uygulanınca katkı çok küçük ve Eylül'de negatif. Bot ve araştırma sinyali aynı evren değil. |
| Uzama BUY vetosu | Günlük fiyat uzaması tek başına alım engeli yapmak için yeterli değil; daha seçici H4 bile beş dönemin tamamında portföye zarar verdi. |
| Portföy bağımlılığı | Bir grubun ortalama kaybı, o grubu engellemenin portföye aynı miktarda kazandıracağı anlamına gelmez. Boşalan zaman dilimlerine başka işlemler girer. Bütün vetolar bu nedenle yeniden sıralandı. |

## 2. Beş yeni varyasyon — ana deney

H1–H4 için aşağıdaki sayılar **taban portföye toplam R katkısıdır**. H5 yeni giriş stratejisidir; kendi toplam R'si yazılmıştır. Pozitif ΔR, stratejinin kendisinin her dönemde kârlı olduğu anlamına gelmez.

| Varyasyon | 2025 ilk | 2025 ikinci | Şub–May | May–Ağu | Eylül | Karar |
|---|---:|---:|---:|---:|---:|---|
| H1: Stres + önceki RTH dibi altında SELL veto | -1.56 | +2.78 | +3.77 | +1.11 | +0.00 | Seçici gölge araştırma adayı |
| H2: Ham ve saat-normalize M5 hacim şoku veto | -7.03 | -4.57 | +0.00 | +0.00 | +0.00 | Reddedildi |
| H3: Yalnız hacim şokunda 3 dk fiyat sınırlı bekleme | -5.92 | -1.54 | +0.00 | +0.00 | +0.00 | Reddedildi |
| H4: MA200+%10 ve 4s aralığın üst %20'sinde BUY veto | -1.30 | -2.80 | -0.17 | -2.40 | -2.50 | Reddedildi |
| H5: Stres sonrası önceki RTH dibini geri alan BUY | +2.87 | -0.05 | +2.18 | -1.76 | +0.00 | Seyrek ve kararsız; terfi yok |

**H1/K5b:** toplam katkı +6.11R; 330 işlem gününün yalnız **11 günü** değişiyor. Eşleştirilmiş gün bootstrap'ında katkının pozitif kalma payı %84.7; günlük ΔR %95 aralığı [-0.0163, +0.0561]. Sıfır aralığın içinde. Beş ana hipotez için düzeltmeli tek yönlü p=0.744; istatistiksel doğrulama değil.

**H5:** 41 işlem / 18 gün, toplam +3,23R; Mayıs–Ağustos −1,77R ve Eylül'de olay yok. Geri alımı beklemek tek başına güvenilir yeni giriş üretmedi. CAPREV ile aynı çıkış geometrisi kullanıldığında ayrıca karşılaştırıldı.

**Kontroller önemli:** tüm stresli günlerin SELL'ini engelleyen K5, 2025 ilk yarıda −12,38R; yalnız dibin altını engelleyen H1 aynı dönemde −1,56R. Buna karşılık Mayıs–Ağustos'ta K5 +8,00R, H1 +1,11R. Seçicilik her dönemde üstün değil. Ham hacim vetosu ΔR: −8,14 / −1,56 / +3,15 / −1,39 / 0,00. Koşulsuz 3 dakika bekleme: −16,02 / −20,50 / +8,07 / +2,12 / −4,74R. Bütün uzamış günlerin BUY'ını engelleyen K6 da son dört dönemde zarar verdi.

### Zaman dilimi aktarımı

| Kural | M1 | M3 | M5 | Ölçü |
|---|---:|---:|---:|---|
| H1 | +6.11 | +0.62 | +14.99 | Portföye ΔR |
| H2 | -11.59 | -1.22 | +1.99 | Portföye ΔR |
| H3 | -7.46 | -2.29 | +1.02 | Portföye ΔR |
| H4 | -9.16 | -19.51 | -1.30 | Portföye ΔR |
| H5 | +3.23 | +9.13 | +1.44 | Kendi toplam R |
| CHASE | +0.30 | +10.60 | +5.70 | Portföye ΔR |

M3 taban portföy −48,07R, M5 taban −30,79R. Örneğin H1 iki ölçekte katkı sağlasa da portföyleri kârlı hale getirmedi. Agregasyonlar aynı M1 fiyat yolunun dönüşümüdür; üç bağımsız piyasa örneği değildir.

### Maliyet ve birleşim denetimi

| İcra | Taban toplam R | H1 katkısı | H2 katkısı | H3 katkısı | H4 katkısı | Birleşim katkısı |
|---|---:|---:|---:|---:|---:|---:|
| Ana | +57,12 | +6,11 | −11,59 | −7,46 | −9,16 | −15,12 |
| Spread ×3 | −90,68 | +1,98 | −7,16 | −1,23 | −5,33 | −9,91 |
| Kayma 1 puan/taraf | −1,28 | +3,36 | −10,89 | −6,99 | −8,93 | −16,88 |
| Giriş +1 M1 | +24,40 | +1,22 | −6,16 | −5,08 | −12,04 | −19,28 |

H1'in katkısı pozitif kalsa da spread3 altında portföy hâlâ −88,70R: bir veto pozitif katkıyla canlı stratejiye dönüşmez. Birleşimde H2 zaten hacim şokunu veto ettiği için H3'ün bekleme kısmı etkisizdir; kombinasyon toplam katkıyı artırmadı.

## 3. CAPREV — en önemli yeni denetim

Diğer raporun kuralını tutarlı bir M1 yürütmeye çevirdim: önceki nakit gün getirisi ≤−%1,5 veya son beş gün ≤−%4; önceki VIX≥18,4; Pazartesi–Perşembe NY03:00–15:00 arası önceki **tam 09:30–16:00 RTH** dibinin altındaki ilk kapanış; sonraki M1 açılışı/ask'ten BUY. Stop: önceki 20 nakit gün getirisinin standart sapması × giriş fiyatı. Hedef yok; NY16:00 M1 açılışında çıkış. Günde en fazla bir işlem.

| Denetim | İşlem | Toplam R | Ortalama R |
|---|---:|---:|---:|
| M1 ana | 11 | +11.12 | +1.01 |
| M5 tetikleyici, M1 icra | 11 | +11.29 | +1.03 |
| M15 tetikleyici, M1 icra | 11 | +11.08 | +1.01 |
| Spread ×3 | 11 | +10.98 | +1.00 |
| Her tarafta 1 puan kayma | 11 | +11.07 | +1.01 |
| Giriş +1 M1 gecikme | 11 | +11.06 | +1.01 |

Ana örneklem yalnız **11 işlem / 11 gün**. 2025 ilk yarı 6 işlem +6.14R; 2025 ikinci yarı 1 işlem +0,79R; Şub–May 3 işlem +4,28R; May–Ağu 1 işlem −0,09R; Eylül ve 1 Ekim sıfır olay. İşlem sayısına göre kronolojik iki yarı: ilk5 işlem yalnız +0,06R, son6 işlem +11,06R; pozitiflik çok dengesiz.

Ham gün bootstrap'ı P(EV>0)=%98.18, %95 EV aralığı [+0.046, +2.265]R. Bu küçük ve önceden seçilmiş örneklem için yeni bir başarı olasılığı veya kâr garantisi değildir. 150 olay eşiğinin çok altında.

**Kâr yoğunlaşması:** 9 Nisan 2025 tek başına +6,08R. En iyi bir gün çıkarılınca +5,05R, en iyi üç gün çıkarılınca yalnız +0,28R, en iyi beş gün çıkarılınca **−1,35R** kalıyor. Stratejinin nadir büyük geri dönüşlere dayandığı açık; küçük örneklemde bunun devamlılığı bilinmiyor.

**Çıkış geometrisi belirleyici:** aynı 11 olayda TP80/SL110 → **+1,07R, ortalama +0,097R**, bootstrap pozitif payı yalnız %62,75. Diğer rapordaki 14 olay/+0,33R ile aynı olay seti ve çıkış modeli değildir. Biz iki eksik önceki RTH günü (11 Mart ve 7 Nisan 2025) ile dondurulmuş bölmeler arasındaki 18 Mayıs 2026'yı kapsam dışı bıraktık; giriş/çıkış ve kayma tanımları da farklıdır. +1,011R'lik günlük-vol sonucu kısa stoplu mevcut bota taşınamaz.

Stop mesafesi bu örneklerde 193–592 fiyat puanı, medyan 290. R aynı başlangıç riskiyle normalize edilir; aynı lot kullanmak eşit parasal risk değildir. Bu rapor lot veya USD kâr önerisi üretmez.

Kontroller: düşük VIX stres örnekleri 9 işlemde −1,94R; stressiz/yüksek VIX aynı olay 33 işlemde +3,35R (4 veri boşluğu içerir), yani bütün kontroller negatif değil. Aynı stres olayında SELL 11 işlemde −2,94R. Dip geri alımını bekleyen, aynı günlük-vol stoplu varyant 9 işlemde +5,80R; daha az ve farklı zamanda olay üretiyor. Bu gözlemler teyitsiz alım fikrini destekliyor, fakat nedensel üstünlük kanıtlamıyor.

Diğer raporun 10 yıllık 1h, 30m ve 15m sonuçları değerli uzun dönem kanıtıdır; bu turda bunların tamamını yeniden üretmedim. Bunlar farklı zamanlarda giriş, kısmen farklı seans dibi ve çıkış tanımları içeriyor. Özellikle 1h seviyesinde 09:00–16:00 aralığı kullanılmış; 09:30 RTH dibiyle birebir aynı değil. Ayrıca 138 olay filtresiz seri, VIX filtresiyle raporlanan seri 108 olay: final kuralın örneklemine 138 yazılmamalı. Uzun dönem no-stop gvol getirisi ile stoplu R ölçüsü ayrı tutulmalı.

## 4. Kovalama endeksi ve evren değişimi

CHASE = SELL yönünde dört bileşenden en az üçü: M5/50-bar regresyon kanalında ≤−1σ, M15 aşağı hizalı, önceki RTH dibinin altında, günlük stres. Aynı beşli portföyde ΔR dönem sırasıyla **+2,72 / +0,09 / +0,01 / +0,84 / −3,35R**; toplam yalnız **+0,30R**. Gün eşleştirmeli pozitif katkı payı %51,45. Botta görülen monoton kötüleşme portföy kazancına güçlü biçimde taşınmadı.

K5b ile CHASE aynı kapı da değil. Stres+dip-altı yalnız iki puan eder; ≥3 eşiğine otomatik yetmez. Yeniden eşlenen bot kararlarında H1'in engellediği **4 karar** CHASE≥3 kapsamına girmiyor. Bu nedenle 'CHASE, K5b'yi içerir' ifadesi genel olarak doğru değil.

## 5. Yeni gün, veri ve icra kalitesi

- Ana protokol sabitlendikten sonra 1 Ekim tam seansı MT5'ten salt okunur alındı; broker saat ofseti +10800 saniye, point=0,1; önceki veriyle çakışma fiyat/saat kontrolleri geçti. Ek CAPREV denetimi yazılırken bu günün mumları zaten alınmıştı; CAPREV için dokunulmamış OOS sayılmadı.
- 1 Ekim taban beşli: 8 işlem, **+3,12R**. H1–H4 aynı işlemleri bıraktı; yeni güne katkıları sıfır. Koşulsuz bekleme 6 işlem **−1,74R**. H5/CAPREV olay üretmedi. Tek gün filtre doğrulaması sağlamaz.
- 30 Eylül önceden görülmüş ek gün: taban 5 işlem +1,12R. Bu turdaki sonuçlarla kural seçmek için kullanılmadı.
- 2025 Dukascopy 306.635 M1; saat onarılmış cache+doğrudan MT5 228.396 M1. Önceki nakit günün tam RTH 390 mumu yoksa seans dibi kullanılmadı. Eksik yarım günler doldurulmadı.
- **Yeni veri kusuru:** diğer klasörde 30 Eylül NDX kapanışı 30.556,29 ve VIX 15,91 idi; tamamlanmış günlük veriyle NDX **30.408,50**, VIX **16,34** olarak kendi araştırma kopyamda yeniledim. Önceki değerler tamamlanmış gün diye kullanılmamalı. Diğer ajanın dosyasını değiştirmedim.
- Önceki cache Şubat–8 Mart saat düzeltmesi korundu. Makro ve M5/M15 özellikleri yalnız karar anına kadar kapanmış veriyi kullanır. Gelecek mumları değiştirme ve 1/3/5 dakika prefix kontrolleri geçti; CAPREV için ayrıca 1/5/15 dakika prefix ve 8 dolum/stop/boşluk fikstürü geçti.
- Taban ve veto portföyleri aynı anda tek pozisyon, 10 dakika yeniden giriş aralığı ve sabit strateji önceliğiyle tekrar yürütüldü. Ana stratejiler 15:55'te, CAPREV16:00'da kapanır; bu iki ürünün tutma süreleri farklıdır.
- Dukascopy gerçek bid/ask OHLC kullanılır. Doğrudan MT5 verisinde kayıtlı bar spreadinden ask türetilir. Eski cache bölümünde spread kaydı yok: **1,3 fiyat puanı varsayımı** kullanıldı; o döneme gerçek spread doğrulaması denemez. Yeni MT5 ihracındaki bar spreadleri 1,0 puan; tick düzeyindeki değişim ve gerçek fill/komisyon doğrulanmış değil. Komisyon ayrıca modellenmedi. Ana model her tarafta0,2 puan kayma; streslerde spread3, kayma1 ve gecikme1M1 kullanıldı. Finansman taşıması yok; bütün işlemler gün içi.
- H2'nin şartı 2025 ham strateji fırsatlarının38'inde, 2026 fırsatlarının **hiçbirinde** oluştu. Dolayısıyla 2026'da sıfır katkı başarılı korunma değil, hareketsizliktir. Saat hacmi geçmişi 2025'te218, 2026'da461 ham fırsatta bilinmiyordu; eksik özellik veto üretmedi. Önceki tam RTH dibi de sırasıyla1.159/82 fırsatta yoktu; kapsam farkı raporlandı.
- Toplam R ve bootstrap noktaları USD/kümülatif hesap kârı değildir. 2025/2026 aynı kuralların farklı sağlayıcı örnekleri; seçimin geçmiş tur yükü silinmedi.

**Veri boşlukları önemli:** taban portföyde 53 çıkış veri boşluğuyla ilişkili. Bunların hepsini en az −1R sayınca toplam +57,12R → **−2,56R**. H1 portföyü +63,23R → **+3,55R**. Bu sınır gerçek gap dolumu tahmini değil, eksik veriye duyarlılık göstergesi. CAPREV'in raporlanan 11 olayında yürütme boşluğu yok; ancak eksik önceki seansı olan olaylar baştan dışarıda. Sağlayıcı kapsamı örnek seçimini etkileyebilir.

## 6. Matematiksel yorumun sınırı

Diğer rapordaki `μ ∝ σ²` sonucu, volatilite gruplarında fark görülmemesinden kanıtlanamaz. Sınırlı örneklem, rejim karışımı, değişken stop mesafesi veya düşük istatistiksel güç de aynı gözlemi üretebilir. Bu yüzden 'volatiliteye uyarlamaya gerek yok' sonucu kesin değil.

Sabit sürüklenmeli modelde uygun durdurma koşulları altında brüt E[PNL]=μ·E[τ] yazılabilir; gerçek icrada maliyetler ayrıca çıkarılır. Sürüklenmesiz sürekli martingalde TP80/SL110'un teorik hedefe önce erişme olasılığı 110/(80+110)≈%57,89'dur; brüt beklenti yine sıfırdır. Yüksek kazanma oranı tek başına kenar değildir. Bu bilinen matematiğin uygulamasıdır; yeni bir Forex yasası keşfedildiği söylenemez.

Çok sayıda strateji üzerinde aynı geçmişe dönerek seçim yapmanın aşırı uyum riski için [Bailey ve diğerlerinin birincil araştırması](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf); tick hacmi ile gerçek işlem hacminin ayrımı için [MetaQuotes MqlRates belgesi](https://www.mql5.com/en/docs/constants/structures/mqlrates) esas alındı. Burada hesaplanan bootstrap P değeri bu seçim geçmişinin olasılığını düzeltmez.

## 7. Nihai karar ve sabit sonraki adım

1. **CAPREV:** en öncelikli araştırma/SHADOW adayı. Günlük-vol stop +16:00 çıkışı ayrı ürün olarak dondurulsun; TP80/SL110 sonucuyla karıştırılmasın. Bu çalışma canlı ya da gölge çalışan süreç eklemedi.
2. **H1/K5b:** ikinci sırada seçici SELL veto hipotezi. Gerçek bot sinyal niyeti evreninde, veto uygulanmadan alınacak ileriye dönük loglarla değerlendirilmesi gerekir. Sadece önceden gerçekleşen 41 işlemden kurtarılacak para hesaplanamaz.
3. **CHASE:** bot örneklerine özel olabilir; portföy aktarımı kanıtlanmadı. H1'in yerine otomatik geçirilmemeli.
4. **H2/H3/H4:** mevcut tanımlarla elendi. Yeni kombinasyon diye canlıya taşınmamalı. **H5:** düşük örneklem ve dönem kırılması nedeniyle terfi yok.
5. CAPREV veya bir veto için canlı kararından önce ≥150 çözülmüş uygun olay, iki kronolojik yarı, pozitif net EV ve gün bootstrap'ı, en az1,5×spread stresi, next-M1-open/gerçek spread ve tek pozisyon kartı gerekir. Hacim eşiğine takılan adaya bu rapor LIVE kartı üretmedi. Tamamen yeni dönem, gerçek sinyal evreni ve gerçek dolum doğrulaması açık iş olarak kaldı.

## 8. Görseller ve yeniden üretim

![Karşılaştırma](results/comparison.png)

![İlk kazanan ve ilk kaybeden örnek](results/trade_examples.png)

Dosyalar: `PROTOCOL.md`, `PROTOCOL_ADDENDUM.md`, `run.py`, `caprev.py`, `verify.py`, `verify_caprev.py`, `results/evaluation.json`, `results/addendum.json`, `results/aggregate.json`, tüm işlem CSV'leri ve `results/provenance.json`. Rapor ve grafikler `make_report.py` ile bu çıktılardan üretilir.

```bash
python3 research/ndx_synthesis_20261002/run.py
python3 research/ndx_synthesis_20261002/verify.py
python3 research/ndx_synthesis_20261002/caprev.py
python3 research/ndx_synthesis_20261002/verify_caprev.py
python3 research/ndx_synthesis_20261002/make_report.py
```

Girdi alma betiği ayrıca ağ/MT5 erişimi ister; yeniden üretim sırasında dondurulmuş veri dosyaları korunmalıdır. Yeni veriyle yeniden koşmak eski raporu sessizce değiştirmemelidir.
