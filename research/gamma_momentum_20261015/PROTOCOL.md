# Ön-kayıt — Gamma koşullu son yarım saat momentumu (NDX) — GM-01

> 2026-10-15, sonuç hesaplanmadan yazıldı. Kullanıcı isteği: "gamma koşullu son yarım saat momentumunu test et".
> Literatür: Baltussen, Da, Lammers & Martens (2021, JFE) — son 30 dk'yı günün geri kalanının getirisi (rROD) öngörür;
> etki opsiyon piyasa yapıcılarının net gamma'sı (NGE) NEGATİFKEN yoğun, pozitifken yok. Gao, Han, Li & Zhou (2018).
> Yerel önceki sonuç: koşulsuz sürüm NDX CFD'de yok (ME-06: 30m eğim −0,017, t −1,33).

## Veri
- Gamma: SqueezeMetrics `DIX.csv` (`data/DIX.csv`, 2026-10-15 indirildi; GEX = S&P 500 opsiyonlarından tahmini dealer gamma).
  **Vekil:** S&P 500 gamma'sı NDX için kullanılıyor (QQQ/NDX gamma'sı yok).
- Zamanlama: d günü kararında **d−1 gününün GEX'i** kullanılır (GEX gün sonu açık pozisyondan hesaplanır; d gününün
  değeri d'nin son yarım saatinde bilinmez).
- Fiyat: NDX CFD (NAS100, Pepperstone, UTC). Birincil: `research/ndx_gate_forge/data/long_30m_utc.parquet`
  (2021-06 → 2026-07-14). İkincil (vekil): `long_1h_utc.parquet` (2016-05 →). Uzatma: `research/ndx_pattern_motifs/data/bars_15m.parquet`
  30m'ye toplanarak 2026-07-15 → 2026-10-02 (hizalama örtüşen haftada sınanır).

## Tanımlar (New York saati, zoneinfo, DST-doğru)
- P_kapanış(d−1) = önceki NY işlem gününün 16:00 fiyatı (15:30 başlayan 30m barın kapanışı).
- **rROD(d)** = ln(P_15:30(d) / P_kapanış(d−1)) — 15:00 başlayan 30m barın kapanışı.
- **rL30(d)** = ln(P_16:00(d) / P_15:30(d)).
- Sinyal: yön = sign(rROD); kazanç = sign(rROD) · rL30 (log getiri; ayrıca NDX puanı).
- İkincil 1h vekil: rROD1 = ln(P_15:00 / P_kapanış(d−1)), rL60 = ln(P_16:00 / P_15:00).
- Dışlanan günler: ABD yarım günleri (Bağımsızlık Günü arifesi, Şükran Günü ertesi, Noel arifesi) ve bunların ertesi
  günü; gerekli barı eksik günler; önceki işlem günü > 4 takvim günü gerideyse.

## Hipotezler
- **H1 (birincil):** GEX(d−1) < 0 günlerinde ortalama sign(rROD)·rL30 > 0.
- **H2 (etkileşim):** ortalama kazanç (GEX < 0) − ortalama kazanç (GEX ≥ 0) > 0.
- **Kontrol:** GEX ≥ 0 günleri (etki beklenmez).
- İkincil, karar dışı: (a) 1h vekil, 2016-05 →; (b) GEX'in kendi önceki 252 gününe göre en düşük %20'si (göreli gamma);
  (c) eğim β (rL30 ~ rROD) GEX < 0 / ≥ 0.

## Bölümler
- **Geliştirme:** 2021-06-29 → 2025-11-30 (30m). İkincil vekil: 2016-05 → 2025-11-30 (1h).
- **Doğrulama (bir kez):** 2025-12-01 → 2026-10-02. Bu dönem ME-07'de başka bir hipotez (gece ipucu) için bir kez açıldı;
  bu hipotez orada hiç sınanmadı. Beklenen negatif-GEX günü ≈ 10 → **güç yok; sonuç önceden "bilgi amaçlı" sayılır**.

## Geçme ölçütleri (geliştirme)
- H1: GEX < 0 günlerinde ortalama kazanç > 0, gün-bootstrap (B = 10.000, gün bağımsız: günde tek gözlem) tek yönlü
  P ≥ 0,975; isabet > %50; iki kronolojik yarıda da > 0; ortalama kazanç NDX puanında > 1,5 puan (spread).
- H2: P ≥ 0,95.
- Hepsi geçerse "gelişmede geçti" (B sınıfı); kesinleşme yalnız ileri gölge dönemle (≥ 30 negatif-GEX günü).
- Tek yük: H1 ve H2 (iki test); ikincil analizler karar vermez.
