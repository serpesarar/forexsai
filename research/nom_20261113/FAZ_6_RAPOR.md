# FAZ 6 — Canlı olasılık motoru (API) (NOM, 2026-11-13)

Kod: `backend/services/nom/engine.py` (tahmin), `live_data.py` (canlı veri), `model_store.py` (sürüm),
`features.py`/`labels.py`/`bars.py` (eğitimle **aynı** kod), `backend/routers/nom_router.py` (main.py'ye kayıtlı).

## Uçlar
| Uç | Dönüş |
|---|---|
| `GET /api/probability/nasdaq?horizon=1h&geometry=1.5x1.0` (takma ad `GET /probability/nasdaq`) | aşağıdaki şema |
| `…&asof=2026-10-15T15:00:00Z` | **yeniden oynatma**: yalnız o andan önce kapanmış barlarla, "şimdi" = asof (panel doğrulaması, olay incelemesi) |
| `GET /api/probability/nasdaq/meta` | etkin sürüm, eğitim sonu, hedef başına `proven`, eşik, taban, final EV/beceri |
| `GET /api/probability/nasdaq/calibration` | canlı kalibrasyon (Faz 8) |
| `GET /api/probability/nasdaq/drift` | PSI + kalibrasyon bozulması (Faz 9) |

Parametreler: `horizon ∈ {15m, 1h, 4h, session}`, `geometry ∈ {1.0x1.0, 1.5x1.0, 2.0x1.0, 1.0x1.5, 1.5x1.5}` (TP×SL, ATR
birimi ufka göre: 15m→M5, 1h→M15, 4h/seans→H1). Geçersiz → 400/422.

## Yanıt
- `tahmin.long` / `tahmin.short`: `p_tp_once`, `p_sl_once`, `p_zaman_asimi` (isotonic kalibre, toplam 1), `beklenen_r`
  (= P(TP)·TP/SL + P(SL)·E[R|SL] + P(TO)·E[R|TO], sürtünmeli; E[·] eğitimden), `p_tp_bandi` (bu P(TP) kovasında WF
  OOS'ta gerçekleşen oran + %95 Wilson GA), `beklenen_r_bandi` (kovada gerçekleşen ort. R + gün-blok bootstrap GA),
  `taban` (iklim P(TP) ve EV), `kanitli`, `esik`, `neden` (TreeSHAP, TP sınıfı marjına en büyük 5 katkı, Türkçe cümle).
- `baglam`: fiyat, ATR(H1), **en yakın 3 destek + 3 direnç** (fiyat, ATR uzaklığı, test sayısı, tür; ±0,3 ATR içindekiler
  tek bölgede birleştirilir), RSI14 her TF (M5/M15/H1/H4/D1) + 70/30'a uzaklık + bölge, trend (H1 EMA dizilimi, PSAR,
  ADX, HH/HL), rejim (ADX≥25 trend/yatay), ATR rejimi, seans fazı, VIX (≥18,4 rejimi), **yaklaşan olay** (FOMC/CPI/NFP/
  mega-cap bilanço, dakika).
- `durum`: yalnız hedef **kanıtlı** (Faz 5 ölçütlerinin hepsi + final EV>0) ve beklenen R donmuş eşiği geçerse
  `LONG`/`SHORT`; aksi hâlde **`NÖTR / belirsiz`** (+ `durum_nedeni`). Faz 5 sonucunda hiçbir hedef kanıtlı değil →
  motor şu an her durumda NÖTR döner ve olasılıkları **bilgi** olarak verir.
- `model` (sürüm, eğitim sonu, veri sürümü), `veri` (kaynak, son bar kapanışı, gecikme sn), `atr_ufuk`.
- Tahminsiz durumlar: `PIYASA_KAPALI`, `VERI_BAYAT` (son bar > 5 dk), `VERI_YOK`, `UFUK_TANIMSIZ` (seans ufku nakit dışı).
- **Otomatik işlem açmaz**; `prediction_logs`'a yazmaz.

## Canlı veri
Supabase `candle_cache` NDX.INDX 1m = kutudaki MT5 kaydedicisinin yazdığı broker barları (MT5 köprüsünün 1m çıktısı;
Faz 0'da MT5 altın standartla gecikme 0, r = 0,994). Son 240 gün (Faz 2 pencere yeterliliği), disk önbelleği
`backend/data/nom_cache/ndx_1m.parquet` + son 1 saatin artımlı yeniden çekimi (ilk yükleme ~31 sn, sonra ~0,2 sn).
Temizlik eğitimle aynı (kapalı saat, OHLC tutarlılığı, yalnız kapanmış barlar). Makro: yfinance günlük, 6 saatte bir
(17:15 ET kuralı özellikte). Takvim: `backend/data/nom/calendar.parquet`.

## Eğitim/servis eşdeğerliği
Özellik hesabı eğitimle **aynı fonksiyon** (`features.compute_features`). Testler:
`test_truncation_equivalence` (kesilmiş geçmiş = tam geçmiş), `test_future_perturbation`, gerçek veride 400 günlük önek
0 uyuşmazlık, 240 günlük canlı pencerede > %1 sapan özellik yok (Faz 2). API testleri `backend/tests/test_nom_engine.py`
(yapı, olasılık toplamı, NÖTR durumu, bayat veri, piyasa kapalı, hatalı girdi, router 200/422, terfi/geri alma) —
**11/11 geçti**. Besleme farkı (Dukascopy ↔ Pepperstone seviye farkı) özellikler ATR-normalize olduğu için etkisiz;
kalan risk: broker 1m mumunun gürültü yapısı Dukascopy'den hafif farklı (Faz 0: ±3 puan uyum %91,7) → canlı kalibrasyon
(Faz 8) bunu ölçmek için var.

## Canlı doğrulama (2026-11-13)
- Gerçek paket (`nom_v1b_20261113`) + gerçek candle_cache: canlı istek (Cuma 17:00 ET sonrası) → `PIYASA_KAPALI`
  (son bar 21:54 UTC); yeniden oynatma `asof=2026-11-13T15:30Z` → 0,4 sn'de tam yanıt: 1 s 1,5/1 LONG P(TP) 0,337 /
  P(SL) 0,511 / zaman 0,152, beklenen R −0,014 (kanıtsız), SHORT 0,317/0,544/0,139; destek 27.700 (−0,27 ATR, yuvarlak),
  27.528,8 (−1,44 ATR, 4 test), direnç 27.760,1 (+0,15 ATR, H1 pivot, 4 test); RSI M5 20,1 / M15 22,0 (aşırı satım);
  VIX 18,7 (yüksek rejim); yaklaşan olay NVDA bilançosu. Durum: NÖTR / belirsiz.
- Tarayıcı (izole önizleme `backend-nom-test` :8081 + `frontend-nom-test` :3013, `/olasilik-motoru?asof=…`):
  barlar, S/R merdiveni (6 seviye), RSI şeritleri, "Neden?" listeleri, kalibrasyon kartı render ediliyor. Doğrulamada
  bulunan iki hata düzeltildi: (1) proje Supabase sarmalayıcısında `.not_` yok + `update()` anında çalışıyor (E128 —
  gölge sonuç yazımı filtresiz güncelleme olurdu, tabloya yazılmadan önce yakalandı); (2) bağımsız sayım ölçütü `>` → `≥ 60 dk`.
