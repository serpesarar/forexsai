# GR-01 — Günlük endeks geri dönüşü — sonuç (2026-10-15)

Ön-kayıt: `PROTOCOL.md` (sonuçtan önce). Betik: `gr_test.py` (bir kez). Ham: `results/sonuc.json`.

**Karar:** Olgu gerçek (NDX/SPX/DAX'ta günlük getiriler negatif otokorelasyonlu), birincil S1 BRÜT ölçütü geçti — ama
**işlem stratejisi değil**: S1 "hep uzun"dan iyi değil, maliyet sonrası negatif, doğrulama döneminde ters işaretli.
Kazancın tamamı "düşüş gününden sonra al" bacağından geliyor (sonradan ayrıştırma; korku döner, coşku dönmez).
Sınıf: olgu B · simetrik strateji X · "düşüş sonrası al" C+ (sonradan, net Sharpe 0,27).

## Geliştirme (NDX nakit 2015-01 → 2025-11, 2.743 gün)
| Strateji | Ort. bp/gün | Yıllık Sharpe | P | Not |
|---|---|---|---|---|
| hep uzun (taban) | +6,59 | 0,75 | 0,996 | sürüklenme |
| **S1 = −sign(dün)** brüt | +6,36 | 0,72 | **0,994** | yarılar +5,2 / +7,8 → ön-kayıt ölçütü geçti |
| S1 net (1,5 p spread + 5 p/gece finansman) | −2,95 | −0,33 | 0,14 | maliyet sonrası negatif |
| S2 (MAC5 ağırlıklı) brüt | +0,77 | 0,09 | 0,63 | yok |
| S3 (S2 + otokorelasyon rejimi) brüt | −1,15 | −0,14 | 0,31 | yok |
| β (r_{t+1} ~ r_t) | −0,123 | — | P(β<0)=0,999 | olgu gerçek |

Ayrıştırma: düşüş gününden sonra ertesi gün **+14,7 bp** (Sharpe 1,53, %57,7 yukarı, 1.206 gün); yükseliş gününden sonra
**+0,2 bp** (1.537 gün). NDX'in 2015–2025 toplam getirisinin ~%98'i düşüş günlerini izleyen günlerde. Yıllara göre
11 yılın 8'inde düşüş sonrası > yükseliş sonrası (2015, 2019, 2023 ters); 2020 (+56,6 bp) ağır basıyor.
"Düşüş sonrası al" net (sonradan, aynı maliyetler): Sharpe 0,27 (P 0,84) — hep uzun brüt 0,75'in altında.

## Teyit
| Set | β (P β<0) | S1 brüt bp (P) | Düşüş sonrası / yükseliş sonrası bp |
|---|---|---|---|
| SPX 2015–2025-11 (ikincil) | −0,132 (0,992) | +3,7 (0,961) | +8,9 / +0,6 |
| **DAX 2020→ (bağımsız)** | −0,101 (0,976) | +1,2 (0,67) | +5,2 / +2,4 |
| **NDX doğrulama 2025-12→2026-09** (208 gün, MDE ≈ 24 bp) | −0,020 (0,68) | **−4,6** (0,26) | +4,5 / **+12,4** (ters) |

DAX'ta "düşüş sonrası al" net Sharpe ≈ 0.

## Okuma
- Negatif seri bağımlılık üç endekste var (Baltussen vd. 2019 ile uyumlu) ama işlenebilir kenar çoğunlukla sürüklenmenin
  zamanlaması: piyasa yükseliş gününden sonra ortalamada yerinde sayıyor, düşüş gününden sonra yükseliyor.
- CFD'de gecelik finansman (≈5 puan/gece) brüt kazancın %73'ünü yiyor → strateji olarak değersiz; vadeli/ETF'de ayrı ölçülmeli.
- Doğrulama dönemi güçsüz ve ters işaretli → ileri kanıt yok.
