# SL Patlaması Otopsisi + Trend Hizası Kapısı — 2026-07-24

Soru: "son 2-3 günde çok SL oldu, yeni filtreler yüzünden mi?"
Veri: `bot_trades` (evolution agent push'u) 332 canlı işlem, 30 gün.

## 1. Kısa cevap: yeni filtreler SEBEP DEĞİL

Günlük net: 07-20 −1.431$ · 07-21 +1.145$ · 07-22 −134$ · 07-23 −705$ · 07-24 −1.846$.
Filtrelerin (BE30/runner/SABIR/CHREV-kapısı) hepsi 07-21 sonrası; kayıplar
onlardan ÖNCE de vardı. Filtrelerin doğrudan zarar ürettiği tek bir işlem yok.

**07-23 detayı:** WR %61 (17W/11L) ama net −705$ — kazanç/kayıp asimetrisi.
CHREV olmasaydı gün +1.070$ kârdaydı.

## 2. Motor bazlı 30 günlük gerçek (kanamanın haritası)

| Motor / scope | n | WR | Net |
|---|---|---|---|
| NAS100 VIXREG SELL | 174 | %59.2 | **+2.071$** |
| SpotCrude mom BUY | 54 | %64.8 | **+1.511$** |
| SpotCrude **mom SELL** | 37 | %37.8 | **−2.509$** |
| **CHREV (tüm kollar)** | 43 | — | **−4.985$** |
| GER40 mom BUY | 4 | %25.0 | −1.104$ |
| NAS100 mom BUY | 15 | %46.7 | −418$ |

## 3. ANA BULGU — karşı-trend girişleri sistemi yiyor

1h EMA50'ye göre (BUY→üstünde, SELL→altında = "hizalı"):

| | n | WR | Net |
|---|---|---|---|
| **Trend-yönü** | 210 | **%63.3** | **+9.710$** |
| **Karşı-trend** | 122 | **%43.4** | **−13.161$** |

Neredeyse her sembol/yön/motor kombinasyonunda aynı yön. En sert:
USOIL SELL karşı-trend n=29 WR %31 **−3.110$** (trend-yönü n=8 %62 +706$).

**Hindsight testi (kritik):** EMA50 kapanış anı yerine 1/2/4/8 saat öncesinden
ölçüldüğünde ayrışma DAYANIYOR (2h: trend %61.5 +4.934$ / karşı %46.2 −8.385$;
4h: %60.4 / %47.3). Etki kapanışa yaklaştıkça büyüyor (bir miktar hindsight var)
ama girişe yakın pencerelerde de net → gerçek edge.

Kavramsal destek: "momentum-continuation" tanımı gereği trend yönünde olmalı;
EMA50'nin ters tarafında açılan momentum girişi kendi tezi ile çelişiyor.
Sistemde aynı prensibin kabul görmüş örnekleri: `XAU_TREND_SELL_GATE`,
`NDX_SMC_SELL_GATE` (H4 close>EMA50 → SMC SELL blok).

## 4. Reddedilen hipotez (dürüstlük kaydı)

"SL sonrası hemen yeniden giriş zararlı" → **YANLIŞ.** 30g: SL sonrası <90dk
girişler n=60 WR %55.0 **+679$**; diğerleri n=259 WR %55.2 −5.803$. Momentum
scope'larına cooldown EKLENMEDİ.

## 5. Uygulananlar

1. **`trend_alignment` + `_trend_gate_blocks`** (`yeni deneme/forexsai_demo_bot.py`):
   giriş anında botun KENDİ 1h MT5 barlarıyla EMA50 hizası; hizasızsa giriş yok.
   - momentum/SR scope'ları → `TREND_GATE_ENABLED` (default açık)
   - VIXREG → `VIXREG_TREND_GATE` (ayrı bayrak; NDX SELL trend n=123 %63 +5.5k$
     vs karşı n=51 %51 −3.5k$)
   - Fail-open: 1h barı yoksa giriş engellenmez.
2. **GDAXI SELL CHREV → "gated"** — dün tabloda unutulmuştu (varsayılan "open"),
   07-24'teki 2 SL (−1.350$) o boşluktan geçti. Taraması: 30g WR %73.1, kapılı %83.3.
3. **`CLAUDE_BIN` yol çözümü** (`claude_decider/decide.py::_claude_bin`) — çıplak
   `["claude"]` Windows'ta PATH'te bulunamayınca her karar sessizce
   `claude exit 1` → WAIT'e düşüyordu. Sıra: CLAUDE_BIN env → PATH → bilinen
   npm/local yolları. `preflight` mesajı da güncellendi.

## 6. Açık kalan şüphe — bot eski kodda olabilir

07-24 19:06–20:54 arası USOIL işlemleri hâlâ **kırıntı TP** ile açılmış
(TP ~0.15 puan; +78/+88/+92$). 07-23'te eklediğim RR tabanı (`min_tp_dist ≥
0.3×SL` = 0.40 puan) uygulansaydı bunlar sabit TP'ye (0.93 puan) düşerdi.
→ **Kutunun gerçekten `f727601`+ üzerinde olduğu doğrulanmalı.** Aynı şüphe
07-24'teki 10016/10018 retlerinin sürüp sürmediğiyle de test edilebilir.

## 7. İzleme

Trend kapısının etkisi 1 hafta sonra ölçülecek: karşı-trend işlem sayısı ~0'a
inmeli; hedef net WR %63 bandı. Ölçüm: aynı `bot_trades` sorgusu +
`TREND_GATE` etiketli `_log_trade` satırlarının sayımı (kaç giriş elendi).
