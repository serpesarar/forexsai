# QS-03 — Zorunlu akış ve takvim: rapor (2026-11-11)

Ön kayıt `PROTOCOL.md`. Kod: `veri.py`, `r1_dengeleme.py`, `r1_teshis.py` (sonradan teşhis), `r1_kart.py`, `r1_duyarlilik.py`
(betimsel), `r2_r4.py`, `r2_havuzP.py`. Sonuçlar `results/*.json`; kart `backend/data/evolution/go_live_cards/qs03_r1_dengeleme.json`.
Deneme sayacı: 3 ön-kayıtlı hipotez (R1, R2, R4).

## Özet
| ID | Fikir | Sonuç | Sınıf |
|---|---|---|---|
| **R1** | **Ay sonu hisse/tahvil dengeleme akışı** | ön-kayıtlı 5/5, kart 6/6, mekanizma teşhisi tutarlı, 36/36 duyarlılık kurgusu artı | **B** — GÖLGE önerisi |
| R2 | Tatil öncesi gün | ABD TEST +9,9 bp (P 0,94), yabancı 10/12; KEŞİF P 0,78, 1985-98 −1,5 | C+ |
| R4 | Fed net likiditesi (WALCL − TGA − RRP) | KEŞİF +43 bp/hafta fark → TEST +11 (P 0,70), 2015-19 +5 | X |

## R1 — kural
Ayın son işlem gününden 3 gün önce (D−3) kapanışta: Δ = SPY'ın ay içi getirisi − TLT'nin ay içi getirisi.
- Δ ≥ +%2 (hisse tahvili çok geçti → dengeleyen fonlar hisse SATACAK) → NAS100 **KISA**
- Δ ≤ −%2 (tahvil hisseyi çok geçti → fonlar hisse ALACAK) → NAS100 **UZUN**
- Tutuş D−3 → D (3 işlem günü). Ayda en çok bir işlem, yılda ~8–9.
Mekanizma (Harvey, Mazzoleni & Melone): sabit oranlı fonlar (emeklilik, hedef-tarih, 60/40) ay sonunda oranı geri kurar; akış önceden
hesaplanabilir ve büyüklüğü farkla orantılı. Fiyatın kendi mumundan değil, **başkasının zorunlu işleminden** gelen bilgi (§3-21).

## R1 — ön-kayıtlı ölçütler
| # | Ölçüt | Sonuç | |
|---|---|---|---|
| 1 | KEŞİF 2002-13 QQQ+SPY havuz | +32,0 bp (n 202), P 0,984; QQQ +19,4, SPY +44,5, IWM +68,9, DIA +39,0 | ✓ |
| 2 | TEST 2014-26 | QQQ +44,4 (P 0,99), SPY +41,0; havuz +42,7, P 1,00; iki yarı +44 / +41 | ✓ |
| 3 | Eğim (pencere getirisi ~ Δ) | KEŞİF QQQ −4,4 bp/%1 (t −1,6; SPY t −3,9) · TEST −6,4 (t −2,1) | ✓ |
| 4 | Bağımsız 1990-2002 (^GSPC + sentetik tahvil) | +5,4 (P 0,60), eğim t −1,3 — zayıf ama artı | ✓ (zayıf) |
| 5 | Broker NAS100 2018-26 | +32,2 bp (n 61, P 0,88) | ✓ |

## R1 — teşhis (sonradan; mekanizma mı, sıradan geri dönüş mü?)
Ön kayıttaki plasebo (ay ortası D−13) +13…+30 bp çıktı → kazanç "ay içi düşüşten dönüş" olabilir mi diye ayrıldı:
- **TEST 2014-26:** yalnız-hisse kuralı QQQ +6,5 / SPY +7,3 (boş); yalnız-tahvil kuralı +35,7 / +33,9; iki değişkenli regresyonda
  **tahvil katsayısı +9,8 (t 2,2) / +9,1 (t 2,75), hisse katsayısı anlamsız** → dengeleme akışının öngördüğü işaret.
  KEŞİF'te hisse geri dönüşü de payını alıyor (SPY hisse t −2,5).
- **Ay içi profil (2002-26, 3 gün tutuş):** sinyal D−3 +38,8, D−4 +31,4, D−5 +32,2, D−6 +19,6; ayın geri kalanı (D−7…D−18)
  ortalama ≈ −1 bp; D−1/D−2 (tutuş yeni aya taşar) −18 / −5. Artı ayın **son haftasına** özgü. D−13 ölçümü gürültünün üst ucu.
- **Bacaklar:** QQQ uzun +63 (n 78, P 0,97), kısa +16 (n 128, P 0,89). Broker 2018-26: uzun +104 (n 18), kısa +0,2 (n 42) —
  son dönemde kazanç uzun bacaktan ("korku döner, coşku dönmez" ile uyumlu).

## R1 — canlıya alma kartı (2. KURAL): **6/6**
hacim 206 (QQQ) · beklenti +34,0 bp P 0,988 · yarılar +19,1 / +48,9 · broker gerçek icra × 1,5 spread +30,5 · icra farkı
(16:00 iyimser vs 16:30 gerçek giriş) 0,8 bp · tek pozisyon. Yıl 17/25 artı, en iyi 5 hariç +20,6 bp.
**Canlı C3b ile çakışma:** işlemlerin %20'sinin penceresinde RSI2<10 var; C3b'siz aylar +36,1 bp (P 0,99) → bağımsız kaynak.

## R1 — duyarlılık (betimsel)
TLT / IEF / sentetik 10 yıl × eşik %1, %1,5, %2, %3 × sinyal D−3, D−4, D−5: **36/36 artı**, +14…+43 bp, 30'unda P ≥ 0,90.

## Ne yapılmalı
- **GÖLGE (öneri):** her ay D−3 16:00'da Δ'yı hesapla, işareti ve sonucunu kaydet. Gerekli veri: SPY ve TLT günlük kapanışı
  (yfinance yeterli; bot tarafında MT5 sembolü gerekmez) + ay takvimi. İcra NAS100 16:30 ET → D 16:30.
- Canlıya alma kararı kullanıcıda. Öneri: kısa bacak son dönemde ≈ 0 olduğu için ilk aşamada **yalnız uzun bacak** ya da iki bacak
  küçük lotla; işlem başına ~30 bp × yılda ~8–9 ≈ +250 bp/yıl (iki bacak), uzun bacak tek başına ~3–4 işlem/yıl × ~60–100 bp.
- Bilinen riskler: akış yayımlanmış bir bulgu (2023) — yayın sonrası zayıflama olabilir (KT-02 ay dönümü söndü); 1990-2002'de zayıf.

## R2 — tatil öncesi (C+)
ABD 4 fon (tarih başına ortalama fazla): KEŞİF 1999-2012 +9,5 bp (P 0,78) · TEST 2013-26 +9,9 (P 0,94; yarılar +5 / +15).
Yabancı 12 endeksin 10'unda tabanın üstünde (AEX +10,9, FCHI +15,7, IBEX +19,5, GSPTSE +13,0, SSMI +9,7…; MXX, TWII eksi), işaret
p 0,019. ^GSPC 1985-98 −1,5 → ölçüt 4 düştü. Yılda ~9 gün × ~10 bp. KSG ile aynı gece yapısında olabilir; canlı öneri yok, gölge etiketi.

## R4 — net likidite (X)
NL 4 haftalık artışta sonraki hafta QQQ: KEŞİF +42,6 vs −0,9 bp (fark P 0,97) → TEST +39,8 vs +29,1 (P 0,70), 2015-19 fark +4,7.
2020 sonrası anlatı 2003-14 verisine uyuyor ama sonrasında ayırt etmiyor.
