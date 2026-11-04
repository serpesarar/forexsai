"""Evidence-led Turkish report; contaminated quotes never become final validation."""
from core import *
from oil_execution import simulate_grid
from oil_variants import DEFS
import hashlib,platform,re
MAIN=['O1_ENERGY_NO_EIA','O2_SPREAD10','O3_BREAK5','O4_OVX_TP1','O5_BOTH']
LABELS=['Enerji seansı / EIA çevresi veto','Spread/risk kontrollü geri çekilme','EIA sonrası5dk kırılım kabulü','OVX / normalize düşüş / +1R hedef','Simetrik şok sonrası geri dönüş']

def load(kind,source,tf,case,name):
    return pd.read_csv(OUT/f'{kind}_{source}_{tf}_{case}_{name}.csv')

def evidence(a,source):
    if source=='cache':return a[a.period.str.startswith('VALID')&(a.day<'2026-08-28')].copy()
    return a[a.period.str.startswith('FINAL')].copy()

def primary(kind,name,tf=1,case='base'):
    parts=[evidence(load(kind,s,tf,case,name),s).assign(feed=s)for s in ['cache','direct']]
    return pd.concat(parts,ignore_index=True).sort_values('decision').reset_index(drop=True)

def num(x):return f'{x:+.2f}'
def table_metric(a):
    s=stats(a,True);ci=s['bootstrap']['ci95'];wr=s['wr_ci95'];return f"{s['n']} | {num(s['total_R'])} | {num(s['ev'])} | {s['wr']*100:.1f}% [{wr[0]*100:.1f},{wr[1]*100:.1f}] | [{ci[0]:+.3f},{ci[1]:+.3f}] | {s['drawdown_R']:.2f}"

def plots():
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(11,5))
    for nm,label in zip(MAIN,LABELS):
        a=primary('oil',nm);ax.plot(pd.to_datetime(a.decision,unit='s',utc=True),a.R.cumsum(),label=nm)
    ax.axhline(0,color='gray',lw=.7);ax.set(title='WTI frozen ideas: eligible validation + separate MT5 final epoch',ylabel='Cumulative net simulated R');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'equity.png',dpi=170);plt.close(fig)
    direct=datasets()['direct'];a=evidence(load('oil','direct',1,'base','O3_BREAK5'),'direct')
    chosen=[]
    for sign in [True,False]:
        x=a[(a.R>0)==sign]
        if len(x):chosen.append(x.iloc[0])
    if len(chosen)<2:
        a=primary('oil','O3_BREAK5');chosen=[a[a.R>0].iloc[0],a[a.R<=0].iloc[0]]
    fig,axes=plt.subplots(2,1,figsize=(12,7))
    for ax,row in zip(axes,chosen):
        src=row.get('feed','direct');d=datasets()[src];q=d[(d.t>=row.decision-3600)&(d.t<=row.exit_t+900)]
        times=pd.to_datetime(q.t,unit='s',utc=True).dt.tz_convert('America/New_York');ax.plot(times,q.close,color='black',lw=.9)
        ax.scatter(pd.Timestamp(row.entry_t,unit='s',tz='UTC').tz_convert('America/New_York'),row.entry,label='entry',color='blue')
        ax.scatter(pd.Timestamp(row.exit_t-60,unit='s',tz='UTC').tz_convert('America/New_York'),row.exit,label='exit',color='purple')
        ax.axhline(row.entry-row.side*row.risk,color='red',ls='--',label='stop');ax.axhline(row.entry+row.side*1.5*row.risk,color='green',ls='--',label='target')
        ax.set(title=f"First chronological {'win'if row.R>0 else 'loss'}: {row.day}, {'BUY'if row.side>0 else 'SELL'}, {row.R:+.3f}R ({src})",ylabel='USD/barrel');ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(OUT/'first_win_loss.png',dpi=170);plt.close(fig)

def matched_controls():
    out={}
    for source,d in datasets().items():
        for geom,kw,names in [('slow',dict(risk_mult=8,hold_minutes=240,reward_ratio=2),MAIN[:2]),('core',dict(risk_mult=5,hold_minutes=90,reward_ratio=1.5),[MAIN[2]])]:
            grid=simulate_grid(d,window_start=540,window_end=840,deadline=870,allowed_weekdays=5,**kw)
            full=pd.concat(list(grid.values()),ignore_index=True)
            full=full[(full.decision>=lab.stamp('2026-05-20'))&(full.exit_t<lab.stamp('2026-08-28'))]if source=='cache'else full[(full.decision>=lab.stamp('2026-09-01'))&(full.exit_t<lab.stamp('2026-10-02'))]
            b=full.groupby(['day','hour','side']).R.mean().rename('base_R')
            for name in names:
                a=evidence(load('oil',source,1,'base',name),source);a['hour']=pd.to_datetime(a.decision,unit='s',utc=True).dt.tz_convert('America/New_York').dt.hour
                a=a.join(b,on=['day','hour','side']);a['lift']=a.R-a.base_R
                out[f'{source}/{name}']={'n':len(a),'baseline_ev':float(a.base_R.mean())if len(a)else None,'lift_ev':float(a.lift.mean())if len(a)else None,'lift_bootstrap':lab.bootstrap(a,'lift',4000)}
    # Gate controls preserve full one-position replay, including replacement opportunities.
    pairs=[('O1_ENERGY_NO_EIA','O1_ENERGY_5D'),('O2_SPREAD10','O2_BASE'),('O2_WAIT3','O2_BASE'),('O4_OVX_TP1','O4_BASE'),('O5_BOTH','O5_CONTINUE')]
    for a,b in pairs:
        aa,bb=primary('oil',a),primary('oil',b);out[f'paired/{a}/{b}']={'delta_R':float(aa.R.sum()-bb.R.sum()),'day_paired':mechanism.delta_boot(aa,bb)}
    lab.save_json(OUT/'controls.json',out);return out

def main():
    raw={n:json.loads((OUT/(n+'.json')).read_text())for n in ['micro_discovery','micro_all','micro_detailed','daily','oil_variants','diagnostics','verification']}
    counts={k:v.get('evaluation_cells',0)for k,v in raw.items()if k!='verification'}
    controls=matched_controls();aggregate={'counts':counts,'selection_status':'frozen prior to forward label inspection; data integrity exclusion after full download','primary':{},'no_live_change':True}
    lines=['# WTI / USOIL — Nasdaq kapılarının aktarımı ve petrol varyasyonları','',
    '**Sonuç: Nasdaq’ta seçilen kapılar WTI’ye aynı başarıyla taşınmadı. Beş petrol fikrini20 varyasyonla sınadım; bu çalışma beş kârlı veya canlıya hazır kapı bulmadı. EIA sonrası kırılım ve normalize stres sonrası alış küçük örneklem araştırma fikirleri olarak kaldı.**','',
    '## 1. Veri bütünlüğü: sonuçtan önce dikkat edilmesi gereken bulgu','',
    'Panelin petrol M1 geçmişinde farklı fiyat tabanları iç içe geçiyor. Doğrudan MT5 ile46.806 ortak mum karşılaştırmasında20.820 kapanış aynı;233 ardışık dakika geçişinde iki serinin fiyat farkı10 centten fazla değişiyor. İlk gözlenen geçiş28 Ağustos03:36UTC. Eylül21 gibi günlerde bu fark yaklaşık4,6 dolarlık sıçramalar yaratıyor. Bu, saat kaymasından farklı bir fiyat bütünlüğü sorunu; akışın kök nedeni bu araştırmada değiştirilmedi. Projenin mevcut `bl_ab30ec56db` ve `bl_5830306710` kayıtlarında Yahoo/MT5 fiyat tabanı karışması ve geçmiş cache onarımı zaten açık; bulgum bu kayıtlarla uyumlu, güncel üretim durumunun doğrulaması değildir.','',
    'Tam çakışmada ±1saat kaydırınca günlük fiyat farkından arındırılmış medyan hata yaklaşık0,294–0,295 dolar; doğru saatle0,003 dolar. Saat eşlemesi geçiyor, panel fiyat tutarlılığı geçmiyor. İlk180 mumluk referans kontrolü tek başına bu sorunu yakalamamıştı; tam geçmiş kontrolü yakaladı.','',
    '**Kanıt kapsamı:** Panel VALID döneminde20 Mayıs–27 AğustosNY kullanılır.28 Ağustos sonrası panel sonuçları yalnız tanı çıktısıdır. Nihai Eylül–1 Ekim testinde doğrudanSpotCrude serisi kullanılır. Fiyat mumları birbirine eklenmedi; rapordaki birleşik işlem istatistiği bu iki çakışmayan dönemin ayrı yürütülmüş R defterlerini toplar. Bu veri bütünlüğü kararı sonuçlar görüldükten sonra yapılan bir düzeltmedir; temiz yeni dış örneklem veya bağımsız sağlayıcı doğrulaması olarak sunulmuyor.','',
    'Önceki M1/M5 eşleşmesi keşifte hareket korelasyonu0,995–0,999, VALID_A’da0,9997; yine de fiyat tabanı ve geçmiş gerçek spread tam kanıtlanmış değildir. Bu eski bölüm de gerçek işlem PnL kanıtı değildir. Ayrıntılar: `historical_price_integrity.json`, `price_basis_overlap.csv`, `verification.json`.','',
    '## 2. İndirilen veri ve saatler','',
    '| Seri | Kullanılan mum | Başlangıç UTC | Son UTC |','|---|---:|---|---|']
    for s,d in datasets().items():lines.append(f'| {s} M1 | {len(d):,} | {d.ts.min()} | {d.ts.max()} |')
    for step in [5,15,30,60]:
        d=native(step);lines.append(f'| native M{step} | {len(d):,} | {d.ts.min()} | {d.ts.max()} |')
    lines+=['','Altı zaman diliminin hamcache geçmişi ve VIX/OVX/DXY/CL=F referansları indirildi. BrokerSpotCrude: point0,001,100barrel/lot. MT5 ham mum saati bu Ağustos–Eylül dönemindeUTC+3; normalleştirme−10.800s. Panel/nativesaatUTC: Nasdaq’a uygulanan eskiNY+7 veya erkenMart düzeltmesi petrole uygulanmadı. İstenenUSO, USOIL.FOREX/WTI olarak yorumlandı; USO ETF testi yapılmadı.','',
    'MT5 terminalindeki sınırlı geçmiş indirme sırasında ilerledi: metadata13 Ağustos başlangıcı gösterse de nihai kullanılan doğrudanM1 başlangıcı16 Ağustos22:00UTC. Ham indirmede46.807 satır;2 Ekim sınırındaki mum çıkarılınca46.806. D1ham geçmişi2010’dan geliyor ama28 Temmuz2026’da bitiyor; güncel makro etiketi olarak kullanılmadı. Önceki tamamlanmış16:00NY CFD kapanışı kullanıldı, futures settlement diye adlandırılmadı.','',
    'Dukascopy2025 M1 indirmesiHTTP429, alternatifhost403 nedeniyle veri sağlamadı. Bu nedenle2025 M1 testini yapılmış saymıyorum. Çok yıllıM15/M30/H1 inceleme M1 yürütmenin yerine geçmez. H1 enerji varyasyonunda14:30 OHLC içinden bilinemez:14:00açılış vekili kullanıldı, sonraki saat içi hareketler okunmadı.','',
    '## 3. Hangi önceki testler taşındı?','',
    '| Araştırma bölümü | Kapsam | Sonuç hücresi |','|---|---|---:|',
    f'| İlk432 ve genişletilmiş1620 tanım | 540sinyal ×3 risk/çıkış geometrisi; ilk432 altküme | {counts["micro_all"]} |',
    f'| Keşif ayrı kayıt | Aynı1620 tanım, iki keşif yarısı; tekrar gözlenen testler | {counts["micro_discovery"]} |',
    f'| Dondurulmuş10 strateji /20 mekanizma /kapılar |87 isimli test ve ebeveyn/kör/makro/mikro kontrolleri | {counts["micro_detailed"]} |',
    f'| CAPREV / çıkış /VIX /overnight /sermaye |19 günlük-yol tanımı +6 overnight +4 portföy kolu | {counts["daily"]} |',
    f'| Petrole özgü5 aile |20 varyasyon; M1/M3/M5/M15 ve stres ailesinin native testi | {counts["oil_variants"]} |',
    f'| Ek geometri tanıları |10 seçilmiş strateji ×1:1 /literal35 /literal80–110 | {counts["diagnostics"]} |',
    f'| **Toplam hesaplanan dönem hücresi** | Keşif tekrarları ve bağımlı kontroller dahil | **{sum(counts.values())}** |','',
    'Tarama1620 + ayrıntılı87 + günlük29 + petrol20 +tanı30 =1786 adlandırılmış konfigürasyon; ekonomik olarak benzersiz1786 kapı değildir. Dondurulmuş adaylar taramanın altkümesi; BASE/CAPREV/DIP_SAME, O4_OVX_TP1/O5_LONG gibi tanımlar aynı olayları paylaşır. TF/maliyet/sağlayıcı/split sayısı işlem örneklemi sayısı değildir.','',
    'Aktarılan kapılar: H1/K5b, K5, H2, RAWVOL, H3, WAITALL, H4, K6, COMBINED, H5 ve geri-alım kontrolleri; diğer rapordakiK1 Pazartesi satış, K2FOMC, K3ay sonu, K4a/bVR15/240, CHASE ve birleşimleri. K3 son iki iş günü standart hafta takvimidir; tatil duyarlı exchange takvimi değildir. Bazı önceki miner/gerçek-bot analizleri botun niyet/log evrenini gerektirir; OHLC’den aynı kapı-atlama, HOLD, cooldown, brokerdolumu veya botUSD kazancı üretilmedi.','',
    '## 4. Yürütme ve kronoloji','',
    'M1/M3/M5/M15 sinyali yalnız kapanmış mumlar; yürütme sonraki tamM1 açılışı. ATR70/ATR14 ve makro yalnız o anda bilinen geçmiş. İlk araştırma penceresiMon–Thu03:00–15:30, son çıkış15:55. Petrole uyarlanan minimum stop0,05USD/barrel; hızlı2ATR/15dk/RR2, ana5ATR/90dk/RR1,5, yavaş8ATR/240dk/RR2. Sabit petrol geometriTP%1,04/SL%1,49, önceki fiyat üzerinden risk. Nasdaq35/80/110 nominal dolar mesafeleri ayrı tanı olarak saklandı.','',
    'Cache spread0,03USD vekil; doğrudanMT5 M1 kayıtlı barspreadi medyan0,024USD. Bu barspreadi gerçek tarihsel giriş anı bid/askspreadi değildir. Her tarafta0,002slip; ek testspread×3, slip0,01 ve giriş+1M1. Komisyon ve gerçek geçmiş finansman bilinmiyor; overnight için5bp/gece yalnız duyarlılık. Sonuçlar maliyet modeli sonrasıR, brokerhesapUSD veya kâr tahmini değildir.','',
    'DISC_A11Şub–31Mar; DISC_B1Nis–15May. VALID_A20May–30Haz; VALID_B1Tem–28Ağu (kanıtta28Ağustos çıkarıldı). FINAL_A1–15Eyl; FINAL_B16Eyl–1Eki. Split sınırını geçen sonuçlar dışarıda. Doğrudan makro kendi kapanışlarından hesaplanır;20gün volatilite ve200gün uzama ısınması veri başında yoktur. H4/K6 gibi200gün isteyen kapı için doğrudan kısa geçmiş sıfır etki gösteriyorsa bu doğrulama değildir.','',
    'Her defterde tek pozisyon ve600s yeniden giriş aralığı. Stop/TP aynı mumsa stop öncelikli; açılış hedefi sonraki stop hareketinden önce; stopgap kötü açılıştan dolabilir. Gün içi bilinmeyen veri boşluğunda son gözlenen fiyatla vekil R hesaplanır; `data_gap` etiketi ve en az−1R duyarlılığı korunur. Bu gerçek dolum değildir. Gece işleminin terminal seansı eksikse sonuç çözülememiş olarak ayrı tutulur. NativeM15/30/H1OHLC stop sırası belirsiz ve spreadvekil olduğundan go-live yürütme kanıtı sayılmaz.','',
    '## 5. Beş petrol fikri: ayrı doğrulama ve nihai MT5 dönemi','',
    'Aşağıdaki temsilciler kârlı diye seçilmiş yeni beşli portföy değildir;20 sabit varyasyondan her mekanizmayı anlatan örneklerdir. Birleştirilmiş sonuç, VALIDcache (<28Ağu) + FINALdirect (Eyl–1Eki); aynı olaylar çift sayılmadı.','',
    '| Fikir | n | Toplam R | EV R | WR ve Wilson%95 | Gün-bootstrap EV%95 | MaxDD R |','|---|---:|---:|---:|---|---|---:|']
    for nm,label in zip(MAIN,LABELS):
        a=primary('oil',nm);aggregate['primary'][nm]={'stats':stats(a,True),'by_epoch':{s:stats(z,True)for s,z in a.groupby('feed')},'by_side':{str(side):stats(z,True)for side,z in a.groupby('side')}}
        lines.append(f'| {nm}: {label} | {table_metric(a)} |')
    lines+=['','**O1:**15dakikalık orta seviyeyi yönsel/verimli hareketle geri alma. Keşifte seçilen LEGACY iyi görünmesine rağmen ileri döneme taşınmadı. Enerji penceresi ve EIA çevresi veto maliyet/yoğunluğu değiştirdi; kalıcı pozitif kenar yaratmadı.','',
    '**O2:**30dakikalık verimli geri çekilme; spread/risk≤%10/20. Bu stop boyutlarında her iki spreadfiltresi BASEile aynı işlem kümesini bıraktı. Bir şey elemediği için başarı katmış kabul edilemez.3dakika bekleme de güvenilir iyileştirme üretmedi.','',
    '**O3:**EIA öncesi tam60M1range, yayın+5 veya+15dakika sonrasında gövdeli kırılım; release+45e kadar ilk olay,5ATR/90dk/RR1,5. BREAK5 küçük pozitif;5 ve15dakika tetiklerde VALIDbölümü negatif. Keşif BREAK5negatifken sonrakipozitif olduğu için bu zaten istikrarlı iki-yarı başarı değildir. Yayın sonrası rangeiçi FADE5 çoğunlukla negatif. Haber sürprizi/beklenti verisi kullanılmadı.','',
    '**O4:**Önceki petrol getirisi−1σ veya5gün−√5σ, önceki09:00–14:30seans düşük seviyesi altında ilk kapanış; OVX önceki252gün medyanı üstünde, günlükσrisk, +1R veya14:30. VIX18,4yerine petrolün kendi volatilitesini kullanma fikri mantıklı ama örneklem küçüktür. Native sonuçlar yıl/TF arasında işaret değiştirir.','',
    '**O5:**Aynı stressin yukarı aynasıyla satış veya aşağıstressalış; BOTHgeri dönüş, CONTINUEşoku takip. Yönü ters çevirmek istikrarlı fark üretmedi. NativeH1BOTH265olayına rağmen yakın dönemi negatiftir; uzunörneklem alone geçiş bileti değildir.','',
    '###20 varyasyonun tamamı — hiçbir başarısız kol gizlenmedi','',
    '| Varyasyon | VALIDcache n/R (<28Ağu) | FINALdirect n/R | Birleşik n/R |','|---|---|---|---|']
    for fam,vs in DEFS.items():
        for v in vs:
            nm=fam+'_'+v;aa=[evidence(load('oil',s,1,'base',nm),s)for s in ['cache','direct']];a=primary('oil',nm)
            lines.append(f'| {nm} | {len(aa[0])}/{num(aa[0].R.sum())} | {len(aa[1])}/{num(aa[1].R.sum())} | {len(a)}/{num(a.R.sum())} |')
    lines+=['','### Zaman dilimi doğrulaması — aynı M1 yürütme','',
    '| Temsilci | M1 n/R | M3 n/R | M5 n/R | M15 n/R |','|---|---|---|---|---|']
    for nm in MAIN:
        cols=[]
        for tf in [1,3,5,15]:
            a=primary('oil',nm,tf);cols.append(f'{len(a)}/{num(a.R.sum())}')
        lines.append('| '+nm+' | '+' | '.join(cols)+' |')
    lines+=['','TFler aynı piyasa günlerini paylaştığından örnek sayıları toplanamaz. Özellikle O2M5pozitif görülüp M1/M3negatif çıkması başarılıM5yeniden seçimi için izin değildir; yeni dönem testi gerektirir.','',
    '### Maliyet ve gecikme — M1 net toplamR','',
    '| Temsilci | Baz | Spread×3 | Slip0,01 | +1M1 |','|---|---:|---:|---:|---:|']
    for nm in MAIN:lines.append('| '+nm+' | '+' | '.join(num(primary('oil',nm,1,c).R.sum())for c in ['base','spread3','slip1','delay1'])+' |')
    lines+=['','### Çok yıllı stres varyasyonları — ayrı nativeOHLC, yalnız2025 sonuna kadar','',
    '| Kural | M15 n/R | M30 n/R | H1 n/R |','|---|---|---|---|']
    for nm in ['O4_BASE','O4_OVX_TP1','O5_SHORT','O5_BOTH','O5_CONTINUE']:
        cols=[]
        for step in [15,30,60]:
            a=load('oil',f'native{step}',step,'base',nm);a=a[a.day<'2026-01-01'];cols.append(f'{len(a)}/{num(a.R.sum())}')
        lines.append('| '+nm+' | '+' | '.join(cols)+' |')
    lines+=['','Yıl bloklarının tüm istatistikleri `oil_variants.json` içinde. H1ilk2016–2020dönemi ile2021–2023/2024–2025aynı değildir. Buradaki200+OHLColayı150gerçek nextM1/actualspread koşulunu karşılamaz.','',
    '## 6. Nasdaq’taki kazanç fikri WTI’de ne oldu?','',
    '| Önceden dondurulmuş Nasdaq stratejisi | WTI kanıt dönemi n/R |','|---|---|']
    from micro import FROZEN1,FROZEN2
    for spec in FROZEN1+FROZEN2:
        nm='frozen_'+spec['id'];a=primary('micro',nm);lines.append(f'| {spec["id"]} | {len(a)}/{num(a.R.sum())} |')
    lines+=['','Nasdaq beşli araştırma portföyü ve ek CAPREV, bütün fırsatlarla tekrar yürütüldü; yalnız kabul edilmiş eski işlemlerden türetilmedi.','',
    '| Portföy | n | Toplam R | Taban farkıR | Gün-eşli fark güven aralığı |','|---|---:|---:|---:|---|']
    portfolios={}
    for rule in ['NONE','BASE','HALF_RISING','TP1_RISING']:
        aa=[]
        for s in ['cache','direct']:aa.append(evidence(pd.read_csv(OUT/f'capital_{s}_base_{rule}.csv'),s))
        portfolios[rule]=pd.concat(aa,ignore_index=True).sort_values('decision')
    b=portfolios['NONE']
    for rule,a in portfolios.items():
        ci=mechanism.delta_boot(a,b)['ci95'];lines.append(f'| {rule} | {len(a)} | {num(a.R.sum())} | {num(a.R.sum()-b.R.sum())} | [{ci[0]:+.3f},{ci[1]:+.3f}] günlükR |')
        aggregate.setdefault('capital',{})[rule]=compare(a,b)
    lines+=['','Nasdaq’ta daha önceki +9,40R katkı WTI için varsayılmadı. RisingVIX/+1Rburada petrolmekanizması olarak doğrulanmadı; CAPeklemek kaybeden taban portföyünü otomatik kârlı yapmıyor.','',
    '| Günlük yol / negatif kontrol | n | ToplamR |','|---|---:|---:|']
    for rule in raw['daily']['paths']+['ON_'+r for r in raw['daily']['overnight']]:
        a=primary('daily',rule);lines.append(f'| {rule} | {len(a)} | {num(a.R.sum())} |')
    lines+=['','Açılış/gece kombinasyonu tek pozisyon altında ölçüldü. İki ayrı bacağın toplamı iki katsermaye veya birbirini örten pozisyonlarla başarı diye raporlanmadı. Fonlama duyarlılığı ve çözülememiş işlemler `daily.json` içinde.','',
    '## 7. Kontroller, belirsizlik ve karar','',
    'Seçim1620deneme yükü taşır. Bootstraplar gün bloklarıyla4000tekrar, işlemWRWilson%95, iki kronolojik yarı ve eniyi5işlem çıkarma çıktıları korunmuştur. Çoklu testten bağımsız alfa iddiası yok. BREAK5eniyi5işlem çıkarılınca pozitiflik kaybolur; +R örneklerin küçük sayısına dayanır. Her işleme eşitRrisk yaklaşımı kullanıldı; sabitlot ve eşitRkazanç aynı şey değildir.','',
    'EIA BREAK5 pozitif net R gösterse de aynı gün/saat/yön/geometri genel dakika girişlerinden daha iyi değildir: VALID lift yaklaşık−0,27R, FINAL lift−0,38R. Dolayısıyla pozitif toplamı kanıtlanmış giriş becerisi diye yorumlamıyorum. Aynı gün/saat/yön/geometri genel dakika girişleriyle O1/O2/O3matchedEV karşılaştırması yapıldı (`controls.json`). Bu genel fırsatlar örtüşür; yürütülebilir portföy PnL olarak sunulmaz. EIA için bu genel saat kontrolü haberçevresi etkisini bütünüyle ayırmaz. OVX/BASE, EIA veto/ebeveyn, WAIT3/ebeveyn ve dönüş/devam gün-eşli karşılaştırmaları da saklandı. Veto ardından boşalan sermayenin alacağı farklı fırsatlar defterde yeniden yürütüldü.','',
    '| Kontrol | n | Aynı gün/saat/yön tabanEV | Aday liftEV | Lift%95 |','|---|---:|---:|---:|---|']
    for k,v in controls.items():
        if k.startswith('paired/'):continue
        ci=v['lift_bootstrap']['ci95'];lines.append(f'| {k} | {v["n"]} | {num(v["baseline_ev"]or 0)} | {num(v["lift_ev"]or 0)} | [{ci[0]:+.3f},{ci[1]:+.3f}] |')
    v=raw['verification'];lines+=['',f'Denetimler: {len(v["fixtures"])}yürütme fikstürü; dörtTFde540sinyal tanımının prefix testi ve günlük/makro prefixleri; {v["ledgers"]["ledgers"]}işlemdefteri tek-pozisyon/600skontrolü geçti. Yeni mumlar eklenince geçmiş sinyal değişmedi. Başlangıçta bir Pythonruntimeındaki rollinghesabı boş validkümesi üretti; o çıktı `INVALID_runtime_empty_discovery.json` adıyla geçersiz saklandı, sistemPython/pandas3ile tekrarlandı. Bu rapor geçersiz ilk çıktıyı kullanmaz.','',
    '**Durum:** O1/O2 mevcut kurallarla reddedildi. O3 veO4 yalnız yeni temiz veriyle incelenecek araştırma adayları. O5yön aynası kalıcı kenar göstermedi. Beş aileden hiçbirineLIVEkartı verilmedi; bot veya gölge çalışan kapı eklenmedi.','',
    'Öncelikli sonraki çalışma: petrol fiyat kaynağı geçişlerini kaynakkimliğiyle teşhis edip tek tutarlı kontratla arşivlemek; ardından bu20dondurulmuş varyasyonu yeni dönem gerçekspread/dolum/komisyonla enaz150uygun çözümlenmiş olaya kadar doğrulamak. Bu raporun ölçmediği botHOLD/WAIT/kapı atlama evreni ayrı gerçek kararlogları gerektirir.','',
    '## 8. Grafikler ve kaynaklar','',
    '![Kanıt dönemlerinin ayrı yürütülmüş R çizgileri](results/equity.png)','',
    '![İlk kronolojik kazanan/kaybeden EIA örnekleri](results/first_win_loss.png)','',
    'Grafikler betimleyicidir. İki örnek başarı oranı kanıtı değildir; olumlu örnekler elle ayıklanmadı.','',
    '- [EIA resmi Weekly Petroleum Status Report yayın takvimi](https://www.eia.gov/petroleum/supply/weekly/schedule.php): Çarşamba10:30NY ve2025/2026tatil değişimleri. İlkOcak2026belirsiz sınır haftaları takvimden çıkarıldı; M1zatenŞubatta başlıyor.',
    '- [Fed resmi FOMC takvimi](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm): K2bilinen toplantı günleri.',
    '- [CME petrol kontrat özellikleri](https://www.cmegroup.com/markets/energy/crude-oil/light-sweet-crude.contractSpecs.html) ve [resmi settlement yöntemi](https://www.cmegroup.com/trading/energy/files/NYMEX_Energy_Futures_Daily_Settlement_Procedure.pdf): petrolseans referansı. CFD16:00kapanışı CMEsettlementdeğildir.',
    '- [Dukascopy resmi petrol CFD ürün sayfası](https://www.dukascopy.com/swiss/english/cfd/range-of-markets/cfd-commodities/): denenmiş2025veri kaynağı; veri indirilemedi.',
    '- [Bailey vd., backtest overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf): büyük taramalarda seçim yanlılığı.','',
    '## 9. Dosyalar ve yeniden üretim','',
    '`PROTOCOL.md`, `PROTOCOL_OIL_VARIANTS.md`; ham ve temiz indirmeler yerel `data/` içinde. SonuçJSON/CSVleri `results/` içinde. `aggregate.json` raporun kalite kapsamına göre hesaplanan ana ölçümleri; kapsam hücreleri ham deneyJSONlarında, clock/price/fill denetimleri ayrı. Kaynaktaki Nasdaq araştırma dosyaları değiştirilmedi.','',
    '```bash','python3 research/wti_transfer_20261002/micro.py scan','python3 research/wti_transfer_20261002/micro.py detailed','python3 research/wti_transfer_20261002/daily.py','python3 research/wti_transfer_20261002/oil_variants.py','python3 research/wti_transfer_20261002/diagnostics.py','python3 research/wti_transfer_20261002/verify.py','python3 research/wti_transfer_20261002/make_report.py','```','',
    'Hesap runtimeı sistemPython3/pandas3; indirme ve parquet hazırlığı `.venv` ile yapıldı. `make_report.py` yalnız yerel kayıtlı veriyi okur. Veriyi yeniden indirme komutları `pull.py` içindedir; ağ ve salt-okunurMT5köprüsü gerektirir.']
    text='\n'.join(lines)+'\n'
    # Space numeric quantities without touching code identifiers or link destinations.
    pieces=re.split(r'(`[^`]*`|https?://[^)\s]+)',text)
    for i in range(0,len(pieces),2):
        pieces[i]=re.sub(r'(?<=\d)(?=[a-zçğıöşü])',' ',pieces[i])
        pieces[i]=re.sub(r'(?<=[a-zçğıöşü])(?=\d)',' ',pieces[i])
    text=''.join(pieces)
    text=text.replace('###20','### 20')
    text=re.sub(r'(?<=[;:])(?=[0-9A-ZİÖÜÇŞ])',' ',text)
    text=re.sub(r'(?<=[a-zçğıöşü]\.)(?=[0-9A-ZİÖÜÇŞ])',' ',text)
    replacements={'doğrudanSpotCrude':'doğrudan SpotCrude','AğustosNY':'Ağustos NY','hamcache':'ham cache','BrokerSpotCrude':'Broker SpotCrude','dönemindeUTC':'döneminde UTC','Panel/nativesaatUTC':'Panel/native saat UTC','eskiNY':'eski NY','erkenMart':'erken Mart','İstenenUSO':'İstenen USO','doğrudanM1':'doğrudan M1','yıllıM15':'yıllı M15','indirmesiHTTP429':'indirmesi HTTP429','alternatifhost':'alternatif host','penceresiMon':'penceresi Mon','b/bVR':'b/b VR','K5 b':'K5b','K4 a':'K4a','diğer rapordakiK1':'diğer rapordaki K1','K2FOMC':'K2 FOMC','brokerdolumu':'broker dolumu','botUSD':'bot USD','geometriTP':'geometri TP','bid/askspreadi':'bid/ask spreadi','testspread':'test spread','giriş+1M1':'giriş +1 M1','NativeM15':'Native M15','H1OHLC':'H1 OHLC','spreadvekil':'spread vekil','VALIDcache':'VALID cache','FINALdirect':'FINAL direct','sonrakipozitif':'sonraki pozitif','VALIDbölümü':'VALID bölümü','rangeiçi':'range içi','aşağıstressalış':'aşağı stres sonrası alış','BOTHgeri':'BOTH geri','CONTINUEşoku':'CONTINUE şoku','NativeH1BOTH265':'Native H1 BOTH: 265','uzunörneklem alone':'uzun örneklem tek başına','sonrakipozitif':'sonraki pozitif','gün-eşli':'gün eşli','VIX18':'VIX 18','kanıtlanmış giriş becerisi':'kanıtlanmış giriş becerisi','skontrolü':'s kontrolü','Pythonruntimeındaki':'Python ortamındaki','rollinghesabı':'rolling hesabı','validkümesi':'valid kümesi','sistemPython':'sistem Python','veO4':'ve O4','hiçbirineLIVEkartı':'hiçbirine LIVE kartı','kaynakkimliğiyle':'kaynak kimliğiyle','botHOLD':'bot HOLD','kararlogları':'karar logları','İlkOcak':'İlk Ocak','zatenŞubatta':'zaten Şubatta','petrolseans':'petrol seans','CMEsettlementdeğildir':'CME settlement değildir','SonuçJSON/CSVleri':'Sonuç JSON/CSV’leri','deneyJSONlarında':'deney JSON’larında','salt-okunurMT5':'salt okunur MT5','son iki iş günü':'son iki iş günü'}
    for a,b in replacements.items():text=text.replace(a,b)
    for a,b in {'doğrudanMT5':'doğrudan MT5','tamM1':'tam M1','dörtTFde':'dört TF’de ','tek-pozisyon':'tek pozisyon','gerçekspread':'gerçek spread','aynıR':'aynı R','barspreadi':'bar spreadi','sonrasıR':'sonrası R','brokerhesapUSD':'broker hesap USD','işlemdefteri':'işlem defteri','barrel/lot':'barrel/lot','NASDAQ':'NASDAQ','veriyleSpotCrude':'veriyle SpotCrude','Enaz':'En az','enaz':'en az','spreadfiltresi':'spread filtresi','BASEile':'BASE ile','geçmişfinansman':'geçmiş finansman','günlükσrisk':'günlük σ risk','kârlı yapmıyor':'kârlı yapmıyor'}.items():text=text.replace(a,b)
    text=text.replace('(results/equity.png)',f'({OUT}/equity.png)').replace('(results/first_win_loss.png)',f'({OUT}/first_win_loss.png)')
    (HERE/'NIHAI_RAPOR.md').write_text(text);lab.save_json(OUT/'aggregate.json',aggregate)
    plots();files=list(HERE.glob('*.py'))+list(HERE.glob('*.md'))+list(OUT.glob('*.json'))
    dependencies=[Path(m.__file__)for m in [lab,old2,olddata,mechanism,synth,cap_paths,cap_overnight]]
    dependencies+=list((ROOT/'research/ndx_five_gates_20260930/results').glob('frozen*.json'))
    aggregate['dependency_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in dependencies}
    lab.save_json(OUT/'aggregate.json',aggregate)
    lab.save_json(OUT/'code_result_provenance.json',{'runtime':platform.python_version(),'pandas':pd.__version__,'files':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files if p.name!='code_result_provenance.json'}})
    print('REPORT',HERE/'NIHAI_RAPOR.md','cells',sum(counts.values()),flush=True)
if __name__=='__main__':main()
