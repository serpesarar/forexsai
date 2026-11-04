"""Build an inspectable Turkish report from saved experiment evidence."""
import json
import math
import pandas as pd
from data_audit import HERE, SYMBOLS
OUT=HERE/'results'

def table(rows,cols):
 lines=['| '+' | '.join(label for _,label in cols)+' |','| '+' | '.join('---' for _ in cols)+' |']
 for row in rows:
  lines.append('| '+' | '.join(str(row.get(key,'—')) for key,_ in cols)+' |')
 return '\n'.join(lines)
def fmt(v,n=3):
 try:return f'{float(v):+.{n}f}' if math.isfinite(float(v)) else '—'
 except:return '—'

def main():
 s=pd.read_csv(OUT/'summary.csv');t=pd.read_csv(OUT/'trades.csv');aud=json.loads((OUT/'causality.json').read_text());full=json.loads((OUT/'full_prefix_checks.json').read_text());cards=json.loads((OUT/'research_cards.json').read_text())
 dev=s[(s.epoch=='development')];test=s[s.epoch=='test'];nonzero=test[test.n>0]
 native=json.loads((OUT/'native_smoke.json').read_text());inventory=json.loads((OUT/'example_inventory.json').read_text());cov=json.loads((OUT/'data_audit.json').read_text());cross=aud['audits'][-1]
 report=f'''# Vibe-Trading — ForexSAI verileriyle nedensel sınama

Tarih: 22 Ekim 2026. **Sonuç: 54 hücrenin hiçbirinde tüm araştırma koşulları sağlanmadı; canlıya uygunluk kanıtı yok.**
Bu sonuç yalnız aşağıdaki hazır örneklere ve tanımlanmış icraya aittir; Vibe-Trading ile üretilebilecek bütün stratejiler hakkında hüküm değildir.

Kaynak: [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading),
[sabit commit](https://github.com/HKUDS/Vibe-Trading/tree/11cff3f3a2d89605c89148b03dcc2dd0fcfb60db).
MIT lisanslı kod indirildi, {len(json.loads((OUT/'source_manifest.json').read_text()))} kaynak dosyası Git blob kimliğiyle doğrulandı;
[sıkıştırılmış kaynak](source_snapshot.tar.gz), [kaynak manifestosu](results/source_manifest.json).

## Ne sınandı?

Görseldeki ürün tek bir dondurulmuş işlem kuralı değildir; LLM, veri araçları, strateji örnekleri ve backtest motoru içeren bir çerçevedir.
Bu çalışma **orijinal yedi deterministik SignalEngine örneğini** varsayılan parametrelerle çalıştırdı.
LLM ajan takımı, haber tarama, dış MCP araçları ve otomatik emir yürütme bu testin parçası değildir.
Eski bir tarihi güncel LLM prompt'una yazmak modelin eğitimindeki gelecek bilgisini silmez; o yüzden bu rapor geçmiş LLM karar performansı iddia etmez.
İndirilen README/skill talimatları kaynak malzeme kabul edildi; proje talimatlarını geçersiz kılmadı.

Yedi örnek: teknik temel (EMA/ADX + BB/RSI + OBV), mum desenleri, Ichimoku, volatilite,
mevsimsellik, harmonik (yerleşik fallback), Elliott. İki frekans × dört sembol × yedi örnek = 56;
uzun XAU/OIL teknik temelde hacim yok → **54 geçerli test hücresi**. Bunların {len(nonzero)}'inde test işlemi oluştu;
Elliott'un 8 hücresinde varsayılan kuralla işlem oluşmadı. Parametre optimizasyonu: **0**.

Frekans aktarımı açıkça yapıldı: örnekteki 20 bar, 5m'de 100 dakika, 1h'de 20 saattir; 20 günlük kuralın aynı olduğu iddia edilmiyor.
0=FLAT, +1=BUY, −1=SELL hedef pozisyonudur. Ichimoku/harmonik olayından sonra gelen 0 konumu kapatır;
karşıt sinyale kadar tutma veya sonradan TP/SL ekleme yapılmadı. Tüm örnekler aynı sözleşmeyle sınandı.

## Gelecek bilgisi denetimi

- İlk 800 yakın dönem barında dört sembol × yedi örnek = **28/28** prefix/gelecek değiştirme denetimi geçti.
  Toplam {sum(x.get('checks',0) for x in aud['audits'][:-1]):,} geçmiş sinyal değeri karşılaştırıldı.
- Asıl veri üzerinde erken/orta/son önekler: **{sum(x['passed'] for x in full)}/{len(full)}** geçti.
- Harmonik ve Elliott sağ taraftan teyit gerektiren pivotları teyit barına geciktiriyor; kodda merkezli pencere bulunması tek başına sızıntı sayılmadı.
- **cross-market-strategy sızıntılı:** `_vol_adjust`, son 20 barın volatilitesinin son değerini bütün geçmişin ağırlığı yapıyor.
  Aynı anda dört sembol verildiğinde önek kısalınca geçmiş ağırlıkları değişti; {len(cross['errors'])} hata kaydı oluştu.
  Gelecek fiyat/hacim pertürbasyonu geçmiş çıktıyı da değiştirdi. Bu örnek performans tablolarına alınmadı.
- Aynı örneğin sembol tanıması bu dört CFD ismini `a_share` varsayıyor. ForexSAI sembol/spec adaptörü olmadan varsayılan motor seçimine güvenilmedi.

Bunlar dinamik örneklem denetimidir; tüm olası girdiler için matematiksel ispat değildir.
[İlk denetim](results/causality.json), [tam veri önekleri](results/full_prefix_checks.json),
[sızıntılı kaynak](upstream/agent/src/skills/cross-market-strategy/example_signal_engine.py).

## Veri ve saat ekseni

Yakın dönem: mevcut `indicator_snapshots` 1m yerel cache; 16/17 Haziran–20/21 Ekim 2026.
Eski broker saatlerine projenin `normalize_snapshot_clock` düzeltmesi uygulandı (28 Temmuz öncesi −3 saat;
18:00–21:00 belirsiz geçişi at). Her sembolün son M1 kaydı çıkarıldı.
5m mumları yalnız beş dakikanın tamamı varsa oluştu; sağ kenar kapanış damgalı.

Uzun 1h: NDX 2016–2026, DAX 2019–2026; XAU/OIL 2016–2 Eylül 2026, yalnız broker kaynaklı.
Yahoo vadeli emtia uzantısı dışlandı. İki veri ailesi birleştirilmedi.
Kullanılan bütün dosyalarda yinelenen zaman ve geçersiz OHLC sayısı **0**.

{table([dict(symbol=r['symbol'],dataset=r['dataset'],rows=f"{r['rows']:,}",start=r['start'][:16],end=r['end'][:16]) for r in cov if r['dataset']!='recent_m1'], [('symbol','Sembol'),('dataset','Veri'),('rows','Bar'),('start','Başlangıç UTC'),('end','Son kapanış UTC')])}

Saat çapraz kontrolü: uzun saatlik veri ile normalize M1→1h kesişiminde en düşük medyan kapanış farkı dört sembolde de **0 dakika** kaymada.
NDX/DAX/XAU medyan fiyat farkı 0; OIL'de 0,379 fiyat birimi baz farkı var. OIL geçmişlerini birleştirmemek bu yüzden de gerekli.
Bu denetim saat uyumunu destekler, iki fiyat kaynağının birebir aynı olduğu anlamına gelmez.
[Tam veri denetimi ve hash'ler](results/data_audit.json), [saat karşılaştırması](results/clock_overlap.json).

## İcra ve ölçüm

Karar yalnız kapanmış barla. Yakın testte giriş/çıkış ilgili karar anındaki **sonraki M1 açılışı**;
sinyali oluşturan 5m barın kapanış fiyatından dolum yapılmıyor. Gerekli açılış yoksa yeni giriş yok.
Uzun 1h'de sonraki 1h açılışı kullanıldı: bu kısım M1 doğrulaması değildir.
Tek pozisyon/sembol/örnek; ters sinyalde kapat ve yeni yön aç. Gelecek fiyatı büyüklük seçmekte kullanma.

Tam spread varsayımı: NDX 1,5 puan, DAX 1,5 puan, XAU 0,25$, OIL 0,03$.
Dolum başına ek 0,1×spread kayma → işlemde toplam 1,2×spread. Stres tüm maliyetin ×1,5'i.
Tarihsel gerçek bid/ask, komisyon ve swap kayıtları yok; sonuçlar **tahmini maliyetlidir**, gerçek broker neti değildir.
Gecelik taşımalarda eksik swap özellikle önemlidir.

Veri boşluğunu önceden bilip önceki kapanıştan kaçış yok: açık pozisyon boşluktan sonraki ilk gözlenen açılışta kapanır.
Değerlendirme sonu kapanışları ayrı etiketlidir. Fiyat boşlukları ve endpoint kapatmaları [işlem CSV'sinde](results/trades.csv) görünür.
Barlar arası gizli likidite/kayma ve stop içi yol simüle edilmez.

R = karar anındaki **2×ATR14 fiyat mesafesi**. Örneklerde gerçek SL/TP yoktur; R risk referansıdır,
−1R'de çıkış garantisi değildir. Toplam R, gerçek sermaye getirisi değildir; DD yalnız kapanmış işlem R eğrisidir,
pozisyon içi mark-to-market DD ve sermaye/marj modelini içermez. bp, işlem başlangıç fiyatına göre net baz puandır (1 bp=%0,01).

Geliştirme/sınama: uzun veride 2024-01-01, yakın veride 2026-09-01. Açık işlemler sınırdan taşınmaz;
ısınma fiyatları kullanılabilir, etiket/sonuçlar kullanılmaz. Bu fiyat geçmişleri başka proje araştırmalarında da görüldü;
"ilk kez görülen bağımsız piyasa" iddiası yok.

Gün-blok bootstrap 2.000 tekrar; Wilson %95 WR aralığı. Plasebo: aynı giriş/çıkış yolu ve masraf üzerinde
**gün bazında rastgele yön çevirme**, 10.000 tekrar. Bu kontrol yön katkısını sınar;
aynı yön/saatte rastgele başka girişlerin tam bir zamanlama kontrolü değildir.
Buy-and-hold ayrıca hesaplandı; maruziyet/tutuş eşit olmadığı için doğrudan üstünlük kanıtı değildir.
54 test hücresine Holm düzeltmesi; sonuçtan sonra en iyiyi seçip doğrulandı deme yok.
İlk 1.000 plasebonun Holm eşiğine sayısal olarak yetmemesi düzeltmesi ön kaydın EK-2'sinde açıklandı.

## Dönem dışı sonuçların tamamı

**Hiçbir hücre Holm kontrol eşiğini geçmedi. {sum(c['research_candidate'] for c in cards)}/54 araştırma adayı.**
N>0 olan {len(nonzero)} hücrenin {int((nonzero.mean_R>0).sum())}'inde ortalama R pozitif;
pozitif ortalama tek başına tekrarlanabilir üstünlük değildir. Elliott'da işlem olmaması performans kanıtı değildir.

![Dönem dışı net R karşılaştırması](results/oos_heatmap.png)

'''
 for dataset,title in [('recent_5m','Yakın 5m — 1 Eylül–20/21 Ekim 2026'),('long_1h','Uzun 1h — 2024 ve sonrası')]:
  rows=[]
  for _,r in test[test.dataset==dataset].iterrows():
   rows.append(dict(symbol=r.symbol,strategy=r.strategy,n=int(r.n),wr=f'{r.win_rate:.1f}' if pd.notna(r.win_rate) else '—',mean=fmt(r.mean_R),bp=fmt(r.mean_bp,2),stress=fmt(r.stress_R),dd=fmt(r.dd_R,1),ci=f'[{fmt(r.ci_low)}, {fmt(r.ci_high)}]' if pd.notna(r.ci_low) else '—'))
  report+=f'### {title}\n\n'+table(rows,[('symbol','Sembol'),('strategy','Örnek'),('n','n'),('wr','WR %'),('mean','Ort net R'),('bp','Net bp/işlem'),('stress','Stres R'),('dd','DD R'),('ci','EV %95 aralık')])+'\n\n'
 report+='''Pozitif istisnaları güçlü kanıt diye yorumlamamak gerekir:

- NDX teknik temel 5m: +0,039R, 501 işlem, WR %35,7; stres +0,018R, yalnız +0,15 bp/işlem.
  Aynı örneğin uzun 1h sınaması −0,029R. Bağımsız, maliyete dayanıklı üstünlük kanıtı oluşmadı.
- XAU mevsimsellik 5m: WR %72,7 ama yalnız 22 işlem. DAX mevsimsellik de 22 işlem.
  Küçük örnek, gecelik taşıma ve kontrol testi yüzünden bu satırlar aday değil.
- OIL mevsimsellik 1h: +0,308R, 145 işlem; asgari 150 test işlemi yok ve çoklu kontrol anlamlı değil.
- DAX'ta bazı R-pozitif satırların net bp ortalaması negatiftir: ATR'yle risk ağırlığı değişince ölçüm ağırlıkları değişir.
  Bu, tek başına "kâr eden lot stratejisi" olarak okunamaz.

[Geliştirme + sınama özet CSV](results/summary.csv), [yön dökümü](results/by_side.csv),
[yıl dökümü](results/by_year.csv), [buy-and-hold](results/buy_hold.csv),
[koşul kartları](results/research_cards.json), [tüm varsayımsal işlemler](results/trades.csv).
Farklı strateji/frekans satırları ortak fiyat geçmişi kullandığından tek bir portföy veya bağımsız işlem havuzu gibi toplanamaz.

## Kazanç/kayıp örnekleri

Her sembolde teknik temel 5m sınamasının kronolojik **ilk kazancı ve ilk kaybı** seçildi.
Bunlar açıklayıcı grafiklerdir; kuralın doğruluğunun kanıtı değildir. Gri alan karar sonrası yoldur;
sinyal bu veriyi görmedi. TP/SL olmadığı grafikte açıkça belirtilmiştir.

![Sekiz betimsel işlem örneği](results/trade_examples.png)

## Orijinal motorun çalışabilirliği

Orijinal upstream ForexEngine, her sembolde son 800 yerel 5m bar üzerinde teknik temel örneğiyle
çalıştırıldı. CFD fiyat/spread ve miktar birimleri küçük bir LocalCFD adaptörüyle açıkça tanımlandı;
Forex paritesi varsayılan pip/lot sayıları endekslere uygulanmadı. Hesap bağlantısı yok, swap kapalı.
Bu çalışabilirlik kontrolüdür; ayrı tarih aralığı ve sermaye modeli nedeniyle ana R tablosuyla aynı sonuç beklenmez.

'''
 report+=table([dict(symbol=x['symbol'],passed=x['passed'],trades=x.get('trades',0),fills=x.get('fills',0)) for x in native],[('symbol','Sembol'),('passed','Başarılı'),('trades','Kapanmış işlem'),('fills','Dolum')])
 report+='\n\n[Native motor kanıtı](results/native_smoke.json), [orijinal motor çıktıları](results/native/).\n\n'
 report+='''## Diğer örneklerin kapsam durumu

'''+table(inventory,[('example','Örnek'),('status','Kapsam / neden')])+'''

SMC/Chanlun, bu çalışmada kurulup sınanmış gibi sunulmuyor. PIT haber, bilanço, opsiyon zinciri veya
önceden seçilmiş çift verisi olmayan örnekler için veri uydurulmadı.

## Teslim ve sonraki somut doğrulama

Yeniden çalıştırma: [README](README.md), [ön kayıt](PROTOCOL.md), [5 icra sözleşmesi testi](selftest.py).
Canlı bot, sinyal kapısı, strateji ayarı, deployment veya üretim veritabanı değişikliği yapılmadı.
Kaynak, kod ve rapor yerel araştırma klasöründe; Evolution kayıtları yalnız bu analizi kataloglar.

Tam LLM takımını değerlendirmek için sonraki geçerli deney, **gelecekte toplanacak gölge kararlar**dır:
model/sürüm/prompt sabitlenir; araçlar yalnız karar anında bilinen mum/haber döndürür; karar önceden
değiştirilemez kayda yazılır; broker bid/ask ve sonraki M1 dolum kaydedilir; en az 150 çözülmüş bağımsız
olaydan sonra proje go-live kartıyla değerlendirilir. Bu araştırma böyle bir deneyi başlatmadı ve LIVE kararı vermedi.
'''
 (HERE/'RAPOR.md').write_text(report)
 print('RAPOR.md written;',len(t),'simulated round trips across development+test; no pooling claim')
if __name__=='__main__':main()
