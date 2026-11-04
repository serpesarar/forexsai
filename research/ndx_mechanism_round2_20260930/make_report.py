"""Turkish research report and representative, non-curated charts."""
import hashlib
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as md
from data import HERE, ROOT, OUT, lab, datasets
from experiment import TITLES


def plots(result):
    fig,axes=plt.subplots(5,2,figsize=(15,17),constrained_layout=True)
    ds=datasets()
    for i,r in enumerate(result["candidates"]):
        ident=r["spec"]["id"]
        for j,positive in enumerate([True,False]):
            ax=axes[i,j];chosen=None;period=None
            for p in ["S26","M26","C26","D25b","D25a"]:
                rows=pd.read_csv(OUT/f"trades_{ident}_{p}.csv")
                rows=rows[rows.R.gt(0) if positive else rows.R.lt(0)]
                if len(rows):chosen=rows.iloc[0];period=p;break
            if chosen is None:ax.text(.2,.5,"No example",transform=ax.transAxes);continue
            row=chosen;d=ds["duka" if period.startswith("D25") else "mt5"]
            w=int(r["spec"]["variant"][-1])if r["spec"]["family"]in["D2","D3"]else 0
            origin=int(row.decision)-w*60
            z=d[(d.t>=origin-30*60)&(d.t<=row.exit_t+10*60)]
            tt=pd.to_datetime(z.t,unit="s",utc=True).dt.tz_convert("America/New_York")
            ax.vlines(tt,z.low,z.high,alpha=.3,color="#385678",linewidth=.65)
            ax.plot(tt,z.close,lw=.85,color="#244969")
            ax.axhline(row.entry,color="#7864b5",lw=1,label="entry")
            ax.axhline(row.entry+row.side*80,color="#17815e",lw=.8,ls="--",label="TP80")
            ax.axhline(row.entry-row.side*110,color="#b84141",lw=.8,ls="--",label="SL110")
            decision=pd.Timestamp(int(row.decision),unit="s",tz="UTC").tz_convert("America/New_York")
            orig=pd.Timestamp(origin,unit="s",tz="UTC").tz_convert("America/New_York")
            exit_t=pd.Timestamp(int(row.exit_t),unit="s",tz="UTC").tz_convert("America/New_York")
            ax.axvspan(tt.iloc[0],orig,color="#e8e9f2",alpha=.65)
            if w:ax.axvspan(orig,decision,color="#f2dc9d",alpha=.4)
            ax.axvline(decision,color="#7864b5",lw=1)
            ax.scatter(exit_t,row.exit,color="#17815e"if positive else"#b84141",s=28,zorder=4)
            ax.set_title(f"{ident} | {'first win'if positive else'first loss'} | {period}\n{decision:%Y-%m-%d %H:%M} NY | {'BUY'if row.side>0 else'SELL'} | {row.R:+.3f}R",fontsize=10)
            ax.xaxis.set_major_formatter(md.DateFormatter("%H:%M",tz="America/New_York"));ax.grid(alpha=.15)
            if i==0 and j==0:ax.legend(fontsize=8,ncol=3)
    fig.suptitle("Frozen derivatives: first observed win and loss, September then earlier periods\nGrey: pre-signal context; yellow: known waiting path. Exit dot uses bar-end availability bound.",fontsize=13)
    fig.savefig(OUT/"trade_examples.png",dpi=140);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(13,4.6),constrained_layout=True)
    for p,ax in zip(["M26","S26"],axes):
        for r in result["candidates"]:
            z=pd.read_csv(OUT/f"trades_{r['spec']['id']}_{p}.csv").sort_values("exit_t")
            if len(z):ax.step(pd.to_datetime(z.exit_t,unit="s",utc=True),z.R.cumsum(),where="post",lw=.9,label=r["spec"]["family"])
        z=pd.read_csv(OUT/f"portfolio_{p}.csv").sort_values("exit_t")
        ax.step(pd.to_datetime(z.exit_t,unit="s",utc=True),z.R.cumsum(),where="post",lw=2,color="#182733",label="Portfolio")
        ax.axhline(0,color="gray",lw=.5);ax.grid(alpha=.15);ax.set_title(p);ax.set_ylabel("Cumulative net R")
        ax.xaxis.set_major_locator(md.WeekdayLocator(byweekday=md.MO,interval=2 if p=="M26"else 1))
        ax.xaxis.set_major_formatter(md.DateFormatter("%m-%d"));ax.legend(fontsize=8,ncol=3)
    fig.suptitle("Executable one-position replays; fixed TP80 / SL110; historical labels already seen")
    fig.savefig(OUT/"equity.png",dpi=160);plt.close(fig)


def wilson(n,wr):
    if not n:return "—"
    z=1.96;den=1+z*z/n;mid=(wr+z*z/(2*n))/den;rad=z*np.sqrt(wr*(1-wr)/n+z*z/(4*n*n))/den
    return f"%{100*(mid-rad):.1f}–%{100*(mid+rad):.1f}"


def run():
    x=json.loads((OUT/"evaluation.json").read_text());a=json.loads((OUT/"autopsy.json").read_text())
    o=json.loads((OUT/"occupancy.json").read_text());forward=json.loads((OUT/"forward_day.json").read_text())
    impact=json.loads((OUT/"early_clock_impact.json").read_text());plots(x)
    intro="""# Nasdaq: başarılı örneklerin mekanizmasından türetilen ikinci araştırma turu

Tamamlanma: **1 Ekim 2026**. İlk tanımlar ve seçim: 30 Eylül. Sembol NDX.INDX / MT5 NAS100; transfer kaynağı Dukascopy US100. Kullanıcının istediği ortak mantık → yeni fikir → karşılaştırmalı sınama zinciri uygulandı. Canlı bot, bayraklar ve emirler değiştirilmedi.

## Sonuç

**20 yeni türev tanımı sınandı; beş ailenin hiçbiri doğrulanmış yeni kâr kapısı olmadı.** En ilginç mekanizma D3'ün “bekle + gürültü bandı + fiyatı kovalamama” birleşimi; Mayıs–Ağustos ve Eylül toplamı pozitif, fakat 2025 ilk yarısı negatif, Eylül ikinci yarısı negatif, 3m aktarımı negatif ve ağır maliyetlere hassas. Bu nedenle araştırma hipotezi olarak kalır.

Yeni beşlinin tek-pozisyon portföyü 1–29 Eylül'de **73 karar / +1,97R**; Mayıs–Ağustos'ta **286 / −8,54R**. Eylül bootstrap %95 EV aralığı **[−0,131, +0,183]R**, pozitif bootstrap payı %63,49. Önceki +11,27R portföyün yerine geçecek kanıt üretmedi. 30 Eylül ek gününde donmuş portföy **5 / −0,38R** verdi.

R başlangıç stop mesafesine göre normalize edilmiş replay getirisidir. Simülasyon R'si, gerçek botun dolar kârı ve gelecekteki kâr aynı şey değildir.

## Ortak mantık nasıl çıkarıldı?

Önce gerçek işlem kazananları, kaybedenleri ve önceki araştırmada elenen fırsatlar aynı karar-anı özellikleriyle karşılaştırıldı. Ortak özellik ancak aynı strateji içinde anlamlıysa yeni fikre dönüştürüldü. Sırf kazananlarda bir özellik görünmesi nedensel fayda sayılmadı.

319 pozisyon bacağı → aynı dakika/yönde **317 bağımsız giriş kararı**. Bunların 316'sına taze kapalı-mum bağlamı eşlendi; 12 Temmuz 22:00 UTC'deki bir karar için yeterince taze mum yoktu. Kapsam 30 Haziran–29 Eylül, 46 karar günü. Giriş/önceki-kapanış fiyat farkı medyan 4,9 puan; saat kayması ±180/±1230 dakika alternatifleri çok daha kötü. Gerçek işlem puanı yönlü giriş/çıkış farkıdır; bacaklar eşit ağırlıklıdır. Lot, swap ve yönetilen stoplar nedeniyle bu puanlar gerçek R diye sunulmadı.

| Gerçek motor | Karar | WR | Puan/karar | Mekanizma yorumu |
|---|---:|---:|---:|---|
"""
    lines=[intro]
    names={"52890969":"MOM/SR","52890970":"CHREV","52890971":"VIXREG","52890973":"DAYCOMBO","52890975":"REENTRY"}
    for magic,label in names.items():
        r=a["by_magic"][magic]
        lines.append(f"| {label} | {r['n']} | %{100*r['wr']:.1f} | {r['mean_points']:+.2f} | Farklı risk/yönetim; yeni kural testi değil |")
    lines.append("""

**Yön + uygun giriş fiyatı** ortak bir tasarım fikridir; her motorda aynı EMA koşulu değildir. DAYCOMBO'nun 29/29 kararı M15 yönlü bağlamda; bu kendi kuralının parçası, bağımsız keşif sayılmaz. REENTRY'de yeniden hesaplanan H1 hizası 17/18; fakat 18 karar yeni bir kuralı kanıtlamaz. VIXREG'de ek M15 hizalı 115 karar −5,86 puan/karar, diğer 102 karar +11,03 (1 bağlam bilinmiyor): “daha çok trend teyidi her zaman daha iyi” varsayımı bu kohortta yanlış.

**Yeterli fiyat alanı** VIXREG'de daha belirgin: eksiksiz dört saatlik M1 pencere konumu BUY<0,60 / SELL>0,40 olan 92 karar +14,07 puan/karar; diğer 92 −6,92. Arada mum boşluğu olan 34 karar bu konum karşılaştırmasından çıkarıldı; bilinmeyenler kaybeden/uygunsuz sayılmadı. Bu eşikler zaten `forexsai_demo_bot.py::_position_gate_blocks` içinde mevcut; yeni kapı diye yeniden adlandırılmadı. DAYCOMBO devam stratejisinde aynı konum filtresi çoğu kazancı da elerdi. Bu bağlam karşılaştırmaları geçmiş işlemler üzerinde betimseldir; bloklandıktan sonra hangi yeni işlemlerin açılacağı bilinmez.

Kapalı H1 EMA50 burada uzun geçmişten yeniden hesaplandı. Botun sınırlı pencere EMA başlangıcı, geçmiş sürüm ve gerçek sinyal kuyruğu birebir yeniden üretilmedi; bu tablo bugün çalışan bayrağın etkisini ölçmez. Dönem/lot/strateji değişimleri vardır. Kodun kendi kuralını örneklerin ortak özelliği olarak bulmak yeni bağımsız kanıt değildir.

**Günlük stres ile mikro teyit aynı şey değildir.** Önceki günler düşmüşken SELL örnekleri daha zayıf olabilir; bundan doğrudan yeni BUY stratejisi çıkarılamaz. D4 bu ikinci adımı ayrıca sınadı.

**Portföy seçimi sonucu değiştiriyor.** Önceki varyans stratejisinin bağımsız Eylül sonucu −8,13R iken portföyün kabul ettiği 22 karar +7,30R idi. Ham 162 fırsat yeniden ayrıldı: kabul edilen 13 kırılım +7,74R, 9 dönüş −0,44R. H1/M15 hizası tek başına bu kazancı açıklamıyor. Diğer motorların doluluk takvimini gün içinde 500 kez nötr kaydırınca toplam R'nin %5/%50/%95 dilimleri −6,94/+0,85/+8,64 çıktı; tekrarların %8,4'ü +7,30R'ye ulaştı. Böyle bir alt küme ilginçtir, fakat aynı ayın sonuçlarından seçilmiştir; gelecekte uygulanabilir bir giriş kapısının kanıtı değildir. Kontrol tekrarlarının karar sayısı medyan 33, gerçek alt küme 22 olduğundan eşit risk/eşit hacimli bir alfa testi de değildir.

## Beş türev ve değişmeden kalan tanımlar

Tanımlar [PROTOCOL.md](PROTOCOL.md) içinde, kodda `experiment.py::candidates`. İlk üç seçim dönemi: 2025 H1/H2 ve saatleri düzeltilmiş Şubat–Mayıs 2026. Mayıs–Ağustos ve 1–29 Eylül yeniden sınamadır: bu tarihler önceki araştırmalarda görülmüştür, yeni bağımsız holdout olarak sunulmaz.

Her ailenin 2 varyantı × 2 çıkış geometrisi = 20 tanım. Üç seçim diliminde EV>0, toplam≥100, her dilim≥15 ve boşluk stresi≥0 arandı. Hiçbiri bütün şartları geçmedi. İnceleme için aile başına en iyi en-kötü-dilim EV'si seçildi; seçim başarısızlığı korunuyor. Ön seçimde küçük dilime konulan −10 sıralama cezası protokoldeki EV sıralamasıyla uyuşmadığı için Mayıs–Ağustos/Eylül türev etiketleri hesaplanmadan düzeltildi; ilk dosya `frozen_preliminary_ranking.json` içinde korundu.

Son seçilen beş tanımın hepsinde TP80/SL110, 90 dakika, 15:55 NY zorunlu çıkış var. CORE geometrisi de ilk 20 tanım içinde denenmişti; seçilmedi.

| Türev | Kesin ek koşul | Mayıs–Ağustos n / ΣR | Eylül n / ΣR | Eylül 3m / 5m ΣR | Karar |
|---|---|---:|---:|---:|---|
""")
    rules={"D1":"Efficient pullback30 + kapalı M15 yönü","D2":"Failed-break60; 2dk sınırın içinde kapanışlar + ≤0,5ATR fiyat kovalamama",
           "D3":"D1; 3dk bekle, aleyhe uç≤1,28ATR14√3, ilerleme≤0,5ATR70",
           "D4":"Failed-break60 BUY veya efficient-pullback30 BUY; önceki 5g z≤−1 + M15↑",
           "D5":"Varyans kırılım dalı; VR5/120M1>1,2, ER60>0,2, 60dk yön hizası"}
    for r in x["candidates"]:
        fam=r["spec"]["family"];m=r["periods"]["M26"]["candidate"];s=r["periods"]["S26"]["candidate"];tf=r["tf_transfer"]["S26"]
        lines.append(f"| {fam} {TITLES[fam]} | {rules[fam]} | {m['n']} / {m['total_R']:+.2f} | {s['n']} / {s['total_R']:+.2f} | {tf['3']['total_R']:+.2f} / {tf['5']['total_R']:+.2f} | RED; seçim şartları geçilmedi |")
    lines.append("\n### Ana stratejiye gerçekten ne eklendi?\n\nToplam R farkı seçilen EV kadar önemlidir. Her iki akış kendi fırsatlarıyla tek pozisyon olarak tekrar yürütüldü; ayrı ayrı kabul/reddedilen alt akışlar birbirine eklenerek canlı portföy sayılmaz.\n\n| Türev | Ön dönem kapısız / kapılı R | Eylül kapısız / kapılı R | Eylül toplam fark R | Gün-bloklu fark P(>0) | Holm(5) p |\n|---|---:|---:|---:|---:|---:|")
    for r in x["candidates"]:
        m=r["periods"]["M26"];s=r["periods"]["S26"];b=s["delta_bootstrap"]
        lines.append(f"| {r['spec']['family']} | {m['parent']['total_R']:+.2f} / {m['candidate']['total_R']:+.2f} | {s['parent']['total_R']:+.2f} / {s['candidate']['total_R']:+.2f} | {s['delta_total_R']:+.2f} | %{100*b['p_positive']:.1f} | {b['holm_p_selected_five']:.3f} |")
    lines.append("""

D3'ün Mayıs–Ağustos karşılaştırması özellikle öğretici: hemen giriş +4,59R; kör 3dk bekleme −1,76R; yalnız gürültü bandı +0,16R; band+fiyat sınırı +3,39R. Demek ki **bekleme tek başına faydalı değil**, birleşimin değeri gecikmeden çok hangi fiyattan kabul edildiğiyle ilişkili. Yine de +3,39R hemen girişin toplamını geçmedi. Eylül'de aynı dört sonuç −1,86/−0,89/+0,22/+0,26R. Bu, sebebin tüm dönemlerde aynı olduğunu kanıtlamaz.

D4'te Mayıs–Ağustos makro koşulu tek başına +3,57R; M15 koşulu tek başına +1,68R; ikisi birlikte −3,01R. İki pozitif özellik birleşince pozitif strateji oluşacağı varsayımı da yanlış. Eylül'deki üç pozitif kararın neti sadece **bir günden** geliyor. D5'te Eylül tek karar var; “%100 başarı” veya bootstrap %100 söylemi anlamlı değil.

### Belirsizlik, maliyet ve iki yarı

| Türev | Eylül WR / Wilson %95 | EV / gün-bloklu %95 | Etkin gün | İlk / ikinci yarı R | spread×1,5 / ×3 R | 1p kayma / +1dk R |
|---|---:|---:|---:|---:|---:|---:|
""")
    for r in x["candidates"]:
        s=r["periods"]["S26"]["candidate"];b=r["periods"]["S26"]["bootstrap"];h=r["halves"];st=r["stress"]
        ci="tek gün; hesaplanamaz"if b["effective_days"]<2 else f"[{b['ci95'][0]:+.3f}, {b['ci95'][1]:+.3f}]"
        lines.append(f"| {r['spec']['family']} | %{s['wr']*100:.1f} / {wilson(s['n'],s['wr'])} | {s['ev']:+.3f} / {ci} | {b['effective_days']} | {h['S26a']['total_R']:+.2f} / {h['S26b']['total_R']:+.2f} | {st['spread_1_5']['S26']['total_R']:+.2f} / {st['spread_3']['S26']['total_R']:+.2f} | {st['slip_1']['S26']['total_R']:+.2f} / {st['extra_delay_1m']['S26']['total_R']:+.2f} |")
    lines.append("\nWilson bağımsız karar varsayımıyla betimseldir; gün içi bağımlılık için esas EV aralığı gün bloklarından gelir. Tek gün bootstrap'ı aynı günü tekrarlar, varyans öğrenemez; JSON'daki ham p=1 ve nokta aralığı anlamlı güven değildir. Bütün altı tarihsel kontrolün birlikte geçtiği aday sayısı **0**; hiçbir adayın Eylül hacmi 150 değil. Kapanıştan iyimser giriş farkı da ölçüldü; D3 bu duyarlılık kontrolünü geçmedi.\n\n### Tek pozisyonla yeni beşli\n\n| Dönem | n | Toplam R | EV R | DD R | Bootstrap pozitif payı |\n|---|---:|---:|---:|---:|---:|")
    for p,m in x["portfolio"].items():lines.append(f"| {p} | {m['n']} | {m['total_R']:+.2f} | {m['ev']:+.3f} | {m['drawdown_R']:.2f} | %{100*m['bootstrap']['p_positive']:.1f} |")
    lines.append("\n| Portföy kontrolü | Mayıs–Ağustos n / ΣR | Eylül n / ΣR |\n|---|---:|---:|")
    for label,ms in x["portfolio_controls"].items():
        m,s=ms["M26"],ms["S26"];lines.append(f"| {label} | {m['n']} / {m['total_R']:+.2f} | {s['n']} / {s['total_R']:+.2f} |")
    lines.append("\n![Karar sıralı equity](results/equity.png)\n\n## Kurallar dondurulduktan sonraki 30 Eylül günü\n\n1 Ekim'de mevcut MT5 köprüsünden **salt okunur** çekildi. Önce 29 Eylül çakışmasıyla saat/fiyat kontrol edildi. Donmuş kurallar, yönler, geometriler ve öncelik değişmedi. Bu çalışma için yeni gün kontrolüdür; diğer proje çalışmalarının aynı tarihteki veriyi hiç görmediği iddia edilmez.\n")
    au=forward["audit"];lines.append(f"\nM1 bar sayısı {au['new_day_rows']}; çakışma {au['overlap_rows']}, medyan/maksimum close farkı {au['overlap_median_close_error']:.3f}/{au['overlap_max_close_error']:.3f} puan. Broker UTC farkı 10800 saniye, point=0,1; spread dağılımı {au['spread_points']}.\n\n| Türev | Yeni gün n / R | 3m n / R | 5m n / R |\n|---|---:|---:|---:|")
    for r in forward["candidates"]:
        s=r["stats"];t=r["tf_transfer"];lines.append(f"| {r['id']} | {s['n']} / {s['total_R']:+.3f} | {t['3']['n']} / {t['3']['total_R']:+.3f} | {t['5']['n']} / {t['5']['total_R']:+.3f} |")
    lines.append("\nPortföy 5 karar / **−0,382R**. D3 M1'de işlem üretmedi ve ana stratejinin bir kazancını kaçırdı. Tek günlük kazanç/kayıp bir stratejiyi doğrulamaya veya reddetmeye yetmez; bu sonucun ardından ayarlar yeniden seçilmedi.\n\n## Saat onarımı ve önceki sonuca etkisi\n\nMart öncesi cache etiketleri 60 dakika erken. Ayrı H1 kaynağıyla kontrol: Şubat median close farkı kaydırmadan 28,9 puan; +60dk ile 2,2. Mart sonrası kaydırmadan 4,6; +60dk ile 35,6. Ayrıca kış cache'inde en güçlü dakika 08:30 NY görünürken düzeltmeyle 09:30'a gelir; normal Nasdaq nakit açılışı [09:30 ET](https://www.nasdaq.com/nasdaq-system-hours-of-operation). Ham dosya korunarak sadece bu turun okuma kopyası düzeltildi.\n\nİlk turun beş kuralı aynı halde düzeltilmiş erken dönemde tekrar yürütüldü:\n\n| İlk kural | Eski n / EV | Düzeltilmiş n / EV |\n|---|---:|---:|")
    for r in impact:
        a0,b0=r["old_unrepaired_discovery"],r["repaired_discovery"];lines.append(f"| {r['id']} | {a0['n']} / {a0['ev']:+.4f} | {b0['n']} / {b0['ev']:+.4f} |")
    lines.append("""

En belirgin fark süpürme örneğinde +0,0747→+0,0310R. İlk 432 adayın tamamı düzeltilmiş saatle yeniden seçilmedi: eski sıralamanın hâlâ aynı olduğu söylenemez. Buna karşılık ilk raporun Mayıs sonrası MT5, 2025 Dukascopy ve Eylül sonuçları bu kış-cache hatasından etkilenmez; önceki “beş kanıtlı kapı bulunamadı” sonucu değişmez.

## Yöntem ve doğrulama

Karar bar start+TF süresi geçince; giriş sonraki M1 açılışı. BUY ask, SELL bid; SELL çıkış ask, Dukascopy gerçek ask OHLC; MT5 bar-spread kaydı. 0,2 puan/fill, stop gap'inde kötü açılış, aynı bar TP/SL belirsizliğinde stop önce. Komisyon 0 yerel demo varsayımı; canlı hesap ücreti doğrulanmadı. Overnight yok. Risk gecikmiş yeni giriş anında belirlenir. NY03:00–15:30, Pazartesi–Perşembe, 15:55 flat; ≥10dk karar arası, tek pozisyon. Mevcut panel/model sinyalleri ve tüm canlı kapılar taklit edilmez.

Cache spread 1,3 puan yaklaşık. MT5 Eylül bar-spread'i sabit 1 puan; değişken tick/fill spread dağılımı ayrıca kanıtlanmış değil. Bu yüzden ×1,5/3 ve 1 puan/fill stresi kullanıldı. Boşluklar raporda ayrı ve en az −1R stresiyle görünür; son görülen kapanıştaki çıkış gerçek fill garantisi değildir. 1/3/5m aynı fiyat yoludur; bağımsız üç örneklem sayılmaz. VR120 ve diğer istatistiksel bağlamlar bütün trigger TF'lerinde M1 penceresidir.

Ana stratejiye karşı yürütme, reddedilen fırsat replay'i, ters yön, kör gecikme/band/makro/mikro ablasyonları; saat/yön başına aynı sayıda ham fırsatı kabul eden 300 rastgele kapı kontrolü yapıldı. Rastgele kapı işlenebilir karar sayısını/olay kümelenmesini değiştirebilir; tanısal plasebodur. Aynı günün gelecekte gerçekleşmiş ortalaması burada seçim metriği veya giriş özelliği değildir. Eski raporda bu ortalama karşılaştırma tanısıydı; onu bir giriş özelliğiyle karıştırmamak gerekir, fakat ileri taşınabilir alfa için yeterli taban da değildir.

20 aday tanımı + 114 kontrol hücresi = **134 sayım** (ilk arama dönemi çoğaltmaları ve ana/elenen tekrarları ayrıca aynı tanımın ölçümüdür). Yeni gün 5 ana + 10 TF ölçümü ve 1 portföy ekledi. 3000 rastgele kabul ve 500 doluluk takvimi tekrarı yeni strateji tanımı sayılmaz. Önceki 2052 arama değerlendirmesi ve diğer proje taramaları var; Holm(5) bütün bu geçmiş seçimi temizlemez. [Backtest overfitting çalışmasının](https://escholarship.org/uc/item/4w1110bb) işaret ettiği çoklu seçim sorunu nedeniyle tarihsel retest, yeni dönem kanıtının yerine geçmez.

20 tanım × 3 TF prefix-causality testi geçti; gelecekteki fiyatları değiştirmek geçmiş özellikleri değiştirmedi. Beş sentetik bekleme fikstürü, 10000 saat-tarihi eşitliği kontrolü geçti. Ortak motorun bid/ask, boşluk, stop önceliği, gerçek ask, alternatif risk/süre ve 432 eski tanımın prefix kontrolleri tekrar geçti. Tarihi biçimlendirmede local timezone çıkarma yalnız performans düzeltmesidir, 10000 tarihte aynı günü üretir.

![İlk kazanan ve ilk kaybeden örnekler](results/trade_examples.png)

Grafikler seçilen tanımın Eylül'deki ilk kazanan/kaybedenini gösterir; kaybeden yoksa önceki dönemden ilk kaybeden alınır ve dönem yazılır. D5 kaybedeni Mayıs–Ağustos döneminden gelir. Mor: gerçekçi giriş, yeşil/kırmızı: TP/SL; gri: sinyal öncesi görülen bağlam; sarı: bekleme sırasında bilinen yol. Çıkış noktası M1 içi kesin zaman yerine barın bitiş sınırında. Bunlar betimleyici grafiktir.

## Araştırmadan çıkan uygulanabilir karar

Yeni evrensel trend filtresi eklemek yerine **hangi motorun hangi fiyattan girdiği** ölçülmeli. Bu turda D3 mekanizması sonraki kapalı-mum niyetleri üzerinde, kendi ana stratejisi ve kör gecikmeyle yan yana, aynı risk ve işlem kapasitesiyle ölçülmeye değer. D4/D5 çok seyrek; düşük örnekli pozitif hücreler öne çıkarılmamalı. Bu beşli canlıya eklenmez; önceki donmuş portföyün gölge doğrulama backlog'u devam eder. Araştırma işi tamamlandı; gerçekten sonraki ≥150 karar/tick-fill doğrulaması henüz gerçekleşmedi. Hiçbir yeni gölge/canlı süreç başlatılmadı.

Tekrar üretim: `experiment.py search` → `experiment.py evaluate`; `verify.py`; `occupancy.py`; `forward_day.py`; `make_report.py`. Yeni gün ham export'u yoksa `pull_day.py` yalnız okuma köprüsünü kullanır; var olan çekimi üzerine yazmaz. Rapor, tanımlar, kayıtlar ve kaynak hash'leri `results/provenance.json` içinde izlenebilir.
""")
    report=re.sub(r"(\|[^\n]*\|)\n(?:[ \t]*\n)+(?=\|)",r"\1\n","\n".join(lines))
    (HERE/"RAPOR.md").write_text(report,encoding="utf-8")
    paths=list(HERE.glob("*.py"))+[HERE/"PROTOCOL.md",OUT/"frozen_derivatives.json",OUT/"evaluation.json",OUT/"forward_day.json",
        ROOT/"research/ndx_gate_forge/data/macro_daily_patched.csv",lab.CACHE,lab.MT5,
        HERE.parent/"ndx_five_gates_20260930/lab.py",HERE.parent/"ndx_five_gates_20260930/transfer.py",HERE.parent/"ndx_five_gates_20260930/second_search.py"]
    lab.save_json(OUT/"provenance.json",{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths})
    print("Report and charts saved",HERE/"RAPOR.md",flush=True)

if __name__=="__main__":run()
