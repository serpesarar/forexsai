# CORTEX Backfill — Bulgular (2026-07-03)

## Veri (kullanıcının yerel dosyaları, indirme YOK)
NDX günlük 2010-24 · VIX 1990+ · DXY 2015+ · US10Y(DGS10) 2005+ · **NQ 5m 2019-08→2024-08**.
NQ dosyası karışık-TZ → ay-bazlı çift hacim-çıpası (09:30 açılış + 16:00 kapanış)
ile çözüldü; belirsiz aylar düşürüldü. Doğrulama: çevrilen ilk bar Pazar 18:05 ET
= vadeli açılışı ✓. Sentetik testte bilinen offset birebir geri bulundu.

## Sızıntı kuralları (9 testle KANITLI)
situation: günlük ≤ D-1 + NQ barları ≤ T; outcome (NQ T→T+H) situation'a giremez
(future fiyat değiştirilip situation aynılığı asserte edildi); walk-forward yalnızca
aynı-karar-saatli daha eski epizodlara bakar.

---

## HEDEF v2 (DOĞRU — kullanıcı düzeltmesi 2026-07-03)
Karar anı **intraday** (NY açılışı 09:30 / 10:00 / 11:00 ET). Tahmin edilen:
o andan **ileriye** NQ futures net yönü — **+6 saat** (seans kalanı) ve **+24 saat**
(gece Asya/Avrupa dahil ertesi gün aynı saat). 3567 epizod (1189 gün × 3 saat).

### ⚠️ SONUÇ: analog katmanı bu hedef için YÖN ÖNGÖRMÜYOR (dürüst)
Walk-forward, p_up kartil kalibrasyonu (Q4=en yüksek tahmin p_up, gerçek up-oranı):

| karar | horizon | n | baseUp% | Q1up% | Q4up% | **Q4−Q1** | momentum-baseline |
|-------|---------|---|---------|-------|-------|-----------|-------------------|
| 09:30 | 6h  | 892 | 56.2 | 57.8 | 56.1 | **−1.8pp** | 48.7% |
| 09:30 | 24h | 947 | 55.5 | 59.7 | 57.2 | **−2.5pp** | 48.9% |
| 10:00 | 6h  | 873 | 54.8 | 57.3 | 54.1 | **−3.2pp** | 50.3% |
| 10:00 | 24h | 955 | 56.1 | 58.8 | 55.5 | **−3.4pp** | 50.2% |
| 11:00 | 6h  | 847 | 57.5 | 62.6 | 56.4 | **−6.2pp** | 50.7% |
| 11:00 | 24h | 944 | 57.3 | 56.8 | 58.1 | **+1.3pp** | 49.4% |

**Yorum:** Q4−Q1 farkı çoğunlukla **negatif veya sıfır** — analog sıralaması
ileri yönü ayırmıyor (yön-öngörüsü yok, hatta hafif ters). Tek pozitif hücre
(11:00×24h, +1.3pp) **train'de +7.9pp → holdout 2023-24'te −11.3pp** = aşırı-uyum,
gerçek edge değil. Momentum baseline ~%49-50 = yazı-tura: ileri yön geceki hareketi
de basitçe sürdürmüyor. Base up ~%54-57 (drift).

**Net hüküm:** yapısal-kNN (makro + rejim + gece hareketi) NASDAQ'ın **intraday-ileri
yönünü öngörmüyor.** Bu, verimli-fiyatlama beklentisiyle tutarlı. Kullanıcının
"tek örnekti, emin değiliz" şüphesi bir kez daha HAKLI çıktı.

---

## HEDEF v1 (YANLIŞ hedefti — kayıt için) — ertesi-gün open→close
İlk (hatalı) formülasyon: 08:00 premarket kararı → aynı-gün NDX open→close.
Analog %49.8 vs baseline %55.1; kalibrasyon Q1→Q4 sadece +5.3pp, holdout +2.5pp.
Bu da zaten zayıftı ve zaten YANLIŞ soruydu.

---

## VIX-rejim tek-faktör (her iki hedefte de)
VIX rejimi → ileri yön ayrımı YOK (tüm rejimler ~%54-57 up). Haziran 2026'daki
+25pp bulgusu **gün-içi SİNYAL yönü** içindi; günlük/ileri yöne taşınmıyor.
(Hafıza [[macro-ndx-vix-direction]] bu sınırla güncellendi.)

## Sonuç → CORTEX için anlamı
- Analog katmanı bir **yön kâhini DEĞİL.** CIO'ya "P(up) %X" diye sunmak yanıltıcı olur.
- Epizodik hafıza yine de değerli: LLM debate'in muhakemesi + Faz 2 (ajan-trust,
  kNN'i değil LLM ajanlarını ölçer) + Faz 3 (reflection). Ama **yön-öngörü iddiası yok.**
- Karar: canlı debate'e analog **enjeksiyonu VARSAYILAN KAPALI** (`CORTEX_ANALOG_INJECT=0`);
  hafıza kaydı açık kalır (Faz 2/3 birikir). Yön edge'i başka yerde (haber, mikroyapı,
  ya da LLM'in kendisi) aranmalı — kNN'de yok.

Dosyalar: `episodes_fwd.json` (3567), `walkforward_fwd.json`.
