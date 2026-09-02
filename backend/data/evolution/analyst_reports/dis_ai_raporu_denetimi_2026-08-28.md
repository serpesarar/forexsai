# Dış AI raporunun denetimi — "NASDAQ 13–27 Ağustos" kural paketi

**Tarih:** 2026-08-28 · **Denetlenen:** `NASDAQ_AUGUST_SONI_ANALIZ.md` (dış AI, n=28)
**Yöntem:** 120 günlük gerçek MT5 geçmişi (482 kapanmış işlem, 282'si NAS100),
101.288 adet 1m bar, sızıntısız bar-yolu simülasyonu, 2 puan spread sürtünmesi.
**Bölünme:** DIŞ-örneklem 29 Haz–12 Ağu (n=254) · İÇ-örneklem 13–27 Ağu (n=28, raporun verisi)

## VERDİKT: paketin 5 kuralının 5'i de canlıya ALINMADI

| Kural | Raporun iddiası | Dış-örneklem gerçeği | Hüküm |
|---|---|---|---|
| **K1** saat 07 UTC bloğu | "en güçlü tek filtre", 3/3 SL −900$ | n=5, WR %60, **+99$**, ortR +0.036 (diğer saatlerden İYİ) | ❌ iç-örneklem gürültüsü (n=3) |
| **K2** SELL gün-rejimi kapısı | dayret>0 & daypos>0.7 → SELL yok | Engelleyeceği işlemler n=36 **ortR +0.144 / +2.875$**; kalan ortR +0.008 / **−16$** | ❌ **TERS** — sistemin en kârlı kümesini kesiyor |
| **K3/D4** TP=2×ATR14(1m) | WR %60.7→%82.1, PnL korunur | WR gerçekten +14/21pp **ama para**: DIŞ +1.448$ → **−2.458$**; İÇ +1.977$ → +1.617$ | ❌ "kozmetik WR" — 2026-08-15'te zaten elenmişti |
| **K4** REENTRY'ye K2 | 26 Ağu SL'i bloklanıyor | Dayanak n=1; K2'nin tersliğini miras alır | ❌ kanıt yok |
| **K5** BE@0.5R tetiklenmedi | "botun BE eşiğini kontrol edin" | MFE=**0.518R** doğru; ama `trade_manager.py:133` SELL'i bilinçli kapsam dışı bırakır (SELL BE = Δ−7.5R) | ❌ hata değil, tasarım |
| **D8** = K1+K3 (şampiyon) | WR %84 | İki bileşeni de yukarıda eleniyor | ❌ |

### K3 neden bu kadar önemli bir hata
`phase_rules.py` içinde `TP_MODE` varsayılanı **2026-08-15'te** tam bu gerekçeyle
"fixed"e alınmıştı: *"küçük hedef 'yüksek WR' kozmetiği üretiyor, kenar üretmiyor."*
Rapor aynı deneyi yeniden keşfedip "şampiyon" ilan etti. Kendi tablosunda bile
imza görünüyor: WR %60.7→%82.1 iken PnL +1.859$→+1.850$ (yatay).

## YAN BULGU: kâr ters yönde — hedefi KÜÇÜLTMEK değil, BÜYÜTMEK

Aynı motorla TP çarpanı taraması (2 puan sürtünme dahil, ortR/işlem):

| TP | DIŞ-örneklem | İÇ-örneklem | Ç1 | Ç2 | Ç3 | Ç4 | 4/4 pozitif? |
|---|---|---|---|---|---|---|---|
| sabit (mevcut) | +0.007 | +0.147 | +0.091 | +0.020 | −0.107 | +0.079 | hayır |
| **2.0×ATR (K3)** | **−0.007** | +0.097 | +0.065 | **−0.092** | +0.015 | +0.025 | hayır |
| 3.0×ATR | +0.031 | +0.190 | +0.108 | +0.028 | +0.009 | +0.044 | ✅ |
| 4.0×ATR | +0.050 | +0.163 | +0.100 | +0.029 | +0.065 | +0.053 | ✅ |
| **5.0×ATR** | **+0.079** | **+0.290** | +0.156 | +0.049 | +0.057 | +0.135 | ✅ |
| 6.0×ATR | +0.060 | +0.122 | — | — | — | — | tepe sonrası düşüş |

3-4-5× üçlüsü **iki dönemde ve dört çeyrekte de** pozitif, 5×'te tek tepe →
plato imzası. Kart ölçüt-3 (kronolojik kararlılık) geçiyor.

**AMA canlıya alınamaz — simülasyon canlıyı taklit etmiyor:**
1. `MAX_OPEN_PER_SCOPE=1` — uzun tutuş sonraki sinyalleri bloklar; sim bu fırsat
   maliyetini modellemiyor.
2. Sim, BUY'lardaki BE@30dk + 0.6R kazananı-koştur yönetimini modellemiyor
   (mevcut "runner" mekanizması bu etkinin bir kısmını zaten yakalıyor).
3. Çok günlük tutuşta swap + hafta sonu boşluğu yok.
4. Aynı aile (`TP_MODE="atr"`) bir kez OOS'ta elendi — sime güvenmek tam olarak
   o hatanın tekrarı olur.

→ Önerilen: **gölge bayrağı** (`TP_ENLARGE_SHADOW`), 2 hafta ölçüm, sonra
koşullu plasebo + derin dış-örneklem. Varsayılan = eski davranış.

## Kalıcı ders
Dış raporun tek bir metodolojik kusuru vardı: **her şey n=28'lik tek pencerede
optimize edildi, dış-örneklem yok.** Beş kuralın beşi de o pencerenin
gürültüsüydü; ikisi (K2, K3) canlıda para kaybettirecekti. Kural: WR yükselten
her öneri önce beklenti-R ve para ekseninde, sonra kronolojik dilimlerde sınanır.
