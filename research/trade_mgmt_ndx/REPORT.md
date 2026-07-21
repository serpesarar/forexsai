# NDX İşlem-Yönetimi Araştırması — SL/TP Dinamik Yönetim Stratejileri

**Tarih:** 2026-07-21 · **Veri:** 223 gerçek MT5 NDX işlemi (iki kohort) + 25.531 × 1m bar
- Kohort A: 2026-06-25→07-09, MT5 deal CSV (103 işlem; tetiklenen TP/SL seviyesi `[tp X]/[sl X]` comment'inden BİREBİR)
- Kohort B: 2026-06-15→06-24, bot_live_audit/positions.json (120 işlem; 1m barlar Supabase candle_cache, :00 hizalı)
- Kalibrasyon: replay-vs-gerçek sonuç uyumu %82.1 (fark: konservatif SL-önce kuralı + giriş dakikası atlama + spread)

## Dürüstlük sözleşmesi
Kararlar yalnız **bar kapanışında**; değişiklik **sonraki bardan** geçerli. Aynı barda TP+SL → **SL-önce** (konservatif, baseline dahil her stratejide aynı). Giriş barı değerlendirme dışı. Zaman = piyasa dakikası. SL yalnız lehte taşınır; TP yalnız yakına çekilir. Geleceği gören hiçbir kural yok.

## 1. Fenomen analizi — "algoritmayı anlamak"

| Fenomen | Ölçüm | Sonuç |
|---|---|---|
| **TP'ye yaklaşıp SL olma** | TP yolunun %70'ine varıp SL'e dönen | **NADİR: 124 SL'in sadece 9'u.** P(kazan \| %70'e vardı) = **%88.2** → TP'ye yaklaşan işlem büyük ihtimalle TP olur; "yaklaşıp dönme" ana kanama DEĞİL |
| | %50'ye varıp SL olan | 21/124; P(kazan \| %50) = %79.0 |
| **SL-yarısında sürünme** | ≥10 ardışık dk r ≤ −0.5R | 26 işlem; sadece **8'i (%30.8) toparlayıp TP** oldu |
| Kazananların derin dalışı | TP olup yolda r ≤ −0.5R gören | 27/99 — kazananların %27'si önce SL-yarısına dalıyor |
| Süreler | medyan TP 18 dk · medyan SL 12.5 dk | SL'ler hızlı ölüyor → erken müdahale penceresi dar |

**Segment gerçeği (baseline replay):** BUY 91 işlem **+16.1R**, SELL 132 işlem **−39.9R** (B kohortu SELL −43.9R tek başına). Kanamanın kaynağı yönetim değil, SELL girişleri (bilinen VIXREG bulgusuyla tutarlı).

## 2. 10 strateji — tüm işlemler (223)

| # | Strateji | ΔtotalR | Bootstrap Δp50 [%5,%95] | P(iyileşme) |
|---|---|---|---|---|
| S2 | **BE@30dk** (SL→giriş) | **+7.9** | +8.1 [−4.0, +20.2] | %86 |
| S7 | %70-TP sonrası 15dk'da TP yoksa çık | +6.8 | +6.6 [−2.4, +17.1] | %88 |
| S1 | BE @ TP-yolunun %50'si | +5.9 | +6.0 [−4.6, +16.5] | %83 |
| S10 | Kombo S1+S5+S6 | +4.4 | +4.7 [−9.2, +18.8] | %71 |
| S6 | %70-TP'de yarı kâr kilidi | +4.3 | +4.1 [−4.9, +13.8] | %77 |
| S8 | %50 sonrası iz süren SL | +1.4 | +1.4 [−14.0, +16.7] | %55 |
| S4 | 10dk SL-yarısı → TP=giriş (scratch) | −3.3 | −3.2 | %17 |
| S3 | 30dk sonra SL yarıya | −3.8 | −3.8 | %29 |
| S9 | 120dk zaman-stopu | −5.1 | −5.1 | %15 |
| S5 | 10dk SL-yarısı → market çık (dodge) | −6.2 | −6.0 | %8 |

**Dwell-dodge ailesi (kullanıcı hipotezi) 24 parametre varyantında da (5/10/15/20dk × −0.33/−0.5/−0.66R × cut/scratch) ~0 veya negatif.** Neden: SL-yarısında bekleyen işlemin tutma beklentisi ≈ −0.47R, kesme ise ≈ −0.6R realize eder + toparlanan %31'in TP'sini öldürür. **SL'i "dodge" etmenin bedeli, kurtulanların kârından büyük.**

## 3. ANA BULGU — Yönetim yalnız BUY'da çalışıyor

Tüm iyileşme BUY segmentinden; SELL'de her kural nötr/negatif (SELL'ler çok hızlı öldüğü için kurallar yetişemiyor, yetişince de zarar):

| Strateji (BUY-only, n=91) | totalR | Δ | Bootstrap [%5,%95] | P(+) |
|---|---|---|---|---|
| baseline | +16.1 | — | — | — |
| **BE@30dk** | **+32.3** | **+16.2** | [+7.7, +24.3] | **%99.9** |
| BE@15dk | +32.4 | +16.3 | [+6.0, +26.3] | %99.5 |
| BE@45dk | +29.3 | +13.3 | [+5.2, +21.0] | %99.4 |
| **KOMBO: BE30 + %70-kilit + 15dk-stall** | **+34.0** | **+17.9** | [+6.5, +29.7] | %99.6 |

- Parametreye duyarlılık DÜŞÜK (15/30/45dk hepsi +13..16R) → eğri-uydurma değil, gerçek yapı.
- Kohort tutarlılığı: A +1.7R (n=19), B +14.5R (n=72) — ikisi de pozitif.
- Mekanizma: BUY işlemlerinde 30dk sonunda giriş üstünde olup SONRA ölenler çok (BE bunları 0'a çevirir: tam-SL sayısı 33→~20); bedeli (BE'ye değip sonra TP olacakların kaybı) küçük.

## 4. Öneri

1. **NDX BUY işlemlerine BE@30dk uygula** (SL→giriş, 30 piyasa-dakikası sonra, fiyat girişin üstündeyse; değilse ilk üstüne çıkışta). Beklenen etki: BUY kârını ~2×. En sağlam tek kural.
2. Kombo (BE30 + %70-TP'de yarı kilit + %70 sonrası 15dk stall-çıkış) marjinal +1.7R ekler — istenirse ikinci faz.
3. **SELL işlemlerine yönetim kuralı EKLEME** — çözüm giriş tarafında (bilinen SELL kanaması).
4. Dwell-dodge / TP-girişe-çekme / SL-yarılama / 120dk-stop: **KANIT YOK, uygulama.**

## Sınırlamalar
Spread/slippage modellenmedi (BE çıkışları gerçekte ~−1..2 puan realize eder; NAS100'de ≈0.01-0.02R — sonucu değiştirmez). Aynı-bar belirsizliği konservatif çözüldü. n=91 BUY; canlıya almadan önce bot tarafında **gölge modda** (önerilen BE seviyesi loglanır, gerçek SL değişmez) 2 hafta ileriye dönük doğrulama önerilir. Bu rapor geçmiş işlem seti üzerinde in-sample'dır; parametre-düzlüğü ve çift-kohort tutarlılığı overfit riskini azaltır ama sıfırlamaz.

---

# AŞAMA 3 — Genişletilmiş Hipotez Uzayı (2026-07-21, bar verisi 07-21'e uzatıldı)

## Yeni teşhisler

| Teşhis | Sonuç | Çıkarım |
|---|---|---|
| **TP sonrası devam** | TP olan 99 işlemin TP-sonrası ek hareketi: **medyan +1.42R, p75 +2.78R; %77'si ≥+0.5R daha gidiyor** | Sabit TP kazananın çoğunu masada bırakıyor → "kazananı koştur" ana fırsat |
| **SL sonrası stop-avı** | SL olan 124 işlemin **%71'i 240dk içinde girişe geri dönüyor** (%46'sı 60dk'da) | SL'ler çoğunlukla gürültü/av; re-entry ve ters-işlem aileleri denenmeye değer |
| Hızlı başlangıç | İlk 10dk'da +0.3R gören: **%66 kazanır**; görmeyen: %25.8 | Erken momentum güçlü ayrıştırıcı |
| Dip zamanlaması | −0.5R dalışı NE ZAMAN olursa olsun kötü (P(win) %17-30); hiç dalmayan %59.5 | Dip-zamanı bazlı kural yok |
| BE30 saat kırılımı (BUY) | 00-06 UTC +8.4R · 06-12 +3.9 · 18-24 +5.9 · **12-18 UTC −1.9** | İyileşme gece/Avrupa'da; ABD seansında nötr (bilgi amaçlı, koşullandırma önerilmez — overfit riski) |

## Yeni strateji aileleri (BUY-only, baseline +16.1R)

| Strateji | totR | Δ | Bootstrap [%5,%95] | P(+) | Karar |
|---|---|---|---|---|---|
| **⭐ KOMBO: BE30 + kazananı-koştur (TP'de çıkma, 0.6R iz süren SL)** | **+45.6** | **+29.5** | **[+16.9, +43.1]** | **%100** | **EN GÜÇLÜ BULGU** |
| N3 kazananı-koştur (yalnız) | +28.2 | +12.2 | [+1.1, +24.2] | %97 | güçlü; trail 0.4/0.6/0.8 hepsi + (param-düz) |
| N2 SL-sonrası ters işlem | +29.5 | +13.3 | [−2.2, +30.2] | %92 | umutlu ama CI sıfırı kesiyor; NDX'i şortlamak drift'e karşı — BEKLET |
| N4 kısmi kâr (½@0.5TP + BE) | +29.4 | +13.5 | [−2.0, +28.8] | %92 | param-hassas (0.4/0.6 zayıf) — BEKLET |
| N1 SL-sonrası re-entry | +20.7 | +4.6 | — | — | zayıf |
| N6 −0.33R limit giriş | +11.2 | −4.9 | — | — | RED (kazananları kaçırıyor) |
| N7 10dk teyit-gecikmeli giriş | −24.9 | −41.0 | — | — | BUY'da FELAKET (hızlı kazananları kaçırıyor) |
| N8/N9/N10 (erken kes / yavaş-scratch / V-toparlanma BE) | +13..20 | ≤+4 | — | — | kanıtsız |

**Kombo detayı:** Kohort A Δ+0.4 (n=19, düz), B Δ+29.0. En iyi 5 işlem Δ'nın %42'si (26 işlem R>1 koştu — tek aykırı değere bağlı değil). Koşan işlemlerde maks tutma 248dk (gecelik swap ihmal edilebilir). Uyarı: aynı anda açılmış paralel pozisyonlar var (küme etkisi) → efektif n bootstrap'ın imasından biraz küçük.

## SELL tarafı — tek işe yarayan şey "sabır kapısı"
10dk teyit gecikmesi (sinyalden 10dk sonra, işlem hâlâ yaşıyorsa ve −0.3R üstündeyse gir): SELL kanaması **−39.9R → −0.65R**. Mekanizma: 132 SELL'in 63'ü ilk 10dk'da kendi kendine ölüyor (bunlar atlanıyor), 22'si teyit veremiyor; girilen 47'si topluca başabaş. Bu alfa değil **filtre** — ama operasyonel değeri büyük: hızlı ölen SELL'ler kendini ele veriyor. (BUY'a UYGULAMA — orada −41R.)

## Nihai öneri sıralaması
1. **NDX BUY: BE@30dk + TP'de çıkmayıp 0.6R iz süren SL** — beklenen ~+29R/91 işlem (+0.32R/işlem); iki kural birbirini tamamlıyor (BE kaybedeni sıfırlar, trail kazananı büyütür).
2. NDX SELL: 10dk teyit kapısı (veya SELL'i kapalı tut — mevcut bilgiyle aynı kapıya çıkar).
3. N2 ters-işlem ve N4 kısmi-kâr: gölge listede tut, canlı veri biriktikçe yeniden test.
4. Tümü için önce **gölge mod** (öneri loglanır, MT5'e dokunulmaz) — in-sample bulgunun ileriye dönük teyidi şart. ~50 varyant tarandı; yalnız P(+)≥%97 + kohort-tutarlı + param-düz olanlar öneriye girdi.

---

# AŞAMA 4 — Tarih-Dilimi Doğrulaması + Çok-Sembol + CANLI BAĞLAMA (2026-07-21)

`multi_symbol.py` — aynı sızıntısız pipeline 4 sembole; NDX'te seçilen SABİT parametreler (BE30, trail 0.6, sabır 10dk) diğer sembollere olduğu gibi uygulandı (sembol başına ayar = overfit). Haftalık tarih-dilimi kırılımı eklendi.

## Dilim doğrulaması (haftalık kombo Δ)
| Sembol/Yön | W25 | W26 | W27 | W28 | Karar |
|---|---|---|---|---|---|
| NDX BUY kombo | +6.4 | +22.6 | −0.1 | +0.6 | ✅ hiçbir dilim anlamlı negatif değil |
| GDAXI BUY koştur | −0.9 | +12.4 | +0.6 | — | ✅ W26 ağırlıklı ama negatif dilim yok |
| XAU SELL koştur | −1.2 | +10.6 | — | — | ⚠ tek haftada yoğun → yalnız decider dersi |
| USOIL SELL kombo | −3.4 | −5.5 | +0.1 | +0.4 | ❌ |

## Çok-sembol özet (Δ, bootstrap P(+))
| | BE@30 | Kazananı-koştur (0.6R) | KOMBO | Sabır-10dk |
|---|---|---|---|---|
| **NDX BUY** (n=91) | +16.6 (%99.9) | +12.2 (%97) | **+29.5 (%100)** | −41.0 ❌ |
| **NDX SELL** (n=132) | −7.6 ❌ | −0.7 | −5.8 | **+39.3 ✅** |
| **GDAXI BUY** (n=43) | +0.1 (nötr) | **+12.1 (%98.3)** | +12.0 | −19.4 ❌ |
| GDAXI SELL (n=79) | −3.4 | +0.3 | −3.3 | +52.2 (ama 15/79 giriş ≈ kapat) |
| XAU BUY (n=71) | 0.0 (tetiklenmiyor) | −1.7 | −1.7 | +3.0 |
| **XAU SELL** (n=75) | 0.0 | **+9.4 (%95)** | +9.4 | −2.4 |
| USOIL BUY (n=28) | +1.6 | +7.0 (%93) | +4.2 | +2.1 |
| USOIL SELL (n=60) | −10.7 ❌ | +1.0 (param-hassas) | −11.3 ❌ | +12.3 |

## CANLI BAĞLANANLAR (ön-kayıtlı kriter: P≥%95 + param-düz + dilim-tutarlı)
1. ✅ **Bot — NDX BUY: BE@30dk + kazananı-koştur** (`yeni deneme/trade_manager.py`, momentum+vixreg magic)
2. ✅ **Bot — GDAXI BUY: yalnız kazananı-koştur** (BE yok — kanıt nötr)
3. ✅ **Bot — NDX vixreg SELL: 10dk sabır kapısı** (`queue_sell`/`process_pending`; sinyalden 10dk sonra ±menzil görülmemişse ve aleyhte <0.3R ise gir)
4. ✅ **claude_decider — LESSONS.md onaylı ders #4** (tüm yönetim kuralları + XAU SELL ihtiyatlı notu)
5. ❌ Bağlanmayan: USOIL (param-hassas/n küçük), XAU bot tarafı (XAU trading kapalı), GDAXI SELL (zaten kapalı olmalı)

Bayraklar: `TRADE_MGMT_ENABLED`, `MGMT_BE_MINUTES=30`, `MGMT_TRAIL_R=0.6`, `VIXREG_SELL_PATIENCE=1` (config.py). Durum: `mgmt_state.json` (restart-dayanıklı). Yaş ölçümü first_seen bazlı (broker TZ kaymasına bağışık; restart'ta BE gecikir = konservatif).

**HEDEF/İZLEME:** 2 hafta sonra MT5 deal geçmişinden `[MGMT]` işlemlerinin gerçekleşen R'ı replay beklentisiyle karşılaştırılacak (beklenti: NDX BUY ort. +0.32R/işlem iyileşme). Sapma büyükse bayraklar kapatılır.

**Dosyalar:** `build_dataset.py` (veri), `replay.py` (motor+10 strateji), `analyze2.py` (segment/grid/bootstrap), `stage3.py` (teşhisler+10 yeni aile), `multi_symbol.py` (dilim+4 sembol), `results*.json`, `per_trade.json`
