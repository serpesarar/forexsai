# Saniye ölçeğinde XAU stratejileri (TS) — ÖN KAYIT (2026-11-25, hiçbir TS hücresi koşulmadan)
Kullanıcı: "saniyelik çıkışlarda daha fazla strateji geliştir". Çıkış noktası: scalper hesapları 2385027/2365400 (AR-07…09) — girişleri
5 sn'de ≥ 1,5 $ sıçrama ∧ ~100 sn'lik ~6 $ koşu içinde; kendi işlemleri 1 sn gecikmeyle hâlâ + (+0,66 / +0,16 $/ons) ama mekanik tetik
kontrol pencerelerinde − (SP-4). Defter: tick düzeyinde XAU stratejisi hiç sınanmadı; BTC meta-dersi 12 (perakende maliyetle scalping yok,
mikro sinyaller maliyet mertebesinde) ve E67 (spread yol içinde) → dolumlar gerçek bid/ask tick'inden.
**Veri:** kutu tick arşivi XAUUSD (Pepperstone, 2026-09-01 → 11-25; time_msc sunucu saati → UTC'ye çevrilir). KEŞİF 09-01 → 10-20,
TEST 10-21 → 11-25 (tek atış). Kısa örneklem → sonuçlar en iyi ihtimalle "gölge adayı".
**İcra modeli:** tetik tick'inden 1.000 ms sonraki ilk tick'te giriş (alış ask / satış bid); çıkış alışta bid / satışta ask yolu üzerinde
TP/SL'yi ilk geçen tick'in fiyatından (kayma dahil), süre dolunca ilk tick; komisyon 0,07 $/ons (Razor ≈ 7 $/lot gidiş-dönüş); tek pozisyon.
Ek gecikme duyarlılığı: 500 / 2.000 ms (yalnız seçilen hücreler).
**Aileler:**
- TS-A patlamaya bin: y = işaret(Δmid_W); |Δmid_W| ≥ k $, W {2; 5; 10} sn × k {1,0; 1,5; 2,0} × trend süzgeci y·Δmid_180 ≥ {0; 4} $,
  çıkış TP {0,5; 1; 2} $ × SL {1,5; 3} $ × süre {15; 60} sn → 216 hücre.
- TS-B patlamayı sön (ayna): aynı tetik, yön −y → 216 hücre.
- TS-C tick hızı patlaması kırılımı: son 10 sn tick sayısı ≥ m × önceki 10 dk ortalaması (m {3; 5}) ∧ fiyat önceki 5 dk tepesi/dibinin
  ötesinde → kırılım yönü; aynı 12 çıkış → 24 hücre.
**Plasebo:** her işlem için aynı UTC saatinde rastgele tick, aynı yön ve çıkış. **KEŞİF geçme:** n ≥ 200, ort > 0 (maliyet sonrası),
gün bloklu P ≥ 0,95, iki yarı > 0, plaseboya fark > 0 ∧ P ≥ 0,95; aile başına en çok 1 aday (ort × n / gün sırasıyla). **TEST geçme:**
ort > 0, P ≥ 0,90, plaseboya fark > 0, 2.000 ms gecikmede de ort > 0 → GÖLGE adayı (canlı için en az 3 ay ileri gölge).

### TS KEŞİF sonucu (değiştirilmez) — `results/ts_kesif.csv/json`
Veri: 36 gün, 18,6 M tick (2026-09-01 → 10-20); spread ort 0,115 $, maliyet ≈ spread + 0,07 $ komisyon ≈ 0,185 $/ons/işlem.
**456 hücreden hiçbiri geçmedi → TEST atışı yok.** Maliyet sonrası artı yalnız 2 hücre (aile C, n 5–6, anlamsız).
- **A patlamaya bin (216):** medyan −0,279 $; plasebodan KÖTÜ 216/216 (fark medyan −0,146 $) → 1 sn gecikmeyle girince patlama devam etmiyor, geri dönüyor.
- **B patlamayı sön (216):** medyan −0,130 $; plasebodan İYİ 213/216 (fark medyan +0,045 $, en iyi +0,096 $, P 1,00) → **bilgi gerçek ama brüt kenar
  (en iyi ≈ +0,11 $) maliyetin (≈ 0,185 $) altında**; k 2,0 daha kötü.
- **C tick hızı kırılımı (24):** Pepperstone akışında tick hızı 3–5× nadiren (≤ 0,6 olay/gün) → sınanamaz kadar seyrek.
**Hüküm: X** — saniye ölçeğinde (1 sn gecikmeli perakende icra) XAU'da maliyeti aşan kural yok; scalper'ın kârı (AR-07…09) sıfır gecikmeli icra ve
seçimdedir. Kaldıraç sinyalde değil maliyette: brüt +0,11 $'lık sönme etkisi ancak gidiş-dönüş maliyeti ≤ ~0,08 $ olan bir hesapta artıya döner (sınanmadı).
