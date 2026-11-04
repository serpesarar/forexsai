# fam_turev — Türev konumlanma sinyalleriyle BTC scalp — ÖN KAYIT

Yazılış: 2026-10-22, **hiçbir sonuç (getiri/R) hesaplanmadan önce.** Önceden yalnız özellik dağılımlarına bakıldı
(funding seviyesi yüzdelikleri: settled funding p5 −0,45 bp, p10 −0,16, p50 +0,66, p80/p90 +1,00 (%31'i tam 1 bp),
p95 +1,79, p99 +4,6 bp; liq vekil sayıları veri notunda). Bu dosya değiştirilmez; değişiklik gerekirse sona tarihli
"EK-n" olarak ve gerekçesiyle eklenir.

Okunan girdiler: `research_notes/BTC scalping strateji araştırması/01,02,03`, `docs/KAPI_KAYIT_DEFTERI.md` §0, §1 (E1–E50),
§2.11 (BTC-S05/S06 OHLCV-şok fade'leri; BTC-M06 funding saati), §3.

## 0. Defter kontrolü (3. KURAL)
- BTC-S05/S06: 60 dk ±3,5σ fiyat şoku fade (yalnız OHLCV) → S05 X (−0,021R), S06 X/veto (−0,194R, "coşku dönmez").
  Buradaki DV02 **yeni tanım**: şok + **OI düşüşü (zorunlu kapanış) teyidi** + 1–5 dk ölçek (S05/S06 60 dk, 1–4 s tutuş idi).
- BTC-M06: funding saati ±15 dk koşulsuz L/S → X. Buradaki DV03c/d **yeni tanım**: funding **işaretine/seviyesine koşullu** yön.
- OI, premium/baz, L/S oranları için defterde önceki sınama YOK (yeni veri).
- Uyulan tuzaklar: E6/E9 (epizod bastırma, tek-pozisyon zinciri), E7 (sonraki 1m açılışı + maliyet), E15/E33 (taban saat×yıl, sonuçtan
  bağımsız), E24/E30 (max-z seçim düzeltmesi), E40 (ısınma; n_DISC<50 hücre seçilemez), E41 (asimetride iki kolun mutlak işareti),
  E43 (yönsüz taban: plasebo aynı yön), E48 (kalıcı rejim sinyali → dairesel kaydırma plasebosu), E49 (mod a priori ya da iki mod
  birlikte max-z'ye girer), E50 (R ve bp birlikte).

## 1. Veri, nedensellik, dışlamalar
- Tek dosya: `research/btc_scalp_20261021/data/btc_scalp_1m.parquet` (+ aynı klasördeki `metrics_5m_effective.parquet` yalnız OI
  dizisi ve 5 dk vekil ara sütunları için; aynı `eff_ts`/`avail_ts` nedensellik kuralıyla).
- **İşlem yolu (TP/SL/zaman çözümü): Binance SPOT 1m OHLC** (`spot_*`) — Pepperstone CFD bir spot endeksini izler ve fizibilite motoru da
  spot kullandı. Sinyaller perp/metrics/premium/funding'den.
- Satır `ts` değerleri ts+60 s'de bilinir → karar barı t, **giriş = t+1 açılışı**.
- Metrics: satır yalnız `eff_ts + 1 dk ≤ karar barı kapanışı` iken kullanılır (2024-03-04 damga değişimi `eff_ts`'de çözülmüş). 5 dk
  metrics tabanlı her olayın karar barı = `eff_ts` dakikası (kapanışı `eff_ts+1 dk = avail_ts`), giriş `eff_ts+1 dk` açılışı.
  Sağlamlık: en iyi adaylar için **+1 dk ek gecikme** (giriş `eff_ts+2 dk`) ayrıca raporlanır (veri notu: 2025-08→2026-03 alt-dakika kayması).
- Funding: `funding_pred_running` (kendi nedensel tahminimiz, bar dahil) ve `funding_rate_last` (uzlaşma ≤ bar kapanışı).
  `funding_last_estimated=1` (Ekim 2026, yalnız BLIND) yalnız `funding_rate_last` kullanan DV03d'yi etkiler → BLIND onunla ve onsuz raporlanır.
- Dışlanan dakikalar (BAD): 2023-03-24 11:28–14:00 UTC; `spot_missing=1`; `spot_zero_vol=1`; `perp_zero_vol=1`. Pencere [e, e+H)
  veya karar barı BAD ile kesişen girişler atılır.
- Broker rollover: NY 17:00 → yaz 21:00 / kış 22:00 UTC (ABD DST). Pozisyon **20:58 / 21:58 UTC açılışında zorla kapanır** (son bar 20:57/21:57,
  çıkış o barın kapanışı). Giriş dakikası e ∈ [20:58, 21:02) yaz / [21:58, 22:02) kış → giriş yok.
- Isınma: tüm kayan istatistikler yalnız geçmiş (`shift(1)`), min_periods belirtilen gibi; ısınmada sinyal yok.

## 2. Dönemler (sabit)
DISC 2021-06-01 → 2023-12-31 · OOS 2024-01-11 → 2025-06-30 · BLIND 2025-07-01 → 2026-10-20 (giriş zamanına göre).
2024-01-01 → 01-10 arası hiçbir bölmeye girmez. POST = OOS ∪ BLIND. Parametre/hücre seçimi yalnız DISC'te.

## 3. Geometri, icra, maliyet (tüm hücreler)
- SL mesafesi s = max(19 bp, 1,1 × ATR14(5m)) — ATR14(5m) spot, girişten önce tamamlanmış son 14 adet 5 dk kova (fizibilite `lib.atr_5m` tanımı).
- TP = r × s, r ∈ {1,0; 1,5; 2,0}. Zaman stopu H ∈ {15; 60} dk (DV03c'de H = 35 sabit). Rollover kesiyorsa H kısalır.
- Giriş fiyatı = open[e]. İlk dokunuş [e, e+H) içindeki 1m high/low ile (giriş barı dahil).
- SL dolumu boşluk-duyarlı: long min(SL, open[hit]) / short max(SL, open[hit]), üstüne **kayma 1 bp**; çıkış dakikasının |log(c/o)|
  değeri DISC'teki p99'un üstündeyse **5 bp**. TP limit, seviyeden dolar. Zaman çıkışı: son barın kapanışı (kaymasız).
- **Aynı barda TP+SL → SL** (ana/kötümser). Ek: iyimser (→TP) ve OHLC-sezgisel (açılış hangi seviyeye yakınsa o önce).
  Stratejinin kendi aynı-bar oranı **< %0,5** olmalı; değilse hücre geçersiz.
- R = brüt bp / s. Maliyet (gidiş-dönüş, bp; net R = (brüt bp − maliyet − kayma)/s):
  **PEP 1,85 (birincil)** · PEP_STRESS 2,78 · PEP_FIX15 = 15 $ / giriş fiyatı · BIN_MAKER 4 · BIN_TAKER 10. Funding/swap: tutuş ≤ 60 dk ve
  rollover öncesi kapanış → swap 0; perp funding (yalnız Binance varyantları, uzlaşmayı kesen pozisyonlar) ihmal edildi (not edilir).
- "İyimser icra" (kart 5): giriş = karar barı kapanışı (Binance'te ≈ sonraki açılış, boşluk medyanı 0), maliyet 0, kayma 0, aynı bar → TP.

## 4. Olay üretimi ve epizod bastırma
- Olay tabanlı hücreler: aynı hücrenin bir önceki tetiğinden itibaren **60 dk** içinde yeni tetik sayılmaz (epizod).
- Kalıcı rejim hücreleri (DV03a, DV05): **saatlik ızgara** — karar barı her saatin :00 barı, giriş :01; koşul o barda sağlanıyorsa olay
  (H ≤ 60 olduğundan aynı hücrede örtüşme yok).
- Tek-pozisyon (kart 6): hücrenin olayları zaman sırasıyla; açık pozisyon varken gelen olay atlanır.

## 5. Hipotezler (aile = aşağıdaki tüm hücreler; hepsi max-z düzeltmesine girer)
Notasyon: z_P = fiyat değişiminin kendi geçmiş std'sine bölümü (merkezsiz), z_OI = OI değişiminin merkezli z'si; kayan pencereler
30 gün (5 dk satırda 8.640, min 2.000; 1m'de 43.200, min 10.000), `shift(1)`.

### DV01 — OI × fiyat dörtlüleri (W ∈ {15, 60} dk, k ∈ {1,5; 2,5})
5 dk metrics satırı (eff) başına: dP_W = ln(perp_close[eff−1dk] / perp_close[eff−W−1dk]) ([eff−W, eff) penceresi), dOI_W = OI(eff)/OI(eff−W) − 1
(eff−W satırı ızgarada olmalı). z_P = dP_W / std(dP_W), z_OI = (dOI_W − ort)/std, istatistikler 5 dk satırlarda 30 g, shift(1).
| ID | Dörtlü | Koşul | Mod (a priori beklenti) | Yön |
|---|---|---|---|---|
| DV01a-C / DV01a-R | Fiyat↑ OI↑ (yeni long) | z_P ≥ k ∧ z_OI ≥ k | C devam (a priori) / R dönüş | BUY / SELL |
| DV01b-R / DV01b-C | Fiyat↑ OI↓ (short kapatma) | z_P ≥ k ∧ z_OI ≤ −k | R dönüş (a priori) / C devam | SELL / BUY |
| DV01c-C / DV01c-R | Fiyat↓ OI↑ (yeni short) | z_P ≤ −k ∧ z_OI ≥ k | C devam (a priori) / R dönüş | SELL / BUY |
| DV01d-R / DV01d-C | Fiyat↓ OI↓ (long tasfiyesi) | z_P ≤ −k ∧ z_OI ≤ −k | R dönüş (a priori) / C devam | BUY / SELL |
Her ID: 2 W × 2 k × 6 geometri = 24 hücre (8 ID → 192).

### DV02 — Tasfiye vekili olayları (fade vs follow; long-liq vs short-liq asimetrisi)
| ID | Tetik | Karar anı | Yön |
|---|---|---|---|
| DV02-P5L-F / -P5L-W | 5 dk vekil long-liq (`liq_proxy_long_5m`=1, veri notu P5) | eff | F: BUY (fade) / W: SELL (follow) |
| DV02-P5S-F / -P5S-W | 5 dk vekil short-liq | eff | F: SELL / W: BUY |
| DV02-P1L-F / -W, DV02-P1S-F / -W | 1 dk akış vekili (`liq_flow_*_1m`, P1; OI'siz) | o bar | aynı |
| DV02-P1oL-F / -W, DV02-P1oS-F / -W | 1 dk akış vekili ∧ o dakikayı içeren 5 dk pencerede z_OI ≤ −2 (OI-teyitli zorunlu akış) | eff (OI yayınlanınca) | aynı |
Her ID: 6 geometri (12 ID → 72). Asimetri: long-liq fade − short-liq fade farkı + iki kolun mutlak işaretleri (E41).
Ön beklenti: short-liq fade (DV02-*S-F) kaybeder ("coşku dönmez", S06).

### DV03 — Funding
fp = `funding_pred_running` (bp). θL ∈ {1,5; 3} bp (kalabalık long), θS ∈ {0 (fp < 0); −1} bp (kalabalık short).
| ID | Tanım | Yön | Hücre |
|---|---|---|---|
| DV03a-L / DV03a-S | Saatlik ızgara, `min_to_next_funding ≤ 450` (pencereye ≥30 dk girilmiş) ∧ fp ≥ θL / fp ≤ θS (kontraryan) | SELL / BUY | 2 θ × 6 geo |
| DV03b-L / DV03b-S | fp ≥ 1,5 bp ∧ 1m spot getirisi ≤ −2×ATR14(1m) (ilk karşı şok, epizod 60 dk) / fp ≤ 0 ∧ getiri ≥ +2×ATR14(1m) | SELL / BUY | 6 geo |
| DV03c-L / DV03c-S | Uzlaşma S öncesi: karar barı S−31 dk, giriş S−30 dk; fp ≥ θL → SELL (öder taraf kapatır) / fp ≤ θS → BUY; H = 35 (S+5'te kapanır) | SELL / BUY | 2 θ × 3 r |
| DV03d-L / DV03d-S | Uzlaşma S sonrası: karar barı S, giriş S+1; yeni uzlaşan oran (`funding_rate_last`) ≥ θL → BUY (rahatlama) / ≤ θS → SELL | BUY / SELL | 2 θ × 6 geo |
(DV03: 2×12 + 2×6 + 2×6 + 2×12 = 72 hücre.) DV03a dairesel kaydırma plasebosu birincil (E48).

### DV04 — Premium / baz
| ID | Tanım | Yön | Hücre |
|---|---|---|---|
| DV04a-H / DV04a-L | zp = (prem_close_bp − ort₁₄₄₀)/std₁₄₄₀ (1m, shift(1), min 1.000); zp ≥ k → SELL (perp pahalı) / zp ≤ −k → BUY; k ∈ {3; 5}; ilk geçiş, epizod 60 dk | SELL / BUY | 2 k × 6 geo |
| DV04b-U / DV04b-D | Perp-öncülü hareket fade: 5 dk spot getirisi r5 (ln c[t]/c[t−5]), z5 = r5/std(r5, 30 g, shift(1)); \|z5\| ≥ 3 ∧ Δbaz₅ = basis_perp_spot_bp[t]−[t−5] hareketle aynı işaretli ve \|Δbaz₅\| ≥ b → fade | U (yukarı): SELL / D: BUY | b ∈ {1; 3} bp × 6 geo |
| DV04c-U / DV04c-D | Spot-öncülü hareket takip: \|z5\| ≥ 3 ∧ Δbaz₅ hareketle ters işaretli ∧ \|Δbaz₅\| ≥ b → takip | U: BUY / D: SELL | b ∈ {1; 3} × 6 geo |
(DV04: 6 ID × 12 = 72 hücre.)

### DV05 — Long/short oranları (kontraryan; eksik dönemler dahil edilmez)
z = log(oran)'ın 5 dk metrics satırlarında 30 g kayan z'si (shift(1), min 2.000 satır); 1m satırlara metrics nedensellik kuralıyla taşınır;
saatlik ızgara.
| ID | Tanım | Yön | Hücre |
|---|---|---|---|
| DV05-TOP-L / -TOP-S | top-trader **pozisyon** oranı (`top_ls_pos`) z ≥ k / z ≤ −k | SELL / BUY | k ∈ {2; 3} × 6 geo |
| DV05-GLB-L / -GLB-S | global **hesap** oranı (`global_ls_count`) z ≥ k / z ≤ −k | SELL / BUY | k ∈ {2; 3} × 6 geo |
| DV05-DIV-B / -DIV-S | ıraksama: top z ≥ +2 ∧ global z ≤ −1 → top yönünde BUY / top z ≤ −2 ∧ global z ≥ +1 → SELL | BUY / SELL | 6 geo |
(DV05: 4×12 + 2×6 = 60 hücre.) top oranları 2021-12 → 2022-12 çoğunlukla NaN → DISC olayları azalır (E40); eksik satırda sinyal yok.

**Aile toplamı: 192 + 72 + 72 + 72 + 60 = 468 hücre, 50 hipotez (ID).**

## 6. Seçim, istatistik ve plasebo
- Hücre istatistiği: net R (PEP) ortalaması; gün-kümeli SE (giriş UTC günü); z = ort/SE.
- **Seçim (DISC):** her ID içinde, n_DISC ≥ 50 ve aynı-bar < %0,5 olan hücrelerden DISC z'si en yüksek olan seçilir. Seçilebilir hücre yoksa ID "değerlendirilemez".
- **Max-z (seçim düzeltmesi):** 500 kopya; her kopyada TÜM ailenin olay zamanları DISC içinde aynı rastgele **tam gün** sayısı (30 gün ≤ D ≤ uzunluk−30)
  kadar dairesel kaydırılır (saat korunur), tüm 468 hücrenin DISC z'si yeniden hesaplanır, maks. alınır. p_sel(ID) = P(null maks ≥ seçilen hücrenin DISC z'si).
  Holm: DISC'te 468 hücrenin tek yönlü p'lerine (normal yaklaşım) ve POST'ta seçilen hücrelerin tek yönlü p'lerine (ID sayısı kadar) ayrı ayrı.
- **Plasebo:** (i) olay tabanlı ID'ler: her olay için aynı **yıl × UTC saati**, aynı yön ve aynı geometri kuralıyla rastgele geçerli giriş dakikası; 500 çekiliş;
  yüzdelik = P(plasebo ort. < strateji ort.). (ii) kalıcı rejim ID'leri (DV03a, DV05; ayrıca hepsi için bilgi amaçlı): koşul serisinin tam gün
  dairesel kaydırması (≥30 gün), 500 kopya. Birincil plasebo: olay tabanlı → (i), kalıcı → (ii).
- **Brüt kenar çıtası:** (strateji brüt R − plasebo brüt R ortalaması) ≥ 0,15R **veya** strateji brüt bp ≥ 2 × 1,85 bp.
- Gün-blok bootstrap 2.000 kopya: P(EV>0) ve %95 GA.

## 7. Canlıya alma kartı (POST üzerinde, seçilen hücre; tam dönem ve yıllık da raporlanır)
1 n ≥ 150 · 2 ort R > 0 ∧ P(EV>0) ≥ %90 · 3 POST'un kronolojik iki yarısı (olay sayısına göre) ≥ 0 · 4 PEP_STRESS'te ort R > 0 ·
5 |iyimser − gerçekçi| ≤ 0,5·|ort R| · 6 tek-pozisyon zincirinde ort R > 0.
Ek: plasebo yüzdeliği ≥ 95 · BLIND ort R > 0 · brüt kenar çıtası · aynı-bar < %0,5.

**Verdikt şeması (tüm kombinasyonlar):**
- **LIVE-aday:** kartın 6/6'sı ∧ plasebo ≥ 95 ∧ BLIND > 0 ∧ brüt kenar çıtası ∧ aynı-bar < %0,5 ∧ POST Holm p < 0,05 ∧ p_sel ≤ 0,10.
- **GÖLGE-aday:** LIVE değil; ama ort R > 0 ∧ P(EV>0) ≥ %90 ∧ kart ≥ 5/6 ∧ plasebo ≥ 90 ∧ BLIND > 0.
- **RED:** diğer her durum (değerlendirilemez dahil).
Raporlanan her hücre: n, WR, ort R, bp, %95 GA, P(EV>0), yarılar, stres, icra farkı, tek-poz, plasebo yüzdeliği, BLIND, yıllık işaretler, işlem/gün.

## 8. Ek sağlamlık (yalnız seçilen hücreler, verdikti değiştirmez — bilgi)
+1 dk metrics gecikmesi; PEP_FIX15/BIN_MAKER/BIN_TAKER net; iyimser/sezgisel aynı-bar; mod aynası (E49); DV02 asimetrisi (E41).

## EK-1 (2026-10-22, olay listesi kurulduktan sonra, HİÇBİR getiri hesaplanmadan önce)
- §5 sonundaki "50 hipotez (ID)" sayım hatasıdır: tanımlı ID sayısı **40** (DV01 8 + DV02 12 + DV03 8 + DV04 6 + DV05 6). Hücre sayısı 468 doğru.
  POST Holm düzeltmesi 40 ID üzerinden yapılır (değerlendirilemeyenler dahil sayılır → muhafazakâr).
- Olay sayıları (`out/event_counts.csv`) bilgi amaçlıdır: fp ≥ 1,5 bp olan saat/uzlaşma 2025-07 sonrasında **hiç yok** → DV03a-L, b-L, c-L, d-L'nin BLIND
  olayı 0 (BLIND ölçütü bu ID'lerde sağlanamaz → tanım gereği en fazla RED/değerlendirilemez). DV05-GLB k3 DISC'te 1/13 olay → seçilemez.
  Bu gözlemler eşik değişikliğine yol açmadı.

## EK-2 (2026-10-22, sonuçlardan SONRA — yalnız açıklama, verdikt değişmedi)
- `04_eval.py` verdiktinde §3'teki "aynı-bar ≥ %0,5 → hücre geçersiz" kuralı POST'ta da uygulandı (ilk koşuda yalnız DISC seçim süzgecindeydi).
  Bu ön kaydın kendi kuralının uygulanmasıdır; etkilediği ID'ler DV02-P5S-F, DV02-P1oS-F, DV04c-U (üçü de başka ölçütlerden de düşüyordu
  ya da DISC'te negatifti).
- `05_diag.py` (taban-üstü brüt kenar, DV02 asimetrisi) ve `06_posthoc.py` (DV03d aynası, baz-öncülüğüne göre ±3σ takip, short-liq takibi)
  sonuçlara bakıldıktan sonra yazıldı → **ön-kayıtsız, yalnız bilgi**; hiçbir verdikt bunlara dayanmaz.
