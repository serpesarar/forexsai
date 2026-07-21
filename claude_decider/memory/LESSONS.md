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

4. **İşlem-SONRASI yönetim (2026-07-21, research/trade_mgmt_ndx — 223 NDX + 122 DAX
   gerçek işlem, 1m sızıntısız replay, haftalık dilim doğrulamalı):**
   - **NDX BUY açtıysan:** 30dk sonra fiyat girişin üstündeyse SL'i girişe çek (BE);
     fiyat TP'ye VARDIĞINDA çıkma — TP'yi kaldır, 0.6R iz süren SL ile koştur
     (TP sonrası medyan +1.4R devam ediyor). Kanıt: Δ+29.5R [16.4,43.5] P=%100.
   - **DAX BUY:** yalnız kazananı-koştur; BE DAX'ta nötr (Δ+12.1R P=%98.3).
   - **XAU SELL (İHTİYATLI — tek kohort):** kazananı-koştur Δ+9.4R P=%95; BE etkisiz
     (XAU işlemleri 30dk'dan hızlı ölüyor).
   - **SELL pozisyonuna BE/trail UYGULAMA** (NDX SELL'de Δ−7.5R) ve **SL-yarısında
     sürünen işlemi erken kesme** (dwell-dodge 24 varyantta kanıtsız; sürünenlerin
     %31'i toparlıyor).
   - **SELL sinyalinde 10dk sabır:** sinyalden 10dk sonra işlem hâlâ yaşıyorsa ve
     aleyhte <0.3R ise gir (NDX SELL kanaması −39.9→−0.65R; hızlı ölenler kendini
     ilk 10dk'da ele veriyor). BUY'da bekleme YOK — hızlı kazananları kaçırır (−41R).

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

<!-- PANEL-LESSONS START -->
## 📟 Panel dersleri (Evrim Paneli'nden — analiz çıktısı, İHTİYATLA uygula)
- **Günlük Analist (2026-07-21)** (2026-07-21): NDX 5m mean-rev kapısı iki yönde de canlıda tutuyor (140 açılış %67.9); gate_setup OOS eşiği üstündeki kurulumlarda güveni koru, eşik altında çekimser kal.
- **Günlük Analist (2026-07-21)** (2026-07-21): NDX'te canlı bot güçlü momentum SELL'de iken zıt yön BUY açma: son çatışmalarda (n=20) bot 13/5 haklı çıktı, decider'ın karşı-momentum BUY'ları tekrar tekrar LOSS oldu.
<!-- PANEL-LESSONS END -->
