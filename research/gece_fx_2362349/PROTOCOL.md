# Hesap 2362349 (IC Markets, 30 FX çifti, gece/rollover scalper'ı) — GF — 2026-11-25
Ham veri ~/Downloads (push edilmez). 898 işlem 2026-01 → 11, 240 $ → +1.262 $, 11/11 ay artı, isabet %94 (başabaş %81), kazanç ~+5 pip /
kayıp ~−23 pip (en kötü −157), lot bakiyeyle (ρ 0,95), ızgara %9, eşzamanlı ≤ 12.
**GF-1 (betimleyici, sonuç görüldü):** eşit lot +4,29 bp P 1,00 (yarılar +5,1 / +3,4). Gerçek bid/ask kopya (6 çift, 392 işlem, +1 dk):
+2,53 bp (P 1,00, %78), aynı hafta × NY 15 dk × yön rastgele −2,58 → **zamanlama +5,11 bp (P 1,00)**; spread ×1,5 +0,55. GBPAUD −1,8.
Anatomi (majör, n 329): NY 17:00–17:59 (rollover/gün açılışı) 126, 16:00 53, 08–10 83, Pazar açılışı 47; yöne göre 60 dk konum medyan 0,15
(dipte alış), 60 dk harekete ters %75; kazanan ~+5 pip, kaybeden medyan tutuş 37 sa.
## GF-2 — rollover açılışında aralık ucundan dönüş (ÖN KAYIT, GF-2 sonuçları görülmeden)
Defter: DH-4/EK-1 (gece dönüşü, majör, 2018–26) X — ama spread ≤ 1,5 pip süzgeci rollover dakikalarını DIŞLAMIŞTI; bu hesabın girişleri tam o dakikalarda.
Kural (dh4_gece motoru, spread süzgeci YOK, eksik ask yıl × NY 15 dk medyanıyla, E154): karar dakikası i, giriş i+1 açılışı (alış ask);
AL: konum60 ≤ q ∧ mom15 ≤ −1·ATR60; SAT ayna. TP 5 pip (hesap), SL {25; 50} pip, süre {360; 2.880} dk, çift başına tek pozisyon, komisyon 0,7 pip.
Pencere NY: RO 16:55–17:20 (rollover açılışı) · SA 08:00–10:59 · AK 16:00–16:54. q {0,15; 0,05}. → 3 × 2 × 2 × 2 = 24 hücre.
Çiftler EURUSD, GBPUSD, AUDUSD, USDCAD (Duka 2018→). **KEŞİF 2018–21 → TEST 2022–25 (tek atış) → KÖR 2026-01 → 11 (hesap dönemi).**
KEŞİF geçme: DH-4 ölçütleri (n ≥ 150, ort > 0, P ≥ 0,95, iki yarı > 0, spread ×1,5 + komisyon 1,0 > 0); en çok 2 aday (günlük toplam R).
TEST geçme: aynı + aynı hafta × NY 15 dk × yön plaseboya fark P ≥ 0,95 + 2022–25 her yıl > 0 + 4 çiftin ≥ 3'ü artı + en kötü işlem raporlanır.

### GF-2 sonucu (değiştirilmez) — `results/g2_kesif.json`, `results/g1.json`
**KEŞİF 2018–21: 24 hücrenin hiçbiri geçmedi → TEST yok.** RO (rollover açılışı) ≈ 0: en iyi SL 50 / 2.880 dk +0,0037 R (+0,19 pip), isabet %86,7
= başabaş %86,1, P 0,74, spread ×1,5 −0,025; SA (NY sabahı) 8/8 eksi (−1,4…−1,6 pip, P 0,00); AK (16:00–16:54) 8/8 eksi.
**Okuma:** hesabın kendi zamanlaması gerçek (GF-1: kopya +2,5 bp, rastgele aynı hafta × NY 15 dk × yön −2,6 bp, fark P 1,00) ama gözlenen
ortak imza (rollover/aralık ucu/ters momentum + TP 5 pip) mekanik kural olarak başabaşta → seçim kuralda yakalanamıyor (KH-14 ile aynı desen).
Kopya yolu (sinyal aboneliği) betimleyici: +2,5 bp/işlem ama spread ×1,5'te +0,55 bp, kayıplar günlerce tutuluyor (en kötü −157 pip),
11 aylık ve listeden seçilmiş hesap (KH-15 uyarıları). **Hüküm: X (kural); kopya = yüksek kuyruk riskli, kanıtı kısa.**
