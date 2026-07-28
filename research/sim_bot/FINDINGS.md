# Hızlandırılmış Geçmiş Deneyi (Timelapse Backtest) — 2026-07-28

Kullanıcı isteği: "ileriye dönük 2 hafta bekleyeceğine geçmiş veriyi sırayla
botun içinden geçir, gelecek görmeden test et."

## Kurulum

`sim.py` — botun karar döngüsünü bar-bar tekrarlar:
- **Sinyaller uydurulmadı:** `prediction_logs`'taki GERÇEK pulse1/2/3 çıktıları
  (NDX 2.510 · GDAXI 1.785 · USOIL 6.850 sinyal, 2026-06-01 → 07-28)
- **Barlar:** `candle_cache` 1m (çözüm) + 5m (dalga konumu) + 1h (EMA50 trendi)
- **Geometri:** botun kendi sabitleri (NDX 80/110, GDAXI 67/119, USOIL %1.04/%1.49)

**Sızıntı sözleşmesi (kodda zorlanır):** her karar yalnız o ana kadar kapanmış
barlarla (`bars[:i]`); giriş = karar barının kapanışı; çözüm yalnız sonraki
barlarla; aynı barda TP+SL → konservatif SL; scope başına tek açık pozisyon.

**Simüle EDİLEMEYENLER (dürüstlük notu):** backend momentum filtresi (geçmişe
gösterge snapshot'ı yok), VIX rejimi (geçmiş VIX serisi yok — bu yüzden SELL
testleri VIXREG alt kümesi değil, TÜM pulse SELL sinyalleridir),
spread/slippage/komisyon (sonuçlar brüt).

## Walk-forward: kronolojik %60 IN / %40 OUT

Eşikler yalnız IN'de bakıldı; OUT dilimi hiç görülmeden test edildi.

| Sembol / Yön | baseline OUT | **trend+konum OUT** | avgR değişimi |
|---|---|---|---|
| NDX BUY | %63.2 · +5.18R | **%82.6 · +9.82R** | +0.091 → **+0.427** |
| NDX SELL | %63.2 · +6.91R | **%80.8 · +10.27R** | +0.091 → **+0.395** |
| GDAXI BUY | %59.1 · −3.36R | **%88.2 · +6.45R** | −0.076 → **+0.379** |
| GDAXI SELL | %71.1 · +4.20R | **%81.2 · +4.32R** | +0.111 → **+0.270** |
| USOIL BUY | %67.5 · +11.30R | **%79.2 · +18.32R** | +0.147 → **+0.346** |
| USOIL SELL | %52.9 · −7.17R | **%68.2 · +3.47R** | −0.102 → **+0.158** |

**6/6 sembol-yönde trend+konum kombinasyonu OUT-OF-SAMPLE'da baseline'ı yendi**
— hem kazanma oranı hem işlem başına verim. İki negatif baseline (GDAXI BUY,
USOIL SELL) artıya döndü. GDAXI BUY'da IN ve OUT birebir aynı (%88.2/+6.45R).

Tek başına kapılar daha zayıf: trend tek başına ortalama +0.15 avgR, konum tek
başına +0.13; **birlikte +0.32** — tamamlayıcılar (biri yön hatasını, diğeri
konum hatasını eliyor).

## ⚠️ SABIR kapısı OUT-OF-SAMPLE'da ZARAR VERİYOR

| SELL scope | trend+konum OUT | +sabır OUT |
|---|---|---|
| NDX | +10.27R | **+5.18R** ↓ |
| GDAXI | +4.32R | **+0.63R** ↓ |
| USOIL | +3.47R | +2.77R ↓ |

Bu, canlıya bağladığım kapının kanıtıyla ÇELİŞİYOR (bot_trades replay'i
Δ+39.3R vermişti). Çelişkinin kaynağı popülasyon farkı: eski ölçüm gerçek
VIXREG işlemleriydi (VIX filtresinden geçmiş alt küme), bu ölçüm tüm pulse
SELL sinyalleri. Hangisinin geçerli olduğu **canlı veriyle** çözülecek —
`gate_skipped.jsonl` zaten sabır iptallerini kaydediyor. **Karar: kapı şimdilik
duruyor, ama izleme listesinde ve n≥20'de `gate_audit.py` ile hükme bağlanacak.**
Bugünkü canlı gözlem de uyarı yönünde: 8 kuyruktan geçen tek işlem SL oldu.

## Konum eşiği duyarlılığı (IN-sample, trend açık)

| | 0.3 | 0.4 | 0.5 | 0.6 |
|---|---|---|---|---|
| GDAXI BUY | +6.3 | +6.5 | +6.9 | +5.1 |
| USOIL BUY | +8.3 | +9.3 | +3.4 | +5.1 |
| USOIL SELL | +15.1 | +13.7 | +14.1 | +17.4 |

0.3–0.6 aralığı **düz** — tek noktaya oturmuş bir optimizasyon değil. Canlıdaki
0.40 bu platonun ortasında, değiştirmeye gerek yok. (NDX SELL'de IN'de eşiksiz
daha yüksek totR görünüyor ama bu işlem sayısı etkisi; OUT'ta trend+konum hem
totR hem avgR olarak baseline'ı geçiyor.)

## Sonuç

1. **Canlıdaki trend + konum kapıları doğrulandı** — sızıntısız, kronolojik
   OUT-OF-SAMPLE'da 6/6. Bunlar için "2 hafta bekle" gereği kalktı.
2. **Sabır kapısı şüpheli** — iki ölçüm çelişiyor, canlı veriyle çözülecek.
3. **Backend gölge vetosu** bu deneyle test EDİLEMEZ (geçmişe Precision Veto
   çıktısı yok) — gölge modda kalmalı, ~2 hafta sonra `gate_audit` ile.

**Dosyalar:** `sim.py` (harness) · `walkforward.py` (doğrulama+duyarlılık) ·
`bars_*.json`/`sig_*.json` (yerel önbellek)
