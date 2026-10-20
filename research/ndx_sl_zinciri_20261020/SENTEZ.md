# 2026-10-19 NASDAQ ardışık SL zinciri — sentez (2026-10-20)

Kaynaklar: kutu `demo_bot.log` (log saati kutu yereli = UTC−4; `results/log_1019.txt`), `bot_trades` +
`output/islem_otopsi/2026-10-20_1409_ndx/`, bot kodu (`yeni deneme/forexsai_demo_bot.py`, `reentry_exec.py`,
`phase_rules.py`), kutu `config.py` (grep).

## Zincir (hepsi NDX BUY, 30 lot, TP 80 / SL 110 puan; UTC)
| # | aile | giriş → çıkış | sonuç | $ | neden açıldı (log) | SQZ |
|---|---|---|---|---|---|---|
| 1 | DAYCOMBO | 14:26 → 15:23 | TP | +2.400 | gece +%0,51 & 15m trend↑ & gövdeli yeşil 5m; probasyon geçti | ≥1 (uyarı yok) |
| 2 | REENTRY | 15:30 → 16:30 | SL | −3.330 | #1 TP ile kapandı → +5 dk yeniden giriş | 0,68 (gölge uyarısı) |
| 3 | DAYCOMBO | 15:31 → 16:30 | SL | −3.300 | #1 kapanınca slot boşaldı, aynı kural tekrar ateşledi; #2 hâlâ açık (ayrı magic) | 0,69–0,72 |
| 4 | REENTRY | 16:32 → 17:47 | SL | −3.300 | #3 SL ile kapandı → +1 dk yeniden giriş | 0,90 |
| 5 | DAYCOMBO | 16:51 → 20:00 | SL | −3.342 | 3. DAYCOMBO; probasyon geçti (−26,9 puan daha iyi giriş) | 0,90–0,91 |
| 6 | REENTRY | 20:02 → 23:04 | TP | +2.243 | #5 SL ile kapandı → +1 dk | ≥1 |
Toplam −8.629 $. DECIDER aynı gün 0,1 lotla ±3–6 $ (önemsiz).

## Neden bu kadar sık açıldı — üç tasarım/kod kusuru
1. **Günlük zarar freni bu iki aileyi görmüyor.** `_bot_magics()` yalnız ana + CHREV + VIXREG + CAPREV magic'lerini sayıyor;
   DAYCOMBO (+4) ve REENTRY (+6) yok. `DAILY_MAX_LOSS=3000` ve `MAX_TOTAL_POSITIONS=6` bu yüzden kör: 16:30'da realize
   −4.230 $, 17:47'de −7.530 $ iken logda tek bir "GÜNLÜK ZARAR LİMİTİ" satırı yok. Kutu config'indeki not 30 lotta tek SL'nin
   ~3.300 $ olduğunu ve freni hesaba kattığını söylüyor; fren bu ailelerde hiç çalışmadı.
2. (olası, doğrulanmadı) `today_realized_pnl()` `history_deals_get`'e UTC tarih veriyor; MT5 broker saati bekliyor
   (`reentry_exec.py` başlığında aynı tuzak yazılı) → son ~3 saatin işlemleri görünmez. Kutuda doğrulanmalı.
3. **Üst üste binme + kendini yeniden tetikleme.** REENTRY ayrı magic olduğu için DAYCOMBO slot kilidine takılmaz; DAYCOMBO
   kendi pozisyonu kapanır kapanmaz (günlük sınır/soğuma yok) yeniden ateşler. Sonuç: aynı bahse 60 lot, 16:30'da iki SL
   aynı dakikada (−6.630 $). Ardından her DAYCOMBO kapanışı bir REENTRY doğurdu.

## Yeni kurallar mı? — Hayır
- Bu işlemleri açan kurallar eski: DAYCOMBO 2026-07-28'den, REENTRY ~08-24'ten beri canlı. Son haftaların commit'leri
  (CAPREV 10-09, XAU gölgeleri, mum benzerlik, fakeout NDX blok 10-20) bu zinciri açmadı; CAPREV dün NDX'te işlem açmadı.
- Bot 10-15'ten beri yeniden başlamamıştı (restart borcu hatası, afd54638) → 10-15 sonrası kod zaten çalışmıyordu.
- Değişen şey **risk büyüklüğü**: DAYCOMBO lot çarpanı 0,2→3,0 (30 lot); REENTRY de 30 lotla açılıyor. Defterde en zayıf
  kanıtlı iki aile bunlar: DAYCOMBO 2025 bağımsız verisinde −0,03R (CK-03, X), REENTRY dış-örneklem plasebosu ❌ (M2, C).
- MOD-E probasyonu üç DAYCOMBO'yu da geçirdi; neden değil.

## Dün ne olsaydı (elle, yukarıdaki tablo; çocuk REENTRY ebeveyniyle birlikte düşer)
| kural | dün sonuç | kurtarılan |
|---|---|---|
| fren tüm magic'leri saysa (−3.000 $) | −4.230 $ | +4.399 $ |
| aynı yönde üst üste binme yok | −2.029 $ | +6.600 $ |
| SL sonrası 60 dk soğuma | −4.230 $ | +4.399 $ |
| DAYCOMBO günde 1 | −930 $ | +7.699 $ |
| SQZ ≥1,00 (B14, şu an gölge) | +2.400 $ | +11.029 $ |
| REENTRY yalnız TP sonrası | −7.572 $ | +1.057 $ |
Tek gün kanıt değildir. **Geçmiş testi (`run.py` → `results/rapor.md`, 315 işlem, plasebolu): hiçbiri geçmedi.**
| kural | geçmişte engellenen | geçmişte kurtarılan R | plasebo % | yarılar |
|---|---|---|---|---|
| K1 fren tüm magic | 1 | −0,71 | 54 | −0,00/−0,71 |
| K2 üst üste binme yok | 28 | −7,66 | 9 | +0,55/−8,21 |
| K3 SL sonrası 60 dk | 107 | −14,44 | 16 | −4,44/−10,00 |
| K4 DAYCOMBO günde 1 | 21 | −8,45 | 28 | −0,00/−8,45 |
| K5a SQZ (DAYCOMBO+REENTRY) | 25 | −6,09 | 89 | −0,00/−6,09 |
| K5b SQZ (tüm aileler) | 153 | +5,05 | 97,5 | +8,27/−3,22 |
| K6 REENTRY yalnız TP sonrası | 10 | −3,78 | 61 | −0,00/−3,78 |
Geçmişte üst üste açılan işlemler +0,198R, SL sonrası 60 dk içinde açılanlar +0,124R, günün 2.+ DAYCOMBO'su +0,348R
(diğerleri +0,05) → zincirler genelde kazandırmış; 10-19 kötü bir gündü. Kalıcı ders kural değil **risk**: fren düzeltildi
(B20, 7862f6c2). SQZ ayrıntısı: `research/sikisma_derin_20261020/SONUC.md` (IO-22, kullanılamaz).
