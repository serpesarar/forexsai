# NASDAQ kazanç kapısı araması — rapor (2026-11-10)

Ön kayıt ve deneme sayacı: `PROTOCOL.md` (her tur sonuçtan önce yazıldı). Kod `tur1…tur6b.py`, sonuçlar `results/`.
Canlı sisteme dokunulmadı. Yerel kart: `backend/data/evolution/go_live_cards/ndx_ksg_gece.json`.

## Sonuç

Altı turda sekiz kapı / kural sınandı. Beşi geçmedi, biri yakın kaldı, biri kartı geçti:

**KSG — "kapanış saati gecesi".** NAS100'de son nakit saati (15:00 → 16:00 ET) aşağı kapandıysa 16:00'da AL,
ertesi seansın 09:30'unda SAT. Stop yok. Yılda ~123 işlem.

| Ölçüm (broker NAS100 M30, 2018-05 → 2026-11, spread × 1,5 + swap dahil) | Değer |
|---|---|
| İşlem | 1.039 gece |
| Ortalama net | **+7,0 bp** (brüt +11,0), isabet %56 |
| P(beklenti > 0), ay-blok | %99,6 · dairesel kaydırma p < 0,0001 |
| İki yarı | +5,6 / +8,4 bp |
| Karşı kol (son saat yukarı, 1.057 gece) | net **−6,1 bp** |
| Yıllık net | ≈ +860 bp (kaldıraçsız), aylık Sharpe 0,87, ayların %63'ü artı |
| En kötü gece / en derin düşüş | −400 bp / −1.326 bp |

Canlıya alma kartı (2. KURAL) **6/6**; ön-kayıtlı şemaya göre sınıf **C+**, çünkü bağımsız eski dönem ölçütü düştü
ve etki 2020'de başlıyor. Önerim gölge; canlı kararı kullanıcıda.

## Neden bu kural, nereden çıktı

Defterde hazır bir öncül vardı: ME-06(f) sonradan ipucu, ME-07 ön-kayıtlı tek sınama — "NDX son nakit saati
aşağıysa gece yükselir". 205 geceyle yön doğrulanmış (fark +12,7 bp, P 0,906) ama güç yetmediği için "sonuçsuz"
kalmıştı. Broker verisi 2.095 gece veriyor; aynı fark burada +13,1 bp.

Mekanizma defterin ilkesine uyuyor ("kim işlem yapmak zorunda?"): kapanışa yığılan zorunlu satış (kaldıraçlı
ETF dengelemesi, korunma, teminat) fiyatı son saatte aşağı iter; riski gece taşıyan taraf prim alır.

## Ön-kayıtlı doğrulamalar (Tur 6, EK-5 / EK-6)

| # | Sınama | Sonuç | Geçti |
|---|---|---|---|
| D1 | Yıl: 9 yılın ≥ 7'sinde net > 0 | 7/9. 2018 −9,7 · 2019 −2,5 · 2020 +26,8 · 2021 +5,6 · 2022 +0,1 · 2023 +2,8 · 2024 +16,7 · 2025 +6,7 · 2026 +11,0 | ✓ |
| D2 | Özgüllük: altı saat penceresi | Yalnız 15→16 ayırıyor: +13,1 bp (P 0,997). 10→11 −6,5 · 11→12 −5,0 · 12→13 −6,5 · 13→14 −0,9 · 14→15 +0,7. Günün yönü ayırmıyor (+0,6). Düşüş günü içinde +15,1, yükseliş günü içinde +12,6 | ✓ |
| D3 | Bağımsız dönem NDX 1h 2016-06 → 2018-05 | Kural brüt +9,9 (n 221, P 0,975), net +6,0; ama kapı farkı +4,5, P 0,79 (eşik 0,90) | ✗ |
| D4 | Kör enstrüman (kendi son saati) | US500 net +2,5 (fark +4,5) · US30 +0,2 (+3,2) · US2000 +7,6 (+14,9, P 0,999); üçünün ortalamasında fark P 0,964 | ✓ |
| D5 | Besleme: Dukascopy 1m 2021-11 → | net +6,2 (P 0,967); broker ile gece getirisi korelasyonu 0,983 | ✓ |
| D6 | Kart | n 1.039; spread × 3'te +5,6 (P 0,984); 16:30 girişinde +5,6; en iyi 5 gece hariç +5,0 | ✓ |
| S1 | Gecikmeli giriş (1m) | 16:01 +5,1 · 16:05 +5,2 (P 0,926) · 16:14 +4,5 | ✓ |
| S2 | Sinyal 15:55'te kesilirse | +4,8 (P 0,958) | ✓ |

Şema: D1 ∧ D2 ∧ D6 zorunlu (geçti). D3 düştüğü için **C+**.

## Dürüst sınırlar

1. **Çağa özgü.** 2018-05 → 2019-12: n 194, net −5,6 bp (fark ters). 2020-01 → 2026-11: n 845, net +9,9 bp,
   7/7 yıl. 2016-18'de kural kazanıyor ama kapı ayırmıyor (o dönemde her gece artıydı). Etki bir gün kaybolabilir.
2. **İnce.** Brüt 11 bp, maliyet 3,9 bp. 2022 ve 2023'te net +0,1 ve +2,8 bp. Swap artarsa erir.
3. **Stop yok.** En kötü gece −%4. Gece boşluğu riski bütünüyle taşınır.
4. **Sonradan görülenler (kural değil):** VIX ≤ 15'te net −3,4 bp (n 256), VIX > 25'te +22,4 (n 179); Perşembe +1,1,
   Cuma −1,6 (üç gece swap). Doz-tepki tam tekdüze değil (en eksi dilim +14,7, orta dilim +12,0, en artı −6,9).
5. **Yoğunlaşma.** C3b ve CAPREV ile aynı gecelerde uzun olabilir; korelasyon ölçülmedi.
6. **Seçim yükü.** Bugün altı tur denendi. KSG'nin yönü defterde önceden yazılıydı ve D1–D6 görülmeden ön-kayıtlandı;
   yine de havuz sonucu Tur 3b tablosunda görüldükten sonra yazıldı.
7. Kart yerel veriyle (kutudan dışa aktarılmış M30). Kutuda `go_live_gate.py` ile yeniden üretilmedi; ileri gölge yok.

## Geçmeyen turlar

| Tur | Fikir | Sonuç |
|---|---|---|
| 1 | Düşüş günü sonrası uzun tabanına üç kapı: korku aşımı (VXN artığı), teslimiyet hacmi (QQQ ≥ 1,5×), yaygın satış (eşit ağırlıklı daha çok düştü) | Üçü de X (Holm 0,64–1,0). Yan olgu: stres etkisi gün-içinde yalnız 2001-10 ve 2018-26'da |
| 2 | Sıkışma günü: yükseliş + yüksek hacim → ertesi gün | Havuz −24,5 bp ama medyan +2,3 (sol kuyruk), doz ✗, SPY ✗ → X. SMA50 altı ralli −39 bp izi C |
| 3 | Gece primi × IBS < 0,2 (QQQ 27 yıl) | Açıkken +10,6 / +21,3 / +13,6 bp, fark 3/3 artı ama p ≈ 0,25, eşik altı → X |
| 4 | Canlı ORB × VIX'e "dün düşüş" kapısı | Açık +0,286R (n 307, 10/10 yıl artı) / kapalı +0,074R; fark P 0,992, üç set, plasebo temiz; kapalı kol sıfıra inmediği için 4/5 → veto değil, **C+** (boyut eğimi adayı; aylık Sharpe 1,32 → 1,44) |
| 5 | Ayı rallisi vetosu (dün yükseliş ∧ SMA50 altı) | +0,076R vs +0,072R, fark yok → X |

Betimsel yan olgular (`results/`): düşüş günü ∧ VIX ≥ 18,4 sonrası gün-içi getiri 1999-2004 −3,3 / 2004-11 +4,0 /
2011-18 −0,4 / 2018-27 **+22,8 bp**; aynı hücrede gece getirisi dört çağda +7,9 / +7,3 / +11,1 / +10,4 bp.
Yani NDX'te korku sonrası gün-içi dönüş 2018 sonrası bir olgu; gece primi ise 27 yıldır var.

## Sıradaki adımlar (yapılmadı)

- KSG gölge kaydı (emir yok): 16:00 ET sinyal, 09:30 çıkış; ≥ 60 gece sonra karne. Durdurma ölçütü önceden: n = 60'ta ort. net < 0.
- Kutuda kartı broker M1 ile yeniden üret (16:00 anındaki gerçek spread ve swap tahakkuk saati).
- C3b / CAPREV / ORB × VIX ile gece-gün örtüşmesi ve birleşik en kötü gün (MH-06).
- Tur 4 eğimi: ORB × VIX'te düşüş günü sonrası lot artışı, E110 ölçütüyle (aylık Sharpe artışı P ≥ %90).

## Ek — İşlem açıldıktan sonra seyir (MAE / MFE), çıkış zamanlaması ve canlı bağlantı (2026-11-10, kullanıcı isteği)

**MAE** = girişten sonraki en kötü yön (düşüş), **MFE** = en iyi yön (yükseliş); işlem boyunca bar high/low. bp = baz puan,
puan = NAS100 ≈ 27.800 fiyatında endeks puanı. Kaynak: `mae_mfe.py`, `results/mae_mfe_*.csv`.

| Kural | n | Ort. düşüş (MAE) | Medyan | En kötü %10 | En kötü | Ort. yükseliş (MFE) | Medyan | En iyi %10 | En iyi |
|---|---|---|---|---|---|---|---|---|---|
| KSG (16:00 → ertesi 09:30) | 1.039 | −70 bp (−195 puan) | −48 | −154 | −609 | +57 bp (+157 puan) | +41 | +125 | +506 |
| C3 (15:30 → ertesi 15:30) | 128 | −128 bp (−355 puan) | −95 | −254 | −720 | +133 bp (+371 puan) | +119 | +272 | +516 |
| C3b (ilk yükselen 15:30, ≤5 gün) | 128 | −166 bp (−461 puan) | −113 | −372 | −1.015 | +150 bp (+417 puan) | +132 | +274 | +832 |
| Bot DAYCOMBO BUY (TP 80 / SL 110) | 43 | −24 bp (−70 puan) | −29 | −41 | −49 | +24 bp (+69 puan) | +28 | +32 | +35 |
| Bot REENTRY BUY | 20 | −20 bp (−58 puan) | −16 | −41 | −43 | +26 bp (+75 puan) | +29 | +34 | +49 |
| Bot REENTRY SELL | 13 | −21 bp (−63 puan) | −16 | −40 | −77 | +30 bp (+86 puan) | +29 | +37 | +45 |
| Bot VIXREG SELL | 209 | −25 bp (−72 puan) | −25 | −42 | −65 | +23 bp (+69 puan) | +28 | +35 | +110 |
| Bot CHREV BUY / SELL | 13 / 15 | −29 / −28 bp | −32 / −33 | −48 / −42 | −61 / −49 | +22 / +21 bp | +27 | +31 / +34 | +33 / +36 |
| Bot MOMSR BUY | 21 | −15 bp (−42 puan) | −15 | −31 | −47 | +15 bp (+44 puan) | +13 | +28 | +29 |
| Bot DECIDER SELL | 80 | −10 bp (−31 puan) | −8 | −23 | −46 | +10 bp (+28 puan) | +10 | +15 | +43 |
| ORB × VIX (5m, 152 işlem) | 152 | yol verisi yok; sonuç dağılımı: %46,7 stop (−1R), %32,2 hedef (+2R), %21,1 arada (ort. +0,56R); ort. risk 39 bp | | | | | | | |

Notlar:
- **Bot aileleri braketle kesiliyor** (SL 110 / TP 80 puan; DECIDER 46 / 31, MOMSR 125 / 52): MAE SL'i, MFE TP'yi aşamaz, bu yüzden küçük
  görünürler. Ortalama düşüş SL mesafesinin yaklaşık %20–27'si, ortalama yükseliş TP mesafesinin %80–95'i (kapanıştan önce TP'ye değip çıkılan işlemler dahil).
- **KSG, C3, C3b'de stop yok**, seyir serbest. KSG kazanan gecelerde ort. −41 bp düştükten sonra +85 bp'ye çıkıyor; kaybeden gecelerde ort. −108 bp düşüp
  yalnız +21 bp'ye çıkıyor. Gecelerin %22,8'inde seyir en az −100 bp, %5,4'ünde en az −200 bp. Dar stop (−100 bp) kazananların büyük kısmını da keser.
- **Acil SL eşiği:** −400 bp'de 8 gece, −500/−600 bp'de 2 gece (2018-12-20 ve 2025-04-04, ikisi −609 bp), −700 bp'de 0 gece tetikler. Ortalama net:
  SL'siz +7,02, %7 SL +7,02, %6 SL +6,16, %5 SL +6,35, %4 SL +4,95 bp. Canlıda %7 kullanılıyor (yalnız sigorta).
- C3 ve C3b satırları aynı olay zincirinden (tek pozisyon) çıkarıldığı için n = 128; kartta C3 n=201 (çakışmalı) idi.
- Gün-içi QQQ günlük testlerinde (NK-01…05) pozisyon yolu yok, yalnız günlük getiri olduğundan MAE/MFE hesaplanamadı. Dukascopy 2024-25 DAYCOMBO/REENTRY
  yeniden üretimi bot işlemleriyle aynı braketi kullandığı için ayrıca hesaplanmadı.

**Çıkış zamanlaması (EK-7, `t_cikis.py`).** KSG kazancı 09:30 açılış sıçramasından gelmiyor: 09:29 kapanış → 09:30 açılış, KSG geceleri +0,13 bp, diğer gecelerde
+0,11 bp (Dukascopy 1m); broker M30 +0,19 / −0,26 bp. Çıkış gecikmesine duyarlılık (Dukascopy 1m, net): 09:29 +6,06 · **09:30 +6,18** · 09:31 +8,12 · 09:32 +8,25 ·
09:35 +6,44 · 09:45 +5,56 bp (ay-blok P 0,96–0,995). Canlı çıkışın tarama gecikmesi kenarı bozmuyor.
*Düzeltme:* betiğin ilk koşusunda dakika numarası yanlıştı (09:30 yerine 15:30 çıkışı ölçülmüş, +9,8 bp); o sonuç geçersizdir, yukarıdakiler düzeltilmiş koşudan.

**Canlı bağlantı (kullanıcı kararı: gölge değil canlı).** `yeni deneme/ksg_live.py`, lot 0.5, magic +11, acil SL %7, çıkış ertesi işlem günü 09:30 ET.
Araştırmayla sadakat (`ksg_sadakat.py`): canlı modül araştırmanın 1.039 sinyal gecesini aynen üretir; fazladan 7 gece tatil/yarım gün öncesi. Birim testleri
yerelde ve kutuda geçti (7 + 12). Commit 40fef13d main'de, kutuda çekildi. **Bot yeniden başlatması açık pozisyon nedeniyle ertelendi (borç yazıldı);
KSG, bot yeni kodla başlayana kadar emir açmaz.** Durdurma ölçütü: n = 60 gecede ort. net < 0.
