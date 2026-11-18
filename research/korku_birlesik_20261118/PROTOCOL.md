# Ön kayıt — Birleşik korku gecesi: skor dozu, felaket stopu, kesişimler, canlı portföy (2026-11-18)

Sonuçlara bakılmadan yazıldı. Kullanıcı: "bulduğun pozisyonları kombine ederek farklı stratejiler, yeni taktikler; yetinme."

## Bileşenler (önceden doğrulandı; burada yeniden seçilmez)

Hepsi 16:00 girişli (tek pozisyon için ortak giriş), ertesi işlem günü 16:00 çıkışlı. KSG = 15:00 → 16:00 aşağı.

| tetik | koşul | kaynak |
|---|---|---|
| T_f | son 12 sa içinde 2h büyük alt fitil (≥ %0,50, üst ≤ alt/2) ∧ KSG | §2.70, 16:00 girişli hâli |
| T_k1 | 16:00 fiyatı TWAP'ın ≥ %0,5 altı ∧ KSG | §2.71 |
| T_k3 | 15:00 → 16:00 ≤ −%0,3 | §2.71 |
| T_k4 | gün içi aralık ≥ %2 ∧ 16:00 < 09:30 açılışı ∧ KSG | §2.71 KG-04, C+ |

**Korku skoru** S = tetiklerin sayısı (0–4).

## Bölüm 1 — Birleşik kural (tek pozisyon) + doz + felaket stopu

- **Birleşik U:** S ≥ 1 → 16:00 AL, ertesi 16:00 çık.
- **Doz:** S = 1, S = 2, S ≥ 3 kovalarının ortalama net bp'si.
  - Doz ölçütü: ESKİ'de ve YENİ'de **ikisinde de** S≥3 > S=2 > S=1 (tekdüze) → "skor dozu" taktiği B.
  - Yalnız S≥3 > S=1 iki dönemde de doğruysa C+.
- **Felaket stopu:** girişten itibaren 1m dip ≤ giriş × (1 − s) olursa stop fiyatından (boşlukta açılıştan) çık. s ∈ {yok, %2, %3, %4}.
  - Ölçüt: stoplu sürümün ort / σ oranı (işlem başına Sharpe) iki dönemde de stopsuzdan büyük ve ortalama > 0 → o stop seviyesi
    önerilir.
  - Birden fazla geçerse en küçük en kötü işleme sahip olan.
- Beslemeler: MT5, EET30, NQ'da U'nun ortalaması > 0 olmalı. Doz ve stop besleme verisinde de raporlanır; NQ 5m'de stop 5m dibiyle.

## Bölüm 2 — Kesişimler (U üzerinde; seçimsiz, 5 hücre)

| hücre | koşul |
|---|---|
| H1 | ters VIX eğrisi (d−1 VIX/VIX3M ≥ 1) |
| H2 | dünkü VIX ≥ 18,4 |
| H3 | C3b aynı gün aktif (15:30 RSI2(günlük) < 10) |
| H4 | Cuma girişi (hafta sonu taşıması) |
| H5 | ayın son 3 işlem günü |

Her hücrede U ∧ H vs U ∧ ¬H. ESKİ ve YENİ'de **ikisinde de** fark > 0 ve tüm dönem P ≥ %90 → "doz artırıcı" (C+). Yalnız bilgi;
Bonferroni 5 hücre (P ≥ %98) geçerse B.

## Bölüm 3 — Canlı kurallarla portföy (2018–26 Dukascopy)

Canlı/kanıtlı kollar (`rules.py`): C3b, ORB × VIX TP 3R, KSG (16:00 → 09:30), CAPREV. Yeni kol: U (Bölüm 1'in önerilen stop
sürümü).

- Günlük P&L (bp; her kol eşit risk: işlem başına σ'ya göre ölçek). Aynı gün birden çok kol açıksa toplanır.
- Ölçüler: yıllık getiri, Sharpe (günlük → √252), maxDD, kollar arası korelasyon (ortak aktif günlerde, E118).
- **Ölçüt:** U eklenince Sharpe ESKİ'de ve YENİ'de ikisinde de artar ∧ maxDD %20'den fazla kötüleşmez → "portföye eklenmeli" önerisi.
- Not: KSG ve U çok örtüşür. U eklenirken KSG ile aynı gece çift pozisyon olmaması için KSG'nin U'lu geceleri U'ya devredilir.

## EK-1 (2026-11-18, sonuçlardan önce) — kısa TP'li korku gecesi

Kullanıcı: "kısa TP'li işlemler". Çift teyitli korku gecesinde (S ≥ 2) 16:00 AL:
- TP ∈ {+%0,3, +%0,5, +%0,8} (bid yolu 1m), stop yok, ertesi 16:00 zaman çıkışı; taban TP yok.
- 2 dönem (ESKİ / YENİ) × 4 = 8 hücre, seçim yok.

Ölçüler: ort bp, isabet, işlem başına Sharpe, ortalama tutuş süresi, en kötü. TP'li bir sürüm iki dönemde de TP'siz sürümden daha
yüksek işlem başına Sharpe veriyorsa "kısa TP'li korku gecesi" taktiği C+. Seçim yapılmadığı için tek başına B olamaz.
