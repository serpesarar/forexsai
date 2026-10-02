# NASDAQ Kapı/Strateji Araştırması — Nihai Rapor v2 (2026-10-02)

Bu klasörün dört turu + diğer ajanın üç çalışması (`ndx_five_gates_20260930`, `ndx_mechanism_round2_20260930`,
`ndx_synthesis_20261002`) karşılaştırıldı. Canlı bot, bayraklar ve emirler değiştirilmedi. Ölçü birimleri:
**gvol** = işlem getirisi / önceki 20 günün günlük volatilitesi (1×gvol stopla R'ye eşit); R (stop birimi); puan.
Dolar vaadi yoktur. 2025–Eylül 2026 geçmişi birçok turda görüldü; yeni dokunulmamış dönem yok.

## 1. Bir bakışta

| # | Çıktı | Tür | Kanıt özeti | Sınıf |
|---|---|---|---|---|
| **1** | **CAPREV-2: stres günü iki kademeli alım** | YENİ STRATEJİ | NDX 1h/30m/15m + **bağımsız piyasa DAX** + günlük QQQ/NDX; saat plasebosu, kırpılmış ortalama, maliyet, gecikme ayakta | **B+** |
| 2 | K5b: stres günü + önceki RTH dibi altında SELL yok | VETO (gölge) | CAPREV'in aynası; botta −12,8 p (41 karar/5 gün); diğer ajanın portföyünde +6,1R ama 11 gün, anlamsız | B− |
| 3 | Kovalama endeksi ≥3 → SELL yok | VETO (yalnız bot) | bot SELL'lerinde monoton; diğer ajanın portföyünde +0,30R → **bota özgü** | C+ |
| 4 | Pazartesi SELL yok · 5m hacim patlaması · 200g+%10 BUY yok · ay sonu | VETO | zaman dilimi/portföy testlerinde tutarsız; diğer ajan hacim ve uzama vetolarını reddetti | C |
| K | REFLEX `mom_cont` canlıya alınmasın | KORUMA | kenarın tamamı geleceğe bakma sızıntısı (sızıntısız −0,08R) | A |

## 2. CAPREV-2 — kural (dondurulmuş)

Koşul (gün başında bilinir): **önceki ABD işlem günü NDX ≤ −%1,5 veya son 5 gün ≤ −%4** VE **önceki gün VIX ≥ 18,4**, Pzt–Per.
- **Kademe 1:** NY 09:30 açılışında BUY · stop 1×gvol · aynı gün 16:00 çıkış.
- **Kademe 2 (ana kenar):** NY 03:00–15:00 arasında fiyatın **önceki RTH (09:30–16:00) dibinin altında kapattığı ilk bar** → sonraki bar açılışında BUY · stop 1×gvol · **ertesi gün 16:00** çıkış. Teyit beklenmez.
- Lot, stop mesafesine göre risk-eşitlenir. 1×gvol ≈ %1,2–1,5 ≈ 300+ puan; botun 110 p SL'iyle aynı lot kullanılmaz.

Bot bağlamı: bu, **VIXREG'in BUY rejiminin zamanlanmış hâli**. VIX ≥ 18,4'te bot zaten BUY yönlü; CAPREV ne zaman ve hangi fiyattan alınacağını söylüyor.

## 3. CAPREV kanıtı (tur 3 + tur 4)

### 3.1 Ana sonuçlar
| Kaynak | Kademe 2, aynı gün | Kademe 2, ertesi gün | Kademe 1+2 gün toplamı (aynı gün) |
|---|---|---|---|
| NDX 1h 2016–26 | +0,24 (n=107, P=0,98) | **+0,34** (P=0,99) | +0,27 (n=223, P=0,996) |
| NDX 30m 2021–26 | +0,40 (n=72, P=1,00) | **+0,45** (P=1,00) | +0,39 (n=132, P=1,00) |
| NDX 15m 2023–26 | +0,82 (n=24, P=1,00) | **+0,77** (P=1,00) | +0,72 (n=47) |
| NDX 1m 2025–26 (gerçek bid/ask) | +0,98 (n=14, P=0,99) | +0,80 | — |
| **DAX 1h 2019–26 (bağımsız piyasa, kural aynen)** | +0,17 (n=54, P=0,89) | **+0,35** (P=0,98, 6/8 yıl) | +0,16 |
| **DAX 30m 2021–26** | +0,12 | **+0,47** (P=0,97) | +0,17 |
| QQQ günlük 2015–26 (önceki dipten limit al, kapanışta sat) | +0,22, **10/11 yıl** | — | açılıştan alım +0,20, 9/11 |
| NDX nakit günlük | +0,23, **11/11 yıl** | — | +0,20, 10/11 |
| S&P 500 günlük | +0,06 (zayıf, 6/11) | — | +0,12, 8/11 |

### 3.2 Diğer ajanın itirazlarına cevap (tur 4, `round4.py`, `cross_market.py`, `w7.py`)
| İtiraz | Test | Sonuç |
|---|---|---|
| Yoğunlaşma: 11 olayda en iyi 5 gün çıkınca −1,35R | uzun veride kırpılmış ortalama (uçlar %5 atılınca), medyan, en iyi %10'un payı | kırpılmış +0,14 / +0,28 / +0,64 (1h/30m/15m), medyan pozitif. ⚠ 10 yıl 1h'te en iyi %10 olay toplamın tamamını taşıyor (2020/2022 kriz ağırlığı); 2021 sonrası daha dengeli (pay 0,75 / 0,45) |
| Kriz piyangosu mu? | aynı olay günlerinde rastgele saatte alım, 200 tekrar | gerçek sonuç tekrarların **%100'ünün** üstünde (NDX 1h/30m/15m ve DAX 1h); zamanlama gerçek |
| Stressiz/yüksek-VIX aynı olay pozitifti (+3,35R/33) | 4 hücre stres×VIX | stressiz∧yüksek VIX: NDX 0,00 / −0,08 / +0,07, DAX ≈0 → **iki şart birlikte gerekli** |
| 1h'te seans dibi 09:00'dan | 09:00 vs 10:00 tanımı | +0,240 vs +0,237, fark yok |
| TP80/SL110 kenarı öldürüyor | çıkış eğrisi | kenar **zamanda**: stopsuz getiri günlerce büyüyor (1h: aynı gün +0,31 → 4 gün +0,91). Braket ürünüyle karıştırılmamalı (diğer ajanla aynı görüş) |
| Geri alımı beklemek? | anında vs geri alım | geri alım pozitif ama her kaynakta anında alımın yarısı |
| Hacim (≥150 olay) | kademe 1+2 | 10 yılda **223 olay günü** → kart hacmi şartı karşılanabilir |

Ayrıca: maliyet ×3 ve +1 bar gecikme etkisi küçük; eşik ızgarası (−%1/−1,5/−2 × −%3/−4/−5) 9/9 pozitif.
VIX 18,4–25 kovası zayıf ama pozitif (+0,12 / +0,08 / +0,26 / +0,09); kenar VIX 25+ ile büyüyor.
Stres ∧ VIX < 18,4: 2016–20'de pozitifti, 2021 sonrası negatif → filtre gerekli.

### 3.3 Dürüst sınırlar
- **Yılda ~22 gün; Temmuz–Eylül 2026 gibi düşük VIX dönemlerinde hiç çalışmaz.** VIXREG BUY rejimiyle aynı uykuda kalır.
- Getiri sağa çarpık; 10 yıllık seride kriz yılları ağırlıklı.
- Aynı NDX geçmişine dört tur bakıldı. En temiz bağımsız kanıt DAX ve günlük QQQ/NDX; S&P 500'de etki zayıf.
- Diğer ajanın katı M1 icrasında (11 olay) +11,1R ama küçük örnek; aynı olay setinde onların ve bizim icra farkı raporlandı.
- 1 gvol stop geniş; gerçek dolum ve gece boşluğu (kademe 2 bir gece taşır) canlıda doğrulanmadı.

## 4. Diğer ajanla karşılaştırma ve düzeltmelerim

| Konu | Diğer ajan | Bu çalışma | Ortak sonuç |
|---|---|---|---|
| Beş kanıtlı kapı | yok | yok | **uyumlu** |
| Cache Şub–8 Mart 60 dk hatası | H1 kaynağıyla | açılış sıçramasıyla | **bağımsız teyit** |
| 30 Eylül makro değeri | gün içi değer olduğunu buldu | düzeltildi (NDX 30.408,50 / VIX 16,34); sonuçları etkilemedi | düzeltildi |
| K5 (tüm stres SELL vetosu) | portföyde dönemsel kararsız (−12,4R / +8,0R) | — | **yalnız K5b** gölgeye |
| Kovalama endeksi | portföye +0,30R | botta monoton | **bota özgü**; ayrıca "K5b'yi içerir" ifadem **yanlıştı** (K5b iki bileşen, ≥3 eşiğine yetmez) |
| Hacim / uzama vetoları | reddedildi (H2/H4) | C+ / tutarsız | **elendi** |
| μ ∝ σ² | volatilite gruplarında fark olmaması bunu kanıtlamaz | — | **haklı**: yalnız olası açıklama, kanıt değil |
| CAPREV | M1'de en güçlü fikir, kanıt yetersiz | uzun veri + DAX + günlük endeks | **en öncelikli gölge adayı** |

## 5. Genel dersler (dört turun özeti)
1. **Rastgele girişte durum kapısı yok** (780 hücre plasebo altında). Kenar ya günlük rejimde ya stratejinin kendi yapısında.
2. **Korku döner, coşku dönmez.** Stres sonrası aşağı aşırılık hem NDX'te hem DAX'ta geri dönüyor, yukarı aşırılık dönmüyor.
3. **Teyit beklemek günlük ölçekte zarar.** Stres günü yeni dip satılmaz, alınır. Geri alımı beklemek kenarın yarısını kaçırır.
4. **Braket ≠ zaman.** Toparlanma sürüklenmesi saatlerce-günlerce sürer; 80/110 braket onu yakalayamaz.
5. **Veto katkısı portföyde ölçülmeli** (diğer ajanın katkısı): bir grubun ortalama kaybı, engellenince aynı miktarda kazanç demek değildir.
6. **Bir kapıyı başka popülasyona taşımadan orada ölç.** Decider bıçak kapısı botta ters çalıştı; kovalama endeksi portföye taşınmadı.

## 6. Önerilen sıra (hiçbiri canlı değil, 2. KURAL)
1. **CAPREV-2 gölge scope** (yeni magic, emir yok): her stres∧VIX≥18,4 gününde kademe 1/2 olay anı, giriş fiyatı, VIX,
   stop, aynı gün/ertesi gün sonuçları kaydedilsin. Uzun veriyle go-live kartı (≥150 olay, iki yarı, bootstrap, spread ×1,5,
   sonraki-bar icra, tek pozisyon) çıkarılabilir. Canlı karar gerçek dolum + gece boşluğu doğrulandıktan sonra.
2. K5b → bot `log_gate_skip` gölge nedeni (veto uygulanmadan ileriye dönük niyet logu).
3. REFLEX: `REFLEX_LIVE=False` kalıcı; araştırma dedektörü düzeltilmeli.
4. Cache Şub–8 Mart +60 dk DB onarımı.

Dosyalar: `RAPOR.md` (tur 1–2), `PROTOCOL.md`…`PROTOCOL_4.md` (ön-kayıtlar), `round3.py`, `v3_robust.py`, `round4.py`,
`cross_market.py`, `w7.py`, `pull_dax.py`; çıktılar `results/round3.json`, `v3_robust.json`, `v3_tail.json`, `round4.json`,
`cross_market.json`, `w7.json`.
