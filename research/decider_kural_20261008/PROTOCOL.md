# Ön-kayıt — claude_decider: SL otopsisi + sembol başına kural araması (2026-10-08)

Kullanıcı: "bunu claude decider içinde yaptır, tüm semboller için ayrı ayrı kural bul."
Defter: D1 ALLOW, D2 giriş kalitesi `chz_dir≥2,0 veya vol≥1,5` (GÖLGE, decider'da A−), D3 VIX≥18,4 NDX SELL,
OLD-25 (seçim alfası yok), decider-cli-auth (09-11→10-02 sahte WAIT'ler), IO-11 (bot veto araması genelleşmedi).

## Veri
`decider_journal` (Supabase). OPEN = decider'ın açtığı (kâğıt + 10-05 sonrası demo) kararlar, `raw.pnl_r` notlanmış
sonuç (ATR geometrisi, giriş barı kapanışı). WAIT = açmadığı; `raw.cf_pnl_r` aynı anda canlı kapı yönünde
açılsaydı sonuç → **kapısız/seçimsiz taban**. Dışlanan: `batch_eval` satırları (sonradan yeniden oynatma),
`reason` 'claude exit/spawn' ile başlayanlar (sahte karar), sonuç/geometri eksikler.

## Bağımsızlaştırma (E6)
Sembol başına kronolojik: bir OPEN, önceki SAYILAN OPEN'ın `outcome_at`'ından önce geldiyse atılır (tek pozisyon).
WAIT tabanı için aynı kural cf işlemlerine ayrı uygulanır.

## Özellikler (yalnız karar anı; yönle işaretli: + = işlem yönünde)
forensics.tfs × {1m,5m,30m,1h,4h}: trend(+1/0/−1), adx, vwap_z, channel_z, vol_ratio, karşı seviye uzaklığı
(BUY→direnç, SELL→destek; ATR), destekleyen seviye uzaklığı, karşı seviye dokunuş sayısı; MTF trend uyumu (0–5);
dirs_live: rev_chan, rev_vwap, gate_fired; makro: vix, dxy, VIX'in NDX için lehte yönü; trade: rr, spread_atr;
size_factor; saat, gün, seans, model.

## Analiz (sembol başına: NDX, XAU, USOIL, DAX)
1. Taban: OPEN ort R vs WAIT-cf ort R (seçim değeri), yön ve model kırılımı.
2. SL anatomisi (path): hiç çalışmadı (mfe<0,15R), önce kâr (mfe≥0,3R), neredeyse TP (tp_progress≥0,7),
   SL sonrası girişe döndü (sl_recovered_entry) — OPEN vs WAIT-cf karşılaştırmalı (mekanik mi?).
3. Kural araması: `research/sl_onleme_kural_20261007` ile AYNI uzay ve ölçüt (eşik yüzdelikleri, tekli+ikili AND,
   min 10 engel, ≤%50), kapsam = sembol ve sembol-yön (eğitimde ≥40). İleri (ilk %60 seç → son %40 sına) ve geri.
   Genelleme: eğitim↔sınama Spearman; eğitimin en iyi %5'inin sınamada pozitif payı.
4. Geçen kural (sınamada +, rastgeleden iyi, ters yönde de aynı özellik+yön +, ≥10 sınama engeli) yalnız GÖLGE
   adayıdır → decider LESSONS'a "gözlem" olarak, canlı karar kuralı olarak DEĞİL.
