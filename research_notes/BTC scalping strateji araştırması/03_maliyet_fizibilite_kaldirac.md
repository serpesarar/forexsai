# BTC scalping: maliyet/fizibilite sınırı, icra gerçekçiliği ve kaldıraç matematiği

Kapsam: 2026-10-21, mevcut veriden hesaplama (yeni indirme yok, kutuya/Supabase'e dokunulmadı, commit yok).
Veri: Binance spot BTCUSDT 1m 2021-06-01 → 2026-10-20 ([btc_1m.parquet](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/btc_1m.parquet)),
Pepperstone BTCUSD M1 BID 2026-10-05 → 10-21 ([broker_btcusd_m1.parquet](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/broker_btcusd_m1.parquet)).
Dışlama: 2023-03-24 11:28–14:00 UTC + ≥5 dk Binance kesintileri; penceresi bunlarla kesişen girişler atıldı.
İcra kuralları: karar = dakika t kapanışı, giriş = **sonraki 1m açılışı**; **aynı barda TP+SL → SL**; SL dolumu boşluk-duyarlı
(min(SL, açılış)); TP limit dolumu seviyeden; zaman stopu = son barın kapanışı. "Rastgele giriş" = geçerli her dakika (2.82 M giriş/yön),
long ve short ayrı. R = SL mesafesi (bp). Maliyetler gidiş-dönüş (RT):

| kısaltma | tanım | RT maliyet |
|---|---|---|
| PEP_PCT | Pepperstone spread %0,0185 (demo tick medyanı 15 $ @ ~84k) | 1,85 bp |
| PEP_STRESS | ×1,5 stres (go-live kartı ölçüt 4) | 2,78 bp |
| PEP_FIX15 | sabit 15 $ (fiyat düştükçe bp büyür) | 1,45–6,48 bp (yıla göre) |
| BIN_TAKER | Binance USDT-M perp taker 0,05%/taraf | 10 bp |
| BIN_MAKER | maker 0,02%/taraf | 4 bp |
| BIN_MIX | maker giriş + taker çıkış | 7 bp |
| BIN_MIXTP | maker giriş, TP maker (4 bp), SL/zaman taker (7 bp) | 4/7 bp |

Betikler ve çıktılar: [feasibility/](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/)
(`lib.py` motor; `00_selftest.py` kaba-döngü eşlemesi 0/18.000 uyuşmazlık + önek/sızıntı testi ATR1/ATR5/RV OK;
`01_hits.py` ilk-dokunuş indeksleri; `02_frontier.py` sınır/ızgara/gruplar; `03_broker.py`; `04_leverage_mc.py`;
`05_martingale_check.py`; `06_brownian_check.py`; `07_gamblers_ruin.py`; `08_tables.py`; günlükler `logs/`, tablolar `out/*.csv`, `out/tables.md`).
Tablolarda ondalık ayırıcı nokta, metinde virgül.

---

## 1. Projenin önceki scalping dersleri

### Takeaway
Projede 1m/5m ölçekli her scalp hattı (XAU/NDX/DAX/USOIL 1m bataryası, NDX Reflex, fakeout işlem kartı, mum formasyonları, BTC 5m
negatif kontrolü) ya maliyete yenildi ya da "kenar" bir ölçüm hatası çıktı: sızıntı (sol-etiketli resample), 5m çözümle şişen WR,
tick-kirli 1m, iyimser stop dolumu, örtüşen örneklem, sürüklenme. Sağ kalan tek dürüst ders: kenar varsa **yön tahmininde değil
geometri/zaman çıkışında** küçük (≈0,03–0,1R) ve maliyete karşı çok kırılgan.

### Cited Findings
- **OLD-01 / 2026-05-29 XAU 1m:** TP=SL=5 pip (1:1) %70 WR "geometrik olarak imkânsız"; 6 kural %48–50, GBM %51–53 (spread sonrası %49,7); "%75"
  8 işlemde 6 (gürültü); 13 eğitim cebinin 0/13'ü testte tuttu (ortalama −18,5 puan); en iyi EV hücresi +0,19 $/işlem CI [−0,005, +0,366] ve
  sürüklenme sürüşü. Pencere taramasında "Pazartesi 02:00 SELL %80" = günde ~60 korele 1m giriş → "253 işlem" ≈ 5 bağımsız gün — [xauusd-scalp-no-edge.md](file:///Users/melihcanodacioglu/.claude/projects/-Users-melihcanodacioglu-Desktop-panel/memory/xauusd-scalp-no-edge.md)
- **Çok-varlık bataryası:** bariyer = medyan fiyatın %0,10'u, spread = bariyerin %6'sı; hiçbir sembolde dürüst ≥%70 WR veya CI alt sınırı > 0 olan net EV yok.
  DAX en büyük brüt yön sinyali (+0,539/işlem) ama net CI [−1,39, −0,40]; USOIL iki yönde ~%44 (aynı-barda çift dokunuş SL-önce kayıpları);
  yüksek-WR pencerelerinin hepsi sürüklenme (BUY+SELL WR toplamı %85–96) — [multi-asset-scalp-no-edge.md](file:///Users/melihcanodacioglu/.claude/projects/-Users-melihcanodacioglu-Desktop-panel/memory/multi-asset-scalp-no-edge.md)
- **NDX Reflex (OLD-15, GF-13, E16):** `mom_cont` "+0,29R transfer" 15m `label=left` resample sızıntısıydı; sızıntısız −0,08R, P(EV>0) %13.
  "70% WR" yüksek-isabet modu tüm 10 grupta ≥%70 (taban %77,8) ama EV ≈ −0,06R (başabaş %86). Trailing-stop kârları **dolum-konvansiyonu
  artefaktı** (stoptan dolum → gerçekçi min(stop, açılış) ile hepsi −0,03…−0,04R). Tek konvansiyona dayanıklı çıkış: ~15 dk zaman stopu.
  Yön tahmini 5/60 dk = taban (ilk "%70" yine sol-etiket sızıntısı). BE-5 bar WR'ı %45→%23 düşürdü — [ndx-reflex-engine-2026-07.md](file:///Users/melihcanodacioglu/.claude/projects/-Users-melihcanodacioglu-Desktop-panel/memory/ndx-reflex-engine-2026-07.md), [KAPI_KAYIT_DEFTERI.md §1 E16, §2.4 OLD-15](file:///Users/melihcanodacioglu/Desktop/panel/docs/KAPI_KAYIT_DEFTERI.md)
- **Fakeout dedektörü:** sınıflandırma isabeti yalnız **+1 bar gecikmeli** kararla %70/%70'e ulaştı (instant mod hiçbir konfigde değil); Temmuz
  etiketleri 3 saatlik broker-saati kaymasıyla bozuktu (E3), yeniden üretimde yalnız NDX geçti; **işlem stratejisi olarak** 786 karar brüt +0,019R,
  net −0,068R, P %1 (CK-02) — lab isabeti teyit-sonrası girişte kazanca dönmüyor; yalnız süzgeç olarak (CK-04) iş görüyor — [fakeout-detector-7070.md](file:///Users/melihcanodacioglu/.claude/projects/-Users-melihcanodacioglu-Desktop-panel/memory/fakeout-detector-7070.md), [KAPI_KAYIT_DEFTERI.md CK-02/CK-04](file:///Users/melihcanodacioglu/Desktop/panel/docs/KAPI_KAYIT_DEFTERI.md)
- **WR şişmesi:** 74,4k sinyalin 1m yeniden oynatmasında üretimdeki 51.562 "kazanç"ın %27,1'i gerçekte **SL-önce** kayıptı (5m mum değerlendirmesinin
  parmak izi); premium modeller 14–23 puan şişkin; yüksek GT-WR ≠ kâr — [ground-truth-wr-inflation.md](file:///Users/melihcanodacioglu/.claude/projects/-Users-melihcanodacioglu-Desktop-panel/memory/ground-truth-wr-inflation.md)
- **Tick-kirli 1m:** `candle_cache` '1m' içinde saniyelik tick satırları (low=high) karışık → yalnız `second=0` mumlar; backend çözümlemesi
  güvenilmez (XAU pulse2 SELL %2,9 backend vs %61 dürüst 1m); "aynala" ters çevirme −EV, RR≥0,8 +EV ama trend-bağımlı (yarılar %64,8→%52,6) — [xau-inverse-shadow-2026-07.md](file:///Users/melihcanodacioglu/.claude/projects/-Users-melihcanodacioglu-Desktop-panel/memory/xau-inverse-shadow-2026-07.md)
- **BE/kilit çıkışları:** 487 bot işleminde her BE eşiği kurtardığından çok kazananı öldürüyor (BE@TP yolunun %60'ı: 54 kurtar / 75 öldür);
  50+ çıkış kuralının hiçbiri sağlam değil; ilk motorda iki iyimser yanlılık: kilit fiyatın üstündeyken stoptan dolum ve gecikmesiz "kapat" — [be-lock-exit-rules-rejected.md](file:///Users/melihcanodacioglu/.claude/projects/-Users-melihcanodacioglu-Desktop-panel/memory/be-lock-exit-rules-rejected.md)
- **Defter tuzakları (seçme):** E6 (aynı koşul 60–75 sn'de bir kaydı → p 8× şişme), E7 (giriş = sinyal barı kapanışı + spread'siz → USOIL %58,8 → %42,7/−0,147R),
  E9 (aynı dakikada bölünmüş bacaklar), E13 (sürüklenme tabanı), E14 (WR↑ ≠ para↑), E16 (sol-etiket MTF sızıntısı); BTC'ye özgü E40–E50:
  E44 (kart ölçüt 5 yalnız ≤15m'de ayırt edici; bp-düzeyi kurallarda fiilen "net ≥ 2×spread"), E46 (DST'ye bağlı rollover = mevsime göre maliyet),
  **E47** (BTC'de 15m ATR stopları sık sık %0,3'ün altında; broker 1m'i Binance'ten ~%12 gürültülü → broker M1 ile teyit şart), **E50**
  (dar ATR stop paydası R'yi çarpıtır; R'yi her zaman bp ile yaz) — [KAPI_KAYIT_DEFTERI.md §1](file:///Users/melihcanodacioglu/Desktop/panel/docs/KAPI_KAYIT_DEFTERI.md)
- **BTC'deki kısa-vade sınamalar:** BTC-T08 (5m Donchian48 + EMA200, TP=SL=1×ATR5m, 24 s) BUY −0,204R (iyimser icrada −0,068 → icra farkı 0,136R),
  SELL −0,163R; BTC-M07 turn-of-the-candle brüt 2021 +0,57 → 2026 −0,08 bp, net −1,72 bp (maliyet modeli bilinen ölü kenarı öldürüyor);
  BTC-M01 kanal dönüşü 32 hücrenin 31'i ≤0; BTC-X09 BE BTC'de zararsız (+0,01R) ama küçük; MK-01: M1'de spread ≈ ATR'nin %19'u, 0/200 formasyon — [KAPI_KAYIT_DEFTERI.md §2.11, MK-01](file:///Users/melihcanodacioglu/Desktop/panel/docs/KAPI_KAYIT_DEFTERI.md), [BTC raporu](file:///Users/melihcanodacioglu/Desktop/panel/reports/BTC%20trader%20bot%20kenar%20ara%C5%9Ft%C4%B1rmas%C4%B1.md)

### Inferences
- Hata kalıpları dört başlıkta toplanıyor: (1) **zaman/sızıntı** (sol-etiket resample, broker saati, `copy_rates_from` ileri bakışı),
  (2) **çözünürlük** (5m'de değerlendirme → SL-önce kayıplar kazanç sayılır; tick-kirli 1m), (3) **dolum iyimserliği** (stoptan dolum,
  gecikmesiz kapat, aynı-bar belirsizliğinde TP), (4) **istatistik** (örtüşen girişler = sahte n, WR'ın geometriye bağlılığı, sürüklenme, seçim yükü).
- Bu çalışmada (aşağıda §3) bunlara bir beşincisi eklendi: **1m bar verisinde seviye kesişiminde ~1 bp örtük aşım** — "seviyeden dolum"
  varsayımı dar-SL/geniş-TP geometrilerine hiçbir beceri olmadan +0,5…+0,8 bp brüt "kenar" verir.
- Önceki çalışmaların hepsinin ortak sonucu, bu notun ana sorusunu belirliyor: brüt yön kenarı ya yok ya da ≤0,1R düzeyinde; bu yüzden
  **maliyet/R oranı ≤ %10** olmadan hiçbir scalp aday sayılmamalı.

### Gaps
- Önceki scalp çalışmaları NDX/XAU/DAX/USOIL içindi; BTC'de ön-kayıtlı bir 1m scalp bataryası (yön/ML) daha önce koşulmadı — yalnız 5m negatif
  kontrol (BTC-T08) ve zaman kuralları var.

---

## 2. Maliyet sınırı (rastgele giriş): asgari braket, çözülme süresi, günlük fırsat

### Takeaway
Rastgele girişin brüt beklentisi gerçekten ≈0'dır (simetrik braketlerde tam olarak −aynı-bar belirsizlik oranı kadar, R cinsinden). Maliyetin R'nin
≤%10'u olması için asgari simetrik braket: **Pepperstone ~18,5 bp** (stres 28 bp; sabit 15 $ varsayımında 2022'de 65 bp, 2025'te 14,5 bp),
**Binance maker 40 bp, maker+taker 70 bp, taker 100 bp**. 2023+ oynaklığında (ATR5m ≈ 12–16 bp) bu, Pepperstone için ~1,1–1,6×ATR5m, medyan
çözülme 11–22 dk ve günde ~80–130 ardışık fırsat; Binance taker için ~6–8×ATR5m, medyan 4–6 saat ve günde 3–6 fırsat demek — yani Binance
taker'da "scalp" tanım gereği yok. ≤%20 sınırında Pepperstone 9 bp, Binance maker 20 bp, taker 50 bp.

### Cited Findings
**Oynaklık rejimi (ATR14 medyanı, bp):** 2021 ATR1m 10,9 / ATR5m 26,9 · 2022 8,4 / 21,2 · 2023 4,1 / 12,0 · 2024 5,9 / 16,4 · 2025 4,6 / 13,0 · 2026 4,5 / 12,9 —
BTC'nin 1m/5m oynaklığı 2021'den beri yarı yarıya düştü; aynı bp braket 2023+'da iki kat "geniş" — [tau_dist.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/tau_dist.csv)

**Gidiş-dönüş maliyet (bp) yıla göre:**

| venue | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| PEP_PCT | 1.85 | 1.85 | 1.85 | 1.85 | 1.85 | 1.85 |
| PEP_STRESS | 2.77 | 2.77 | 2.77 | 2.77 | 2.77 | 2.77 |
| PEP_FIX15 ($15 / medyan fiyat) | 3.17 | 6.48 | 5.41 | 2.34 | 1.45 | 2.05 |
| BIN_TAKER / MIX / MAKER | 10 / 7 / 4 | aynı | aynı | aynı | aynı | aynı |

**Maliyet ≤ %10 R için asgari simetrik braket** (hücre: braket bp (×ATR5m medyanı) · medyan çözülme τ, zaman stopu yok · ardışık örtüşmesiz işlem/gün medyanı) — [frontier_min_bracket.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/frontier_min_bracket.csv):

| venue | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| PEP_PCT (1,85) | 18.5 (0.7×) · 5 dk · 244/g | 18.5 (0.9×) · 9 dk · 174/g | 18.5 (1.6×) · 22 dk · 79/g | 18.5 (1.1×) · 11 dk · 131/g | 18.5 (1.4×) · 16 dk · 90/g | 18.5 (1.4×) · 17 dk · 90/g |
| PEP_STRESS (2,78) | 27.7 (1.0×) · 11 dk · 123/g | 27.7 (1.3×) · 18 dk · 84/g | 27.7 (2.3×) · 44 dk · 38/g | 27.7 (1.7×) · 24 dk · 66/g | 27.7 (2.1×) · 35 dk · 42/g | 27.7 (2.2×) · 36 dk · 44/g |
| PEP_FIX15 | 31.7 (1.2×) · 14 dk · 96/g | 64.8 (3.1×) · 83 dk · 17/g | 54.1 (4.5×) · 139 dk · 11/g | 23.4 (1.4×) · 18 dk · 88/g | 14.5 (1.1×) · 10 dk · 133/g | 20.5 (1.6×) · 21 dk · 76/g |
| BIN_MAKER (4) | 40 (1.5×) · 21 dk · 62/g | 40 (1.9×) · 35 dk · 43/g | 40 (3.3×) · 84 dk · 19/g | 40 (2.4×) · 47 dk · 33/g | 40 (3.1×) · 70 dk · 21/g | 40 (3.1×) · 70 dk · 22/g |
| BIN_MIX (7) | 70 (2.6×) · 62 dk · 22/g | 70 (3.3×) · 95 dk · 15/g | 70 (5.8×) · 210 dk · 7/g | 70 (4.3×) · 129 dk · 11/g | 70 (5.4×) · 189 dk · 7/g | 70 (5.4×) · 184 dk · 7/g |
| BIN_TAKER (10) | 100 (3.7×) · 122 dk · 10/g | 100 (4.7×) · 173 dk · 7/g | 100 (8.4×) · 340 dk · 3/g | 100 (6.1×) · 233 dk · 6/g | 100 (7.7×) · 322 dk · 4/g | 100 (7.8×) · 317 dk · 4/g |

**Maliyet ≤ %20 R:**

| venue | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| PEP_PCT | 9.2 (0.3×) · 2 dk · 657/g | 9.2 (0.4×) · 3 dk · 488/g | 9.2 (0.8×) · 6 dk · 240/g | 9.2 (0.6×) · 4 dk · 381/g | 9.2 (0.7×) · 5 dk · 267/g | 9.2 (0.7×) · 5 dk · 266/g |
| PEP_STRESS | 13.9 (0.5×) · 4 dk · 386/g | 13.9 (0.7×) · 5 dk · 274/g | 13.9 (1.2×) · 13 dk · 129/g | 13.9 (0.8×) · 7 dk · 210/g | 13.9 (1.1×) · 10 dk · 143/g | 13.9 (1.1×) · 11 dk · 144/g |
| PEP_FIX15 | 15.8 · 4 dk · 314/g | 32.4 · 24 dk · 63/g | 27.1 · 43 dk · 40/g | 11.7 · 5 dk · 276/g | 7.2 · 4 dk · 377/g | 10.3 · 6 dk · 230/g |
| BIN_MAKER | 20 (0.7×) · 6 dk · 216/g | 20 (0.9×) · 10 dk · 153/g | 20 (1.7×) · 25 dk · 69/g | 20 (1.2×) · 13 dk · 116/g | 20 (1.5×) · 19 dk · 79/g | 20 (1.6×) · 20 dk · 79/g |
| BIN_MIX | 35 (1.3×) · 17 dk · 80/g | 35 (1.6×) · 28 dk · 55/g | 35 (2.9×) · 67 dk · 24/g | 35 (2.1×) · 37 dk · 43/g | 35 (2.7×) · 55 dk · 27/g | 35 (2.7×) · 55 dk · 28/g |
| BIN_TAKER | 50 (1.9×) · 32 dk · 41/g | 50 (2.4×) · 53 dk · 28/g | 50 (4.2×) · 122 dk · 12/g | 50 (3.0×) · 71 dk · 22/g | 50 (3.9×) · 106 dk · 14/g | 50 (3.9×) · 103 dk · 14/g |

(τ ve işlem/gün, ızgara seviyeleri arasında log-log enterpolasyon; "işlem/gün" = bir önceki işlem çözülür çözülmez sonraki dakikada yeniden
giren ardışık tek-pozisyon zinciri — fiziksel üst sınır, kenarlı fırsat sayısı DEĞİL.)

**Çözülme süresi dağılımı** (simetrik braket, zaman stopu yok; dk medyan [p25–p90] ve aynı-bar TP+SL oranı) — [tau_dist.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/tau_dist.csv):

| bp | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| 5 | 1 [1–2] · %12.0 | 1 [1–5] · %9.2 | 3 [1–13] · %3.1 | 2 [1–6] · %4.6 | 2 [1–9] · %3.1 | 2 [1–11] · %2.8 |
| 10 | 2 [1–7] · %2.6 | 3 [1–15] · %2.1 | 7 [3–41] · %0.6 | 4 [2–19] · %0.8 | 6 [3–28] · %0.5 | 6 [3–33] · %0.5 |
| 20 | 6 [3–22] · %0.3 | 10 [4–55] · %0.3 | 25 [9–139] · %0.1 | 13 [5–63] · %0.1 | 19 [8–97] · %0.1 | 20 [8–109] · %0.1 |
| 30 | 13 [6–45] | 21 [8–116] | 51 [20–263] | 28 [11–131] | 41 [16–204] | 42 [16–223] |
| 50 | 32 [15–114] | 53 [20–280] | 122 [48–557] | 71 [29–313] | 106 [42–474] | 103 [42–484] |
| 100 | 122 [55–410] | 173 [69–717] | 340 [144–998] | 233 [101–794] | 322 [141–976] | 317 [137–975] |

100 bp'de 1440 dk içinde çözülmeyen oran 2023'te %15, 2025'te %11; 150–200 bp'de %21–47 (artık scalp değil, gün-içi swing).

**Rastgele giriş, simetrik braket, 2021-06→2026-10 (R):** brüt L/S ortalaması = −(aynı-bar oranı) — 5 bp −0,054R (amb %5,4), 10 bp −0,011R, 20 bp −0,002R,
≥30 bp ≈ 0,000R. Net (H=60): 10 bp PEP −0,196R / FIX15 −0,362 / TAKER −1,011 / MAKER −0,411; 20 bp −0,094 / −0,177 / −0,502 / −0,202; 50 bp −0,037 / −0,070 / −0,200 / −0,080;
100 bp −0,019 / −0,035 / −0,100 / −0,040. Zaman stopu (H=5→60) R maliyetini değiştirmiyor; yalnız TP/SL/zaman paylarını değiştiriyor (20 bp, H=5'te
%76 zaman çıkışı; H=60'ta %15) — [grid_sym_year.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/grid_sym_year.csv)

**Başabaş WR (saf braket, (SL+c)/(TP+SL)) — asimetrik seçmeler, H=60, tüm yıllar, L/S ortalaması** — [grid_asym_year.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/grid_asym_year.csv):

| TP/SL bp | brüt bp | brüt R | TP oranı | zaman payı | net R PEP | net R TAKER | net R MAKER | başabaş WR PEP | başabaş WR TAKER |
|---|---|---|---|---|---|---|---|---|---|
| 5/5 | −0.27 | −0.054 | 0.471 | 0.003 | −0.424 | −2.054 | −0.854 | 0.685 | 1.50 (imkânsız) |
| 5/20 | −0.68 | −0.034 | 0.756 | 0.030 | −0.126 | −0.534 | −0.234 | 0.874 | 1.20 (imkânsız) |
| 5/100 | −0.79 | −0.008 | 0.854 | 0.125 | −0.026 | −0.108 | −0.048 | 0.970 | 1.05 (imkânsız) |
| 10/10 | −0.11 | −0.011 | 0.481 | 0.027 | −0.196 | −1.011 | −0.411 | 0.592 | 1.00 (imkânsız) |
| 20/10 | +0.23 | +0.023 | 0.310 | 0.068 | −0.162 | −0.977 | −0.377 | 0.395 | 0.667 |
| 20/20 | −0.03 | −0.002 | 0.425 | 0.149 | −0.094 | −0.502 | −0.202 | 0.546 | 0.750 |
| 50/10 | +0.49 | +0.049 | 0.113 | 0.167 | −0.136 | −0.951 | −0.351 | 0.197 | 0.333 |
| 50/20 | +0.25 | +0.013 | 0.163 | 0.313 | −0.080 | −0.487 | −0.187 | 0.312 | 0.429 |
| 50/50 | −0.01 | −0.000 | 0.214 | 0.572 | −0.037 | −0.200 | −0.080 | 0.518 | 0.600 |
| 100/5 | +0.78 | +0.155 | 0.021 | 0.125 | −0.215 | −1.845 | −0.645 | 0.065 | 0.143 |
| 100/20 | +0.31 | +0.015 | 0.048 | 0.407 | −0.077 | −0.485 | −0.185 | 0.182 | 0.250 |
| 100/100 | −0.00 | −0.000 | 0.071 | 0.859 | −0.019 | −0.100 | −0.040 | 0.509 | 0.550 |

Dar-SL/geniş-TP hücrelerinin pozitif brüt değeri (≤ +0,8 bp) beceri değil, ölçüm etkisidir (bkz. §3, "örtük aşım").

**ATR-ölçekli braketler (H=60):** 1×ATR5m'nin medyan bp'si 2021 26,9 → 2023 12,0 → 2026 12,9; medyan τ 9–11 dk; aynı-bar ≤%0,1; maliyet/R medyanı (medyan ATR ile)
PEP ≈ 0,07 (2021) → 0,11–0,15 (2023+), TAKER ≈ 0,37 → 0,61–0,84. 0,5×ATR1m (≈2–5 bp): aynı-bar %5–7, τ = 1 dk, maliyet/R PEP 0,34–0,82 → kesinlikle olanaksız — [grid_atr_year.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/grid_atr_year.csv)

**Saat / hafta sonu / oynaklık rejimi (1×ATR5m braketi, 5 yıl)** — [by_group.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/by_group.csv):

| grup | ATR5m medyan bp | PEP maliyet/R | TAKER maliyet/R | MAKER maliyet/R | 20 bp braket medyan τ (dk) | 20 bp 60 dk'da çözülen |
|---|---|---|---|---|---|---|
| 13–16 UTC (ABD açılışı) | 18,1–25,6 | 0,07–0,10 | 0,39–0,55 | 0,16–0,22 | 7–9 | %91–93 |
| 17–20 UTC | 17,9–20,9 | 0,09–0,10 | 0,48–0,56 | 0,19–0,22 | 11–14 | %85–89 |
| 00–02 UTC | 15,7–17,4 | 0,11–0,12 | 0,58–0,64 | 0,23–0,25 | 12–17 | %83–89 |
| 03–11 UTC (Asya–Avrupa sabahı) | 12,3–14,4 | 0,13–0,15 | 0,69–0,81 | 0,28–0,33 | 18–23 | %77–83 |
| hafta içi | 18,2 | 0,10 | 0,55 | 0,22 | 12 | %91 |
| hafta sonu | 10,9 | 0,17 | 0,92 | 0,37 | 27 | %71 |
| RV24h < %35 | 9,0 | 0,21 | 1,12 | 0,45 | 38 | %65 |
| RV %35–60 | 16,8 | 0,11 | 0,60 | 0,24 | 14 | %91 |
| RV %60–90 | 27,3 | 0,07 | 0,37 | 0,15 | 6 | %99 |
| RV > %90 | 39,9 | 0,05 | 0,25 | 0,10 | 3 | %100 (aynı-bar %1,2) |

Rastgele girişin brüt L/S ortalaması her saat/rejim hücresinde −0,003…−0,08 bp (≈0; RV>%90'da 20 bp braket −0,24 bp = aynı-bar etkisi); L ile S arasındaki işaretli farklar (ör. 16 UTC L −1,18 / S +1,17 bp)
yalnız saat-of-gün sürüklenmesi — BTC-M03 ile tutarlı, kenar değil.

### Inferences
- **Scalping-uygun bölge (maliyet ≤ %10 R)**: Pepperstone'da SL ≥ ~19 bp (stres altında ≥ ~28 bp) ve bunun 2023+ rejiminde ≈1,1–2,2×ATR5m, τ ≈ 10–40 dk olması;
  Binance'te ancak maker girişle ve SL ≥ 40 bp (≈3×ATR5m, τ ≈ 1 saat+). Taker-taker Binance (10 bp RT) %10 sınırını yalnız ≥100 bp'de sağlar: bu bir
  **gün-içi swing**, scalp değil. Kaldıraç bu tabloyu değiştirmez (maliyet notional'la ölçeklenir, R'de sabit; §4).
- Sabit 15 $ spread geçmişe taşındığında 2022–23 dibinde (16–30k) RT maliyet 5–6,5 bp'ye çıkar; 2022–23 verisine dayanan bir CFD scalp backtest'i
  yüzde-sabit varsayımla (1,85 bp) **çok iyimser** olabilir. Hangi varsayımın doğru olduğu bilinmiyor (bkz. Gaps) → iki varyant birlikte raporlanmalı.
- Fırsat sayısı bol (Pepperstone 20 bp'de 2025–26'da günde ~80 ardışık işlem kapasitesi) — darboğaz kapasite değil, **kenar/maliyet oranı**. Kenar ≈ 0,03–0,05R düzeyindeyse
  (projede görülen en iyi dürüst değerler) PEP_PCT maliyeti (20 bp'de 0,09R) kenarı tek başına aşıyor; net-pozitif için brüt kenar ≥ ~0,15R gerekli.
- En "ucuz" dilimler (maliyet/R'nin en düşük olduğu, τ'nun en kısa olduğu) ABD açılışı 13–16 UTC, hafta içi ve RV %60+ rejimleri. Hafta sonu ve RV<%35
  dönemlerinde ATR-ölçekli bir braketin maliyet/R'si ~2 katına çıkar.
- 2021 rejimi (ATR5m 27 bp) bugünün (13 bp) iki katı oynak: 2021'de seçilmiş bp-sabit braketler bugün iki kat geniş ve iki kat yavaş davranır →
  braketi bp yerine ATR/RV ile ölçeklemek ve **yıl bazında** raporlamak zorunlu.

### Gaps
- Pepperstone spread'i yalnız son 14 gün tick + 60 gün M1 ile ölçülmüştü (2026-10); 2021–2025 broker spread'i, canlı (real) hesap spread'i, komisyon ve
  stop kayması bilinmiyor ([02_veri_ve_broker.md](file:///Users/melihcanodacioglu/Desktop/panel/research_notes/BTC%20trader%20bot%20kenar%20ara%C5%9Ft%C4%B1rmas%C4%B1/02_veri_ve_broker.md)).
- Binance ücretleri: VIP0 USDT-M 0,02% maker / 0,05% taker üçüncü taraf kaynaklarda doğrulanıyor ([Finder](https://www.finder.com/cryptocurrency/trading/binance-futures-fees), [CryptoPotato](https://cryptopotato.com/binance-fees/));
  Binance'in kendi destek sayfası oranı vermiyor, VIP seviyesine göre değiştiğini ve BNB ile %10 indirim olduğunu söylüyor ([Binance](https://www.binance.com/es/support/articles/360033544231)). Canlı oran sayfası okunmadı.
- Perp için Binance **spot** 1m kullanıldı (perp–spot bazı, perp spread'i, funding 8 saatte bir) — scalp ufkunda funding yalnız 00/08/16 UTC'yi kesen işlemlere düşer; nicelleştirilmedi.
- Maker dolum olasılığı ve maker'ın ters seçilimi (dolduğun limitin aleyhine hareket) modellenmedi; §3'teki örtük aşım bunun ölçeğini (~1 bp) gösteriyor.

---

## 3. İcra gerçekçiliği: Binance 1m vs broker M1, aynı-bar belirsizliği, örtük aşım

### Takeaway
Broker BID M1'in bar-içi aralığı Binance'in **2,3 katı** (medyan 7,3 vs 3,1 bp; korelasyon 0,92) → aynı braket broker'da daha hızlı ve daha sık
"çift dokunuşlu" çözülüyor: 3 bp'de sınıf uyumu %71, 10 bp'de %83, 20 bp'de %88, 50 bp'de %96. Gerçekçi broker icrası (ask giriş/bid çıkış),
"Binance yolu + 1×spread" modelinden 5–10 bp braketlerde long tarafta 0,06–0,1R, 20 bp+'da ≤0,015R daha kötü. Aynı-bar TP+SL oranı Binance'te
5 bp'de %3–12, 10 bp'de %0,5–2,6, 20 bp'de ≤%0,3 (yıla göre); broker'da 5 bp'de %5,9 (Binance %1,1). Ayrıca 1m verisi, sürekli martingale göre uzak
hedefe önce varmayı **sistematik olarak fazla** gösteriyor: örtük seviye-aşımı ≈ **0,9 bp** (yıla göre 0,3–1,4) — "seviyeden dolum" varsayımı
dar-SL'li geometrilere sahte +0,5…+0,8 bp brüt kenar veriyor. Alt-dakika verisi yok; sınırlar aşağıda.

### Cited Findings
**Aralık ve açılış boşluğu (2026-10-05 21:49 → 10-21 00:00 UTC; ortak 21.503 dk)** — [broker_compare.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/broker_compare.json):
Binance 1m aralığı medyan 3,06 bp (p90 8,8), broker 7,31 bp (p90 13,6); oranların medyanı 2,31; aralık korelasyonu 0,919; broker barlarının yalnız %1'inde
aralık < 15 $. Ardışık açılış−kapanış boşluğu: Binance medyan 0,00 bp (p99 0,015), broker 0,06 bp (p99 3,8).

**Aynı giriş dakikalarında braket sonucu** (19.996 giriş, 16 gün, H=60; "kötümser" = aynı bar → SL, "iyimser" = aynı bar → TP, "sezgisel" = açılış hangi uca
yakınsa o önce) — [broker_compare.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/broker_compare.csv):

| bp | yön | sınıf uyumu | TP oranı Bin/Brk | aynı-bar Bin / Brk | EV R Binance kötümser / sezgisel / iyimser | EV R broker kötümser / iyimser | net R Binance+1×S | net R broker gerçekçi |
|---|---|---|---|---|---|---|---|---|
| 3 | L | 0.711 | 0.486 / 0.376 | 0.035 / 0.227 | −0.028 / +0.006 / +0.043 | −0.248 / +0.207 | −0.635 | −0.699 |
| 5 | L | 0.756 | 0.492 / 0.456 | 0.011 / 0.059 | −0.012 / −0.000 / +0.010 | −0.089 / +0.030 | −0.376 | −0.482 |
| 5 | S | 0.756 | 0.493 / 0.485 | 0.011 / 0.059 | −0.010 / +0.000 / +0.012 | −0.031 / +0.088 | −0.374 | −0.440 |
| 10 | L | 0.828 | 0.463 / 0.470 | 0.001 / 0.006 | −0.012 / −0.011 / −0.010 | −0.044 / −0.032 | −0.194 | −0.254 |
| 10 | S | 0.828 | 0.469 / 0.507 | 0.001 / 0.006 | +0.010 / +0.011 / +0.012 | +0.032 / +0.043 | −0.172 | −0.189 |
| 20 | L | 0.876 | 0.347 / 0.383 | 0.000 / 0.000 | −0.023 (hepsi) | −0.035 | −0.114 | −0.128 |
| 20 | S | 0.876 | 0.368 / 0.416 | 0.000 / 0.000 | +0.023 (hepsi) | +0.034 | −0.068 | −0.068 |
| 50 | L | 0.959 | 0.100 / 0.115 | 0 / 0 | −0.031 | −0.037 | −0.068 | −0.074 |
| 50 | S | 0.959 | 0.133 / 0.155 | 0 / 0 | +0.031 | +0.037 | −0.005 | −0.001 |

(L/S farkı pencerenin aşağı sürüklenmesi; kıyas aynı yön içinde okunmalı.)

**Aynı-bar belirsizliği, 5 yıl Binance** (simetrik braket, zaman stopu yok; yıl başına oran) — [tau_dist.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/tau_dist.csv):
3 bp %7–26 · 5 bp %2,8–12,0 · 10 bp %0,5–2,6 · 20 bp %0,1–0,3 · ≥30 bp ≤%0,2. En yüksek değerler 2021–22'de (yüksek oynaklık) ve 12–13 UTC
veri saatlerinde (20 bp'de %0,3–0,4 vs gece %0,1) — [by_group.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/by_group.csv).
Simetrik braketin brüt beklentisi tam olarak −(aynı-bar oranı)R çıkıyor (5 bp −0,054R ↔ %5,4; 10 bp −0,011R ↔ %1,1) — [grid_sym_year.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/grid_sym_year.csv).

**Ön-dokunuş olasılığı vs sürekli martingal (dolum varsayımından bağımsız)** — [gamblers_ruin.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/gamblers_ruin.csv), [07_gamblers_ruin.py](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/07_gamblers_ruin.py):

| TP/SL | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | tümü |
|---|---|---|---|---|---|---|---|
| 10/5 | %35.4 vs 33.3 (ov 1.07) | %34.5 (0.59) | %35.4 (1.04) | %36.0 (1.42) | %35.8 (1.30) | %35.5 (1.14) | %35.4 vs 33.3 (ov 1.09) |
| 20/5 | %22.0 vs 20.0 (0.89) | %21.1 (0.46) | %22.0 (0.90) | %23.1 (1.42) | %22.7 (1.23) | %22.5 (1.12) | %22.2 vs 20.0 (1.00) |
| 50/10 | %17.3 vs 16.7 (0.58) | %17.0 (0.34) | %17.5 (0.72) | %18.2 (1.41) | %17.6 (0.88) | %17.8 (1.02) | %17.6 vs 16.7 (0.83) |
| 100/5 | %5.27 vs 4.76 (0.60) | %5.00 (0.27) | %5.40 (0.76) | %5.92 (1.38) | %5.65 (1.06) | %5.57 (0.95) | %5.48 vs 4.76 (0.85) |

"ov" = P = (SL+ov)/(TP+SL+2·ov) eşitliğini sağlayan simetrik örtük aşım (bp). 12 yıl×yön hücresinin 12'sinde aynı işaret; simetrik 5/5 ve 10/10'da fark ≈0.

**Neden ve doğrulama:**
- Bar-içi yapıyı koruyup seri bağımlılığı yok eden karıştırma (E42 yöntemi) etkiyi **yeniden üretiyor** (ör. 2025 100/5: gerçek L +0,75 / S +0,83 bp,
  sentetik +1,04 / +1,08 bp); 1m getiri varyans oranları < 1 (VR15 0,94–0,97, VR60 0,94–0,95; ilk-gecikme otokorelasyonu −0,012…+0,011) → kısa vadeli
  momentum değil — [martingale_check.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/martingale_check.csv), [variance_ratio.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/variance_ratio.csv)
- Dakikada 60 alt-adımlı ayrık Brown yolunda motor, alt-adım "gerçek" sonucuna göre dar-SL'li geometrilerde L+S toplamında +0,3…+0,6 bp iyimser
  (SL seviyeden doluyor, gerçek yolda ilk aşan fiyat seviyenin ötesinde); kalın kuyruklu t(3) alt-adımlarda fark büyüyor. Limit-TP ağırlıklı geometride
  (5/100) motor ≈ gerçek — [brownian_check.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/brownian_check.csv)

### Inferences
- **Belirsizlik sınırı (alt-dakika verisi olmadan):** simetrik braket için EV yanlılığı ∈ [−a, +a]·R (a = aynı-bar oranı; kötümser ↔ iyimser fark 2a);
  sezgisel tahmin ~ortada. Bir stratejinin girişleri yüksek oynaklık dakikalarında yoğunsa a rastgele girişten büyüktür → stratejinin KENDİ a'sı raporlanmalı.
  Kenar hedefi 0,03–0,05R iken a ≤ %0,5 olmalı ⇒ 2023+'da braket ≥ ~10–15 bp (≥1×ATR5m), 2021–22 rejiminde ≥ 20 bp. Altında **1s veri** şart.
- **Örtük aşım (~1 bp)** bp-düzeyinde ikinci bir sürtünmedir ve Pepperstone spread'iyle (1,85 bp) aynı mertebededir. Pratik karşılığı: stop emri
  seviyenin ~1 bp ötesinde dolar; limit (maker) emir seviyede dolar ama dolduğu anda adil fiyat ~1 bp aleyhtedir (ters seçilim). Bu yüzden
  (i) SL'lere ≥1 bp kayma ekle (Binance; CFD'de hızlı dakikalarda spread p90 ~42 $ ≈ 5 bp), (ii) her strateji **aynı geometrinin rastgele-giriş
  plasebosuna** karşı ölçülmeli, sıfıra karşı değil — dar-SL/geniş-TP tasarımlarda plasebo kendisi +0,05…+0,15R gösterir.
- Binance 1m ile kurulup broker'da koşacak CFD scalp'leri 15 bp altında sistematik olarak iyimser (broker'ın daha geniş bar-içi gürültüsü SL'i daha sık
  tetikliyor; E47'nin nicel karşılığı). 20 bp üstünde iki kaynak ≤0,015R farkla örtüşüyor → Binance 5 yıllık seri ≥20 bp braketler için güvenilir vekil.
- 16 günlük kıyas tek rejim (Ekim 2026, aşağı sürüklenme, ATR düşük); yüksek oynaklıkta broker/Binance farkı muhtemelen büyür (spread genişlemesi) —
  bu yüzden broker katsayıları alt sınır olarak okunmalı.

### Gaps
- Alt-dakika (1s veya tick) BTC verisi yerelde yok. Binance spot 1s klines `data.binance.vision` üzerinden indirilebilir; indirme izin gerektirdiği için
  yapılmadı. Bu veriyle (a) aynı-bar sıralaması, (b) örtük aşımın stop kayması mı yoksa veri yapısı mı olduğu doğrudan ölçülebilir.
- Broker tick verisi (kutuda 14 gün) yalnız özet olarak alınmıştı; tick düzeyinde stop dolumu simülasyonu yapılamadı. Gerçek BTC dolumu (demo'da
  hiç BTC işlemi yok) ölçülmedi.
- Örtük aşımın 2022'de düşük (0,3–0,6), 2024'te yüksek (1,4) olmasının nedeni (fiyat seviyesi/$ tick boyutu, likidite) araştırılmadı.

---

## 4. Kaldıraç ve risk matematiği

### Takeaway
Kaldıraç girdi değil **çıktıdır**: notional/özsermaye = risk% / SL%. 20 bp SL ve %0,5 risk 2,5× notional demektir (Pepperstone 1:20 marjinle özsermayenin
%12,5'i marjin; stop-out ~37,5% uzakta). Kaldıraç beklentiyi R cinsinden değiştirmez — ücretler notional'la ölçeklendiğinden maliyet/R aynı kalır —
ama varyansı ve iflas olasılığını büyütür: kenar 0 iken %1 risk/işlem, günde 20 işlemle bir yılda %87 olasılıkla ≥%50 düşüş; +0,03R kenarla bile
%2 risk %97,5 olasılıkla ≥%50 düşüş. Makul aralık **%0,25–0,5/işlem** (kenar kanıtlanana kadar ≤%0,25); Kelly (1:1'de f* = kenar) +0,03R için %3 —
belirsiz kenarla tam Kelly kabul edilemez. Ayrıca gerçek perakende Pepperstone kripto kaldıracı **2:1**'dir (demo 1:20 gösteriyor), bu da dar SL'li
scalp'te risk/işlemi tavanlar (10 bp SL → en fazla %0,2).

### Cited Findings
**Pozisyon boyu ve marjin** (Pepperstone BTCUSD demo: marjin %5 = 1:20; perakende stop-out marjin seviyesi %50 → tek pozisyonda stop-out mesafesi d* = 1/L − 0,025) — [leverage_table.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/leverage_table.csv):

| SL bp | risk %/işlem | notional/özsermaye L | marjin (özs. %) @1:20 | stop-out mesafesi (bp) | stop-out/SL | Binance taker ücreti (özs. %/işlem) | PEP spread (özs. %/işlem) |
|---|---|---|---|---|---|---|---|
| 5 | 0.25 | 5.0 | 25 | 1750 | 350× | 0.50 | 0.09 |
| 5 | 1.0 | 20.0 | 100 | 250 | 50× | 2.00 | 0.37 |
| 10 | 0.5 | 5.0 | 25 | 1750 | 175× | 0.50 | 0.09 |
| 20 | 0.25 | 1.25 | 6 | 7750 | 388× | 0.13 | 0.02 |
| 20 | 0.5 | 2.5 | 12.5 | 3750 | 188× | 0.25 | 0.05 |
| 20 | 1.0 | 5.0 | 25 | 1750 | 88× | 0.50 | 0.09 |
| 50 | 0.5 | 1.0 | 5 | 9750 | 195× | 0.10 | 0.02 |
| 50 | 1.0 | 2.0 | 10 | 4750 | 95× | 0.20 | 0.04 |
| 100 | 1.0 | 1.0 | 5 | 9750 | 98× | 0.10 | 0.02 |

5 bp SL + %2 risk = 40× → 1:20 tavanını aşar (açılamaz).
- Pepperstone MT4/5 perakende: marjin seviyesi < %90 uyarı, < %50 stop-out — [Pepperstone destek](https://pepperstone.com/en/support/when-does-a-margin-call-and-stop-out-occur)
- Pepperstone kripto CFD perakende kaldıracı 2:1 (ASIC 29 Mart 2021 müdahalesi; CySEC/AB varlığı aynı, profesyonel olmadıkça değişmez); hesap başına
  kripto notional tavanı 200.000 $ (arama özeti) — [Pepperstone ASIC product intervention](https://pepperstone.com/au/asic-product-intervention), [Pepperstone kaldıraç (AB)](https://pepperstone.com/en-eu/support/what-leverage-can-i-trade-with-pepperstone/), [Pepperstone kripto](https://pepperstone.com:443/en-au/markets-and-symbols/cryptocurrencies);
  demo hesap 1:200 hesap / %5 sembol marjini gösteriyor — [02_veri_ve_broker.md](file:///Users/melihcanodacioglu/Desktop/panel/research_notes/BTC%20trader%20bot%20kenar%20ara%C5%9Ft%C4%B1rmas%C4%B1/02_veri_ve_broker.md)
- 2:1 tavanında azami risk/işlem = 2 × SL%: SL 10 bp → %0,2; 20 bp → %0,4; 30 bp → %0,6; 50 bp → %1,0 (hesap).
- **Binance izole marjin (açıklayıcı):** tasfiye ≈ 1/kaldıraç − MMR; MMR %0,4 varsayımıyla 20× → 460 bp, 50× → 160 bp, 100× → 60 bp, 125× → 40 bp — [binance_isolated_liq.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/binance_isolated_liq.csv).
  Binance'in güncel BTCUSDT kademe tablosu bulunamadı; Pionex'in BTCUSDT örneğinde en üst kademe MMR %0,50, 100× — [Pionex (Binance değil)](https://intercom.help/pionex/en/articles/14616420-maintenance-margin).

**Monte Carlo** (bağımsız işlemler, sabit kesirli bileşik risk, 365 gün, 4.000 yol; 1:1 geometride WR = (1+kenar)/2) — [mc_risk.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/mc_risk.csv):

| net kenar R | WR | işlem/gün | risk % | Kelly % | P(yıl zararı) | maxDD medyan | maxDD p95 | P(DD≥%20) | P(DD≥%50) |
|---|---|---|---|---|---|---|---|---|---|
| −0.05 | 0.475 | 20 | 0.25 | — | 1.00 | 0.63 | 0.73 | 1.00 | 0.93 |
| −0.05 | 0.475 | 5 | 0.5 | — | 0.99 | 0.43 | 0.58 | 0.98 | 0.23 |
| 0 | 0.50 | 20 | 0.25 | 0 | 0.53 | 0.22 | 0.39 | 0.60 | 0.004 |
| 0 | 0.50 | 20 | 0.5 | 0 | 0.57 | 0.41 | 0.64 | 0.99 | 0.25 |
| 0 | 0.50 | 20 | 1.0 | 0 | 0.66 | 0.68 | 0.88 | 1.00 | 0.87 |
| 0 | 0.50 | 20 | 2.0 | 0 | 0.80 | 0.93 | 0.99 | 1.00 | 1.00 |
| +0.03 | 0.515 | 20 | 0.25 | 3 | 0.008 | 0.12 | 0.20 | 0.05 | 0.000 |
| +0.03 | 0.515 | 20 | 0.5 | 3 | 0.012 | 0.23 | 0.37 | 0.73 | 0.002 |
| +0.03 | 0.515 | 20 | 1.0 | 3 | 0.018 | 0.43 | 0.62 | 1.00 | 0.25 |
| +0.03 | 0.515 | 20 | 2.0 | 3 | 0.044 | 0.70 | 0.89 | 1.00 | 0.975 |
| +0.03 | 0.515 | 5 | 0.5 | 3 | 0.12 | 0.16 | 0.28 | 0.24 | 0.000 |
| +0.03 | 0.515 | 5 | 1.0 | 3 | 0.15 | 0.29 | 0.49 | 0.91 | 0.04 |
| +0.05 | 0.525 | 20 | 0.5 | 5 | 0.000 | 0.18 | 0.28 | 0.36 | 0.000 |
| +0.05 | 0.525 | 20 | 1.0 | 5 | 0.000 | 0.34 | 0.50 | 1.00 | 0.045 |
| +0.05 | 0.525 | 20 | 2.0 | 5 | 0.000 | 0.59 | 0.77 | 1.00 | 0.84 |
| +0.10 | 0.55 | 20 | 0.5 | 10 | 0.000 | 0.12 | 0.18 | 0.02 | 0.000 |
| +0.10 | 0.55 | 20 | 1.0 | 10 | 0.000 | 0.23 | 0.33 | 0.83 | 0.000 |
| +0.10 | 0.55 | 20 | 2.0 | 10 | 0.000 | 0.43 | 0.57 | 1.00 | 0.18 |

1,5:1 geometride (WR = (1+kenar)/2,5) aynı kenarla düşüşler daha derin: +0,03R, 20/gün, %0,5 risk → maxDD medyan %30, P(DD≥%50) %3,6; %1 risk → %53 / %62.
Kenar 0 ve %1 riskte medyan yıl sonu özsermaye 0,71 (oynaklık sürüklenmesi: kenarsız stratejide risk arttıkça medyan sonuç düşer).

**Kenarı istatistiksel olarak görmek için gereken işlem** (2σ, bağımsız varsayım) — [edge_detection_n.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/edge_detection_n.csv):
1:1'de +0,03R → 4.440 işlem (20/gün: 222 gün; 5/gün: 888 gün), +0,05R → 1.595, +0,10R → 396; 1,5:1'de +0,03R → 6.729.

### Inferences
- **Kaldıraç kenar yaratmaz:** her satırda beklenti R'de sabit; kaldıraç yalnız risk %'sini (dolayısıyla varyansı) ölçekler. Ücret notional'la büyüdüğü
  için özsermaye cinsinden maliyet = risk% × (c/SL): Binance taker'da 20 bp SL, %0,5 risk → işlem başına %0,25 özsermaye ücret; günde 20 işlemde
  **%5/gün**. "Yüksek kaldıraçla küçük hareketten kâr" sezgisi tam olarak bu maliyet duvarına çarpar.
- Stop-out/tasfiye, risk-tabanlı boyutlandırmada scalp SL'lerinden çok uzaktadır (Pepperstone 1:20'de 20 bp SL/%1 riskte 88×); asıl kaldıraç riski
  (a) stopun boşlukta/flash-crash'te dolmaması, (b) Binance'te izole 100×+ seçilip tasfiyenin (40–60 bp) SL ile aynı mesafeye düşmesi,
  (c) eşzamanlı çok pozisyon. Tasfiye mesafesi her zaman SL'in ≥ 3–5 katı olmalı.
- **Kelly:** 1:1'de f* = kenar (ör. +0,03R → %3/işlem). Kenarın kendisi belirsiz (projedeki "kenarların" çoğu ileride sıfıra/negatife döndü) →
  tam Kelly, kenar 0 çıkarsa P(DD≥%50) ≈ 1 demektir. Kenar güven aralığının alt sınırına göre ¼ Kelly bile +0,03R'de ~%0,75 eder; MC'de %0,5 risk
  P(DD≥%20) %73 veriyor → psikolojik ve operasyonel olarak da sınırda.
- **Makul risk/işlem:** kanıtlanmamış/gölge aşamasında ≤%0,25 (kenar 0 iken 20 işlem/gün ile P(DD≥%50) %0,4); kart geçmiş ve canlı kanıtlı
  ≥+0,05R kenarla %0,5; %1 ancak ≥+0,10R kanıtlı kenarda ve eşzamanlı ≤1 pozisyonla. Pepperstone perakendede 2:1 tavanı 10–20 bp SL'de bu
  aralığı zaten %0,2–0,4'e sınırlar.
- MC bağımsız işlem varsayar; scalp işlemleri saat/rejim kümelenmesiyle koreledir (E6/E9) → gerçek düşüşler tablodakinden derindir.

### Gaps
- Gerçek hesap türü (perakende 2:1 mı, Pro/offshore 1:20 mi) ve BTC CFD komisyonu doğrulanmadı; demo değerleri canlıyla aynı olmayabilir.
- Binance BTCUSDT güncel kaldıraç/MMR kademe tablosu kaynağı bulunamadı (yalnız Pionex örneği); tasfiye mesafeleri açıklayıcıdır.
- Swap/funding scalp ufkunda ihmal edildi; rollover'ı (yaz 21:00 / kış 22:00 UTC) veya funding saatini (00/08/16 UTC) kesen pozisyonlar için eklenmeli (E46, E50).

---

## 5. Scalp tasarım kuralları (sentez — strateji test edenler için bağlayıcı öneri)

### Takeaway
BTC scalping yalnız dar bir bölgede ekonomik olarak tanımlıdır: **Pepperstone'da SL ≥ 20 bp (stres ≥ 28 bp) ≈ 1,2–2×ATR5m, ufuk 10–60 dk;
Binance'te yalnız maker girişle SL ≥ 40 bp**. Taker-taker Binance scalp'i yoktur. Brüt kenar hedefi ≥0,15R, aynı-geometri plasebosunun üstünde
ölçülmeli; risk/işlem ≤%0,25 (gölge) → ≤%0,5 (kanıtlı).

### Cited Findings
- Asgari braket, τ ve fırsat sayıları: §2 tabloları — [frontier_min_bracket.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/frontier_min_bracket.csv)
- Belirsizlik ve örtük aşım: §3 — [gamblers_ruin.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/gamblers_ruin.csv), [broker_compare.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/broker_compare.csv)
- Kaldıraç/MC: §4 — [mc_risk.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021/feasibility/out/mc_risk.csv)

### Inferences
**A. Asgari hedef/stop (maliyet ≤ %10 R; 2023+ rejimi, ATR5m ≈ 12–16 bp):**

| venue | RT maliyet | asgari SL (≤%10 R) | ≈ATR5m | medyan τ | sert alt sınır (≤%20 R) |
|---|---|---|---|---|---|
| Pepperstone CFD (%0,0185) | 1,85 bp | **19 bp** | 1,1–1,6× | 11–22 dk | 9 bp (önerilmez) |
| Pepperstone stres ×1,5 | 2,78 bp | **28 bp** | 1,7–2,3× | 24–44 dk | 14 bp |
| Pepperstone sabit 15 $ | 1,45–2,3 bp (2024–26) / 5–6,5 bp (2022–23) | 15–23 bp / 54–65 bp | — | — | — |
| Binance maker/maker | 4 bp | **40 bp** | 2,4–3,3× | 47–84 dk | 20 bp |
| Binance maker giriş + taker çıkış | 7 bp | **70 bp** | 4,3–5,8× | 2–3,5 s | 35 bp |
| Binance taker/taker | 10 bp | **100 bp** | 6–8× | 4–6 s (scalp değil) | 50 bp |

Bu sınırlara ek olarak SL dolumuna **≥1 bp kayma** (Binance) / hızlı dakikada ~5 bp (CFD) eklenmeli; TP'yi limit (maker) varsay ama dolum
olasılığını ve ~1 bp ters seçilimi hesaba kat.

**B. Ufuk ve saatler:** 10–60 dk zaman stopu (zaman stopu R maliyetini değiştirmez, belirsizliği ve gece/funding/rollover maruziyetini azaltır;
projede tek konvansiyona dayanıklı çıkış). Tercih: **13–20 UTC hafta içi** ve **RV24h ≥ %35** (maliyet/R en düşük, 20 bp'de τ 7–14 dk). Kaçın:
hafta sonu (ATR %40 dar → maliyet/R ~1,7×, τ 2×), RV<%35 dönemleri (maliyet/R 2×, τ 38 dk), 03–11 UTC, broker'ın günlük 20:59–21:01 UTC (yaz) /
Cuma kapanışı ve rollover'ı kesen pozisyonlar (E46). Saat-of-gün yön etkisi yok (BTC-M03) — saat yalnız maliyet/hız filtresidir.

**C. Braket ölçekleme:** bp yerine **ATR5m (veya RV) ile ölçekle** ve sonuçları **yıl bazında** raporla — 2021 ile 2025 arasında ATR5m yarıya indi.
Aynı anda bp karşılığını yaz (E50): bir kural R'de pozitif ama bp'de ≈0 ise kenar yoktur.

**D. Veri çözünürlüğü:** 5 yıllık Binance 1m, braket ≥ 15–20 bp (≥1×ATR5m) için yeterli (aynı-bar ≤ %0,3, broker ile ≤0,015R fark).
Braket < 10 bp (2023+) / < 20 bp (2021–22) → **1s veya tick verisi şart**; o olmadan bu bölge sınanmamalı. CFD'de koşacak her kural broker M1
(16 gün) ile ayrıca teyit edilmeli; 5m/15m bar ile çözülen sonuç kabul edilmez (WR şişmesi: 5m'deki "kazançların" %27'si 1m'de SL-önce).

**E. Belirsizlik ve dolum kuralları:** aynı barda TP+SL → SL (kötümser) ana sonuç; ayrıca iyimser ve OHLC-sezgisel sürümleri rapor et; stratejinin
**kendi** aynı-bar oranı a > %0,5 ise sonuç geçersiz (alt-dakika gerekir). Stop dolumu min(SL, açılış) − kayma; "stoptan dolum" ve gecikmesiz
kapanış yasak (Reflex trailing ve BE motoru dersleri). Giriş = sonraki 1m açılışı + spread (E7).

**F. Kıyas tabanı:** her hücre **aynı geometri + aynı saat/yıl rastgele-giriş plasebosuna** (L ve S ayrı) karşı ölçülür; sıfıra karşı değil.
Dar-SL/geniş-TP geometrilerde plasebo brütü +0,05…+0,15R (örtük aşım), simetriklerde −a. Örtüşen girişler epizod-bastırılmış/tek-pozisyon
zincirine indirgenir (E6/E9); n yerine bağımsız gün sayısı.

**G. Kenar çıtası:** net pozitiflik için brüt kenar ≥ maliyet/R + ~0,05R; Pepperstone 20 bp'de ≥ ~0,15R, Binance maker 40 bp'de ≥ ~0,15R.
Projenin bugüne kadarki dürüst kısa-vade kenarları 0,03–0,1R; bu çıta bir **ön-filtre** olmalı — keşifte bunun altındaki hücreler elenir.

**H. Risk/işlem ve kaldıraç:** kaldıracı seçme, risk%'yi seç: notional = özsermaye × risk% / SL%. Gölge/yeni: ≤%0,25; kanıtlı (kart LIVE + canlı ≥100 işlem)
≥+0,05R: %0,5; %1 yalnız ≥+0,10R ve tek pozisyonla. Pepperstone perakendede 2:1 → risk ≤ 2×SL%. Binance izolede tasfiye mesafesi ≥ 3–5×SL
(fiilen ≤20–25× kaldıraç). Günlük kayıp freni (ör. −3R) ve eşzamanlı pozisyon sınırı zorunlu; MC'deki düşüşler bağımsızlık varsaydığı için alt sınırdır.

**I. Doğrulama süresi:** +0,03R'lik bir kenarı 2σ ile görmek için ~4.400 bağımsız işlem gerekir (20/gün → ~7 ay gölge). Kısa gölge dönemleri
(<1.500 işlem) yalnız ≥+0,05R iddialarını sınayabilir.

### Gaps
- Bu kurallar rastgele giriş fiziğinden türetildi; herhangi bir BTC scalp sinyalinin brüt kenarı burada ölçülmedi (bu not yalnız "nerede aranabilir"i çiziyor).
- Örtük aşımın mekanizması (gerçek stop kayması mı, 1m bar yapısının ürünü mü) alt-dakika verisi olmadan ayrıştırılamadı; kural (≥1 bp kayma + plasebo)
  her iki durumda da güvenli tarafta.
- Pepperstone canlı hesap kaldıraç sınıfı, BTC komisyonu ve tarihsel spread doğrulanmadan PEP_PCT ile PEP_FIX15 arasındaki fark (2022–23'te 3,5×) çözülemez.
