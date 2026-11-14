# FAZ 3 — Doğrulama şeması (modelden ÖNCE kuruldu) (NOM, 2026-11-13)

Kod: `src/validation.py` (Faz 4/5 bunu çağırır; şema değişirse sonuçlar değişir — bu yüzden önce yazıldı).
Ön kayıt: `PROTOCOL.md` §D.

| Öğe | Karar | Uygulama |
|---|---|---|
| Rastgele bölme | **yasak** | Yalnız zamana dayalı maskeler. |
| Final test (kilitli) | **2026-05-01 00:00 UTC → veri sonu (2026-11-03)**, ~6 ay | `FINAL_START`; `assert_not_final()` her WF katında eğitim+test maskesini denetler, final dönem satırı görürse **istisna fırlatır**. Final yalnız Faz 5'te `walk_forward(final=True)` ile tek kez açılır. |
| Walk-forward | genişleyen pencere, 7 test bloğu: 2023H1, 2023H2, 2024H1, 2024H2, 2025H1, 2025H2, 2026-01→04 | İlk blok eğitimi 2021-12 → 2022-12 (13 ay, 2022 ayı piyasasının tamamı). |
| Arındırma (purge) | etiket penceresi test bloğu başını geçen eğitim satırları atılır | `train = t < blok_başı − ufuk − ambargo` (ufuk: 15dk / 1s / 4s / seans ≤ 7s). |
| Ambargo | 1 gün (≥ en uzun ufuk) | `EMBARGO_S = 86400`. |
| Purged K-Fold | 6 ardışık blok, iki yanda ufuk+ambargo arındırma | `purged_kfold()`; hiperparametre araması **yapılmıyor** (sabit parametre), bu yüzden yalnız tutarlılık için. |
| Ölçekleyici | yok (ağaç modeli) | Isotonic kalibratör yalnız eğitim penceresinin son %20'sinde fit edilir; fit ile kalibrasyon arasında ufuk + ambargo boşluğu. |
| Erken durdurma | kalibrasyon kümesinde çok-sınıflı log-loss | Test bloğu hiçbir şekilde görülmez. |
| Eşik/geometri seçimi | WF OOS'ta **seçim blokları** 2023H1–2024H2, **teyit blokları** 2025H1–2026Q1 | Seçilen eşik donar; final testte değişmez. |
| Plasebo P1 | aynı sayıda, **aynı NY-saati dağılımında** rastgele karar anı, aynı yön/geometri (E52: saat eşlemesi) | `hour_matched_placebo()`; model seçiminin EV'si p95'i geçmeli. Not (E51): maliyetli rastgele girişi yenmek tek başına kenar değildir → ayrıca EV > 0 şartı. |
| Plasebo P2 | gün-blok karıştırılmış etiketlerle aynı pipeline, 20 tekrar | Gerçek modelin saat-iklimine göre Brier becerisi plasebo p95'ini geçmeli. |
| Bootstrap | gün-blok, 2.000 tekrar → EV %95 GA ve P(EV>0) | `day_block_bootstrap()`. |
| Bağımsız karar | aynı yönde ≤ 60 dk aralıklı sinyaller tek epizod (E6/E9) | `independent_count()`. |
| Değerlendirme ızgarası | 15 dk (5 dk komşuları neredeyse aynı yolu paylaşır; 3× daha az satır, aynı bilgi) | Tüm WF ve final ölçümleri 15 dk ızgarasında. |
| Taban | NY saati kovası iklimi (sınıf oranları, eğitimden; az örnekli kova genel orana büzülür) + kural tabanı (H1 EMA50 tarafı × M15 RSI14 kovası × saat) | `climate()`, `rule_state()` (Faz 4). |

Kilit doğrulaması: `walk_forward()` geliştirme katlarında `test &= t < FINAL_START` ve `assert_not_final`;
Faz 4 koşusunun hiçbir katı 2026-05-01 sonrasını içermez (katlar `faz4_metrics.csv`'de, son kat 2026Q1).

## EK (2026-11-14) — Purged K-Fold koşuldu (`src/faz34_ek.py`, `results/faz34_ek.json`)
Şema yalnız yazılmış değil, Faz 4 ile aynı sabit LightGBM parametreleri ve aynı isotonic kalibrasyonla koşuldu: geliştirme dönemi
(2021-11 → 2026-04, final hariç; `assert_not_final` her katta) 6 ardışık blok, test bloğunun iki yanında ufuk + 1 g ambargo arındırma.
Ölçüt: saat-iklimine göre Brier becerisi.

| Hedef | Purged K-Fold katları (1…6) | Ortalama | WF ortalaması (7 kat) |
|---|---|---|---|
| 1 s long 1/1 | 0,012 · 0,006 · 0,014 · 0,014 · 0,012 · 0,024 | **+0,013** | +0,014 |
| 4 s long 1/1 | 0,014 · 0,009 · 0,020 · 0,027 · 0,026 · 0,029 | **+0,021** | +0,015 |

6 katın 6'sı pozitif, düzey WF ile aynı mertebede. K-Fold geleceği de eğitimde gördüğü için (iki yanlı arındırmaya rağmen) üst sınır
sayılır; 4 s'teki +0,006'lık fark bu iyimserlik payıyla tutarlı. **Hüküm: WF sonucu şemaya bağlı değil; hiperparametre seçimi
yapılmadığından K-Fold ayrıca bir seçim için kullanılmadı.**
