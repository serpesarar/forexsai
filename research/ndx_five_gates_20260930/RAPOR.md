# Nasdaq: beş aday kapı ve bağımsız dönem denetimi

> **1 Ekim 2026 saat denetimi eki:** cache’in 8 Mart öncesi M1 etiketleri 60 dakika erken. Ayrı H1 kaynağıyla doğrulandı; bu ilk erken keşif/sıralamasını etkiler. Mayıs sonrası MT5, 2025 Dukascopy ve Eylül sonuçları etkilenmez. Beş ilk kuralın düzeltilmiş erken dönem karşılaştırması ve yeni türevler [devam raporunda](../ndx_mechanism_round2_20260930/RAPOR.md). İlk 432 adayın tamamı düzeltilmiş saatle yeniden sıralanmadı; eski keşif sırasının aynı kaldığı iddia edilmez.


**Araştırma tarihi: 30 Eylül 2026. Sembol: NDX.INDX / NAS100; ek transfer kaynağı: Dukascopy US100.**

Bu çalışma yeni giriş kaynakları arar. İlk turdaki 432 ve ikinci turdaki 1.620 değerlendirme açıkça kaydedildi (toplam 2.052 arama değerlendirmesi; bazı tanımlar iki turda tekrarlandı). Sonuçlar gerçekleşmiş bot kârı değildir. Canlı bot, kapılar, ayarlar ve emirler değiştirilmedi.

## Son karar

Beş son adayın **0 tanesi** Eylül'de hem pozitif R, hem iki yarıda istikrar, hem 3/5 dakikalık aktarım, hem de beş hipotez için düzeltilmiş taban-üstü seçim testini birlikte geçti. **Beş kanıtlanmış kâr kapısı bulunamadı.**

Buna karşılık donmuş beşli kombinasyon, toplam tek pozisyonla Eylül'de **123 karar / +11,27R** verdi. İki Eylül yarısı ve ağır maliyet stresleri pozitif; fakat %95 güven aralığı sıfırı içeriyor, ön dönem maliyet stresinde işaret bozuluyor. Bu, sonraki dönemde gölgede ölçülebilecek **tek bir portföy hipotezidir**. Hiçbir aday LIVE olarak ilan edilmedi.

| # | Aday | Yön | Eylül karar | Eylül toplam R | EV/karar | 3m EV | 5m EV | Sonuç |
|---|---|---|---:|---:|---:|---:|---:|---|
| 1 | Açılış aralığı kırılımı | BOTH | 13 | -0.89 | -0.068 | -0.295 | -0.181 | Eylül'de elendi |
| 2 | Aşırı hareketten dönüş | SELL | 38 | +2.30 | +0.060 | olay yok | olay yok | Gölge adayı; seçim çıtası da geçilmedi |
| 3 | Dip/tepe süpürmesi sonrası dönüş | SELL | 59 | +0.23 | +0.004 | -0.084 | -0.012 | Gölge adayı; seçim çıtası da geçilmedi |
| 4 | Varyans oranıyla rejim değişimi | BOTH | 72 | -8.13 | -0.113 | +0.046 | -0.013 | Eylül'de elendi; seçim çıtası da geçilmedi |
| 5 | Başarısız kırılımın geri alınması | BUY | 81 | -2.63 | -0.032 | -0.112 | -0.026 | Eylül'de elendi; seçim çıtası da geçilmedi |

**R**, her kararın başlangıç stop mesafesine göre normalize edilmiş getirisidir; 0,2 fiyat puanı/kapanış kayması da düşülür. Değişen stopta +R ve fiyat-puanı toplamı farklı işaret alabilir. Dolar/lot hesabı veya gelecekteki kazanç sözü üretilmedi.

## Veri, saat ve kronoloji

- İlk yerel önbellek: 195.285 M1 mum, 10 Şubat–28 Ağustos. İlk keşif 11 Şubat–15 Mayıs; erken dönem işlem fiyatları yaklaşık kabul edildi.
- Eski doğrudan MT5: 100.000 M1 mum, 19 Mayıs–28 Ağustos. İlk doğrulama 20 Mayıs–30 Haziran; ilk son test 2 Temmuz–28 Ağustos.
- İki eski kaynağın 99.611 ortak dakikasında ±5 puan uyum %97,02; sıfır kayma medyan fiyat farkı 0. ±120/180 dakika kaymaları medyan hatayı 55,8–70,5 puana çıkarıyor. Eski broker düzeltmesi ikinci kez uygulanmadı.
- Dukascopy 2025: 306.635 M1 mum, 1 Ocak–30 Aralık; ticklerden türetilmiş gerçek bid ve ask OHLC. Ayrı sağlayıcı ve ayrı yıl; aynı sembolün işlem şartları birebir değildir. Spread gerçek sağlayıcı maliyetidir.
- İlk beş kural 2025'e değiştirilmeden aktarıldı. Ardından ikinci tur seçiminde 2025 Ocak–Haziran, Temmuz–Aralık ve 2026 MT5 Mayıs–Ağustos kullanıldı. İkinci turda Temmuz–Ağustos artık seçim verisidir.
- Eylül M1+spread verisi MT5'ten salt okunur çekildi. En az iki taze sembolün broker saat farkı 10.800 saniye; NAS100 `point=0.1` ve `digits=1` terminalden doğrulandı. Son test 1–29 Eylül; 30 Eylül sonuçlara katılmadı.
- Taze çekimde 30.204 M1 mum var; son test aralığında 28.704. Eylül MT5 barlarının spread alanı **tamamında 10**, yani 1,0 fiyat puanı. Bu terminalin tarihsel kaydıdır; tick/fill maliyeti dağılımı ayrıca doğrulanmış değildir. Bu nedenle spread×1,5/3 ve 1 puan/fill kayma stresi raporlandı.
- Eylül kuralları `frozen_second_five.json` içinde sonuç hesaplanmadan sabitlendi; dosya SHA256: `14dd08aab5a3c78fda60859790087c3ad505e4f90f9518d2936a5159e6665766`.
- Panelin yeni önbelleğinde fiyat/hacim tutarsızlıkları gözlendi; Eylül testi o kaynakla yapılmadı. Eski tarihleri önceki proje araştırmaları kullanmıştır; bu çalışmanın ilk holdout'u bu taramaya ayrılmıştır, projenin hiç görmediği tarih olduğu iddia edilmez.

## Ortak yürütme ve matematik

Karar yalnız kapanmış mumlarla verilir; giriş tam sonraki M1 açılışıdır. NY 03:00–15:30, Pazartesi–Perşembe; son çıkış 15:55. Her stratejide ve birleşik portföyde aynı anda tek pozisyon, kararlar arasında en az 10 dakika. Bu ortak kısıt Cuma/Asya yasağını korur; bütün canlı kapılar yeniden üretilmiş değildir.

`ATR70` = M1 true-range'in Wilder ortalaması. FAST: stop=max(35,2×ATR70), hedef=2R, 15 dakika; CORE: max(35,5×ATR70), hedef=1,5R, 90 dakika; SLOW: max(35,8×ATR70), hedef=2R, 240 dakika. Her biri gün sonu sınırına tabidir.

`ER_L = |C_t−C_(t−L)| / Σ|ΔC|`. `CLV = (2C−H−L)/(H−L)`. AR(1): `φ=cov(r_t,r_(t−1))/var(r_(t−1))`, önceki katsayıyla `u_t=r_t−φ_(t−1)r_(t−1)`; yenilik önceki penceredeki standart sapma ile ölçeklenir. `VR=var(k-mum getirisi)/(k×var(1-mum getirisi))`. Bunlar standart istatistiksel araçlarla kurulmuş hipotezlerdir; yeni matematik keşfi iddia edilmez.

MT5 spread her dakikada gerçek kayıt; BUY ask'ten açılır, SELL ask'ten kapanır. 2025'te ask high/low da gerçek ticklerden gelir. Stop gap'inde daha kötü açılış fiyatı; aynı mumda belirsiz TP+SL varsa stop önce. Zaman stopu takip açılışında gerçekleşir. Beklenmeyen veri boşluğunda son gözlenen kapanışla işaretlenen sonuç ayrıca bütün boşlukları en az −1R sayan stresle gösterilir; bu çıkışlar gerçek fill değildir.

Komisyon=0 varsayımı eski yerel demo export'unun 284 işleminin tamamında komisyon=0 olmasıyla uyumludur; canlı hesabın ücret yapısı doğrulanmış değildir. Adaylar gün içinde kapandığından swap modellenmedi. 1/3/5m mumlar aynı piyasa yolunu kullanır; üç farklı zaman dilimi üç bağımsız örneklem değildir. Grafik equity'si çıkış dakikasının üst sınırında basamak olarak çizilir; mum içi fill zamanı bilinmez.

## Beş kapının kesin tanımı ve kanıtı

### 1. Açılış aralığı kırılımı — `opening_break_60_quiet_both_fast`

Tam 09:30–09:45 NY aralığı kapanınca, 09:45'ten itibaren 3L dakika içinde sınırın içeriden dışarı geçildiği kapanış; yönlü gövde/aralık >0,3. Bir günde sonraki yeniden geçişler de tek-pozisyon ve 10 dakika kısıtlarına tabidir.

**Sabit ayar:** L=60 dakika; yön=both; bağlam=ATR14/ATR70<1; çıkış=FAST.

**Eylül:** n=13, etkin gün=7, WR=%38.5, toplam=-0.89R, ortalama=-0.068R, maksimum düşüş=3.00R. Gün-bloklu %95 EV aralığı [-0.292, +0.385], bootstrap pozitif oranı=%33.5. Bu oran gelecekteki kâr olasılığı değildir.

WR Wilson %95 aralığı [%17.7, %64.5]. Wilson bağımsız Bernoulli karar varsayar; gün içi bağımlılık nedeniyle iyimser olabilir. Esas EV güven aralığı bütün günü yeniden örnekler.

Aynı gün/saat/yön tabanı +0.039R; seçim farkı -0.108R; tek-yönlü merkezlenmiş gün-blok testi p=0.7833, Holm(5) p=0.7833. Taban örtüşen varsayımsal kararlar içerir; uygulanabilir portföy kârı gibi toplanmaz.

Gerçekleşen ortalama kazanç 0.577R / kayıp 0.471R; bu çıkış karışımından hesaplanan betimsel başabaş WR %45.0. Zaman çıkışları olduğu için sabit TP/SL başabaşıyla bütün WR karşılaştırılmaz.

| Seçim / son-test dönemi | n | EV R | Taban-üstü fark R |
|---|---:|---:|---:|
| year_a | 62 | +0.069 | +0.017 |
| year_b | 55 | +0.038 | +0.071 |
| mt5_presep | 61 | +0.079 | +0.096 |
| final_a (Eylül) | 6 | +0.171 | — |
| final_b (Eylül) | 7 | -0.273 | — |

| Maliyet / geometri / mum aktarımı | n | EV R |
|---|---:|---:|
| spread_1_5 | 13 | -0.080 |
| spread_3 | 13 | -0.214 |
| slip_1 | 13 | -0.110 |
| delay_1m | 12 | -0.082 |
| fixed_80_110 | 13 | -0.024 |
| symmetric | 13 | -0.102 |
| optimistic_close | 13 | -0.034 |
| 3 dakika mum | 10 | -0.295 |
| 5 dakika mum | 9 | -0.181 |

Altı ölçüt: `{'volume_150': False, 'positive_ev_day_bootstrap_90': False, 'both_calendar_halves': False, 'spread_1_5': False, 'honest_vs_close_entry': True, 'one_position': False}`. Bar kartı tamamı=False; hacim/kart durumu=RED. LIVE yetkisi çıkarılmaz. Seçim ön-ölçütlerini geçti=True.

### 2. Aşırı hareketten dönüş — `exhaustion_15_none_sell_core`

Önceki kapanışın L mumluk fiyat z-skoru BUY için <−2, SELL için >2; son kapanış önceki mumun tepesini/dibini ters yönde geçer ve CLV yönünde >0,2.

**Sabit ayar:** L=15 dakika; yön=sell; bağlam=ek bağlam yok; çıkış=CORE.

**Eylül:** n=38, etkin gün=17, WR=%52.6, toplam=+2.30R, ortalama=+0.060R, maksimum düşüş=4.23R. Gün-bloklu %95 EV aralığı [-0.240, +0.391], bootstrap pozitif oranı=%64.9. Bu oran gelecekteki kâr olasılığı değildir.

WR Wilson %95 aralığı [%37.3, %67.5]. Wilson bağımsız Bernoulli karar varsayar; gün içi bağımlılık nedeniyle iyimser olabilir. Esas EV güven aralığı bütün günü yeniden örnekler.

Aynı gün/saat/yön tabanı -0.133R; seçim farkı +0.193R; tek-yönlü merkezlenmiş gün-blok testi p=0.0163, Holm(5) p=0.0489. Taban örtüşen varsayımsal kararlar içerir; uygulanabilir portföy kârı gibi toplanmaz.

Gerçekleşen ortalama kazanç 0.983R / kayıp 0.964R; bu çıkış karışımından hesaplanan betimsel başabaş WR %49.5. Zaman çıkışları olduğu için sabit TP/SL başabaşıyla bütün WR karşılaştırılmaz.

| Seçim / son-test dönemi | n | EV R | Taban-üstü fark R |
|---|---:|---:|---:|
| year_a | 185 | +0.078 | +0.139 |
| year_b | 182 | +0.024 | +0.112 |
| mt5_presep | 98 | +0.126 | +0.171 |
| final_a (Eylül) | 17 | +0.310 | — |
| final_b (Eylül) | 21 | -0.142 | — |

| Maliyet / geometri / mum aktarımı | n | EV R |
|---|---:|---:|
| spread_1_5 | 38 | +0.058 |
| spread_3 | 38 | +0.049 |
| slip_1 | 38 | +0.039 |
| delay_1m | 39 | +0.123 |
| fixed_80_110 | 34 | +0.049 |
| symmetric | 38 | -0.040 |
| optimistic_close | 37 | +0.149 |
| 3 dakika mum | 0 | +0.000 |
| 5 dakika mum | 0 | +0.000 |

**Zaman dilimi sınırlaması:** 15 dakikalık pencere 3m'de 5, 5m'de 3 fiyat örneğine düşer. Örnek standart sapmasıyla kendi penceresine göre hesaplanan en büyük mutlak z değeri `(n−1)/√n` olduğundan her iki pencerede `|z|>2` mümkün değildir. Dolayısıyla burada 0 olay çıktı; bu kapı 3m/5m'de doğrulanmış sayılmaz. Eylül görüldükten sonra eşiği değiştirip yeni sonucu bağımsız test diye sunmadım.

Altı ölçüt: `{'volume_150': False, 'positive_ev_day_bootstrap_90': False, 'both_calendar_halves': False, 'spread_1_5': True, 'honest_vs_close_entry': False, 'one_position': True}`. Bar kartı tamamı=False; hacim/kart durumu=RED. LIVE yetkisi çıkarılmaz. Seçim ön-ölçütlerini geçti=False.

### 3. Dip/tepe süpürmesi sonrası dönüş — `sweep_30_none_sell_slow`

Önceki L dakikanın dip/tepesi mum içinde aşılır, kapanış yeniden aralığa girer; kapanış-konumu CLV yönünde >0,4, ters fitil mum aralığının >%35'i.

**Sabit ayar:** L=30 dakika; yön=sell; bağlam=ek bağlam yok; çıkış=SLOW.

**Eylül:** n=59, etkin gün=17, WR=%44.1, toplam=+0.23R, ortalama=+0.004R, maksimum düşüş=11.26R. Gün-bloklu %95 EV aralığı [-0.339, +0.382], bootstrap pozitif oranı=%50.3. Bu oran gelecekteki kâr olasılığı değildir.

WR Wilson %95 aralığı [%32.2, %56.7]. Wilson bağımsız Bernoulli karar varsayar; gün içi bağımlılık nedeniyle iyimser olabilir. Esas EV güven aralığı bütün günü yeniden örnekler.

Aynı gün/saat/yön tabanı -0.146R; seçim farkı +0.150R; tek-yönlü merkezlenmiş gün-blok testi p=0.0111, Holm(5) p=0.0444. Taban örtüşen varsayımsal kararlar içerir; uygulanabilir portföy kârı gibi toplanmaz.

Gerçekleşen ortalama kazanç 1.114R / kayıp 0.870R; bu çıkış karışımından hesaplanan betimsel başabaş WR %43.9. Zaman çıkışları olduğu için sabit TP/SL başabaşıyla bütün WR karşılaştırılmaz.

| Seçim / son-test dönemi | n | EV R | Taban-üstü fark R |
|---|---:|---:|---:|
| year_a | 372 | +0.017 | +0.143 |
| year_b | 329 | +0.028 | +0.169 |
| mt5_presep | 202 | +0.010 | +0.167 |
| final_a (Eylül) | 27 | +0.274 | — |
| final_b (Eylül) | 32 | -0.224 | — |

| Maliyet / geometri / mum aktarımı | n | EV R |
|---|---:|---:|
| spread_1_5 | 59 | +0.002 |
| spread_3 | 60 | -0.038 |
| slip_1 | 60 | -0.026 |
| delay_1m | 61 | -0.093 |
| fixed_80_110 | 65 | -0.112 |
| symmetric | 67 | -0.084 |
| optimistic_close | 59 | +0.021 |
| 3 dakika mum | 51 | -0.084 |
| 5 dakika mum | 45 | -0.012 |

Altı ölçüt: `{'volume_150': False, 'positive_ev_day_bootstrap_90': False, 'both_calendar_halves': False, 'spread_1_5': True, 'honest_vs_close_entry': False, 'one_position': True}`. Bar kartı tamamı=False; hacim/kart durumu=RED. LIVE yetkisi çıkarılmaz. Seçim ön-ölçütlerini geçti=False.

### 4. Varyans oranıyla rejim değişimi — `variance_switch_30_quiet_both_core`

VR>1,25 ise L dakikalık aralığın yönlü gövde>0,4 ile kırılması takip edilir; VR<0,75 ise sınır süpürülüp içeri kapanış (yönlü CLV>0,4) ters yönde alınır.

**Sabit ayar:** L=30 dakika; yön=both; bağlam=ATR14/ATR70<1; çıkış=CORE.

**Eylül:** n=72, etkin gün=17, WR=%38.9, toplam=-8.13R, ortalama=-0.113R, maksimum düşüş=10.82R. Gün-bloklu %95 EV aralığı [-0.342, +0.114], bootstrap pozitif oranı=%16.0. Bu oran gelecekteki kâr olasılığı değildir.

WR Wilson %95 aralığı [%28.5, %50.4]. Wilson bağımsız Bernoulli karar varsayar; gün içi bağımlılık nedeniyle iyimser olabilir. Esas EV güven aralığı bütün günü yeniden örnekler.

Aynı gün/saat/yön tabanı -0.131R; seçim farkı +0.018R; tek-yönlü merkezlenmiş gün-blok testi p=0.3762, Holm(5) p=0.7523. Taban örtüşen varsayımsal kararlar içerir; uygulanabilir portföy kârı gibi toplanmaz.

Gerçekleşen ortalama kazanç 0.862R / kayıp 0.733R; bu çıkış karışımından hesaplanan betimsel başabaş WR %46.0. Zaman çıkışları olduğu için sabit TP/SL başabaşıyla bütün WR karşılaştırılmaz.

| Seçim / son-test dönemi | n | EV R | Taban-üstü fark R |
|---|---:|---:|---:|
| year_a | 402 | -0.010 | +0.048 |
| year_b | 375 | -0.005 | +0.077 |
| mt5_presep | 262 | -0.000 | +0.071 |
| final_a (Eylül) | 36 | -0.142 | — |
| final_b (Eylül) | 36 | -0.084 | — |

| Maliyet / geometri / mum aktarımı | n | EV R |
|---|---:|---:|
| spread_1_5 | 71 | -0.140 |
| spread_3 | 72 | -0.157 |
| slip_1 | 71 | -0.186 |
| delay_1m | 71 | -0.105 |
| fixed_80_110 | 66 | -0.038 |
| symmetric | 74 | -0.092 |
| optimistic_close | 72 | -0.100 |
| 3 dakika mum | 58 | +0.046 |
| 5 dakika mum | 61 | -0.013 |

Altı ölçüt: `{'volume_150': False, 'positive_ev_day_bootstrap_90': False, 'both_calendar_halves': False, 'spread_1_5': False, 'honest_vs_close_entry': True, 'one_position': False}`. Bar kartı tamamı=False; hacim/kart durumu=RED. LIVE yetkisi çıkarılmaz. Seçim ön-ölçütlerini geçti=False.

### 5. Başarısız kırılımın geri alınması — `failed_break_60_none_buy_fast`

Önceki kapanış kendi önceki L dakikalık aralığının dışındadır; takip kapanışı aynı sınırı geri alır; yönlü CLV>0,2.

**Sabit ayar:** L=60 dakika; yön=buy; bağlam=ek bağlam yok; çıkış=FAST.

**Eylül:** n=81, etkin gün=17, WR=%42.0, toplam=-2.63R, ortalama=-0.032R, maksimum düşüş=5.41R. Gün-bloklu %95 EV aralığı [-0.178, +0.134], bootstrap pozitif oranı=%34.5. Bu oran gelecekteki kâr olasılığı değildir.

WR Wilson %95 aralığı [%31.8, %52.8]. Wilson bağımsız Bernoulli karar varsayar; gün içi bağımlılık nedeniyle iyimser olabilir. Esas EV güven aralığı bütün günü yeniden örnekler.

Aynı gün/saat/yön tabanı -0.235R; seçim farkı +0.202R; tek-yönlü merkezlenmiş gün-blok testi p=0.0037, Holm(5) p=0.0185. Taban örtüşen varsayımsal kararlar içerir; uygulanabilir portföy kârı gibi toplanmaz.

Gerçekleşen ortalama kazanç 0.855R / kayıp 0.674R; bu çıkış karışımından hesaplanan betimsel başabaş WR %44.1. Zaman çıkışları olduğu için sabit TP/SL başabaşıyla bütün WR karşılaştırılmaz.

| Seçim / son-test dönemi | n | EV R | Taban-üstü fark R |
|---|---:|---:|---:|
| year_a | 469 | -0.015 | +0.277 |
| year_b | 432 | -0.013 | +0.220 |
| mt5_presep | 308 | -0.010 | +0.238 |
| final_a (Eylül) | 51 | -0.030 | — |
| final_b (Eylül) | 30 | -0.037 | — |

| Maliyet / geometri / mum aktarımı | n | EV R |
|---|---:|---:|
| spread_1_5 | 81 | -0.041 |
| spread_3 | 81 | -0.067 |
| slip_1 | 81 | -0.069 |
| delay_1m | 80 | +0.006 |
| fixed_80_110 | 77 | -0.008 |
| symmetric | 81 | -0.048 |
| optimistic_close | 81 | -0.006 |
| 3 dakika mum | 67 | -0.112 |
| 5 dakika mum | 51 | -0.026 |

Altı ölçüt: `{'volume_150': False, 'positive_ev_day_bootstrap_90': False, 'both_calendar_halves': False, 'spread_1_5': False, 'honest_vs_close_entry': False, 'one_position': False}`. Bar kartı tamamı=False; hacim/kart durumu=RED. LIVE yetkisi çıkarılmaz. Seçim ön-ölçütlerini geçti=False.

## İlk turun başarısızlıkları da kayıtlı

İlk beş, dört keşif/doğrulama alt döneminde pozitifti. Sonraki dönem ve ayrı yıl testinde sonuçlar:

| İlk aday | Keşif EV | Mayıs/Haziran EV | Temmuz/Ağustos EV | 2025 M1 EV |
|---|---:|---:|---:|---:|
| exhaustion_60_none_buy | +0.105 | +0.144 | -0.157 | -0.049 |
| sweep_60_quiet_buy | +0.075 | +0.173 | -0.236 | -0.014 |
| failed_break_60_h1_both | +0.102 | +0.256 | -0.217 | -0.084 |
| efficient_pullback_30_efficiency_both | +0.115 | +0.196 | +0.031 | -0.029 |
| midpoint_reclaim_30_quiet_sell | +0.083 | +0.088 | +0.170 | -0.062 |

İlk beş ayrıca yeni Eylül verisinde tanımları değişmeden denendi:

| İlk aday | Eylül M1 n / EV | Eylül 3m n / EV | Eylül 5m n / EV |
|---|---|---|---|
| exhaustion_60_none_buy | 84 / -0.125 | 17 / -0.008 | 7 / -0.364 |
| sweep_60_quiet_buy | 28 / -0.093 | 20 / +0.168 | 18 / -0.216 |
| failed_break_60_h1_both | 56 / -0.016 | 47 / +0.102 | 37 / -0.053 |
| efficient_pullback_30_efficiency_both | 39 / +0.116 | 51 / +0.152 | 56 / +0.236 |
| midpoint_reclaim_30_quiet_sell | 43 / +0.168 | 33 / +0.089 | 31 / +0.224 |

Sakin bant orta seviye SELL ve verimli geri çekilme bu ek Eylül testinde 1/3/5m'de pozitif çıktı. Ancak 2025 aktarımı negatif; ilkinde Temmuz/Ağustos taban-üstü seçim avantajı yok, ikincisi ilk masraf stresinde işaret kaybetmişti. Bu sonuca bakarak ilk beşten yeni bir en-iyi-altküme seçilmedi.

İlk beşin Temmuz/Ağustos tek-pozisyon birleşimi +2,57R, maksimum düşüş 23,91R ve bootstrap pozitif oranı %56,05: uygulanabilir kâr kanıtı vermedi. Aynı dönem kuralları değiştirip yeniden holdout diye sunulmadı.

## Birleşik portföy ve pratik karar

İkinci beş, seçim sıralaması değişmeden tek toplam pozisyonla: n=123, toplam=+11.27R, EV=+0.092R, düşüş=6.86R, gün-blok %95 aralık=[-0.064837032529219, 0.24437823961675426], bootstrap pozitif oranı=%88.0. Aday sonuçlarını birbirine eklemek bu portföyü üretmez; çakışan fırsatlar elenir.

Bu kapılar barlardan tanımlanan yeni giriş kaynaklarıdır. Botun VIXREG/MOM/CHREV akışına uygulanınca ek para kazandırdıkları bu replay ile kanıtlanmış olmaz. Bunun için aynı fırsatta orijinal karar, yeni karar, ret sebebi ve gerçek sonraki tick fill maliyeti eş zamanlı gölgede kaydedilmelidir.

Canlı terfi için: donmuş kural, daha sonraki hiç kullanılmamış dönem; ≥150 bağımsız çözümlenmiş karar; pozitif EV ve gün-blok güveni; iki zaman yarısı; masraf stresi; gerçek spread/fill; tek toplam pozisyon. Beş kuralı seçip ardından Eylül'ün iyi alt kümelerini yeniden seçmek yeni bir arama olur ve yeni son test gerektirir.

## Doğrulama ve tekrar üretim

- 7 elle kurulmuş bid/ask, aynı-mum, adverse gap, zaman-stop ve eksik-dakika yürütme örneği geçti.
- İlk 432 tanım × 1/3/5m için gelecek veriler kaldırıldığında önceki özellikler ve kararlar birebir aynı kaldı.
- İkinci turun AR/VR özelliklerinde 1/3/5m prefix nedensellik ve gerçek ask/high kontrolü ayrıca yapıldı.
- Protokoller, tüm aday taramaları, donmuş seçimler, işlem CSV'leri ve veri kaynağı hash'leri bu klasördedir. Büyük ham veri tekrar üretilebilir yerel artefakttır.

```bash
python3 research/ndx_five_gates_20260930/lab.py discover
python3 research/ndx_five_gates_20260930/lab.py evaluate
python3 research/ndx_five_gates_20260930/transfer.py 2025
python3 research/ndx_five_gates_20260930/second_search.py search
python3 research/ndx_five_gates_20260930/second_search.py evaluate
python3 research/ndx_five_gates_20260930/verify.py
python3 research/ndx_five_gates_20260930/verify_second.py
python3 research/ndx_five_gates_20260930/make_report.py
```

Yeniden `search` çalıştırmak yeni arama sayılmaz ancak donmuş artefaktları yeniden yazar; yeni dönem için önce yeni protokol oluşturun. MT5 uzaktan okuma betiği emir/ayar/dosya yazmaz; köprüde normal komut kuyruğu kaydı oluşturur.

Çoklu aramanın aşırı uyuma yol açabileceği metodolojik dayanak: [Bailey ve diğerleri, The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf). Buradaki seçim ve test ayrımı bu riski azaltmak içindir; bu çalışmada PBO/CSCV hesaplandığı iddia edilmez.

## Grafikler

`results/equity.png`: bağımsız Eylül equity. `results/trade_examples.png`: her adayın tarih sırasındaki ilk kazananı ve ilk kaybedeni; girişten sonra görülen mumlar yalnız betimleyicidir, giriş kararına katılmaz.

## Donmuş portföyün ek stres denetimi

| Dönem / stres | n | EV R | Toplam R |
|---|---:|---:|---:|
| year_a_primary | 698 | +0.019 | +13.58 |
| year_b_primary | 650 | +0.037 | +24.31 |
| mt5_presep_primary | 408 | +0.004 | +1.62 |
| september_primary | 123 | +0.092 | +11.27 |
| september_a_primary | 66 | +0.138 | +9.13 |
| september_b_primary | 57 | +0.038 | +2.14 |
| mt5_presep_spread_1_5 | 408 | -0.000 | -0.01 |
| september_spread_1_5 | 123 | +0.088 | +10.81 |
| september_a_spread_1_5 | 66 | +0.134 | +8.84 |
| september_b_spread_1_5 | 57 | +0.035 | +1.97 |
| mt5_presep_spread_3 | 412 | -0.004 | -1.82 |
| september_spread_3 | 124 | +0.080 | +9.98 |
| september_a_spread_3 | 67 | +0.127 | +8.53 |
| september_b_spread_3 | 57 | +0.025 | +1.45 |
| mt5_presep_slip_1 | 409 | -0.010 | -3.99 |
| september_slip_1 | 123 | +0.070 | +8.60 |
| september_a_slip_1 | 66 | +0.115 | +7.62 |
| september_b_slip_1 | 57 | +0.017 | +0.99 |
| mt5_presep_delay_1m | 415 | -0.011 | -4.67 |
| september_delay_1m | 126 | +0.069 | +8.75 |
| september_a_delay_1m | 66 | +0.077 | +5.05 |
| september_b_delay_1m | 60 | +0.062 | +3.70 |

Bu tabloda portföy sıralaması ve kurallar sabittir. 2025 ve Ağustos öncesi dönemler seçim verisidir; yalnız Eylül son testtir. Masraf senaryolarının aynı ham veri üzerinde tekrar hesaplanması yeni bağımsız örneklem değildir.

**Portföyün geçemediği noktalar:** Eylül n=123 (<150); gün-blok bootstrap pozitif oranı %87,96 (<%90) ve %95 EV aralığı [−0,065,+0,244]R. 2026 Mayıs–Ağustos EV +0,004R iken spread×1,5 ile yaklaşık sıfıra/negatife düşüyor; 1 puan/fill kaymada −0,010R. 2025 iki yarısında veri boşluklarını en az −1R sayınca EV negatif. Bu nedenle pozitif manşet tek başına canlıya terfi sağlamaz.
