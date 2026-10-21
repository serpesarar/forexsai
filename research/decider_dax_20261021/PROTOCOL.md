# Ön-kayıt — Decider GDAXI (DAX) işlemleri: XAU analizinin aynısı (2026-10-21)

Kullanıcı: "DAX için de aynı analizi yap" (DX-04: decider XAU otopsisi + ileri sınama + erken kesme).
Defter: IO-12 (decider sembol başına gösterge-eşik kuralı — DAX dahil — YOK), DX-04 (XAU erken kesme B, CANLI), OLD-03/04
(bot DAX), M4 (bot DAX BUY kazananı-koştur), E18 (kapıyı başka popülasyona taşıma → hedefte ayrıca ölç).
Decider canlı izin: `GDAXI.INDX:BUY` (LIVE_ALLOWED). Gerçek icra yalnız 2 → popülasyon = journal OPEN kararları (simüle).

## Veri
decider_journal GDAXI.INDX (2026-06-30 → bugün). OPEN kararları; aynı yönde ≤10 sn yinelenen atılır. Giriş = karar ts'sinden
SONRA açılan ilk 1m barın açılışı (+ journal'daki ölçülen spread BUY'da; yoksa sembol medyanı). ATR = journal `trade.atr`
(decider'ın kendi ölçtüğü). Geometri decider'ınki: TP 1,0 / SL 1,5 × ATR (`stop_mults` varsayılanı). Barlar: broker 1m
`indicator_snapshots` (islem_otopsi normalize, saat ekseni düzeltmeli). Aynı barda TP+SL → SL; 48 s ufuk.

## Analizler (XAU ile aynı)
A. Taban: OPEN BUY / SELL ortR, WR vs başabaş, gün-blok P(EV>0), iki yarı; son 14 gün ayrıca.
B. Giriş rastgeleden iyi mi: her karar için aynı UTC dakikası, ±10 gün rastgele gün (200 set), aynı ATR/spread → eşli fark.
C. SL anatomisi: SL'lerin "yön doğru" payı (stoptan sonra 240 dk içinde TP seviyesi), ≤10 dk SL payı, 5. dk R'si ile SL/TP AUC.
D. **Birincil — erken kesme TAŞIMA testi, parametreler XAU'dan DONDURULMUŞ:** 5. dk sonundaki 1m kapanışta R ≤ −0,5 → çık.
   Ölçü: fark (kesmeli − kesmesiz) R/işlem, gün-blok P(fark>0), iki yarı, sonraki-bar açılışında çıkış, spread ×1,5, rastgele-gün
   plasebosu (kural rastgele girişlerde de kazandırıyor mu).
   **Geçme:** BUY'da fark > 0, P ≥ %90, iki yarıda > 0 ve sonraki-açılış çıkışında da > 0 → DAX BUY'a genişletme adayı.
   SELL ve bot DAX işlemleri (islem_otopsi `e5_close_r`) bilgi amaçlı.
E. Plato (bilgi): dakika {3,5,7,10,15} × eşik {−0,3…−0,7}.
