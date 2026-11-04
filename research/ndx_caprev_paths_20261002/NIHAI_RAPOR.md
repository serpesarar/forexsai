# Nasdaq — CAPREV olay zamanı, çıkış ve sermaye kullanımı: nihai rapor

2 Ekim 2026. **Araştırma tamamlandı; bütün adaylar araştırma/SHADOW düzeyinde. Çalışan bot veya gölge süreç kurulmadı.**

**En anlamlı yeni fikir:** stresli gün + yüksek ve artan VIX altında, CAPREV girişini günlük volatiliteye göre **+1R hedef / −1R stop** ile yönetmek. Tek başına seans sonuna taşımadan daha az kazanıyor; mevcut beşli araştırma portföyünde daha erken sermaye boşalttığı için daha fazla toplam katkı veriyor. İkinci fikir, +1R'de yarı kâr alıp yarıyı seans sonuna taşımak: kazancı azaltırken uç-gün bağımlılığını ve bazı düşüşleri azaltıyor.

Bunlar doğrulanmış kazanç vaatleri değil. En iyi portföy katkısı yalnız **7 etkilenen güne** dayanıyor; güven aralığı sıfırı içeriyor. Saatlik uzun verinin ilk kronolojik yarısı bazı VIX birleşimlerinde zayıf/negatif. M1 final tanımlarında150 uygun olay yok; saatlik birleşimin sayısı150'yi geçse de gerçek09:30/next-M1 icra kartı yok.

## 1. Eklenen rapor gerçekten yeni miydi?

Çalışmanın başındaki sürüm önceki sentezimizle aynıydı (SHA256 `32dd3fdaa0d17d4c…`); çalışma sırasında rapor **v2/TUR4** olarak güncellendi (SHA256 `547ba81d85701972…`). v2 ayrıca okunup `ATTACHED_V2_SNAPSHOT.md` olarak sabitlendi. Yeni açılış/dip birleşimi ve gece taşıma iddiaları ayrı dördüncü aşamada test edildi; kaynak rapordaki öneriler botu değiştirme talimatı olarak uygulanmadı. Önceki sentez +11,12R CAPREV'in üç büyük güne yoğunlaştığını, TP80/SL110'a doğrudan taşınmadığını ve CHASE aktarımının zayıf olduğunu göstermişti.

Aşama1:5 yeni varyasyon+5 taban/kontrol; aşama2:2 sabit birleşim; aşama3:3 ekleme portföyü+taban; aşama4:açılış/gece/tek-pozisyon için6 tanım. **Toplam22 yapılandırma, 1424 dönem/zaman-dilimi/maliyet hücresi.** İlk780 hücre, birleşimler156, portföy80, v2 denetimi408. Aynı olayların farklı ölçümleridir; bağımsız örnek sayısı değildir. Kurallar her aşamada kendi sonuçlarından önce protokolde yazıldı; sonraki aşamalar önceki sonuçlardan öğrenildi. Bütün dönemler retrospektiftir; yeni dokunulmamış veri çekilmedi.

## 2. Beş yeni varyasyon

Taban CAPREV: önceki nakit NDX getirisi≤−%1,5 veya5 seans≤−%4; önceki VIX≥18,4; Pzt–Per NY03:00–15:00 önceki RTH dibinin altındaki ilk tam kapanış; sonraki yürütme barı açılışı BUY; başlangıç stopu önceki20 nakit getiri std×giriş fiyatı; NY16:00 çıkışı. Günde bir net pozisyon.

| Yeni varyasyon | Mantık | M1 işlem / toplam R | Native30m toplam R | İlk karar |
|---|---|---:|---:|---|
| Yeni dip kırılımı | Zaten dip-altı olmak yerine aynı gün yeni üstten-alta geçiş | 9 / +6.74 | +13.38 | Tabandan zayıf |
| Nakit seansında giriş | İlk dip-altı olayı yalnız09:30 sonrası | 9 / +2.20 | +9.61 | Tabandan zayıf |
| 10:00 başarısız geri-alım çıkışı | 10:00 kapanmış fiyat hâlâ önceki dibin altındaysa erken çıkış | 11 / +7.66 | +19.71 | Kazananı erken kesiyor |
| Yarı+1R / yarı16:00 | Yarısı+1R hedefte, yarısı ilk stopla16:00'a | 11 / +7.65 | +23.77 | Kazanç/risk dengesi adayı |
| Yüksek fakat düşen VIX | Yüksek VIX ama önceki günlük değişim negatif | 2 / -1.40 | +0.32 | Desteklenmedi |

Değişmeyen taban: M1 **11 işlem / +11.12R**, native30m72 işlem / +27.62R. Taban M1'de önceki11 olayla **birebir aynı**; yeni motorun taban kazancı değiştirmediği ayrıca kontrol edildi.

Yeni kırılımı beklemek veya cash açılışına geçmek daha iyi zamanlama üretmedi. Saat10:00'daki 'geri alınamadı, çık' şartı da hem M1 hem uzun veride kazancı azalttı. Günlük bir geri dönüşün sabah erken tamamlanmasını şart koşmak, günün ilerleyen kısmındaki toparlanmaları kesebiliyor. Bu testten 'her teyit zararlıdır' gibi genel bir yasa çıkarılamaz.

## 3. Kârı bölmek — yeni risk dengesi

+1R'de yarım kâr alıp kalan yarıyı16:00'a taşımada ilk stop değişmez; breakeven/trailing yoktur. Kısmi çıkış aynı net pozisyona aittir; kalan açıkken başka pozisyon açılmaz. FULL_TP1 kontrolünde bütün pozisyon aynı+1R hedefte kapanır.

| Kaynak | Taban toplam R / DD | Yarı çıkış toplam R / DD | Tam+1R toplam R / DD |
|---|---:|---:|---:|
| M1:2025/2026 | +11.12 / 1.09 | +7.65 / 1.00 | +4.18 / 1.00 |
| Native15m:2023+ | +19.73 / 1.20 | +17.02 / 1.00 | +14.32 / 1.00 |
| Native30m:2021+ | +27.62 / 3.14 | +23.77 / 2.82 | +19.91 / 2.82 |
| H1 seviye yaklaşımı:2016+ | +25.75 / 4.95 | +20.93 / 3.82 | +16.11 / 3.66 |

DD: başlangıç risk birimi cinsinden gözlenen en büyük düşüş. Aynı nakit riskle normalize edildiği varsayılır; gerçek lot/dolum karnesi değildir.

| En iyi olaylar çıkarılınca kalan toplam R | Taban | Yarı çıkış | Tam+1R |
|---|---:|---:|---:|
| M1, en iyi3 gün | +0.28 | +0.73 | +1.18 |
| Native15m, en iyi5 gün | +4.21 | +6.76 | +9.32 |
| Native30m, en iyi5 gün | +10.51 | +12.71 | +14.91 |
| H1 yaklaşımı, en iyi5 gün | +8.98 | +10.04 | +11.11 |

Her varyasyonun kendi en iyi günleri çıkarıldı; bunlar aynı tarihler olmak zorunda değil. Yarı/tam hedef kârı budarken kalan getiriyi birkaç büyük güne daha az bağımlı hale getiriyor. M1 örneklemi bu sonuç için de yalnız11 gün.

Matematiksel kontrol: **R_yarı =0,5·R_seans-sonu +0,5·R_tam-hedef**. Aynı giriş, ilk stop ve maliyetle24 kaynak/TF/maliyet setinin hepsinde eşitlik en çok4,44×10⁻¹⁶ hata ile sağlandı. Bu bir getiri karışımıdır. Beklenti iki beklentinin ortalaması; varyans da iki getiri arasındaki kovaryansa bağlıdır. Tek başına fiyat tahmini kenarı üretmez, ama risk dağılımını değiştirir. Burada görülen kazanç/risk ödünleşimi böyle açıklanabilir.

## 4. VIX seviyesi ve yönü aynı bilgi değil

Yüksek VIX'in günlük olarak **düşmesi** şartı M1'de yalnız2 işlem ve−1,40R; native15m'de2 işlem−1,38R;30m'de14 işlem+0,32R verdi. Bu yeni ana hipotez desteklenmedi.

Önceden tanımlanan ters kontrol, **VIX artmış/eşit**: M1'de9 işlem+12,52R; native15m22 işlem+21,11R;30m58 işlem+27,30R;H1 yaklaşımında86 işlem+21,79R. Ancak H1 ilk43 işlem ortalaması **−0,052R**, son43+0,559R. Sadece ortalama iyileşti diye uzun dönem kararlılığı geçti denemez. 2025 M1'de fark iki kaybeden günü dışlamaya dayanıyor; çok küçük seçim.

Bu kontrol ile iki çıkış şekli birleştirildi. Bunlar aşama1 sonucundan sonra yazılan, hâlâ retrospektif olan iki ek tanımdır:

| Birleşim | M1 n / toplam R | Native30m n / toplam R | H1 ilk/ikinci yarı EV |
|---|---:|---:|---:|
| Artan VIX + yarı hedef | 9 / +9.05 | 58 / +23.84 | -0.02 / +0.43 |
| Artan VIX + tam+1R hedef | 9 / +5.58 | 58 / +20.38 | +0.02 / +0.31 |

Artan VIX+yarı hedefin saatlik ilk yarısı negatif kalıyor. Artan VIX+tam hedefte iki yarı pozitif olsa da saatlik EV %95 bootstrap aralığı yaklaşık **[−0,005,+0,328]R**: sıfır içeriyor. Bu birleşimleri evrensel kural veya güçlü yeni doğrulama diye sunmuyorum.

## 5. Daha az tek başına kazanç, daha çok portföy katkısı

Mevcut botu mumlardan birebir yeniden üretmek mümkün değil. Burada önceki turda dondurulan beşli **araştırma portföyü** kullanıldı. Bütün ham fırsatlar yeniden sıralandı. Aynı anda tek toplam pozisyon;10 dakika giriş aralığı; açık eski pozisyon varsa CAP kaçırılır. Aynı dakika boşsa CAP öncelikli. Yarım pozisyon açıkken normal stratejiye yeni giriş yok.

| Portföy | Toplam işlem | Alınan CAP | Toplam R | Tabana katkı |
|---|---:|---:|---:|---:|
| Özgün beşli | 2293 | 0 | +61.36 | +0.00 |
| Beşli + CAPREV16:00 | 2260 | 8 | +64.30 | +2.94 |
| Beşli + artanVIX/yarıhedef | 2261 | 7 | +65.94 | +4.58 |
| Beşli + artanVIX/tamhedef | 2267 | 7 | +70.76 | +9.40 |

Artan VIX/tam-hedef, tek başına9 olayda+5,58R ile tabanın+11,12R'sinden az kazandı. Portföyde ise **+9,40R katkı** ile16:00 CAP eklemesinin+2,94R katkısından iyi. Yarı hedef ile tam hedef portföyleri aynı7 CAP olayını aldı; tam hedef6 ek normal işleme yer açtı. CAP kazancı5,99→5,06R düşerken normal stratejilerin toplamı59,95→65,70R yükseldi. Sermayenin beklediği süre de strateji sonucunun parçası.

Dönem katkısı (artanVIX/tamhedef): 2025ilk **+3,76R**,2025ikinci **+1,67R**,2026Şub–May **+4,06R**,May–Ağu **−0,09R**,Eylül–1Ekim **0,00R**. Son dönemde hiç CAP olayı yok; başarılı doğrulama sayılmaz.

Katkı332 taban işlem gününün yalnız **7 gününde** oluştu. Eşleştirilmiş gün bootstrap pozitif katkı payı%95.25; günlük ΔR %95 aralığı **[-0.0015,+0.0654]**. Sıfır içeriyor. Ham tek-yönlü p=0.066;22 yapılandırma için kaba Bonferroni p=1.00. Önceki turların seçim yükünü bile içermeyen bu kontrol, kanıtlı katkı demeye yetmiyor.

### Maliyet ve gecikme

| İcra | Taban portföy toplam R | ArtanVIX/tamhedef toplam R | Katkı |
|---|---:|---:|---:|
| Ana | +61.36 | +70.76 | +9.40 |
| Spread×3 | -86.63 | -74.66 | +11.97 |
| Her tarafta1 puan kayma | +2.72 | +12.68 | +9.96 |
| Giriş+1 M1 | +28.91 | +38.29 | +9.38 |

Katkının pozitif olması bütün portföyü sağlam kârlı yapmıyor: spread3'te sonuç **−74,66R**. Gerçek bot sinyali/lot/dolum evreni ayrı doğrulama gerektiriyor.

## 5b. v2/TUR4: açılış, gece ve iki aşamalı giriş denetimi

v2 yeni bir fikir getiriyor: stresli günün nakit açılışından alım ve dip-kırılımı alımını birleştirmek. Ancak `w7.py` açılış ve dip işlemlerini ayrı ayrı çözüp R değerlerini **topluyor**; açık pozisyon varken ikinci giriş engellenmiyor. İki bacak da1 risk birimi taşıyabiliyor. 223 olay, iki bacak toplamının hesaplandığı **benzersiz gün** sayısı; tek-pozisyon kartının doğrulanmış işlem sayısı değil. Saatlik açılış da09:30 yerine09:00 barı. Bu ayrımlar sonucu yorumlamak için gerekli.

Rapordaki H1 +0,269R/gün, W7 çıktısında **iki bacağın da aynı gün16:00 kapandığı** toplamdır. İki bacağın da ertesi gün kapandığı değer+0,252R/gün. Metinde tarif edilen açılış-bugün/dip-yarın karışımının performansı bu iki sayıdan okunamaz. Aynı sermaye riskini iki önceden ayrılmış yarım bütçeye bölünce+0,269R, toplam bütçe başına yaklaşık **+0,135R/gün** olur; tek açılış bacağının+0,154R/gün değerinden düşük. Bu basit normalizasyon, daha fazla risk kullanarak artan R toplamını ayrı bir yönsel üstünlük gibi yorumlamayı önler; gerçek lot, stop-gap ve sermaye verimliliği kartının yerine geçmez.

Altı tanım ayrıca donduruldu: OPEN_SAME, DIP_SAME, DIP_NEXT, OPEN_NEXT, UNION_SAME ve UNION_MIXED. Birleşimlerde tüm fırsatlar kronolojik sıralanır; açılış/dipten hangisi önce gelirse boş pozisyonda o alınır. Aynı dakika açılış önceliklidir. Stopla boşalınca sonraki dip/açılış olayı,600 saniye giriş aralığı uygunsa alınabilir. DIP_NEXT/OPEN_NEXT tek başına da ertesi güne açık kalan işlemi atlayarak çözülür. UNION_MIXED açılışı aynı gün, dip alımını bir sonraki **nakit işlem seansı**16:00 kapatır; takvimde ertesi gün varsayılmaz.

| M1 tanımı | İşlem / benzersiz gün | Toplam R | EV / işlem | DD |
|---|---:|---:|---:|---:|
| 09:30 al / bugün16:00 | 27 / 27 | +10.60 | +0.393 | 4.21 |
| Dip al / bugün16:00 | 11 / 11 | +11.12 | +1.011 | 1.09 |
| Dip al / sonraki seans16:00 | 11 / 11 | +9.87 | +0.898 | 1.00 |
| 09:30 al / sonraki seans16:00 | 25 / 25 | +5.37 | +0.215 | 4.55 |
| Tek pozisyon, iki fırsat / bugün16:00 | 28 / 27 | +14.72 | +0.526 | 3.90 |
| Tek pozisyon, açılış bugün / dip sonraki seans | 27 / 26 | +11.40 | +0.422 | 2.86 |

M1'de UNION_SAME tabanın+11,12R'sine karşı **+14,72R**, fakat DD1,09→3,90R. Başka günlerde de risk kullanarak daha fazla kazanıyor; risk başına ortalaması tabanın1,011R'sinden0,526R'ye düşüyor. Tabana günlük katkı aralığı **[-0.156,+0.439]R** ve sıfırı içeriyor. En iyi5 işlem çıkarılınca yalnız+0,34R kalıyor. Bu birleşimin üstünlüğü kanıtlanmış değil. UNION_MIXED+11,40R ile aynı-gün birleşiminin altında; en iyi5 çıkarılınca−0,32R.

| Kaynak | Dip bugün: n / R | Dip sonraki seans: n / R | Birleşim bugün: n / gün / R | Birleşim karışık: n / gün / R |
|---|---:|---:|---:|---:|
| M1 | 11 / +11.12 | 11 / +9.87 | 28 / 27 / +14.72 | 27 / 26 / +11.40 |
| Native15m | 24 / +19.73 | 24 / +18.60 | 49 / 47 / +21.92 | 47 / 45 / +18.27 |
| Native30m | 72 / +27.62 | 69 / +27.88 | 142 / 134 / +28.29 | 130 / 122 / +24.85 |
| H1_PROXY | 107 / +25.75 | 101 / +29.37 | 237 / 225 / +43.62 | 224 / 212 / +40.92 |

Dip alımını gece taşımak M1 ve15m toplamını düşürdü;30m/H1 toplamı az arttı.30m dip-next72 ham olaydan69, H1 107 ham olaydan101 çözülmüş işlem bıraktı; ertesi güne kalan pozisyonlar diğer olayları engelledi. H1 dip-next ve birleşim-mixedte ayrıca1 çözülemeyen çıkış var. Dönem sınırını aşan sonuçlar özetlere katılmadı. M1 gece kuralında11 işlem,9 takvim gecesi ve10 quote-gap içeren işlem var; gece taşımanın fiyat boşluklarıyla gerçek icra denetimi tamamlanmış değil.

H1_PROXY birleşiminde sayısal150 eşiği **aşılıyor**: aynı-gün237 işlem/225 gün, karışık224 çözülmüş işlem/212 gün. Dolayısıyla birleşimi “150 olay yok” diye reddetmek yanlış olur. Buna rağmen09:00 vekil açılış/seviye, next-H1 dolum ve varsayımsal spread; gerçek09:30/next-M1/lot/fill/finansman kartı eksik. Sayı şartı, diğer şartların yerine geçmez. Farklı veri tamamlık koşulları ve eksik mumlar nedeniyle bizim ham açılış sayıları W7 ile birkaç gün farklı; bu sayıları birleştirmedik.

| Birleşim bugün: kronolojik ilk / ikinci yarı EV | İlk yarı | İkinci yarı | DD |
|---|---:|---:|---:|
| M1 | +0.362 | +0.690 | 3.90 |
| Native15m | -0.001 | +0.877 | 4.58 |
| Native30m | +0.087 | +0.312 | 6.98 |
| H1_PROXY | +0.114 | +0.253 | 5.48 |

15m ilk yarı−0,001R ile sıfıra yakın/negatif; bağımsız dönem kararlılığı geçti denemez. H1 birleşim-same katkı aralığı da [−0,004,+0,165]R/gün ile sıfırı içeriyor. Pozitif mutlak getiri bootstrapı, mevcut tabana anlamlı ek katkı demek değildir.

| Karışık birleşim | Ana toplam R | Spread×3 | 1 puan kayma | Gece başına örnek5bp finansman |
|---|---:|---:|---:|---:|
| M1 | +11.40 | +11.17 | +11.28 | +11.15 |
| Native15m | +18.27 | +17.61 | +18.01 | +17.63 |
| Native30m | +24.85 | +23.50 | +24.11 | +23.27 |
| H1_PROXY | +40.92 | +39.02 | +38.58 | +39.07 |

5bp finansman günlük giriş-notional üzerinden **varsayımsal stres**; gerçek broker swap oranı değil. Gece fiyat yollarında tüm mevcut barlar kontrol edildi ve stopun altında açılış daha kötü bid ile dolduruldu. Normal seans arası kapanış ile kayıp veri tamamen ayrıştırılamıyor: saatlik karışık birleşimde67 işlemde quote-gap var. Sadece sonraki gözlenen açılışı görmek, boşluk içindeki fiyatı bilmek değildir. Aynı-gün birleşimde gece finansmanı yok.

DAX/günlük endeks kısmını da kaynak kod üzerinden inceledim: DAX pozitif aktarım hipotezini destekleyebilir, fakat bu tur yeni bir DAX icra testi yapmadım. DAX H1 Xetra17:30 yerine18:00 yaklaşımı ve kısmi-seans kabulü var. Günlük QQQ/NDXCASH “önceki dipten limit” kontrolü ise1×günlük-vol stopunu hiç uygulamıyor; günlük OHLC içinden gerçek next-M1 ve stop sırası da çıkarılamaz. Bu günlük sonuç CAPREV stoplu işlem kartıyla aynı değildir. Aynı günlerdeki NDX/QQQ/DAX olaylarını bağımsız örnekler gibi toplamadım.

TUR4 rastgele saat testi, seçilmiş **dip olayı gerçekleşen günlerde** yapılan şartlı bir karşılaştırma. Bu günlerin tamamını saat03:00 öncesinden seçebilmek mümkün değil; karşılaştırma zamanlamanın mekanizmasını betimler, tek başına uygulanabilir strateji/null veya gelecekte başarı olasılığı vermez. 200 tekrarın tümünü yenmek de gelecekte%100 başarı anlamına gelmez.

İcra denetimi:6 ek fikstür (gece stopu, kötü gap, çözülemeyen çıkış, ertesi gün pozisyon engeli, cooldown),4 açılış prefix denetimi ve120 işlem dosyasında gerekli tek-pozisyon koşulları geçti. Önceki kapanmamış açılış mumunun fiyatı/kapanışı giriş kararına alınmadı.

## 6. Zaman dilimleri, kaynaklar ve yürütme sınırları

M1 giriş tetikleri M1/M5/M15 tamamlanmış mumlarda; dolum ortak M1 yolunda. Eski kaynakların native15m/30m/H1 mumlarında ise sonraki **native bar açılışı** kullanılır. Bunlar next-M1 gerçek dolum değildir. Daha uzun barlarda intrabar sıra bilinmez; aynı barda stop ve hedef varsa stop önce varsayılır. Açılışta hedef aşılmışsa bunun daha sonraki stopa göre önce olduğu uygulanır.

| Kaynak/TF | Taban n | Taban toplam R | Yarı hedef toplam R | Tam hedef toplam R |
|---|---:|---:|---:|---:|
| M1 tetik / M1 icra | 11 | +11.12 | +7.65 | +4.18 |
| M5 tetik / M1 icra | 11 | +11.29 | +7.77 | +4.26 |
| M15 tetik / M1 icra | 11 | +11.08 | +7.74 | +4.41 |
| Native15m:2023–Tem2026 | 24 | +19.73 | +17.02 | +14.32 |
| Native30m:2021–Tem2026 | 72 | +27.62 | +23.77 | +19.91 |
| H1_PROXY:2016–Tem2026 | 107 | +25.75 | +20.93 | +16.11 |

- Native15m/30m'de önceki seans tam09:30–16:00 sayımı gerekli; eksik/yarım günler doldurulmadı. H1 bunu çözemez:09:00–16:00 minimumu önceki gerçek RTH dibinin **alt sınır yaklaşımı** olarak kullanıldı. H1_PROXY farklı tetik eşiğidir; birebir RTH doğrulaması sayılmadı.
- Native broker etiketleri NY+7 saat yorumuyla UTC'ye dönüştürüldü. Düzeltilmiş M1 ile sıfır kaydırmada fiyat eşleşmesi15m medyan0,9 puan;30m/H1 de10 puan eşiğinin altında. ±60 dakika kaydırma çok daha kötü. Yıllık hareket yoğunluğu15m/30m'deNY09:30,H1'de yıla göre09:00 veya10:00 barında; saat denetimi geçti.
- Native spread bilinmiyor: her tarafta0,6 baz puan fiyat payı ve0,2 puan kayma varsayıldı. M1Dukascopy gerçek ask/bid; doğrudanMT5 kayıtlı bar spreadi; eski cache1,3 puan spread varsayımı. Komisyon ayrıca modellenmedi. Sonuçlar gerçek hesap USD kârı değil, başlangıç risk birimiR.
- M1 ana örneklem2025Duka+2026MT5/cache olmak üzere11 uygun gün;18May2026 dondurulmuş iki bölümün arasındadır, ham CSV'de saklandı ama ana11'e katılmadı. Önceki raporla taban birebir eşleşti. Eylül–1Ekim'de CAP olayı yok.
- Native15m24,30m72,H1proxy107 taban olayı: bunlar örtüşen yıllar ve çoğunlukla aynı günlerdir. Toplayıp203 bağımsız olay denemez. H1'de2 veri-boşluğu çıkışı var; hepsini en az−1R sayınca taban EV0,241→0,234R, yarı hedef0,196→0,189R, tam hedef0,151→0,144R. M1/15m/30m CAP serilerinde böyle çıkış yok.
- Portföyde eski stratejilerden kaynaklanan boşluk çıkışları da görünür. Hepsi en az−1R sayılınca taban toplamı+1,68R, artanVIX/tamhedef portföyü+11,08R. Bu alt sınır gerçek boşluk dolumu tahmini değildir.
- 13 icra fikstürü: yarım çıkış muhasebesi, aynı-barda stop/TP, hedefte açılış, kötü gap dolumu,10:00'daki kapanmış bilgi, geç giriş, boşluk, gecikme, native spread. Altı farklı M1/native prefix denetimi ve80 portföy CSV'sinde tek toplam pozisyon/600s giriş aralığı geçti. Gelecek verisi giriş şartına katılmadı.

Resmî09:30–16:00 normal seans tanımı için [Nasdaq Equity1](https://listingcenter.nasdaq.com/assets/RuleBook/Nasdaq/rules/Nasdaq%20Equity%201.html); tekrar tekrar aynı geçmişte strateji seçiminin riski için [Bailey ve diğerlerinin birincil araştırması](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) kullanıldı. Bu araştırmanın ham bootstrap oranları seçim geçmişini temizlemez.

## 7. Nihai sıralama

1. **CAPREV günlük-vol +1R hedef/−1R stop, artanVIX şartı:** en anlamlı yeni portföy hipotezi. Daha erken sermaye kullanımı faydalı görünüyor;7 etkilenen gün ve sıfırı içeren katkı aralığı nedeniyle araştırma/SHADOW. Mevcut TP80/SL110 kuralına eşdeğer değildir.
2. **CAPREV yarı+1R / yarı16:00:** uç gün bağımlılığını ve bazı drawdown'ları azaltan risk yönetimi adayı. Aynı başlangıç riskiyle toplam kazancı azaltır. ArtanVIX ile saatlik ilk yarısı negatif; güçlü evrensel birleşim değil.
3. **CAPREV tam+1R, VIX-yön filtresiz kontrol:** native15m/30m/H1'de daha dengeli getiri dağılımı; özellikle saatlik yıllardan yalnız2016negatif (tek olay). Fakat107 olay ve küçük bazı yıllar yeterli canlı kanıtı değil. Kontrolden çıkan bulgu diye etiketlendi.
4. **Stres+yüksekVIX açılış/dip fırsatları, tek pozisyon ve aynı-gün kapanış:** v2'den türetilen sermaye çakışması varyasyonu; M1'de28 işlem/27 gün+14,72R. Dip tabanına göre toplamı artırdı ama drawdown da yükseldi; katkı güven aralığı sıfırı içeriyor,15m ilk yarısı negatif. Diğer beşli portföye ek katkısı bu tur ölçülmedi.
5. **Dip alımını sonraki nakit seansa taşıma:** v2 gece varyasyonunun tek-pozisyon denetimi. M1'de11 işlem+9,87R ile aynı günün altında;30m/H1 toplamı biraz iyileşti. Evrensel daha iyi çıkış olarak desteklenmedi; fiyat boşluğu ve gerçek finansman nedeniyle ikinci planda.

FRESH_CROSS/CASH_ONLY/FAIL_10/VIX_COOLING mevcut tanımlarla tabana üstünlük getirmedi; ek filtre olarak önerilmiyor. Açılış-bugün/dip-yarın karışımı da aynı-gün birleşimi geçmedi. Beş sıralama maddesi beş kanıtlı kâr kapısı değildir. Önceki K5b/CHASE bu turda yeni keşif diye sayılmadı.
İleri doğrulama: final kurallar değiştirilmeden tamamen yeni dönem veya daha önce görülmemiş güvenilirM1 geçmiş, aynı nakit riskle gerçek spread/lot/fill, gerçek bot niyetleri ve tek toplam pozisyon;>=150 çözülmüş uygun olay, iki kronolojik yarı, pozitif netEV/bootstrapping ve maliyet kartı. Geçmiş yılları farklıTF'lerde tekrar sayarak örnek eşiği doldurulamaz. Şu anda LIVE onayı yok.

## 8. Görseller ve yeniden üretim

![Getiri dağılımı karşılaştırması](results/payoff_comparison.png)

![İlk kazanan, ilk kaybeden ve ilk kısmi hedef](results/trade_examples.png)

Ayrı protokoller: `PROTOCOL.md`, `PROTOCOL_COMBINATIONS.md`, `PROTOCOL_PORTFOLIO.md`, `PROTOCOL_OVERNIGHT.md`. Çıktılar: `results/evaluation.json`, `combinations.json`, `portfolio.json`, `aggregate.json`, işlemCSV'leri, `verification.json`, `payoff_identity.json`, `final_audit.json`, `overnight.json`, `overnight_verification.json`, `provenance.json`.

```bash
python3 research/ndx_caprev_paths_20261002/paths.py
python3 research/ndx_caprev_paths_20261002/verify.py
python3 research/ndx_caprev_paths_20261002/combine.py
python3 research/ndx_caprev_paths_20261002/portfolio.py
python3 research/ndx_caprev_paths_20261002/overnight.py
python3 research/ndx_caprev_paths_20261002/verify_overnight.py
python3 research/ndx_caprev_paths_20261002/make_report.py
```
