# Ön-kayıt — day-trader-skill'in TÜM özelliklerinin bizim sembollerimize uyarlanıp sınanması (DTS-01…DTS-05)

2026-11-04, sonuç görülmeden yazıldı. Kullanıcı: "bu sistemin tüm özelliklerini kendi sistemimize ve sembollerimize uyarla,
farklı zaman dilimlerinde uçtan uca test et; kesinlikle çalıştığına emin olabileceğin özellikler hangileri, sistemin hangi
yapısına nasıl entegre edilir". Kaynak: github.com/jakeschincariol/day-trader-skill (MIT, 2026-10-20, 11 yetenek).
Kurallar repodan AYNEN alınır (bizim verimize bakılarak seçilmedi) → tüm tarihçe bizim için dış örneklemdir; yine de
kronolojik iki yarı zorunludur. Defter önceki ilgili satırlar: FG/OLD-15 (NDX ORB −0,89R), FC-xx (FCR X), XS-01 (XAU
55g Donchian B), BTC-T03, HK-04, TM-01. Burada yeni olan: repo'nun TAM tanımları (kapanışla 20-bar tepe, bayrak,
MA20 geri alım, RSI<30, dönüş; ORB'de aralık-ortası stop + 2R + kapanışta düz), DAX/XAU/USOIL ve çoklu TF.

## Sınıflandırma (sınanmadan, kapsam gereği)
| yetenek | bizim için | neden |
|---|---|---|
| trader-scanner (günlük 5 kurulum + ORB taraması) | DTS-01, DTS-02 | sembol-bağımsız kurallar |
| trader-entry + trader-exit (ORB zinciri) | DTS-02 | — |
| trader-timemachine | TM-01 (yapıldı) + DTS-03 (TF genişletme) | — |
| trader-budget (sabit $ risk ile lot) | DTS-04 | botun gerçek işlemleri |
| trader-risk (günlük işlem/zarar sınırı, min R:R, saat penceresi) | DTS-05 | botun gerçek işlemleri |
| trader-alerts | eşleme (kenar iddiası yok) | fiyat/stop/hedef/saat alarmı = mühendislik |
| trader-broker | uygulanamaz | Alpaca; bizde MT5 + 'kullanıcı evet demeden emir yok' zaten decider/bot kuralı |
| trader-news | uygulanamaz/eşleme | tek-hisse Yahoo RSS + SEC 8-K; bizde RSS + yakında Telegram |
| trader-analyst | uygulanamaz | SEC şirket bilançoları; endeks/emtia CFD'de yok |
| trader-pelosi | uygulanamaz | Kongre tek-hisse bildirimleri; endeks/emtia kenarı iddiası yok |

## Veri
`backend/data/candle_history/*.npz` (broker, UTC): 5m NDX 2025-01+, XAU/USOIL 2025-06+; 15m NDX/XAU/USOIL 2023-03+,
DAX 2022-11+; 1h NDX/XAU/USOIL 2016+, DAX 2020+; 4h ve 1d ← 1h (NY 17:00 broker günü). Botun işlemleri: Supabase
`bot_trades` (2026-06-29 → 11-04, 938 kapanmış). Spread (puan, gidiş-dönüş tek seferde girişte): NDX 1,3 · DAX 1,5 ·
XAU 0,25 · USOIL 0,028; stres ×1,5.

## DTS-01 — Tarayıcı kurulumları (repo `find_setups`, kapanışlar üzerinde, aynen)
breakout_20d: kapanış > önceki 20 kapanışın en yükseği · bull_flag: c[-6]/c[-16]−1 > %10 ∧ son 5 kapanış aralığı < %5 ·
reclaim_ma20: dünkü kapanış < dünkü MA20 ∧ bugünkü kapanış > MA20 · oversold: RSI14 (Wilder) < 30 ·
oversold_bounce: önceki barın RSI < 30 ∧ kapanış > önceki kapanış. Repo günlük çalışır; kullanıcı isteğiyle aynı kurallar
bar sayısıyla 1h, 4h, 1d'de. İşlem (repo yalnız uzun): giriş t+1 açılışı + spread, çıkış t+h kapanışı, h ∈ {1, 5, 10} bar.
Ölçü: aynı sembol×TF×h'de TÜM barlarda aynı uzun işleme göre fazla getiri (bp). Belirsizlik takvim-ayı blok bootstrap
(B=5.000). Olay = arada ≥ h bar boşluk olan tetik kümeleri. **Hücre geçer:** fazla > 0, P ≥ 0,975, iki yarıda fazla > 0,
≥ 30 olay, VE net ortalama (spreadli) > 0. Aile 5×4×3×3 = 180 hücre → güçlü kanıt Bonferroni P ≥ 0,99986; simetri:
P ≤ 0,025 (ters yönde anlamlı) hücre sayısı da raporlanır (E26). **Özellik 'çalışıyor' sayılır:** aynı kurulum×TF×h'de
≥ 2 sembolde hücre geçer ve aile geçen sayısı tesadüfü (%2,5) binom p < 0,01 ile aşar.

## DTS-02 — ORB zinciri (trader-entry + trader-exit + timemachine geçmiş kuralı)
Seans açılışı/kapanışı (yerel saat): NDX 09:30–15:55 NY · DAX 09:00–17:25 Berlin · XAU 08:20–13:25 NY · USOIL 09:00–14:25
NY. Aralık = ilk {15 (repo), 30} dk'nın yükseği/düşüğü; giriş barı TF {5m (repo), 15m}; tetik = aralıktan sonraki ilk
KAPANIŞI aralık yükseğinin üstünde olan bar (uzun, repo); ayna kısa ikincil. Son giriş = kapanış − 25 dk.
Giriş: GERÇEKÇİ = sonraki barın açılışı + spread (kart ölçütü 5); İYİMSER = tetik barı kapanışı, spreadsiz.
Stop: or_mid (repo varsayılanı) · or_low · 1,5×ATR14 (giriş TF'si); risk < fiyatın %0,05'i → işlem yok (repo reddi).
Hedef: 2R (repo varsayılanı) · 1R. Aynı barda stop+hedef → stop. Kapanış saatinde düz (o barın kapanışı).
**Birincil hücre (sembol başına 1):** aralık 15 dk, giriş 5m (DAX'ta 15m, 5m arşiv yok), or_mid, 2R, uzun, gerçekçi giriş.
**Geçer (kart ölçütleri):** n ≥ 150, ort R > 0 ve P(EV>0) ≥ 0,90, iki yarı ≥ 0, spread ×1,5'te > 0, (iyimser − gerçekçi)
≤ ort R/2. Gün başına tek işlem → 6. ölçüt kendiliğinden. Diğer hücreler (or 30, 15m, or_low, ATR, 1R, kısa) duyarlılık.

## DTS-03 — Zaman Makinesi farklı TF'lerde (TM-01b'nin genişlemesi)
`time_machine_service` (bar_min parametreli): 5m (NDX/XAU/USOIL) H ∈ {12, 48, 96} · 15m (4 sembol) H ∈ {4, 16, 32} ·
1h (4 sembol) H ∈ {4, 8, 24}. Sorgu adımı ≈ 8 saat, havuz önceki 60 dolu seans, 600 simülasyon. Ölçü: ufuk-sonu kapanışın
%90 ve %50 aralıkta kalma oranı + saat-koşulsuz aralık kıyası; ikincil: 1R/1×ATR hedef-önce Brier vs sabit taban.
**Aralık 'çalışıyor':** her sembol×TF×H hücresinde %90 kapsama ∈ [85, 95] ve medyan genişlik ≤ saat-koşulsuz genişlik × 1,05.

## DTS-04 — Bütçe: sabit $-risk lot (trader-budget) vs botun sabit lotu
Her kapanmış bot işlemi için R = yönlü fiyat hareketi / |giriş − stop| (stop = kayıtlı sl; sl yoksa veya giriş ±%0,02
içindeyse — başabaşa çekilmiş — dışarıda). $/puan çarpanı işlemin kendi kârından türetilir. Sabit-risk P&L = R × (gerçek
işlemlerin ortalama $ riski) → aynı ortalama risk. Ölçü: günlük P&L Sharpe, en büyük düşüş (max DD), toplam. **Çalışıyor:**
sabit-risk Sharpe > sabit-lot Sharpe (gün-blok bootstrap P ≥ 0,90) VE max DD daha küçük.

## DTS-05 — Risk yöneticisi kuralları botun işlemlerinde
Repo varsayılanları uyarlanmış: günde en çok 3 giriş; günlük zarar sınırı = 3 × ortalama $ risk; min R:R 1,0 (TP mesafesi /
SL mesafesi ≥ 1). Her kural ayrı ve birlikte, işlemler zaman sırasıyla (o günün önceki sonuçları bilinerek) süzülür.
Ölçü: kalan işlemlerin toplamı ve ortalaması vs hepsi, elenenlerin ortalaması; **çalışıyor:** elenen kümenin ortalaması
< 0 ve kalanın toplamı ≥ hepsinin toplamı, iki kronolojik yarıda da. (Bot zaten günlük fren taşıyor — E19: atılan işlemin
yerine başka işlem gelebilir; bu ölçüm o etkiyi kapsamaz, sonuç üst sınır sayılır.)

## Ek (sonradan, DTS-02 sonuçları görüldükten sonra — DTS-02b)
Defter §0 madde 5 "kapısız taban" ön-kayıtta unutuldu. Taban: aynı gün, aralık bittikten sonraki ilk barın açılışında
KIRILIM ŞARTI OLMADAN aynı yönde gir (+ spread), aynı stop kuralı (or_mid: aralık ortası; aralık ortası girişin yanlış
tarafındaysa o gün işlem yok), aynı hedef ve kapanış. Ölçü: ORB − taban, aynı günlerde eşli fark (ay-blok bootstrap).
Kırılımın katkısı sayılması için eşli fark > 0, P ≥ 0,90 ve iki yarıda > 0 olmalı.

## Ek-2 (2026-11-04, DTS-04/05/06 ve RSI örtüşme sonuçları GÖRÜLMEDEN; kullanıcı kararı: bant TP/SL ile tüm sisteme)
- **Veri:** `bot_trades` (Supabase, kapanmış, sl>0) → `data/bot_trades.csv`; panel sinyalleri `prediction_logs`
  (`factors.target_type='atr_ladder_v1'`, status completed/stopped, model pulse1/2/3/smc/ml*, son 60 gün) →
  `data/signals.csv`. Bot zamanları broker saatinde DEĞİL (bot_trades UTC timestamptz) — yine de 5m bar ızgarasına yuvarlanır.
- **DTS-04** ve **DTS-05**: yukarıdaki tanımlar aynen. Dönem orta noktası: işlem kapanış zamanının medyanı.
- **DTS-06** (bant × TP/SL): her işlem/sinyal için giriş anından ÖNCE kapanmış son 5m bar = sorgu; havuz önceki 60 seans
  (`time_machine_service`, 5m arşiv + candle_cache 5m birleşik, ≥ 2025-01); ufuk: bot için 48 bar (4 sa; bot işlemlerinin
  medyan süresine yakın), panel sinyali için 12 bar (60 dk = lifecycle penceresi). Ölçüler:
  (a) TP_DIŞ = TP %90 bandın dışında (uzun: TP > p95; kısa: TP < p5); SL_İÇ = SL %50 bandın içinde.
  (b) p_tp = ZM dokunma simülasyonu hedef-önce payı (600 replay) → Brier vs taban + kova sapması.
  (c) FİLTRE = p_tp / (p_tp + p_sl) < 1/(1+R_hedef) → atla.
  Gerçekleşen R: bot için kayıtlı kâr / ($ risk) (DTS-04 tanımı); sinyal için status (completed=+R_TP1, stopped=−1).
  **Kapı adayı (kart gerekir) sayılır:** FİLTRE veya TP_DIŞ elemesi için elenen ort. R < 0, kalan ort. R > hepsinin
  ort. R'si, iki yarıda da, ≥ 30 elenen işlem. Aksi hâlde bant yalnız bilgi/etiket olarak bağlanır.
- **RSI<30 örtüşme:** DTS-01 NDX 4h oversold olaylarını önceki işlem günü VIX kapanışı ≥ 18,4 ve "stres günü"
  (önceki gün ≤ −%1,5 veya 5 gün ≤ −%4) içi/dışı ayır; dış kümede fazla getiri > 0 ve P ≥ 0,90 → bot GÖLGE adayı.
