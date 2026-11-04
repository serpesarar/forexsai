"""Consolidate the path study, its frozen combinations and capital occupancy."""
import os
os.environ.setdefault("MPLCONFIGDIR","/private/tmp/ndx_cap_paths_mpl")
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from paths import HERE,OUT,prior,lab,metrics,M1_PERIODS,RULES,PRIMARY

ALL_RULES=RULES+["HALF_RISING","TP1_RISING"]
TITLES={"FRESH_CROSS":"Yeni dip kırılımı", "CASH_ONLY":"Nakit seansında giriş", "FAIL_10":"10:00 başarısız geri-alım çıkışı", "HALF_RUNNER":"Yarı+1R / yarı16:00", "VIX_COOLING":"Yüksek fakat düşen VIX"}

def collect(rule,tf=1,case="base"):
    rows=[]
    for source in["duka","mt5"]:
        a=pd.read_csv(OUT/f"trades_{source}_{tf}_{case}_{rule}.csv")
        for p,(start,end)in M1_PERIODS.items():
            if p.startswith("D25")!=(source=="duka"):continue
            z=a[(a.decision>=lab.stamp(start))&(a.exit_t<lab.stamp(end))].copy()
            z["period"]=p;rows.append(z)
    return pd.concat(rows,ignore_index=True).sort_values("decision").reset_index(drop=True)

def ledger(rule,case="base"):
    return pd.concat([pd.read_csv(OUT/f"portfolio_{p}_{case}_{rule}.csv")for p in M1_PERIODS],ignore_index=True).sort_values("decision").reset_index(drop=True)

def fmt(x):return f"{x:+.2f}"

def main():
    agg={"strategy":{},"portfolio":{}}
    frames={}
    for source in["M1","native15","native30","native60"]:
        frames[source]={}
        for rule in ALL_RULES:
            a=collect(rule)if source=="M1" else pd.read_csv(OUT/f"trades_{source}_{source[6:]}_base_{rule}.csv")
            frames[source][rule]=a
        agg["strategy"][source]={r:metrics(a,frames[source]["BASE"])for r,a in frames[source].items()}
    for case in["base","spread3","slip1","delay1"]:
        b=ledger("BASE",case);agg["portfolio"][case]={}
        for rule in["BASE","BASE_ADD","HALF_RISING_ADD","TP1_RISING_ADD"]:
            a=ledger(rule,case);v=metrics(a,b)
            v["cap_taken_n"]=int(a.candidate.str.startswith("CAP_").sum())
            v["cap_taken_R"]=float(a.loc[a.candidate.str.startswith("CAP_"),"R"].sum())
            v["normal_taken_R"]=float(a.loc[~a.candidate.str.startswith("CAP_"),"R"].sum())
            v["paired"]["bonferroni_p22_descriptive"]=min(1.,22*v["paired"]["one_sided_p"])
            agg["portfolio"][case][rule]=v
    lab.save_json(OUT/"aggregate.json",agg)
    base=frames["M1"]["BASE"]
    old=pd.concat([pd.read_csv(prior.OUT/f"trades_{p}_1_base_CAPREV.csv")for p in["D25a","D25b","C26","M26","S26"]],ignore_index=True).sort_values("decision")
    assert base.decision.tolist()==old.decision.tolist() and np.max(np.abs(base.R.to_numpy()-old.R.to_numpy()))<1e-10
    ledgers=list(OUT.glob("portfolio_*.csv"))
    for path in ledgers:
        a=pd.read_csv(path).sort_values("decision")
        assert(a.decision.diff().dropna()>=600).all()
        assert(a.entry_t.iloc[1:].to_numpy()>=a.exit_t.iloc[:-1].to_numpy()).all()
    lab.save_json(OUT/"final_audit.json",{"status":"PASS","baseline_matches_previous_11_events":True,"portfolio_ledgers_checked":len(ledgers),"one_total_position":True,"cooldown_seconds":600})

    # Compare payoffs on each source's own sample, without pooling overlapping years.
    plt.rcParams.update({"font.size":10,"axes.grid":True,"grid.alpha":.2})
    fig,axes=plt.subplots(2,1,figsize=(12,8),constrained_layout=True)
    x=np.arange(4)
    for i,r in enumerate(["BASE","HALF_RUNNER","FULL_TP1","TP1_RISING"]):
        vals=[agg["strategy"][s][r]["total_R"]for s in frames]
        axes[0].bar(x+(i-1.5)*.18,vals,width=.18,label=r)
        vals=[agg["strategy"][s][r]["drop_best"]["3"if s=="M1"else"5"]["total_R"]for s in frames]
        axes[1].bar(x+(i-1.5)*.18,vals,width=.18,label=r)
    labels=["M1: 11 baseline events","15m: 24 baseline events","30m: 72 baseline events","H1 proxy: 107 baseline events"]
    for ax in axes:
        ax.set_xticks(x,labels,fontsize=9);ax.axhline(0,color="black",lw=.7);ax.set_ylabel("Simulated R")
    axes[0].set_title("Exit geometry changes the distribution of returns");axes[0].legend(ncol=4)
    axes[1].set_title("After removing best 3 events (M1) or best 5 (native data)")
    fig.savefig(OUT/"payoff_comparison.png",dpi=160);plt.close(fig)
    ds=prior.load_data();h=frames["M1"]["HALF_RUNNER"]
    examples=[h[h.R>0].iloc[0],h[h.R<0].iloc[0],h[h.target_done.astype(bool)].iloc[0]]
    fig,axes=plt.subplots(3,1,figsize=(12,10),constrained_layout=True)
    for ax,r,title in zip(axes,examples,["First chronological win","First chronological loss","First chronological partial target"]):
        d=ds[r.source]
        z=d[(d.t>=r.decision-3600)&(d.t<=r.exit_t+1800)]
        tm=pd.to_datetime(z.t,unit="s",utc=True).dt.tz_convert("America/New_York")
        ax.plot(tm,z.close,lw=1,color="#24658e")
        for price,label,col,style in[(r.entry,"Entry","#27834a","-"),(r.entry-r.risk,"Initial stop","#bc443d","--"),(r.entry+r.risk,"Half-position target","#ad832d",":")]:
            ax.axhline(price,color=col,ls=style,label=label)
        for time,label,col in[(r.entry_t,"Entry time","#27834a"),(r.exit_t-60,"Final exit","#bc443d")]:
            ax.axvline(pd.Timestamp(time,unit="s",tz="UTC").tz_convert("America/New_York"),color=col,ls=":",label=label)
        if pd.notna(r.partial_t):ax.axvline(pd.Timestamp(r.partial_t,unit="s",tz="UTC").tz_convert("America/New_York"),color="#ad832d",ls="--",label="Partial target bar")
        ax.set(title=f"{title}: {r.day}, {r.R:+.3f}R",ylabel="Nasdaq price",xlabel="New York local time")
        ax.legend(ncol=3,fontsize=8)
    fig.savefig(OUT/"trade_examples.png",dpi=160);plt.close(fig)

    m=agg["strategy"]["M1"];n30=agg["strategy"]["native30"];n60=agg["strategy"]["native60"]
    port=agg["portfolio"]["base"]["TP1_RISING_ADD"]
    sourcehash=hashlib.sha256((HERE.parent/"ndx_gate_forge/NIHAI_RAPOR.md").read_bytes()).hexdigest()
    priorhash=json.loads((prior.OUT/"provenance.json").read_text())["files"]["research/ndx_gate_forge/NIHAI_RAPOR.md"]
    snapshot_hash=hashlib.sha256((HERE/'ATTACHED_V2_SNAPSHOT.md').read_bytes()).hexdigest()
    assert sourcehash==snapshot_hash,"The attached report changed again; inspect the new version before delivering"
    overnight=json.loads((OUT/'overnight.json').read_text())
    assert json.loads((OUT/'overnight_verification.json').read_text())['status']=='PASS'
    raw=json.loads((OUT/"evaluation.json").read_text());comb=json.loads((OUT/"combinations.json").read_text());pf=json.loads((OUT/"portfolio.json").read_text())
    cells=raw["evaluation_cells"]+comb["evaluation_cells"]+pf["evaluation_cells"]+overnight['evaluation_cells']
    lines=["# Nasdaq — CAPREV olay zamanı, çıkış ve sermaye kullanımı: nihai rapor","",
    "2 Ekim 2026. **Araştırma tamamlandı; bütün adaylar araştırma/SHADOW düzeyinde. Çalışan bot veya gölge süreç kurulmadı.**","",
    "**En anlamlı yeni fikir:** stresli gün + yüksek ve artan VIX altında, CAPREV girişini günlük volatiliteye göre **+1R hedef / −1R stop** ile yönetmek. Tek başına seans sonuna taşımadan daha az kazanıyor; mevcut beşli araştırma portföyünde daha erken sermaye boşalttığı için daha fazla toplam katkı veriyor. İkinci fikir, +1R'de yarı kâr alıp yarıyı seans sonuna taşımak: kazancı azaltırken uç-gün bağımlılığını ve bazı düşüşleri azaltıyor.","",
    "Bunlar doğrulanmış kazanç vaatleri değil. En iyi portföy katkısı yalnız **7 etkilenen güne** dayanıyor; güven aralığı sıfırı içeriyor. Saatlik uzun verinin ilk kronolojik yarısı bazı VIX birleşimlerinde zayıf/negatif. M1 final tanımlarında150 uygun olay yok; saatlik birleşimin sayısı150'yi geçse de gerçek09:30/next-M1 icra kartı yok.","",
    "## 1. Eklenen rapor gerçekten yeni miydi?","",
    f"Çalışmanın başındaki sürüm önceki sentezimizle aynıydı (SHA256 `{priorhash[:16]}…`); çalışma sırasında rapor **v2/TUR4** olarak güncellendi (SHA256 `{sourcehash[:16]}…`). v2 ayrıca okunup `ATTACHED_V2_SNAPSHOT.md` olarak sabitlendi. Yeni açılış/dip birleşimi ve gece taşıma iddiaları ayrı dördüncü aşamada test edildi; kaynak rapordaki öneriler botu değiştirme talimatı olarak uygulanmadı. Önceki sentez +11,12R CAPREV'in üç büyük güne yoğunlaştığını, TP80/SL110'a doğrudan taşınmadığını ve CHASE aktarımının zayıf olduğunu göstermişti.","",
    f"Aşama1:5 yeni varyasyon+5 taban/kontrol; aşama2:2 sabit birleşim; aşama3:3 ekleme portföyü+taban; aşama4:açılış/gece/tek-pozisyon için6 tanım. **Toplam22 yapılandırma, {cells} dönem/zaman-dilimi/maliyet hücresi.** İlk780 hücre, birleşimler156, portföy80, v2 denetimi408. Aynı olayların farklı ölçümleridir; bağımsız örnek sayısı değildir. Kurallar her aşamada kendi sonuçlarından önce protokolde yazıldı; sonraki aşamalar önceki sonuçlardan öğrenildi. Bütün dönemler retrospektiftir; yeni dokunulmamış veri çekilmedi.","",
    "## 2. Beş yeni varyasyon","",
    "Taban CAPREV: önceki nakit NDX getirisi≤−%1,5 veya5 seans≤−%4; önceki VIX≥18,4; Pzt–Per NY03:00–15:00 önceki RTH dibinin altındaki ilk tam kapanış; sonraki yürütme barı açılışı BUY; başlangıç stopu önceki20 nakit getiri std×giriş fiyatı; NY16:00 çıkışı. Günde bir net pozisyon.","",
    "| Yeni varyasyon | Mantık | M1 işlem / toplam R | Native30m toplam R | İlk karar |","|---|---|---:|---:|---|"]
    decisions={"FRESH_CROSS":"Tabandan zayıf", "CASH_ONLY":"Tabandan zayıf", "FAIL_10":"Kazananı erken kesiyor", "HALF_RUNNER":"Kazanç/risk dengesi adayı", "VIX_COOLING":"Desteklenmedi"}
    reasons={"FRESH_CROSS":"Zaten dip-altı olmak yerine aynı gün yeni üstten-alta geçiş", "CASH_ONLY":"İlk dip-altı olayı yalnız09:30 sonrası", "FAIL_10":"10:00 kapanmış fiyat hâlâ önceki dibin altındaysa erken çıkış", "HALF_RUNNER":"Yarısı+1R hedefte, yarısı ilk stopla16:00'a", "VIX_COOLING":"Yüksek VIX ama önceki günlük değişim negatif"}
    for r in PRIMARY:lines.append(f"| {TITLES[r]} | {reasons[r]} | {m[r]['n']} / {fmt(m[r]['total_R'])} | {fmt(n30[r]['total_R'])} | {decisions[r]} |")
    lines +=["",f"Değişmeyen taban: M1 **11 işlem / {fmt(m['BASE']['total_R'])}R**, native30m72 işlem / {fmt(n30['BASE']['total_R'])}R. Taban M1'de önceki11 olayla **birebir aynı**; yeni motorun taban kazancı değiştirmediği ayrıca kontrol edildi.","",
    "Yeni kırılımı beklemek veya cash açılışına geçmek daha iyi zamanlama üretmedi. Saat10:00'daki 'geri alınamadı, çık' şartı da hem M1 hem uzun veride kazancı azalttı. Günlük bir geri dönüşün sabah erken tamamlanmasını şart koşmak, günün ilerleyen kısmındaki toparlanmaları kesebiliyor. Bu testten 'her teyit zararlıdır' gibi genel bir yasa çıkarılamaz.","",
    "## 3. Kârı bölmek — yeni risk dengesi","",
    "+1R'de yarım kâr alıp kalan yarıyı16:00'a taşımada ilk stop değişmez; breakeven/trailing yoktur. Kısmi çıkış aynı net pozisyona aittir; kalan açıkken başka pozisyon açılmaz. FULL_TP1 kontrolünde bütün pozisyon aynı+1R hedefte kapanır.","",
    "| Kaynak | Taban toplam R / DD | Yarı çıkış toplam R / DD | Tam+1R toplam R / DD |","|---|---:|---:|---:|"]
    for s,label in[("M1","M1:2025/2026"),("native15","Native15m:2023+"),("native30","Native30m:2021+"),("native60","H1 seviye yaklaşımı:2016+")]:
        a=agg["strategy"][s]
        lines.append(f"| {label} | {fmt(a['BASE']['total_R'])} / {a['BASE']['drawdown_R']:.2f} | {fmt(a['HALF_RUNNER']['total_R'])} / {a['HALF_RUNNER']['drawdown_R']:.2f} | {fmt(a['FULL_TP1']['total_R'])} / {a['FULL_TP1']['drawdown_R']:.2f} |")
    lines +=["", "DD: başlangıç risk birimi cinsinden gözlenen en büyük düşüş. Aynı nakit riskle normalize edildiği varsayılır; gerçek lot/dolum karnesi değildir.","",
    "| En iyi olaylar çıkarılınca kalan toplam R | Taban | Yarı çıkış | Tam+1R |","|---|---:|---:|---:|"]
    for s,label,n in[("M1","M1, en iyi3 gün",3),("native15","Native15m, en iyi5 gün",5),("native30","Native30m, en iyi5 gün",5),("native60","H1 yaklaşımı, en iyi5 gün",5)]:
        vals=[agg["strategy"][s][r]["drop_best"][str(n)]["total_R"]for r in["BASE","HALF_RUNNER","FULL_TP1"]]
        lines.append(f"| {label} | "+" | ".join(fmt(v)for v in vals)+" |")
    lines +=["", "Her varyasyonun kendi en iyi günleri çıkarıldı; bunlar aynı tarihler olmak zorunda değil. Yarı/tam hedef kârı budarken kalan getiriyi birkaç büyük güne daha az bağımlı hale getiriyor. M1 örneklemi bu sonuç için de yalnız11 gün.","",
    "Matematiksel kontrol: **R_yarı =0,5·R_seans-sonu +0,5·R_tam-hedef**. Aynı giriş, ilk stop ve maliyetle24 kaynak/TF/maliyet setinin hepsinde eşitlik en çok4,44×10⁻¹⁶ hata ile sağlandı. Bu bir getiri karışımıdır. Beklenti iki beklentinin ortalaması; varyans da iki getiri arasındaki kovaryansa bağlıdır. Tek başına fiyat tahmini kenarı üretmez, ama risk dağılımını değiştirir. Burada görülen kazanç/risk ödünleşimi böyle açıklanabilir.","",
    "## 4. VIX seviyesi ve yönü aynı bilgi değil","",
    "Yüksek VIX'in günlük olarak **düşmesi** şartı M1'de yalnız2 işlem ve−1,40R; native15m'de2 işlem−1,38R;30m'de14 işlem+0,32R verdi. Bu yeni ana hipotez desteklenmedi.","",
    "Önceden tanımlanan ters kontrol, **VIX artmış/eşit**: M1'de9 işlem+12,52R; native15m22 işlem+21,11R;30m58 işlem+27,30R;H1 yaklaşımında86 işlem+21,79R. Ancak H1 ilk43 işlem ortalaması **−0,052R**, son43+0,559R. Sadece ortalama iyileşti diye uzun dönem kararlılığı geçti denemez. 2025 M1'de fark iki kaybeden günü dışlamaya dayanıyor; çok küçük seçim.","",
    "Bu kontrol ile iki çıkış şekli birleştirildi. Bunlar aşama1 sonucundan sonra yazılan, hâlâ retrospektif olan iki ek tanımdır:","",
    "| Birleşim | M1 n / toplam R | Native30m n / toplam R | H1 ilk/ikinci yarı EV |","|---|---:|---:|---:|"]
    for r,label in[("HALF_RISING","Artan VIX + yarı hedef"),("TP1_RISING","Artan VIX + tam+1R hedef")]:
        h=n60[r]["halves"]
        lines.append(f"| {label} | {m[r]['n']} / {fmt(m[r]['total_R'])} | {n30[r]['n']} / {fmt(n30[r]['total_R'])} | {fmt(h[0]['ev'])} / {fmt(h[1]['ev'])} |")
    lines +=["", "Artan VIX+yarı hedefin saatlik ilk yarısı negatif kalıyor. Artan VIX+tam hedefte iki yarı pozitif olsa da saatlik EV %95 bootstrap aralığı yaklaşık **[−0,005,+0,328]R**: sıfır içeriyor. Bu birleşimleri evrensel kural veya güçlü yeni doğrulama diye sunmuyorum.","",
    "## 5. Daha az tek başına kazanç, daha çok portföy katkısı","",
    "Mevcut botu mumlardan birebir yeniden üretmek mümkün değil. Burada önceki turda dondurulan beşli **araştırma portföyü** kullanıldı. Bütün ham fırsatlar yeniden sıralandı. Aynı anda tek toplam pozisyon;10 dakika giriş aralığı; açık eski pozisyon varsa CAP kaçırılır. Aynı dakika boşsa CAP öncelikli. Yarım pozisyon açıkken normal stratejiye yeni giriş yok.","",
    "| Portföy | Toplam işlem | Alınan CAP | Toplam R | Tabana katkı |","|---|---:|---:|---:|---:|"]
    for r,label in[("BASE","Özgün beşli"),("BASE_ADD","Beşli + CAPREV16:00"),("HALF_RISING_ADD","Beşli + artanVIX/yarıhedef"),("TP1_RISING_ADD","Beşli + artanVIX/tamhedef")]:
        v=agg["portfolio"]["base"][r]
        lines.append(f"| {label} | {v['n']} | {v['cap_taken_n']} | {fmt(v['total_R'])} | {fmt(v['delta_R'])} |")
    lines +=["", "Artan VIX/tam-hedef, tek başına9 olayda+5,58R ile tabanın+11,12R'sinden az kazandı. Portföyde ise **+9,40R katkı** ile16:00 CAP eklemesinin+2,94R katkısından iyi. Yarı hedef ile tam hedef portföyleri aynı7 CAP olayını aldı; tam hedef6 ek normal işleme yer açtı. CAP kazancı5,99→5,06R düşerken normal stratejilerin toplamı59,95→65,70R yükseldi. Sermayenin beklediği süre de strateji sonucunun parçası.","",
    "Dönem katkısı (artanVIX/tamhedef): 2025ilk **+3,76R**,2025ikinci **+1,67R**,2026Şub–May **+4,06R**,May–Ağu **−0,09R**,Eylül–1Ekim **0,00R**. Son dönemde hiç CAP olayı yok; başarılı doğrulama sayılmaz.","",
    f"Katkı332 taban işlem gününün yalnız **{port['paired']['affected_days']} gününde** oluştu. Eşleştirilmiş gün bootstrap pozitif katkı payı%{100*port['paired']['p_positive']:.2f}; günlük ΔR %95 aralığı **[{port['paired']['ci95'][0]:+.4f},{port['paired']['ci95'][1]:+.4f}]**. Sıfır içeriyor. Ham tek-yönlü p={port['paired']['one_sided_p']:.3f};22 yapılandırma için kaba Bonferroni p={port['paired']['bonferroni_p22_descriptive']:.2f}. Önceki turların seçim yükünü bile içermeyen bu kontrol, kanıtlı katkı demeye yetmiyor.","",
    "### Maliyet ve gecikme","",
    "| İcra | Taban portföy toplam R | ArtanVIX/tamhedef toplam R | Katkı |","|---|---:|---:|---:|"]
    for case,label in[("base","Ana"),("spread3","Spread×3"),("slip1","Her tarafta1 puan kayma"),("delay1","Giriş+1 M1")]:
        b=agg["portfolio"][case]["BASE"];v=agg["portfolio"][case]["TP1_RISING_ADD"]
        lines.append(f"| {label} | {fmt(b['total_R'])} | {fmt(v['total_R'])} | {fmt(v['delta_R'])} |")
    lines +=["", "Katkının pozitif olması bütün portföyü sağlam kârlı yapmıyor: spread3'te sonuç **−74,66R**. Gerçek bot sinyali/lot/dolum evreni ayrı doğrulama gerektiriyor.","",
    "## 6. Zaman dilimleri, kaynaklar ve yürütme sınırları","",
    "M1 giriş tetikleri M1/M5/M15 tamamlanmış mumlarda; dolum ortak M1 yolunda. Eski kaynakların native15m/30m/H1 mumlarında ise sonraki **native bar açılışı** kullanılır. Bunlar next-M1 gerçek dolum değildir. Daha uzun barlarda intrabar sıra bilinmez; aynı barda stop ve hedef varsa stop önce varsayılır. Açılışta hedef aşılmışsa bunun daha sonraki stopa göre önce olduğu uygulanır.","",
    "| Kaynak/TF | Taban n | Taban toplam R | Yarı hedef toplam R | Tam hedef toplam R |","|---|---:|---:|---:|---:|"]
    for tf in[1,5,15]:
        b=collect("BASE",tf);h=collect("HALF_RUNNER",tf);t=collect("FULL_TP1",tf)
        lines.append(f"| M{tf} tetik / M1 icra | {len(b)} | {fmt(b.R.sum())} | {fmt(h.R.sum())} | {fmt(t.R.sum())} |")
    for s,label in[("native15","Native15m:2023–Tem2026"),("native30","Native30m:2021–Tem2026"),("native60","H1_PROXY:2016–Tem2026")]:
        v=agg["strategy"][s]
        lines.append(f"| {label} | {v['BASE']['n']} | {fmt(v['BASE']['total_R'])} | {fmt(v['HALF_RUNNER']['total_R'])} | {fmt(v['FULL_TP1']['total_R'])} |")
    lines +=["", "- Native15m/30m'de önceki seans tam09:30–16:00 sayımı gerekli; eksik/yarım günler doldurulmadı. H1 bunu çözemez:09:00–16:00 minimumu önceki gerçek RTH dibinin **alt sınır yaklaşımı** olarak kullanıldı. H1_PROXY farklı tetik eşiğidir; birebir RTH doğrulaması sayılmadı.",
    "- Native broker etiketleri NY+7 saat yorumuyla UTC'ye dönüştürüldü. Düzeltilmiş M1 ile sıfır kaydırmada fiyat eşleşmesi15m medyan0,9 puan;30m/H1 de10 puan eşiğinin altında. ±60 dakika kaydırma çok daha kötü. Yıllık hareket yoğunluğu15m/30m'deNY09:30,H1'de09:00 barında; saat denetimi geçti.",
    "- Native spread bilinmiyor: her tarafta0,6 baz puan fiyat payı ve0,2 puan kayma varsayıldı. M1Dukascopy gerçek ask/bid; doğrudanMT5 kayıtlı bar spreadi; eski cache1,3 puan spread varsayımı. Komisyon ayrıca modellenmedi. Sonuçlar gerçek hesap USD kârı değil, başlangıç risk birimiR.",
    "- M1 ana örneklem2025Duka+2026MT5/cache olmak üzere11 uygun gün;18May2026 dondurulmuş iki bölümün arasındadır, ham CSV'de saklandı ama ana11'e katılmadı. Önceki raporla taban birebir eşleşti. Eylül–1Ekim'de CAP olayı yok.",
    "- Native15m24,30m72,H1proxy107 taban olayı: bunlar örtüşen yıllar ve çoğunlukla aynı günlerdir. Toplayıp203 bağımsız olay denemez. H1'de2 veri-boşluğu çıkışı var; hepsini en az−1R sayınca taban EV0,241→0,234R, yarı hedef0,196→0,189R, tam hedef0,151→0,144R. M1/15m/30m CAP serilerinde böyle çıkış yok.",
    "- Portföyde eski stratejilerden kaynaklanan boşluk çıkışları da görünür. Hepsi en az−1R sayılınca taban toplamı+1,68R, artanVIX/tamhedef portföyü+11,08R. Bu alt sınır gerçek boşluk dolumu tahmini değildir.",
    "- 13 icra fikstürü: yarım çıkış muhasebesi, aynı-barda stop/TP, hedefte açılış, kötü gap dolumu,10:00'daki kapanmış bilgi, geç giriş, boşluk, gecikme, native spread. Altı farklı M1/native prefix denetimi ve80 portföy CSV'sinde tek toplam pozisyon/600s giriş aralığı geçti. Gelecek verisi giriş şartına katılmadı.","",
    "Resmî09:30–16:00 normal seans tanımı için [Nasdaq Equity1](https://listingcenter.nasdaq.com/assets/RuleBook/Nasdaq/rules/Nasdaq%20Equity%201.html); tekrar tekrar aynı geçmişte strateji seçiminin riski için [Bailey ve diğerlerinin birincil araştırması](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) kullanıldı. Bu araştırmanın ham bootstrap oranları seçim geçmişini temizlemez.","",
    "## 7. Nihai sıralama","",
    "1. **CAPREV günlük-vol +1R hedef/−1R stop, artanVIX şartı:** en anlamlı yeni portföy hipotezi. Daha erken sermaye kullanımı faydalı görünüyor;7 etkilenen gün ve sıfırı içeren katkı aralığı nedeniyle araştırma/SHADOW. Mevcut TP80/SL110 kuralına eşdeğer değildir.",
    "2. **CAPREV yarı+1R / yarı16:00:** uç gün bağımlılığını ve bazı drawdown'ları azaltan risk yönetimi adayı. Aynı başlangıç riskiyle toplam kazancı azaltır. ArtanVIX ile saatlik ilk yarısı negatif; güçlü evrensel birleşim değil.",
    "3. **CAPREV tam+1R, VIX-yön filtresiz kontrol:** native15m/30m/H1'de daha dengeli getiri dağılımı; özellikle saatlik yıllardan yalnız2016negatif (tek olay). Fakat107 olay ve küçük bazı yıllar yeterli canlı kanıtı değil. Kontrolden çıkan bulgu diye etiketlendi.",
    "4. **Stres+yüksekVIX açılış/dip fırsatları, tek pozisyon ve aynı-gün kapanış:** v2'den türetilen sermaye çakışması varyasyonu; M1'de28 işlem/27 gün+14,72R. Dip tabanına göre toplamı artırdı ama drawdown da yükseldi; katkı güven aralığı sıfırı içeriyor,15m ilk yarısı negatif. Diğer beşli portföye ek katkısı bu tur ölçülmedi.",
    "5. **Dip alımını sonraki nakit seansa taşıma:** v2 gece varyasyonunun tek-pozisyon denetimi. M1'de11 işlem+9,87R ile aynı günün altında;30m/H1 toplamı biraz iyileşti. Evrensel daha iyi çıkış olarak desteklenmedi; fiyat boşluğu ve gerçek finansman nedeniyle ikinci planda.","",
    "FRESH_CROSS/CASH_ONLY/FAIL_10/VIX_COOLING mevcut tanımlarla tabana üstünlük getirmedi; ek filtre olarak önerilmiyor. Açılış-bugün/dip-yarın karışımı da aynı-gün birleşimi geçmedi. Beş sıralama maddesi beş kanıtlı kâr kapısı değildir. Önceki K5b/CHASE bu turda yeni keşif diye sayılmadı.",
    "İleri doğrulama: final kurallar değiştirilmeden tamamen yeni dönem veya daha önce görülmemiş güvenilirM1 geçmiş, aynı nakit riskle gerçek spread/lot/fill, gerçek bot niyetleri ve tek toplam pozisyon;>=150 çözülmüş uygun olay, iki kronolojik yarı, pozitif netEV/bootstrapping ve maliyet kartı. Geçmiş yılları farklıTF'lerde tekrar sayarak örnek eşiği doldurulamaz. Şu anda LIVE onayı yok.","",
    "## 8. Görseller ve yeniden üretim","","![Getiri dağılımı karşılaştırması](results/payoff_comparison.png)","","![İlk kazanan, ilk kaybeden ve ilk kısmi hedef](results/trade_examples.png)","",
    "Ayrı protokoller: `PROTOCOL.md`, `PROTOCOL_COMBINATIONS.md`, `PROTOCOL_PORTFOLIO.md`, `PROTOCOL_OVERNIGHT.md`. Çıktılar: `results/evaluation.json`, `combinations.json`, `portfolio.json`, `aggregate.json`, işlemCSV'leri, `verification.json`, `payoff_identity.json`, `final_audit.json`, `overnight.json`, `overnight_verification.json`, `provenance.json`.","",
    "```bash","python3 research/ndx_caprev_paths_20261002/paths.py","python3 research/ndx_caprev_paths_20261002/verify.py","python3 research/ndx_caprev_paths_20261002/combine.py","python3 research/ndx_caprev_paths_20261002/portfolio.py","python3 research/ndx_caprev_paths_20261002/overnight.py","python3 research/ndx_caprev_paths_20261002/verify_overnight.py","python3 research/ndx_caprev_paths_20261002/make_report.py","```"]
    from overnight_report import section
    ix=lines.index('## 6. Zaman dilimleri, kaynaklar ve yürütme sınırları')
    lines[ix:ix]=section()
    lines=[s.replace("H1'de09:00 barında; saat denetimi geçti.","H1'de yıla göre09:00 veya10:00 barında; saat denetimi geçti.") for s in lines]
    (HERE/"NIHAI_RAPOR.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    files=list(HERE.glob("*.py"))+list(HERE.glob("*.md"))
    files += [OUT/f for f in["evaluation.json","combinations.json","portfolio.json","aggregate.json","verification.json","clock_audit.json","payoff_identity.json","final_audit.json","overnight.json","overnight_verification.json"]]
    files += [HERE.parent/"ndx_gate_forge/NIHAI_RAPOR.md",prior.HERE/"NIHAI_RAPOR.md",prior.OUT/"macro_daily.csv",prior.OUT/"fresh_oct01.json"]
    files += [HERE.parent/'ndx_gate_forge'/f for f in ['round4.py','w7.py','cross_market.py','PROTOCOL_4.md','results/round4.json','results/w7.json','results/cross_market.json']]
    files += [HERE.parents[1]/f"research/ndx_buy_lab/data/long_{tf}.csv"for tf in["15m","30m","1h"]]
    lab.save_json(OUT/"provenance.json",{"created_utc":pd.Timestamp.now(tz="UTC").isoformat(),"attached_report_same_as_previous_audit":sourcehash==priorhash,
                                        "configurations":22,"evaluation_cells":cells,"all_evaluation_retrospective":True,
                                        "sha256":{str(p.relative_to(HERE.parents[1])):hashlib.sha256(p.read_bytes()).hexdigest()for p in files}})
    print("REPORT",HERE/"NIHAI_RAPOR.md",cells,"cells",flush=True)

if __name__=="__main__":main()
