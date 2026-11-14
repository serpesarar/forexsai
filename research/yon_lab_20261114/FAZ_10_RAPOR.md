# FAZ 10 — Entegrasyon, kayıt ve DÜRÜST SONUÇ (Yön Lab, 2026-11-14)

## Entegrasyon (geçen kural yok → uyarı)
- Panel `/olasilik-motoru`: "LONG − SHORT farkı yön sinyali değildir" kartı (`frontend/components/nom/ProbabilityEnginePanel.tsx`,
  `DirectionWarning`), durum bandının hemen altında. API `/api/probability/nasdaq` yanıtına `yon_uyarisi` alanı eklendi
  (`backend/services/nom/engine.py`). NOM motor/özellik testleri 11/11 geçti; tarayıcıda doğrulandı.
- `yon_katmani`, `nom_predictions` yön kolonları ve canlıya alma kartı **eklenmedi** (ön-kayıtlı ölçütü geçen kural yok; kart yalnız
  geçen kurallar için).
- Kayıt: `docs/KAPI_KAYIT_DEFTERI.md` §2.55 (YL-01…06) + §1 E129–E131 + §3 meta-ders; Evrim Paneli oturum notu + backlog +
  `analyses.json` girdisi.

## DÜRÜST SONUÇ
**Soru:** Fiyat herhangi bir andayken yukarı mı aşağı mı gideceğini, şanstan ayırt edilebilir biçimde önceden söyleyen bilgi var mı?

**Cevap: Gün-içi NASDAQ'ta, sistemin ücretsiz erişebildiği bilgi sınıflarında, işlem maliyetini aşan yön bilgisi yok.**
8.680 deneme, dört şans tabanı (analitik D/(U+D), hayalet referans, eşlenmiş taban, 10 martingal piyasa) ve kilitli kör test/taşıma
ile ölçüldü.

| Bilgi sınıfı | Sonuç | Kanıt |
|---|---|---|
| **Seviyeler** (S/R pivotları, EMA/SMA, Bollinger/Keltner/Donchian, TWAP ±σ, önceki gün/hafta/ay, gece, ORB, yuvarlak sayılar, Fib, Ichimoku, SAR/SuperTrend, kümeleşme) | **Tükendi.** Yarış oranı kumarbazın iflası geometrisiyle açıklanıyor; 13 ailenin hiçbiri hayaletten ayrılmıyor (|t| ≤ 1,58, üç dönemde de); hiçbir üye mıknatıs/duvar değil; değdikten sonra kırılım %50,5 vs hayalet %50,8 | Faz 4 |
| **Gösterge durumları** (RSI/Stoch/W%R/CCI/MACD/ADX/Aroon/Vortex/TRIX/UO, EMA dizilim/kesişim, bant, mum formasyonları, NR4/7, yapı, zaman, takvim akışları) | **Yalnız 15 dk aşırı-uzama dönüşü** gerçek: KEŞİF −2,3 p (t −7,3) → DOĞRULAMA −1,35 p (t −3,1) → KÖR −0,7 p (t −1,2); 4/4 endekste aynı işaret ama anlamsız. 1 s / 4 s / seans sonunda iz yok | Faz 4–5, 8 |
| **Model** (NOM 132 + tüm durumlar + seviye uzaklıkları, şans ofsetli) | ±1 ATR yarışında yön isabeti **%49,8–50,3** (NOM %49,3–52,7), P2 plaseboyu geçmiyor; işaret etiketinde %51,4–52,3 (aynı 15 dk bilgisi) | Faz 7 |
| **DIX / GEX** (günlük, 2011→) | Seans, gece, ertesi gün yönünde eşik altı (max |t| 2,52 < 2,93) | Faz 6 L1 |
| **Çapraz varlık** (mega-cap genişliği, NVDA/SOXX öncülüğü, SPY/IWM/US500/US30/US2000 göreli güç, VIX/DXY/TNX) | Eşik altı (2,20 < 3,25 saatlik; 2,71 < 3,66 M5) | Faz 6 L2–L3 |
| **Tick mikroyapısı** (tick-yönü dengesizliği, kotasyon hızı, spread) | Eşik altı (2,14 < 3,00); hacim alanı yok | Faz 6 L4 |
| **İşlem** | 15 dk dönüş kuralı DOĞRULAMA −0,22R, KÖR −0,13R, taşıma 4/4 eksi; model kuralı −0,15R. Bilgi ≈ 0,3–0,6 puan/işlem, maliyet ≈ 3,4–5,4 puan | Faz 9 |

**Bunun ne olmadığı:** Bu sonuç, sistemde zaten kanıtlı olan *günlük/rejim ve zorunlu akış* kenarlarını (C3b RSI2 korku dönüşü,
CAPREV, VIXREG, ORB × VIX, ay sonu dengeleme, FOMC öncesi gece, KSG) çürütmez — onlar gün-içi "her an yön" değil, seyrek ve günler
ölçeğinde zamanlanmış kurallardır. Bu çalışma onların **gün-içi her ana genelleştirilemeyeceğini** gösterir.

**Hangi koşulda güvenilmez / kullanılmamalı:** LONG−SHORT olasılık farkını, bir seviyeye yakınlığı, "seviye tuttu/kırıldı" anlatısını,
gösterge uçlarını ve çapraz varlık öncülüğünü gün-içi yön sinyali olarak kullanmayın. 15 dk dönüş bilgisi yalnız *icra zamanlaması*
için düşünülebilir (ör. zaten verilmiş bir SHORT kararını aşırı-uzama barında açmak) — bu da ayrı ön kayıt ister.

**Geriye ne kaldı (ücretli dahil, maliyetiyle — fiyatlar yaklaşık mertebedir, bu oturumda satıcı sitelerinden DOĞRULANMADI):**
1. **Emir defteri / gerçek hacim / agresör tarafı (footprint, delta):** CME MNQ/NQ Level-2 ve işlem verisi — Databento (≈ $0,0001–
   0,0005/kayıt; tarihsel NQ MBP-10 aylık tipik ~$100–300), Rithmic/CQG feed (~$25–100/ay + borsa ücretleri). Bu sınıf sistemde hiç
   sınanmadı; gün-içi yön için literatürde iz bulunan tek sınıf (order flow imbalance, birkaç saniye–dakika ölçeğinde).
2. **Opsiyon akışı ve dealer konumlanması (strike düzeyi gamma, 0DTE akışı):** SpotGamma (~$90–300/ay), Cboe DataShop / OPRA
   (yüksek), Unusual Whales (~$50/ay). Ücretsiz toplam GEX (L1) yön vermedi; strike düzeyi "gamma duvarı" sınanmadı.
3. **Kurumsal akış takvimi** (ETF yaratma/itfa, CTA/vol-target konumlanması): ücretli tahminler (Nomura/GS raporları erişilemez).
4. **Haber hızı** (`news_stories`, 2026-11-05 →): kapsam birikince yeniden; HB-01/02'ye göre yön değil oynaklık beklenir.

Kör test dramatik kötüleşme göstermedi (işaret korundu, büyüklük yarıya indi); kör veriyle hiçbir ayar yapılmadı.
