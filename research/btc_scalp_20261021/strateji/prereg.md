# Ön kayıt — BTC strateji inşası (Core + kol portföyü, scalp icra zamanlaması, kaldıraç)

Yazılış: **2026-10-22 08:00 UTC**, bu klasörde HİÇBİR sonuç üretilmeden önce. Yazan: strateji ajanı (Claude).
Girdi: `research_notes/BTC trader bot kenar araştırması/01–07`, `research_notes/BTC scalping strateji araştırması/01–06`,
`reports/BTC trader bot kenar araştırması.md`, `docs/KAPI_KAYIT_DEFTERI.md` §0–§3 (E1–E50 + notlardaki öneriler).
Kural: aşağıdaki tanımlar, eşikler, seçim ölçütü ve verdikt şeması sonuçlara bakılmadan donduruldu. Sonradan yapılan her
ek "EK-n (sonuç SONRASI)" etiketiyle bu dosyanın sonuna yazılır ve verdikti değiştiremez.

## 0. Dürüstlük çerçevesi (önceden yazılan beklenti)
- Bu çalışma **yeni kenar aramıyor**. Önceki iki turda bulunan adayları DONDURULMUŞ tanımlarıyla birleştiriyor; parametre
  yeniden ayarı YOK. Tek yeni serbestlik derecesi: Core için 8 hücrelik "limit ile giriş zamanlaması" ızgarası (yalnız DISC'te seçilir).
- POST (OOS∪BLIND) bu adayların çoğu için **zaten görülmüş** veridir (C sınıfı kolların bazıları POST'a bakılarak bulundu: E53/T5).
  Bu yüzden POST kartı bu adaylar için bağımsız doğrulama DEĞİLDİR; sonuç en fazla "GÖLGE portföyü + ileri sınama planı" olabilir.
  Portföy her zaman **post-hoc kollarla ve onlarsız** raporlanır.
- BLIND bir önceki turda açıldı ve harcandı (E23). Burada yeniden açılması yeni kanıt sayılmaz; yalnız tutarlılık kontrolüdür.

## 1. Veri ve bölmeler
- Fiyat yolu: Binance spot BTCUSDT 1m (`research/btc_5y_20261021/data/btc_1m.parquet`; `btc_scalp_1m.parquet` içindeki `spot_*`
  ile aynı seri). Akış/baz (OF02, DV04c): `research/btc_scalp_20261021/data/btc_scalp_1m.parquet`. QQQ: `macro_daily.parquet`.
- Dışlama: 2023-03-24 11:28–14:00 UTC; ≥5 dk Binance kesintileri (OF/DV kollarında kendi geçerlilik maskeleriyle).
- Bölmeler (giriş zamanına göre): DISC 2021-06-01→2023-12-31 · OOS 2024-01-11→2025-06-30 · BLIND 2025-07-01→2026-10-20.
  POST = OOS∪BLIND. Seçim (yalnız Core icra ızgarası) yalnız DISC'te.

## 2. Ortak icra modeli (tüm kollar, tüm plasebolar)
- Karar = sinyal barının kapanışı; **giriş = sonraki 1m açılışı** (mid) ± yarım spread (long ask = mid + h).
- Maliyet: taban RT %0,0185 (1,85 bp) → h = 0,5×0,000185×fiyat; stres ×1,5 (2,775 bp); sabit 15 $ RT varyantı; iyimser varyant
  (giriş = sinyal barı kapanışı, spread 0, kayma 0) yalnız kart ölçüt 5 için.
- SL: bid/ask tetik (long: mid_low − h ≤ SL). Dolum boşluk-duyarlı: long min(SL, açılış − h); **ek kayma**: 1 bp, vuruş dakikasının
  |1m log getirisi| DISC %99 yüzdeliğini aşıyorsa 5 bp. TP: limit, seviyeden doluma (kayma yok). **Aynı barda TP+SL → SL.**
  Zaman çıkışı: son barın kapanışı ∓ h.
- Swap: her NY 17:00 rollover geçişinde long −%14/365, short +%2/365 × giriş nominali (gece sayısı = (giriş, çıkış] aralığındaki rollover).
- R = net PnL / dondurulmuş stop mesafesi (her kolun kendi tanımı). Her sonuç ayrıca bp ile raporlanır (E50).
- **Limit giriş (yalnız Core ızgarası):** long limit fiyatı Lp = (O[e] + h) − k×ATR5m. Dolum yalnız mid_low ≤ Lp − h − 1 bp×Lp
  (fiyat limiti ≥1 bp İÇİNDEN geçmeli) ile [e, e+W) içinde; dolum fiyatı = Lp (fiyat iyileşmesi sayılmaz). Dolum dakikasında SL
  tetiklenebilir (aynı-bar kötümser), TP tetiklenemez (bir sonraki dakikadan itibaren). SL/TP mesafeleri piyasa girişindekiyle aynı
  (2×/4×ATR14(H4)), Lp'den ölçülür; zaman stopu (karar + 30×240 dk) değişmez. Dolmazsa: "skip" → işlem yok; "market" → e+W
  dakikasının açılışında piyasa girişi (aynı mesafeler, aynı bitiş).
- ATR5m = son 14 TAMAMLANMIŞ 5m barın TR ortalaması (`feasibility/lib.py::atr_5m`).

## 3. Kollar (dondurulmuş tanımlar; kaynak not/kod)
| ID | Kol | Tanım (aynen) | Sınıf / kaynak | Ön-kayıtlı mı? |
|---|---|---|---|---|
| S1 | **CORE** = BTC-T03 H4D20-T-L | UTC H4 barı kapanışı ≥ önceki 20 H4 barın en yükseği ∧ son tamamlanmış D1 kapanışı > EMA200(D1); BUY; SL 2×ATR14(H4, Wilder), TP 4×ATR14, zaman stopu karar+30 H4 bar; tek pozisyon | B — `fam_trend/run_trend.py` | DISC-seçili hücre (prosedür ön-kayıtlı) |
| S2 | MAX10 = BTC-T02 MX10-L-1d | D1 kapanışı = son 10 D1 kapanışının en yükseği → ertesi 00:00 UTC BUY; felaket SL 2×ATR14(D1); TP yok; 24 s sonra zaman çıkışı | B− — `fam_trend` | evet (★ birincil) |
| S3 | QB = BTC-M02 | her gün rollover+1 dk (NY 17:01) BUY → 22:59 UTC barının kapanışında çık. R paydası ATR14(1h) (son kapanmış 1h, basit ortalama). Dondurulmuş hâli stopsuz. **Bot biçimi (sunucu SL zorunlu):** felaket SL 2×ATR14(1h); portföyde bu biçim kullanılır, R paydası = 2×ATR14(1h) | C — `fam_mr_zaman/run_timing.py` | evet (birincil hücre; kart 5/6) |
| S4 | X04 = BTC-X04 QQQ boşluk tersi | QQQ işlem günü: gz = ln(QQQ açılış/önceki kapanış) / std20(QQQ günlük log getirisi, D−1'e kadar); \|gz\| > 0,5 → yön = −işaret(boşluk); 10:00 ET 1m açılışında gir, 16:58 ET (rollover−2) çık; SL 1×dvol20 (son 20 tamamlanmış UTC günü log getirisi std'si) × giriş | C — `fam_capraz_cikis/10_regime.py` | evet (DISC-seçili; POST'ta sönümlü) |
| S5 | CAPREV-RV D0 = BTC-S02 `G2_k1.0_UTC_D0` | UTC günü: σ20 = önceki 20 gün getiri std'si; stres = dün ≤ −σ20 ∨ 5g ≤ −σ20·√5; RV = σ30 > önceki 365 g medyanı (min 120); tetik = başı ≤19:00 UTC olan ilk 1h barın kapanışı < önceki UTC günü dibi → BUY; SL giriş×(1−σ20); TP yok; çıkış UTC gün sonu (00:00) | C — **post-hoc** — `fam_stres/posthoc_g2.py` | HAYIR (post-hoc) |
| S6 | OF02 W15 θ5 emilim fade | \|z(perp taker delta 15 dk, 30 g geçmiş)\| ≥ 5 ∧ \|z(spot 15 dk log getiri)\| ≤ 0,5 ∧ veri bayrakları temiz → akışın TERSİNE; yön başına 30 dk epizod; SL max(19 bp, 1,1×ATR5m), TP 1×SL, 15 dk zaman (rollover−2 tavanı), [RO−2, RO+3) giriş yok | C — **post-hoc** — `fam_orderflow/ofl.py`, `01_build.py` | HAYIR (post-hoc köşe) |
| S7 | DV04c-U b3 spot-öncülü yukarı takip | z5 = r5/std(r5; 30 g, shift 1) ≥ 3 ∧ Δbaz₅ ≤ −3 bp → BUY; 60 dk epizod; SL max(19 bp, 1,1×ATR5m), TP 2×SL, 60 dk (rollover−2 tavanı) | C — **geçersiz** (POST aynı-bar %0,85 ≥ %0,5; DISC negatif, T5) — `fam_turev/scripts/03_events.py` | seçilmiş ama DISC-negatif → post-hoc say |

Olay listeleri: S1/S2 `fam_trend` mantığıyla yeniden üretilir; S3/S4/S5 kendi kodlarının mantığıyla yeniden üretilir;
S6 `ofl.features` (önek testli) ile yeniden üretilir; S7 `fam_turev/cache/signals.pkl` (doğrulanmış önbellek) + giriş geçerlilik maskesi.
Yeniden üretimin önceki notlardaki n/ortR'yi (kayma farkı dışında) tekrarlaması beklenir; tekrarlamazsa kol dondurulmuş haliyle
yine kullanılır ama fark raporlanır.

## 4. Core "scalp-icra" ızgarası (S1 için tek seçim)
- Hücreler: k ∈ {0,25; 0,5}×ATR5m × W ∈ {15, 60} dk × dolmazsa ∈ {skip, market} = 8 hücre + piyasa girişi (taban).
- **Seçim ölçütü (yalnız DISC, tüm T03 olayları, örtüşmeli set):** sinyal başına ortalama R (skip edilen sinyal = 0R).
  Bir limit hücresi yalnız DISC'te piyasa girişini **≥ +0,02R/sinyal** geçerse benimsenir; birden fazla geçerse en yükseği; eşitlikte
  (fark < 0,005R) daha basit olan (W küçük, market yedekli). Hiçbiri geçmezse Core = piyasa girişi.
- Raporlanan (her hücre, DISC ve POST): dolum oranı, dolan/dolmayan sinyallerin **piyasa girişi R'si** (ters seçilim: dolmayanlar daha
  mı çok kazanıyor?), net R değişimi (sinyal başı ve işlem başı), tek-pozisyon zinciri.

## 5. Portföyler
| Portföy | Kollar | Not |
|---|---|---|
| P-CORE | S1 | seçilen icra hücresiyle |
| P-PRE | S1+S2+S3+S4 | post-hoc kol YOK |
| P-ALL | S1…S7 | tüm adaylar; seçim yanlılığı taşır |
| P-ALL−DV | S1…S6 | S7 aynı-bar geçersizliği yüzünden hariç |
- Her kol kendi içinde **tek pozisyon** (açıkken gelen sinyal yok sayılır). Kollar arası eşzamanlılık serbest; eşit risk/işlem
  (her işlem 1 risk birimi; portföy PnL'i R toplamı).
- Bilgi: küresel tek pozisyon (tüm kollar arasında aynı anda tek işlem, ilk gelen alır) ayrıca raporlanır.

## 6. Kart (her kol ve her portföy; birincil pencere POST; DISC ve TAM ayrıca)
1. hacim n ≥ 150 · 2. ort R > 0 ∧ gün-bloklu bootstrap P(EV>0) ≥ %90 · 3. kronolojik iki yarı ≥ 0 · 4. spread ×1,5'te ort R > 0 ·
5. icra farkı \|iyimser − gerçek\| ≤ ort R / 2 · 6. kol-başı tek pozisyonla pozitif (portföyde yapı gereği; ayrıca küresel tek-poz bilgi) ·
**+P** plasebo yüzdeliği ≥ %95 · **+B** BLIND ort R > 0.
Ek raporlar (geçme ölçütü değil): sabit 15 $ varyantı, yıl bazında ort R/n, en iyi 20 UTC giriş günü hariç ort R, R-cinsinden azami
düşüş (çıkış sırasına göre kümülatif), kol korelasyonu (POST günlük R toplamlarının Pearson'u + aynı gün işlem örtüşmesi), kol katkısı
(ΣR payı), kendi aynı-bar oranı (>%0,5 ise o kol 1m veriyle ölçülemez sayılır).
**Verdikt şeması:** LIVE = 6/6 + P + B **ve** portföy post-hoc kol içermez **ve** POST bu adaylar için görülmemiş veri olurdu —
bu son koşul bu turda hiçbir aday için sağlanmadığından **bu turda LIVE verdikti yapısal olarak verilemez** (en fazla "kart geçti →
ileri gölge zorunlu"). GÖLGE = ort R > 0 ∧ 6 ölçütten ≥ 4'ü. RED = diğerleri.

## 7. Plasebo
Her kol, 200 tekrar: her işlem aynı takvim yılı × aynı UTC saat:dakika × aynı yönden, o yılın rastgele bir gününe taşınır; aynı
geometri tanımı (stop/TP/tutuş o anın göstergeleriyle yeniden hesaplanır), aynı geçerlilik kuralları. İstisna (E53): S3 QB sabit
saatli olduğu için plasebosu **aynı gün, rastgele UTC saati, aynı dakika, aynı süre**dir (orijinal "hour" plasebosu).
Portföy plasebosu: her tekrarda tüm kolların işlemleri plasebo işlemleriyle değiştirilir, portföy ort R'si hesaplanır (kol başına
işlem sayısı korunur). Yüzdelik = gerçek ortR'nin plasebo dağılımındaki yeri.

## 8. Vetolar (yalnız filtre; işlem SİLER, eklemez)
- V1 (B, BTC-S06): SELL girişinde karar anından önceki 60 dk içinde herhangi bir 5m kapanışında r60 ≥ +3,5·σ60
  (σ60 = önceki 30 gün 5m-ızgara 60 dk getiri std'si, shift 1) → SELL açma.
- V2 (B−, BTC-S03): BUY girişinde günün bayrağı stres(k=1) ∧ RV-düşük (σ30 ≤ 365 g medyanı) ve karar kapanışı < önceki UTC günü dibi → BUY açma.
- V3 (B−, VS06/VS08): SELL girişinde karar kapanışı ≥ günlük (00:00 UTC çapalı) VWAP + 2σ_vw (hacim ağırlıklı, tipik fiyat) VEYA son 15 dk
  içinde fiyat önceki UTC günü tepesinin üstüne çıkmışsa → SELL açma.
Rapor: veto başına silinen n, silinenlerin ort R'si, portföy ort R değişimi (vetolu − vetosuz), POST ve DISC.

## 9. Kaldıraç ve boyut
- lot = özsermaye × risk% / SL_$ (1 lot = 1 BTC; 0,01 adım; min 0,01). Nominal/özsermaye = risk% / SL%. Perakende 2:1 ve demo 1:20
  tavanında izin verilen azami risk% = tavan × SL%; eşzamanlı pozisyonların nominal toplamı da tavana tabi.
- Monte Carlo: POST portföy işlem dizisi, **gün blokları** (bir UTC giriş gününün tüm işlemleri bir blok; işlemsiz günler dahil) 365 gün
  yerine koyarak çekilir; 10.000 yol; sabit-kesirli bileşik risk {%0,25, %0,5, %1}; çıktılar: medyan yıllık getiri, %5 yüzdelik, P(zarar),
  P(DD ≥ %20), P(DD ≥ %50). Eşzamanlı işlemler sırayla bileşiklenir (yaklaşım; not edilir).
- Önceden yazılan öneri kuralı: kanıt sınıfı < A iken risk ≤ %0,25 (not 03 kuralı H). MC'de P(DD≥%20) ≤ %10 ve P(zarar) ≤ %25 sağlayan
  en büyük risk "kanıt sonrası tavan" olarak raporlanır.

## 10. Motor doğrulama (sonuçtan önce koşulur)
- Kaba-döngü: rastgele ≥2.000 olay (piyasa + limit girişler, iki yön, TP'li/TP'siz, kaymalı) dakika dakika döngüyle yeniden hesaplanır →
  uyuşmazlık 0 olmalı (|ΔR| < 1e-9).
- Çapraz: kayma 0 iken T03 olaylarında motor = `fam_trend/lib_trend.M1.simulate` (birebir).

## 11. İleri gölge planı (karar kuralı burada dondurulur, sayılar sonuçtan sonra doldurulur)
- Gölge kaydı: her kol sinyali, broker BTCUSD M1/tick ile (bid/ask, gerçek spread, gerçek swap tahakkuku) sanal dolum.
- Geçme (kol veya portföy): n ≥ 150 olay **VE** 6 ölçüt **VE** plasebo ≥ %95 (ileri veride aynı yöntem). Ara bakış: n = 50 ve 100'de
  yalnız "durdurma" kuralı: ortR < 0 ∧ P(EV>0) < %20 → kolu bırak. Ara bakışta "erken başarı" ilanı yok.
- Canlıya geçiş yalnız 2. KURAL kartı (go_live_gate) + kullanıcı kararı ile; önce 0,01 lot "icra probu" kullanıcı onayına bağlı.

---
## EK-1 (sonuç SONRASI, 2026-10-22 ~08:40 UTC — verdikti değiştirmez)
- Yeniden üretim farkı: S6/S7 bu motorda (spread bid/ask bariyeri olarak yolda; TP/SL dolum fiyatından ölçülür = MT5 mekaniği)
  önceki notlardan yüksek çıktı (OF02 +0,210 vs +0,176; DV04c POST +0,273 vs +0,243). Önceki motor bariyerleri mid'den ölçüp
  maliyeti PnL'den düşüyordu. İki konvansiyon rastgele girişte aynı beklentiyi verir; güçlü-hareket olaylarında farklılaşır.
  Kart bu motorla (bot gerçekçi) raporlanır, fark notta yazılır.
- `05_extras.py` (bilgi): swap −%22,5 varyantı, QB stopsuz vs 2×ATR1h felaket stoplu, post-hoc kollar %50 küçültme senaryosu,
  son 12 ay alt dönemi. Hiçbiri seçim için kullanılmadı.
