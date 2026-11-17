# akntrade — 1H iğne → 15m süpürme → 5m/3m CHoCH → FVG geri çekilmesi (NDX, 9 yıl) — rapor (2026-11-16)

Ön kayıt `PROTOCOL.md` (+ EK-0, yalnız olay sayılarıyla, sonuç görülmeden).
- Veri: NDX Dukascopy 1m 2018-01 → 2026-11, gerçek bar spread'i.
- Motor `akn.py`, testleri `test_akn.py` + `test_sirali.py`.
- Örnek grafikler `grafik/*.png`.

**Hüküm:**
- Birincil (EK-0 iç içe okuma) P1–P3: **X**. Üç dönemin üçünde de eksi; bootstrap P(EV > 0) 0,01–0,02.
- Asıl ön kayıtlı sıralı okuma: artı ve kontrolleri geçiyor, ama 9 yılda yalnız 39–43 işlem (yılda ~4). n ≥ 150 ve Holm ölçütü düşüyor → **C**.

## 1) Strateji ve tespit kuralı
| katman | videodaki söz | motor (`akn.py`) |
|---|---|---|
| K1 1H | "mum küçük, iğne uzun, likidite süpürüldü" | 1H barı aktif 1H fraktal tepeyi fitille aşar, altında kapanır; üst fitil ≥ %50 aralık, gövde ≤ %33 |
| K2 15m | "yeşil mumla süpürme, sonraki mum kırmızı" | iki okuma (aşağıda) |
| K3 CHoCH | "5m'de 5–6 mum, yoksa 3m'ye in" | onay anında bilinen en son LTF fraktal dibinin altında kapanış, 60 dk içinde; önce 5m 6 bar, 3m de devrede |
| K4 FVG | "ilk dokunuş ya da 0,5" | CHoCH bacağındaki ayı FVG; satış limiti alt kenarda (E1) ya da ortada (E50), 60 dk |
| stop / hedef | "likiditenin biraz üstü; en yakın likidite ya da order block" | süpürme ucu + 1 tick; T1 = en yakın 15m fraktal dip (≥ 0,5R), T2 = en yakın 1H fraktal dip (≥ 1R); 24 sa |

İki 15m okuması:
- **Sıralı (ilk ön kayıt):** 1H iğnesi kapandıktan SONRA yeni bir 15m yeşil süpürme + kırmızı mum.
- **İç içe (EK-0):** 1H iğnesinin ucunu yapan 15m mumu yeşil, sonraki kırmızı (videonun 3. karesi).

EK-0 sayımında sıralı okuma 9 yılda 39 işlem verdi. Bu yüzden birincil iç içe okumaya alındı (193 işlem).

## 2) Birincil sonuç (iç içe okuma, C53)
| ID | giriş · hedef | n | ort.R (P) | A 2018–20 | B 2021–23 | C 2024–26 | ayna | zaman plasebosu | SAT / AL |
|---|---|---|---|---|---|---|---|---|---|
| P1 | ilk dokunuş · T1 | 215 | **−0,186** (0,01) | −0,26 | −0,12 | −0,19 | +0,02 | −0,23 (%83) | −0,25 / −0,11 |
| P2 | %50 · T1 | 193 | **−0,184** (0,02) | −0,22 | −0,17 | −0,17 | −0,03 | −0,25 (%89) | −0,28 / −0,07 |
| P3 | %50 · order block (T2) | 193 | **−0,207** (0,02) | −0,12 | −0,21 | −0,28 | −0,03 | −0,25 (%77) | −0,41 / +0,03 |

- T1 hedefi medyanda 1,42R ötede, başabaş için ~%41 isabet gerekiyor; gerçekleşen %34.
- Kayıp en çok SAT tarafında (−0,28 / −0,41). AL tarafı sıfır civarı — defterdeki "korku döner, coşku dönmez" ve FR-15 ile aynı yön.
- Videonun "1m'de %50 isabet" sözü: iç içe C1 %38,5 (−0,15R), sıralı C1 %47 (+0,12R, n 73).

## 3) Katman katkısı (C53, ilk dokunuş · T1)
| zincir | n | ort.R |
|---|---|---|
| yalnız CHoCH + FVG (her 15m fraktal tepe/dip sonrası) | 12.305 | −0,106 |
| yalnız 15m renk-dönüşlü süpürme (1H yok) | 1.383 | −0,092 |
| yalnız 1H iğnesi (15m yok) | 386 | −0,114 |
| 1H + 15m iç içe (birincil) | 215 | −0,186 |
| 1H + 15m sıralı | 43 | **+0,332** |

CHoCH + FVG girişi tek başına her yerde −0,1R civarı (SM-01, HL-02a ile tutarlı). İç içe katman eklemek sonucu düzeltmiyor, kötüleştiriyor.

## 4) Sıralı okuma (C adayı, post-hoc kontroller `results/sirali_tani.json`)
| hücre | n | ort.R | medyan | en büyük işlem hariç | ayna | plasebo | spread × 1,5 | yıl + |
|---|---|---|---|---|---|---|---|---|
| %50 · T1 | 39 | +0,408 | +0,53 | +0,30 | +0,05 | %100 | +0,315 | 6/9 |
| ilk dokunuş · T1 | 43 | +0,332 | +0,55 | +0,24 | +0,04 | %96 | +0,276 | 6/9 |
| %50 · T2 | 39 | +0,601 | −1,0 | +0,36 | +0,21 | %99,5 | +0,385 | 7/9 |
| %50 · 1R | 39 | +0,232 | +1,0 | +0,21 | −0,23 | %100 | +0,137 | 6/9 |

- Dönemler (%50 · T1): A +0,07 (12), B +0,22 (17), C +1,14 (10). SAT +0,46 / AL +0,31.
- Hedefli önek sızıntı testi 5 işlemde geçti.
- Okuma, iç içe okumayla aynı motoru ve aynı tanımları kullanıyor.

**Neden yalnız C:**
- Yılda ~4 işlem; 9 yılda 39. Dönem başına 10–17 işlem.
- Aynı ~40 olayın 32 korele hücresinden biri. Holm'u geçmiyor (en küçük p 0,035).
- Bağımsız sembolde sınanamadı: elde 1m DAX/XAU yalnız 9 ay, bu sıklıkta ~3 işlem eder.
- Mekanizma: iğneden sonra fiyatın aynı bölgeyi ikinci kez yoklayıp yine reddedilmesi ("ikinci başarısız itme"). Makul, ama bu az örnekle kanıtlanmış değil.

## Sonuç
- Videonun anlattığı zincir NASDAQ'ta, videonun kendi çizimine en yakın iç içe okumayla, 9 yılın her döneminde kaybettiriyor (−0,18 … −0,21R/işlem).
- Kayıp, CHoCH + FVG girişinin kendisinden geliyor; sweep ve 1H iğnesi bunu düzeltmiyor.
- Tek ilginç iz sıralı okumanın seyrek olaylarında. İşlem kuralı değil, gölge kaydı adayı (yılda ~4 olay, ileri doğrulama yıllar sürer).
- Canlıya veya gölgeye bağlanan bir şey yok. Defter: §2.63 AK-01…03.

Yeniden üretim: `sayim.py` → `test_akn.py` → `run.py` (~8 dk) → `sirali_tani.py` → `test_sirali.py` → `ornek.py` (Homebrew python3).
