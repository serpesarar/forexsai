"""Render the research evidence into a Turkish report and static QA charts."""
from __future__ import annotations

import json
import os
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR","/private/tmp/ndx-five-gates-mpl")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import lab
from transfer import fresh

NAMES={"pullback":"Trendde geri çekilme teyidi","sweep":"Dip/tepe süpürmesi sonrası dönüş",
    "compression":"Sıkışma sonrası kırılım","absorption":"Büyük hareketin emilmesi",
    "exhaustion":"Aşırı hareketten dönüş","failed_break":"Başarısız kırılımın geri alınması",
    "efficient_pullback":"Verimli trendde geri çekilme","vwap_reclaim":"Seans VWAP geri alımı",
    "opening_break":"Açılış aralığı kırılımı","opening_failure":"Açılış aralığı başarısız kırılımı",
    "two_shock":"İkinci uç hareketten dönüş","midpoint_reclaim":"Sakin bant orta seviye kırılımı",
    "innovation_revert":"Beklenmeyen hareketten dönüş","variance_switch":"Varyans oranıyla rejim değişimi",
    "shock_continuation":"Beklenmeyen hareketin devamı"}
RULES={
    "pullback":"EMA20/EMA60 yönünde önce en az 0,5 ATR geri çekilme; sonra fiyat EMA20'yi yeniden geçer. Son beş dakikanın önceki hareketi ters yönde en az 0,5 ATR olmalıdır.",
    "sweep":"Önceki L dakikanın dip/tepesi mum içinde aşılır, kapanış yeniden aralığa girer; kapanış-konumu CLV yönünde >0,4, ters fitil mum aralığının >%35'i.",
    "compression":"Önceki L dakikalık aralık ATR70'e göre dar (L=15/30/60 için 5/7/10 ATR); ATR14/ATR70<1; kapanış aralığı dışarı kırar ve yönlü gövde/aralık >0,5.",
    "absorption":"Önceki mum aralığı L=15/30/60 için >1,8/2,2/2,6 ATR, yönlü gövdesi >0,6; takip mumu önceki gövdenin orta noktasını ters yönde geri alır.",
    "exhaustion":"Önceki kapanışın L mumluk fiyat z-skoru BUY için <−2, SELL için >2; son kapanış önceki mumun tepesini/dibini ters yönde geçer ve CLV yönünde >0,2.",
    "failed_break":"Önceki kapanış kendi önceki L dakikalık aralığının dışındadır; takip kapanışı aynı sınırı geri alır; yönlü CLV>0,2.",
    "efficient_pullback":"Önceki L dakikada yol-verimliliği ER>0,25 ve net hareket >1 ATR; önceki beş dakikada >0,3 ATR ters geri çekilme; son kapanış önceki mum tepe/dibini trend yönünde geçer.",
    "vwap_reclaim":"03:00 New York'tan itibaren tick-hacim ağırlıklı ortalama: önceki kapanış ortalamanın ters tarafında >0,3 ATR; son kapanış ortalamayı geri alır ve L dakikalık hareket yönle uyumludur. Tick hacmi borsa hacmi değildir.",
    "opening_break":"Tam 09:30–09:45 NY aralığı kapanınca, 09:45'ten itibaren 3L dakika içinde sınırın içeriden dışarı geçildiği kapanış; yönlü gövde/aralık >0,3. Bir günde sonraki yeniden geçişler de tek-pozisyon ve 10 dakika kısıtlarına tabidir.",
    "opening_failure":"Tam 09:30–09:45 NY aralığı bilindikten sonra, 3L dakika içinde sınır süpürülüp içeri kapanış; yönlü CLV>0,3.",
    "two_shock":"Önceki mum daha eski L dakikalık dip/tepeyi yeniler ve L dakikalık hareket >1 ATR; son mum önceki mum tepe/dibini ters yönde geri alır, yönlü gövde/aralık >0,2.",
    "midpoint_reclaim":"Önceki L dakikalık high/low orta seviyesi yönlü geçilir; L dakikalık net hareket >1 ATR, yönlü gövde/aralık >0,3.",
    "innovation_revert":"Kapalı geçmiş getirilerden AR(1) φ hesaplanır; önceki φ<−0,1 ve önceki normalize yenilik BUY için <−1,5 / SELL için >1,5; son kapanış önceki mum tepe/dibini ters yönde geçer; yönlü CLV>0,2.",
    "variance_switch":"VR>1,25 ise L dakikalık aralığın yönlü gövde>0,4 ile kırılması takip edilir; VR<0,75 ise sınır süpürülüp içeri kapanış (yönlü CLV>0,4) ters yönde alınır.",
    "shock_continuation":"Normalize AR(1) yeniliği yönünde >2, φ>0, yönlü gövde/aralık>0,5 ve yönlü CLV>0,5: beklenmeyen hareket takip edilir."}
CONTEXTS={"none":"ek bağlam yok","h1":"tam kapanmış H1 close/EMA50 yön hizası; H1 yaşı <2 saat",
    "efficiency":"60 dakikalık ER>0,20 ve net hareket yön hizası","quiet":"ATR14/ATR70<1"}


def val(x):return f"{x:+.3f}"
def pct(x):return f"%{100*x:.1f}"
def wilson(n,p):
    if n<=0:return (0.,1.)
    z=1.96;den=1+z*z/n;ctr=(p+z*z/(2*n))/den
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return (max(0.,ctr-half),min(1.,ctr+half))


def plot_examples(data,results):
    fig,axs=plt.subplots(5,2,figsize=(16,18),constrained_layout=True)
    for i,c in enumerate(results):
        spec=c["spec"]
        r=pd.read_csv(lab.OUT/f"second_trades_{spec['id']}.csv")
        for j,win in enumerate([True,False]):
            rows=r[r.R.gt(0) if win else r.R.le(0)]
            ax=axs[i,j]
            if rows.empty:
                ax.set_title("No eligible example");continue
            row=rows.iloc[0]
            w=data[(data.t>=row.decision-60*40)&(data.t<=row.exit_t+60*10)]
            times=pd.to_datetime(w.t,unit="s",utc=True).dt.tz_convert("America/New_York")
            ax.plot(times,w.close,color="#334155",linewidth=1)
            ax.vlines(times,w.low,w.high,color="#94a3b8",alpha=.25,linewidth=.6)
            entry=pd.Timestamp(row.entry_t,unit="s",tz="UTC").tz_convert("America/New_York")
            exit_t=pd.Timestamp(row.exit_t,unit="s",tz="UTC").tz_convert("America/New_York")
            ax.axvline(entry,color="#0284c7",linestyle="--",label="Entry / decision")
            ax.scatter([entry,exit_t],[row.entry,row.exit],color=["#0284c7","#16a34a" if win else "#dc2626"],zorder=4)
            rr={"fast":2.,"core":1.5,"slow":2.}[spec["geometry"]]
            ax.axhline(row.entry-row.side*row.risk,color="#dc2626",linestyle=":",label="SL")
            ax.axhline(row.entry+row.side*rr*row.risk,color="#16a34a",linestyle=":",label="TP")
            ax.axvspan(times.iloc[0],entry,color="#e2e8f0",alpha=.5)
            ax.set_title(f"Gate {i+1} | first {'winner' if win else 'loss'} | {row.R:+.2f} R | {'BUY' if row.side==1 else 'SELL'}")
            ax.tick_params(axis="x",rotation=30,labelsize=8)
            ax.grid(alpha=.15)
    fig.suptitle("September 2026 — descriptive examples; shaded area was available before entry",fontsize=14)
    fig.savefig(lab.OUT/"trade_examples.png",dpi=150)
    plt.close(fig)


def main():
    first=json.loads((lab.OUT/"final_evaluation.json").read_text())
    second=json.loads((lab.OUT/"second_final.json").read_text())
    frozen=json.loads((lab.OUT/"frozen_second_five.json").read_text())
    tr=json.loads((lab.OUT/"transfer_2025.json").read_text())
    names={c["spec"]["id"]:NAMES[c["spec"]["family"]] for c in second["candidates"]}
    lines=["# Nasdaq: beş aday kapı ve bağımsız dönem denetimi", "", "**Araştırma tarihi: 30 Eylül 2026. Sembol: NDX.INDX / NAS100; ek transfer kaynağı: Dukascopy US100.**", "",
        "Bu çalışma yeni giriş kaynakları arar. İlk turdaki 432 ve ikinci turdaki 1.620 değerlendirme açıkça kaydedildi (toplam 2.052 arama değerlendirmesi; bazı tanımlar iki turda tekrarlandı). Sonuçlar gerçekleşmiş bot kârı değildir. Canlı bot, kapılar, ayarlar ve emirler değiştirilmedi.","",
        "## Son karar", ""]
    passed=[c for c in second["candidates"] if c["final"]["ev"]>0 and c["matched_baseline"]["holm_p_five"]<.05 and all(m["ev"]>0 for m in c["timeframe_transfer"].values()) and all(m["ev"]>=0 for m in c["halves"].values())]
    lines += [f"Beş son adayın **{len(passed)} tanesi** Eylül'de hem pozitif R, hem iki yarıda istikrar, hem 3/5 dakikalık aktarım, hem de beş hipotez için düzeltilmiş taban-üstü seçim testini birlikte geçti. **Beş kanıtlanmış kâr kapısı bulunamadı.**", "",
        "Buna karşılık donmuş beşli kombinasyon, toplam tek pozisyonla Eylül'de **123 karar / +11,27R** verdi. İki Eylül yarısı ve ağır maliyet stresleri pozitif; fakat %95 güven aralığı sıfırı içeriyor, ön dönem maliyet stresinde işaret bozuluyor. Bu, sonraki dönemde gölgede ölçülebilecek **tek bir portföy hipotezidir**. Hiçbir aday LIVE olarak ilan edilmedi.","",
        "| # | Aday | Yön | Eylül karar | Eylül toplam R | EV/karar | 3m EV | 5m EV | Sonuç |",
        "|---|---|---|---:|---:|---:|---:|---:|---|"]
    for i,c in enumerate(second["candidates"],1):
        s,m=c["spec"],c["final"]
        label="Gölge adayı" if m["ev"]>0 else "Eylül'de elendi"
        if not s["eligible"]:label+="; seçim çıtası da geçilmedi"
        tf3=c['timeframe_transfer']['3'];tf5=c['timeframe_transfer']['5']
        lines.append(f"| {i} | {names[s['id']]} | {s['side'].upper()} | {m['n']} | {m['total_R']:+.2f} | {val(m['ev'])} | {val(tf3['ev']) if tf3['n'] else 'olay yok'} | {val(tf5['ev']) if tf5['n'] else 'olay yok'} | {label} |")
    lines += ["","**R**, her kararın başlangıç stop mesafesine göre normalize edilmiş getirisidir; 0,2 fiyat puanı/kapanış kayması da düşülür. Değişen stopta +R ve fiyat-puanı toplamı farklı işaret alabilir. Dolar/lot hesabı veya gelecekteki kazanç sözü üretilmedi.","",
        "## Veri, saat ve kronoloji","",
        "- İlk yerel önbellek: 195.285 M1 mum, 10 Şubat–28 Ağustos. İlk keşif 11 Şubat–15 Mayıs; erken dönem işlem fiyatları yaklaşık kabul edildi.",
        "- Eski doğrudan MT5: 100.000 M1 mum, 19 Mayıs–28 Ağustos. İlk doğrulama 20 Mayıs–30 Haziran; ilk son test 2 Temmuz–28 Ağustos.",
        "- İki eski kaynağın 99.611 ortak dakikasında ±5 puan uyum %97,02; sıfır kayma medyan fiyat farkı 0. ±120/180 dakika kaymaları medyan hatayı 55,8–70,5 puana çıkarıyor. Eski broker düzeltmesi ikinci kez uygulanmadı.",
        "- Dukascopy 2025: 306.635 M1 mum, 1 Ocak–30 Aralık; ticklerden türetilmiş gerçek bid ve ask OHLC. Ayrı sağlayıcı ve ayrı yıl; aynı sembolün işlem şartları birebir değildir. Spread gerçek sağlayıcı maliyetidir.",
        "- İlk beş kural 2025'e değiştirilmeden aktarıldı. Ardından ikinci tur seçiminde 2025 Ocak–Haziran, Temmuz–Aralık ve 2026 MT5 Mayıs–Ağustos kullanıldı. İkinci turda Temmuz–Ağustos artık seçim verisidir.",
        "- Eylül M1+spread verisi MT5'ten salt okunur çekildi. En az iki taze sembolün broker saat farkı 10.800 saniye; NAS100 `point=0.1` ve `digits=1` terminalden doğrulandı. Son test 1–29 Eylül; 30 Eylül sonuçlara katılmadı.",
        "- Taze çekimde 30.204 M1 mum var; son test aralığında 28.704. Eylül MT5 barlarının spread alanı **tamamında 10**, yani 1,0 fiyat puanı. Bu terminalin tarihsel kaydıdır; tick/fill maliyeti dağılımı ayrıca doğrulanmış değildir. Bu nedenle spread×1,5/3 ve 1 puan/fill kayma stresi raporlandı.",
        "- Eylül kuralları `frozen_second_five.json` içinde sonuç hesaplanmadan sabitlendi; dosya SHA256: `"+second["freeze_sha256"]+"`.",
        "- Panelin yeni önbelleğinde fiyat/hacim tutarsızlıkları gözlendi; Eylül testi o kaynakla yapılmadı. Eski tarihleri önceki proje araştırmaları kullanmıştır; bu çalışmanın ilk holdout'u bu taramaya ayrılmıştır, projenin hiç görmediği tarih olduğu iddia edilmez.","",
        "## Ortak yürütme ve matematik","",
        "Karar yalnız kapanmış mumlarla verilir; giriş tam sonraki M1 açılışıdır. NY 03:00–15:30, Pazartesi–Perşembe; son çıkış 15:55. Her stratejide ve birleşik portföyde aynı anda tek pozisyon, kararlar arasında en az 10 dakika. Bu ortak kısıt Cuma/Asya yasağını korur; bütün canlı kapılar yeniden üretilmiş değildir.","",
        "`ATR70` = M1 true-range'in Wilder ortalaması. FAST: stop=max(35,2×ATR70), hedef=2R, 15 dakika; CORE: max(35,5×ATR70), hedef=1,5R, 90 dakika; SLOW: max(35,8×ATR70), hedef=2R, 240 dakika. Her biri gün sonu sınırına tabidir.","",
        "`ER_L = |C_t−C_(t−L)| / Σ|ΔC|`. `CLV = (2C−H−L)/(H−L)`. AR(1): `φ=cov(r_t,r_(t−1))/var(r_(t−1))`, önceki katsayıyla `u_t=r_t−φ_(t−1)r_(t−1)`; yenilik önceki penceredeki standart sapma ile ölçeklenir. `VR=var(k-mum getirisi)/(k×var(1-mum getirisi))`. Bunlar standart istatistiksel araçlarla kurulmuş hipotezlerdir; yeni matematik keşfi iddia edilmez.","",
        "MT5 spread her dakikada gerçek kayıt; BUY ask'ten açılır, SELL ask'ten kapanır. 2025'te ask high/low da gerçek ticklerden gelir. Stop gap'inde daha kötü açılış fiyatı; aynı mumda belirsiz TP+SL varsa stop önce. Zaman stopu takip açılışında gerçekleşir. Beklenmeyen veri boşluğunda son gözlenen kapanışla işaretlenen sonuç ayrıca bütün boşlukları en az −1R sayan stresle gösterilir; bu çıkışlar gerçek fill değildir.","",
        "Komisyon=0 varsayımı eski yerel demo export'unun 284 işleminin tamamında komisyon=0 olmasıyla uyumludur; canlı hesabın ücret yapısı doğrulanmış değildir. Adaylar gün içinde kapandığından swap modellenmedi. 1/3/5m mumlar aynı piyasa yolunu kullanır; üç farklı zaman dilimi üç bağımsız örneklem değildir. Grafik equity'si çıkış dakikasının üst sınırında basamak olarak çizilir; mum içi fill zamanı bilinmez.","",
        "## Beş kapının kesin tanımı ve kanıtı",""]
    for i,c in enumerate(second["candidates"],1):
        s,m=c["spec"],c["final"];b=c["bootstrap"];base=c["matched_baseline"]
        wlo,whi=wilson(m['n'],m['wr'])
        lines += [f"### {i}. {names[s['id']]} — `{s['id']}`","",RULES[s["family"]],"",
            f"**Sabit ayar:** L={s['lookback']} dakika; yön={s['side']}; bağlam={CONTEXTS[s['context']]}; çıkış={s['geometry'].upper()}.","",
            f"**Eylül:** n={m['n']}, etkin gün={m['days']}, WR={pct(m['wr'])}, toplam={m['total_R']:+.2f}R, ortalama={val(m['ev'])}R, maksimum düşüş={m['drawdown_R']:.2f}R. Gün-bloklu %95 EV aralığı [{b['ci95'][0]:+.3f}, {b['ci95'][1]:+.3f}], bootstrap pozitif oranı={pct(b['p_positive'])}. Bu oran gelecekteki kâr olasılığı değildir.","",
            f"WR Wilson %95 aralığı [{pct(wlo)}, {pct(whi)}]. Wilson bağımsız Bernoulli karar varsayar; gün içi bağımlılık nedeniyle iyimser olabilir. Esas EV güven aralığı bütün günü yeniden örnekler.","",
            f"Aynı gün/saat/yön tabanı {val(base['baseline_ev'])}R; seçim farkı {val(base['lift_ev'])}R; tek-yönlü merkezlenmiş gün-blok testi p={base['one_sided_p']:.4f}, Holm(5) p={base['holm_p_five']:.4f}. Taban örtüşen varsayımsal kararlar içerir; uygulanabilir portföy kârı gibi toplanmaz.","",
            f"Gerçekleşen ortalama kazanç {m.get('average_win_R',0):.3f}R / kayıp {m.get('average_loss_R',0):.3f}R; bu çıkış karışımından hesaplanan betimsel başabaş WR {pct(m.get('empirical_breakeven_wr',0))}. Zaman çıkışları olduğu için sabit TP/SL başabaşıyla bütün WR karşılaştırılmaz.","",
            "| Seçim / son-test dönemi | n | EV R | Taban-üstü fark R |","|---|---:|---:|---:|"]
        for p,v in s["metrics"].items():lines.append(f"| {p} | {v['n']} | {val(v['ev'])} | {val(v['lift'])} |")
        for p,v in c["halves"].items():lines.append(f"| {p} (Eylül) | {v['n']} | {val(v['ev'])} | — |")
        lines += ["","| Maliyet / geometri / mum aktarımı | n | EV R |","|---|---:|---:|"]
        for p,v in c["stress"].items():lines.append(f"| {p} | {v['n']} | {val(v['ev'])} |")
        for p,v in c["timeframe_transfer"].items():lines.append(f"| {p} dakika mum | {v['n']} | {val(v['ev'])} |")
        if s['family']=='exhaustion' and s['lookback']==15:
            lines += ["","**Zaman dilimi sınırlaması:** 15 dakikalık pencere 3m'de 5, 5m'de 3 fiyat örneğine düşer. Örnek standart sapmasıyla kendi penceresine göre hesaplanan en büyük mutlak z değeri `(n−1)/√n` olduğundan her iki pencerede `|z|>2` mümkün değildir. Dolayısıyla burada 0 olay çıktı; bu kapı 3m/5m'de doğrulanmış sayılmaz. Eylül görüldükten sonra eşiği değiştirip yeni sonucu bağımsız test diye sunmadım."]
        lines += ["",f"Altı ölçüt: `{c['go_live_checks']}`. Bar kartı tamamı={c['bar_card_passes']}; hacim/kart durumu={c['verdict']}. LIVE yetkisi çıkarılmaz. Seçim ön-ölçütlerini geçti={s['eligible']}.",""]
    lines += ["## İlk turun başarısızlıkları da kayıtlı","",
        "İlk beş, dört keşif/doğrulama alt döneminde pozitifti. Sonraki dönem ve ayrı yıl testinde sonuçlar:","",
        "| İlk aday | Keşif EV | Mayıs/Haziran EV | Temmuz/Ağustos EV | 2025 M1 EV |","|---|---:|---:|---:|---:|"]
    for c in first["candidates"]:
        s=c["spec"];v=next(v for v in tr if v["spec"]==s["id"] and v["timeframe"]==1)
        lines.append(f"| {s['id']} | {val(s['metrics']['discovery']['ev'])} | {val(s['metrics']['validation']['ev'])} | {val(c['final']['ev'])} | {val(v['stats']['ev'])} |")
    september=json.loads((lab.OUT/'transfer_september.json').read_text())
    lines += ["","İlk beş ayrıca yeni Eylül verisinde tanımları değişmeden denendi:","","| İlk aday | Eylül M1 n / EV | Eylül 3m n / EV | Eylül 5m n / EV |","|---|---|---|---|"]
    for c in first['candidates']:
        entries={v['timeframe']:v['stats'] for v in september if v['spec']==c['spec']['id']}
        cells=[f"{entries[tf]['n']} / {val(entries[tf]['ev'])}" for tf in [1,3,5]]
        lines.append(f"| {c['spec']['id']} | {' | '.join(cells)} |")
    lines += ["","Sakin bant orta seviye SELL ve verimli geri çekilme bu ek Eylül testinde 1/3/5m'de pozitif çıktı. Ancak 2025 aktarımı negatif; ilkinde Temmuz/Ağustos taban-üstü seçim avantajı yok, ikincisi ilk masraf stresinde işaret kaybetmişti. Bu sonuca bakarak ilk beşten yeni bir en-iyi-altküme seçilmedi."]
    p=second["portfolio"]
    lines += ["","İlk beşin Temmuz/Ağustos tek-pozisyon birleşimi +2,57R, maksimum düşüş 23,91R ve bootstrap pozitif oranı %56,05: uygulanabilir kâr kanıtı vermedi. Aynı dönem kuralları değiştirip yeniden holdout diye sunulmadı.","",
        "## Birleşik portföy ve pratik karar","",
        f"İkinci beş, seçim sıralaması değişmeden tek toplam pozisyonla: n={p['n']}, toplam={p['total_R']:+.2f}R, EV={val(p['ev'])}R, düşüş={p['drawdown_R']:.2f}R, gün-blok %95 aralık={p['bootstrap']['ci95']}, bootstrap pozitif oranı={pct(p['bootstrap']['p_positive'])}. Aday sonuçlarını birbirine eklemek bu portföyü üretmez; çakışan fırsatlar elenir.","",
        "Bu kapılar barlardan tanımlanan yeni giriş kaynaklarıdır. Botun VIXREG/MOM/CHREV akışına uygulanınca ek para kazandırdıkları bu replay ile kanıtlanmış olmaz. Bunun için aynı fırsatta orijinal karar, yeni karar, ret sebebi ve gerçek sonraki tick fill maliyeti eş zamanlı gölgede kaydedilmelidir.","",
        "Canlı terfi için: donmuş kural, daha sonraki hiç kullanılmamış dönem; ≥150 bağımsız çözümlenmiş karar; pozitif EV ve gün-blok güveni; iki zaman yarısı; masraf stresi; gerçek spread/fill; tek toplam pozisyon. Beş kuralı seçip ardından Eylül'ün iyi alt kümelerini yeniden seçmek yeni bir arama olur ve yeni son test gerektirir.","",
        "## Doğrulama ve tekrar üretim","",
        "- 7 elle kurulmuş bid/ask, aynı-mum, adverse gap, zaman-stop ve eksik-dakika yürütme örneği geçti.",
        "- İlk 432 tanım × 1/3/5m için gelecek veriler kaldırıldığında önceki özellikler ve kararlar birebir aynı kaldı.",
        "- İkinci turun AR/VR özelliklerinde 1/3/5m prefix nedensellik ve gerçek ask/high kontrolü ayrıca yapıldı.",
        "- Protokoller, tüm aday taramaları, donmuş seçimler, işlem CSV'leri ve veri kaynağı hash'leri bu klasördedir. Büyük ham veri tekrar üretilebilir yerel artefakttır.","",
        "```bash","python3 research/ndx_five_gates_20260930/lab.py discover","python3 research/ndx_five_gates_20260930/lab.py evaluate",
        "python3 research/ndx_five_gates_20260930/transfer.py 2025","python3 research/ndx_five_gates_20260930/second_search.py search",
        "python3 research/ndx_five_gates_20260930/second_search.py evaluate","python3 research/ndx_five_gates_20260930/verify.py",
        "python3 research/ndx_five_gates_20260930/verify_second.py","python3 research/ndx_five_gates_20260930/make_report.py","```","",
        "Yeniden `search` çalıştırmak yeni arama sayılmaz ancak donmuş artefaktları yeniden yazar; yeni dönem için önce yeni protokol oluşturun. MT5 uzaktan okuma betiği emir/ayar/dosya yazmaz; köprüde normal komut kuyruğu kaydı oluşturur.","",
        "Çoklu aramanın aşırı uyuma yol açabileceği metodolojik dayanak: [Bailey ve diğerleri, The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf). Buradaki seçim ve test ayrımı bu riski azaltmak içindir; bu çalışmada PBO/CSCV hesaplandığı iddia edilmez.","",
        "## Grafikler","","`results/equity.png`: bağımsız Eylül equity. `results/trade_examples.png`: her adayın tarih sırasındaki ilk kazananı ve ilk kaybedeni; girişten sonra görülen mumlar yalnız betimleyicidir, giriş kararına katılmaz.",""]
    pp=lab.OUT/'portfolio_validation.json'
    if pp.exists():
        pv=json.loads(pp.read_text())
        lines += ["## Donmuş portföyün ek stres denetimi","","| Dönem / stres | n | EV R | Toplam R |","|---|---:|---:|---:|"]
        for key,v in pv.items():lines.append(f"| {key} | {v['n']} | {val(v['ev'])} | {v['total_R']:+.2f} |")
        lines += ["","Bu tabloda portföy sıralaması ve kurallar sabittir. 2025 ve Ağustos öncesi dönemler seçim verisidir; yalnız Eylül son testtir. Masraf senaryolarının aynı ham veri üzerinde tekrar hesaplanması yeni bağımsız örneklem değildir.","",
            "**Portföyün geçemediği noktalar:** Eylül n=123 (<150); gün-blok bootstrap pozitif oranı %87,96 (<%90) ve %95 EV aralığı [−0,065,+0,244]R. 2026 Mayıs–Ağustos EV +0,004R iken spread×1,5 ile yaklaşık sıfıra/negatife düşüyor; 1 puan/fill kaymada −0,010R. 2025 iki yarısında veri boşluklarını en az −1R sayınca EV negatif. Bu nedenle pozitif manşet tek başına canlıya terfi sağlamaz.",""]
    (lab.HERE/"RAPOR.md").write_text("\n".join(lines),encoding="utf-8")
    fig,ax=plt.subplots(figsize=(12,6),constrained_layout=True)
    for i,c in enumerate(second["candidates"],1):
        r=pd.read_csv(lab.OUT/f"second_trades_{c['spec']['id']}.csv")
        tt=np.r_[r.decision.iloc[0]-60,r.exit_t.to_numpy()]
        ax.step(pd.to_datetime(tt,unit="s",utc=True),np.r_[0.,r.R.cumsum()],where='post',label=f"{i}. {c['spec']['family']}")
    p=pd.read_csv(lab.OUT/"second_portfolio_trades.csv")
    tt=np.r_[p.decision.iloc[0]-60,p.exit_t.to_numpy()]
    ax.step(pd.to_datetime(tt,unit="s",utc=True),np.r_[0.,p.R.cumsum()],where='post',color="black",linewidth=2,label="One-position portfolio")
    ax.axhline(0,color="gray",linewidth=.7);ax.set_ylabel("Cumulative net R");ax.set_title("Frozen candidates — direct MT5, September 1–29, 2026")
    locator=mdates.AutoDateLocator(minticks=5,maxticks=9)
    ax.xaxis.set_major_locator(locator);ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    ax.legend(fontsize=8);ax.grid(alpha=.2);fig.savefig(lab.OUT/"equity.png",dpi=160);plt.close(fig)
    plot_examples(fresh(),second["candidates"])
    print("Report and charts saved",lab.HERE/"RAPOR.md",flush=True)


if __name__=="__main__":main()
