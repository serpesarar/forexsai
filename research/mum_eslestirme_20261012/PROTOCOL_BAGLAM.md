# Ön-kayıt — Bağlam ve çapraz-sembol eşleştirme testi (ME-03)

> **Tarih:** 2026-10-12 (sonuçlar hesaplanmadan yazıldı). **Kullanıcı isteği:** "başarı yakalayacak özellikler ekle —
> VIX rejimlerinde aynı anda tespit, başka sembollerle beraber, kombinasyonlar". **Önceki kanıt:** ME-02 (şekil tek başına =
> rastgele komşu), OLD-10 (VIX rejimi → NDX yönü, A), GF-05 (VIXREG genel girişte ~0,01R), GF-16/22 (stres ∧ VIX ≥ 18,4 →
> NDX/DAX dönüşü, nadir), CORTEX (günlük çapraz-piyasa önceki-gün değerleri yön vermiyor).

## 1. Hipotezler ve başarı ölçütü

| ID | Soru | Kıyas (aynı sorgular, eşli) |
|---|---|---|
| B1 (**ana**) | Şekil + bağlam (komşular yalnız aynı bağlamdaki geçmiş anlardan) **yalnız bağlamdan** iyi mi? | şekil+bağlam ↔ bağlam-koşullu taban (aynı bağlamın yukarı oranı / medyan hareketi) |
| B2 (bilgi) | Bağlamın kendisi bilgi taşıyor mu? | bağlam-koşullu taban ↔ koşulsuz taban |
| B3 (**ana**) | Çapraz-sembol ortak şekil (hedef + ortak sembolün aynı andaki mumları) hedefin kendi şeklinden ve ortağın şeklinden iyi mi? | ortak ↔ kendi, ortak ↔ ortak-sembol-yalnız, hepsi ↔ taban |

**Başarı (hücre = sembol × TF × ufuk × temsil × bağlam):** eşli fark (yön isabeti; büyüklük mutlak hatası) gün-blok bootstrap
P ≥ 0,975 **ve** iki kronolojik yarıda da > 0. **Genel karar:** bir bağlam/çift ancak başarılı hücre sayısı tesadüf
beklentisini (%2,5) binom testiyle p < 0,01 aşarsa **ve** en az iki sembolde görülürse "katkı var" sayılır. Aksi hâlde yok.

## 2. Bağlamlar (hepsi karar anında bilinen değerlerle)

| Ad | Tanım | Kaynak |
|---|---|---|
| `vix` | Sorgu barının bitişindeki NY tarihinden **önceki** son işlem gününün VIX kapanışı ≥ 18,4 | `ndx_gate_forge/data/macro_daily_patched.csv` (tamamlanmış kapanış, E20) |
| `stres` | Sembolün kendi günlük (NY 17:00 sınırlı, tamamlanmış) son getirisi ≤ −%1,5 **veya** son 5 gün ≤ −%4 | 1h'ten türetilen 1d |
| `vix_stres` | `vix` × `stres` (4 hücre) | — |
| `saat` | Aynı UTC saatinde biten barlar | — |
| `oyn` | A_t / önceki 1 yılın medyan A'sı: < 0,8 · 0,8–1,25 · > 1,25 | — |

Eşikler önceden sabittir (VIX 18,4 ve stres eşikleri NDX'te bulunmuştu; XAU/OIL'de aynen uygulanır, ayrı ayarlanmaz).

## 3. Çapraz-sembol

Sıralı çiftler (hedef, ortak): NDX, DAX, XAU, OIL'in 12 sıralı çifti. TF: 30m, 1h, 4h, 1d. İki sembolün **ortak zaman
damgalı** barları (iç birleşim). Varyantlar: `kendi` (hedefin şekli), `ortak` (yalnız ortağın şekli), `ikisi` (iki şekil
yan yana, eşit boyut). Sonuç her zaman hedefin.

## 4. Değişmeyenler (ME-02 ile aynı)

Temsil R7 ve P33, K = 50, olay kopyaları kaldırılır (V2), kayan 5 y kütüphane, j + H ≤ t, çıplak komşu oyu, ufuklar ve
sorgu takvimi ME-02 ile aynı, her hücrenin **son 7 ayı dokunulmaz**, plasebo = aynı (bağlam-süzülmüş) havuzdan rastgele
komşu. Bağlamda havuz < 50 ise mevcut olanla devam edilir; < 10 ise o sorgu-bağlam tahminsiz kalır (taban kullanılır).

## 5. Raporlama

Olumlu ve olumsuz her sonuç; bağlam ve çift başına başarılı hücre sayısı, binom p, sembol dağılımı; B2 sonuçları ayrı.
Sonuçtan sonra eşik/tanım değiştirilmez; değişirse bu dosyaya tarih + gerekçe ile yazılır.

## 6. Değişiklik kaydı

| Tarih | Değişiklik | Gerekçe | Sonuç görüldü mü? |
|---|---|---|---|
| 2026-10-12 | Özete **ikincil, bilgi amaçlı** Brier ölçütü eklendi (B1/B2). Karar ölçütü değişmedi (yön isabeti + büyüklük hatası) | NDX günlük duman testinde iki VIX rejiminde de çoğunluk yönü aynı (yukarı) → isabet ölçütü bağlamın olasılık bilgisini göremez | yalnız duman testi hücresi (NDX 1d) görüldü; karar ölçütü sonuçla değiştirilmedi |
