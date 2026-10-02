# NDX Kapı Dökümhanesi — RAPOR (2026-09-30)

Soru: NASDAQ için bot'a para kazandıracak **yeni kapı / strateji** bul; farklı zaman
dilimlerinde doğrula; 5 kapı getir. Canlı sisteme dokunulmadı (salt araştırma).

## 0. Tek paragraf özet

NASDAQ'ta ~850 aday (16 ön-kayıtlı hipotez, 780 hücrelik sistematik
tarama, 34 gün-düzeyi koşul, takvim/mikro-yapı testleri) beş dönemde (2025 Dukascopy ×2,
2026 cache, 2026 MT5, 2026-Eylül ileri dönem) ve dört zaman diliminde (1m, 15m, 30m, 1h/10 yıl)
sınandı. **Rastgele girişlerde tek-özellikli piyasa-durumu kapıları plasebodan ayırt edilemiyor**
(780 hücrede 13 geçen vs plasebo ortalaması 16,4). Çağlar arasında taşınan tek tema
**"stres → ertesi gün yukarı, aşırı uzama → aşağı"** (günlük ölçekte ortalamaya dönüş) ve
bundan iki kapı çıktı; yanlarına Pazartesi ve ay-sonu akış kapıları eklendi. Beşinci çıktı bir
**strateji kapısı**: gölgede bekleyen REFLEX `mom_cont`'un bütün kenarı geleceğe bakma
sızıntısıymış — canlıya alınmamalı. Ayrıca iki veri hatası bulundu (§6).

## 1. Veri (tek saat ekseni: gerçek UTC)

| Kod | Kaynak | Dönem | Not |
|---|---|---|---|
| D25a / D25b | Dukascopy USATECHIDXUSD tick → 1m bid/ask | 2025 H1 / H2 | bağımsız kaynak, gerçek spread |
| C26 | candle_cache 1m | 2026-02-10 → 05-19 | **03-08 öncesi +60 dk düzeltildi** (§6) |
| M26 | MT5 NAS100 M1 (kutu) | 2026-05-19 → 08-28 | gerçek bid + spread |
| **S26** | `indicator_snapshots` (MT5, UTC) | **2026-08-29 → 09-30** | hiçbir analizde kullanılmamış ileri dönem; M26 ile çakışmada fark 0,0 |
| L15/L30/L60 | candle_cache 15m/30m/1h (broker = NY+7s) | 2023/2021/2016 → 2026-07-15 | uzun ufuk |
| Bot | NAS100 işlemleri (07-01→08-27 + kutudan taze 40 gün) | 317 bağımsız karar | aynı dakika bacakları tek karar |

İcra: karar = kapanmış bar; giriş = sonraki bar açılışı (BUY ask, SELL bid), +0,2 p kayma/dolum,
aynı barda TP+SL → SL, boşluk → açılış fiyatı. Simülatör el yapımı fikstürlerle test edildi
(`test_engine.py`).

**Yöntem hatası (bulundu ve düzeltildi):** "aynı günün ortalamasına göre fark" metriği geleceğe
bakar (günün kalan fiyat yolu ortalamaya girer) ve konum/VWAP tipi kapıları sahte iyi, trend
kapısını sahte kötü gösterir. Taban = aynı dönem × yön × UTC saati ortalaması.

## 2. Yeni matematik: braket beklentisi = sürüklenme × maruziyet

Sabit TP/SL braketi (botun 80/110'u) için, fiyat sürüklenmeli Brown hareketiyse isteğe bağlı
durdurma teoreminden:

- **E[PnL] = μ · E[τ]**, driftsiz çözülme süresi **E[τ] ≈ TP·SL/σ²**
- R cinsinden **EV_R ≈ (μ/σ²) · TP**

Sonuçlar (hepsi veride doğrulandı):
1. Giriş sinyali ancak pozisyonun **açık kaldığı süredeki** sürüklenmeyi değiştirdiği ölçüde para
   kazandırır. Botun P&L'i = ∫ pozisyon(t)·μ(t) dt − maliyet ("maruziyet muhasebesi").
2. Bir yön kapısının değeri sürüklenmeyle değil **varyans başına sürüklenmeyle** ölçeklenir.
   Stres günlerinde σ² büyük → 80 puanlık braket yazı-tura; bu yüzden gün-içi stres kapıları
   işlem düzeyinde söndü, **önceki günlerden** okunan stres/uzama kapıları kaldı.
3. Driftsiz piyasada TP<SL braketi yalnız ortalamaya dönen yolda kazanır; yol kalıcıysa
   (varyans oranı VR>1) trend yönündeki işlem kazanır, fade kaybeder. Bot işlemleri tam bunu
   gösterdi (VR>1,2'de trend-yönlü SELL'ler +23 p/karar).

## 3. Beş çıktı

Kanıt sınıfı envanterdeki ölçekle (A/B/C/X). Etki = bloklanan kümenin tabana farkı, R (80/110).

### K5 — Stres-dönüş: SELL açma (sınıf **B−**) ⭐ en para-ilgili
Koşul: **önceki ABD işlem günü NDX ≤ −%1,5** veya **son 5 gün ≤ −%4** → o gün SELL yok.

| katman | sonuç |
|---|---|
| 10 yıl 1h (2 saatlik z) | dün≤−1,5%: yukarı 8/11 yıl P=0,989 (2016-22 ve 2023+ aynı işaret); 5g≤−4%: 7/8 yıl P=0,946 |
| 30m 2021-26 | −0,037R, 4/6 yıl, P=0,93 |
| 15m 2023-26 | −0,021R, 3/4 yıl |
| 1m 2025-26 | −0,067R, 3/4 dönem, P=0,89 |
| **bot SELL kararları** | bloklanan 99 karar −7,3 p vs kalan +15,5 p; SELL içinde fark −17 p, **gün-bloklu P=0,974** (10 bloklu gün) |
| vekil portföy | ΣR −4,7 → +0,9 |

Yön bot işlemlerine bakılmadan teoriden/10 yıldan belirlendi. Zayıflık: bot kanıtı 10 güne dayanıyor
(çoğu Temmuz).

### K6 — Aşırı uzama: BUY açma (sınıf **C+**) — K5'in aynası
Koşul: NDX, 200 günlük ortalamanın **%10+ üstünde** → BUY yok.
10 yıl: 7/9 yıl P=0,962, iki çağda aynı işaret · 30m −0,024R 5/6 · 15m −0,016R 4/4 · 1m −0,033R 4/5 ·
**bot BUY: uzamışken +4,6 p (36 karar) vs değilken +46,8 p (39 karar)** · ⚠ vekil portföyde ZARARLI
(−5,7R). Etki küçük, uzun süre açık kalır (boğa piyasasında günlerin ~%40'ı).

### K1 — Pazartesi: SELL açma (sınıf **B−** genel / **C** bot)
Genel veride en tutarlı aday: 30m −0,061R **6/6 yıl** P=0,992 · 15m −0,074R **4/4** P=0,993 ·
1m −0,080R 4/5 P=0,973 · 10 yıl yukarı sürüklenme 8/11 yıl P=0,974 (NY 06–15 arası yoğun).
Ama: **son çağa özgü** (2016-20'de zayıf, 2023+ güçlü; ileri-yürüme 2016-20'den seçmezdi), bot
kapı evreninde 2/4, bot Pazartesi SELL'leri +6,6 p (34 karar, nötr), S26'da vekil kötüleşti.

### K3 — Ay sonu yeniden dengeleme (sınıf **C+**)
Koşul: ayın **son 2 işlem günü**; ay-içi NDX ≥ +%4 → BUY yok, ≤ −%4 → SELL yok
(emeklilik fonu dengelemesi, Harvey–Mazzoleni–Melone 2025).
10 yıl: +%4 sonrası aşağı 6/8 P=0,986; −%4 sonrası yukarı 4/4 P=0,976 · 30m −0,064R 4/6 ·
1m −0,145R 4/5 (19 gün) · botta hiç tetiklenmedi · yılda ~6 gün.

### K7 — Strateji kapısı: REFLEX `mom_cont` canlıya ALINMASIN (sınıf **A**)
`ndx_reflex_engine/triggers/detect.py::detect_mom_cont` 15m barı sol-etiketle örnekliyor ve 1m
teyidini **aynı** 15 dakikanın içinde arıyor: "gerilme ≥ 2 ATR" kararı teyitten sonraki 15m
kapanışını kullanıyor. 2026 transfer testi de bu fonksiyonu çağırıyor. Aynı icrayla:

| geometri | sızıntılı (araştırma) | sızıntısız (üretim servisi) |
|---|---|---|
| üretim: 15 dk süre + 1,5·ATR SL | +0,88R (n=645, P=1,00) | **−0,08R** (n=493, P(EV>0)=0,13) |
| araştırma tp1,5/sl1,0 ts30 | +0,34R | **−0,19R** (P=0,00) |
| araştırma tp1,5/sl1,5 ts60 | +0,32R | **−0,13R** (P=0,004) |

Gölgedeki `reflex_engine_service` doğru (sızıntısız) sürümü koşuyor → gölge karnesi negatif
çıkacak. `REFLEX_LIVE=False` kalmalı; hafızadaki "+0,29R transfer" iddiası geçersiz.

### Birlikte
Bot kararları (K1+K3+K5+K6): 317'nin 160'ı bloklanırdı; bloklananlar −0,3 p/karar (−512 $),
kalanlar +17,3 p/karar. Vekil VIXREG portföyü: K1+K3+K5 → ΣR −4,7 → **+13,5** (613→500 işlem,
3/5 dönem iyileşir, S26 kötüleşir); K6 eklenince +7,9.

## 4. Elenenler (tekrar denenmesin)

| aday | neden |
|---|---|
| 780 hücrelik tek-özellik taraması (78 özellik × 1/5/15/60 dk × 5 dilim × 2 yön) | 13 geçen < plasebo ortalaması 16,4 (dairesel kaydırma, 200 tekrar) |
| Ön-kayıtlı H1–H16 (kapanış akışı, Avrupa açılışı, boşluk, 10:00 dönüşü, ADR, yuvarlak sayı, emilim, ölü piyasa, VWAP bandı, önceki gün uçları, çarpıklık, TOM, OPEX, VIX vade yapısı) | saat-eşlemeli tabanla dört dönemde tutarsız |
| Sürüklenme takvimi (gün × saat) | 2016-20'den öğrenilen 2021-26'da korelasyon 0,0085; ters yön −0,016 |
| p-değeriyle gün-düzeyi koşul seçimi | 2016-20'de seçilen 6 koşulun 2021+'da 1'i doğru (seçilmeyenler 17/26) |
| K2 FOMC öncesi 24 saat SELL yok | tam pencerede 1m'de ters işaret (+0,22R, 1/5) |
| K4 pürüzlülük (VR>1,2 → TP<SL açma), K4b fade-koruma | genelde 5/5 küçük (−0,02R) ama bot işlemleriyle ters; 15m/30m ölçeğine taşınmıyor |
| Gün-içi stres (bugün ≤ −%1,5), dakika-içi zamanlama, sessiz-öğle | tutarsız |
| VIXREG yön etkisi, genel girişlerde | gerçek (10 yılda 9/10 ve 10/11 yıl doğru) ama işlem başına ~0,01R — botun VIXREG kenarı varsa sinyal etkileşiminden geliyor |

## 5. Önerilen adımlar (hiçbiri LIVE değil)

1. **K5 + K6 → gölge** (`log_gate_skip` nedeni `stress_reversal` / `extension_buy`): bot her taramada
   NAS100 D1 kapanışlarından dün getirisi, 5 gün getirisi ve 200g ortalama mesafesini hesaplar;
   bloklamaz, yalnız kaydeder. 4–6 hafta sonra kapı-atlama replay'i (`audit_skipped.py`) ile oku.
2. **K1 → gölge** (`monday_sell`). K3 nadir → gölge kaydı yeterli.
3. REFLEX: `REFLEX_LIVE=False` kalıcı; `detect.py::detect_mom_cont` düzeltilmeli
   (`resample(label="right", closed="right")` + teyit bir sonraki dilimde), FINDINGS/hafıza notu güncellenmeli.
4. Canlıya alma yalnız 2. KURAL kartıyla (panel sinyali tabanlı → canlı/gölge işlem kartı, ≥100 işlem).

## 6. Yan bulgular (veri hataları)

1. **candle_cache NDX 1m, 2026-02-10 → 03-08 etiketleri 60 dk ERKEN.** Kış saatinde açılış
   sıçraması 14:30 UTC olması gerekirken 13:30'da; 8:30 ET verileri 12:30'da. 03-08 sonrası doğru.
   Muhtemel neden: 08-12 onarımı kış dönemine de yaz ofsetini (−180 dk) uygulamış; doğrusu −120 dk.
   Bu dönemi saat-bazlı kullanan her araştırma (ör. `ndx_five_gates_20260930` protokolü) etkilenir.
2. `research/ndx_buy_lab/data/macro_daily.csv` **2026-07-28'de bitiyor**; sonrasını kullanan
   analizler ileri taşınmış bayat VIX/NDX okur. Burada yfinance ile 09-30'a tamamlandı
   (`data/macro_daily_patched.csv`, çakışma farkı 0,0).

## 7. Dosyalar

`PROTOCOL.md` (ön-kayıt) · `common.py` (veri + numba simülatör) · `test_engine.py` · `features.py`,
`feat2.py` (nedensel özellikler, 1/5/15/60 dk) · `evaluate.py` (H1–H16) · `scan.py` (plasebolu tarama) ·
`decomp.py` (yön/yapı ayrışımı) · `momcont.py` (sızıntı kanıtı) · `macro10y.py`, `walkforward.py`,
`drift_calendar.py` (10 yıl) · `daylevel_trades.py` (30m/15m/1m işlem düzeyi) ·
`final_candidates.py` (son değerlendirme) · `results/` (JSON/CSV çıktılar).
Yeniden üretim: `build_duka.py → build_labels.py → build_features.py 1 5 15 → feat2.py → final_candidates.py`.

---

# TUR 2 — Başarılı örneklerin ortak mantığı → türev hipotezler (`PROTOCOL_2.md`, `round2*.py`)

## 8. Ortak payda (kanıtlı örneklerden mantık yoluyla)

Projede ayakta kalan her şey (Cuma, ASIA, TREND_GATE, VIXREG, decider giriş-kalitesi, probasyon,
fakeout teyidi, USOIL/formasyon/SMC SELL yasakları) ve tur 1'in K1/K3/K5/K6'sı altı ilkeye indirgendi:
P1 ölçek ayrışması · P2 maruziyet×sürüklenme · P3 teyit>tahmin · P4 SELL vergisi · P5 varyans
ölçeklemesi · P6 bilgi şoku. Her ilkeden bir hipotez türetildi ve sonuçtan önce donduruldu.

## 9. Sonuçlar

| # | Türev hipotez | Sonuç | Karar |
|---|---|---|---|
| T1 | Vol-normalize günlük gerilme pusulası (z5 ≥ ±1) | genel 3/5, 30m 4/6, 15m 2/4 — K5/K6'nın sabit eşiklerinden zayıf | elendi |
| T2 | Decider bıçak kapısını (5m kanal karşı ≥2σ) bota taşı | botta **ters** (+47 p, n=37) ama kovalar monoton değil → gürültü; genel veride 1/5 | **bota taşınmasın** |
| T3 | Hacim patlaması (son kapalı 5m ≥1,5× önceki 20) | bot işlemleri −25,6 p vs +10,5 (P=0,93); bot-evreni genel −0,11R (3/4, P=0,92); decider'da A−. **Ama** 1m/15m ve diğer eşiklerde tutmuyor (15m'de botta ters), etkinin çoğu C26'da | **C+ gölge** |
| T4 | Kapı etkisi sakin rejimde büyük olmalı (μ/σ²) | çürüdü — etkiler vol tertilinden bağımsız / ters | teori düzeltildi (aşağıda) |
| T5 | Stres gününde yalnız teyitli (önceki dibin altı) SELL | **tam ters**: dibin altında SELL en kötü hücre −0,18R, 4/4 dönem, P=0,982 | → **K5b** |
| T6 | Açık SELL'i 16:55 NY'de kapat | genel −0,015 (P=0,58), botta tutmak daha iyi | elendi |
| — | Ölçek haritası (kanal-z fade/kovalama, 1–60 dk) | hiçbir ölçekte tutarlı etki yok (±0,02R, 2–3/5) | fiyat-konumu kapıları sinyale özgü |
| — | Ayna: coşku (dün ≥+%1,5 / 5g ≥+%4) → BUY yok | 1/5 (+0,049R) — öngörüldüğü gibi TUTMADI | **korku döner, coşku dönmez** |

## 10. Mantık yoluyla çıkan yeni bilgiler

1. **Korku/coşku asimetrisi.** Günlük ölçekte aşağı aşırılık geri döner (K5, K5b), yukarı aşırılık
   dönmez (ayna 1/5). NDX'te kazanan kapıların neredeyse hepsinin SELL bloğu olması bundan.
2. **Teyit ilkesi günlük ölçekte ters döner.** Probasyon/fakeout teyidi sinyalin kendi gürültüsünü
   süzer; stres sonrası "yeni dibi kırınca sat" ise kapitülasyonu satmaktır — en kötü SELL.
3. **Fiyat-konumu kapıları popülasyonlar arası taşınmaz, bilgi-şoku kapıları kısmen taşınır.**
   Decider'ın kanal kapısı (A−) botta ters; hacim patlaması aynı tanımda üç popülasyonda aynı yön.
   Bir kapıyı bir sistemden diğerine taşımadan önce hedef popülasyonda ayrıca ölçmek şart.
4. **Teori düzeltmesi: sürüklenme varyansla ölçeklenir (μ ∝ σ², risk primi).** Böylece
   EV_R ≈ (μ/σ²)·TP rejimden bağımsız kalır → günlük kapıları volatiliteye göre ayarlamaya gerek yok.

## 11. Güncel aday listesi (tur 1 + tur 2)

| # | Kapı | Kanıt | Sınıf |
|---|---|---|---|
| **K5b** | Stres günü (dün ≤−%1,5 veya 5g ≤−%4) **ve** fiyat < önceki RTH dibi → SELL yok | genel −0,18R 4/4 P=0,982 (23 gün); bot −12,8 p (41 karar, 5 gün) | B− (alt hücre, sonradan) |
| **K5** | Stres günü → SELL yok (K5b'yi kapsar) | bot SELL: stres&dip altı −12,8 · stres&üstü −3,3 · stres yok +9,8 (monoton) | B− |
| K6 | NDX 200g +%10 → BUY yok | tur 1'deki gibi; K6b (> önceki tepe) ek fayda vermedi | C+ |
| K1 | Pazartesi SELL yok | tur 1'deki gibi | B− / C |
| K3 | Ay sonu dengeleme | tur 1'deki gibi | C+ |
| T3 | 5m hacim patlaması ≥1,5 → giriş yok | yalnız ön-tanımlı eşikte; TF testi geçmedi | C+ |
| K7 | REFLEX mom_cont canlıya alınmasın | sızıntı | A |
| — | Decider bıçak kapısı bota **taşınmasın** | botta ters/gürültü | uyarı |

---

# TUR 3 — diğer ajanın raporuyla karşılaştırma → varyasyonlar
Ayrıntı ve konsolide sonuç: **[NIHAI_RAPOR.md](NIHAI_RAPOR.md)** (`PROTOCOL_3.md`, `round3.py`, `v3_robust.py`).
Özet: CAPREV kapitülasyon alımı (stres günü + VIX≥18,4 + önceki RTH dibi altında ilk kapanış → BUY, 16:00 çıkış)
10y 1h 9/11 yıl / 30m 6/6 / 15m 4/4, kontroller negatif → B+ strateji adayı. Kovalama endeksi ≥3 → SELL yok: bot SELL'lerinde
monoton (+28,8 → −38,9 p), genel 4/5 → B−. Diğer ajanın M15 bulgusu genel veride tekrarlanmadı.

# TUR 4 — diğer ajanın sentez raporu (`ndx_synthesis_20261002`) ile karşılaştırma
Konsolide sonuç **[NIHAI_RAPOR.md](NIHAI_RAPOR.md) v2**. Özet: stres VE yüksek VIX birlikte gerekli (stressiz∧yüksek VIX ≈0);
saat plasebosu %100 üstünde (kriz piyangosu değil); kenar zaman çıkışında (ertesi gün 16:00 en iyi stoplu çıkış);
kural değiştirilmeden DAX'ta çalışıyor (ertesi gün +0,35/+0,47, P≈0,97); günlük QQQ 10/11, NDX 11/11 yıl;
iki kademeli tasarım (açılış + dip kırılımı) 10 yılda 223 olay günü → CAPREV-2 (B+). Düzeltmeler: "kovalama K5b'yi içerir" yanlıştı;
μ∝σ² yalnız olası açıklama; 30 Eylül makro değeri tamamlanmış kapanışla güncellendi.
