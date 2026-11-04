"""Render the v2 source audit and frozen phase4 findings into the final report."""
import json
from paths import OUT

def section():
    x=json.loads((OUT/'overnight.json').read_text())
    def get(source,rule,case='base'):
        return x['M1'][case+'/'+rule] if source=='M1' else x['sources'][source]['results'][case+'/'+rule+'/aggregate']
    lines=['## 5b. v2/TUR4: açılış, gece ve iki aşamalı giriş denetimi','',
        'v2 yeni bir fikir getiriyor: stresli günün nakit açılışından alım ve dip-kırılımı alımını birleştirmek. Ancak `w7.py` açılış ve dip işlemlerini ayrı ayrı çözüp R değerlerini **topluyor**; açık pozisyon varken ikinci giriş engellenmiyor. İki bacak da1 risk birimi taşıyabiliyor. 223 olay, iki bacak toplamının hesaplandığı **benzersiz gün** sayısı; tek-pozisyon kartının doğrulanmış işlem sayısı değil. Saatlik açılış da09:30 yerine09:00 barı. Bu ayrımlar sonucu yorumlamak için gerekli.','',
        'Rapordaki H1 +0,269R/gün, W7 çıktısında **iki bacağın da aynı gün16:00 kapandığı** toplamdır. İki bacağın da ertesi gün kapandığı değer+0,252R/gün. Metinde tarif edilen açılış-bugün/dip-yarın karışımının performansı bu iki sayıdan okunamaz. Aynı sermaye riskini iki önceden ayrılmış yarım bütçeye bölünce+0,269R, toplam bütçe başına yaklaşık **+0,135R/gün** olur; tek açılış bacağının+0,154R/gün değerinden düşük. Bu basit normalizasyon, daha fazla risk kullanarak artan R toplamını ayrı bir yönsel üstünlük gibi yorumlamayı önler; gerçek lot, stop-gap ve sermaye verimliliği kartının yerine geçmez.','',
        'Altı tanım ayrıca donduruldu: OPEN_SAME, DIP_SAME, DIP_NEXT, OPEN_NEXT, UNION_SAME ve UNION_MIXED. Birleşimlerde tüm fırsatlar kronolojik sıralanır; açılış/dipten hangisi önce gelirse boş pozisyonda o alınır. Aynı dakika açılış önceliklidir. Stopla boşalınca sonraki dip/açılış olayı,600 saniye giriş aralığı uygunsa alınabilir. DIP_NEXT/OPEN_NEXT tek başına da ertesi güne açık kalan işlemi atlayarak çözülür. UNION_MIXED açılışı aynı gün, dip alımını bir sonraki **nakit işlem seansı**16:00 kapatır; takvimde ertesi gün varsayılmaz.','',
        '| M1 tanımı | İşlem / benzersiz gün | Toplam R | EV / işlem | DD |',
        '|---|---:|---:|---:|---:|']
    names={'OPEN_SAME':'09:30 al / bugün16:00','DIP_SAME':'Dip al / bugün16:00','DIP_NEXT':'Dip al / sonraki seans16:00','OPEN_NEXT':'09:30 al / sonraki seans16:00','UNION_SAME':'Tek pozisyon, iki fırsat / bugün16:00','UNION_MIXED':'Tek pozisyon, açılış bugün / dip sonraki seans'}
    for rule in x['configurations']:
        a=get('M1',rule)
        lines.append(f"| {names[rule]} | {a['n']} / {a['unique_days']} | {a['total_R']:+.2f} | {a['ev']:+.3f} | {a['drawdown_R']:.2f} |")
    u=get('M1','UNION_SAME');p=u['paired']
    lines+=['',
        f"M1'de UNION_SAME tabanın+11,12R'sine karşı **+14,72R**, fakat DD1,09→3,90R. Başka günlerde de risk kullanarak daha fazla kazanıyor; risk başına ortalaması tabanın1,011R'sinden0,526R'ye düşüyor. Tabana günlük katkı aralığı **[{p['ci95'][0]:+.3f},{p['ci95'][1]:+.3f}]R** ve sıfırı içeriyor. En iyi5 işlem çıkarılınca yalnız+0,34R kalıyor. Bu birleşimin üstünlüğü kanıtlanmış değil. UNION_MIXED+11,40R ile aynı-gün birleşiminin altında; en iyi5 çıkarılınca−0,32R.",'',
        '| Kaynak | Dip bugün: n / R | Dip sonraki seans: n / R | Birleşim bugün: n / gün / R | Birleşim karışık: n / gün / R |',
        '|---|---:|---:|---:|---:|']
    for source,label in [('M1','M1'),('native15','Native15m'),('native30','Native30m'),('native60','H1_PROXY')]:
        a,b,c,d=[get(source,r)for r in ['DIP_SAME','DIP_NEXT','UNION_SAME','UNION_MIXED']]
        lines.append(f"| {label} | {a['n']} / {a['total_R']:+.2f} | {b['n']} / {b['total_R']:+.2f} | {c['n']} / {c['unique_days']} / {c['total_R']:+.2f} | {d['n']} / {d['unique_days']} / {d['total_R']:+.2f} |")
    lines+=['',
        'Dip alımını gece taşımak M1 ve15m toplamını düşürdü;30m/H1 toplamı az arttı.30m dip-next72 ham olaydan69, H1 107 ham olaydan101 çözülmüş işlem bıraktı; ertesi güne kalan pozisyonlar diğer olayları engelledi. H1 dip-next ve birleşim-mixedte ayrıca1 çözülemeyen çıkış var. Dönem sınırını aşan sonuçlar özetlere katılmadı. M1 gece kuralında11 işlem,9 takvim gecesi ve10 quote-gap içeren işlem var; gece taşımanın fiyat boşluklarıyla gerçek icra denetimi tamamlanmış değil.','',
        'H1_PROXY birleşiminde sayısal150 eşiği **aşılıyor**: aynı-gün237 işlem/225 gün, karışık224 çözülmüş işlem/212 gün. Dolayısıyla birleşimi “150 olay yok” diye reddetmek yanlış olur. Buna rağmen09:00 vekil açılış/seviye, next-H1 dolum ve varsayımsal spread; gerçek09:30/next-M1/lot/fill/finansman kartı eksik. Sayı şartı, diğer şartların yerine geçmez. Farklı veri tamamlık koşulları ve eksik mumlar nedeniyle bizim ham açılış sayıları W7 ile birkaç gün farklı; bu sayıları birleştirmedik.','',
        '| Birleşim bugün: kronolojik ilk / ikinci yarı EV | İlk yarı | İkinci yarı | DD |',
        '|---|---:|---:|---:|']
    for source,label in [('M1','M1'),('native15','Native15m'),('native30','Native30m'),('native60','H1_PROXY')]:
        a=get(source,'UNION_SAME');h=a['halves']
        lines.append(f"| {label} | {h[0]['ev']:+.3f} | {h[1]['ev']:+.3f} | {a['drawdown_R']:.2f} |")
    lines+=['',
        '15m ilk yarı−0,001R ile sıfıra yakın/negatif; bağımsız dönem kararlılığı geçti denemez. H1 birleşim-same katkı aralığı da [−0,004,+0,165]R/gün ile sıfırı içeriyor. Pozitif mutlak getiri bootstrapı, mevcut tabana anlamlı ek katkı demek değildir.','',
        '| Karışık birleşim | Ana toplam R | Spread×3 | 1 puan kayma | Gece başına örnek5bp finansman |',
        '|---|---:|---:|---:|---:|']
    for source,label in [('M1','M1'),('native15','Native15m'),('native30','Native30m'),('native60','H1_PROXY')]:
        vals=[get(source,'UNION_MIXED',case)['total_R']for case in ['base','spread3','slip1','funding5bp']]
        lines.append('| '+label+' | '+' | '.join(f'{v:+.2f}'for v in vals)+' |')
    lines+=['',
        '5bp finansman günlük giriş-notional üzerinden **varsayımsal stres**; gerçek broker swap oranı değil. Gece fiyat yollarında tüm mevcut barlar kontrol edildi ve stopun altında açılış daha kötü bid ile dolduruldu. Normal seans arası kapanış ile kayıp veri tamamen ayrıştırılamıyor: saatlik karışık birleşimde67 işlemde quote-gap var. Sadece sonraki gözlenen açılışı görmek, boşluk içindeki fiyatı bilmek değildir. Aynı-gün birleşimde gece finansmanı yok.','',
        'DAX/günlük endeks kısmını da kaynak kod üzerinden inceledim: DAX pozitif aktarım hipotezini destekleyebilir, fakat bu tur yeni bir DAX icra testi yapmadım. DAX H1 Xetra17:30 yerine18:00 yaklaşımı ve kısmi-seans kabulü var. Günlük QQQ/NDXCASH “önceki dipten limit” kontrolü ise1×günlük-vol stopunu hiç uygulamıyor; günlük OHLC içinden gerçek next-M1 ve stop sırası da çıkarılamaz. Bu günlük sonuç CAPREV stoplu işlem kartıyla aynı değildir. Aynı günlerdeki NDX/QQQ/DAX olaylarını bağımsız örnekler gibi toplamadım.','',
        'TUR4 rastgele saat testi, seçilmiş **dip olayı gerçekleşen günlerde** yapılan şartlı bir karşılaştırma. Bu günlerin tamamını saat03:00 öncesinden seçebilmek mümkün değil; karşılaştırma zamanlamanın mekanizmasını betimler, tek başına uygulanabilir strateji/null veya gelecekte başarı olasılığı vermez. 200 tekrarın tümünü yenmek de gelecekte%100 başarı anlamına gelmez.','',
        'İcra denetimi:6 ek fikstür (gece stopu, kötü gap, çözülemeyen çıkış, ertesi gün pozisyon engeli, cooldown),4 açılış prefix denetimi ve120 işlem dosyasında gerekli tek-pozisyon koşulları geçti. Önceki kapanmamış açılış mumunun fiyatı/kapanışı giriş kararına alınmadı.','']
    return lines
