# USOIL Kırılım-Devam Araştırması (2026-08-06)

## Amaç
USOIL SELL S/R-pullback scope'unun canlıda derinden -EV çıkması (%21.3 WR,
-0.46R/işlem, bkz. konuşma geçmişi) üzerine: yüksek başarı oranlı bir
kırılım-devam (breakout continuation) giriş scope'u arayışı.

## Veri
150 gün / 29.415 adet USOIL.FOREX 5m bar (candle_cache, 2026-03-09→2026-08-05).

## Metodoloji
1. Rolling N-bar Donchian kanal kırılımı tespiti (`usoil_breakout_detect.py`).
2. Her kırılım için tam gösterge seti: ADX/+DI/-DI, RSI14, MACD hist,
   dist(EMA20)/ATR, hacim/20-bar oranı, ATR14, kırılım-barı range/ATR,
   kırılım-barı gövde oranı.
3. Etiketleme: kırılımdan sonra ±1.0×ATR yarışı (devam hedefi vs geri-dönüş
   hedefi, 36 bar/3 saat pencere) → GENUINE / FAKE.
4. Kronolojik train(%70)/test(%30) + placebo (`usoil_breakout_analyze.py`).
5. Eşik taraması + LightGBM (chronological train/val/test) — `usoil_breakout_rule.py`,
   `usoil_breakout_lgbm.py`.
6. N (48/96/144/288) ve çoklu-bar teyidi (1/2/3) duyarlılık taraması —
   `usoil_breakout_v2.py`.

## Bulgular
- **Taban devam oranı** (filtresiz): BUY ~%58-60 OOS (N ve teyit sayısından
  BAĞIMSIZ, çok kararlı); SELL ~%50-57 OOS (N'e göre dalgalı, kararsız).
- **Tek-eşik gösterge filtreleri** (range/ATR, hacim oranı, RSI vb.): TRAIN'de
  placebo'yu geçen ayrımlar bulundu (ör. BUY range_atr/vol_ratio AUC ayrımı
  0.108 > placebo p95 0.074) ama **TEST/OOS'ta baseline'ı YENEMEDİ** — bazı
  konfigürasyonlarda baseline'ın ALTINA düştü. Aşırı-uyum.
- **LightGBM (çok-değişkenli)**: VAL AUC 0.495 (BUY) / 0.583 (SELL) — pratikte
  rastgele. %70+ kesinlikte hiçbir eşik n≥15 üretmedi. Reddedildi.
- **Çoklu-bar teyidi** (2-3 kapanış üst üste): örneklem küçülüyor, WR
  iyileşmiyor/kötüleşiyor (tekdüze değil ama hiçbir konfig baseline'ı
  güvenilir şekilde geçmedi).
- **TEK sağlam, OOS-kararlı ayrım — 5m EMA200 trend hizası:**
  - BUY, fiyat EMA200 ÜZERİNDE: TRAIN %59.7 (n=397) → TEST **%62.7** (n=185)
  - BUY, fiyat EMA200 ALTINDA: TRAIN %61.1 (n=54) → TEST **%21.1** (n=19) — çöküyor
  - SELL: trend-hizalı TRAIN %65.0→TEST %54.2; trend-tersi TRAIN %65.9→TEST
    %50.0 — ayrım yok, SELL kapsam dışı bırakıldı.

## Çapraz-kontrol: mevcut fakeout dedektörünün canlı gölge performansı
`shadow_pattern_trades` (USOIL, source=fakeout, n=29, 2026-07-19'dan beri):
- SAHTE (fade) çağrısı: %57.1 WR (n=21), toplam +3.00R — belgelenen %86
  OOS'un çok altında ama hafif pozitif.
- GERÇEK (kırılım yönü) çağrısı: %50.0 WR (n=8), toplam 0R — **edge YOK**
  (küçük örneklem, ama cesaretlendirici değil).

Bu, kendi bulgumla tutarlı: "kırılım yönünü izle" tarzı bir sinyal USOIL'de
zor bir problem; EMA200 trend-hizası basit ama gerçek ayrımı sağlayan tek
mekanizma oldu.

## Uygulanan Scope
`yeni deneme/forexsai_demo_bot.py::check_usoil_breakout()` — Donchian(48×5m)
kırılımı + 5m EMA200 üstü (yalnız BUY) → market giriş, TP=SL=1.0×ATR14(5m)
(RR 1:1). Ayrı magic (`MAGIC_NUMBER+5`), `config.USOIL_BREAKOUT_*` bayraklarıyla
kontrol edilir (varsayılan açık). SELL yönü koda ALINMADI (kanıt yok).

## Dürüstlük notu
%62.7 "yüksek" değil, ama (a) OOS'ta gerçekten doğrulanmış, (b) mevcut USOIL
SELL S/R-pullback'in (%21.3) üç katı, (c) RR 1:1 ile başabaşın (%50)
belirgin üzerinde (+0.25R/işlem beklenti). Daha agresif filtreler denendi,
hepsi ya aşırı uydu ya da sinyal vermedi — bu, dürüstçe ulaşılabilen tavan.
Canlıda ilk 2-3 hafta ölçülüp gerekirse (n küçükse) TQ tarzı bir "çok-emin"
kapısına terfi ettirilebilir.
