# Decider LESSONS — terfi etmiş dersler (kararı ETKİLER)

> Buradaki her madde JOURNAL'dan **kanıt-kapısını geçerek** geldi (min 20 örnek +
> WR ≥ base+8pp + placebo p<0.05), VEYA araştırmada zaten OOS+placebo doğrulandı.
> "İyi fikir" buraya yazılmaz — yalnız kanıt. Decider bunu her kararda okur.

## ✅ Onaylı dersler (araştırmadan tohumlandı, 2026-06-27)
1. **XAU BUY geniş stop ister.** Gate WR %84 (OOS) ama "patient WR" — dar MT5 stop'la
   canlıda −EV'ye döner. XAU BUY onaylarken `size_factor` düşür ve geniş-stop yönetimi not düş.
   (kanıt: [[xauusd-meta-stop-sizing]])
2. **USOIL SELL / XAU BUY yüksek base'i kısmen dönem trendi.** Oil düşüş, gold yükseliş
   trendi base'i şişiriyor. Bu iki kurulumda canlı WR base'in çok altına inerse (rejim flip)
   → güveni düşür, REGIME.md'yi güncelle.
3. **Kapı-dışı "iyi görünüyor" işlem AÇMA (Faz 1).** Head&shoulders/RSI-divergence/sweep/
   S-R-pivot bizim verimizde edge taşımadı — entry yalnız doğrulanmış 5m mean-rev kapısından.

## 🔍 Canlı gözlemler (küçük örnek — İHTİYATLA uygula, distill doğrulayacak)
1. **GDAXI BUY — rev çelişkisi = düşük kalite.** Kapı rev_chan'da ateşlese bile rev_vwap
   NEGATİF/ters ise (iki gösterge çelişiyor: biri oversold der, diğeri değil) → BEKLE veya
   çok küçük. (canlı 2026-06-29: rev_vwap −0.99'lu 2 GDAXI BUY girişinin ikisi de kaybetti)
2. **GDAXI BUY — ADX ekstreminde zayıf.** ADX>40 (güçlü trend = düşen bıçağı yakalama) veya
   ADX<12 (ölü/choppy) → mean-reversion zayıf, küçült/bekle. Tatlı nokta düşük-orta ADX.
3. **GDAXI SELL zayıf — açma.** Gate %79 ama OOS yalnız %58 (breakeven %60 altı). Opus zaten
   doğru reddediyor; rev_vwap 1.5+ tetiklese bile SELL'e girme. (GDAXI = yalnız seçici BUY)
> Bunlar n~7 canlı gözlem, KANITLANMIŞ değil. `distill_journal.py` n≥20'de placebo ile
> teyit/ret edecek; o zaman ✅'e taşınır ya da silinir.

## ⏳ İzlenenler (henüz kanıt-kapısını geçmedi → kararı ETKİLEMEZ)
*(boş — JOURNAL biriktikçe `distill_journal.py` aday ekleyecek)*

<!-- AUTO-LESSONS START (distill_journal.py üretir) -->
## 🤖 Auto-dersler (decider geçmişinden, kanıt-kapılı)
_Son güncelleme: 2026-07-07 21:33 · journal 1026 kayıt (39 grade-deduped, 971 WAIT, 0 açık) · ~$316.63 quota_

**Genel:** WR 77% (n=39) · EV +0.271R/işlem → ✅ +EV (breakeven ~%60 @ RR0.67)

**Kalibrasyon (canlı vs kanıt base):**
  GDAXI.INDX BUY: canlı %69 (n=13) (kanıt %78)
  NDX.INDX BUY: canlı %71 (n=7) (kanıt %76)
  NDX.INDX SELL: canlı %80 (n=10) (kanıt %62)
  USOIL.FOREX SELL: canlı %100 (n=6) (kanıt %88)
  XAUUSD BUY: canlı %67 (n=3) (kanıt %84)

**Opus yargı değeri:**
  size>med %89(n=18) vs size≤med %67(n=21) → konviksiyon GERÇEK (büyük→daha çok kazanıyor)
  gate-içi %76(n=38) vs kapı-dışı %100(n=1) → kapı-dışı tutuyor — özerklik değer katıyor

**Aday dersler (placebo-kapılı):**
  (kanıt-kapısını geçen yok — terfi yok)
<!-- AUTO-LESSONS END -->

<!-- POST-MORTEM AUTO START (post_mortem.py/distill üretir) -->
### 🔬 Post-mortem (2026-07-07) · distill-yönetimli
İzlenen adaylar (henüz teyitsiz — kararı ETKİLEMEZ):
- ⏳ 1h_adx: kayıplarda yüksek (W 21.37 vs L 46.76, p=0.002, 1/2 teyit)
- ⏳ 1h_beh_last_bounce: kayıplarda düşük (W 0.95 vs L 0.76, p=0.002, 1/2 teyit)
- ⏳ 1h_beh_sr_dist: kayıplarda düşük (W 1.20 vs L 0.47, p=0.002, 1/2 teyit)
- ⏳ 1h_opp_sr_dist: kayıplarda yüksek (W 1.01 vs L 2.87, p=0.002, 1/2 teyit)
- ⏳ 1h_opp_sr_touches: kayıplarda düşük (W 9.08 vs L 5.55, p=0.002, 1/2 teyit)
- ⏳ 1h_rev_chan: kayıplarda düşük (W 0.77 vs L -0.56, p=0.002, 1/2 teyit)
- ⏳ 1h_rev_vwap: kayıplarda yüksek (W -0.79 vs L 0.88, p=0.002, 1/2 teyit)
- ⏳ 1h_trend_aligned: kayıplarda düşük (W 0.93 vs L 0.10, p=0.002, 1/2 teyit)
- ⏳ 1h_vol_ratio: kayıplarda düşük (W 0.84 vs L 0.37, p=0.002, 1/2 teyit)
- ⏳ 1m_adx: kayıplarda düşük (W 35.00 vs L 8.57, p=0.002, 1/2 teyit)
- ⏳ 1m_beh_sr_dist: kayıplarda düşük (W 1.08 vs L 0.93, p=0.010, 1/2 teyit)
- ⏳ 1m_opp_last_bounce: kayıplarda düşük (W 0.93 vs L 0.20, p=0.002, 1/2 teyit)
- ⏳ 1m_rev_chan: kayıplarda düşük (W -0.01 vs L -0.54, p=0.002, 1/2 teyit)
- ⏳ 1m_rev_vwap: kayıplarda yüksek (W -0.55 vs L 0.75, p=0.002, 1/2 teyit)
- ⏳ 1m_trend_aligned: kayıplarda düşük (W 0.68 vs L 0.04, p=0.002, 1/2 teyit)
- ⏳ 1m_vol_ratio: kayıplarda yüksek (W 1.04 vs L 1.54, p=0.002, 1/2 teyit)
- ⏳ 30m_adx: kayıplarda yüksek (W 15.58 vs L 28.13, p=0.002, 1/2 teyit)
- ⏳ 30m_beh_sr_dist: kayıplarda düşük (W 0.98 vs L 0.60, p=0.002, 1/2 teyit)
- ⏳ 30m_opp_sr_dist: kayıplarda düşük (W 1.30 vs L 0.86, p=0.002, 1/2 teyit)
- ⏳ 30m_opp_sr_touches: kayıplarda yüksek (W 8.36 vs L 9.47, p=0.005, 1/2 teyit)
- ⏳ 30m_rev_chan: kayıplarda düşük (W 0.81 vs L 0.01, p=0.002, 1/2 teyit)
- ⏳ 30m_rev_vwap: kayıplarda yüksek (W -0.28 vs L 1.35, p=0.002, 1/2 teyit)
- ⏳ 30m_trend_aligned: kayıplarda düşük (W 0.80 vs L 0.09, p=0.002, 1/2 teyit)
- ⏳ 30m_vol_ratio: kayıplarda düşük (W 0.91 vs L 0.44, p=0.002, 1/2 teyit)
- ⏳ 4h_adx: kayıplarda yüksek (W 40.49 vs L 51.34, p=0.002, 1/2 teyit)
- ⏳ 4h_beh_sr_dist: kayıplarda yüksek (W 1.17 vs L 1.66, p=0.032, 1/2 teyit)
- ⏳ 4h_opp_sr_dist: kayıplarda yüksek (W 0.97 vs L 5.44, p=0.002, 1/2 teyit)
- ⏳ 4h_opp_sr_touches: kayıplarda yüksek (W 11.45 vs L 18.02, p=0.002, 1/2 teyit)
- ⏳ 4h_rev_chan: kayıplarda yüksek (W -0.93 vs L 1.12, p=0.002, 1/2 teyit)
- ⏳ 4h_rev_vwap: kayıplarda yüksek (W -1.64 vs L 1.59, p=0.002, 1/2 teyit)
- ⏳ 4h_trend_aligned: kayıplarda düşük (W 0.92 vs L 0.19, p=0.002, 1/2 teyit)
- ⏳ 5m_adx: kayıplarda düşük (W 34.52 vs L 21.95, p=0.002, 1/2 teyit)
- ⏳ 5m_beh_last_bounce: kayıplarda yüksek (W 0.88 vs L 0.97, p=0.015, 1/2 teyit)
- ⏳ 5m_beh_sr_dist: kayıplarda yüksek (W 0.50 vs L 0.84, p=0.002, 1/2 teyit)
- ⏳ 5m_opp_sr_dist: kayıplarda yüksek (W 1.59 vs L 1.85, p=0.002, 1/2 teyit)
- ⏳ 5m_opp_sr_touches: kayıplarda yüksek (W 13.09 vs L 15.93, p=0.002, 1/2 teyit)
- ⏳ 5m_rev_chan: kayıplarda yüksek (W -0.62 vs L 1.78, p=0.002, 1/2 teyit)
- ⏳ 5m_rev_vwap: kayıplarda yüksek (W -0.74 vs L 0.85, p=0.002, 1/2 teyit)
- ⏳ 5m_trend_aligned: kayıplarda düşük (W 0.25 vs L 0.04, p=0.002, 1/2 teyit)
- ⏳ 5m_vol_ratio: kayıplarda yüksek (W 1.06 vs L 2.24, p=0.002, 1/2 teyit)
- ⏳ n_tf_trend_aligned: kayıplarda düşük (W 2.96 vs L 0.43, p=0.002, 1/2 teyit)
- ⏳ n_tf_trend_anti: kayıplarda yüksek (W 0.84 vs L 4.18, p=0.002, 1/2 teyit)
<!-- POST-MORTEM AUTO END -->
