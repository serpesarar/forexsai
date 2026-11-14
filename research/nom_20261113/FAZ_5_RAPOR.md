# FAZ 5 — Ekonomik test, stres, final test (NOM, 2026-11-13)

Kod: `src/faz5_econ.py` (`dev`, `final`, `bundle`). Çıktı: `results/faz5_dev.json`, `results/faz5_final.json`,
`results/faz5_bot_crosscheck.json`, `results/faz5_skill_slices.json`, `results/final/*.parquet`,
`results/plots/final_reliability_*.svg`, kilit kaydı `results/FINAL_OPENED.json`.

## 1. Geliştirme dönemi (WF OOS) — işlem kuralı ve eşik seçimi
Kural adayları (ön kayıt): beklenen R ≥ {0; 0,05; 0,10; 0,15; 0,20} veya P(TP) ≥ {0,50…0,65} ∧ beklenen R ≥ 0.
Seçim **yalnız seçim bloklarında** (2023H1–2024H2, bağımsız karar ≥ 30, EV > 0), teyit **teyit bloklarında** (2025H1–2026Q1).
Sürtünme: gerçek dolum (spread + 1 p giriş + 1 p SL kayma) etikette; **2×** stres = ek (spread + 2 p) / SL mesafesi.

- 40 hedefin 16'sında seçim bloklarında pozitif kural bulundu; **0'ı** ön-kayıtlı geçme ölçütlerinin hepsini sağladı
  (teyitte EV>0, P(EV>0) ≥ %90, 2× sürtünmede EV>0, P1 plasebo p95 üstü, ≥2/3 yıl +, bağımsız n ≥ 30).
- Teyit bloklarında en umut verici görünenler küçük bağımsız örneklemliydi: 4 s long 1/1 (beklenen R ≥ 0,2) n=31,
  **8 bağımsız**, +0,40R; 4 s long 1,5/1 n=82, 24 bağımsız, +0,21R; seans short 1,5/1,5 n=86, 39 bağımsız, +0,09R.
  Büyük örneklemliler eksi: 1 s long 1,5/1,5 (n=206, 48 bağımsız) −0,19R; seans long 2/1 (n=603, 163 bağımsız) −0,13R.
- Taban (her an işlem) WF EV'si: 15 dk −0,31…−0,48R · 1 s −0,14…−0,25R · 4 s −0,05…−0,12R · seans −0,01…−0,09R.
**Hüküm (dev): işlem önerisi için kanıtlı hedef yok → tüm eşikler "kanıtsız" olarak dondu.**

## 2. Rejim / yıl / seans dilimleri (olasılık becerisi, saat-iklimine göre Brier becerisi)
WF (`faz5_skill_slices.json`), 1 s long 1/1: yıl 2023 +0,002 · 2024 +0,012 · 2025 +0,024 · 2026 +0,018;
VIX <18,4 +0,013 / ≥18,4 +0,012; trend +0,014 / yatay +0,012; seans Asya +0,027 · Londra +0,007 ·
**NY açılış −0,019** · öğle +0,003 · kapanış +0,009. 4 s long: 2023 **−0,006** → 2026 +0,036; kapanış sonrası +0,11.
15 dk: Asya +0,11, NY öğle +0,008. Haftanın günü / olay günü dilimleri işlem kuralı seçilen hedeflerde `slices` alanında.
**Okuma:** beceri yıllar içinde artıyor (veri büyüdükçe) ve **en çok ticaretin yapıldığı NY açılışında yok**. Tek döneme
bağlı değil ama küçük; VIX/rejimden bağımsız.

## 3. FİNAL TEST (2026-05-01 → 2026-11-03, kilit tek kez açıldı, ayar değişmedi)
Not: ilk açılış denemesi ilk hedefte, hiçbir final metriği hesaplanmadan bir kod hatasıyla (işlem yokken `n_indep`
anahtarı) düştü; yalnız çökme düzeltildi, aynı donmuş ayarlarla yeniden koşuldu (`FINAL_OPENED.json.previous_attempt`).
Model: geliştirme verisiyle (≤ 2026-04-30 − arındırma) eğitilmiş, aynı sabit parametreler; eşikler dev'den.

| Ufuk | Brier becerisi final (WF) | Kural tabanı final | AUC TP model / iklim | Kalibrasyon eğimi final (WF), long 1/1 |
|---|---|---|---|---|
| 15 dk | **+0,049** (+0,059) | +0,003 | 0,609 / 0,597 | 0,68 (0,97) |
| 1 saat | **+0,022** (+0,015) | +0,005 | 0,625 / 0,624 | 0,59 (0,91) |
| 4 saat | **+0,038** (+0,011) | +0,008 | 0,662 / 0,650 | 0,54 (0,91) |
| seans | **+0,082** (−0,001) | +0,003 | 0,725 / 0,721 | 0,99 (0,81) |

- **Final, WF'den kötü değil** (beceri benzer/yüksek) → overfit DUR koşulu oluşmadı.
- Ama **kalibrasyon eğimi finalde 0,54–0,68**: model doğru sıralıyor fakat olasılıkları fazla yayıyor (ör. 1 s long 1/1:
  "%10" kovası %18,5 gerçekleşti, "%47" kovası %43,6). Final dönem (NDX 27–31k, farklı oynaklık rejimi) isotonic'in
  öğrendiği eşlemeden kaymış. Üretim paketi kalibrasyonu son %20'lik (≈ son 12 ay, final dahil) dilimde yeniden fit
  edildi; canlıda eğim **Faz 8 izlemesinin birinci maddesi**.
- Donmuş kurallarla final işlem akışı (kanıtsız oldukları hâlde raporlanır): 4 s long 1,5/1 n=258 / 53 bağımsız +0,095R
  (2× +0,03, P %68); seans long 1/1,5 n=424 / 75 bağımsız +0,087R (2× +0,05, P %89, plasebo p95 +0,039); seans long
  1,5/1,5 +0,104R (20 bağımsız); 1 s long 1,5/1,5 −0,116R; 15 dk long 1,5/1,5 −0,19R; 4 s long 1/1 −0,36R (6 bağımsız).
  Karışık, küçük örneklemli, geliştirme teyidiyle tutarsız (seans long 1/1,5 dev teyitte −0,05R'ydi) → **kenar yok**.
- Final taban EV (her an işlem): 15 dk ≈ −0,21R, 1 s ≈ −0,12R, 4 s ≈ −0,06R, seans long ≈ −0,05R / short ≈ −0,01R.

## 4. Bot işlemleriyle çapraz kontrol (final dönem, 2026-06-30 → 08-28)
`NAS100_tum_islemler.csv`: TP/SL ile kapanan 281 işlem (164 TP, 117 SL). Giriş dakikasında, işlem yönünde modelin
P(TP önce) (dev-eğitimli final modeli):
- 1 s 1/1: AUC **0,544** (TP'lerde ort. P 0,337, SL'lerde 0,321); gün-içi permütasyon p95 0,571 → **anlamsız**.
- 4 s 1/1: AUC **0,543**, p95 0,567 → **anlamsız**.
Model bot'un TP ve SL işlemlerini anlamlı ayırt etmiyor (bot geometrisi farklı — sabit puan TP/SL — bu kıyası
zayıflatır; yine de sıralama bilgisi yok denecek kadar az). 28k kapı kaydı (gate_skipped) tekrarlı tarama kayıtlarıdır
(E6) ve sonuç taşımaz; final dönem içinde olduğundan ayrıca etiketlenmedi.

## 5. DÜRÜST SONUÇ
- **Var olan:** Kalibre, sızıntısız, plasebo-üstü (**P2: +0,018 vs p95 −0,0003**) bir *olasılık* bilgisi. Bu bilgi büyük
  ölçüde **"bariyerlere ne kadar hızlı varılır"** (oynaklık/zamanlama) bilgisidir: P(zaman aşımı) ve sürtünmeye göre
  hareket büyüklüğü. Beceri 15 dk ve Asya seansında en yüksek.
- **Olmayan:** **Yön kenarı.** Hiçbir ufuk/geometri/yönde sürtünme sonrası pozitif beklenen değer kanıtlanmadı.
  Her an açılan işlem her hücrede negatif; modelin seçtiği alt kümeler teyitte ve finalde tutarsız. Bot işlemlerini
  ayırmıyor. Bu, GC-02 / TM-01 / DTS-03 bulgularıyla aynı resim: oynaklık öngörülür, yön öngörülmez.
- **Kullanılmaması gereken yerler:** (1) **Yön/işlem önerisi olarak hiçbir yerde** — motor bu yüzden her durumda
  "NÖTR / belirsiz" döner; (2) **15 dk ufkunda işlem**: taban −0,2…−0,4R, sürtünme ATR(M5)'in %30–40'ı; (3) **NY açılışı
  (09:30–10:30 ET)**: beceri sıfır/negatif; (4) **seans sonu ufku** için WF'de iklimi yenemedi (final iyi ama tek dönem);
  (5) final dönem kalibrasyon eğimi 0,54–0,68 → canlı kalibrasyon mezuniyetinden önce olasılık değerlerini ±5–8 puan
  belirsiz okuyun.
- **Güvenilir olduğu kullanım:** "Şu an 1 s içinde ±1 ATR'ye dokunma ihtimali / zaman aşımı ihtimali nedir?", risk
  boyutlandırma ve "bu stop bu sürede yenir mi?" sorusu — yani **oynaklık/menzil bilgisi**; yönsüz.

## 6. Bağımsız eski dönem: 2018-01 → 2021-10 (HistData, 2020 çöküşü dahil) — Faz 0 EK-3 sonrası ek sınama
Etkin paket (2021-11 → 2026-11 ile eğitildi) bu dönemi HİÇ görmedi; farklı besleme; spread bp × fiyat; iklim tabanı dönemin KENDİ saat
oranları (modele avantaj vermez). 15 dk ızgara, 1/1 geometri. Kaynak `results/faz0_v3_eski_donem.json`.
**Düzeltme (2026-11-14, E135):** ilk koşu HistData damgalarını sabit EST (+5 sa) sanıyordu; yaz aylarında 60 dk kaymıştı (Faz 0 EK-5).
Aşağıdaki tablo düzeltilmiş eksenle; ilk koşu `faz0_v3_eski_donem_v1_sabitEST.json`'da saklı ve son sütunda.

| Hedef | n | Brier becerisi (tüm) | Kalibrasyon eğimi | ort. P(TP) / gerçekleşen | 2020-02-15→05-15 becerisi | Her an EV (R) | ilk koşu becerisi |
|---|---|---|---|---|---|---|---|
| 15m long | 84.500 | **+0,025** | 1,25 | 0,221 / 0,173 | **+0,068** | −0,55 | +0,012 |
| 15m short | 84.500 | **+0,034** | 1,21 | 0,235 / 0,183 | +0,062 | −0,55 | +0,019 |
| 1h long | 83.906 | −0,000 | 1,14 | 0,288 / 0,268 | +0,008 | −0,25 | −0,002 |
| 1h short | 83.906 | −0,004 | 1,05 | 0,317 / 0,269 | +0,002 | −0,28 | −0,007 |
| 4h long | 83.454 | +0,008 | 1,15 | 0,310 / 0,306 | +0,005 | −0,08 | −0,001 |
| 4h short | 83.454 | +0,004 | 0,95 | 0,347 / 0,302 | +0,014 | −0,14 | −0,004 |
| seans long | 23.467 | +0,010 | 0,82 | 0,355 / 0,364 | −0,026 | −0,06 | +0,016 |
| seans short | 23.467 | +0,010 | 0,77 | 0,346 / 0,361 | −0,017 | −0,10 | +0,016 |

**Okuma:** Doğru saat ekseniyle eski dönemde 15 dk becerisi geliştirme dönemi düzeyine yaklaşıyor (+0,025/+0,034 vs WF +0,059) ve
2020 çöküşünde en yüksek (+0,06–0,07) — oynaklık bilgisi kriz rejiminde de, bağımsız beslemede de taşınıyor. 1 s ≈ 0, 4 s küçük +,
seans küçük + (çöküş diliminde −). Kalibrasyon eğimi 0,77–1,25 (mezuniyet bandı 0,7–1,3 içinde); 15 dk'da düzey yanlılığı (+5 puan)
besleme/spread farkından. **Her an işlem açmak çöküş dahil her ufukta eksi; yön kenarı hükmü (0/40) bağımsız eski dönemde de geçerli.**
Saat ekseni hatası bu hükmü değiştirmedi ama oynaklık becerisini olduğundan düşük gösteriyordu.
