# NOM — NASDAQ Olasılık Motoru · ÖN KAYIT (2026-11-13, sonuçlara bakılmadan yazıldı)

Bu dosya Faz 1–5 kararlarının sonuçtan ÖNCE dondurulmuş hâlidir. Sonradan yapılan her değişiklik
"EK-n" olarak tarihle ve gerekçeyle eklenir; eski metin silinmez.

## A. Veri (Faz 0 çıktısı)
- Ana seri: `data/ndx_1m_v1.parquet` — Dukascopy USATECHIDXUSD 1m BID, UTC, bar AÇILIŞ zamanı.
  Çekirdek dönem 2021-11-01 → 2026-11-03 (+ indirme tamamlanırsa 2018-01 → 2021-10 ve 2026-01 boşluğu).
- Spread: NY saatine göre koruyucu model = max(Dukascopy 2025 gerçek medyan, Pepperstone MT5 medyan);
  2025'te gözlenen spread modelden büyükse gözlenen. Slippage: giriş ve stop çıkışında 1,0 puan. Komisyon 0
  (Pepperstone endeks CFD'si komisyonsuz; swap ihmal — en uzun ufuk ≤ seans sonu, gecelik pozisyon yok).

## B. Etiket (Faz 1) — Triple-Barrier
- **Karar anı t** = 1m barın kapanışı (5 dk ızgarası: t mod 300 = 0). Özellikler yalnız açılışı < t olan barlardan.
- **Giriş** = t'de açılan 1m barın açılışı. LONG: ask = bid_open + spr + 1 slip. SHORT: bid_open − 1 slip.
- **ATR birimi ufka bağlı** (yalnız KAPANMIŞ barlar, Wilder 14): 15dk→M5, 1s→M15, 4s→H1, seans sonu→H1.
- **Bariyerler** gerçek giriş fiyatından: LONG TP = giriş + TP·A (bid high ile), SL = giriş − SL·A (bid low ile);
  SHORT TP/SL ask yolu (bid + spr) ile. Bar açılışı bariyerin ötesindeyse dolum açılıştan (boşluk dolumu).
  SL dolumu 1 puan aleyhte.
- **Aynı 1m barda TP ve SL** → SL (muhafazakâr). 2025 tick verisiyle bu kuralın yanlılığı ölçülür (rapor).
- **Zaman bariyeri**: ufuk sonunda son barın kapanışından çıkış (LONG bid, SHORT ask) − 1 slip.
- **Ufuklar**: 15dk, 60dk, 240dk (duvar saati), **seans sonu** = NY nakit kapanışı (16:00 ET, yarım gün 13:00);
  seans sonu yalnız 09:30 ≤ t ≤ kapanış − 30dk kararlarında tanımlı.
- Hafta sonu arasını geçen ufuk → etiket yok. Günlük ara (17-18 ET) geçilebilir (boşluk dolumu kuralıyla).
  Ufuk penceresinde beklenen açık dakikaların < %50'si varsa (veri deliği) → etiket yok.
- **Geometri ızgarası** TP/SL (ATR): 1.0/1.0, 1.5/1.0, 2.0/1.0, 1.0/1.5, 1.5/1.5.
- Çıktı her (yön, geometri, ufuk) için: sınıf ∈ {TP, SL, TO}, gerçekleşen R (birim = SL mesafesi, sürtünme dahil).
- Örnekleme: 15dk ve 60dk ufuk 5 dk ızgarası; 240dk ve seans sonu 15 dk ızgarası.

## C. Özellik (Faz 2)
- Tek kod yolu: `backend/services/nom/features.py` (eğitim = servis). HTF barı yalnız `bar_bitişi ≤ t` ise kullanılır
  (merge_asof, kapanış zamanına göre). Makro günlük değer d günü yalnız d 17:15 ET'den SONRA kullanılır (E20/E99).
- Otomatik sızıntı sınaması: (i) t'den sonraki tüm barlar rastgele bozulunca t'deki özellikler değişmemeli;
  (ii) t'de kesilmiş veriyle hesap = tam veriyle hesap (train/serve eşdeğerliği). Her ikisi de testtir (pytest).
- Hacim özellikleri YOK (Dukascopy hacmi ile MT5 tick hacmi farklı tanım → eğitim/servis uyuşmazlığı).
- Spread özellikleri YOK (geçmişte yalnız 2025 gözlenmiş; diğer yıllar model = saat bilgisinin kopyası).

## D. Doğrulama (Faz 3) — modelden ÖNCE
- **Final test (KİLİTLİ)**: 2026-05-01 00:00 UTC → veri sonu. Hiçbir hiperparametre, eşik, geometri bu dönemde
  seçilmez; Faz 5'te tek kez açılır, sonuç değiştirilmeden raporlanır.
- **Geliştirme dönemi**: veri başı → 2026-04-30.
- **Walk-forward** (genişleyen pencere): test blokları 2023H1, 2023H2, 2024H1, 2024H2, 2025H1, 2025H2, 2026-01→04.
  Eğitim = blok başından önceki tüm veri; **arındırma**: etiket penceresi blok başını geçen satırlar atılır;
  **ambargo** 1 gün (en uzun ufuk ≤ 8 s). İlk blok eğitimi ≥ 13 ay.
- Kalibrasyon: her katta eğitimin son %20'si (zaman olarak) iç kalibrasyon kümesi → isotonic (sınıf başına,
  sonra normalize). Kalibrasyon kümesi model ağaçlarını eğitmez.
- Hiperparametreler sabit (aşağıda), arama YOK. Tek ayar: erken durdurma kalibrasyon kümesinde log-loss ile.
- **Eşik seçimi**: yalnız geliştirme dönemi WF OOS tahminlerinden (ilk 4 blok seçim, son 3 blok teyit);
  sonra donar. Final testte değişmez.
- **Plasebo** (iki tür): (P1) aynı sayıda, aynı NY saati dağılımlı rastgele karar anı + aynı yön → EV dağılımı,
  model seçimi p95'i geçmeli; (P2) gün-blok karıştırılmış etiketlerle aynı pipeline (≥20 tekrar) → AUC/Brier
  dağılımı; gerçek model p95'i geçmeli.
- **Bootstrap**: gün-blok bootstrap (2.000) → EV %95 GA ve P(EV>0). Bağımsız karar sayısı raporlanır
  (aynı yönde ardışık örtüşen sinyaller 60 dk epizoda indirgenir — E6/E9).

## E. Model (Faz 4)
- Taban: (1) iklim tabanı = eğitim dönemindeki sınıf oranları (yön × geometri × ufuk × NY saat kovası);
  (2) basit kural: RSI14(M15) + EMA50(H1) trend (kural: trend yönünde ve RSI aşırı bölgede değil);
  (3) ndx_reflex_engine mom_cont (causal) — olay kümesinde.
- Ana model: LightGBM multiclass (TP/SL/TO), yön başına ayrı; karşılaştırma: yön-koşullu tek model (60dk 1.5/1.0'da).
  Sabit parametre: num_leaves 31, max_depth 6, lr 0.03, min_child_samples 200, feature_fraction 0.7,
  bagging 0.8/1, lambda_l2 5, ≤ 2.000 ağaç + erken durdurma 100.
- XGBoost yalnız karşılaştırma (aynı katlar). CatBoost/derin modeller ortamda yok; derin model ancak
  boosting tabanı geçerse denenir (geçemezse rapor).
- Metrik: Brier (çok sınıflı) ve log-loss iklim tabanına göre **beceri skoru**; AUC (TP vs değil); kova kalibrasyonu
  (ondalık); reliability diyagramı.

## F. Ekonomik test (Faz 5)
- İşlem kuralı: P(TP) ≥ τ ve beklenen R = P(TP)·TP/SL − P(SL)·(1+s) + P(TO)·E[R|TO] ≥ 0 (E62: kalibre olasılıkla).
  τ ∈ {0,50, 0,55, 0,60, 0,65} raporlanır; işlem önerisi için τ yalnız geliştirme WF'sinde seçilir.
- Raporlar: n, bağımsız n, WR, EV(R), PF, maks. DD (R), en uzun kayıp serisi; 1× ve 2× sürtünme.
- Dilimler: yıl, VIX (<18,4 / ≥18,4), trend/range (ADX H1 25), seans, haftanın günü, olay günü.
- **Geçme ölçütü (edge iddiası için hepsi)**: dev-WF EV > 0 ve P(EV>0) ≥ %90, 2× sürtünmede EV > 0, P1 plasebo p95
  üstü, ≥ 2/3 yıl pozitif, final testte EV > 0. Aksi hâlde motor yalnız **olasılık/oynaklık bilgisi** sunar,
  işlem önerisi "NÖTR".
- Bot işlemleri çapraz kontrolü: `NAS100_tum_islemler.csv` girişlerinde modelin P(TP)'si TP/SL ile ilişkili mi (AUC).

## G. Mezuniyet (Faz 8)
Canlı gölge ≥ 4 hafta ve ≥ 300 bağımsız tahmin: her kovada gerçekleşen oran WF bandı (%95 GA) içinde,
rolling Brier beceri ≥ 0 ve kalibrasyon eğimi 0,7–1,3. Aksi hâlde "güvenilir değil".
