# OK-01 — Bot ↔ Decider ortak kazanç kapısı · rapor (2026-11-13)

Ön kayıt: `PROTOCOL.md` + EK-1…8 (her ek bir önceki sonuçtan sonra, kendi sonucundan önce yazıldı).
Veri: `bot_trades` 1.114 kapanış → pozisyon (06-29 → 11-13), `decider_journal` 10.315 karar (06-25 → 11-13, OPEN + WAIT karşı-olgu,
net R), panel `prediction_logs` 9.395 çözülmüş sinyal (07-28 →), NDX 30m 2021-26 + 1h 2016-21 vekil. Saat ekseni: bot broker saati
UTC+3 (≤ 11-01) / UTC+2 — decider icralarının günlük zamanıyla 504/504 eşleşti (medyan fark < 1 sn).

## 1. Son 3 ayın tablosu (08-13 → 11-13, 675 pozisyon)

| ajan / aile | n | WR | ort R | net $ |
|---|---|---|---|---|
| Bot REENTRY NDX BUY (30 lot) | 23 | %78 | +0,355 | +20.496 |
| Bot DAYCOMBO NDX BUY (30 lot) | 33 | %67 | +0,151 | +9.442 |
| Bot REENTRY NDX SELL | 14 | %86 | +0,480 | +6.100 |
| Bot CHREV DAX/NDX | 15 | %87 | +0,33…0,54 | +5.649 |
| Bot MOMSR USOIL BUY | 37 | %57 | +0,050 | +1.786 |
| Bot VIXREG NDX SELL | 28 | %46 | +0,010 | −381 |
| Bot MOMSR DAX BUY | 15 | %53 | +0,028 | −250 |
| **Decider XAU BUY** (0,01 lot) | **383** | %57 | **−0,051** | −291 |
| Decider NDX SELL | 91 | %64 | +0,064 | +12 |
| Decider DAX BUY | 30 | %53 | −0,114 | −10 |

Toplam +42.200 $; bot +42.489 $, decider −290 $. **"%50-%50" hissinin kaynağı decider:** 504 işlem (işlem sayısının %75'i),
geometrisi TP 1×ATR / SL 1,5×ATR (RR 0,67) → başabaş isabet **%60**; XAU BUY %57, DAX BUY %53 isabetle başabaşın altında.
Botun parası birkaç günde (en iyi 5 gün +48.289 $, en kötü 5 gün −18.829 $; 44 işlem günü) ve 30 lotluk NDX BUY ailelerinde.

## 2. Sınanan hipotezler

| ID | Fikir | Sonuç | Sınıf |
|---|---|---|---|
| H1 | Decider onayı bot için kapı (bot girişinden önceki 30 dk'daki son decider kararı) | AGREE n 22 Δ −0,09R P 0,39; OPPOSE n 11 Δ −0,39R P 0,06 (n < 30) | X (ortak karar kazandırmıyor) |
| H2 | Bot onayı decider için kapı | BOT_SAME n 40 Δ −0,01 P 0,45; BOT_OPP n 35 Δ −0,13 P 0,16 | X |
| H3 | Kaybettireni engelle — aile tahsisi | ENGEL ölçütünü geçen (iki yarı < 0, P(<0) ≥ %90, ön dönem de < 0): **decider XAU BUY** (441 epizod, net −0,105R, yarılar −0,02/−0,19, P 0,998, ön dönem −0,25), decider NDX BUY (−0,22R, P 0,994; zaten canlı değil, D4), decider USOIL SELL (−0,32R, P 0,993; zaten canlı değil, D5). Bot ailelerinin hiçbiri 3 ayda anlamlı eksi değil | **B** (decider XAU BUY) |
| H4 | Decider kapısı (`gate_fired`) açılan kararlar içinde ayırıyor mu | açılanların %95+'ı zaten tetikli → sınanamadı | — |
| H5 | Decider çıkış politikası (journal `exit_grades`, 25 hücre) | 0/25; en yakın NDX SELL TP1,5/SL1,5 (+0,08 ATR, P 0,98) ön dönemde eksi | X |
| H6 | Decider'ın mekanik mean-rev tetiği seans/saat bağımlı mı | **tetik 6/6 sembol-yönde maliyet sonrası eksi** (−0,06…−0,14R, 2.032 epizod); 3 çağda da + hücre 1/28 (plasebo ort 0,45) | X |
| H7 | LLM seçimi tetiğe değer katıyor mu (CLI hatası WAIT'leri = doğal kontrol, aynı hafta eşli) | DAX BUY +0,19 (P 0,78), NDX SELL +0,12 (P 0,78) ama gerçek LLM-WAIT'e göre −0,03; NDX BUY −0,23, USOIL SELL −0,27/−0,39 (seçim zararlı) | X |
| H8 | Mekanik tetiğin tersi (momentum aynası) | NDX BUY tersi üç çağda + ama P 0,917, seçilmiş; OLD-15/E16 ile aynı aile | X |
| H9 | Bot aileleri: "iyi seriden sonra al" | her k'da kaybettiriyor; Spearman −0,09/−0,09/−0,14, plasebo %0–1 → **anlamlı negatif seri bağımlılık** | X (ama tersine bkz. H10) |
| H10 | **"Kendi karnesi geri dönüşü"** — aynı aile-sembol-yönde girişten önce kapanmış son k işlemin ort R ≤ 0 ise al | Bot (nedensel): k=3/5/10 Δ +0,17/+0,11/+0,18R, yarılar +/+, plasebo %95–99,7, aile 8–9/10, plato k=1…12 hep + ; ama $ olarak −10,6k (büyük lotlu kazananları atlıyor), k=5 gün-blok P 0,93. **Bağımsız popülasyonlarda tekrarlanmadı:** decider yoğun dizi Δ +0,01…+0,05 (pl %41–89), decider tek-poz −0,01…+0,06 (pl %37–86), decider OPEN ters; **panel tek-poz TERS** (k=3 Δ −0,095, pl %0) | X (bota/döneme özgü) |
| H11 | H10'un 10 yıllık NDX vekili (bot yapısı birebir: tek pozisyon, 80/110 braket, sonraki bar + yarım spread; 7 strateji; 30m 2021-26 + 1h 2016-21) | VIXREG vekili Δ −0,04…+0,03 (pl %11–72); taban BUY anlamlı TERS (1h k=10 Δ −0,11, pl %0); yalnız kanal-üst SELL 30m'de +0,10 (pl %93–98), 1h'de tutarsız | X |
| H12 | **Farklı emtialarla birlikte:** giriş anında eş piyasanın (NDX↔DAX, USOIL/XAU→NDX) son 30 dk'sı — eş hizası (F1), gecikme yakalama (F2, birincil), altın risk-off karşıtlığı (F3); bot + panel + decider, 15/30/60 dk | F2 bot +0,01 (P 0,58), decider −0,01, panel −0,27 (TERS) → X. Panel'in büyük etkisi kayıt artefaktı: `ml_entry_price` kayıttan 25–95 dk eski (E124); gerçek girişli bot/decider'da düz | X |

## 3. Hüküm

1. **Bot ile decider arasında kazandıran bir "ortak nokta" yok.** İki ajanın aynı yönde anlaşması kazancı artırmıyor (H1/H2).
   Ters düştüklerinde ikisi de biraz kötüleşiyor, ama örneklem n < 40 ve ölçütün altında.
2. **Kaybettiren tek sağlam grup decider XAU BUY.** Sınıf B: iki yarıda, ön dönemde ve gerçek icrada eksi. Kök neden yapısal:
   decider'ın mekanik mean-rev tetiği altı sembol-yönün altısında maliyet sonrası eksi (H6). LLM seçimi bunu anlamlı biçimde
   düzeltmiyor (H7), çıkış politikası da düzeltmiyor (H5). **Uygulandı:** `claude_decider/decide.py` `LIVE_ALLOWED` varsayılanından
   `XAUUSD:BUY` çıkarıldı; kararlar journal'da ölçülmeye devam eder. Etki: decider'ın işlem sayısı ≈ %76 azalır, 3 aylık R'si
   −17,3R'den ≈ +2,4R'ye çıkar. Para etkisi küçüktür (0,01 lot, −291 $), çünkü asıl değer gürültüyü azaltmaktır.
3. **Botun 3 aylık kârı gerçek (+42.489 $), ama defterde C sınıfı olan ailelere dayanıyor:** REENTRY + DAYCOMBO 30 lot NDX BUY
   (+29.938 $, CK-05: kenar 2026'ya özgü). Bot ailelerinin hiçbiri 3 ayda anlamlı eksi değil. VIXREG SELL 220 işlemde ≈ 0R;
   kaybettirmiyor ama riskin büyük payını yiyor (MA-03).
4. **İşlem-düzeyi kalıplar yine taşınmadı.** Botun kendi sonuçlarında güçlü görünen anti-persistans (H10), bağımsız üç
   popülasyonun üçünde de tutmadı. Bu, E24/IO-11/IO-26 dersinin tekrarı: botun 4,5 aylık geçmişinden seçilen kural, bağımsız
   veride sınanmadan kapı yapılmaz.
5. **Kalıcı kazanç kaynağı defterde zaten tanımlı:** "endekste korku + uzun + zaman çıkışı" ailesi (C3b A−/B, CAPREV, ORB×VIX B,
   teyitli çekiç B, ay sonu B, KSG C+). Bunlar 2026-11-08 → 12 arasında küçük lotla canlıya alındı. Son 3 ayda bunlardan
   yalnız 5 işlem kapandı, bu yüzden ölçüm henüz erken.

## 4. Öneriler (kullanıcı kararı)
- (uygulandı, push bekliyor) decider XAU BUY canlıdan çıktı.
- VIXREG SELL lotu: ≈ 0R ile yüksek risk payı → lotu düşürmek varyansı azaltır; beklenen $ bedeli MA-05'e göre sıfırdan ayırt edilemiyor.
- REENTRY/DAYCOMBO 30 lot: kanıt sınıfı C; en kötü 5 gün −18.829 $. Lot tavanı MA-03 karşı-olgusunda günlük SR'yi artırıyordu (C).
- Yeni kapı yok: H1–H12'nin hiçbiri GÖLGE ölçütünü geçmedi.
- Panel sinyal karnesi giriş-öncesi fiyat özelliği sınamasında kullanılmamalı (E124): giriş fiyatı kayıttan 25–95 dk eski.
