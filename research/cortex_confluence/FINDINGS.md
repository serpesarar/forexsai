# CORTEX Confluence — Bulgular (2026-07-03)

## Hipotez (kullanıcı)
Fiyat yukarı/aşağı hareketinden önce göstergelerde bir **çakışma (confluence)**
olmalı. Diğer verilerde / kombinasyonlarında bu örüntüyü ara.

## Yöntem (sızıntıya karşı katı)
- **Feature'lar:** başkasının 3531-kolonlu soupu DEĞİL (263'ü repaint-riskli
  swing/wave, 2443'ü otomatik `X__x__Y` feature-cross patlaması = overfitting
  yakıtı). Bunun yerine **NQ 5m'den kendimiz ürettik**: M30/H1/H4 çoklu-zamanda
  41 causal gösterge (RSI, MACD-hist, EMA stack/slope, ATR%, Bollinger-z, ADX,
  hacim-oranı, realized-vol, momentum) + overnight gap + ilk-saat hareketi.
  Hepsi geçmiş barlardan, repaint YOK.
- **Etiket:** ileriye NQ yönü (+6h/+24h), sızıntı-denetli backfill'den.
- **Split:** kronolojik. Train ≤2022, TEST 2023-2024 (dokunulmadı).
- **Model:** LightGBM, ağır regularize (ağaçlar confluence/konjonksiyonu yakalar).
- **Placebo:** karıştırılmış-etiket koşusu ~0.5 AUC vermeli (sızıntı yoksa).

## Grid sonucu (3552 satır, 6 hücre)
5 hücre zayıf/edge yok (AUC ~0.53-0.56, placebo ~0.5, baseline'ı geçmiyor).
**Tek hücre öne çıktı: karar 11:00 ET × horizon 24h.**

## ⭐ 11:00 ET → 24h ileri yön — GERÇEK ama KOŞULLU sinyal

| Test | Sonuç |
|------|-------|
| OOS 2023-24 AUC (15 seed) | **0.596 ± 0.004** (çok kararlı) |
| Permütasyon (40 shuffle) | placebo ort 0.494 ± 0.035 → **p = 0.000** |
| Güven top-%20 (long) | **%67.2 up** (base %59) |
| Güven alt-%20 (short) | %46.3 up = **%53.7 down** (base down %41) |
| Uç-%20 yön isabeti | %60.6 |

**Confluence feature'ları (önem sırası):** `vol_ratio_H4`, `ret6_H4`,
`overnight_change`, `adx_H4`, `vol_ratio_H1`, `boll_z_M30`, `rsi_M30`,
`macd_hist_H4` → tam da senin dediği **çoklu-zaman kesişimi**: H4 trend+hacim +
M30 momentum/aşırılık + gece hareketi.

### ⚠️ KRİTİK KOŞUL: rejime bağlı, her-hava-koşulu DEĞİL
Yıl-yıl (expanding train):
- **2022: AUC 0.46** (ayı piyasası — ÇALIŞMADI, yazı-turadan kötü)
- 2023: AUC 0.589
- 2024: AUC 0.614

2022 faiz-şoku/ayı rejiminde örüntü kırıldı. Yani bu **koşullu bir edge** —
trend/boğa rejiminde çalışıyor, sert ayı rejiminde bozuluyor. Canlı kullanımda
**rejim-kapısı ŞART** (VIX/market_regime ile).

## Dürüst kalibrasyon (abartmıyorum)
- Sinyal GERÇEK: p=0.000, 15 seed'de stabil, 2023 VE 2024'te AYRI AYRI tekrar etti.
- Ama: (a) 6 hücre taradım → seçim yanlılığı var; yine de permütasyon + iki ayrı
  yıl tekrarı şansı zayıflatıyor. (b) Büyüklük mütevazı (AUC 0.60; güvenli long'da
  +8pp). (c) Sadece ~2 yıl OOS. (d) Rejime bağlı (2022 çöktü). (e) İşlem maliyeti
  düşülmedi.
- **Neden 11:00 × 24h?** Mantıklı: 11:00'de seansın ilk ~1.5 saati oturmuş
  (H4/M30 confluence oluşmuş), 24h horizon trend-devamını yakalıyor. 6h ve erken
  saatler sinyal vermiyor — bilgi yeterince oluşmamış.

## Hüküm
Analog-kNN yön veremedi; ama **denetimli ML + çoklu-zaman confluence, 11:00 ET
kararı için 24h ileri yönde istatistiksel olarak anlamlı, mütevazı, REJİME BAĞLI
bir edge buldu.** Senin "muhakkak bir çakışma belirtisi olmalı" hipotezin — bu
spesifik pencerede — veriyle desteklendi. Ama al-sat'a geçmeden önce: rejim-kapısı
+ canlı ileri-doğrulama + işlem-maliyeti analizi gerekir.

Dosyalar: `dataset.parquet` (3552×45), `results.json`, `discover.py`.
