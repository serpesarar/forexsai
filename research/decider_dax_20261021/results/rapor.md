# Decider GDAXI — XAU ile aynı analiz (ön-kayıt PROTOCOL.md)

Journal OPEN (yinelenmeyen): 222 · yön: {'BUY': 199, 'SELL': 23} · modeller: {'claude-opus-5': 76, 'opus': 64, 'claude-sonnet-5': 63, 'claude-sonnet-5-5': 19}

## BUY — OPEN n=185 (06-30 → 10-20) (gerçek MT5 icrası değil — icra yalnız 2, bkz. SONUC.md)
A. ortR +0.054 · WR %63.2 (başabaş %60) · P(EV>0) %80 · yarılar +0.051/+0.057 · son 14 gün n=10 ortR +0.333
B. giriş − rastgele gün (aynı dakika, aynı ATR/spread, ×200): +0.096 R/işlem, P(>0) %96 (rastgele ortR -0.042)
C. SL n=68: yön doğru (stop sonrası 240 dk'da TP seviyesi) %59 · ≤10 dk %37 · 5. dk R ile SL/TP ayrımı AUC 0.82
D. erken kesme (XAU'dan DONDURULMUŞ 5 dk / −0,5R):
                     varyant   n  kesilen    fark  P(fark>0)         yarılar  ortR kesmeli  ortR taban
          5dk/−0,5 (kapanış) 185       21 -0.0158    +0.2047 -0.0087/-0.0230       +0.0382     +0.0541
        sonraki açılışta çık 185       21 -0.0183    +0.1533 -0.0100/-0.0266       +0.0357     +0.0541
                 spread ×1,5 185       21 -0.0241    +0.1153 -0.0052/-0.0427       +0.0119     +0.0360
sonraki açılış + spread ×1,5 185       21 -0.0274    +0.0833 -0.0081/-0.0466       +0.0086     +0.0360
   rastgele-gün plasebo (×60): kuralın rastgele girişlerdeki kazancı medyan -0.0074 vs gerçek -0.0158
E. plato (fark R/işlem):
 dk    -0.3    -0.4    -0.5    -0.6    -0.7
  3 -0.0301 -0.0146 -0.0151 -0.0072 +0.0002
  5 -0.0672 -0.0368 -0.0158 -0.0060 -0.0012
  7 -0.0897 -0.0887 -0.0226 -0.0181 -0.0003
 10 -0.0506 -0.0670 -0.0520 -0.0219 -0.0102
 15 -0.0094 +0.0029 -0.0036 -0.0095 -0.0015

## SELL — OPEN n=17 (07-10 → 09-08) (gerçek MT5 icrası değil — icra yalnız 2, bkz. SONUC.md)
A. ortR -0.020 · WR %58.8 (başabaş %60) · P(EV>0) %41 · yarılar -0.167/+0.111 · son 14 gün n=0 ortR +nan
B. giriş − rastgele gün (aynı dakika, aynı ATR/spread, ×200): +0.030 R/işlem, P(>0) %57 (rastgele ortR -0.050)
C. SL n=7: yön doğru (stop sonrası 240 dk'da TP seviyesi) %86 · ≤10 dk %29 · 5. dk R ile SL/TP ayrımı AUC 0.53
D. erken kesme (XAU'dan DONDURULMUŞ 5 dk / −0,5R):
                     varyant  n  kesilen    fark  P(fark>0)         yarılar  ortR kesmeli  ortR taban
          5dk/−0,5 (kapanış) 17        0 +0.0000    +0.0000 +0.0000/+0.0000       -0.0196     -0.0196
        sonraki açılışta çık 17        0 +0.0000    +0.0000 +0.0000/+0.0000       -0.0196     -0.0196
                 spread ×1,5 17        1 -0.0729    +0.0000 +0.0000/-0.1378       -0.1906     -0.1176
sonraki açılış + spread ×1,5 17        1 -0.0822    +0.0000 +0.0000/-0.1553       -0.1999     -0.1176
   rastgele-gün plasebo (×60): kuralın rastgele girişlerdeki kazancı medyan -0.0258 vs gerçek +0.0000
E. plato (fark R/işlem):
 dk    -0.3    -0.4    -0.5    -0.6    -0.7
  3 -0.0119 -0.0119 +0.0236 +0.0000 +0.0000
  5 -0.0288 -0.0671 +0.0000 +0.0000 +0.0000
  7 -0.0539 -0.0539 -0.0539 +0.0176 +0.0176
 10 +0.0223 +0.0808 +0.0113 +0.0113 +0.0113
 15 +0.0313 -0.0097 -0.0427 -0.0427 -0.0859

## Bot DAX işlemleri (MOMSR/CHREV, bilgi; 5. dk kapanış R'si islem_otopsi `e5_close_r`): n=66 · kesilen 2 · ortR +0.050 → kesmeli +0.060 (fark +0.010)