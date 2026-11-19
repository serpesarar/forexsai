# Korku gecesi + XP: kaybeden ve kazanan işlemlerin derin karşılaştırması — ÖN KAYIT (2026-11-19, sonuçlardan önce)

## Kullanıcı isteği
"Kaybeden ve kazanan işlemleri kümele, tüm gösterge, hacim, formasyon, destek/direnç ve trend kanalı farklarını önce tek tek, sonra
kombinasyonla analiz et. Kaybedenleri elemeyi sağlayacak farkı bul."

## Defter kontrolü (3. KURAL)
- **XG-01:** 32 günlük/seans düzeyi özellik (gün getirisi, son saat, TWAP uzaklığı, RSI2 günlük, SMA uzaklıkları, VIX, QQQ günlük hacmi, takvim) → bilgi.
- **XG-03:** dört veto KEŞİF'te zararı yarıya indirdi; TEST'te kâr ×0,44–0,80 → X.
- **XG-04:** lojistik ve GBM sınıflandırıcı, TEST AUC 0,50–0,62 → X.
- **Yeniden açma gerekçesi (yeni bilgi türleri):** 30 dk/1 sa gün içi göstergeler (RSI14, Stokastik, MACD, Bollinger, ADX, CCI, EMA dizilimi), fiyat–gösterge uyumsuzluğu, **gün içi tik hacmi yapısı** (düşüşteki hacim, son saat payı, kırmızı/yeşil hacim oranı, klimaks), 16:00 mum formasyonu, destek/direnç konumu (önceki dipler kırıldı mı, üstte direnç uzaklığı), trend kanalı (regresyon konumu, eğim, kanal kırılımı), düşüşün yapısı (hız, en büyük mum payı, dipten sekme) ve öbür endekslere göre göreli zayıflık. XG-01'in 32 özelliği kombinasyonlara dahil edilir.

## Veri
- **Ana veri:** MT5 M30 (tik hacmi var), dört piyasa: NAS100, US500, US30, US2000. İşlemler `research/xp_gelistir_20261119/results/islemler.parquet` (K1 + XP, net bp).
- **İkincil kontrol:** Duka NDX 1m → 30 dk, hacimsiz özellikler.
- **Dönemler:** KEŞİF ≤ 2021-10-31 (310 işlem, 74 kaybeden), TEST 2021-11 → (454 işlem, 118 kaybeden).
- **Sızıntı kuralı:** tüm özellikler yalnız 16:00 NY'den önce kapanmış mumlardan hesaplanır. Göstergeler nedenseldir; seviyeler giriş gününden önceki günlerden kurulur.

## Etiketler
- **Kaybeden:** net < 0.
- **İkincil (büyük kayıp):** net ≤ −150 bp.

## Adımlar (sırası ve ölçütleri sabit)
1. **Tek tek:** her özellik için KEŞİF'te piyasa içi AUC (kaybeden vs kazanan), piyasa ağırlıklı ortalama.
   - **Çoklu test koruması:** etiketler piyasa içinde 1.000 kez karıştırılır, tüm özellikler üzerinden en büyük |AUC − 0,5|'in %95'liği eşik olur (aile hatası).
   - Eşiği geçen özellikler ve en iyi 10 özellik TEST'e taşınır. Yön ve beşte birlik sınırı KEŞİF'te piyasa başına dondurulur.
2. **Kümeleme:**
   - (a) KEŞİF'te piyasa içi standartlaştırılmış özelliklerle KMeans k = 2…6; k kaybeden oranına göre değil siluet ile seçilir. TEST işlemleri en yakın KEŞİF merkezine atanır; kaybeden-yoğun küme TEST'te de yoğun mu bakılır.
   - (b) Kaybedenlerin giriş sonrası yollarına göre tipleri (betimleyici); her tipin giriş anında tanınıp tanınmadığı (AUC).
3. **Kombinasyon:**
   - (a) En iyi 20 özelliğin ikili VE kesişimleri (her özellikte kaybeden yönlü üçte birlik). Kesişimin en iyisi için permütasyon sıfırı.
   - (b) Yalnız KEŞİF'te eğitilen modeller: derinlik 2–3 karar ağacı, L1 lojistik, GBM. TEST AUC ölçülür; tahmini kaybeden olasılığı en yüksek %15'e veto uygulanır (oran donmuş).
4. **Geçme ölçütü (veto kuralı, TEST):**
   - **B:** üç koşulun üçü de sağlanmalı.
     - Vetolananların ortalaması < 0 ve blok-bootstrap P(ort < 0) ≥ 0,90.
     - Toplam kâr ≥ tabanın %95'i ve brüt zarar ≤ tabanın %80'i.
     - Aynı yön dört piyasanın en az üçünde ve Duka NDX'te.
   - **C:** vetolananların ortalaması tabanın belirgin altında (kalite takası) ama kâr ≥ %5 düşüyor.
   - **X:** hiçbiri sağlanmazsa.
5. Toplam özellik, hücre ve model sayısı raporlanır. Canlıya bağlama yok; B çıkarsa kart (2. KURAL) ayrı adımda.

## EK-1 (2026-11-19, ana sonuçlardan SONRA — sonradan kontrol, seçim değil)
Ana koşuda ön kayıtlı ilk 10'dan gelen `T_1sa_z` (1 sa regresyon kanalı z'si, 80 mum) ve GBM, B'nin yalnız "vetolanların ort. < 0" koşulunu
kaçırıp C aldı. Bunların hükmü değişmez. Yalnız şunları raporlarım (sonuç seçimi yok, tüm hücreler yazılır):
- kanal uzunluğu 40/80/120/200 saat × eşik %10/%20/%30 (12 hücre) × dört piyasa ve Duka,
- yıl yıl,
- VIX, ATR, 1 sa RSI ve son saat ile korelasyon, VIX üçte birlikleri içinde ayırma,
- GBM vetosu piyasa ve yıl bazında.
