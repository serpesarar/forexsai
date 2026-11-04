"""Build the consolidated Turkish research artifact from saved executions."""
import os
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/ndx_synthesis_mpl")
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from run import HERE, OUT, PRIMARY, OVERLAYS, RECLAIMS, lab, load_data, summary
from caprev import context_extra

PERIODS = ["D25a", "D25b", "C26", "M26", "S26"]
NAMES = {"D25a": "2025 ilk yarı", "D25b": "2025 ikinci yarı", "C26": "2026 Şub–May15", "M26": "2026 May20–Ağu28", "S26": "2026 Eyl1–29"}


def trades(rule, tf=1, case="base", periods=PERIODS):
    return pd.concat([pd.read_csv(OUT / f"trades_{p}_{tf}_{case}_{rule}.csv") for p in periods], ignore_index=True).sort_values("decision").reset_index(drop=True)


def num(v):
    return f"{v:+.2f}"


def main():
    main_eval = json.loads((OUT / "evaluation.json").read_text())
    extra = json.loads((OUT / "addendum.json").read_text())
    allrules = OVERLAYS + RECLAIMS + ["CAPREV", "CAP_ALLVIX", "CAP_LOWVIX", "CAP_CALM", "CAP_SELL", "CAP_FIXED", "CAP_RECLAIM", "CHASE"]
    base = trades("BASE")
    aggregate = {}
    for r in allrules:
        a = trades(r)
        parent = trades("RECLAIM_ALL") if r in RECLAIMS else base
        aggregate[r] = summary(a, parent)
        aggregate[r]["halves"] = [lab.stats(a.iloc[:len(a)//2]), lab.stats(a.iloc[len(a)//2:])]
        if r.startswith("CAP"):
            aggregate[r]["risk_min_median_max"] = [float(a.risk.min()), float(a.risk.median()), float(a.risk.max())] if len(a) else []
            aggregate[r]["drop_best"] = {str(n): lab.stats(a.sort_values("R").iloc[:-n].sort_values("decision")) for n in [1, 3, 5] if len(a) > n}
            # A different strategy's total is not the incremental effect of an entry veto.
            for key in ["base_total_R", "delta_R", "paired", "worst_gap_delta_R"]:
                aggregate[r].pop(key, None)
    lab.save_json(OUT / "aggregate.json", aggregate)
    ds = load_data()
    diagnostics = {}
    for source, d in ds.items():
        f = pd.read_pickle(OUT / f"features_{source}_1.pkl")
        from run import events
        x = events(f, 1)
        diagnostics[source] = {"bars": len(d), "raw_opportunities": len(x),
                               "volume_unknown": int(x.season_ratio.isna().sum()), "shock_raw_opportunities": int(x.shock.sum()),
                               "prev_rth_unknown": int(x.prev_rth_low.isna().sum())}
    actual = pd.read_csv(OUT / "actual_decisions.csv")
    f = context_extra(ds["mt5"], pd.read_pickle(OUT / "features_mt5_1.pkl"))
    ix = np.searchsorted(f.decision, actual.decision, side="right") - 1
    cf = f.iloc[ix].reset_index(drop=True)
    score = np.sum(np.vstack([(cf.channel5 <= -1), (cf.m15_dir < 0),
                              (actual.open_price < cf.prev_rth_low), cf.stress]), axis=0)
    actual["chase_sell"] = score
    sell = actual[actual.side < 0]
    diagnostics["actual_chase_buckets"] = {str(k): {"n": len(z), "mean_points": float(z.points.mean())} for k, z in sell.groupby("chase_sell")}
    diagnostics["H1_not_in_chase"] = int((actual.H1 & ~(actual.side.lt(0) & (score >= 3))).sum())
    diagnostics["fresh_day"] = {"bars_utc_oct1": int(((ds['mt5'].t >= lab.stamp('2026-10-01')) & (ds['mt5'].t < lab.stamp('2026-10-02'))).sum()),
                                "note": "UTC day includes the entire NY strategy session; all exits precede the UTC boundary."}
    lab.save_json(OUT / "diagnostics.json", diagnostics)

    # Small research figures, no implied capital curve or USD conversion.
    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": .2})
    fig, ax = plt.subplots(2, 1, figsize=(12, 8), constrained_layout=True)
    for r, label in [("CAPREV", "CAPREV: daily-vol stop / 16:00"), ("CAP_FIXED", "Same entry: TP80 / SL110"), ("CAP_RECLAIM", "Reclaim confirmation / daily-vol stop")]:
        a = trades(r)
        ax[0].step(pd.to_datetime(a.decision, unit="s", utc=True), a.R.cumsum(), where="post", marker="o", label=label)
    ax[0].set(title="CAPREV execution audit — 2025/2026, very small sample", ylabel="Cumulative simulated R")
    ax[0].legend(loc="upper left", fontsize=9)
    ax[0].set_xlim(pd.Timestamp("2025-01-01", tz="UTC"), pd.Timestamp("2026-10-02", tz="UTC"))
    xx = np.arange(5)
    for i, r in enumerate(["H1", "H2", "H3", "H4", "CHASE"]):
        vals = [(main_eval["results"] if r != "CHASE" else extra["results"])[f"{p}_1_base_{r}"]["delta_R"] for p in PERIODS]
        ax[1].bar(xx + (i - 2) * .15, vals, width=.15, label=r)
    ax[1].set_xticks(xx, ["2025 H1", "2025 H2", "2026 Feb–May", "2026 May–Aug", "2026 Sep"])
    ax[1].set(ylabel="Change vs frozen portfolio (R)", title="Entry vetoes: executable effect by period")
    ax[1].axhline(0, color="black", lw=.7); ax[1].legend(ncol=5)
    fig.savefig(OUT / "comparison.png", dpi=160); plt.close(fig)
    cap = trades("CAPREV")
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), constrained_layout=True)
    for ax, r in zip(axes, [cap[cap.R > 0].iloc[0], cap[cap.R < 0].iloc[0]]):
        d = ds["duka"] if r.day.startswith("2025") else ds["mt5"]
        z = d[(d.t >= r.decision - 3600) & (d.t <= r.exit_t + 1800)]
        tm = pd.to_datetime(z.t, unit="s", utc=True).dt.tz_convert("America/New_York")
        ax.plot(tm, z.close, color="#295f88", lw=1)
        ax.axhline(r.entry, color="#258051", label="Ask entry")
        ax.axhline(r.entry - r.risk, color="#be433d", ls="--", label="Initial stop")
        for tt, col, label in [(r.entry_t, "#258051", "Entry"), (r.exit_t - 60, "#be433d", "Exit bar")]:
            ax.axvline(pd.Timestamp(tt, unit="s", tz="UTC").tz_convert("America/New_York"), color=col, ls=":", label=label)
        ax.set(title=f"First chronological {'win' if r.R > 0 else 'loss'}: {r.day}, {r.R:+.3f}R ({r.reason})", ylabel="Nasdaq price", xlabel="New York local time")
        ax.legend(ncol=4, fontsize=8)
    fig.savefig(OUT / "trade_examples.png", dpi=160); plt.close(fig)

    lines = ["# Nasdaq — iki araştırmanın sentezi ve nihai icra raporu", "", "Tarih: 2 Ekim 2026. Durum: **offline araştırma; hiçbir strateji LIVE onayı almadı.**", "",
    "**Sonuç:** İki rapordan beş yeni varyasyon türettim; diğer raporun sonradan fark edilen TUR3 ekindeki CAPREV ve kovalama endeksini de denetledim. En güçlü araştırma fikri **yüksek VIX altında, günlük volatilite stoplu ve seans kapanışına taşınan CAPREV**. En makul seçici veto **K5b/H1**. İkisinin de kanıtı canlıya geçmek için yetersiz. Diğer filtreleri üst üste eklemek net bir iyileştirme getirmedi.", "",
    "Bu tur **22 sabit yapılandırma, 924 dönem/zaman dilimi/maliyet değerlendirme hücresi** içerir. Bunlar 924 bağımsız deneme değildir. İlk 14 tanım ana protokolde, son 8 tanım ek protokolde sonuçlarından önce yazıldı; yeni sonuçla eşik seçilmedi. 2025–Eylül 2026 geçmişi önceki turlarda görülmüştür. Bu turun tarih bölmeleri yeni, dokunulmamış OOS diye sunulamaz.", "",
    "## 1. İki rapor nerede birleşiyor, nerede ayrılıyor?", "",
    "| Konu | Birlikte çıkarılan sonuç |", "|---|---|",
    "| Stres sonrası SELL | Diğer raporun K5b bulgusunu gerçek bot örneklerinde tekrar elde ettim: 41 karar / 5 gün, ortalama −12,82 puan. Bu küçük ve önceden görülmüş örneklem. Yeni portföyde etkisi ayrıca ölçüldü. |",
    "| Teyit beklemek | Bizim koşulsuz bekleme filtremiz birçok dönemde kazananı kaçırdı. Diğer rapor bunu teyitsiz alıma bağladı. Bu, mantıklı hipotez; günlük ölçekte bütün teyitlerin zararlı olduğu kanıtlanmış değil. |",
    "| Hacim şoku | Ham M5 oranı botun 18 kararında olumsuz; aynı saatin geçmişiyle normalize edilince yalnız 2 bot kararı kalıyor. Evrensel ve taşınabilir bir hacim kapısı henüz yok. |",
    "| Kovalama | Bot örneklerinde kötü alt kümeler var; özgün beşli portföye uygulanınca katkı çok küçük ve Eylül'de negatif. Bot ve araştırma sinyali aynı evren değil. |",
    "| Uzama BUY vetosu | Günlük fiyat uzaması tek başına alım engeli yapmak için yeterli değil; daha seçici H4 bile beş dönemin tamamında portföye zarar verdi. |",
    "| Portföy bağımlılığı | Bir grubun ortalama kaybı, o grubu engellemenin portföye aynı miktarda kazandıracağı anlamına gelmez. Boşalan zaman dilimlerine başka işlemler girer. Bütün vetolar bu nedenle yeniden sıralandı. |", "",
    "## 2. Beş yeni varyasyon — ana deney", "",
    "H1–H4 için aşağıdaki sayılar **taban portföye toplam R katkısıdır**. H5 yeni giriş stratejisidir; kendi toplam R'si yazılmıştır. Pozitif ΔR, stratejinin kendisinin her dönemde kârlı olduğu anlamına gelmez.", "",
    "| Varyasyon | 2025 ilk | 2025 ikinci | Şub–May | May–Ağu | Eylül | Karar |", "|---|---:|---:|---:|---:|---:|---|"]
    descriptions = {"H1": "Stres + önceki RTH dibi altında SELL veto", "H2": "Ham ve saat-normalize M5 hacim şoku veto", "H3": "Yalnız hacim şokunda 3 dk fiyat sınırlı bekleme", "H4": "MA200+%10 ve 4s aralığın üst %20'sinde BUY veto", "H5": "Stres sonrası önceki RTH dibini geri alan BUY"}
    verdict = {"H1": "Seçici gölge araştırma adayı", "H2": "Reddedildi", "H3": "Reddedildi", "H4": "Reddedildi", "H5": "Seyrek ve kararsız; terfi yok"}
    for r in PRIMARY:
        vals = [main_eval["results"][f"{p}_1_base_{r}"]["total_R" if r == "H5" else "delta_R"] for p in PERIODS]
        lines.append(f"| {r}: {descriptions[r]} | " + " | ".join(num(v) for v in vals) + f" | {verdict[r]} |")
    h1 = aggregate["H1"]
    lines += ["", f"**H1/K5b:** toplam katkı {h1['delta_R']:+.2f}R; 330 işlem gününün yalnız **{h1['paired']['affected_days']} günü** değişiyor. Eşleştirilmiş gün bootstrap'ında katkının pozitif kalma payı %{100*h1['paired']['p_positive']:.1f}; günlük ΔR %95 aralığı [{h1['paired']['ci95'][0]:+.4f}, {h1['paired']['ci95'][1]:+.4f}]. Sıfır aralığın içinde. Beş ana hipotez için düzeltmeli tek yönlü p={h1['paired']['bonferroni_p5']:.3f}; istatistiksel doğrulama değil.", "",
    "**H5:** 41 işlem / 18 gün, toplam +3,23R; Mayıs–Ağustos −1,77R ve Eylül'de olay yok. Geri alımı beklemek tek başına güvenilir yeni giriş üretmedi. CAPREV ile aynı çıkış geometrisi kullanıldığında ayrıca karşılaştırıldı.", "",
    "**Kontroller önemli:** tüm stresli günlerin SELL'ini engelleyen K5, 2025 ilk yarıda −12,38R; yalnız dibin altını engelleyen H1 aynı dönemde −1,56R. Buna karşılık Mayıs–Ağustos'ta K5 +8,00R, H1 +1,11R. Seçicilik her dönemde üstün değil. Ham hacim vetosu ΔR: −8,14 / −1,56 / +3,15 / −1,39 / 0,00. Koşulsuz 3 dakika bekleme: −16,02 / −20,50 / +8,07 / +2,12 / −4,74R. Bütün uzamış günlerin BUY'ını engelleyen K6 da son dört dönemde zarar verdi.", "",
    "### Zaman dilimi aktarımı", "",
    "| Kural | M1 | M3 | M5 | Ölçü |", "|---|---:|---:|---:|---|"]
    for rule in PRIMARY + ["CHASE"]:
        vals = []
        for tf in [1, 3, 5]:
            a = trades(rule, tf)
            vals.append(float(a.R.sum()) if rule == "H5" else float(a.R.sum() - trades("BASE", tf).R.sum()))
        lines.append(f"| {rule} | " + " | ".join(num(v) for v in vals) + (" | Kendi toplam R |" if rule == "H5" else " | Portföye ΔR |"))
    lines += ["", "M3 taban portföy −48,07R, M5 taban −30,79R. Örneğin H1 iki ölçekte katkı sağlasa da portföyleri kârlı hale getirmedi. Agregasyonlar aynı M1 fiyat yolunun dönüşümüdür; üç bağımsız piyasa örneği değildir.", "",
    "### Maliyet ve birleşim denetimi", "",
    "| İcra | Taban toplam R | H1 katkısı | H2 katkısı | H3 katkısı | H4 katkısı | Birleşim katkısı |", "|---|---:|---:|---:|---:|---:|---:|",
    "| Ana | +57,12 | +6,11 | −11,59 | −7,46 | −9,16 | −15,12 |",
    "| Spread ×3 | −90,68 | +1,98 | −7,16 | −1,23 | −5,33 | −9,91 |",
    "| Kayma 1 puan/taraf | −1,28 | +3,36 | −10,89 | −6,99 | −8,93 | −16,88 |",
    "| Giriş +1 M1 | +24,40 | +1,22 | −6,16 | −5,08 | −12,04 | −19,28 |", "",
    "H1'in katkısı pozitif kalsa da spread3 altında portföy hâlâ −88,70R: bir veto pozitif katkıyla canlı stratejiye dönüşmez. Birleşimde H2 zaten hacim şokunu veto ettiği için H3'ün bekleme kısmı etkisizdir; kombinasyon toplam katkıyı artırmadı.", "",
    "## 3. CAPREV — en önemli yeni denetim", "",
    "Diğer raporun kuralını tutarlı bir M1 yürütmeye çevirdim: önceki nakit gün getirisi ≤−%1,5 veya son beş gün ≤−%4; önceki VIX≥18,4; Pazartesi–Perşembe NY03:00–15:00 arası önceki **tam 09:30–16:00 RTH** dibinin altındaki ilk kapanış; sonraki M1 açılışı/ask'ten BUY. Stop: önceki 20 nakit gün getirisinin standart sapması × giriş fiyatı. Hedef yok; NY16:00 M1 açılışında çıkış. Günde en fazla bir işlem.", "",
    "| Denetim | İşlem | Toplam R | Ortalama R |", "|---|---:|---:|---:|"]
    for tf, case, title in [(1,"base","M1 ana"),(5,"base","M5 tetikleyici, M1 icra"),(15,"base","M15 tetikleyici, M1 icra"),(1,"spread3","Spread ×3"),(1,"slip1","Her tarafta 1 puan kayma"),(1,"delay1","Giriş +1 M1 gecikme")]:
        a = trades("CAPREV", tf, case)
        lines.append(f"| {title} | {len(a)} | {num(a.R.sum())} | {num(a.R.mean())} |")
    c = aggregate["CAPREV"]
    lines += ["", f"Ana örneklem yalnız **11 işlem / 11 gün**. 2025 ilk yarı 6 işlem {num(extra['results']['D25a_1_base_CAPREV']['total_R'])}R; 2025 ikinci yarı 1 işlem +0,79R; Şub–May 3 işlem +4,28R; May–Ağu 1 işlem −0,09R; Eylül ve 1 Ekim sıfır olay. İşlem sayısına göre kronolojik iki yarı: ilk5 işlem yalnız +0,06R, son6 işlem +11,06R; pozitiflik çok dengesiz.", "",
    f"Ham gün bootstrap'ı P(EV>0)=%{c['bootstrap']['p_positive']*100:.2f}, %95 EV aralığı [{c['bootstrap']['ci95'][0]:+.3f}, {c['bootstrap']['ci95'][1]:+.3f}]R. Bu küçük ve önceden seçilmiş örneklem için yeni bir başarı olasılığı veya kâr garantisi değildir. 150 olay eşiğinin çok altında.", "",
    "**Kâr yoğunlaşması:** 9 Nisan 2025 tek başına +6,08R. En iyi bir gün çıkarılınca +5,05R, en iyi üç gün çıkarılınca yalnız +0,28R, en iyi beş gün çıkarılınca **−1,35R** kalıyor. Stratejinin nadir büyük geri dönüşlere dayandığı açık; küçük örneklemde bunun devamlılığı bilinmiyor.", "",
    "**Çıkış geometrisi belirleyici:** aynı 11 olayda TP80/SL110 → **+1,07R, ortalama +0,097R**, bootstrap pozitif payı yalnız %62,75. Diğer rapordaki 14 olay/+0,33R ile aynı olay seti ve çıkış modeli değildir. Biz iki eksik önceki RTH günü (11 Mart ve 7 Nisan 2025) ile dondurulmuş bölmeler arasındaki 18 Mayıs 2026'yı kapsam dışı bıraktık; giriş/çıkış ve kayma tanımları da farklıdır. +1,011R'lik günlük-vol sonucu kısa stoplu mevcut bota taşınamaz.", "",
    f"Stop mesafesi bu örneklerde {c['risk_min_median_max'][0]:.0f}–{c['risk_min_median_max'][2]:.0f} fiyat puanı, medyan {c['risk_min_median_max'][1]:.0f}. R aynı başlangıç riskiyle normalize edilir; aynı lot kullanmak eşit parasal risk değildir. Bu rapor lot veya USD kâr önerisi üretmez.", "",
    "Kontroller: düşük VIX stres örnekleri 9 işlemde −1,94R; stressiz/yüksek VIX aynı olay 33 işlemde +3,35R (4 veri boşluğu içerir), yani bütün kontroller negatif değil. Aynı stres olayında SELL 11 işlemde −2,94R. Dip geri alımını bekleyen, aynı günlük-vol stoplu varyant 9 işlemde +5,80R; daha az ve farklı zamanda olay üretiyor. Bu gözlemler teyitsiz alım fikrini destekliyor, fakat nedensel üstünlük kanıtlamıyor.", "",
    "Diğer raporun 10 yıllık 1h, 30m ve 15m sonuçları değerli uzun dönem kanıtıdır; bu turda bunların tamamını yeniden üretmedim. Bunlar farklı zamanlarda giriş, kısmen farklı seans dibi ve çıkış tanımları içeriyor. Özellikle 1h seviyesinde 09:00–16:00 aralığı kullanılmış; 09:30 RTH dibiyle birebir aynı değil. Ayrıca 138 olay filtresiz seri, VIX filtresiyle raporlanan seri 108 olay: final kuralın örneklemine 138 yazılmamalı. Uzun dönem no-stop gvol getirisi ile stoplu R ölçüsü ayrı tutulmalı.", "",
    "## 4. Kovalama endeksi ve evren değişimi", "",
    "CHASE = SELL yönünde dört bileşenden en az üçü: M5/50-bar regresyon kanalında ≤−1σ, M15 aşağı hizalı, önceki RTH dibinin altında, günlük stres. Aynı beşli portföyde ΔR dönem sırasıyla **+2,72 / +0,09 / +0,01 / +0,84 / −3,35R**; toplam yalnız **+0,30R**. Gün eşleştirmeli pozitif katkı payı %51,45. Botta görülen monoton kötüleşme portföy kazancına güçlü biçimde taşınmadı.", "",
    f"K5b ile CHASE aynı kapı da değil. Stres+dip-altı yalnız iki puan eder; ≥3 eşiğine otomatik yetmez. Yeniden eşlenen bot kararlarında H1'in engellediği **{diagnostics['H1_not_in_chase']} karar** CHASE≥3 kapsamına girmiyor. Bu nedenle 'CHASE, K5b'yi içerir' ifadesi genel olarak doğru değil.", "",
    "## 5. Yeni gün, veri ve icra kalitesi", "",
    "- Ana protokol sabitlendikten sonra 1 Ekim tam seansı MT5'ten salt okunur alındı; broker saat ofseti +10800 saniye, point=0,1; önceki veriyle çakışma fiyat/saat kontrolleri geçti. Ek CAPREV denetimi yazılırken bu günün mumları zaten alınmıştı; CAPREV için dokunulmamış OOS sayılmadı.",
    "- 1 Ekim taban beşli: 8 işlem, **+3,12R**. H1–H4 aynı işlemleri bıraktı; yeni güne katkıları sıfır. Koşulsuz bekleme 6 işlem **−1,74R**. H5/CAPREV olay üretmedi. Tek gün filtre doğrulaması sağlamaz.",
    "- 30 Eylül önceden görülmüş ek gün: taban 5 işlem +1,12R. Bu turdaki sonuçlarla kural seçmek için kullanılmadı.",
    "- 2025 Dukascopy 306.635 M1; saat onarılmış cache+doğrudan MT5 228.396 M1. Önceki nakit günün tam RTH 390 mumu yoksa seans dibi kullanılmadı. Eksik yarım günler doldurulmadı.",
    "- **Yeni veri kusuru:** diğer klasörde 30 Eylül NDX kapanışı 30.556,29 ve VIX 15,91 idi; tamamlanmış günlük veriyle NDX **30.408,50**, VIX **16,34** olarak kendi araştırma kopyamda yeniledim. Önceki değerler tamamlanmış gün diye kullanılmamalı. Diğer ajanın dosyasını değiştirmedim.",
    "- Önceki cache Şubat–8 Mart saat düzeltmesi korundu. Makro ve M5/M15 özellikleri yalnız karar anına kadar kapanmış veriyi kullanır. Gelecek mumları değiştirme ve 1/3/5 dakika prefix kontrolleri geçti; CAPREV için ayrıca 1/5/15 dakika prefix ve 8 dolum/stop/boşluk fikstürü geçti.",
    "- Taban ve veto portföyleri aynı anda tek pozisyon, 10 dakika yeniden giriş aralığı ve sabit strateji önceliğiyle tekrar yürütüldü. Ana stratejiler 15:55'te, CAPREV16:00'da kapanır; bu iki ürünün tutma süreleri farklıdır.",
    "- Dukascopy gerçek bid/ask OHLC kullanılır. Doğrudan MT5 verisinde kayıtlı bar spreadinden ask türetilir. Eski cache bölümünde spread kaydı yok: **1,3 fiyat puanı varsayımı** kullanıldı; o döneme gerçek spread doğrulaması denemez. Yeni MT5 ihracındaki bar spreadleri 1,0 puan; tick düzeyindeki değişim ve gerçek fill/komisyon doğrulanmış değil. Komisyon ayrıca modellenmedi. Ana model her tarafta0,2 puan kayma; streslerde spread3, kayma1 ve gecikme1M1 kullanıldı. Finansman taşıması yok; bütün işlemler gün içi.",
    "- H2'nin şartı 2025 ham strateji fırsatlarının38'inde, 2026 fırsatlarının **hiçbirinde** oluştu. Dolayısıyla 2026'da sıfır katkı başarılı korunma değil, hareketsizliktir. Saat hacmi geçmişi 2025'te218, 2026'da461 ham fırsatta bilinmiyordu; eksik özellik veto üretmedi. Önceki tam RTH dibi de sırasıyla1.159/82 fırsatta yoktu; kapsam farkı raporlandı.",
    "- Toplam R ve bootstrap noktaları USD/kümülatif hesap kârı değildir. 2025/2026 aynı kuralların farklı sağlayıcı örnekleri; seçimin geçmiş tur yükü silinmedi.", "",
    "**Veri boşlukları önemli:** taban portföyde 53 çıkış veri boşluğuyla ilişkili. Bunların hepsini en az −1R sayınca toplam +57,12R → **−2,56R**. H1 portföyü +63,23R → **+3,55R**. Bu sınır gerçek gap dolumu tahmini değil, eksik veriye duyarlılık göstergesi. CAPREV'in raporlanan 11 olayında yürütme boşluğu yok; ancak eksik önceki seansı olan olaylar baştan dışarıda. Sağlayıcı kapsamı örnek seçimini etkileyebilir.", "",
    "## 6. Matematiksel yorumun sınırı", "",
    "Diğer rapordaki `μ ∝ σ²` sonucu, volatilite gruplarında fark görülmemesinden kanıtlanamaz. Sınırlı örneklem, rejim karışımı, değişken stop mesafesi veya düşük istatistiksel güç de aynı gözlemi üretebilir. Bu yüzden 'volatiliteye uyarlamaya gerek yok' sonucu kesin değil.", "",
    "Sabit sürüklenmeli modelde uygun durdurma koşulları altında brüt E[PNL]=μ·E[τ] yazılabilir; gerçek icrada maliyetler ayrıca çıkarılır. Sürüklenmesiz sürekli martingalde TP80/SL110'un teorik hedefe önce erişme olasılığı 110/(80+110)≈%57,89'dur; brüt beklenti yine sıfırdır. Yüksek kazanma oranı tek başına kenar değildir. Bu bilinen matematiğin uygulamasıdır; yeni bir Forex yasası keşfedildiği söylenemez.", "",
    "Çok sayıda strateji üzerinde aynı geçmişe dönerek seçim yapmanın aşırı uyum riski için [Bailey ve diğerlerinin birincil araştırması](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf); tick hacmi ile gerçek işlem hacminin ayrımı için [MetaQuotes MqlRates belgesi](https://www.mql5.com/en/docs/constants/structures/mqlrates) esas alındı. Burada hesaplanan bootstrap P değeri bu seçim geçmişinin olasılığını düzeltmez.", "",
    "## 7. Nihai karar ve sabit sonraki adım", "",
    "1. **CAPREV:** en öncelikli araştırma/SHADOW adayı. Günlük-vol stop +16:00 çıkışı ayrı ürün olarak dondurulsun; TP80/SL110 sonucuyla karıştırılmasın. Bu çalışma canlı ya da gölge çalışan süreç eklemedi.",
    "2. **H1/K5b:** ikinci sırada seçici SELL veto hipotezi. Gerçek bot sinyal niyeti evreninde, veto uygulanmadan alınacak ileriye dönük loglarla değerlendirilmesi gerekir. Sadece önceden gerçekleşen 41 işlemden kurtarılacak para hesaplanamaz.",
    "3. **CHASE:** bot örneklerine özel olabilir; portföy aktarımı kanıtlanmadı. H1'in yerine otomatik geçirilmemeli.",
    "4. **H2/H3/H4:** mevcut tanımlarla elendi. Yeni kombinasyon diye canlıya taşınmamalı. **H5:** düşük örneklem ve dönem kırılması nedeniyle terfi yok.",
    "5. CAPREV veya bir veto için canlı kararından önce ≥150 çözülmüş uygun olay, iki kronolojik yarı, pozitif net EV ve gün bootstrap'ı, en az1,5×spread stresi, next-M1-open/gerçek spread ve tek pozisyon kartı gerekir. Hacim eşiğine takılan adaya bu rapor LIVE kartı üretmedi. Tamamen yeni dönem, gerçek sinyal evreni ve gerçek dolum doğrulaması açık iş olarak kaldı.", "",
    "## 8. Görseller ve yeniden üretim", "", "![Karşılaştırma](results/comparison.png)", "", "![İlk kazanan ve ilk kaybeden örnek](results/trade_examples.png)", "",
    "Dosyalar: `PROTOCOL.md`, `PROTOCOL_ADDENDUM.md`, `run.py`, `caprev.py`, `verify.py`, `verify_caprev.py`, `results/evaluation.json`, `results/addendum.json`, `results/aggregate.json`, tüm işlem CSV'leri ve `results/provenance.json`. Rapor ve grafikler `make_report.py` ile bu çıktılardan üretilir.", "",
    "```bash", "python3 research/ndx_synthesis_20261002/run.py", "python3 research/ndx_synthesis_20261002/verify.py", "python3 research/ndx_synthesis_20261002/caprev.py", "python3 research/ndx_synthesis_20261002/verify_caprev.py", "python3 research/ndx_synthesis_20261002/make_report.py", "```", "",
    "Girdi alma betiği ayrıca ağ/MT5 erişimi ister; yeniden üretim sırasında dondurulmuş veri dosyaları korunmalıdır. Yeni veriyle yeniden koşmak eski raporu sessizce değiştirmemelidir."]
    (HERE / "NIHAI_RAPOR.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    files = [HERE / "PROTOCOL.md", HERE / "PROTOCOL_ADDENDUM.md", HERE / "run.py", HERE / "caprev.py", HERE / "verify.py", HERE / "verify_caprev.py", HERE / "make_report.py", HERE / "NIHAI_RAPOR.md",
             HERE.parent / "ndx_gate_forge/RAPOR.md", HERE.parent / "ndx_gate_forge/NIHAI_RAPOR.md",
             HERE.parent / "ndx_mechanism_round2_20260930/RAPOR.md"]
    files += [OUT / x for x in ["macro_daily.csv", "fresh_oct01.json", "evaluation.json", "addendum.json", "verification.json", "verification_caprev.json", "aggregate.json"]]
    lab.save_json(OUT / "provenance.json", {"created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
                                           "files": {str(p.relative_to(HERE.parents[1])): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                                           "code_change_after_initial_input": "Only added local overlap/OHLC assertions to run.py after the initial input export; rules unchanged.",
                                           "old_reports_are_references_not_instructions": True})
    print("REPORT", HERE / "NIHAI_RAPOR.md", flush=True)


if __name__ == "__main__":
    main()
