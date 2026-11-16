# NDX 9 yıllık 1m — yeniden sınama, genişletme, yeni kapılar (2026-11-16)

Ön kayıt: `PROTOCOL.md` (§2–§4 sonuçlar görülmeden, EK-1 ilk sonuçlardan sonra ama EK-1 koşulmadan önce).
Kod: `src/lib.py` (veri, maliyet, istatistik), `src/rules.py` (canlı kodla birebir 8 kural), `a_retest.py`, `b_extend.py`,
`c_new.py`, `d_ek1.py`, `kart.py`. Sonuçlar `results/`. Koşma: `../../.venv/bin/python src/a_retest.py` (≈ 4 sn; önbellek `cache/`).

## Veri: ne yeni?
Dukascopy USATECHIDXUSD BID 1m, **2018-01-02 → 2026-11-13, 2,96 M bar**, tek besleme (`research/nom_20261113/data/ndx_1m_v3_duka.parquet`).
2021-11 → 2026-11 dilimi 1m'de zaten incelenmişti (KT-01, CK2). **Gerçekten yeni olan 2018-01 → 2021-10 dilimi** (Şubat 2018 şoku,
2018 Q4, 2020 çöküşü, 2021): önceki sınamalar orayı broker M30/H1 ya da 1h geometrisiyle görmüştü. Rapor bu dilime **ESKİ**, sonrasına **YENİ** der.
Sınırlar: Dukascopy NDX 16:15–18:00 ET işlem görmüyor (ay başı kuralının 16:30 girişi 16:14 kapanışıyla ölçüldü); spread NY saatine göre
bp modeli (2025 gözlenen), stop/TP 1m'de, aynı barda ikisi → stop; uzun pozisyona gece başına %6,41/365 finansman.
Sızıntı: önek testi (veriyi 2020-06-15 ve 2023-03-01'de kesip yeniden koşmak) C3b/CAPREV/ORB/KSG'de 8/8 birebir.

## A — Canlı kuralların dondurulmuş hâliyle yeniden sınaması

| kural | birim | n | ort tüm | P | ESKİ n / ort / P | YENİ n / ort / P | ×1,5 spr | hüküm |
|---|---|---|---|---|---|---|---|---|
| C3b | bp | 132 | +68,1 | 1,00 | 51 / +59,6 / 0,999 | 81 / +73,5 / 1,00 | +67,4 | **dayanıyor** |
| C3 | bp | 209 | +43,3 | 1,00 | 75 / +40,9 / 0,999 | 134 / +44,6 / 1,00 | +42,7 | dayanıyor |
| FOMC gecesi | bp | 69 | +28,1 | 1,00 | 29 / +26,6 / 0,989 | 40 / +29,1 / 1,00 | +27,4 | **dayanıyor** |
| KSG | bp | 1.078 | +6,4 | 0,99 | 487 / +6,7 / 0,95 | 591 / +6,2 / 0,97 | +5,7 | dayanıyor (2018-19 eksi, 2020 +26) |
| ORB × VIX (2R) | R | 741 | +0,101 | 0,99 | 341 / +0,110 / 0,97 | 400 / +0,094 / 0,93 | +0,084 | dayanıyor — **ama iddia edilenin yarısı** |
| AY BAŞI uzun | bp | 48 | +66,3 | 0,99 | 21 / +50,4 / 0,90 | 27 / +78,6 / 0,96 | +65,2 | dayanıyor (n küçük) |
| AY SONU son seans | bp | 68 | +40,9 | 1,00 | 35 / **+8,6 / 0,68** | 33 / +75,1 / 1,00 | +40,2 | **zayıf** — kazanç 2022 sonrası |
| CAPREV (NDX) | R | 103 | +0,278 | 0,99 | 39 / **+0,065 / 0,64** | 64 / +0,407 / 1,00 | +0,272 | **zayıf** — 2020'de −0,07 (n 16) |
| FR-15 çekiç | R | 701 | +0,119 | 0,95 | 300 / +0,082 / 0,81 | 401 / +0,147 / 0,92 | +0,082 | zayıf; 2026 −0,05 |
| (ORB VIX altı kolu) | R | 803 | +0,002 | 0,53 | +0,031 | −0,020 | | VIX şartı gerçek |

Önceki ölçümler birebir tekrar üretildi (C3b broker +71 / burada +68; C3 +45,7 / +43,3; FOMC +28,5 / +28,1; KSG +7,0 / +6,4;
CAPREV kartı +0,240 / +0,278). Yıl tablosu `results/a_retest.md`.

**Önemli düzeltme (§4 açık işi kapandı):** ORB × VIX'in "10 yılda +0,185R" iddiası, 2016-21'i **1h geometrisiyle** havuzlamaktan geliyordu
(E139). Canlı geometriyle (OR15, 5m tetik) gerçek değer 2018-26 **+0,101R**; 2018 −0,009, 2022 −0,050 (170 olay).

## B — Genişletme: komşuluk haritası (plato mu, tepe mi?)
Ölçü ay başına toplam; aday = iki dönemde de canlı parametreyi geçen ve fark P ≥ 0,90 olan komşu (`results/b_grid.csv`, `b_extend.json`).

| kural | hücre | iki dönemde artı | aday |
|---|---|---|---|
| ORB × VIX | 72 | %79 | **TP 3R** (ESKİ +0,110 → +0,220R, dP 0,999; YENİ +0,094 → +0,182, dP 0,995) — OR15/5m'de dört VIX eşiğinin dördünde 3R > 2R |
| C3b | 18 | %100 (plato) | **16:00 girişi** (ESKİ +59,6 → +73,7 bp, dP 0,945; YENİ +73,5 → +82,3, dP 0,975) — KT-01 A2 (C) yeniden ölçümü |
| KSG | 6 | %100 | yok; 10:00 çıkışı iki dönemde iyi (+9,0 / +7,7 bp) ama dP 0,88 / 0,79 |
| CAPREV | 24 | %75 | yok; ertesi gün 16:00 çıkışı ESKİ +0,18 (dP 0,81), YENİ aynı; ESKİ her varyantta zayıf |
| çekiç | 12 | %100 | yok; komşular dönemler arası tutarsız (lw 0,6 ESKİ +0,18 / YENİ +0,07) |

## C — Ön kayıtlı yeni kapı/strateji hipotezleri

| H | fikir | sonuç | hüküm |
|---|---|---|---|
| H1 | ORB OR-genişliği dozu (öngörü: dar kötü) | **Ters:** dar tertil en iyi (R +0,218 / +0,176; geniş +0,006 / +0,064). Bp'de de (EK1-b) ESKİ +10,5 vs −5,3 (P 0,95), YENİ +5,6 vs +5,1 | öngörü X · dar açılış C (doz adayı, tek dönemde güçlü) |
| H2 | Oynaklık-yönetimli kitap (Moreira–Muir) | ters oynaklık ESKİ Sharpe 1,58 → 1,35, YENİ 2,16 → 2,40; oynaklıkla büyütme iki dönemde düşürüyor | **X** |
| H3 | Panik freni (dünkü VIX ≥ 35 → uzun açma) | atlanacak 111 işlem **ort +81 bp**; fren 8.480 $ kaybettirir, max düşüşü değiştirmez | **X (ters, A olgu): korku günleri kitabın en iyi günleri** |
| H4 | KSG son saat düşüş yoğunluğu dozu | derin tertil iki dönemde en iyi (+16,5 / +10,7 bp) ama YENİ monoton değil, uç fark P 0,92 | C |
| H5 | önceki C+ etiketleri ESKİ 1m'de | NK-04 ORB × dün düşüş ✓ (+0,205 vs +0,024); DB-02 KSG × VIX ≥ 25 ✓ (+32,2 vs +0,3 bp, P 0,98); TS-01 O4 C3b vade haftası ✓ (−18,9 vs +74,1, n 8); KT-01 A4 C3b ek birim ✓ (+80 bp, n 24); **CK2-03 CAPREV × dün son saat aşağı ✗** (+0,04 vs +0,12) | 4/5 tutarlı |
| H6 | Kitap stres sınaması (canlı lotlar, 1m işaretleme) | aşağıda | A (olgu) |

**H6 — canlı kitap 2018-26 (C3b 2,0 · CAPREV 1,0 · ORB 0,75 · çekiç 0,5 · KSG 0,5 · AY SONU 1,0 · AY BAŞI 0,75; 1 lot = 1 $/puan):**
toplam +57.462 $, aylık Sharpe 1,82 (ESKİ 0,98, YENİ 1,51 $ cinsinden; fiyat düzeyi 2018'de 6.400). ESKİ'nin en kötü günü
**2020-03-12 −1.189 $**, max düşüş −1.624 $ (2020-02-27). Tüm dönemin en kötü günü 2025-04-06 −1.863 $ (gümrük vergisi boşluğu), max düşüş
−4.455 $ (2022-02-23). Acil stoplar: C3b %10 tüm dönemde 1 kez sınırda (−%10,09, YENİ dilimde; 2020'de en kötü −%8,3), KSG %7 hiç (en kötü −%6,2),
ay sonu %4 / %8 hiç. Açık lot en çok 4,5 (tavan hiç aşılmadı).

## EK-1 — sonuçlardan doğan sorular (en fazla B−)
- **EK1-a ORB çıkış eğrisi:** ort R (ESKİ / YENİ) — 2R +0,110 / +0,094 · **3R +0,220 / +0,182** · 4R +0,204 / +0,212 · 5R +0,180 / +0,187 ·
  TP'siz +0,175 / +0,193. 2R eğrinin en kötü noktası ("braket ≠ zaman", §3-5: korku günü kırılımı gün sonuna kadar taşıyor, 2R kuyruğu kesiyor).
  **TP 3R kartı 6/6** (`go_live_cards/ndx_orb_vix_tp3.json`): n 741, isabet %39,8, ort +0,199R (bp: +7,2 / +8,8), %95 [+0,10; +0,31],
  P 1,00, yarılar +0,19 / +0,21, spr×1,5 +0,18, icra farkı 0,012, **9/9 yıl artı** (2R'de 2018 ve 2022 eksiydi), en iyi 5 hariç +0,18.
- **EK1-c doz, kitap aylık Sharpe'ı (E110), ortalama lot sabit:** KSG × dünkü VIX ≥ 25 (×2) 1,82 → 1,88 (ESKİ 1,58 → 1,63, YENİ 2,16 → 2,20,
  birleşik P 0,92) ✓ · C3b vade haftası ×0,5: 1,82 → 1,95 (ESKİ 1,58 → 1,62, YENİ 2,16 → 2,34, P 0,94) ✓ · ORB × dün düşüş (×1,5/×0,5)
  1,82 → 1,81 ✗ (işlem kalitesini artırıyor, Sharpe'ı artırmıyor — E110'un tam örneği).
- **EK1-d FOMC öncesi sürüklenme (Lucca–Moench):** 16:00 → 13:55 çıkışı 09:30'u iki dönemde aşıyor (+28,9 / +34,7 vs +26,6 / +29,1 bp) ama
  09:30 → 13:55 dilimi tek başına +1,4 / +4,7 bp (P 0,58 / 0,75) → NDX'te önce-FOMC primi **gecede**; gün içi uzatma C.

## Uygulamaya geçenler (2026-11-16, kullanıcı isteği "uygulamaya geç"; hepsi config ile geri alınır)
| değişiklik | dosya | sınıf | kapatma |
|---|---|---|---|
| ORB × VIX hedef 2R → **3R** | `yeni deneme/orb_vix_live.py` (`TP_R_LIVE`) | B (kart 6/6) | `ORB_VIX_LIVE_TP_R = 2.0` |
| C3b vade haftasında **yarım lot** | `yeni deneme/c3b_live.py` (`entry_lot`, `opex_week`) | B− (risk azaltan) | `C3B_OPEX_HALF = False` |
| KSG dünkü VIX ≥ 25'te **çift lot** | `yeni deneme/ksg_live.py` (`entry_lot`, `_vix_prev`) | B− | `KSG_VIX25_DOUBLE = False` |
Testler: `test_kural_canli.py` (+2 yeni), `test_orb_vix_shadow.py` (+1), toplam 57/57. Gölge (`orb_vix_shadow.py`) kart geometrisini (2R) ölçmeye
devam eder; 3R'nin ileri karnesi canlı işlemlerden (`kural_canli_olaylar.jsonl`, `tp_r` alanı). Durdurma ölçütleri (önceden yazılı):
ORB 3R n = 60 işlemde ort R < 0 → 2R'ye dön; C3b/KSG dozları için n = 20 dozlu işlemde dozlu ort < dozsuz ort → kapat.

**Bağlanmayanlar (bilinçli):** C3b 16:00 girişi (en büyük lotlu kuralın giriş saatini değiştirmek; KT-01 A2'de kör 1/3; gölge etiketi önerisi),
CAPREV/AY SONU son seans zayıflığı (kural değişmedi, karar kullanıcıda; ikisi de 2018-21'de pozitif ama P < 0,7), FOMC gecesi (zaten gölge önerisi).

## EK-2 — yeni strateji aileleri (ön kayıt PROTOCOL EK-2, `src/e_ek2.py`, `src/f_s4.py`)
| S | kural (dondurulmuş) | ESKİ n / ort / P | YENİ n / ort / P | hüküm |
|---|---|---|---|---|
| S1 | korku açılış boşluğu: dünkü VIX ≥ 18,4 ∧ açılış < önceki kapanış × (1 − 0,5·dvol) → 09:30 AL, 15:55 | 66 / +36,7 bp / 0,99 | 93 / +12,0 / 0,75 | C (kontrol VIX < 18,4: +12 / −11) |
| S2 | ORB kısa aynası (VIX ≥ 18,4, OR dibi kırılımı SAT, 3R) | 297 / +0,012R / 0,55 | 364 / +0,018R / 0,59 | X (spr×1,5 −0,002) |
| S3 | Avrupa açılışı (03:00–03:15 ET) aralık kırılımı AL, 3R, 09:25 | 320 / −0,013R | 419 / −0,083R | X |
| **S4** | **korku günü öğleden sonra:** dünkü VIX ≥ 18,4 ∧ 12:00 fiyatı > 09:30 açılışı → 12:00 AL, 15:55 SAT | 249 / **+10,0 bp / 0,993** | 301 / **+9,9 / 0,954** | **tek başına 6/6, portföyde X** |

S4 ayrıntısı: isabet %61,5, spr×1,5 +9,3, en iyi 5 hariç +5,6, 1 dk geç giriş +9,9, kontrol (VIX < 18,4) −3,0 / −1,0 bp; yıllar 7/9 artı (2024 −13,
2026 −1,8). ORB'nin 12:00'de açık olduğu günlerde +8,1 / +11,2, açık olmadığı günlerde +12,7 / +8,4. **Canlı kitaba (ORB 3R'li) 0,5 lotla eklenince
aylık Sharpe ESKİ 1,69 → 1,80 (P 0,93) ama YENİ 2,18 → 2,04 (P 0,09), tüm dönem 1,86 → 1,78** — aynı korku günlerine yığılan risk (E110, §3-30).
Karar: **bağlanmadı**; gölge adayı (B− tek başına). Mekanizma ORB×VIX'inkiyle aynı (korku günü gün içi yukarı sürüklenme); ikinci bir bahis değil.

## Hükümler (defter §2.57)
NX-01 A yeniden sınama (8 kural, 5 dayanıyor, 3 zayıf) · NX-02 ORB 2R → 3R **B, canlı** · NX-03 C3b 16:00 C → **C+** · NX-04 panik freni **X** (A olgu) ·
NX-05 oynaklık-yönetimli kitap X · NX-06 OR genişliği C · NX-07 KSG yoğunluğu C · NX-08 doz etiketleri: KSG × VIX25 ve C3b vade haftası **B−, canlı**,
ORB × dün düşüş C+ kalır (Sharpe yok), CAPREV × son saat **C+ → C** · NX-09 FOMC 13:55 uzatması C · NX-10 kitap stres olgusu A · NX-11 S1 korku açılış boşluğu C · NX-12 S2/S3 X · NX-13 S4 korku günü öğleden sonra tek başına 6/6, portföy katkısı yok → gölge adayı (B−/portföy X).

**Dağıtım doğrulaması (2026-11-16 22:12 UTC):** kutu `remote.py pull` ile 889ee25d'ye geçti, bot `remote.py restart bot` ile yeniden başladı (açık pozisyon 0), kutuda `orb_vix_live.TP_R_LIVE = 3.0`, `c3b_live.OPEX_LOT_MULT = 0.5`, `ksg_live.VIX_DOSE_TH = 25.0` yüklendi; MT5 Pepperstone-Demo bağlı.
