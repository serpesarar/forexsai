# Ek protokol — diğer raporun TUR3 ekinin icra denetimi

Ana 14 tanım değişmedi. Çalışırken `RAPOR.md` sonundaki TUR3 bağlantısı ve
`NIHAI_RAPOR.md` görüldü. Bu ekin bütün sonuçları, **1 Ekim dahil**, artık
retrospektif sayılacak; yeni günün mumları ana protokol için önceden alınmıştı.

Ek sekiz tanım, eşik araması yok:

1. **CAPREV:** önceki nakit gün stresli, önceki VIX>=18.4, NY03:00–15:00 arasında
   ilk tam bar kapanışı önceki tam RTH dibinin altında; BUY. Stop mesafesi önceki
   20 nakit gün getirisinin örnek standart sapması × giriş fiyatı. TP yok, NY16:00
   M1 açılışında kapat. Spread/iki yönlü kayma, bar içi stop ve açılış boşluğu uygulanır.
2. Aynı kural VIX şartı olmadan.
3. Aynı kural VIX<18.4.
4. Stressiz gün + VIX>=18.4, aynı ilk dip-altı kapanış BUY (rejim kontrolü).
5. CAPREV olayında SELL (yön kontrolü).
6. CAPREV aynı olay TP80/SL110, en geç16:00 (çıkış geometrisi kontrolü).
7. Stres+yüksek VIX altında H5 geri-alım koşulunun ilk olayı, CAPREV'in aynı
   günlük-vol stopu ve16:00 çıkışı (teyit karşılaştırması; farklı olay zamanı).
8. **CHASE:** mevcut beşli portföyde SELL için dört bileşenden>=3 ise veto:
   son tam M5'in 50-bar regresyon kanalındaki konumu<=−1σ; M15 aşağı hizalı;
   fiyat önceki tam RTH dibinden aşağıda; önceki nakit gün stresli.

CAPREV 1/5/15 dakikalık **tam bar tetikleyicileri**, ortak M1 yürütme yolu,
beş tarih bölmesi ve iki ek gün; base/spread3/slip1/delay1. CHASE 1/3/5 tetikleyici
portföyün önceden tanımlanmış geometri/sıralamasıyla aynı streslerden geçer.
1h, 30m, 15m eski rapordaki yıllık oranlar bize ait yeni doğrulama diye sunulmaz.
H1 tarih verisinin RTH09:00–16:00 yaklaşımı, gerçek09:30–16:00 ile aynı seviye
değildir. Eksik önceki RTH seansı pas geçilir; yarım günler doldurulmaz.

Toplam bu turda 22 sabit yapılandırma; geçmiş turların seçim yükü ayrıca vardır.
Ek tanımlar keşfedilmiş olumlu rapordan türetildiği için p-değeri keşif yanlılığını
gidermez. Başarı sınıfı raporlardaki harf notundan devralınmayacak.
