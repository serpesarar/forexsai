# Ön kayıt — Kaldıraçlı ETF (TQQQ/SQQQ) kapanış dengelemesi: son dakikalarda günün yönüne itiş (2026-11-18)

Sonuçlara bakılmadan yazıldı. Kullanıcı: "algoların sistemini analiz edip karşısında işlem türet; son 5 yıl yapı değişti".

## Mekanizma
Günlük kaldıraçlı ETF'ler kaldıracı korumak için kapanışa doğru ΔPozisyon ≈ L·(L−1)·r·AUM kadar işlem yapar. TQQQ (L = 3) ve SQQQ
(L = −3) için L(L−1) > 0 → ikisi de **günün yönünde** alım/satım yapar. Akış mekanik ve önceden hesaplanabilir; büyüklüğü 2018 →
2026'da katlandı. Defter: MA-04 yalnız endeksler arası dolaylı sınama (X); GN-02 MOC penceresinin geceye etkisi; GM-01 15:30 momentumu
gamma koşullu (kanıtı zayıf). Aynı gün son 15/30 dk sınanmadı.

## Veri
NDX Dukascopy 1m (ana; spread bar değeri). Bağımsız: MT5 NAS100 2m (2017 → 2026; 15:30 / 15:44 / 16:00 barları), NQ 5m (2019–24).
Dönemler: ESKİ YAPI 2018-04 → 2021-10 (karşılaştırma), KEŞİF 2021-11 → 2024-06, TEST 2024-07 → 2026-11.

## Kural
- R = P(E) / P(09:30) − 1, E ∈ {15:30, 15:45} (MT5'te 15:44). σ = önceki 20 günün aynı R std'si.
- |R| ≥ k·σ, k ∈ {1,0, 1,5} → E'de sign(R) yönünde gir, 16:00'da çık (aynı gün). 4 hücre.
- Taban: yönsüz (0). Bilgi: |R| beşte birlik dilimlerinde ortalama (doz), aynı işlemin ertesi 09:30'a taşınmış hâli (geri dönüş var mı).

## Seçim / doğrulama
KEŞİF'te n ≥ 50, ort > 0, P ≥ 0,90 → t'ye göre ≤ 2 hücre dondurulur. TEST: ort > 0 ∧ P ≥ 0,975; MT5 2m TEST: ort > 0; spread × 1,5 ile
TEST ort > 0. Hepsi → B; P hariç → C+; değilse X. **Yapı değişimi:** ESKİ YAPI etkisi < KEŞİF ve TEST etkisi ise yazılır.
