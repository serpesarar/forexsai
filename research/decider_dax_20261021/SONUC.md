# Sonuç — Decider GDAXI (DAX): XAU analizinin aynısı (2026-10-21)

Ön-kayıt: [PROTOCOL.md](PROTOCOL.md) · çıktı `results/rapor.md`. Popülasyon: decider journal OPEN kararları (yinelenmeyen 222:
BUY 199 / SELL 23), broker 1m ile decider geometrisi (TP 1,0 / SL 1,5 × ATR) simüle. Gerçek MT5 icrası yalnız **2**.

## BUY (185 karar, 06-30 → 10-20)
| ölçü | sonuç |
|---|---|
| ortR / WR | **+0,054R**, WR %63,2 (başabaş %60), P(EV>0) %80, yarılar +0,051 / +0,057 (kararlı) |
| son 14 gün | 10 karar +0,333R |
| giriş − rastgele gün (aynı dakika/ATR/spread, ×200) | **+0,096R/işlem, P %96** (rastgele giriş −0,042) |
| SL anatomisi (68 SL) | %59'u yön doğru (stoptan sonra TP seviyesi), %37'si ≤10 dk, 5. dk R'si SL/TP'yi ayırıyor (AUC 0,82) |
| **erken kesme (XAU'dan dondurulmuş 5 dk / −0,5R)** | **−0,016R/işlem, P %20; sonraki açılış −0,018; plato 25 hücrenin ~23'ü negatif → DAX'a TAŞINMIYOR** |
SELL (17 karar) yetersiz ve ≈başabaş. Bot DAX işlemleri (66) erken kesmede yalnız 2 kesim (+0,010, bilgi).

## Asıl bulgu: DAX BUY kararları icra edilemiyor
Kutu `claude_decider/live_orders.jsonl`: 10-05 → 10-20 arasındaki 23 DAX BUY emir denemesinin **16'sı "günlük emir sınırı (10)"**,
5'i Asya saatinde spread/ATR > 0,15, yalnız 2'si gönderildi. Sınır (`execute_mt5.LIVE_MAX_ORDERS_PER_DAY = 10`) TÜM semboller için
ortak; günün erken saatlerinde XAU (ve NDX SELL) emirleri onu dolduruyor, DAX'ın Avrupa/ABD seansındaki kararları hak bulamıyor.

## Hüküm
- Decider DAX BUY seçimi XAU'daki gibi rastgeleden iyi (P %96) ve ortalama hafif pozitif (+0,054R, P %80) — XAU ile aynı sınıf.
- XAU'nun erken kesme kuralı DAX'ta zararlı → **genişletilmez** (E18: kapı başka popülasyona taşınmaz).
- Düzeltme adayı (yapılandırma, kanıt değil): günlük emir sınırını **sembol başına** yapmak, ki DAX kararları icra edilsin.
  Canlı davranışı değiştirdiği için kullanıcı kararı.
