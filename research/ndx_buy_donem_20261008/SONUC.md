# NDX BUY: son 45 gün neden iyi, öncesi neden değil? (2026-10-08)

`analyze.py` · `results/`. Bot NDX BUY kararları: önce (06-30 → 08-23) 56, son 45 gün (08-24 → 10-08) 20.

## Cevap: piyasa + strateji karışımı + küçük örneklem; decider DEĞİL

**1. Piyasa yönü değişti.** NDX önce −%3,6 (Temmuz −%6,9; yükselen gün %47, günlük oyn. %1,25),
son 45 gün +%6,9 (yükselen gün %62, oyn. %0,77). Kapısız taban (ABD seansında saat başı BUY, yönetimsiz):
- bot geometrisi 80/110: önce −0,10R → son45 +0,02R
- "kazanan" geniş geometri 137,5/240: önce **−0,20R** (Temmuz −0,38) → son45 **+0,19R** (Ekim +0,90)
→ Son 1,5 ayın en iyi TP/SL'si (TP×3) yükselen piyasaya yapılmış bir bahis; düşen Temmuz'da en kötüsü.
Önceki dönemde test edince kötü çıkmasının sebebi bu (IO-13).

**2. Kaybettiren aileler NDX BUY'dan çekildi, kalan aile aynı performansta.**
| aile | önce | son 45 gün |
|---|---|---|
| MOMSR | 21 işlem, −0,04R | 0 |
| CHREV | 13, −0,07R | 0 |
| VIXREG BUY | 3, +0,73R | 0 (VIX < 18,4) |
| **DAYCOMBO** | 19, **+0,28R** | 11, **+0,25R** — değişmedi |
| REENTRY | — | 9, +0,53R (Eylül'de başladı) |
Ortalamadaki sıçrama (+0,10 → +0,38R) iyileşmeden değil, karışımdan: zayıf aileler gitti, REENTRY yükselen
piyasada kazananları tekrarladı.

**3. Bot girişi rastgeleden iyi — ama örneklem küçük.** Aynı saat/geometride rastgele giriş: önce bot +0,10 vs
rastgele +0,05; son45 bot +0,38 vs rastgele −0,03. Son45 %95 aralığı +0,03…+0,64 (n=20). Ekim'deki 2 işlemin
ikisi de −1R (30 lot, −6.755$).

**4. Decider'ın etkisi yok.** Decider NDX BUY canlıda 07-28'den beri engelli; bot decider'a yalnız momentum/
CHREV/VIXREG'in "çukur" pencerelerinde bakar (DAYCOMBO/REENTRY bakmaz); decider 09-11 → 10-02 kapalıydı;
decider'ın kâğıt NDX BUY'ları aylar içinde kötüleşti (Tem −0,01, Ağu −0,58, Eyl +0,06, Eki −1,0R).

## Ders
Son 1,5 ayın performansı "sistem öğrendi" değil, "piyasa yükseldi + kötü aileler BUY açmadı". Piyasa yön
değiştirirse DAYCOMBO'nun (+0,25…+0,28R, iki dönemde sabit) dışındaki artış geri gidebilir. Geometriyi
yükselen piyasaya göre genişletmek (TP×3) düşen piyasada en kötü sonucu verir.
