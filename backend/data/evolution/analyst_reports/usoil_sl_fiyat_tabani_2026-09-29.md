# −3.064$ SpotCrude SL'i: otopsi + "zarar → kâr → SL" paterninin 487 işlemlik sınaması

**Tarih:** 2026-09-29 · **İşlem:** ticket/position 390567007 · **Betikler:** `research/sl_pattern_2026-09-29/`

## TL;DR

1. **Zararın büyüklüğü bir HATADAN geliyor.** Bot SL mesafesini
   `|broker fiyatı − backend sl_price|` ile hesaplıyordu. 2026-09-03'ten beri backend'in
   emtia mumları Yahoo vadelisine (CL=F / GC=F) düştü; broker SpotCrude ile fark 28 Eylül'de
   3,6$. SL mesafesi = besleme farkı: **3,064$ (%3,1, RR 0,34)**. Config SL (%1,49) ile
   aynı işlem **−1.470$** olurdu. Düzeltme: `phase_rules.backend_sl_distance` (tolerans
   `BACKEND_BASIS_TOL_PCT=0.25`), bot testleri `test_backend_basis.py`.
2. **"Kâra geçince başabaşa/kilide çek" kuralı genelde para KAYBETTİRİYOR.** Her eşikte
   kurtardığından çok kazananı öldürüyor. TP ile biten 279 kazananın 75'i de TP yolunun
   %60'ına varıp girişe geri döndükten sonra TP'yi vurmuş: ekranda izlenen şekil
   kazananlarda da aynı sıklıkta görülüyor.
3. USOIL BUY'a özel kâr kilidi (%60 tetik → %50 kilit) örneklem içinde +10,3R gösterdi, ama
   **bağımsız 123 sinyallik yeniden oynatmada −8,1R** (isabet %65 → %72'ye çıktı, toplam R
   düştü) ve walk-forward'da sıfır katkı → **REDDEDİLDİ**.
4. Petrolde dar SL zarar yazıyor (%0,75–1,0); %1,49 ve üstü iki dönemde de pozitif.
   Mevcut config geometrisi doğru.

## 1. İşlemin anatomisi

| | |
|---|---|
| Sinyal | 12:10:13 UTC, `USOIL.FOREX:BUY` S/R-limit, **tek oy: pulse2** (pulse3 SCOUT sayılmadı) |
| Giriş | limit 98,648 (fiyat 98,726), 12:10:22'de doldu, **10 lot** |
| TP / SL | 99,675 (%1,04 sabit) / 95,584 (**3,064 = %3,1 = 3,5×ATR1h**) → RR 0,34, başabaş isabeti %75 |
| Gölge kapılar | giriş skoru 4/8 (ema200 tarafı, 1h karşı momentum, bıçak, 5m trend) — gölgede, açıldı |
| Giriş öncesi | 60 dk'da −1,38 ATR, 15 dk'da −0,75 ATR düşüş (bıçak yakalama) |
| Yol | 14:00 **−0,44R (−1.340$)** → 14:57 **+0,21R zirve (+658$)**, TP'ye 0,37 kala, TP yolunun %64'ü → 16:15 ani çöküş 95,59 (SL'ye 0,006 kala) → **17:11 SL** → sonra 97'ye geri döndü |

Grafik: `research/sl_pattern_2026-09-29/islem_390567007.png`

## 2. Kök neden: fiyat tabanı karışması

`/api/bot/trade-signal` bota fiyat almıyor; backend kendi beslemesinden fiyat çekip
`sl_price` üretiyor (optimizer SL üretmezse `sl_price = fiyat`). Bot (`_fixed_distances`)
bu mutlak seviyeyi broker fiyatından çıkarıyordu.

| gün | USOIL broker−backend | XAU broker−backend |
|---|---|---|
| ≤ 2026-09-02 | 0,00 (birebir aynı) | 0,00 |
| 09-03 … 09-17 | 0,47 → 0,11 (daralan baz) | −46 … −39 |
| 09-18 (kontrat devri) | **4,69** | −38,8 |
| 09-28 | 3,60 | −32,5 |

Daralan ve sonra sıçrayan fark vadeli kontrat bazının imzası. Railway MT5-Redis dinleyicisi
0 tick / 907 yeniden bağlanma gösteriyor. `data_recorder` aynı MT5 barlarını hem
`candle_cache`'e hem `indicator_snapshots`'a yazıyor; 09-03'ten beri emtia satırları
`candle_cache`'te Yahoo yedeği tarafından eziliyor (`indicator_snapshots` broker gerçeği).

Etki (USOIL BUY SL mesafeleri): 09-23 → 4,37 · 4,60 · 5,20 · 1,92 · 09-28 → 3,06.
Korelasyon SL ~ |fark| = 0,82. Fark sıfırken de dejenere `sl_price == fiyat` %0,05–0,3'lük
mikro SL'ler üretiyordu.

| Eylül USOIL (15 işlem) | $ |
|---|---|
| gerçek | +1.788 |
| config SL | +4.063 |
| config SL + kilit | +4.320 |

**Sinyal kalitesi de etkilendi:** pulse USOIL BUY (broker barlarında, config geometri)
Ağustos'ta (MT5 verisi) ort. **+0,23R** (n=36), Eylül'de (Yahoo verisi) **+0,03R** (n=51).

## 3. Veri ve doğrulama

- 538 kapanmış işlem (`bot_trades`) + 561 canlı giriş satırı (ilk TP/SL, oy verenler).
- 1m broker barları `indicator_snapshots`. `candle_cache` KULLANILMADI (Eylül'de başka enstrüman).
- ⚠️ `indicator_snapshots` 2026-07-28 18:00 UTC'den ÖNCE broker saatinde (+3s) etiketli
  (`fixbars.py`: −3s kaydırma, 18:00–21:00 arası atıldı).
- 491 işlemin giriş ve çıkış fiyatı barla birebir tuttu. Simülatör gerçek TP/SL sonucunu
  **479/487 (%98,4)** tutturuyor (uyuşmayanlar "kazananı koştur" yönetimli NDX işlemleri).
- Muhafazakâr kurallar: giriş dakikası atlanır, aynı barda hedef+stop = stop,
  stop taşıma bir sonraki bardan geçerli.

## 4. "Önce zarar → sonra kâr → SL" paterni

- SL'lerin **%33'ü** SL'den önce TP yolunun ≥%50'sini görmüş. Tam patern (≥0,2R zarar →
  ≥%50 TP yolu → SL) **48 işlem, −20.866$**.
- Başabaş kuralının muhasebesi (487 işlem):

| tetik (TP yolu) | kurtarılan kaybeden | öldürülen kazanan | net R | net $ |
|---|---|---|---|---|
| %30 | 95 | 146 | −11,4 | −8.653 |
| %50 | 68 | 102 | −9,1 | −7.773 |
| %60 | 54 | 75 | +0,2 | −4.007 |
| %80 | 19 | 28 | −1,3 | −5.024 |

- 50+ çıkış kuralı (BE/kilit/trailing/kısmi kâr/TP×/SL×/zaman stopu): en iyisi +11,7R ama
  TEST +1,1R, Eylül −3,2R, dolar −861$. **Sağlam iyileşme YOK.**
- Sentetik test (6.256 rastgele USOIL girişi): kilit kuralları yalnız eğilime TERS yönde
  yardım ediyor → girişin kenarı yoksa yara bandı, kenar değil.
- Erken kes (ilk N dk'da −kR): NDX'te zararlı, USOIL BUY'da küçük, bağımsız yeniden
  oynatmada −11R.
- Derinden limit giriş: USOIL BUY +12,5R ama +10,2R'si TRAIN'de. NDX BUY'da zararlı
  (önceki bulguyla aynı, bkz. `teyit_bekleme_girisi_2026-09-02.md`).

## 5. Ne gerçekten işliyor

- Sistem **ortalamaya dönüşten** kazanıyor: 4s aralığın dibinden alış / tepesinden satış
  +26R (p=0,002). Son 60 dk'da işlem yönünün tersine sert hareketten sonra giriş +11,3R
  (p=0,036). "Bıçak yakalama" genelde kötü DEĞİL.
- NDX'te kazananı koşturmak (TP×1,5–2) walk-forward'da da +4–8R (NDX BUY'da zaten canlı).
- USOIL geometrisi: SL ≥ %1,49 her iki yarıda pozitif. %0,75–1,0 SL'ler −14 / −4 fiyat-%.

## 6. Ek araştırma — zikzak-koşullu başabaş/kilit (kullanıcı hipotezi)

**Soru:** SL'yi hemen değil, fiyat girişin etrafında zikzak yaptıktan sonra çekersek (önce
zarar → kâr; kâr → zarar → kâr; n'inci kâr ziyareti; süre şartı) kazanan öldürme azalır mı?

**Motor:** `research/sl_pattern_2026-09-29/zigzag.py` (numba). Bar içi sıra mum rengine göre
(yeşil O→dip→tepe→C). SL taşıma **2 bar gecikmeli** (bot döngüsü ~80 sn). Kilit devreye
girdiğinde fiyat zaten altındaysa dolum **açılıştan** yapılır; ilk sürümde bu iki iyimser
yanlılık vardı, düzeltildi. 44.064 varyant: kaçıncı kâr ziyareti (1–3) × ilk olay (kâr/zarar/
fark etmez) × kâr eşiği (TP yolunun %20–80'i) × zarar eşiği (0.05–0.5R) × kilit (−0.3R…½TP)
× yaş (0/15/30/60 dk) × eylem (SL çek / kapat).

**Veri setleri:** A = 487 bot işlemi (Ağu öncesi/sonrası), B = 615 çakışmasız pulse sinyali
(botun geometrisiyle broker barlarında), C = 14.964 sentetik giriş (iki yön, 3 sembol).

**Neden zikzak yardım etmiyor (koşullu olasılık, %60 / 0.2R):** 1. kâr ziyaretinden sonra
BE'nin işlem başına net etkisi ≈ 0 (A −0.002, B +0.012, C −0.008R). 2. ziyaretten sonra
DAHA KÖTÜ (A −0.020, B −0.070, C −0.032R): zikzak yapan fiyat girişe daha sık döner, TP
oranı değişmez.

**Kazanan öldürme ~0'a iner — kilit girişin ÜSTÜNDE olursa** (A+B, 1.102 sinyal):

| kural | kazanan→zarar | kârı kırpılan | kaybeden→kâr | net (A+B) | C cR/işlem |
|---|---|---|---|---|---|
| klasik %60 → girişe BE | 171 | 0 | 0 | +10.1R | +0.04 |
| klasik + 60 dk şartı | 63 | 0 | 0 | +15.2R | +0.04 |
| 3 zikzak → girişin 0.1R altı | 96 | 0 | 0 | +26.4R | **−0.65** |
| F1: önce ≥0.3R zarar → %60 → SL ½TP | **6** | 172 | 66 | +19.9R | +1.17 |
| F3: aynı zikzak → kapat | 11 | 221 | 63 | +23.0R | +1.34 |

Grafik: `research/sl_pattern_2026-09-29/zikzak_kurallari.png`

**Ama grup bazında hiçbiri tutmuyor.** Her (sembol, yön) için 44.064 kural × 6 dilim
(A iki dönem, B iki yarı, C iki yarı), 6/6 pozitif olan: USOIL BUY **0**, NDX BUY **0**,
NDX SELL 5, DAX BUY 16. Bağımsız şans beklentisi ~%1,6, yani ~700. F1'in toplam
pozitifliği büyük ölçüde USOIL SELL'den (bloklu scope; petrol dönemde +%23) geliyor.
USOIL BUY'da F1: A +8.0R ama B −8.5R, C −13.9R. Dünkü işlemi (+514$) ve 47 patern işlemini
(+20.770$) kurtarıyor, ama bunun ~16 bin doları başka kazananların kırpılmasıyla ödeniyor.

**Sonuç:** zikzak ailesinde canlıya alınabilir kural YOK. En iyi aday (F1) kazananı hiç zarara
çevirmediği için ileriye dönük gölge ölçümüne uygun.

## 7. Kararlar

| | durum |
|---|---|
| Bot fiyat-tabanı koruması (`backend_sl_distance`) | uygulandı (bot tarafı), test 8/8 |
| Backend emtia beslemesini MT5'e geri döndür | backlog — yüksek |
| Genel BE/kâr kilidi | **UYGULANMAZ** (kanıt aleyhte) |
| USOIL BUY kâr kilidi | reddedildi (bağımsız örneklemde −8,1R) |
| Zikzak-koşullu BE/kilit (44.064 varyant) | canlıya alınmaz; hiçbir grupta 6/6 dilim yok |
| F1 (önce zarar → %60 → SL ½TP) | **GÖLGEDE** (2026-09-30): `trade_manager._shadow_lock_pass`, USOIL BUY, `shadow_lock.jsonl` |
| USOIL BUY seans filtresi (yalnız 13–23 UTC) | **GÖLGEDE** (2026-09-30): `_session_gate_blocks`, `gate_skipped.jsonl` reason=usoil_session_gate, parmak izi `session_gate` |

## 8. Yalnız USOIL BUY — kazancı en üste çıkarma araştırması (kullanıcı odağı)

**Veri:** kutudan SALT-OKUMA ile 99.000 SpotCrude M5 barı (2025-05-08 → 2026-09-29; 1m broker
verisiyle %98,3 birebir; `box_pull.py`), 950 pulse USOIL BUY sinyali (15 dk tekilleştirme),
74 canlı-aile bot girişi. Hepsi config geometrisiyle (TP %1,04 / SL %1,49).
⚠️ `candle_cache` USOIL 1m Şubat–Nisan 2026 2 ondalıklı (SpotCrude değil) ve Haziran'ı +3s
kayık — kullanılmadı.

**Çıkış taktikleri (1.558 taktik × 3 rejim):** TP çarpanı 0,6–2,5, koştur 0,3–0,8R, zikzak
kilidi/kapat. 2025 dönemiyle seçilen taktiklerin sıralaması 2026'ya taşınmıyor: L1↔L2
ρ = −0,09 / +0,24 / −0,15. Rastgele girişlerde her taktiğin sonucu o çeyreğin petrol
yönünü izliyor (2025Q4 ve 2026Q2 hepsi negatif, 2026Q1 ve Q3 hepsi pozitif). Çıkış taktiği
USOIL'de yalnız yön kaldıracı → **sağlam çıkış taktiği YOK**.

**Giriş tarafı:**
| filtre | bot $ (74→) | pulse cR/işlem (yarılar) | 17 ay rastgele |
|---|---|---|---|
| filtresiz | 2.276$ | 3,3 (−0,5 / 15,7) | −0,52 |
| **yalnız 13–23 UTC** | **3.937$ (50)** | **8,8 (4,8 / 16,0)** | +0,56 (4/6 çeyrek) |
| pulse3 şart | kalite ↑, toplam ≈ | 16,6 (18,4 / 10,2) | — |
| düşen trendde alma | ters | −20 | ters (2025'te en kötü rejim "yükselen") → RED |

Seans filtresinin canlıya alma kartı: hacim ✅ 556 · beklenti +0,088R ama gün-blok bootstrap
**%81** ❌ · yarılar ✅ · spread×1,5 ✅ · icra ✅ · **tek pozisyon kısıtında toplam kazanç yok**
(+9,9R vs +10,1R) ❌ → **GÖLGE adayı**.

**Düzeltme:** SL hatası 3 ayda sistematik zarar ettirmedi (gerçek +2.757$ vs config
+2.276$); zararı kuyruk riskinde (tek işlemde −3.064$). Düzeltme yine gerekli.
