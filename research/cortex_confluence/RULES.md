# CORTEX Confluence — Doğrulanmış Kurallar (2026-07-04)

Yöntem: pozitif vs negatif gün değer-farkı (discriminative) → çakışma kombini →
**train 2019-2021 / TEST 2022-2024** (test'te hem ayı 2022 hem boğa 2023-24).
Feature'lar NQ 5m'den causal (repaint yok) + makro/rejim (VIX/DXY/US10Y).
51 feature, 3 karar saati × 2 horizon tarandı.

## ✅ LONG kombinasyonları (momentum-devamı)

**L1 · RSI momentum-devamı** — karar **11:00 ET**, horizon **24h**
> `rsi_M30 > 73` → YUKARI
- TEST %69 (base %53, **+16pp**), kapsam %11
- Yıl-yıl: 2022 %71 · 2023 %65 · 2024 %74 → **ayı yılında bile tuttu** (momentum kendini seçiyor)

**L3 · Fiyat kısa-EMA üstünde güçlü** — **11:00 ET**, **24h**
> `px_ema20_M30 > +0.38%` → YUKARI
- TEST %62 (+9pp), kapsam %23 (yüksek), 2022 %57 · 2023 %64 · 2024 %70

## ✅ SHORT kombinasyonları (stres-kapılı kırılım devamı)

**S1 · Stres + aşağı momentum** — karar **10:00 ET**, horizon **6h**
> `ret1_H1 < 0` VE `px < ema20_H1` VE `VIX rejimi ≥ ELEVATED (≥20)` → AŞAĞI
- TEST ↓%57 (base ↓%45, **+11pp**), kapsam %13 (çoğu stres/2022'de ateşler)

**S2 · Stres + aşağı momentum + faiz baskısı** — **10:00 ET**, **6h**
> `ret6_M30 < 0` VE `VIX ≥ ELEVATED` VE `US10Y_chg > 0` → AŞAĞI
- TEST ↓%59 (+14pp), kapsam %7

## ⭐ Çakışmanın kanıtı (kullanıcının hipotezi)
Aynı S1 kurulumunda, VIX koşulunu çıkar/değiştir:
| Koşul | down-oranı (TEST) |
|-------|-------------------|
| aşağı-momentum TEK BAŞINA | %47 (edge yok) |
| aşağı-momentum **+ VIX-stres** | **%57** (edge) |
| aşağı-momentum + VIX-SAKİN | %41 (tersine döner — sakinde UP) |

→ Edge'i açan tek gösterge değil, **çakışma**. Sakin rejimde aynı momentum
YUKARI dönüyor. "Bir gösterge aşağı + diğeri (VIX) yukarı → ters işlem" fikri
veriyle doğrulandı.

## Örüntülerin ekonomik mantığı
- **LONG = momentum persistence:** NDX kalıcı yükseliş trendi; güçlü momentum
  (RSI>73 / fiyat EMA üstü) devam ediyor, dönmüyor. Aşırı-alım ≠ satış sinyali.
- **SHORT = stres-kırılımı:** NDX ancak VIX yükseldiğinde + momentum aşağıyken
  düşüşü sürdürüyor. Sakin piyasada short çalışmaz (mean-reversion up).

## Dürüst sınırlar
- Mütevazı lift (long +9-16pp, short +11-14pp), kapsam %7-23.
- Short kombinleri NADİR + stres-rejimine bağlı (test'te çoğu 2022'de ateşliyor);
  sakin dönemde neredeyse hiç fırsat yok.
- ~2.5 yıl OOS; işlem maliyeti düşülmedi; tek karar saati/horizon başına 1 örüntü.
- LONG tarafı SHORT'tan belirgin daha sağlam ve daha yüksek kapsamlı.

## Hüküm
Hedef (≥2 long + ≥2 short) sağlandı, hepsi OOS + rejim-kırılımı + marjinal
incelemeden geçti. Bunlar **rejim-kapılı, yorumlanabilir kurallar** — al-sat'a
geçmeden önce canlı shadow ileri-doğrulama + işlem-maliyeti şart.

Dosyalar: `dataset2.parquet`, `discover.py`, `FINDINGS.md`.

---

## 2. TUR — ÇAKIŞMA-SKORU STİLİ (2026-07-04, `dataset3.parquet`)
Farklı stil: tek-eşik yerine **hizalanma-sayısı** (bull_score 0-12 = kaç gösterge
aynı yönde) + gap-continuation + rsi-divergence. Hedef %70.

### ✅✅ YENİ LONG (11:00 ET) — %75-78, HER YIL TUTTU (2022 ayı dahil)
**NL1** · `bull_score≥11` VE `mom_agree=3` VE `rsi_M30>q85` → 6h UP
- TEST %78 (+21pp), kapsam %6 · yıl: 2022 %67 · 2023 %79 · 2024 %89
**NL2** · `bull_score≥11` VE `px_ema20_M30>q80` VE `gap_cont≥1` → 24h UP
- TEST %75 (+22pp), kapsam %7 · yıl: 2022 %90 · 2023 %69 · 2024 %70
**NL3** · `bull_score≥11` VE `mom_agree=3` VE `rsi_spread>q70` → 24h UP
- TEST %78 (+25pp), kapsam %6 · yıl: 2022 %85 · 2023 %82 · 2024 %62

→ Örüntü: **neredeyse tüm göstergeler aynı yönde hizalandığında** (bull_score≥11/12)
+ kısa-vade momentum lideri → 24h/6h yukarı %75-78. Tam çakışma = yüksek güven.

### ❌ SHORT %70 — NDX'te OOS'ta MÜMKÜN DEĞİL (dürüst tavan)
Bu tur 5 farklı stil denendi (çakışma-skoru, agresif derin-stres, gap-down,
ampirik tavan taraması, LGBM güven-kuyruğu), 3 seans × 2 horizon.
**En yüksek kararlı short: TEST ↓%59** (stres-kapılı, 6h). Model güven-kuyruğu:
en emin down uç-%10 bile ~%50. **%70 short yok** — zorlamak = overfit (n≈12 şanslı
gün). Yapısal sebep: NDX kalıcı yükseliş; down-günler azınlık ve zayıf-öngörülebilir.
Short ancak yüksek-VIX + aşağı-momentum penceresinde ~%57-59 verir (S1/S2).

**Sonuç:** LONG'da %70 hedefi AŞILDI (3 yeni kombin %75-78, her yıl). SHORT'ta
dürüst tavan %59 — bu enstrümanın doğası. Mean-reversion short için farklı
enstrüman (XAU/DAX) gerekir; NDX değil.

---

## 3. ÇOK-ENSTRÜMAN (2026-07-04) — jenerik motor gold + DAX

### 🥇 GOLD (XAUUSD, 2021-2026 M30 UTC, train ≤2023 / test 2024-26) — İKİ YÖNLÜ %70+
Kilit çakışma filtresi: **DXY (dolar yönü)** — altın-dolar ters ilişkisi.
- **GL1** `trend_agree≥3 VE gece↑ VE DXY↓` → 24h UP **%85** (2024 %83, 2025 %86)
- **GL2** `bull_score≥11 VE DXY↓` → 24h UP **%84**
- **GS1** `bull_score≤2 VE DXY↑` → 6h DOWN **%78** (2024 %79, 2025 %77)
- **GS2** `macd_M30↓ VE DXY↑` → 3h DOWN **%72**
- **Marjinal:** bear-hizalanma TEK %53 → +DXY↑ %78. DXY = edge açan filtre
  (tıpkı NDX'te VIX-stres gibi). Teknik tek başına hiç; makro-rejimle çakışınca edge.

### DAX — YETERSİZ VERİ
Sadece `DAX_1D` 100 gün (2025-05→10). Çok-yıllı intraday yok → confluence
imkânsız. Gerekli: gold gibi ~5yıl M30/M5 DAX intraday.

## Genel ilke (3 enstrümandan)
**Teknik çakışma TEK BAŞINA yön vermez; doğru MAKRO rejimle kesişince edge doğar:**
NDX → VIX-stres (short) / momentum (long); GOLD → DXY yönü (iki yönlü).
Enstrümanın makro-sürücüsünü bulmak, filtrenin kalbi.

Kurallar sisteme kayıtlı: `backend/services/cortex_confluence_rules.py` (ajanlara
debate'te enjekte edilir). Veri: `dataset_gold.parquet`, motor: `generic.py`.

---

## 4. GENİŞLETME (2026-07-04) — gold DAHA İYİ + DAX 1h eklendi

### 🥇 GOLD — ÇİFT-MAKRO (DXY+US10Y) daha güçlü (dataset_gold_wide, tüm saatler)
Tek-makrodan belirgin daha iyi. Kilit: DXY VE US10Y AYNI yönde = altın kesin yön.
- **GL-dual** `DXY↓ VE US10Y↓` (13UTC×12h) → UP **%86** (2024 %78, 2025 %94)
- **GL-bull+DXY** `bull_score≥11 VE DXY↓` (6UTC×12h) → UP **%89** (2024 %89, 2025 %88)
- **GS-dual** `DXY↑ VE US10Y↑` (8UTC×12h) → DOWN **%89** (2024 %95, 2025 %71)
- **GS-px+DXY** `px<EMA20 VE DXY↑` (9UTC×12h) → DOWN %79
Ekonomik: dolar+reel-faiz ikisi de altının maliyetini artırır/azaltır → çift-teyit.

### 📊 DAX (GDAXI, yfinance 1h, 2023-08→2026-07, ~1yr OOS) — PRELIMINARY
- **LONG %74-77** (momentum/hizalanma, NDX'e benzer): `mom_agree≥3 VE boll_z>q80` %77;
  `bull_score≥11 VE boll_z>q80` %74.
- **SHORT zayıf** (tek kombin %67) — DAX da equity, NDX gibi short yapısal zor.
- ⚠️ Küçük örneklem (n=12-19), sadece 2.9yıl veri → temkinli. Daha uzun DAX intraday gerek.

## Enstrüman doğası (3'ten çıkan net tablo)
| Enstrüman | LONG | SHORT | Sürücü |
|-----------|------|-------|--------|
| NDX | %75-78 güçlü | %59 zayıf (yapısal) | VIX-stres + momentum |
| GOLD | %86-89 güçlü | %79-89 güçlü | **DXY+US10Y çift-makro (iki yönlü)** |
| DAX | %74-77 (prelim) | %67 zayıf | momentum (equity, NDX-benzeri) |

→ **Equity indeksleri (NDX/DAX): long-ağırlıklı, short zor. Altın: iki-yönlü, makro-sürücülü.**
Kurallar: `backend/services/cortex_confluence_rules.py` (11 kural, ajanlara enjekte).
