# ForexSAI — Claude Decider PLAYBOOK (doğrulanmış priorlar)

> Bu, `claude_decider`'ın HER kararda okuyacağı temel. Tüm kurallar bizim verimizde
> **OOS + placebo + dedup** ile doğrulandı. Kitap/sezgi DEĞİL — kanıt. Ham geçmişi
> yeniden analiz etme; bu damıtılmış base rate'lere göre karar ver.

## 🎯 EPİSTEMİK KURALLAR (önce bunu oku)
1. **Yalnız doğrulanmış kurulumda işlem aç.** Aşağıdaki ✅ edge'ler dışında "iyi görünüyor" deme.
2. **Base rate'e güven, anlatıya güvenme.** Mantıklı gerekçe ≠ kârlı. Çoğu "bariz" kurulum bizde edge taşımadı.
3. **Belirsizsen BEKLE (HOLD).** İşlem açmamak da bir karar.
4. **RR ≈ 0.67** (TP1 ~1×ATR, SL ~1.5×ATR) → breakeven WR ~%60. Sadece WR≥%65 beklenen kurulumları al.

## ✅ DOĞRULANMIŞ EDGE'LER (base rate'leriyle)

### 1. 5m Mean-Reversion Aşırılığı (EN GÜÇLÜ — re-damıtma 2026-06-27 ile sadeleşti)
- **Tetik (yön-hizalı):** 5m'de fiyat ya linreg trend-çizgisinden **rev_chan > 2.0σ** ya da VWAP'tan **rev_vwap > 1.5σ** sinyal yönünün TERSİNE aşırı uzakta (BUY=oversold, SELL=overbought). `rev = (−z) if BUY else z`.
- **KRİTİK SADELEŞME:** Edge **tek-koşullu ve 5m**. Kapsamlı tarama (21.5k deduped, 5 model, greedy+nested-CV+placebo) 2. koşul ve üst-TF eklemeyi REDDETTİ (gain<%3) → basit = robust. Eski "z≥2.5 + multi-TF" gereğinden karmaşıktı; gerçek sinyal 5m tek-boyut.
- **Base rate (nested-CV DÜRÜST OOS, placebo p=0, 4/4 fold):** meta **%88** · smc **%83** · pulse3 %77 · pulse1 %73 · pulse2 %71. Eşik modele göre: meta/smc yüksek aşırılık ister (rev>1.85/2.6), pulse'lar düşük eşikte çalışır (rev>1.1-1.7).
- **Yön:** BUY (oversold dönüş) genelde SELL'den güçlü. Per-sembol tablo aşağıda (artık dürüst OOS).

### 2. Momentum-Continuation (backend-filtreli)
- **Tetik:** backend momentum filtresi (M15 stoch>70, dist_ema20_atr>0.8, SAR) geçen 4 scope.
- **Base rate:** NDX:BUY %78.6 · USOIL:SELL %96.6 · GDAXI:BUY/USOIL:BUY +EV (bootstrap %99.9).
- **Not:** mean-reversion'ın ZITTI — güçlü momentumda geçerli (M15 stretch>2σ).

### 3. VIX-Rejim → NDX YÖNÜ (makro)
- **Tetik:** VIX<18.4 (sakin)→**NDX SELL** favored · VIX≥18.4 (stres)→**NDX BUY** favored.
- **Base rate:** favored yön %70 vs against %45 (**+25pp, OOS +17, placebo p=0**). pulse1/pulse2 güçlü.
- **YALNIZ NDX.** XAU'da makro çöküyor.

## ⛔ DOĞRULANMIŞ BAŞARISIZLIKLAR (ASLA bunlara dayanma)
- **XAUUSD intraday:** edge YOK (yazı-tura, canlı −16k). **XAU SELL kalıcı YASAK.** XAU yalnız BUY (yapısal bias) + daily-swing (Donchian, ayrı).
- **S/R pivot rejection:** zayıf/zararlı (geniş toleransta −EV).
- **Liquidity sweep (dönüş):** NEGATİF (−8/−12pp). **(devam):** mütevazı + kanalla redundant.
- **Volume Profile:** gerçek ama kanalla REDUNDANT (ek değer yok).
- **Makro→XAU yön:** çöküyor (güncel veriyle de). XAU'da makro KULLANMA.
- **RSI/MACD tek başına:** zayıf. Yalnız kombinasyonda (ör. adx<23 & macd_hist<0) işe yaradı.
- **Yüksek-ADX/yüksek-momentumda naive giriş** → SL (mean-reversion için; momentum scope ayrı).

## 📊 SEMBOL-YÖN ÖZETİ (5m mean-rev kapısı — 2026-07-27 CANLI-BLEND vintage)
Kapı WR = araştırma prior + 1894 grade'li CANLI karar Bayesyen blend'i (refresh_evidence).
OOS = araştırma out-of-sample; † = canlı-teyitsiz ≥%80 iddia 72'ye kapaklandı.
| Sembol | Yön | Kapı WR (canlı-blend) | OOS WR | Karar |
|---|---|---|---|---|
| **GDAXI** | BUY | %61 | %78 | ✅ hâlâ en güçlü index — ama eski %89 ŞİŞİKTİ; ekstrem kovalar (rev>2.5) hâlâ %79-81 |
| GDAXI | SELL | %61 | %58 | ⚠ OOS breakeven (%60) ALTINDA — yalnız ekstrem kova (rev_chan>3) + küçük boyut (≤0.3) |
| **NDX** | BUY | %63 | %76 | ✅ (yön için VIX-rejim) |
| NDX | SELL | %67 | %62 | ✅ ince marj ama canlıda DÜZELDİ (canlı %68, n=170) |
| **USOIL** | SELL | %62 | %72† | ⚠ **REJİM-FLIP ŞÜPHESİ GERÇEKLEŞİYOR**: canlı %58 (n=173) breakeven altı — eski %91 dönem trendiydi. Kanıt eşiğini yüksek tut, boyut küçült |
| USOIL | BUY | %30 | %10 | ❌ mean-rev ÇÖKER (momentum scope ayrı, +EV) |
| **XAUUSD** | BUY | %70 | %72† | ✅ PATIENT WR — DAR stop (13-25 puan ≈0.3-0.6×ATR) −EV; ama 2026-07-28 ölçümü 2.5×ATR'yi de ELEDİ (12 politikada iki havuzda da alttan 3'te) → geometri ev varsayılanına döndü: TP1.0/SL1.5, breakeven %60. Canlı %67 (n=150); NY seansında canlı %15 (n=20) — NY'de XAU BUY'a aşırı temkin |
| XAUUSD | SELL | %42 | %21 | ❌ **KALICI YASAK** |

> 🔬 **CANLI KALİBRASYON (2026-07-27, 1894 grade'li karar):** araştırma-dönemi yüksek iddialar
> canlıda ŞİŞİK çıktı (%80-90 vaadi → canlı ~%64, %90-100 → %55; ECE 12.9pp). evidence_tables
> artık canlı-blend + kapaklı: hücrelerdeki `live_n` = canlı örnek, `capped:true` = iddia
> kapaklandı. `live_n` küçük + WR yüksek hücreye temkinle yaklaş; tablo tek gerçek kaynaktır.

> ⚠️ **Base-rate drift uyarısı (2026-07-27 GÜNCELLEME — tahmin gerçekleşti):** USOIL SELL'in
> eski %91'i canlıda %58'e indi (n=173) — dönem-trendi şüphesi DOĞRULANDI. XAU BUY %67'de
> tutunuyor. Rejim dönerse base düşer; canlı WR (`live_n` hücreleri) her zaman esastır.

## ⚙️ RİSK
- RR ~0.67, breakeven %60 → WR≥%65 hedefle. · Günlük zarar limiti var. · Aynı yönde aşırı yığılma yapma.
- Yüksek-etkili haber/olay (FOMC/CPI/NFP/EIA) penceresinde: yön tahmin etme, KÜÇÜLT/BEKLE.

## 🔄 CANLI ADAPTASYON
Sana her kararda **son N canlı işlem sonucu** verilir. Bir edge'in canlı WR'ı base rate'inin
ÇOK altına düşüyorsa (ör. %88 beklenen kanal %55'e indi) → o edge'e güveni düşür, BEKLE'ye meylet.
