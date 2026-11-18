# Birleşik korku gecesi — skor dozu, felaket stopu, kesişimler, canlı portföy (2026-11-18)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md). Kod: `src/kb.py`. Kart: `backend/data/evolution/go_live_cards/ndx_korku_birlesik.json`.

## Yeni taktikler (özet)

| taktik | kanıt | sınıf |
|---|---|---|
| **1. Çift teyitli korku gecesi:** dört korku tetiğinden en az 2'si aynı anda (S ≥ 2) → 16:00 AL, ertesi 16:00 | n 287, +52,3 bp; 2018–21 +58,5, 2021–26 +48,0; MT5, EET30 ve NQ'da aynı. Tek tetik (S = 1) ≈ 0 | C+ (ön kayıtlı doz kovalarından; post-hoc eşik) |
| **2. Korku gecesi + ters VIX eğrisi = doz artır** | +119,2 vs +18,2 bp (n 64); iki dönemde de (+98 / +153), P %99,6 | **B** (Bonferroni 5 hücre geçti) |
| **3. Korku gecesi + C3b aynı gün = doz artır** | +66,8 vs +22,0 bp (n 101); +72 / +64, P %98,3 | **B** |
| 4. Korku gecesi + VIX ≥ 18,4 / ay sonu | +38 vs +18 / +53 vs +26 | C+ |
| 5. **Felaket stopu kullanma** | %2 / %3 / %4 stopların hepsi her veride işlem başına Sharpe'ı düşürüyor (toparlanmadan önce çıkarıyor). Risk lotla yönetilmeli | yönetim kuralı |
| 6. Cuma (hafta sonu taşıması) | +20 vs +33 | X — Cuma korku gecesi daha zayıf |

Tetikler (16:00 girişi, ertesi 16:00 çıkışı):
- 2h büyük alt fitil (12 sa) ∧ son saat aşağı,
- TWAP'ın ≥ %0,5 altı ∧ son saat aşağı,
- son saat ≤ −%0,3,
- aralık ≥ %2 ∧ açılış altı ∧ son saat aşağı.

## Bölüm 1 — birleşik kural ve doz

| veri | birleşik (S ≥ 1) | S = 0 taban | S1 (ESKİ / YENİ) | S2 | S ≥ 3 |
|---|---|---|---|---|---|
| Dukascopy | +30,9 (n 509) | −4,2 | −5,3 / +9,0 | +35,7 / +54,0 | +83,6 / +42,1 |
| MT5 | +30,1 | −4,3 | −2,1 / +20,0 | +19,3 / +38,6 | +94,5 / +40,1 |
| EET30 | +30,3 | −3,7 | −0,2 / +13,3 | +20,9 / +42,8 | +99,6 / +33,2 |
| NQ | +38,4 | −6,2 | +26,9 / +15,6 | +35,6 / +59,7 | +105,9 / +32,0 |

**Ders:** tek bir korku belirtisi yetmez; iki ya da daha fazla belirti aynı anda olunca ertesi gün toparlanması güçlü. Bu,
"teyit sinyal ölçeğinde iyi" (§3-3) ilkesinin gece hâli.

## Bölüm 3 — canlı portföy (C3b + ORB × VIX + KSG + CAPREV)

| | Sharpe TÜM / ESKİ / YENİ | maxDD (risk birimi) |
|---|---|---|
| canlı 4 kol | 1,54 / 1,38 / 1,66 | −1.657 |
| + birleşik korku gecesi (S ≥ 1) | 1,45 / 1,42 / 1,48 | −1.725 |
| + çift teyitli (S ≥ 2), keşif | 1,56 / 1,65 / 1,50 | **−1.230** |

**Ders:** korku gecesi, canlı portföyde büyük ölçüde zaten var. Ortak günlerde korelasyon CAPREV ile 0,91, C3b ile 0,66, KSG ile
yüksek. Tümünü eklemek Sharpe'ı düşürüyor. Çift teyitli sürüm düşüşü ~%25 azaltıyor, ama son dönem Sharpe'ı da düşürüyor.

**En verimli kullanım yeni kol açmak değil, doz:**
- korku gecesi ∧ (ters VIX eğrisi ya da C3b) olduğunda mevcut kolların (C3b / KSG) lotunu büyütmek,
- tek tetikli korku gecesinde pozisyon açmamak.

## EK-1 — kısa TP'li korku gecesi (S ≥ 2): X

| çıkış | ESKİ | YENİ | isabet | işlem başına Sharpe (ESKİ / YENİ) | ort tutuş |
|---|---|---|---|---|---|
| TP yok (ertesi 16:00) | +58,5 bp | +48,0 | %61–64 | 0,280 / 0,245 | 34 sa |
| TP %0,8 | +32,3 | +25,3 | %77–78 | 0,325 / 0,231 | 25 sa |
| TP %0,5 | +21,4 | +17,5 | %84–86 | 0,259 / 0,193 | 21 sa |
| TP %0,3 | +10,4 | +9,4 | %89–92 | 0,141 / 0,125 | 16 sa |

- Kısa TP isabeti %90'a çıkarıyor ama ortalamayı beşte birine indiriyor.
- En kötü işlem değişmiyor (−612 bp): kötü geceler TP'ye hiç ulaşmıyor.
- Hiçbir TP iki dönemde birden TP'sizden yüksek Sharpe vermiyor.
- **Korku gecesinin kazancı toparlanmanın kuyruğunda.** Erken TP onu kesiyor. "Braket ≠ zaman" (§3-5) yeniden.
