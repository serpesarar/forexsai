# Ön kayıt — Korku genişliği: NDX korku gecesinde öteki ABD endeksleri de korkuda mı? (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## Gerekçe
K1 (§2.71) ABD'nin dört endeksinde çalışıyor (GI-02), Avrupa'da çalışmıyor (bu günkü `korku_kuresel_20261118`). CC-02: Russell
korkusu NDX'in kendi K1'i yokken NDX'e bilgi taşımıyor. Sınanmamış soru: **NDX K1 gecesinde korkunun genişliği** doz mu? Geniş korku
(Dow ve Russell de K1) zorunlu risk azaltımı demektir ve daha çok dönmesi beklenir. Dar korku ise teknolojiye özgü haber olabilir.

## Veri
NDX: Dukascopy 1m (K1 ve getiri). Genişlik: MT5 US30 ve US2000 M30 (2018 →), aynı K1 tanımı (16:00, TWAP 09:30–16:00 × 0,995 ∧ son
saat aşağı). Bağımsız tekrar: NDX getirisi MT5 NAS100 M30 ile.

## Hücreler (seçimsiz, tek doz sınaması)
NDX K1 geceleri (16:00 AL → ertesi 16:00), genişlik g = US30 ve US2000'den K1 olanların sayısı (0, 1, 2).
- Doz ölçütü: ESKİ (2018-04 → 2021-10) ve YENİ (2021-11 →) ikisinde de ort(g=2) > ort(g=0).
- **B:** iki dönemde de doğru ∧ tüm dönem g=2 − g=0 farkı P ≥ 0,95 ∧ NAS100 MT5 tekrarında da fark > 0.
- İki dönemde de doğru ama P < 0,95 → C+. Ters yönde iki dönemde de doğru → "dar korku daha iyi" C+ (aynı ölçütle).
- Değilse X (genişlik doz değil).
Bilgi: tekdüzelik (g=0 < g=1 < g=2), yıl dağılımı, risk (σ, en kötü).
